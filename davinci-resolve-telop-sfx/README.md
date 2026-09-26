# TelopSFX — DaVinci Resolve テロップ / 効果音 一括挿入ツール

DaVinci Resolve の **Workspace › Scripts** メニューから呼び出すパネルです。
原稿を貼り付けるだけで Text+ テロップを正確な位置・尺でタイムラインに並べ、効果音を再生ヘッド / マーカー / テロップに合わせて一発で置けます。

## できること

| 機能 | 内容 |
| --- | --- |
| テロップ一括挿入 | 原稿 (1 行 = 1 枚) を貼り付け → 再生ヘッドから順に並べる / マーカー位置に置く / SRT の時間どおりに置く |
| 字幕 → Text+ 変換 | Resolve の自動字幕 (字幕トラック) を、そのままの尺で Text+ テロップに変換 |
| スタイルプリセット | 標準 / 強調 / 帯付き / 見出し / 左上キャプション。JSON で自作も可能 |
| 効果音ライブラリ | フォルダを指定 → 検索 → ダブルクリックで再生ヘッドに挿入。★お気に入り |
| 効果音一括挿入 | マーカー (色で絞込) の位置に一括、または全テロップの頭に同じ効果音 |
| 行ごとの効果音指定 | 原稿の行末に `@ぴこん` と書くと、その行のテロップと同時にその効果音が入る |
| トラック自動回避 | 置き先が埋まっていたら上のトラックへ (無ければ自動追加) |
| クイック挿入 | クリップボードの文字列を 1 枚だけ挿入 / 直前の効果音を再生ヘッドに挿入 |

Studio 版では Resolve ネイティブのパネル (UIManager)、無償版 (20.x まで) では同じ機能の別ウィンドウ (tkinter) が開きます。

## 動作要件

- DaVinci Resolve 18.5 〜 20.x (19 / 20 で想定)。この範囲なら Studio でなくても動きます
  - **無償版は 20.x まで**。Resolve 21.1 以降の無償版は Python スクリプトを読み込まなくなった (BMD が Python スクリプティングを Studio 限定に変更) ため、21.1 以降で使うには Studio 版が必要です
- macOS: **Mac App Store 版 Resolve は非対応** (サンドボックスのためスクリプトが動きません)。blackmagicdesign.com からダウンロードした版を使ってください
- Python 3.7 以降 (3.10〜3.12 を推奨。Resolve が Python スクリプトを実行するために必要)
  - macOS: <https://www.python.org/downloads/> の Python 3 をインストール
  - Windows: 同上。インストーラで「Add python.exe to PATH」にチェック
  - Rocky/RHEL 8 などの system python3 は 3.6 なので python.org 版 3.10+ を入れる
- (任意・Studio のみ) ターミナル等 Resolve の外から API を叩く場合だけ **環境設定 › システム › 一般 › External scripting using** を `Local` に。Workspace › Scripts から使うだけなら不要です

## インストール

1. このフォルダ (`davinci-resolve-telop-sfx`) をダウンロード
2. macOS は `install.command` をダブルクリック (初回は右クリック › 開く)。Windows は `install.bat` をダブルクリック
   - ターミナル派は `python3 install.py`
3. Resolve を再起動 → **Workspace › Scripts** に次の 3 つが出ます
   - `TelopSFX - Panel` … メインパネル
   - `TelopSFX - Quick Telop (clipboard)` … コピーした文字列を再生ヘッドに 1 枚挿入
   - `TelopSFX - Quick SFX (last used)` … 最後に使った効果音を再生ヘッドに挿入

インストール先: ランチャーは Resolve の `Scripts/Utility`、本体は `~/.telopsfx/lib/telopsfx`。
アンインストールは `python3 install.py --uninstall`。

## 初回だけ: Text+ テンプレートをメディアプールに置く (重要)

Resolve の API はタイトルを「指定した位置・尺」で置く手段を持っていないため、
**メディアプールにある Text+ をコピーして並べる**方式を取っています。次の一度だけやってください。

1. Edit ページ → **プロジェクト設定 › 編集 › 標準ジェネレーターの長さ** を、想定する最長テロップより長く (例: 60 秒) にして保存
2. **エフェクト › タイトル › Text+** を、タイムラインではなく **メディアプールにドラッグ**
3. 出来た `Text+` クリップをダブルクリックしてフォント・サイズ・位置などを好みに整える (この見た目が全テロップの土台になります)
4. 標準ジェネレーターの長さは元に戻して OK

複数のデザインを使い分けたい場合は、名前を変えた Text+ クリップを複数置き、パネルの「テンプレ」で選びます。
テンプレートが無い場合も動きますが、その時は Resolve 標準の `InsertFusionTitleIntoTimeline` で代替するため、尺は Resolve の既定値・トラックは選択中のトラックになります。

## 使い方

### テロップ

1. 原稿を貼り付ける (または「ファイル読込」で `.txt` / `.srt`)
2. 「配置」を選ぶ
   - **再生ヘッドから順に並べる** … 表示秒 + 間隔秒で順番に。行頭に時刻を書いた行はその位置に飛ぶ
   - **マーカーの位置に 1 行ずつ** … マーカー (色で絞込可) に 1 行ずつ割り当て。マーカーの長さがあればそれを尺に。「次のマーカーまで表示」「マーカー名/メモを原稿にする」も可
   - **字幕トラックを Text+ に変換** … 自動字幕の結果をそのままテロップ化 (原稿は不要)
3. スタイル / テンプレ / トラックを選んで **「配置を確認」** (ログに一覧が出るだけ) → **「▶ テロップを挿入」**

原稿の書き方 (「書き方」ボタンでも表示):

