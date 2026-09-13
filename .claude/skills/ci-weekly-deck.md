# 週次定例デッキ作成スキル（5co. CI v2）

> 顧客向けの **週次定例デッキ**（Amazonリテール週次レビュー等）を 5co. CI v2 準拠の
> HTML→PDF/Googleスライドで生成する手順。
> ユーザーが「週次定例デッキ」「週次レビュー資料」「CIスライドで定例を作る」等を指示した際に実行する。
> **必ずこのスキルに従う。CSSは0から書かず CI基盤を複製・参照する。顧客固有値はビルド設定と本文領域にだけ置く。**

## いつ起動するか

- 顧客の週次／隔週の定例報告デッキを新規生成・再生成する
- 既存の週次デッキを当週データで更新する
- 「CI v2で定例資料を作って」「岸田担当の週次デッキをAIで」等の依頼

## 同梱物（Tier3・`ci-weekly-deck/`）

| パス | 役割 |
|------|------|
| `scripts/ci_v2_lib.py` | 再利用ライブラリ（数値整形＋レイアウトヘルパ＋追加CSS＋CI基盤ローダ＋PDF化）。顧客固有情報なし。 |
| `scripts/deck_builders.py` | 全テーブルビルダー（skyu/DSP/SA/SAファネル/香調別月別/エマージング/PD）。列構成は原本準拠、顧客固有定数は引数化。 |
| `scripts/extract_deck_data.py` | `[資料用]`タブを OAuth直読みで抽出（config駆動）。 |
| `scripts/sample_data.py` | worked sample 用のダミー構造データ（架空ブランド・同じ列レイアウト）。 |
| `scripts/build_deck.py` | worked sample【フル忠実版・14枚】。本文領域を実値に差し替えて使う。 |
| `config.example.json` | 設定雛形。`config.json` にコピー（git管理外）。 |
| `assets/client_logo_placeholder.svg` | 顧客ロゴ枠（各顧客ロゴに差し替え）。 |
| `assets/shoken_draft_template.md` | Step 1.5 所見MDドラフト雛形（実値差し替え前の内容確認用）。 |
| `README.md` | キット詳細。 |

デッキは元の制作デッキと同じ**14枚構成**（表紙／OKR／S級ドリル／エマージング／PD章扉／PD目標／DSP／SA／まとめ／補助章扉／SAファネル／香調別月別／競合ベンチ／全ブランド一覧）。

## 新規クライアント対応（全クライアント共通）

スキルは **CI基盤を同梱（`assets/ci_base_sample.html`）して自己完結**しているため、どのクライアントでも
作業フォルダに `config.json` を1つ用意するだけで動く（CI基盤の別途コピー不要）。

1. クライアント作業フォルダを作る（例 `02_OKR・CFR/顧客OKR/<クライアント>/projects/定例デッキ/`）
2. `config.example.json` をそこへ `config.json` としてコピーし、`client_name` / `client_logo`（実ロゴ）/
   `spreadsheet_id` / `ranges`（そのクライアントの集計シート）を記入。`ci_base_html` は
   `<スキル>/assets/ci_base_sample.html`（絶対 or 相対）に向ける
3. **デッキ型を選ぶ**：
   - **週次・OKR/S級/エマージング型**（NatureLab系）→ `build_deck.py`
   - **月次・運用報告/カテゴリ/○△×型**（WELLA系）→ `build_wella_deck.py`
   - 構造が違うクライアントは、近い方を複製し「顧客ごとに書き換える領域」を作り替える
4. ダミーで生成 → はみ出し検査 → 実データ抽出（`extract_deck_data.py`）→ 差し替え → 差異チェック → Drive配置

> **図の型は `framework-recommend` で広げる（標準ステップ）**：本文スライドを設計するとき、その
> スライドの「言いたいこと」を `python3 scripts/framework_recommend.py "<意図>"` に渡し、内容に合う図
> ＋『未経験かものフレームワーク図（発見枠）』を提示する。作り手が知っている型だけに寄らせない。
> 選んだ型は `docs/SLIDE-PATTERN-CI-ADAPTER-SPEC.md`（A4・3色・φ）に従って CI v2 で描く。

