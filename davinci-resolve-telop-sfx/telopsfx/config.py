"""ユーザー設定 (~/.telopsfx/config.json)."""

import json
import os

DEFAULTS = {
    "template_name": "Text+",
    "video_track": 2,
    "audio_track": 2,
    "auto_free_track": True,
    "default_duration_sec": 3.0,
    "gap_sec": 0.0,
    "preset": "テンプレートのまま",
    "sfx_folder": "",
    "favorites": [],
    "quick_sfx": "",
    "telop_sfx": "",
    "telop_sfx_enabled": False,
    "marker_color": "すべて",
    "subtitle_track": 1,
    "last_source_mode": 0,
    "last_text": "",
    "ui_geometry": [200, 120, 760, 720],
}


def user_dir():
    return os.path.join(os.path.expanduser("~"), ".telopsfx")


def config_path():
    return os.path.join(user_dir(), "config.json")


def load_config():
    cfg = dict(DEFAULTS)
    path = config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                cfg.update(data)
        except (OSError, ValueError):
            pass
    return cfg


def save_config(cfg):
    os.makedirs(user_dir(), exist_ok=True)
    tmp = config_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, config_path())
