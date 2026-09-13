# ci-weekly-deck ビルドキット

Amazonリテール等の **週次定例デッキ** を 5co. CI v2 準拠のHTML→PDF/Googleスライドで生成する一式。
顧客非依存の共通部品のみを同梱し、顧客固有の値・ブランド名・所見・ID・ロゴは `config.json` と
`build_deck.py` の「顧客ごとに書き換える領域」にだけ置く設計。

## 中身

| ファイル | 役割 |
|----------|------|
| `scripts/ci_v2_lib.py` | 再利用ライブラリ。正典CSS連結(`inject_ci_head`＝`5co-CI-kit/ci_head.py` 経由・fail-closed)＋数値整形(百万円/万円/円/件/%)＋レイアウトヘルパ(表紙/ヘッダ/章扉/OKRノード)＋案件固有CSS(EXTRA_CSS)＋PDF化。**顧客固有情報は持たない**。 |
| `scripts/deck_builders.py` | 全テーブルビルダー(skyu/DSP/SA/SAファネル/香調別月別/エマージング/PD)。列構成は原本準拠、顧客固有定数(市場辞書/ハイライト/PD行/レシピ)は引数化。 |
| `scripts/extract_deck_data.py` | 集計用シートの `[資料用]` タブを OAuth直読みで `deck_data.json` に抽出(config駆動)。 |
| `scripts/sample_data.py` | worked sample 用のダミー構造データ(架空ブランド・原本と同じ列レイアウト)。 |
| `scripts/build_deck.py` | worked sample【フル忠実版・14枚】。架空顧客のダミー値で生成。実運用は本文領域を実値に差し替える。 |
| `config.example.json` | 設定の雛形。`config.json` にコピーして書き換える(`config.json` はgit管理外)。 |
| `assets/client_logo_placeholder.svg` | 顧客ロゴ枠。各顧客のロゴに差し替える。 |
| `assets/shoken_draft_template.md` | Step 1.5 所見MDドラフト雛形。実値差し替え前に所見をMDで確定する内容確認用。 |
| (共有) `scripts/html_to_pptx.py` | A4横PDF→画像ベースPPTX変換(任意の追加出力)。リポジトリ直下 `scripts/`。 |

デッキは元の制作デッキと同じ**14枚**(表紙／OKR／S級ドリル／エマージング／PD章扉／PD目標／DSP／SA／まとめ／補助章扉／SAファネル／香調別月別／競合ベンチ／全ブランド一覧)。

## 前提

- **CI基盤は複製しない・参照する**。正典CSSは `5co-CI-kit/ci_head.py`（`VERSION` の format: 宣言を
  連結する唯一の標準方式・V3.2_FORMAT 1.6）でHEADへ自動注入され、正典改定に自動追従する。
  CI基盤HTML(`config.json` の `ci_base_html`)からは**ロックアップSVG(ブランド資産)のみ**流用する。
  → ルートの CI 運用ルール(`CLAUDE.md` の CI・トンマナ節)に従う。「0からCSSを書かない」。
- **表紙CIコンセプトは自動付与**。`cover()` は正典 `ci_head.cover_ci_block()` を既定で載せる
  （全CIスライド規則・V3.2_FORMAT「表紙CIコンセプト」）。手書きで重複追加・削除しない。
- Python: `google-api-python-client` / `google-auth`(抽出に必要)。例 `~/venv-gapi/bin/python3`。
- 抽出には Sheets 閲覧スコープ付き OAuth トークン(`oauth_token`)が必要。
- PDF化は Chrome `--headless --print-to-pdf`(`build_deck.py --pdf` または `ci_v2_lib.to_pdf`)。

## 使い方