> 既知の対応: NatureLab＝`build_deck.py`＋`Naturelab_リテール_定例資料集計用`[資料用]タブ。
> WELLA＝`build_wella_deck.py`＋`定例用`/`提出用_カテゴリ別`/`定例会用` 系（月次・OPI/RH）。

## 実行手順

### 0. 設定（顧客ごと・初回のみ）

`ci-weekly-deck/config.example.json` を `config.json` にコピーし、以下を記入する：

- `client_name` / `client_kicker` … 顧客名・表紙キッカー
- `ci_base_html` … 既定は**スキル同梱の `assets/ci_base_sample.html`**（`config.example.json` の既定値・`docs/SLIDE-md/SLIDE-md-5co/sample.html` の同一コピー）。`lockup_symbol_id` は基盤の `<symbol>` ID（同梱基盤・`5co-CI-kit/5co_slide_template.html` いずれも `lk`）。基盤からは**ロックアップsymbol（ブランド資産）のみ**流用し、正典CSSは `5co-CI-kit/ci_head.py` 連結（V3.2_FORMAT 1.6）で自動注入・自動追従する
- `client_logo` … 顧客ロゴ（透過PNG/SVG）。未用意なら `assets/client_logo_placeholder.svg` のまま
- `spreadsheet_id` / `ranges` / `oauth_token` … 抽出元シートID・`[資料用]`各タブ範囲・OAuthトークン
- `data.skyu_full` / `data.deck_data` / `data.lavon` … 実データJSON（未指定なら `sample_data.py` のダミーで14枚生成）
- `output_html` / `output_pdf` / `period_text`

> `config.json` は実IDを含むため **コミットしない**（`.gitignore` 済）。

### 1. データ抽出（ライブにする時）

```bash
python3 scripts/extract_deck_data.py   # → deck_data.json（FORMATTED_VALUE）
```

- 要 OAuthトークン（Sheets閲覧スコープ・原本へ閲覧権限）。
- **原本シートはコピー不可**（外部コネクタ依存で値が壊れる）。ライブ範囲読みのみ。
- 香調別月次など別ソースがある場合は `ranges` に追加するか、別JSONを用意する。

### 1.2 入力ゲート（Observe/Orient 欠損チェック・必須）

生成に進む前に次を確認する。**欠損を推測・ダミー値で補完して先へ進まない**
（全体定義 = `docs/slide-process-ooda.md`「入力ゲートとアラート」）：

- **Observe 系**：`deck_data.json` の対象範囲・広告実績（DWH）・Shelpha・ECモール商品データ・
  Amazon月間検索Vol・**前回定例会の議事録/文字起こし**・クライアント戦略文書
- **Orient 系**：OKR進捗（必須）・**年間計画書**（年間目標推移の元データ）
- **所在が未定義の項目**（保存場所の規約が無いもの）は、欠損と断定する前に
  **まずユーザーへ所在を確認**する
- **欠損があれば**：**まず担当コンサルタント**への**「データ欠損アラート」**（何が・どの期間・
  どのタブ/ソースで欠けているか明示）の連絡文を作成し、送付を依頼する
- **データ自体が存在しない場合**（アラートの結果「ソース未接続・計画書が未作成」と確定した
  場合）：**CTO 石井聡明さんへのサポート依頼**（接続・権限付与）や**年間計画書の作成支援**を
  提案する（コンサルタント確認より先に CTO へ直行しない）
- **正当に存在しない入力**（初回定例＝前回文字起こし無し・年間計画が対象外 等）は、
  担当コンサルタントの承認で免除できる（免除と理由を資料の前提注記へ。
  形式 = `docs/slide-process-ooda.md` 規則7）

### 1.5 所見MDドラフト確認（実値差し替え前・必須）

データ抽出が済んだら、**HTMLに書き込む前に「所見・ナラティブ」を MD で提示してユーザー承認を取る**。
これは MD→HTML→PPTX フローの「コンテンツ(中身)の最終確認ポイント」を定例エンジンに移植したもの。
高コストな HTML 生成・差し替えに進む前に、軽い MD 段階で論旨を確定させ手戻りを断つ。

