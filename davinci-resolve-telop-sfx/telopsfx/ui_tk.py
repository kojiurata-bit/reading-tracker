"""無償版 DaVinci Resolve 用パネル (tkinter). UIManager が使えない環境のフォールバック."""

import tkinter as tk
from tkinter import filedialog, ttk

from .engine import read_script_text
from .presets import write_example_user_presets
from .resolve_bridge import ResolveError
from .ui_common import HELP_TEXT, SOURCE_MODES, Session


class TkPanel:
    def __init__(self, resolve):
        self._log_widget = None
        self._pending = []
        # Resolve 側の検証を先に行う (失敗しても空ウィンドウを残さない)
        self.session = Session(resolve, self.log)  # ResolveError はここで送出され, まだ root は無い
        self.root = tk.Tk()
        try:
            self.root.report_callback_exception = self._on_callback_error
            self.root.title("TelopSFX  テロップ / 効果音")
            cfg = self.session.cfg
            geo = cfg.get("ui_geometry") or [200, 120, 760, 720]
            self.root.geometry("%dx%d+%d+%d" % (geo[2], geo[3], geo[0], geo[1]))
            self._sfx_rows = []
            self._telop_sfx_paths = []
            self._build()
            for m in self._pending:
                self.log(m)
            self.log("準備完了: " + self.session.bridge.timeline_name())
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        except Exception:
            try:
                self.root.destroy()
            except Exception:  # noqa: BLE001
                pass
            raise

    def _on_callback_error(self, etype, value, tb):
        """Tk コールバック内の例外. Resolve にはコンソールが無いのでパネルのログにも出す."""
        import traceback
        text = "".join(traceback.format_exception(etype, value, tb))
        print(text)  # Resolve の Workspace > Console 用
        try:
            self.log("エラー: %s: %s" % (etype.__name__, value))
        except Exception:  # noqa: BLE001
            pass

    def log(self, msg):
        if self._log_widget is None:
            self._pending.append(msg)
            return
        self._log_widget.configure(state="normal")
        self._log_widget.insert("end", msg + "\n")
        self._log_widget.see("end")
        self._log_widget.configure(state="disabled")

    # ---------------------------------------------------------------- build
    def _build(self):
        cfg = self.session.cfg
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=6)
        telop = ttk.Frame(nb)
        sfx = ttk.Frame(nb)
        nb.add(telop, text="テロップ")
        nb.add(sfx, text="効果音")
        nb.bind("<<NotebookTabChanged>>", lambda ev: self._fill_marker_colors())

        # --- telop tab
        top = ttk.Frame(telop)
        top.pack(fill="x", pady=2)
        ttk.Label(top, text="原稿 (1 行 = 1 テロップ)").pack(side="left")
        ttk.Button(top, text="書き方", command=lambda: self.log(HELP_TEXT)).pack(side="right")
        ttk.Button(top, text="ファイル読込 (txt / srt)", command=self._on_load).pack(side="right", padx=4)
        self.script = tk.Text(telop, height=12, wrap="word")
        self.script.pack(fill="both", expand=True)
        self.script.insert("1.0", cfg.get("last_text", ""))

        row = ttk.Frame(telop); row.pack(fill="x", pady=2)
        ttk.Label(row, text="配置").pack(side="left")
        self.mode = ttk.Combobox(row, state="readonly", values=[l for l, _ in SOURCE_MODES])
        self.mode.current(min(int(cfg.get("last_source_mode", 0)), len(SOURCE_MODES) - 1))
        self.mode.pack(side="left", fill="x", expand=True, padx=4)

        row = ttk.Frame(telop); row.pack(fill="x", pady=2)
        ttk.Label(row, text="表示秒").pack(side="left")
        self.duration = tk.DoubleVar(value=float(cfg.get("default_duration_sec", 3.0)))
        ttk.Spinbox(row, from_=0.1, to=3600, increment=0.5, textvariable=self.duration, width=6).pack(side="left", padx=2)
        ttk.Label(row, text="間隔秒").pack(side="left")
        self.gap = tk.DoubleVar(value=float(cfg.get("gap_sec", 0.0)))
        ttk.Spinbox(row, from_=0, to=600, increment=0.5, textvariable=self.gap, width=6).pack(side="left", padx=2)
        ttk.Label(row, text="V").pack(side="left")
        self.video_track = tk.IntVar(value=int(cfg.get("video_track", 2)))
        ttk.Spinbox(row, from_=1, to=99, textvariable=self.video_track, width=4).pack(side="left", padx=2)
        self.auto_free = tk.BooleanVar(value=bool(cfg.get("auto_free_track", True)))
        ttk.Checkbutton(row, text="重なるなら上のトラックへ", variable=self.auto_free).pack(side="left", padx=6)

        row = ttk.Frame(telop); row.pack(fill="x", pady=2)
        ttk.Label(row, text="マーカー色").pack(side="left")
        self.marker_color = ttk.Combobox(row, state="readonly", width=12)
        self.marker_color.pack(side="left", padx=2)
        self.until_next = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="次のマーカーまで表示", variable=self.until_next).pack(side="left", padx=4)
        self.marker_text = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="マーカー名/メモを原稿にする", variable=self.marker_text).pack(side="left", padx=4)
        ttk.Label(row, text="字幕Tr").pack(side="left")
        self.sub_track = tk.IntVar(value=int(cfg.get("subtitle_track", 1)))
        ttk.Spinbox(row, from_=1, to=20, textvariable=self.sub_track, width=4).pack(side="left", padx=2)

        row = ttk.Frame(telop); row.pack(fill="x", pady=2)
        ttk.Label(row, text="スタイル").pack(side="left")
        presets = list(self.session.presets.keys())
        self.preset = ttk.Combobox(row, state="readonly", values=presets)
        self.preset.current(presets.index(cfg["preset"]) if cfg.get("preset") in presets else 0)
        self.preset.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row, text="プリセット編集…", command=self._on_preset_file).pack(side="left", padx=2)
        ttk.Label(row, text="テンプレ").pack(side="left")
        candidates = self.session.template_candidates()
        tmpl = cfg.get("template_name", "Text+")
        if tmpl not in candidates:
            candidates.insert(0, tmpl)
        self.template = ttk.Combobox(row, values=candidates, width=16)
        self.template.set(tmpl)
        self.template.pack(side="left", padx=2)

        row = ttk.Frame(telop); row.pack(fill="x", pady=2)
        self.telop_sfx_on = tk.BooleanVar(value=bool(cfg.get("telop_sfx_enabled", False)))
        ttk.Checkbutton(row, text="各テロップに効果音", variable=self.telop_sfx_on).pack(side="left")
        self.telop_sfx = ttk.Combobox(row, state="readonly")
        self.telop_sfx.pack(side="left", fill="x", expand=True, padx=2)
        ttk.Label(row, text="A").pack(side="left")
        self.audio_track = tk.IntVar(value=int(cfg.get("audio_track", 2)))
        ttk.Spinbox(row, from_=1, to=99, textvariable=self.audio_track, width=4).pack(side="left", padx=2)

        row = ttk.Frame(telop); row.pack(fill="x", pady=4)
        ttk.Button(row, text="配置を確認 (挿入しない)", command=lambda: self._run(True)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(row, text="▶ テロップを挿入", command=lambda: self._run(False)).pack(side="left", expand=True, fill="x", padx=2)

        # --- sfx tab
        row = ttk.Frame(sfx); row.pack(fill="x", pady=2)
        ttk.Label(row, text="フォルダ").pack(side="left")
        self.sfx_folder = tk.StringVar(value=cfg.get("sfx_folder", ""))
        ttk.Entry(row, textvariable=self.sfx_folder).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(row, text="選択…", command=self._on_folder).pack(side="left")
        ttk.Button(row, text="再読込", command=self._on_rescan).pack(side="left", padx=2)
        row = ttk.Frame(sfx); row.pack(fill="x", pady=2)
        self.query = tk.StringVar()
        self.query.trace_add("write", lambda *a: self._fill_sfx_list())
        ttk.Entry(row, textvariable=self.query).pack(side="left", fill="x", expand=True, padx=2)
        self.fav_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="★のみ", variable=self.fav_only, command=self._fill_sfx_list).pack(side="left")
        self.sfx_list = ttk.Treeview(sfx, columns=("fav", "name"), show="headings", selectmode="browse")
        self.sfx_list.heading("fav", text="★"); self.sfx_list.column("fav", width=28, stretch=False)
        self.sfx_list.heading("name", text="効果音")
        self.sfx_list.pack(fill="both", expand=True, pady=2)
        self.sfx_list.bind("<Double-1>", lambda ev: self._on_sfx_playhead())
        row = ttk.Frame(sfx); row.pack(fill="x", pady=2)
        ttk.Button(row, text="▶ 再生ヘッドに挿入 (ダブルクリックでも)", command=self._on_sfx_playhead).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(row, text="★ お気に入り切替", command=self._on_fav).pack(side="left", padx=2)
        row = ttk.Frame(sfx); row.pack(fill="x", pady=2)
        ttk.Button(row, text="マーカー位置に一括挿入", command=self._on_sfx_markers).pack(side="left", padx=2)
        ttk.Label(row, text="マーカー色").pack(side="left")
        self.sfx_marker_color = ttk.Combobox(row, state="readonly", width=12)
        self.sfx_marker_color.pack(side="left", padx=2)
        ttk.Label(row, text="A").pack(side="left")
        ttk.Spinbox(row, from_=1, to=99, textvariable=self.audio_track, width=4).pack(side="left", padx=2)

        # --- log
        ttk.Label(self.root, text="ログ").pack(anchor="w", padx=8)
        self._log_widget = tk.Text(self.root, height=7, state="disabled", wrap="word")
        self._log_widget.pack(fill="x", padx=8, pady=(0, 8))

        self._fill_marker_colors()
        self._fill_telop_sfx()
        self._fill_sfx_list()

    def _fill_marker_colors(self):
        colors = self.session.marker_colors()
        cfg_color = self.session.cfg.get("marker_color", "すべて")
        for combo in (self.marker_color, self.sfx_marker_color):
            current = combo.get()
            combo["values"] = colors
            if current in colors:
                value = current
            elif cfg_color in colors:
                value = cfg_color
            else:
                value = colors[0]
            combo.set(value)

    def _fill_telop_sfx(self):
        # 現在の選択を優先し、無ければ保存値 (初回表示時など) にフォールバック
        idx = self.telop_sfx.current()
        if 0 <= idx < len(self._telop_sfx_paths):
            keep = self._telop_sfx_paths[idx]
        else:
            keep = self.session.cfg.get("telop_sfx", "")
        favs = [s for s in self.session.sfx_items if s.favorite]
        items = favs or self.session.sfx_items
        self._telop_sfx_paths = [s.path for s in items]
        self.telop_sfx["values"] = [("★ " if s.favorite else "") + s.rel for s in items]
        if keep in self._telop_sfx_paths:
            self.telop_sfx.current(self._telop_sfx_paths.index(keep))
        elif items:
            self.telop_sfx.current(0)
        else:
            self.telop_sfx.set("")

    def _fill_sfx_list(self):
        for iid in self.sfx_list.get_children():
            self.sfx_list.delete(iid)
        self._sfx_rows = self.session.search_sfx(self.query.get(), self.fav_only.get())
        for i, s in enumerate(self._sfx_rows):
            self.sfx_list.insert("", "end", iid=str(i), values=("★" if s.favorite else "", s.rel))

    def _selected_sfx(self):
        sel = self.sfx_list.selection()
        if not sel:
            return None
        idx = int(sel[0])
        return self._sfx_rows[idx] if 0 <= idx < len(self._sfx_rows) else None

    # --------------------------------------------------------------- actions
    def _num(self, var, default, cast=float, label=""):
        """Spinbox は自由入力なので空欄/非数値だと Var.get() が TclError を投げる. 既定値で救済."""
        try:
            return cast(var.get())
        except (tk.TclError, ValueError, TypeError):
            self.log("%s の値が不正なので %s を使います" % (label or "数値", default))
            try:
                var.set(default)
            except tk.TclError:
                pass
            return default

    def _save_form(self):
        cfg = self.session.cfg
        cfg["last_text"] = self.script.get("1.0", "end").rstrip("\n")
        cfg["last_source_mode"] = self.mode.current()
        cfg["default_duration_sec"] = self._num(self.duration, float(cfg.get("default_duration_sec", 3.0)), float, "表示秒")
        cfg["gap_sec"] = self._num(self.gap, float(cfg.get("gap_sec", 0.0)), float, "間隔秒")
        cfg["video_track"] = self._num(self.video_track, int(cfg.get("video_track", 2)), int, "V")
        cfg["audio_track"] = self._num(self.audio_track, int(cfg.get("audio_track", 2)), int, "A")
        cfg["auto_free_track"] = bool(self.auto_free.get())
        cfg["preset"] = self.preset.get()
        cfg["template_name"] = self.template.get() or "Text+"
        cfg["marker_color"] = self.marker_color.get()
        cfg["subtitle_track"] = self._num(self.sub_track, int(cfg.get("subtitle_track", 1)), int, "字幕Tr")
        cfg["telop_sfx_enabled"] = bool(self.telop_sfx_on.get())
        idx = self.telop_sfx.current()
        cfg["telop_sfx"] = self._telop_sfx_paths[idx] if 0 <= idx < len(self._telop_sfx_paths) else ""
        cfg["sfx_folder"] = self.sfx_folder.get()
        try:
            cfg["ui_geometry"] = [self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height()]
        except Exception:  # noqa: BLE001
            pass
        self.session.save()

    def _on_close(self):
        try:
            self._save_form()
        except Exception as exc:  # noqa: BLE001
            print("TelopSFX: 設定保存に失敗: %r" % (exc,))
        finally:
            self.root.destroy()

    def _on_load(self):
        path = filedialog.askopenfilename(filetypes=[("原稿", "*.txt *.srt *.vtt"), ("すべて", "*.*")])
        if not path:
            return
        try:
            text = read_script_text(path)  # 読めてから消す (失敗時に原稿を失わない)
        except (OSError, ValueError) as exc:
            self.log("読み込み失敗: %s" % exc)
            return
        self.script.delete("1.0", "end")
        self.script.insert("1.0", text)
        self.log("読み込み: " + path)

    def _on_preset_file(self):
        self.log("プリセットファイル: %s  (編集後にパネルを開き直すと反映)" % write_example_user_presets())

    def _on_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.sfx_folder.set(path)
            self._on_rescan()

    def _on_rescan(self):
        items = self.session.set_sfx_folder(self.sfx_folder.get())
        self.log("効果音 %d 件を読み込みました" % len(items))
        self._fill_sfx_list()
        self._fill_telop_sfx()

    def _on_sfx_playhead(self):
        s = self._selected_sfx()
        if not s:
            self.log("効果音を選択してください")
            return
        try:
            self.session.cfg["audio_track"] = self._num(self.audio_track, int(self.session.cfg.get("audio_track", 2)), int, "A")
            self.session.cfg["auto_free_track"] = bool(self.auto_free.get())
            self.session.insert_sfx_at_playhead(s.path)
        except Exception as exc:  # noqa: BLE001
            self.log("エラー: %s" % exc)

    def _on_fav(self):
        s = self._selected_sfx()
        if not s:
            return
        self.session.toggle_favorite(s.path)
        self._fill_sfx_list()
        self._fill_telop_sfx()

    def _on_sfx_markers(self):
        s = self._selected_sfx()
        if not s:
            self.log("効果音を選択してください")
            return
        try:
            self.session.cfg["audio_track"] = self._num(self.audio_track, int(self.session.cfg.get("audio_track", 2)), int, "A")
            self.session.cfg["auto_free_track"] = bool(self.auto_free.get())
            self.session.insert_sfx_at_markers(s.path, self.sfx_marker_color.get())
        except Exception as exc:  # noqa: BLE001
            self.log("エラー: %s" % exc)

    def _run(self, preview):
        try:
            self._save_form()
            cfg = self.session.cfg
            telop_sfx = cfg["telop_sfx"] if cfg.get("telop_sfx_enabled") else ""
            opt = self.session.build_options(
                cfg["last_source_mode"], cfg["default_duration_sec"], cfg["gap_sec"], cfg["preset"],
                cfg["video_track"], cfg["audio_track"], cfg["auto_free_track"], cfg["marker_color"],
                bool(self.until_next.get()), bool(self.marker_text.get()), cfg["subtitle_track"],
                telop_sfx, cfg["template_name"],
            )
            if preview:
                jobs, warnings = self.session.preview(cfg["last_text"], opt)
                for w in warnings:
                    self.log("注意: " + w)
                b = self.session.bridge
                for j in jobs:
                    self.log("  %s  %5.2fs  %s" % (b.frame_tc(j.start), j.duration / b.fps,
                                                  j.text.replace("\n", " ")[:30] + ("  @" + j.sfx if j.sfx else "")))
                self.log("計 %d 枚 (まだ挿入していません)" % len(jobs))
            else:
                self.session.insert_telops(cfg["last_text"], opt)
        except ResolveError as exc:
            self.log("エラー: %s" % exc)
        except (tk.TclError, ValueError) as exc:
            self.log("数値の入力が不正です: %s" % exc)
        except Exception as exc:  # noqa: BLE001
            self.log("予期しないエラー: %r" % (exc,))

    def run(self):
        self.root.mainloop()


def run_panel(resolve):
    TkPanel(resolve).run()
