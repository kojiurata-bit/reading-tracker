# -*- coding: utf-8 -*-
# TelopSFX launcher. 本体 (telopsfx パッケージ) を探して読み込む.
import os
import sys


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


_root = _find_package_root()
if _root is None:
    raise RuntimeError("telopsfx パッケージが見つかりません。install.py を実行してください")
if _root not in sys.path:
    sys.path.insert(0, _root)
for _name in [m for m in list(sys.modules) if m == "telopsfx" or m.startswith("telopsfx.")]:
    del sys.modules[_name]  # 更新した本体を毎回読み直す

import telopsfx.app  # noqa: E402

telopsfx.app.run_panel(globals())
