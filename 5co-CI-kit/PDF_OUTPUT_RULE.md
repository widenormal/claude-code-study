# CI スライド PDF 出力ルール（5co-CI-kit 正本）

**Status: APPROVED 2026-10-28 by 若松さん**（PDF は承認制＋HTML 最終ページに「PDFをダウンロード」ボタン＝手元確認用 PDF のダウンロード。印刷ダイアログは使わない）

- 正本: 本ファイル（`5co-CI-kit/PDF_OUTPUT_RULE.md`）。実装＝`make_handout_pdf.py`／`pdf_save_button_snippet.html`。
- 適用対象: すべての CI HTML デッキ（CIスライドBot 制作分）。

## 1. 既定 = HTML のみ
- `*.ci-options.json`（および `.ci-options.json`）は `"pdf": false`。
  - 例: `ci_options.py write <deck.html> --interactive --no-pdf --no-pptx`
- 仕上げは `ci-finalize.sh ... --no-pdf`（PDF を作らない）。
- `interactive: true` の既定は**変えない**。pptx はデッキごとの決定のまま。
- ※ `ci_options.py` は未知キーを拒否するため、JSON に注記キーは足さない。

## 2. PDF を作るのは若松さんが明示承認したときだけ
- 対象: メール送付・社外/社内配布など、配布品質 PDF が要るとき。
- 承認があったら、そのデッキだけ `"pdf": true` にして `ci-finalize.sh --pdf` を回す（フォント埋め込み・#static 最終状態）。
- 承認の記録（いつ・誰に・どの用途）をデッキのフォルダのメモに1行残す。

## 3. HTML 最終ページに「PDFをダウンロード」ボタン（v3・2026-10-28 若松さん確定）
- 最後の本文／クロージング（出典）ページの section 内、**取扱注意アンバーの直下・中央**に置く（`.ci-agree-stack`：アンバー → 「上記に同意して」+「PDFをダウンロード」）。スタック全体 `bottom:48px`（フッター版スタックと ≥16px）。ボタンは 1.5×（font 18px / padding 6px 21px / dot 10.5px）。
- **押すとブラウザのダウンロードが始まる。`window.print()`（印刷ダイアログ）は使わない**（若松さん：印刷ダイアログ不可）。
  - 中身 = 手元確認用 PDF `<stem>_手元確認用.pdf`（Chrome ヘッドレスで #static を印刷したもの・デッキと同じフォルダ）。
  - その PDF を HTML 内に base64 で埋め込み（`<script type="application/pdf;base64" id="ci-handout-pdf">`）、クリックで Blob → `a.download`。
    file:// で開いても、HTML 単体で渡しても動く。埋め込みが無いときは `<a href=隣のPDF download>` にフォールバック。
  - HTML のサイズは PDF 分（約 +2.7MB）増える。
- 作り方は手で貼らず `python3 5co-CI-kit/make_handout_pdf.py <deck.html>`（BLOCK/STYLE/SCRIPT 差し替え → PDF 生成 → 埋め込みを一括）。
  **デッキを直したら必ず再実行**（PDF と HTML の中身をそろえる）。
- 色は CI 正典トークンのみ（`--ink` / `--crystal` / `--crystal-25` / `--ink-14` / `--ink-60`）。目立たせない丸ボタン。
- 部品: `5co-CI-kit/pdf_save_button_snippet.html`（v7）、生成: `5co-CI-kit/make_handout_pdf.py`。
- ヘッダー・フッター・グリッドは触らない。追加後に `ci-gates.sh` を回し、追加前と結果が同じことを確かめる。

## 3b. ボタン左の説明文と取扱注意（若松さん確定・2026-10-28）
- ボタンの**左**に説明文（画面だけ・PDF には出さない）:
  「上記に同意して」（ボタンラベルは「PDFをダウンロード」のまま。旧・手元確認用／メール送付用の長文キャプションは使わない）
- 取扱注意はボタン行の**上**（画面にも、生成 PDF の最終ページにも残す）。2行:
  「[取扱注意] 複数社の機密保持契約の対象・社外秘。許可なき転送・再配布・数値の抽出転載を禁じます。
   漏洩時は契約違反として請求・是正の対象になり得ます。使用後は必ずシュレッダーにかけてください。」
  - 必須要素: 複数社の機密保持契約／社外秘・許可なき転送・再配布・数値の抽出転載の禁止・漏洩時は契約違反として請求・是正の対象・必ずシュレッダー。
  - 使わない言葉: 「訴訟」「刑事」、ベンダー名。「推奨」「など」の弱い表現にしない。これ以上長くしない。
- 印刷 CSS: `@media print { .ci-pdf-save-row{display:none} .ci-conf-note{color:var(--ink)} }`

## 4. 2つの PDF の違い
| | ボタン（手元確認用 PDF をダウンロード） | 承認済み finalize |
|---|---|---|
| 用途 | 手元確認・ちょっと渡す | メール送付・配布 |
| 作り方 | `make_handout_pdf.py` で事前生成 → ボタンでダウンロード | `ci-finalize.sh --pdf`（若松さん承認後のみ） |
| 品質 | Chrome ヘッドレス出力（フォント埋め込み・ゲート未通過でも作る＝確認用） | フォント埋め込み・検査済み |

## 実装記録
- 2026-10-28 15:20 JST: v7。取扱注意の**下**に「上記に同意して」+PDFを**中央**配置（`.ci-agree-stack`）。ボタン 1.5×（18px / 6×21 / dot 10.5）。pad:320 / stack bottom:48 / gap:16。digest フッター左ボタン CSS は非干渉。
- 2026-10-28 15:10 JST: v6。キャプション「上記に同意して」。conf bottom:48 / pdf:175 / pad:232。フッター版スタックとアンバーの衝突解消（≥16px）。
- 2026-10-28 14:45 JST: v5 重なり修正。SCREEN で padding-bottom:196px、PDF wrap bottom:152px（アンバー上≥12px）。near_miss(ci-conf×ci-pdf)解消。
- 2026-10-28: Amazon全体補正 要因グループ図解 CI（本番・digest_trial）の p18（出典ページ・21/21 枚目）に追加。options は pdf:false に変更。
- 2026-10-28: 同 p18 に説明文（ボタン左）と印刷時の機密注意（印刷に残す）を追加（snippet v2）。
- 2026-10-28 14:10 JST: v3 に変更（若松さん確定）。ボタン＝手元確認用 PDF のダウンロード（Blob・埋め込み）、window.print() 廃止。取扱注意を2行版（転送・再配布・抽出転載禁止／漏洩時は請求・是正の対象）に。本番・digest_trial の両方に適用、`*_手元確認用.pdf` を生成。

## 取扱注意ブロック（2026-10-28 確定）

- 最終ページ**中央下部**に**1ブロック**で置く（右下の小さくない）。
- 文言は確定文のまま2行。色は**アンバー**（`--insight` / `--insight-bg` / `--insight-ink`）。
- PDFダウンロードボタン行とは分離。印刷時も取扱注意は残す。
- 配置（v7・取扱注意の下に同意+PDF中央・ボタン1.5×）: 上から 取扱注意アンバー → 「上記に同意して」+PDF行（中央） → 空き → フッター版スタック。`.ci-agree-stack{bottom:48px; gap:16px}`；`section.slide:has(> .ci-agree-stack){padding-bottom:320px}` を**画面でも**適用。印刷時は PDF行非表示・pad 180px。
