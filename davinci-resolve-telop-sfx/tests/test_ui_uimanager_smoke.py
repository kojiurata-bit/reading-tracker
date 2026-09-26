"""UIManager パネルを偽の UIManager で組み立て、イベントハンドラを一通り叩くスモークテスト."""

import pytest

from fake_resolve import FakeResolve
from telopsfx import ui_uimanager


class _Proxy(dict):
    """Text[0] = ... / ColumnWidth[0] = ... のような添字代入を受ける."""


class FakeElement:
    def __init__(self, attrs=None, children=None):
        attrs = attrs or {}
        self.attrs = dict(attrs)
        self.children = children or []
        self.ID = attrs.get("ID")
        self.Text = attrs.get("Text", "")
        self.PlainText = attrs.get("PlainText", "")
        self.Checked = attrs.get("Checked", False)
        self.Value = attrs.get("Value", 0)
        self.CurrentIndex = 0
        self.items = []
        self.rows = []
        self.ColumnWidth = _Proxy()
        self._appended = []

    # ComboBox / TabBar
    def AddItems(self, items):
        self.items.extend(items)

    def AddItem(self, item):
        self.items.append(item)

    def AddTab(self, name):
        self.items.append(name)

    def Clear(self):
        self.items = []
        self.rows = []

    @property
    def CurrentText(self):
        return self.items[self.CurrentIndex] if 0 <= self.CurrentIndex < len(self.items) else ""

    # Tree
    def SetHeaderLabels(self, labels):
        self.headers = labels

    def NewItem(self):
        row = FakeElement()
        row.Text = _Proxy()
        return row

    def AddTopLevelItem(self, row):
        self.rows.append(row)

    def CurrentItem(self):
        return self.rows[0] if self.rows else None

    # TextEdit
    def Append(self, text):
        self._appended.append(text)


class FakeUI:
    def __getattr__(self, name):
        def factory(*args):
            attrs, children = {}, []
            for a in args:
                if isinstance(a, dict):
                    attrs = a
                elif isinstance(a, list):
                    children = a
            return FakeElement(attrs, children)
        return factory


class _EventTarget:
    def __init__(self):
        self.handlers = {}

    def __setattr__(self, name, value):
        if name == "handlers":
            object.__setattr__(self, name, value)
        else:
            self.handlers[name] = value


class _On:
    def __init__(self):
        object.__setattr__(self, "targets", {})

    def __getattr__(self, name):
        return self.targets.setdefault(name, _EventTarget())


class FakeWindow:
    def __init__(self, attrs, layout):
        self.attrs = attrs
        self.layout = layout
        self.On = _On()
        g = attrs.get("Geometry") or [0, 0, 0, 0]
        self.Geometry = {1: g[0], 2: g[1], 3: g[2], 4: g[3]}  # real Resolve returns a 1-based dict
        self.shown = False

    def _collect(self, el, out):
        if el.ID:
            out[el.ID] = el
        for c in el.children:
            self._collect(c, out)
        return out

    def GetItems(self):
        return self._collect(self.layout, {})

    def Show(self):
        self.shown = True

    def Hide(self):
        self.shown = False


class FakeDispatcher:
    def __init__(self, ui):
        self.ui = ui
        self.loops = 0

    def AddWindow(self, attrs, layout):
        return FakeWindow(attrs, layout)

    def RunLoop(self):
        self.loops += 1

    def ExitLoop(self):
        pass


class FakeFusion:
    UIManager = FakeUI()

    def RequestDir(self, *a, **k):
        self.dir_calls = getattr(self, "dir_calls", 0) + 1
        return None  # cancelled

    def RequestFile(self, *a, **k):
        self.file_calls = getattr(self, "file_calls", 0) + 1
        return None  # cancelled


class FakeBmd:
    @staticmethod
    def UIDispatcher(ui):
        return FakeDispatcher(ui)


