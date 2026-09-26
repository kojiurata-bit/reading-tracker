import platform

from telopsfx import presets


def _styles(monkeypatch, system):
    monkeypatch.setattr(platform, "system", lambda: system)
    return {p["Style"] for p in presets.builtin_presets().values()}


def test_mac_presets_use_hiragino_weights(monkeypatch):
    weights = {"W%d" % i for i in range(10)}
    assert _styles(monkeypatch, "Darwin") <= weights
    assert presets.default_japanese_font() == "Hiragino Sans"


def test_windows_and_linux_presets_use_bold_regular(monkeypatch):
    for system in ("Windows", "Linux"):
        assert _styles(monkeypatch, system) <= {"Bold", "Regular"}
