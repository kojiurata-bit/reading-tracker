# -*- coding: utf-8 -*-
# TelopSFX launcher. 本体 (telopsfx パッケージ) を探して読み込む.
import os
import sys

if sys.version_info < (3, 7):
    raise RuntimeError("TelopSFX は Python 3.7 以上が必要です (現在 %s)" % sys.version.split()[0])


def _find_package_root():
    paths = []
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        paths += [os.path.join(here, "..", ".."), here]
    except NameError:
        pass
    if os.environ.get("TELOPSFX_HOME"):
        paths.append(os.environ["TELOPSFX_HOME"])
    paths.append(os.path.join(os.path.expanduser("~"), ".telopsfx", "lib"))
    for p in paths:
        if os.path.isfile(os.path.join(p, "telopsfx", "app.py")):
            return os.path.abspath(p)
    return None


def _report(message):
    # app._report と同じ: Console に出しつつ、可能なら tkinter でダイアログも出す
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


def _main():
    import traceback

    _root = _find_package_root()
    if _root is None:
        _report("telopsfx パッケージが見つかりません。install.py を実行してください "
                "(探した場所: ~/.telopsfx/lib, TELOPSFX_HOME)")
        return
    if _root not in sys.path:
        sys.path.insert(0, _root)
    for _name in [m for m in list(sys.modules) if m == "telopsfx" or m.startswith("telopsfx.")]:
        del sys.modules[_name]  # 更新した本体を毎回読み直す
    try:
        import telopsfx.app
    except Exception:  # noqa: BLE001  (ImportError / SyntaxError on old Python など)
        _report("TelopSFX 本体の読み込みに失敗しました (Python %s, root=%s):\n%s"
                % (sys.version.split()[0], _root, traceback.format_exc()))
        return
    telopsfx.app.run_panel(globals())


_main()