- 雛形：`ci-weekly-deck/assets/shoken_draft_template.md` を作業フォルダにコピーして埋める。
- 各スライドの **数値ハイライト＋所見（SMART：目標対比/前年対比の実数＋期限）＋次の打ち手** を箇条書きで。
- POS等の最高機密の生データ・ASIN・個別売上は載せない（**集約値のみ**／機密ルール準拠）。
- ユーザーが OK したドラフトの所見を、Step 2 の「顧客ごとに書き換える領域」へそのまま反映する。

> 図の型に迷うスライドは、このタイミングで `framework-recommend` を併用（内容に合う図＋発見枠）。

### 2. 生成

```bash
python3 scripts/build_deck.py          # → output HTML（まずダミーで雛形確認）
python3 scripts/build_deck.py --pdf    # Chrome --headless でA4横PDFも出力
```

`build_deck.py` の **「ここから顧客ごとに書き換える領域」** を `deck_data.json` の実値・実ブランド・
実所見に差し替える。表は `ci_v2_lib` の整形ヘルパ（`mm`=百万円 / `man`=万円 / `f_yen` / `f_cnt` / `f_pc`）を
必ず通す（IR作法：整数四捨五入・マイナス△・単位は表頭）。レイアウトは `cover/header/divider/pd_divider/oknode`、
表は `deck_builders`（`skyu`/`dsp_tbl`/`sa_tbl`/`sa_funnel_tbl`/`lavon_tbls`/`emrg_tbl`/`emrg_tbl_all`/`pd_tbl`）を使う。

**はみ出し検査（必須）**: 生成・編集後は必ず実行する。

```bash
python3 ../../../5co-CI-kit/slide_overflow_check.py output/週次デッキ.html
```

`OVERFLOW` が出たら行数・所見量を詰めて A4 内に収める（`LOGO>64px:102px` はヘッダ右上ロックアップの
意図的拡大で、元デッキと同じ・許容）。

### 3. 差異チェック（提示前・必須）

原本（前提資料・前週デッキ・PPT）との **数値差異** を Codex 等で確認してから共有する。
逆転（実績＞着地見込 等）や参照ズレは取消線＋「要確認」で明示し、確定前に担当へ確認する。

### 3.5 PPTX出力（任意・追加出力）

既定の配布形式は **PDF / Googleスライド** のまま。PowerPoint 形式が要る相手には、Step 2 で出した
**A4横PDF** をそのまま画像ベース PPTX に変換できる（CI完全忠実・決定論的）。

```bash
python3 ../../../scripts/html_to_pptx.py output/週次デッキ.pdf -o output/週次デッキ.pptx
# 寸法は PDF のページ寸法（A4横）から自動決定。--aspect は不要。
```

- 14枚（PDFの各ページ）が1スライド=1ページの PPTX になる。
- **画像ベース**のため PowerPoint 上でテキスト直接編集は不可。文言・数値・所見の修正は
  **データ／build_deck.py の本文領域に戻って**やり直す（PPTX側で直さない）。位置・サイズの微調整のみ手作業。
- 編集可能テキストの PPTX が必要なら Claude Design のエクスポートを使う（本パスはCI忠実な決定論出力）。

### 4. Drive配置

完成HTMLを共有ドライブの該当フォルダへ。`uploadFile(convertToGoogleFormat=true)` で
Googleスライド化できる。**原本のコピーは不可**（コネクタ切れ）。配布はライブ抽出→生成の原則を守る。
PPTX を配る場合は Step 3.5 の出力を同フォルダへ。

### 5. 定例会後（次サイクルの入力・必須）

- **会議音声の文字起こしを必ずインプット**するようユーザーへリマインドする
  （Decide の必須成果物・次回 Observe の入力・次の広告運用指示書の根拠。
  未入力のまま次回作成に入った場合は Step 1.2 の欠損アラート対象）。
  **実行タイミング＝Step 4 の配布時**：配布の依頼文・完了報告に
  「定例会後は文字起こしのインプットをお願いします」を必ず添える
