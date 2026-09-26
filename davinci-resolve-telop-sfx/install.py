#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TelopSFX を DaVinci Resolve のスクリプトメニューにインストールする.

  python3 install.py            -> インストール
  python3 install.py --uninstall
"""

import os
import platform
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHERS = os.path.join(HERE, "resolve_scripts", "Utility")
PACKAGE = os.path.join(HERE, "telopsfx")
LIB_DIR = os.path.join(os.path.expanduser("~"), ".telopsfx", "lib")


def scripts_utility_dir():
    system = platform.system()
    home = os.path.expanduser("~")
    if system == "Darwin":
        return os.path.join(home, "Library", "Application Support", "Blackmagic Design",
                            "DaVinci Resolve", "Fusion", "Scripts", "Utility")
    if system == "Windows":
        appdata = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
        return os.path.join(appdata, "Blackmagic Design", "DaVinci Resolve", "Support",
                            "Fusion", "Scripts", "Utility")
    return os.path.join(home, ".local", "share", "DaVinciResolve", "Fusion", "Scripts", "Utility")


def launcher_files():
    return [f for f in os.listdir(LAUNCHERS) if f.endswith(".py")]


def install():
    target = scripts_utility_dir()
    os.makedirs(target, exist_ok=True)
    for fn in launcher_files():
        shutil.copy2(os.path.join(LAUNCHERS, fn), os.path.join(target, fn))
        print("  script  ->", os.path.join(target, fn))
    dest = os.path.join(LIB_DIR, "telopsfx")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(PACKAGE, dest, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    print("  package ->", dest)
    print("\n完了。DaVinci Resolve を再起動 (または Workspace > Scripts を開き直し) すると、")
    print("Workspace > Scripts に『TelopSFX - Panel』などが表示されます。")


def uninstall():
    target = scripts_utility_dir()
    for fn in launcher_files():
        path = os.path.join(target, fn)
        if os.path.exists(path):
            os.remove(path)
            print("  removed", path)
    dest = os.path.join(LIB_DIR, "telopsfx")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
        print("  removed", dest)
    print("アンインストール完了 (設定ファイル ~/.telopsfx/config.json は残しています)")


if __name__ == "__main__":
    if sys.version_info < (3, 6):
        sys.exit("Python 3.6 以上が必要です")
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
