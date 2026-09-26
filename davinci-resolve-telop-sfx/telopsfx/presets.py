"""テロップのスタイルプリセット (Text+ の入力値)."""

import json
import os
import platform

from .config import user_dir

# Text+ (TextPlus) の主要な入力名:
#   StyledText: 本文 / Font, Style, Size / Red1..Alpha1: 文字色
#   Enabled2, Red2.., Thickness2: アウトライン / Enabled3, Red3..: シャドウ
#   Enabled4, Red4..Alpha4, ElementShape4, ExtendHorizontal4, ExtendVertical4: 背景ボックス
#   Center: 位置 {x, y} (0-1, 左下原点)

TEMPLATE_AS_IS = "テンプレートのまま"


def default_japanese_font():
    return default_japanese_font_styles()[0]


def default_japanese_font_styles():
    """(font, bold_style, regular_style). Style は Text+ がそのフォントに対して実際に列挙する名前でなければ効かない."""
    system = platform.system()
    if system == "Darwin":
        # macOS の Hiragino Sans は W0..W9 のウェイト名しか持たない (Bold/Regular は存在しない)
        return ("Hiragino Sans", "W6", "W3")
    if system == "Windows":
        return ("Yu Gothic UI", "Bold", "Regular")
    return ("Noto Sans CJK JP", "Bold", "Regular")


def builtin_presets():
    font, bold, regular = default_japanese_font_styles()
    return {
        "標準 (白・黒フチ・下部)": {
            "Font": font, "Style": bold, "Size": 0.075,
            "Red1": 1.0, "Green1": 1.0, "Blue1": 1.0, "Alpha1": 1.0,
            "Enabled2": 1, "Red2": 0.0, "Green2": 0.0, "Blue2": 0.0, "Thickness2": 0.05,
            "Enabled4": 0,
            "Center": [0.5, 0.12],
            "ClipColor": "Yellow",
        },
        "強調 (黄・黒フチ・下部)": {
            "Font": font, "Style": bold, "Size": 0.085,
            "Red1": 1.0, "Green1": 0.9, "Blue1": 0.1, "Alpha1": 1.0,
            "Enabled2": 1, "Red2": 0.05, "Green2": 0.05, "Blue2": 0.05, "Thickness2": 0.06,
            "Enabled4": 0,
            "Center": [0.5, 0.12],
            "ClipColor": "Orange",
        },
        "帯付き (白文字・黒帯・下部)": {
            "Font": font, "Style": bold, "Size": 0.07,
            "Red1": 1.0, "Green1": 1.0, "Blue1": 1.0, "Alpha1": 1.0,
            "Enabled2": 0,
            "Enabled4": 1, "ElementShape4": 2,
            "Red4": 0.0, "Green4": 0.0, "Blue4": 0.0, "Alpha4": 0.75,
            "ExtendHorizontal4": 0.3, "ExtendVertical4": 0.2,
            "Center": [0.5, 0.12],
            "ClipColor": "Yellow",
        },
        "見出し (中央・大)": {
            "Font": font, "Style": bold, "Size": 0.12,
            "Red1": 1.0, "Green1": 1.0, "Blue1": 1.0, "Alpha1": 1.0,
            "Enabled2": 1, "Red2": 0.0, "Green2": 0.0, "Blue2": 0.0, "Thickness2": 0.05,
            "Center": [0.5, 0.5],
            "ClipColor": "Pink",
        },
        "左上キャプション (小)": {
            "Font": font, "Style": regular, "Size": 0.045,
            "Red1": 1.0, "Green1": 1.0, "Blue1": 1.0, "Alpha1": 1.0,
            "Enabled2": 1, "Red2": 0.0, "Green2": 0.0, "Blue2": 0.0, "Thickness2": 0.04,
            "Center": [0.2, 0.88],
            "ClipColor": "Teal",
        },
    }


def user_presets_path():
    return os.path.join(user_dir(), "presets.json")


def load_presets():
    """組み込み + ユーザー定義 (~/.telopsfx/presets.json) をマージして返す (順序保持)."""
    presets = {TEMPLATE_AS_IS: None}
    presets.update(builtin_presets())
    path = user_presets_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f)
            if isinstance(user, dict):
                presets.update(user)
        except (OSError, ValueError):
            pass
    return presets


def write_example_user_presets(force=False):
    """ユーザーが編集する叩き台として presets.json を書き出す."""
    path = user_presets_path()
    if os.path.exists(path) and not force:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    example = {"マイプリセット (例)": builtin_presets()["標準 (白・黒フチ・下部)"]}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(example, f, ensure_ascii=False, indent=2)
    return path


def apply_preset_to_tool(tool, preset):
    """Text+ ツールへプリセット値を流し込む. 未知のキーは無視される."""
    if not preset:
        return
    for key, value in preset.items():
        if key == "ClipColor":
            continue
        try:
            if key == "Center" and isinstance(value, (list, tuple)):
                tool.SetInput("Center", {1: float(value[0]), 2: float(value[1])})
            else:
                tool.SetInput(key, value)
        except Exception:  # noqa: BLE001 - Resolve 側の失敗は握りつぶして続行
            pass