```bash
cd .claude/skills/ci-weekly-deck
cp config.example.json config.json          # 顧客名・client_logo・spreadsheet_id 等を記入

# 0) まずダミーで14枚を確認(抽出なしで動く)
python3 scripts/build_deck.py               # → output/週次デッキ.html
python3 scripts/build_deck.py --pdf         # PDFも出す

# 1) データ抽出(ライブにする時)
python3 scripts/extract_deck_data.py        # → deck_data.json(config の data.* に指定)

# 1.2) 入力ゲート(Observe/Orient 欠損チェック・必須)
#    生成前に deck_data の範囲・OKR進捗・年間計画書・前回定例会の文字起こし等の入力を確認。
#    欠損時はまず担当コンサルタントへ「データ欠損アラート」、データ自体が無いと確定したら
#    CTO 石井聡明さんへのサポート依頼・年間計画書の作成支援を提案(欠損の推測・ダミー補完禁止。
#    詳細 = ci-weekly-deck.md Step 1.2 / docs/slide-process-ooda.md「入力ゲートとアラート」)。

# 1.5) 所見MDドラフト確認(実値差し替え前・必須)
#    assets/shoken_draft_template.md を作業フォルダにコピーして所見を MD で埋め、ユーザー承認を取る。
#    高コストな HTML 差し替え前に、軽い MD 段階で論旨を確定させ手戻りを断つ(MD→HTML→PPTX の内容確認点)。

# 2) build_deck.py の「ここから顧客ごとに書き換える領域」を実値・実ブランド・(承認済み)実所見に差し替える。
#    表は deck_builders、整形は ci_v2_lib のヘルパ(mm/man/f_yen/f_pc 等)を通す。

# 3) はみ出し検査(必須)
python3 ../../../5co-CI-kit/slide_overflow_check.py output/週次デッキ.html
#    OVERFLOW が出たら行数・所見量を詰める。LOGO>64px:102px は意図的拡大(元デッキと同じ・許容)。

# 3.5) PPTX出力(任意・追加出力。既定の配布は PDF/Googleスライドのまま)
python3 ../../../scripts/html_to_pptx.py output/週次デッキ.pdf -o output/週次デッキ.pptx
#    A4横PDFの各ページを1スライド=1ページの画像ベースPPTXに変換(寸法はPDFから自動・CI完全忠実)。
#    画像ベースのため文言修正はデータ/build_deck.py に戻る。位置の微調整のみ PowerPoint で。

# 5) 定例会後(必須)
#    配布時(Step 4)の依頼文に「定例会後は会議音声の文字起こしのインプットをお願いします」を添える。
#    広告運用指示書は実行(ACT)前にコンサルタントの確認・承認必須(承認なしで入札・予算・KWメンテへ反映しない)。
```

## CI制約(厳守)

- 配色は **白 #FFFFFF / 水色 `--crystal` #C3D7EE / 紺 `--ink` #101820 の3色のみ**（SLIDE.md準拠）。緑・赤・グレー・他色相は不可。旧名 `--navy`/`--powder`・旧hex #A9CFDF/#0E1A38 は廃止
  (増減セマンティクスを出す時だけ CI の `--pos`/`--neg` を使う)。
- **丸数字①②③は使わない**。「打ち手:1 / KR:1」表記。
- A4横。和文ヒラギノ明朝＋欧文Garamond。ロックアップは「水晶玉＋Strategy, refined.」固定。
- 考察は SMART(目標対比/前年対比の **実数** と期限)で書く。所見はカードで主役化する。

## 機密ルール

- `config.json`(実スプレッドシートID・トークンパスを含む)は **コミットしない**(`.gitignore` 済)。
- POS等の最高機密データ・生データ・ASIN・個別売上は **外部送信しない**。スライドには集約値のみ。
- 提示前に Codex 等で原本(前提資料)との **数値差異チェック** を行ってから共有する。

## Drive配置

- 完成HTMLは共有ドライブの該当フォルダへ。`uploadFile(convertToGoogleFormat=true)` で
  Googleスライド化できる。**原本シートのコピーは外部コネクタ切れで値が壊れるため不可**、
  ライブ範囲読み(extract)を原則とする。
