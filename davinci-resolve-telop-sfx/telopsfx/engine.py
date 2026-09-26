"""UI から呼ばれる実行ロジック (Resolve へは bridge 経由でのみ触る)."""

from dataclasses import dataclass, field
from typing import List, Optional

from .parsers import TelopLine, parse_auto
from .planner import (
    MODE_MARKERS,
    MODE_SEQUENTIAL,
    MODE_SUBTITLES,
    TelopJob,
    build_plan,
    build_plan_from_subtitles,
    build_plan_markers,
)
from .resolve_bridge import ResolveBridge, ResolveError
from .sfxlib import SfxFile, find_sfx


@dataclass
class TelopOptions:
    mode: int = MODE_SEQUENTIAL
    default_duration_sec: float = 3.0
    gap_sec: float = 0.0
    marker_color: str = "すべて"
    until_next_marker: bool = False
    use_marker_text: bool = False
    subtitle_track: int = 1
    video_track: int = 2
    auto_free_track: bool = True
    template_name: str = "Text+"
    preset: Optional[dict] = None
    telop_sfx_path: str = ""  # 全テロップ共通で鳴らす効果音 (空なら無し)
    audio_track: int = 2
    sfx_library: List[SfxFile] = field(default_factory=list)


@dataclass
class RunResult:
    telops: int = 0
    sfx: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


def plan_telops(bridge: ResolveBridge, lines: List[TelopLine], opt: TelopOptions):
    fps = bridge.fps
    start = bridge.timeline_start
    if opt.mode == MODE_SUBTITLES:
        subs = bridge.subtitle_items(opt.subtitle_track)
        if not subs:
            raise ResolveError("字幕トラック %d に字幕がありません" % opt.subtitle_track)
        return build_plan_from_subtitles(subs)
    if opt.mode == MODE_MARKERS:
        markers = bridge.markers()
        if not markers:
            raise ResolveError("タイムラインにマーカーがありません")
        if not lines and not opt.use_marker_text:
            raise ResolveError("原稿が空です")
        return build_plan_markers(
            lines, markers, fps, start, opt.default_duration_sec,
            color=opt.marker_color, until_next_marker=opt.until_next_marker,
            use_marker_text=opt.use_marker_text,
        )
    if not lines:
        raise ResolveError("原稿が空です")
    return build_plan(lines, fps, start, bridge.playhead_frame(), opt.default_duration_sec, opt.gap_sec)


def run_telops(bridge: ResolveBridge, jobs: List[TelopJob], opt: TelopOptions, log=None) -> RunResult:
    log = log or bridge.log
    result = RunResult()
    template = bridge.find_clip_by_name(opt.template_name)
    if template is None:
        result.warnings.append(
            "メディアプールに『%s』が見つからないため、InsertFusionTitleIntoTimeline で代替します "
            "(尺は Resolve 既定値、トラックは選択中のトラック)" % opt.template_name
        )
        log(result.warnings[-1])
    else:
        frames = bridge.clip_frames(template)
        longest = max((j.duration for j in jobs), default=0)
        if frames and longest > frames:
            result.warnings.append(
                "テンプレート『%s』の尺 (%d フレーム) より長いテロップがあります。"
                "その分は切り詰められます (README のテンプレート作成手順を参照)" % (opt.template_name, frames)
            )
            log(result.warnings[-1])
    for job in jobs:
        try:
            bridge.insert_telop(job, template, opt.video_track, opt.auto_free_track, opt.preset)
            result.telops += 1
            log("テロップ %s  %s" % (bridge.frame_tc(job.start), job.text.replace("\n", " ")[:30]))
        except Exception as exc:  # noqa: BLE001
            result.errors.append("%d行目 (%s): %s" % (job.line_no, job.text[:20], exc))
            log("エラー: " + result.errors[-1])
            continue
        sfx_path = None
        if job.sfx:
            found = find_sfx(opt.sfx_library, job.sfx)
            if found:
                sfx_path = found.path
            else:
                result.warnings.append("%d行目: 効果音 '%s' がライブラリにありません" % (job.line_no, job.sfx))
                log(result.warnings[-1])
        elif opt.telop_sfx_path:
            sfx_path = opt.telop_sfx_path
        if sfx_path:
            try:
                bridge.insert_sfx(sfx_path, job.start, opt.audio_track, opt.auto_free_track)
                result.sfx += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append("%d行目 効果音: %s" % (job.line_no, exc))
                log("エラー: " + result.errors[-1])
    return result


def run_sfx_at_playhead(bridge: ResolveBridge, path: str, audio_track: int, auto_free: bool, max_seconds=0.0):
    frame = bridge.playhead_frame()
    bridge.insert_sfx(path, frame, audio_track, auto_free, max_seconds)
    return frame


def run_sfx_at_markers(bridge: ResolveBridge, path: str, audio_track: int, auto_free: bool, color: str, log=None) -> RunResult:
    log = log or bridge.log
    result = RunResult()
    markers = [m for m in bridge.markers() if not color or color == "すべて" or m.color == color]
    if not markers:
        raise ResolveError("該当するマーカーがありません")
    for m in markers:
        frame = bridge.timeline_start + m.frame
        try:
            bridge.insert_sfx(path, frame, audio_track, auto_free)
            result.sfx += 1
            log("効果音 %s" % bridge.frame_tc(frame))
        except Exception as exc:  # noqa: BLE001
            result.errors.append("%s: %s" % (bridge.frame_tc(frame), exc))
            log("エラー: " + result.errors[-1])
    return result


def load_script_file(path: str) -> List[TelopLine]:
    with open(path, "r", encoding="utf-8-sig") as f:
        return parse_auto(f.read(), path)