@pytest.fixture
def panel(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("os.path.expanduser", lambda p: p.replace("~", str(tmp_path)))
    sfx = tmp_path / "sfx"
    sfx.mkdir()
    (sfx / "pikon.wav").write_bytes(b"")
    fake = FakeResolve()
    fake.add_template()
    fake.timeline.markers = {10: {"color": "Blue", "name": "Marker 1", "note": "", "duration": 1}}
    p = ui_uimanager.UIManagerPanel(fake, FakeFusion(), FakeBmd())
    p.fake = fake
    p.itm["SfxFolder"].Text = str(sfx)
    p._on_rescan(None)
    return p


def test_panel_builds_and_populates(panel):
    itm = panel.itm
    assert itm["Tabs"].items == ["テロップ", "効果音"]
    assert len(itm["Mode"].items) == 3
    assert "テンプレートのまま" in itm["Preset"].items
    assert "Text+" in itm["Template"].items
    assert itm["MarkerColor"].items == ["すべて", "Blue"]
    assert [r.Text[1] for r in itm["SfxList"].rows] == ["pikon.wav"]
    handlers = panel.win.On.targets
    assert "Clicked" in handlers["BtnInsert"].handlers
    assert "Close" in handlers[ui_uimanager.WIN_ID].handlers


def test_panel_insert_and_sfx_flow(panel):
    itm = panel.itm
    itm["Script"].PlainText = "こんにちは\n世界\t1"
    itm["TelopSfxOn"].Checked = True
    itm["VideoTrack"].Value = 2
    panel._run(preview=True)
    assert len(panel.fake.timeline.tracks["video"].get(2, [])) == 0
    panel._run(preview=False)
    v2 = panel.fake.timeline.tracks["video"][2]
    assert [i.comp.tool.inputs["StyledText"] for i in v2] == ["こんにちは", "世界"]
    assert len(panel.fake.timeline.tracks["audio"][2]) == 2  # 各テロップに効果音
    panel._on_sfx_playhead()
    # 再生ヘッド位置 (A2 は既に使用中) → 空いている A3 に逃げる
    assert len(panel.fake.timeline.tracks["audio"][2]) == 2
    assert len(panel.fake.timeline.tracks["audio"][3]) == 1
    panel._on_fav(None)
    assert itm["SfxList"].rows[0].Text[0] == "★"
    panel._on_sfx_markers(None)
    all_audio = [i for t in panel.fake.timeline.tracks["audio"].values() for i in t]
    assert any(i.start == panel.fake.timeline.start_frame + 10 for i in all_audio)
    panel._on_close(None)
    assert panel.session.cfg["last_text"] == "こんにちは\n世界\t1"
    assert panel.session.cfg["ui_geometry"] == [200, 120, 760, 720]  # 1 始まり dict から変換される
    assert panel.session.cfg["quick_sfx"].endswith("pikon.wav")
    log = "\n".join(itm["Log"]._appended)
    assert "完了" in log and "エラー" not in log.replace("エラー 0 件", "")


def test_panel_run(panel):
    panel.run()
    assert panel.disp.loops == 1


def test_request_path_cancel_does_not_fall_back(panel, monkeypatch):
    import sys
    import types

    def boom(*a, **k):
        raise AssertionError("tkinter dialog must not be opened")

    fake_tk = types.ModuleType("tkinter")
    fake_tk.Tk = boom
    monkeypatch.setitem(sys.modules, "tkinter", fake_tk)
    assert panel._request_path(directory=False) is None
    assert panel._request_path(directory=True) is None
    assert panel.fusion.file_calls == 1 and panel.fusion.dir_calls == 1
    panel._on_load(None)  # キャンセル -> 何もしない
    assert "ダイアログを開けません" not in "\n".join(panel.itm["Log"]._appended)


def test_load_reads_cp932_file(panel, tmp_path):
    path = tmp_path / "script.txt"
    path.write_bytes("こんにちは\n世界\n".encode("cp932"))
    panel.fusion.RequestFile = lambda *a, **k: str(path)
    panel._on_load(None)
    assert panel.itm["Script"].PlainText == "こんにちは\n世界\n"


def test_guarded_handler_logs_exception(panel):
    handlers = panel.win.On.targets
    panel._request_path = lambda directory=False: (_ for _ in ()).throw(RuntimeError("boom"))
    handlers["BtnLoad"].handlers["Clicked"](None)  # 例外はログに流れて落ちない
    assert any("RuntimeError: boom" in m for m in panel.itm["Log"]._appended)


def test_tab_switch_keeps_marker_color_selection(panel):
    itm = panel.itm
    itm["MarkerColor"].CurrentIndex = 1  # "Blue"
    panel._on_tab({"Index": 1})
    panel._on_tab({"Index": 0})
    assert itm["MarkerColor"].CurrentText == "Blue"
    assert itm["Stack"].CurrentIndex == 0


def test_sfx_markers_uses_auto_free_checkbox(panel):
    itm = panel.itm
    itm["AutoFree"].Checked = False
    panel._on_sfx_markers(None)
    assert panel.session.cfg["auto_free_track"] is False
    itm["AutoFree"].Checked = True
    panel._on_sfx_markers(None)
    assert panel.session.cfg["auto_free_track"] is True