```
こんにちは                 -> 順番に並べる
こんにちは<TAB>2.5         -> 表示時間を個別指定 (秒)
[00:12] こんにちは          -> 12 秒地点に置く (タイムライン先頭基準)
00:12-00:15 こんにちは      -> 12〜15 秒
こんにちは @ぴこん          -> 効果音 "ぴこん" (ライブラリ内の名前) を同時に鳴らす
1 行目\n2 行目              -> Text+ 内で改行
# から始まる行と空行は無視。SRT を貼り付けてもそのまま使えます
```

サンプル: `examples/telop_sample.txt`, `examples/telop_sample.srt`

### 効果音

1. 「効果音」タブでフォルダを選ぶ (サブフォルダも読みます。wav / mp3 / aif / m4a / flac / ogg)
2. 検索欄で絞り込み → **ダブルクリックで再生ヘッドに挿入** (メディアプールの `SFX` ビンに自動取り込み。2 回目以降は再利用)
3. よく使うものは「★ お気に入り」。★ は一覧の先頭に来て、「各テロップに効果音」の候補にもなります
4. 「マーカー位置に一括挿入」で、指定色のマーカー全部に同じ効果音

### スタイルプリセット

「プリセット編集…」を押すと `~/.telopsfx/presets.json` が作られます。中身は Text+ の入力名と値そのもので、
自由に増やせます (パネルを開き直すと反映)。主なキー:

| キー | 意味 |
| --- | --- |
| `Font`, `Style`, `Size` | フォント名 / スタイル / サイズ (0〜1、0.08 が標準)。`Style` は Text+ のスタイル欄にそのフォントが実際に出す名前 (Yu Gothic UI: `Bold`/`Regular`、Hiragino Sans: `W3`〜`W9` など) でないと無視されます |
| `Red1` `Green1` `Blue1` `Alpha1` | 文字色 (0〜1) |
| `Enabled2`, `Red2`.., `Thickness2` | アウトライン ON/OFF、色、太さ |
| `Enabled4`, `ElementShape4`=2, `Red4`.., `Alpha4`, `ExtendHorizontal4`, `ExtendVertical4` | 背景ボックス |
| `Center` | 位置 `[x, y]` (0〜1、左下が原点。下部テロップは `[0.5, 0.12]`) |
| `ClipColor` | タイムライン上のクリップ色 (`Yellow`, `Orange`, `Teal` など) |

「テンプレートのまま」を選ぶと文字だけ差し替え、見た目はテンプレート Text+ のものを使います。

## 設定ファイル

`~/.telopsfx/config.json` に、効果音フォルダ・お気に入り・トラック番号・最後の原稿などを保存します。

## 仕組みと制限

- テロップ配置は `MediaPool.AppendToTimeline` の `recordFrame` / `trackIndex` を使い、置いた後に `GetStart()` / `GetDuration()` を読み戻して、Resolve バージョン差 (recordFrame が絶対か相対か、endFrame が排他的か) を **初回挿入時に自動補正**します
- テロップの尺はテンプレート Text+ の長さが上限です。超える場合はログに注意が出ます (上の「初回だけ」を参照)
- ドロップフレーム (29.97 DF / 59.94 DF) のタイムコードにも対応しています
- 効果音の音量は変えません (Fairlight 側で調整してください)
- Resolve の外部 (ターミナル等) からの実行は Studio 版のみ可能です。パネルは Scripts メニューから使ってください
- スクリプトへのキーボードショートカット割り当ては Resolve の仕様上できないため、Quick 系スクリプトも Workspace › Scripts から呼びます

## トラブルシューティング

| 症状 | 確認すること |
| --- | --- |
| Scripts メニューに出ない | 無償版で Resolve 21.1 以降を使っていないか (21.1 以降の無償版は .py を読み込みません → 20.x に戻すか Studio 版を使う)。macOS で App Store 版 Resolve を使っていないか (非対応。BMD サイトのダウンロード版に入れ替える)。Python 3 (3.7 以上) がインストールされているか。Resolve を再起動したか。`install.py` の出力先にファイルがあるか |
| 「telopsfx パッケージが見つかりません」 | `install.py` を実行し直す (`~/.telopsfx/lib/telopsfx` が出来ます) |
| テロップの文字が変わらない | テンプレートが Text+ (Fusion タイトル) か。他のタイトルは非対応 |
| 位置がずれる / 末尾に追加される | 置き先のトラックが埋まっていないか (「重なるなら上のトラックへ」を ON に) |
| 尺が短い | テンプレート Text+ の長さ不足。標準ジェネレーターの長さを延ばして Text+ を置き直す |
| 無償版でウィンドウが出ない | tkinter 入りの Python (python.org 版) か。`TELOPSFX_UI=tk` で強制的に tkinter を使うことも可 |

## 開発

```
pip install pytest
python3 -m pytest tests
```

Resolve 本体が無くてもテストできるよう、`tests/fake_resolve.py` に API のモックがあります。
Resolve に触るコードは `telopsfx/resolve_bridge.py` だけにまとめています。

```
telopsfx/
  timecode.py       タイムコード ⇄ フレーム (DF 対応)
  parsers.py        原稿 (txt / SRT) パーサ
  planner.py        原稿 → フレーム位置の配置計画
  resolve_bridge.py Resolve API 呼び出し (自動補正含む)
  engine.py         配置の実行
  sfxlib.py         効果音フォルダのスキャン / 検索
  presets.py        スタイルプリセット
  ui_uimanager.py   Studio 用パネル
  ui_tk.py          無償版用パネル
  app.py            エントリポイント
resolve_scripts/Utility/  Resolve の Scripts メニューに入るランチャー
```
