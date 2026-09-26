"""DaVinci Resolve Scripting API とのやり取りをここに閉じ込める.

このモジュール以外は Resolve のオブジェクトに触らない (テストしやすくするため).
"""

import os
from typing import Callable, Dict, List, Optional

from .planner import MarkerInfo, TelopJob
from .presets import apply_preset_to_tool
from .timecode import frame_to_timecode, parse_fps, timecode_to_frame

Logger = Callable[[str], None]


class ResolveError(RuntimeError):
    pass


def _is_true(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class ResolveBridge:
    def __init__(self, resolve, log: Optional[Logger] = None):
        if resolve is None:
            raise ResolveError("Resolve に接続できません (Resolve のスクリプトメニューから実行してください)")
        self.resolve = resolve
        self.log = log or (lambda msg: None)
        self.pm = resolve.GetProjectManager()
        self.project = self.pm.GetCurrentProject() if self.pm else None
        if not self.project:
            raise ResolveError("プロジェクトが開かれていません")
        self.media_pool = self.project.GetMediaPool()
        self.timeline = self.project.GetCurrentTimeline()
        if not self.timeline:
            raise ResolveError("タイムラインが開かれていません")
        self._record_base = None  # recordFrame が絶対か相対かを初回挿入で自動判定
        self._end_exclusive = None  # endFrame が排他的か自動判定
        self._track_cache: Dict[tuple, list] = {}
        self._sfx_cache: Dict[str, object] = {}

    # ------------------------------------------------------------------ basics
    def refresh(self):
        self.project = self.pm.GetCurrentProject()
        self.media_pool = self.project.GetMediaPool()
        self.timeline = self.project.GetCurrentTimeline()
        self._track_cache.clear()
        if not self.timeline:
            raise ResolveError("タイムラインが開かれていません")

    @property
    def fps(self) -> float:
        value = None
        try:
            value = self.timeline.GetSetting("timelineFrameRate")
        except Exception:  # noqa: BLE001
            value = None
        if not value:
            value = self.project.GetSetting("timelineFrameRate")
        return parse_fps(value)

    @property
    def drop_frame(self) -> bool:
        try:
            return _is_true(self.timeline.GetSetting("timelineDropFrameTimecode"))
        except Exception:  # noqa: BLE001
            return False

    @property
    def timeline_start(self) -> int:
        return int(self.timeline.GetStartFrame())

    def playhead_frame(self) -> int:
        tc = self.timeline.GetCurrentTimecode()
        return timecode_to_frame(tc, self.fps, self.drop_frame)

    def set_playhead(self, frame: int):
        self.timeline.SetCurrentTimecode(frame_to_timecode(frame, self.fps, self.drop_frame))

    def timeline_name(self) -> str:
        return self.timeline.GetName()

    def frame_tc(self, frame: int) -> str:
        return frame_to_timecode(frame, self.fps, self.drop_frame)

    # ---------------------------------------------------------------- markers
    def markers(self) -> List[MarkerInfo]:
        raw = self.timeline.GetMarkers() or {}
        result = []
        for key, info in raw.items():
            try:
                frame = int(key)
            except (TypeError, ValueError):
                continue
            info = info or {}
            result.append(
                MarkerInfo(
                    frame=frame,
                    duration=int(info.get("duration", 1) or 1),
                    color=str(info.get("color", "")),
                    name=str(info.get("name", "")),
                    note=str(info.get("note", "")),
                )
            )
        return sorted(result, key=lambda m: m.frame)

    def marker_colors(self) -> List[str]:
        return sorted({m.color for m in self.markers() if m.color})

    # -------------------------------------------------------------- subtitles
    def subtitle_items(self, track_index: int = 1):
        items = self.timeline.GetItemListInTrack("subtitle", int(track_index)) or []
        out = []
        for it in items:
            try:
                out.append((it.GetName() or "", int(it.GetStart()), int(it.GetDuration())))
            except Exception:  # noqa: BLE001
                continue
        return out

    # -------------------------------------------------------------- media pool
    def _walk_folders(self, folder=None):
        folder = folder or self.media_pool.GetRootFolder()
        yield folder
        for sub in folder.GetSubFolderList() or []:
            for f in self._walk_folders(sub):
                yield f

    def find_clip_by_name(self, name: str):
        key = (name or "").strip().casefold()
        if not key:
            return None
        for folder in self._walk_folders():
            for clip in folder.GetClipList() or []:
                try:
                    if (clip.GetName() or "").strip().casefold() == key:
                        return clip
                except Exception:  # noqa: BLE001
                    continue
        return None

    def template_candidates(self) -> List[str]:
        """メディアプール内で Text+ テンプレートとして使えそうなクリップ名."""
        names = []
        for folder in self._walk_folders():
            for clip in folder.GetClipList() or []:
                try:
                    name = clip.GetName() or ""
                    ctype = str(clip.GetClipProperty("Type") or "")
                except Exception:  # noqa: BLE001
                    continue
                if "text+" in name.casefold() or "テロップ" in name or any(
                    k in ctype for k in ("Title", "Generator", "Fusion", "タイトル")
                ):
                    if name not in names:
                        names.append(name)
        return names

    def clip_frames(self, clip) -> Optional[int]:
        try:
            frames = clip.GetClipProperty("Frames")
            if frames not in (None, ""):
                return int(float(frames))
        except Exception:  # noqa: BLE001
            pass
        try:
            duration = clip.GetClipProperty("Duration")
            if duration:
                return timecode_to_frame(str(duration), self.fps, False)
        except Exception:  # noqa: BLE001
            pass
        return None

    def _get_or_create_bin(self, name: str):
        root = self.media_pool.GetRootFolder()
        for sub in root.GetSubFolderList() or []:
            if sub.GetName() == name:
                return sub
        return self.media_pool.AddSubFolder(root, name)

    def import_sfx(self, path: str):
        """効果音ファイルをメディアプールの SFX ビンに取り込む (取り込み済みなら再利用)."""
        norm = os.path.normcase(os.path.abspath(path))
        if norm in self._sfx_cache:
            return self._sfx_cache[norm]
        sfx_bin = self._get_or_create_bin("SFX")
        for clip in sfx_bin.GetClipList() or []:
            try:
                fp = clip.GetClipProperty("File Path") or ""
            except Exception:  # noqa: BLE001
                continue
            if fp and os.path.normcase(os.path.abspath(fp)) == norm:
                self._sfx_cache[norm] = clip
                return clip
        previous = self.media_pool.GetCurrentFolder()
        try:
            self.media_pool.SetCurrentFolder(sfx_bin)
            imported = self.media_pool.ImportMedia([path]) or []
        finally:
            if previous:
                self.media_pool.SetCurrentFolder(previous)
        if not imported:
            raise ResolveError("効果音を取り込めませんでした: %s" % path)
        self._sfx_cache[norm] = imported[0]
        return imported[0]

    # ------------------------------------------------------------------ tracks
    def track_count(self, track_type: str) -> int:
        return int(self.timeline.GetTrackCount(track_type) or 0)

    def ensure_track(self, track_type: str, index: int):
        while self.track_count(track_type) < index:
            ok = self.timeline.AddTrack(track_type, "stereo") if track_type == "audio" else self.timeline.AddTrack(track_type)
            if not ok:
                raise ResolveError("%s トラック %d を作成できませんでした" % (track_type, index))
            self.log("%s トラック %d を追加しました" % ("ビデオ" if track_type == "video" else "オーディオ", self.track_count(track_type)))

    def _track_items(self, track_type: str, index: int):
        key = (track_type, index)
        if key not in self._track_cache:
            spans = []
            for it in self.timeline.GetItemListInTrack(track_type, index) or []:
                try:
                    spans.append((int(it.GetStart()), int(it.GetEnd())))
                except Exception:  # noqa: BLE001
                    continue
            self._track_cache[key] = spans
        return self._track_cache[key]

    def _is_free(self, track_type: str, index: int, start: int, end: int) -> bool:
        for s, e in self._track_items(track_type, index):
            if s < end and start < e:
                return False
        return True

    def pick_track(self, track_type: str, preferred: int, start: int, end: int, auto: bool) -> int:
        preferred = max(1, int(preferred))
        if not auto:
            self.ensure_track(track_type, preferred)
            return preferred
        idx = preferred
        for _ in range(32):
            if idx > self.track_count(track_type):
                self.ensure_track(track_type, idx)
                return idx
            if self._is_free(track_type, idx, start, end):
                return idx
            idx += 1
        raise ResolveError("空いている %s トラックが見つかりません" % track_type)

    def _remember(self, track_type: str, index: int, start: int, end: int):
        self._track_items(track_type, index).append((start, end))

    # ------------------------------------------------------------------ append
    def _append(self, clip, duration: int, record: int, track: int, media_type: int):
        """AppendToTimeline を、recordFrame / endFrame の解釈差を自動補正しながら実行する."""
        record_base = self._record_base or 0
        end_exclusive = bool(self._end_exclusive)
        for attempt in range(3):
            info = {
                "mediaPoolItem": clip,
                "startFrame": 0,
                "endFrame": duration if end_exclusive else duration - 1,
                "trackIndex": int(track),
                "recordFrame": int(record - record_base),
            }
            if media_type:
                info["mediaType"] = media_type
            items = self.media_pool.AppendToTimeline([info]) or []
            if not items:
                raise ResolveError("AppendToTimeline に失敗しました (トラック %d, %s)" % (track, self.frame_tc(record)))
            item = items[0]
            actual_start = int(item.GetStart())
            actual_dur = int(item.GetDuration())
            fix = False
            if actual_start != record and self._record_base is None:
                delta = actual_start - (record - record_base)
                if delta in (self.timeline_start, -self.timeline_start):
                    self._record_base = delta
                    record_base = delta
                    self.log("recordFrame の基準を自動補正しました (offset=%d)" % delta)
                    fix = True
                else:
                    self._record_base = 0
                    self.log("注意: %s に置けず %s に配置されました (既存クリップと重なっている可能性)"
                             % (self.frame_tc(record), self.frame_tc(actual_start)))
            if actual_dur == duration - 1 and self._end_exclusive is None and not end_exclusive:
                self._end_exclusive = True
                end_exclusive = True
                fix = True
            if self._record_base is None:
                self._record_base = 0
            if self._end_exclusive is None:
                self._end_exclusive = False
            if fix and attempt < 2:
                self.timeline.DeleteClips([item])
                continue
            if actual_dur < duration:
                self.log("注意: %s の長さが %d フレームに切り詰められました (テンプレートの尺が不足)" % (self.frame_tc(record), actual_dur))
            return item
        raise ResolveError("AppendToTimeline の補正に失敗しました")

    # ------------------------------------------------------------------ telops
    def set_text_plus(self, item, text: str, preset: Optional[dict] = None) -> bool:
        comp = None
        try:
            comp = item.GetFusionCompByIndex(1)
        except Exception:  # noqa: BLE001
            comp = None
        if not comp:
            return False
        tool = None
        try:
            tool = comp.FindToolByID("TextPlus")
        except Exception:  # noqa: BLE001
            tool = None
        if not tool:
            try:
                tools = comp.GetToolList(False, "TextPlus") or {}
                tool = list(tools.values())[0] if tools else None
            except Exception:  # noqa: BLE001
                tool = None
        if not tool:
            return False
        try:
            comp.Lock()
        except Exception:  # noqa: BLE001
            pass
        try:
            tool.SetInput("StyledText", text)
            apply_preset_to_tool(tool, preset)
        finally:
            try:
                comp.Unlock()
            except Exception:  # noqa: BLE001
                pass
        return True

    def insert_telop(self, job: TelopJob, template, video_track: int, auto_free: bool, preset: Optional[dict] = None):
        """1 枚のテロップをタイムラインへ. template が None なら InsertFusionTitleIntoTimeline で代替."""
        if template is not None:
            track = self.pick_track("video", video_track, job.start, job.end, auto_free)
            item = self._append(template, job.duration, job.start, track, 1)
        else:
            self.set_playhead(job.start)
            item = self.timeline.InsertFusionTitleIntoTimeline("Text+")
            if not item:
                raise ResolveError("Text+ を挿入できませんでした (%s)" % self.frame_tc(job.start))
            track = video_track
        try:
            self._remember("video", track, int(item.GetStart()), int(item.GetEnd()))
        except Exception:  # noqa: BLE001
            pass
        if not self.set_text_plus(item, job.text, preset):
            self.log("警告: %s のテキストを設定できませんでした (Text+ が見つかりません)" % self.frame_tc(job.start))
        color = (preset or {}).get("ClipColor") if preset else None
        if color:
            try:
                item.SetClipColor(color)
            except Exception:  # noqa: BLE001
                pass
        try:
            item.SetName(job.text.replace("\n", " ")[:40])
        except Exception:  # noqa: BLE001
            pass
        return item

    # --------------------------------------------------------------------- sfx
    def insert_sfx(self, path: str, frame: int, audio_track: int, auto_free: bool, max_seconds: float = 0.0):
        clip = self.import_sfx(path)
        frames = self.clip_frames(clip)
        if not frames or frames < 1:
            frames = int(round(self.fps * 2))  # 長さ不明なら 2 秒
        if max_seconds and max_seconds > 0:
            frames = min(frames, max(1, int(round(max_seconds * self.fps))))
        track = self.pick_track("audio", audio_track, frame, frame + frames, auto_free)
        item = self._append(clip, frames, frame, track, 2)
        try:
            self._remember("audio", track, int(item.GetStart()), int(item.GetEnd()))
        except Exception:  # noqa: BLE001
            pass
        return item
