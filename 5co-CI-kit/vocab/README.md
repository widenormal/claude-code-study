# Amazon Ads 語彙帳（日本語・英語・中国語）— 使い方

> **スライドやコピーを書くときはこの語彙帳に合わせる。**
> 正本（唯一の格納場所）＝ **`5co-hub/template` の `5co-CI-kit/vocab/`**。派生リポ・共有ドライブ・各 Bot の手元にあるものは写し（`apply-template.sh`／`drive-canonical-refresh.sh` が配る）。写し側で直さず、template へ PR を出す。

## 中身（4ファイル・98 概念）

| ファイル | 中身 | 使いどころ |
|---|---|---|
| `VOCAB_BOOK.md` | 全種類のページ（ja-jp／en-us／zh-cn）で数えた語彙帳。章ごとの表：日本語（Amazon 表記）・English・中文・定義（5 co. の要約）・使う場面・**当社で使う**・**当社で使わない** | 人が読む。言葉に迷ったらここ |
| `VOCAB_BOOK_product-solution-guide.md` | 同じ 98 概念を、種類 product・solution・guide のページだけで数えた版 | 製品説明・解決策の文脈で表記が割れたとき |
| `vocab_book.csv` | `VOCAB_BOOK.md` の機械可読版（出現回数・ページ数・出典 URL・ページ種類別の件数つき） | 検査（`vocab_check.py`）・表計算・Bot が読む |
| `vocab_book_product-solution-guide.csv` | 上の product・solution・guide 版 | 同上 |

CSV の主な列：`key`（概念 ID）・`ja`／`en`／`zh`（Amazon の表記）・`use_5co`（当社で使う表記）・`avoid_5co`（当社で使わない表記）・`src_ja`／`src_en`／`src_zh`（出典 URL）。文字コードは UTF-8（BOM つき＝Excel でそのまま開ける）。

## ルール

1. **スライド・コピー・提案書の文言は「当社で使う」列に合わせる。**「当社で使わない」列の表記は残さない（`COPY_GUIDE.md` ルール6・検収チェック3）。
2. 区分 **当社NG語**（ダッシュボード・リアルタイム・API・ダウンロード・CSV・日次・データ連携 など。語彙帳 11章）は、Amazon が使っていても当社の対外文章では使わない。
3. 5 co. が Amazon や公式・認定パートナーを名乗る、またはそう見える書き方はしない（「Amazon公式」「Amazon認定代理店」等）。
4. 語彙帳は**社内調査用**。Amazon の文章を対外文章にそのまま写さない。定義列は 5 co. による要約。
5. 正式表記の根拠は `../TERMS_AMAZON_ADS.md`（行ごとに公式の出典）と、この語彙帳の出現頻度。食い違ったら出典のある方を採り、語彙帳を直す PR を出す。カテゴリー・商品の単位などは `../TERMS_AMAZON.md`。
6. 社名の英語表記は「5 co.」。データの出典名は「Shelpha」。

## 検査（当社NG語は落とす／表記ゆれは警告）

`ci-gates.sh` が毎回 `vocab_check.py --fail-on ng` を回し、「当社で使わない」表記を **`VOCAB?`** として出す（2026-11-01 若松さん決定）。

| 区分 | 語数 | ci-gates | 例 |
|---|---|---|---|
| **当社NG語**（avoid_5co に「当社NG」・11章 banned_watch） | 15 | **落とす（ゲートNG）** | ダッシュボード・リアルタイム・API・システム連携・ダウンロード・CSV・日次・データ連携・稼働・併願 |
| 表記ゆれ・紛れる言い方 | 31 | 警告（落とさない）。`--strict` では落とす | カテゴリ→カテゴリー・スポンサード広告→スポンサー広告・クリック率→クリックスルー率 |

```bash
python3 5co-CI-kit/vocab_check.py --warn-only deck.html   # 単体
python3 5co-CI-kit/vocab_check.py --list                  # 拾う語の一覧（avoid_5co 列から機械で取り出した語）
```

- 出典欄で Amazon のページ名をそのまま引くなど、残す理由がある箇所は要素か section に `data-vocab-exempt="理由"` を付ける（当社NG語もこれで通る＝理由が残る）。
- kit が差し込む UI（手元確認用 PDF のボタン `data-ci-pdf-save`）の文言は数えない。
- 拾うのは日本語の表記だけ（avoid_5co 列が日本語のため）。英語・中国語は人が「当社で使う」列を見て合わせる。
- 文脈でしか判断できない書き方（「DSP」単独・「新規」とだけ書く・ACOS と TACOS の混用・1文字の「棚」など）は拾わない＝検収チェック3で人が見る。

## 共有ドライブの写し（Google スプレッドシート）

- 置き場所：共有ドライブ **AI-Objective-MGMT / 5co-CI-kit / vocab /**（フォルダ ID `1LUz9vGbpIUEM8CiOtCnG5miMgsXbX9Yp`）
  - 「Amazon Ads 語彙帳（全ページ版）」= `vocab_book.csv` の写し：https://docs.google.com/spreadsheets/d/1uc-MYIXlf6jm8JdmKJ_nTbId66dFY5l8Vkke2u9BMlU/edit
  - 「Amazon Ads 語彙帳（product・solution・guide 版）」= `vocab_book_product-solution-guide.csv` の写し：https://docs.google.com/spreadsheets/d/1HJvjJBU-oqhlJlAjZZ-Q7AKF-KgQlQoDmqBMKz7ZhcE/edit
- **写し（手編集禁止）**。直すときは template へ PR。書き込むのはサービスアカウントだけ。共有は共有ドライブ（と親フォルダ）からの継承のみで、ファイルに個別の共有は付けない。
- 更新：`scripts/vocab_sheet_publish.py --apply`（ID＝`scripts/vocab-sheets.json`・同じファイルを上書き・中身が同じなら何もしない）。GitHub Actions `vocab-sheet-publish.yml`（いまは `scripts/workflows-pending/`・workflow 権限が付いたら `.github/workflows/` へ移す）が main の CSV 更新時と毎日実行する。

## 更新のしかた（担当＝コピーライター Bot）

語彙帳の更新担当は **コピーライター Bot**（2026-11-01 若松さん決定）。再生成したら template へ PR を出す。

1. 生成元（収集 DB・生成スクリプト）は git に入れない。共用作業箱の `knowledge/copy/amazon-ads-db/` で再生成する（`VOCAB_BOOK.md` 冒頭「更新」）。
2. 再生成した4ファイルをこのフォルダへ写し、`VOCAB_BOOK*.md` 冒頭の「正本」行がこのフォルダを指していることを確かめる。
3. template へ PR：`5co-CI-kit/VERSION`・`CHANGELOG.md`・`template-manifest.json`（CalVer）を上げる。表記が変わった語は CHANGELOG に書く。
4. マージ後、派生リポは週次 sync、共有ドライブの CSV・md は `drive-canonical-refresh.sh`、スプレッドシートは `vocab-sheet-publish` workflow で写しが更新される。
