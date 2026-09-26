import os
import platform

import install


def test_app_store_detection(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    real_isdir = os.path.isdir
    monkeypatch.setattr(os.path, "isdir",
                        lambda p: p.endswith("DaVinciResolveAppStore") or real_isdir(p))
    assert install.app_store_resolve_installed() is True
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert install.app_store_resolve_installed() is False


def test_install_warns_about_app_store(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(install, "scripts_utility_dir", lambda: str(tmp_path / "Utility"))
    monkeypatch.setattr(install, "LIB_DIR", str(tmp_path / "lib"))
    monkeypatch.setattr(install, "app_store_resolve_installed", lambda: True)
    install.install()
    out = capsys.readouterr().out
    assert "App Store" in out
    assert os.path.isfile(str(tmp_path / "lib" / "telopsfx" / "app.py"))
