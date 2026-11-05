# 同意画面（#ci-consent）— kit v3.18.0

正本：候補者用の事業プラン資料 v22（2026-11-05 若松さん合格）。見た目と文言は v22 のまま、宛先・資料名・氏名・破棄のタイミングだけを引数にした。

## 使い方

```bash
# 候補者用（既定）：同意するまで本文を見せない
python3 5co-CI-kit/consent/apply_consent.py deck.html -o deck_candidate.html \
  --mode candidate --to recruit@5inc.jp --doc-title "事業プランと期待役割" --name "氏名"
# 社内用：同意画面なし。PDF（印刷）だけ表紙の右上に取扱注意の注記
python3 5co-CI-kit/consent/apply_consent.py deck.html -o deck_internal.html \
  --mode internal --to recruit@5inc.jp --doc-title "事業プランと期待役割"
```

- `--to`：同意メールの宛先（案件ごとに変える）。`--doc-title`：件名と本文に入る資料名。`--name`：件名と本文の氏名（候補者用）。
- `--when`（画面と PDF 注記・既定「面接が終了した時点」）、`--mail-when`（メール本文・既定「面接が終わった時点」）。
- 冪等。キットや共有の場所に候補者の個人名を書かない（氏名は出力ファイルにだけ入る）。

## ふるまい

| | 候補者用 candidate | 社内用 internal |
|---|---|---|
| 画面 | 5co ロゴ＋取扱注意＋「同意して閲覧する」を全面に出し、押すまで本文を隠す | 同意画面なし |
| ボタン | mailto（件名【破棄同意】資料名（氏名）、本文に破棄の同意と氏名）を開き、本文を表示 | — |
| `#static` | 同意画面のまま（本文を出さない） | 通常どおり |
| JS 無効 | 本文を隠し「JavaScriptを有効にしてください」 | 通常どおり |
| 印刷・PDF | 本文を出さない（同意の前も後も） | 表紙の右上に取扱注意の注記 |

同意画面のあいだは表紙・帯のモーションを止め、同意後に再開する（`window.ciBoid` / `window.ciHB`）。

## メモ

- v22 のボタンは「同意して閲覧する」1つ（押すと破棄同意のメールが開き、本文が見える）。「同意しない」ボタンは v22 に無いため入れていない。
- 部品：`consent.css`・`consent_head.js`・`consent.js`・`candidate_print.css`（v22 から抜き出し・編集は正本の更新と同時に）。
