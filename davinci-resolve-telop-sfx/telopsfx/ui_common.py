"""UI 実装 (UIManager / tkinter) で共有する状態と処理."""

import os

from . import config as cfgmod
from .engine import TelopOptions, load_script_file, plan_telops, run_sfx_at_markers, run_sfx_at_playhead, run_telops
from .parsers import parse_auto
from .planner import MODE_MARKERS, MODE_SEQUENTIAL, MODE_SUBTITLES
from .presets import TEMPLATE_AS_IS, load_presets
from .resolve_bridge import ResolveBridge, ResolveError
from .sfxlib import filter_sfx, scan_folder

SOURCE_MODES = [
    ("再生ヘッドから順に並べる (行頭に時刻があればその位置)", MODE_SEQUENTIAL),
    ("マーカーの位置に 1 行ずつ置く", MODE_MARKERS),
    ("字幕トラックを Text+ に変換する", MODE_SUBTITLES),
]

HELP_TEXT = """原稿の書き方 (1 行 = テロップ 1 枚)
  こんにちは                 -> 順番に並べる
  こんにちは<TAB>2.5         -> 表示時間を個別指定 (秒)
  [00:12] こんにちは          -> 12 秒地点に置く (タイムライン先頭基準)
  00:12-00:15 こんにちは      -> 12〜15 秒
  こんにちは @ぴこん          -> 効果音 "ぴこん" (ライブラリ内の名前) を同時に鳴らす
  1 行目\\n2 行目              -> Text+ 内で改行
  # から始まる行と空行は無視。SRT を貼り付けてもそのまま使えます。"""


class Session:
    """UI から独立した「状態 + 操作」. どちらの UI もこれを叩くだけ."""

    def __init__(self, resolve, log):
        self.log = log
        self.cfg = cfgmod.load_config()
        self.presets = load_presets()
        self.bridge = ResolveBridge(resolve, log)
        self.sfx_items = []
        self.rescan_sfx()

    # ----------------------------------------------------------- persistence
    def save(self):
        try:
            cfgmod.save_config(self.cfg)
        except OSError as exc:
            self.log("設定の保存に失敗: %s" % exc)

    # ------------------------------------------------------------------ sfx
    def rescan_sfx(self):
        self.sfx_items = scan_folder(self.cfg.get("sfx_folder", ""), self.cfg.get("favorites", []))
        return self.sfx_items

    def set_sfx_folder(self, folder):
        self.cfg["sfx_folder"] = folder or ""
        self.save()
        return self.rescan_sfx()

    def search_sfx(self, query, favorites_only=False):
        return filter_sfx(self.sfx_items, query, favorites_only)

    def toggle_favorite(self, path):
        favs = list(self.cfg.get("favorites", []))
        if path in favs:
            favs.remove(path)
        else:
            favs.append(path)
        self.cfg["favorites"] = favs
        self.save()
        for it in self.sfx_items:
            it.favorite = it.path in favs
        return path in favs

    def sfx_by_path(self, path):
        for it in self.sfx_items:
            if it.path == path:
                return it
        return None

    def insert_sfx_at_playhead(self, path):
        self.bridge.refresh()
        frame = run_sfx_at_playhead(
            self.bridge, path, int(self.cfg.get("audio_track", 2)), bool(self.cfg.get("auto_free_track", True))
        )
        self.cfg["quick_sfx"] = path
        self.save()
        self.log("効果音 %s → %s" % (os.path.basename(path), self.bridge.frame_tc(frame)))

    def insert_sfx_at_markers(self, path, color):
        self.bridge.refresh()
        res = run_sfx_at_markers(
            self.bridge, path, int(self.cfg.get("audio_track", 2)),
            bool(self.cfg.get("auto_free_track", True)), color, self.log,
        )
        self.log("効果音を %d 箇所に挿入しました" % res.sfx)
        return res

    # ---------------------------------------------------------------- telops
    def parse_text(self, text):
        return parse_auto(text or "")

    def load_file(self, path):
        return load_script_file(path)

    def build_options(self, mode_index, duration, gap, preset_name, video_track, audio_track,
                      auto_free, marker_color, until_next_marker, use_marker_text,
                      subtitle_track, telop_sfx_path, template_name):
        preset = self.presets.get(preset_name)
        if preset_name == TEMPLATE_AS_IS:
            preset = None
        return TelopOptions(
            mode=SOURCE_MODES[mode_index][1],
            default_duration_sec=float(duration),
            gap_sec=float(gap),
            marker_color=marker_color or "すべて",
            until_next_marker=bool(until_next_marker),
            use_marker_text=bool(use_marker_text),
            subtitle_track=int(subtitle_track),
            video_track=int(video_track),
            auto_free_track=bool(auto_free),
            template_name=template_name or "Text+",
            preset=preset,
            telop_sfx_path=telop_sfx_path or "",
            audio_track=int(audio_track),
            sfx_library=self.sfx_items,
        )

    def preview(self, text, opt):
        """挿入せずに配置計画だけ返す."""
        self.bridge.refresh()
        lines = self.parse_text(text)
        jobs, warnings = plan_telops(self.bridge, lines, opt)
        return jobs, warnings

    def insert_telops(self, text, opt):
        self.bridge.refresh()
        lines = self.parse_text(text)
        jobs, warnings = plan_telops(self.bridge, lines, opt)
        for w in warnings:
            self.log("注意: " + w)
        if not jobs:
            raise ResolveError("配置できるテロップがありません")
        self.log("%d 枚のテロップを挿入します (fps=%s, timeline=%s)" % (len(jobs), self.bridge.fps, self.bridge.timeline_name()))
        res = run_telops(self.bridge, jobs, opt, self.log)
        res.warnings = warnings + res.warnings
        self.log("完了: テロップ %d 枚, 効果音 %d 個, エラー %d 件" % (res.telops, res.sfx, len(res.errors)))
        return res

    def marker_colors(self):
        try:
            self.bridge.refresh()
            return ["すべて"] + self.bridge.marker_colors()
        except Exception:  # noqa: BLE001
            return ["すべて"]

    def template_candidates(self):
        try:
            self.bridge.refresh()
            return self.bridge.template_candidates()
        except Exception:  # noqa: BLE001
            return []