- AI が**広告運用指示書**を作成・更新する際は、**実行（ACT）前にコンサルタントの
  確認・承認を必ず依頼**する（承認なしで入札・予算・KWメンテへ反映しない）。
  経路＝Claude が指示書ドラフトと承認依頼文を作成 → 担当コンサルタントへ提出 →
  承認記録後に反映（承認記録＝承認者名・日時 or スレッドURLを指示書に残す。
  文字起こしの保存先はクライアント議事録規約に従い、受領検証は次回 Step 1.2 が担う）

## CI正本（必読）

制作前に **`docs/SLIDE-md/SLIDE-md-5co/SLIDE.md`**（正規仕様・配色/級数/コンポーネント）を必ず読む。
補助として `5co-CI-kit/CI_KICKOFF.md` / `SLIDE_DESIGN_GUIDELINES.md`。

**所見（Step 1.5・`shoken_draft_template.md`）の文体は `5co-CI-kit/COPY_GUIDE.md` が正**
（2026-07-08 制定・全定例会資料のコメントに採用）。数値ハイライトの羅列で終えず、
読者の問いに答える一文から書く（原則5・誠実トーンの定型）。定例会資料の読者は
運用の専門用語に不慣れなことが多い（EC/デジタル初心者を含む）ため、専門用語は
初出で日常語を併記する（原則4）。

正典CSSは **`5co-CI-kit/ci_head.py` の連結（V3.2_FORMAT 1.6・唯一の標準方式）** でHEADへ注入され、
`VERSION` の format: 宣言（版上げ）に自動追従する。CI基盤HTML（`ci_base_html`）からは
**ロックアップ `symbol id="lk"`（ブランド資産）のみ**流用する。スキルは `docs/SLIDE-md/SLIDE-md-5co/sample.html`
の同一コピーを `assets/ci_base_sample.html` として同梱し、config.example.json の `ci_base_html` は
この同梱コピーを指す（`lockup_symbol_id="lk"`、`numfield_svg=""`）。`ci_v2_lib.py` の EXTRA_CSS は
**正典に無い案件固有ルールと意図的上書きのみ**（正典と重複するルールは 2026-07-07 の ci_head 移行で
削除済み）。**旧世代のトークン名は使わない**。

> 注意: この skill は **データ駆動の週次デッキ生成器**。SLIDE.md の「テンプレ複製・文言差し替え」フローは
> 静的1枚物向け。本 skill はその CSS/トークンに準拠しつつ、表をシートから自動生成する正規パスです。

## CI制約（厳守）

- **テーブルの罫線は横線のみ**（行区切りの下罫線）。**縦罫線はできるだけ使わない**。列のまとまりはヘッダの網掛けで示す。
- 配色は **白 #FFFFFF / 水色 `--crystal` #C3D7EE / 紺 `--ink` #101820 の3色のみ**（SLIDE.md準拠）。緑・赤・グレー・他色相は禁止。**旧名 `--navy`/`--powder`・旧hex #A9CFDF/#0E1A38 は廃止・使用禁止**
  （増減セマンティクスを示す時のみ CI の `--pos`/`--neg`）。
- **丸数字①②③禁止**。「打ち手:1 / KR:1」表記。
- A4横。和文ヒラギノ明朝＋欧文Garamond。ロックアップは「水晶玉＋Strategy, refined.」固定。
- 考察は SMART（目標対比/前年対比の **実数** と期限）。所見はカードで主役化。

## 禁止事項

- CI基盤のCSSを0から書き直す／3色以外を持ち込む
- `config.json`・実スプレッドシートID・OAuthトークン・実顧客ロゴ・POS生データをコミット／外部送信する
- POS等の最高機密の生データ・ASIN・個別売上をスライドに載せる（**集約値のみ**）
- 原本との差異チェックを飛ばして共有する
- 顧客固有の値・ブランド名・所見を `ci_v2_lib.py`（共通ライブラリ）側に書く
