"""DaVinci Resolve Studio 用パネル (Fusion UIManager)."""


from .presets import write_example_user_presets
from .resolve_bridge import ResolveError
from .ui_common import HELP_TEXT, SOURCE_MODES, Session

WIN_ID = "TelopSFXWin"


class UIManagerPanel:
    def __init__(self, resolve, fusion, bmd):
        self.fusion = fusion
        self.ui = fusion.UIManager
        self.disp = bmd.UIDispatcher(self.ui)
        self.session = Session(resolve, self.log)
        self.itm = None
        self._pending_log = []
        self._sfx_rows = []
        self.win = self._build()
        self.itm = self.win.GetItems()
        self._populate()
        self._bind()

    # ------------------------------------------------------------------ log
    def log(self, msg):
        if self.itm is None:
            self._pending_log.append(msg)
            return
        try:
            self.itm["Log"].Append(msg)
        except Exception:  # noqa: BLE001
            try:
                self.itm["Log"].PlainText = (self.itm["Log"].PlainText or "") + msg + "\n"
            except Exception:  # noqa: BLE001
                pass

    # ---------------------------------------------------------------- build
    def _build(self):
        ui = self.ui
        cfg = self.session.cfg
        geo = cfg.get("ui_geometry") or [200, 120, 760, 720]
        telop_page = ui.VGroup({"Spacing": 6}, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "原稿 (1 行 = 1 テロップ)", "Weight": 1}),
                ui.Button({"ID": "BtnLoad", "Text": "ファイル読込 (txt / srt)", "Weight": 0}),
                ui.Button({"ID": "BtnHelp", "Text": "書き方", "Weight": 0}),
            ]),
            ui.TextEdit({"ID": "Script", "PlainText": cfg.get("last_text", ""), "Weight": 1,
                         "PlaceholderText": "ここに原稿を貼り付け (SRT もそのまま可)"}),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "配置", "Weight": 0}),
                ui.ComboBox({"ID": "Mode", "Weight": 1}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "表示秒", "Weight": 0}),
                ui.DoubleSpinBox({"ID": "Duration", "Minimum": 0.1, "Maximum": 3600, "Decimals": 2,
                                  "SingleStep": 0.5, "Value": float(cfg.get("default_duration_sec", 3.0))}),
                ui.Label({"Text": "間隔秒", "Weight": 0}),
                ui.DoubleSpinBox({"ID": "Gap", "Minimum": 0, "Maximum": 600, "Decimals": 2,
                                  "SingleStep": 0.5, "Value": float(cfg.get("gap_sec", 0.0))}),
                ui.Label({"Text": "V", "Weight": 0}),
                ui.SpinBox({"ID": "VideoTrack", "Minimum": 1, "Maximum": 99, "Value": int(cfg.get("video_track", 2))}),
                ui.CheckBox({"ID": "AutoFree", "Text": "重なるなら上のトラックへ", "Checked": bool(cfg.get("auto_free_track", True))}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "マーカー色", "Weight": 0}),
                ui.ComboBox({"ID": "MarkerColor", "Weight": 1}),
                ui.CheckBox({"ID": "UntilNext", "Text": "次のマーカーまで表示", "Checked": False}),
                ui.CheckBox({"ID": "MarkerText", "Text": "マーカー名/メモを原稿にする", "Checked": False}),
                ui.Label({"Text": "字幕Tr", "Weight": 0}),
                ui.SpinBox({"ID": "SubTrack", "Minimum": 1, "Maximum": 20, "Value": int(cfg.get("subtitle_track", 1))}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "スタイル", "Weight": 0}),
                ui.ComboBox({"ID": "Preset", "Weight": 1}),
                ui.Button({"ID": "BtnPresetFile", "Text": "プリセット編集…", "Weight": 0}),
                ui.Label({"Text": "テンプレ", "Weight": 0}),
                ui.ComboBox({"ID": "Template", "Editable": True, "Weight": 1}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.CheckBox({"ID": "TelopSfxOn", "Text": "各テロップに効果音", "Checked": bool(cfg.get("telop_sfx_enabled", False))}),
                ui.ComboBox({"ID": "TelopSfx", "Weight": 1}),
                ui.Label({"Text": "A", "Weight": 0}),
                ui.SpinBox({"ID": "AudioTrack", "Minimum": 1, "Maximum": 99, "Value": int(cfg.get("audio_track", 2))}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Button({"ID": "BtnPreview", "Text": "配置を確認 (挿入しない)"}),
                ui.Button({"ID": "BtnInsert", "Text": "▶ テロップを挿入"}),
            ]),
        ])
        sfx_page = ui.VGroup({"Spacing": 6}, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "フォルダ", "Weight": 0}),
                ui.LineEdit({"ID": "SfxFolder", "Text": cfg.get("sfx_folder", ""), "Weight": 1,
                             "PlaceholderText": "効果音が入っているフォルダ (サブフォルダも可)"}),
                ui.Button({"ID": "BtnFolder", "Text": "選択…", "Weight": 0}),
                ui.Button({"ID": "BtnRescan", "Text": "再読込", "Weight": 0}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.LineEdit({"ID": "SfxQuery", "PlaceholderText": "検索 (スペース区切りで AND)", "Weight": 1,
                             "Events": {"TextChanged": True}}),
                ui.CheckBox({"ID": "FavOnly", "Text": "★のみ", "Checked": False, "Events": {"Clicked": True}}),
            ]),
            ui.Tree({"ID": "SfxList", "Weight": 1, "AlternatingRowColors": True,
                     "Events": {"ItemDoubleClicked": True, "ItemClicked": True, "CurrentItemChanged": True}}),
            ui.HGroup({"Weight": 0}, [
                ui.Button({"ID": "BtnSfxPlayhead", "Text": "▶ 再生ヘッドに挿入 (ダブルクリックでも)"}),
                ui.Button({"ID": "BtnFav", "Text": "★ お気に入り切替", "Weight": 0}),
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Button({"ID": "BtnSfxMarkers", "Text": "マーカー位置に一括挿入", "Weight": 0}),
                ui.Label({"Text": "マーカー色", "Weight": 0}),
                ui.ComboBox({"ID": "SfxMarkerColor", "Weight": 1}),
                ui.Label({"Text": "A", "Weight": 0}),
                ui.SpinBox({"ID": "AudioTrack2", "Minimum": 1, "Maximum": 99, "Value": int(cfg.get("audio_track", 2))}),
            ]),
        ])
        layout = ui.VGroup({"Spacing": 6}, [
            ui.TabBar({"ID": "Tabs", "Weight": 0}),
            ui.Stack({"ID": "Stack", "Weight": 1}, [telop_page, sfx_page]),
            ui.Label({"Text": "ログ", "Weight": 0}),
            ui.TextEdit({"ID": "Log", "ReadOnly": True, "Weight": 0, "MinimumSize": [100, 110], "MaximumSize": [4000, 160]}),
        ])
        return self.disp.AddWindow(
            {"ID": WIN_ID, "WindowTitle": "TelopSFX  テロップ / 効果音", "Geometry": geo}, layout
        )

    def _populate(self):
        itm = self.itm
        cfg = self.session.cfg
        itm["Tabs"].AddTab("テロップ")
        itm["Tabs"].AddTab("効果音")
        itm["Mode"].AddItems([label for label, _ in SOURCE_MODES])
        itm["Mode"].CurrentIndex = int(cfg.get("last_source_mode", 0))
        presets = list(self.session.presets.keys())
        itm["Preset"].AddItems(presets)
        if cfg.get("preset") in presets:
            itm["Preset"].CurrentIndex = presets.index(cfg["preset"])
        self._fill_marker_colors()
        candidates = self.session.template_candidates()
        tmpl = cfg.get("template_name", "Text+")
        if tmpl not in candidates:
            candidates.insert(0, tmpl)
        itm["Template"].AddItems(candidates)
        itm["Template"].CurrentIndex = candidates.index(tmpl)
        self._fill_telop_sfx()
        self._fill_sfx_list()
        for msg in self._pending_log:
            self.log(msg)
        self._pending_log = []
        self.log("準備完了: " + self.session.bridge.timeline_name())

    def _fill_marker_colors(self):
        colors = self.session.marker_colors()
        for cid in ("MarkerColor", "SfxMarkerColor"):
            combo = self.itm[cid]
            try:
                combo.Clear()
            except Exception:  # noqa: BLE001
                pass
            combo.AddItems(colors)
            saved = self.session.cfg.get("marker_color", "すべて")
            if saved in colors:
                combo.CurrentIndex = colors.index(saved)

    def _fill_telop_sfx(self):
        combo = self.itm["TelopSfx"]
        try:
            combo.Clear()
        except Exception:  # noqa: BLE001
            pass
        favs = [s for s in self.session.sfx_items if s.favorite]
        self._telop_sfx_paths = [s.path for s in (favs or self.session.sfx_items)]
        combo.AddItems([("★ " if s.favorite else "") + s.rel for s in (favs or self.session.sfx_items)])
        saved = self.session.cfg.get("telop_sfx", "")
        if saved in self._telop_sfx_paths:
            combo.CurrentIndex = self._telop_sfx_paths.index(saved)

    def _fill_sfx_list(self):
        tree = self.itm["SfxList"]
        tree.Clear()
        tree.SetHeaderLabels(["★", "効果音"])
        rows = self.session.search_sfx(self.itm["SfxQuery"].Text, bool(self.itm["FavOnly"].Checked))
        self._sfx_rows = rows
        for s in rows:
            row = tree.NewItem()
            row.Text[0] = "★" if s.favorite else ""
            row.Text[1] = s.rel
            tree.AddTopLevelItem(row)
        try:
            tree.ColumnWidth[0] = 28
        except Exception:  # noqa: BLE001
            pass

    def _selected_sfx(self):
        tree = self.itm["SfxList"]
        try:
            item = tree.CurrentItem()
        except Exception:  # noqa: BLE001
            item = None
        if not item:
            return None
        rel = item.Text[1]
        for s in self._sfx_rows:
            if s.rel == rel:
                return s
        return None

    # ---------------------------------------------------------------- events
    def _bind(self):
        on = self.win.On
        getattr(on, WIN_ID).Close = self._on_close
        on.Tabs.CurrentChanged = self._on_tab
        on.BtnLoad.Clicked = self._on_load
        on.BtnHelp.Clicked = lambda ev: self.log(HELP_TEXT)
        on.BtnPresetFile.Clicked = self._on_preset_file
        on.BtnPreview.Clicked = lambda ev: self._run(preview=True)
        on.BtnInsert.Clicked = lambda ev: self._run(preview=False)
        on.BtnFolder.Clicked = self._on_folder
        on.BtnRescan.Clicked = self._on_rescan
        on.SfxQuery.TextChanged = lambda ev: self._fill_sfx_list()
        on.FavOnly.Clicked = lambda ev: self._fill_sfx_list()
        on.SfxList.ItemDoubleClicked = lambda ev: self._on_sfx_playhead()
        on.BtnSfxPlayhead.Clicked = lambda ev: self._on_sfx_playhead()
        on.BtnFav.Clicked = self._on_fav
        on.BtnSfxMarkers.Clicked = self._on_sfx_markers

    def _on_tab(self, ev):
        self.itm["Stack"].CurrentIndex = ev["Index"]
        if ev["Index"] == 1:
            self._fill_marker_colors()

    def _on_close(self, ev):
        self._save_form()
        self.disp.ExitLoop()

    def _save_form(self):
        itm = self.itm
        cfg = self.session.cfg
        cfg["last_text"] = itm["Script"].PlainText or ""
        cfg["last_source_mode"] = int(itm["Mode"].CurrentIndex)
        cfg["default_duration_sec"] = float(itm["Duration"].Value)
        cfg["gap_sec"] = float(itm["Gap"].Value)
        cfg["video_track"] = int(itm["VideoTrack"].Value)
        cfg["audio_track"] = int(itm["AudioTrack"].Value)
        cfg["auto_free_track"] = bool(itm["AutoFree"].Checked)
        cfg["preset"] = itm["Preset"].CurrentText
        cfg["template_name"] = itm["Template"].CurrentText or "Text+"
        cfg["marker_color"] = itm["MarkerColor"].CurrentText
        cfg["subtitle_track"] = int(itm["SubTrack"].Value)
        cfg["telop_sfx_enabled"] = bool(itm["TelopSfxOn"].Checked)
        idx = int(itm["TelopSfx"].CurrentIndex)
        cfg["telop_sfx"] = self._telop_sfx_paths[idx] if 0 <= idx < len(self._telop_sfx_paths) else ""
        cfg["sfx_folder"] = itm["SfxFolder"].Text or ""
        try:
            geo = self.win.Geometry
            cfg["ui_geometry"] = [int(geo[0]), int(geo[1]), int(geo[2]), int(geo[3])]
        except Exception:  # noqa: BLE001
            pass
        self.session.save()

    def _request_path(self, directory=False):
        try:
            result = self.fusion.RequestDir() if directory else self.fusion.RequestFile()
            if result:
                return str(result)
        except Exception:  # noqa: BLE001
            pass
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            path = filedialog.askdirectory() if directory else filedialog.askopenfilename(
                filetypes=[("原稿", "*.txt *.srt *.vtt *.csv"), ("すべて", "*.*")]
            )
            root.destroy()
            return path or None
        except Exception:  # noqa: BLE001
            self.log("ファイル選択ダイアログを開けません。パスを直接入力してください")
            return None

    def _on_load(self, ev):
        path = self._request_path(directory=False)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                self.itm["Script"].PlainText = f.read()
            self.log("読み込み: " + path)
        except OSError as exc:
            self.log("読み込み失敗: %s" % exc)

    def _on_preset_file(self, ev):
        path = write_example_user_presets()
        self.log("プリセットファイル: %s  (編集後にパネルを開き直すと反映)" % path)

    def _on_folder(self, ev):
        path = self._request_path(directory=True)
        if path:
            self.itm["SfxFolder"].Text = path
            self._on_rescan(ev)

    def _on_rescan(self, ev):
        items = self.session.set_sfx_folder(self.itm["SfxFolder"].Text)
        self.log("効果音 %d 件を読み込みました" % len(items))
        self._fill_sfx_list()
        self._fill_telop_sfx()

    def _on_sfx_playhead(self):
        s = self._selected_sfx()
        if not s:
            self.log("効果音を選択してください")
            return
        self.session.cfg["audio_track"] = int(self.itm["AudioTrack2"].Value)
        self.session.cfg["auto_free_track"] = bool(self.itm["AutoFree"].Checked)
        try:
            self.session.insert_sfx_at_playhead(s.path)
        except Exception as exc:  # noqa: BLE001
            self.log("エラー: %s" % exc)

    def _on_fav(self, ev):
        s = self._selected_sfx()
        if not s:
            return
        self.session.toggle_favorite(s.path)
        self._fill_sfx_list()
        self._fill_telop_sfx()

    def _on_sfx_markers(self, ev):
        s = self._selected_sfx()
        if not s:
            self.log("効果音を選択してください")
            return
        self.session.cfg["audio_track"] = int(self.itm["AudioTrack2"].Value)
        try:
            self.session.insert_sfx_at_markers(s.path, self.itm["SfxMarkerColor"].CurrentText)
        except Exception as exc:  # noqa: BLE001
            self.log("エラー: %s" % exc)

    def _run(self, preview):
        self._save_form()
        itm = self.itm
        cfg = self.session.cfg
        telop_sfx = cfg["telop_sfx"] if cfg.get("telop_sfx_enabled") else ""
        opt = self.session.build_options(
            cfg["last_source_mode"], cfg["default_duration_sec"], cfg["gap_sec"], cfg["preset"],
            cfg["video_track"], cfg["audio_track"], cfg["auto_free_track"], cfg["marker_color"],
            bool(itm["UntilNext"].Checked), bool(itm["MarkerText"].Checked), cfg["subtitle_track"],
            telop_sfx, cfg["template_name"],
        )
        try:
            if preview:
                jobs, warnings = self.session.preview(cfg["last_text"], opt)
                for w in warnings:
                    self.log("注意: " + w)
                for j in jobs:
                    self.log("  %s  %5.2fs  %s" % (self.session.bridge.frame_tc(j.start), j.duration / self.session.bridge.fps,
                                                  j.text.replace("\n", " ")[:30] + ("  @" + j.sfx if j.sfx else "")))
                self.log("計 %d 枚 (まだ挿入していません)" % len(jobs))
            else:
                self.session.insert_telops(cfg["last_text"], opt)
        except ResolveError as exc:
            self.log("エラー: %s" % exc)
        except Exception as exc:  # noqa: BLE001
            self.log("予期しないエラー: %r" % (exc,))

    # ------------------------------------------------------------------ run
    def run(self):
        self.win.Show()
        self.disp.RunLoop()
        self.win.Hide()


def run_panel(resolve, fusion, bmd):
    UIManagerPanel(resolve, fusion, bmd).run()
