"""エントリポイント. Resolve のスクリプトメニューから呼ばれる."""

import os
import traceback


def _resolve_objects(globals_dict):
    """スクリプト実行時のグローバル (resolve / fusion / bmd) を集める. 無ければ API 経由で接続."""
    resolve = globals_dict.get("resolve")
    fusion = globals_dict.get("fusion")
    bmd = globals_dict.get("bmd")
    if resolve is None:
        try:
            import DaVinciResolveScript as dvr  # type: ignore

            resolve = dvr.scriptapp("Resolve")
        except Exception:  # noqa: BLE001
            resolve = None
    if resolve is not None and fusion is None:
        try:
            fusion = resolve.Fusion()
        except Exception:  # noqa: BLE001
            fusion = None
    if bmd is None:
        try:
            import fusionscript as bmd  # type: ignore
        except Exception:  # noqa: BLE001
            bmd = None
    return resolve, fusion, bmd


def _ui_manager_available(fusion, bmd):
    if fusion is None or bmd is None:
        return False
    try:
        ui = fusion.UIManager
        if not ui:
            return False
        disp = bmd.UIDispatcher(ui)
        return bool(disp)
    except Exception:  # noqa: BLE001
        return False


def _report(message):
    print(message)
    try:
        import tkinter
        from tkinter import messagebox

        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror("TelopSFX", message)
        root.destroy()
    except Exception:  # noqa: BLE001
        pass


def run_panel(globals_dict):
    resolve, fusion, bmd = _resolve_objects(globals_dict)
    if resolve is None:
        _report("DaVinci Resolve に接続できません。Resolve の Workspace > Scripts メニューから実行してください。")
        return
    force_tk = os.environ.get("TELOPSFX_UI", "").lower() == "tk"
    try:
        if not force_tk and _ui_manager_available(fusion, bmd):
            from .ui_uimanager import run_panel as run_ui

            run_ui(resolve, fusion, bmd)
        else:
            from .ui_tk import run_panel as run_tk

            run_tk(resolve)
    except Exception:  # noqa: BLE001
        _report("TelopSFX でエラーが発生しました:\n" + traceback.format_exc())


def quick_telop(globals_dict, text=None):
    """クリップボード (または引数) のテキストを再生ヘッドに 1 枚だけ挿入する."""
    from . import config as cfgmod
    from .engine import TelopOptions, run_telops
    from .parsers import parse_lines
    from .planner import build_plan
    from .presets import TEMPLATE_AS_IS, load_presets
    from .resolve_bridge import ResolveBridge

    resolve, _, _ = _resolve_objects(globals_dict)
    if resolve is None:
        _report("DaVinci Resolve に接続できません")
        return
    if text is None:
        try:
            import tkinter

            root = tkinter.Tk()
            root.withdraw()
            text = root.clipboard_get()
            root.destroy()
        except Exception:  # noqa: BLE001
            text = ""
    lines = parse_lines(text or "")
    if not lines:
        _report("クリップボードにテロップ文字列がありません (先にテキストをコピーしてください)")
        return
    cfg = cfgmod.load_config()
    presets = load_presets()
    preset = presets.get(cfg.get("preset")) if cfg.get("preset") != TEMPLATE_AS_IS else None
    try:
        bridge = ResolveBridge(resolve, print)
        jobs, _ = build_plan(lines[:1], bridge.fps, bridge.timeline_start, bridge.playhead_frame(),
                             float(cfg.get("default_duration_sec", 3.0)))
        opt = TelopOptions(
            default_duration_sec=float(cfg.get("default_duration_sec", 3.0)),
            video_track=int(cfg.get("video_track", 2)), audio_track=int(cfg.get("audio_track", 2)),
            auto_free_track=bool(cfg.get("auto_free_track", True)),
            template_name=cfg.get("template_name", "Text+"), preset=preset,
            telop_sfx_path=cfg.get("telop_sfx", "") if cfg.get("telop_sfx_enabled") else "",
        )
        res = run_telops(bridge, jobs, opt, print)
        if res.errors:
            _report("\n".join(res.errors))
    except Exception:  # noqa: BLE001
        _report("TelopSFX でエラーが発生しました:\n" + traceback.format_exc())


def quick_sfx(globals_dict):
    """設定済みの「クイック効果音」(最後に挿入した効果音) を再生ヘッドに挿入する."""
    from . import config as cfgmod
    from .engine import run_sfx_at_playhead
    from .resolve_bridge import ResolveBridge

    resolve, _, _ = _resolve_objects(globals_dict)
    if resolve is None:
        _report("DaVinci Resolve に接続できません")
        return
    cfg = cfgmod.load_config()
    path = cfg.get("quick_sfx") or ""
    if not path or not os.path.exists(path):
        _report("クイック効果音が未設定です。先にパネルから効果音を 1 度挿入してください。")
        return
    try:
        bridge = ResolveBridge(resolve, print)
        run_sfx_at_playhead(bridge, path, int(cfg.get("audio_track", 2)), bool(cfg.get("auto_free_track", True)))
    except Exception:  # noqa: BLE001
        _report("TelopSFX でエラーが発生しました:\n" + traceback.format_exc())
