# 5co-CI-kit CHANGELOG（スライド媒体版）

> **これは「スライド媒体」の版ログ**です。スライドの正本は本キット（template `5co-CI-kit`）。
> 全媒体共通の**ブランド版**は Drive `5co-CI/CHANGELOG.md` ＋ `BRAND_GUIDELINE.md` が正。

## 2026-11-01 v3.13.3 — Amazon Ads 語彙帳を kit に同梱／語彙帳の検査 VOCAB?（当社NG語は落とす）

- **語彙帳 `vocab/`**（スライドやコピーを書くときはこの語彙帳に合わせる・正本は template）：コピーライター Bot が Amazon Ads の公開ページ（ja-jp／en-us／zh-cn）から作った 98 概念の語彙帳 v0.2（2026-10-30）の4ファイル＝`VOCAB_BOOK.md`・`VOCAB_BOOK_product-solution-guide.md`・`vocab_book.csv`・`vocab_book_product-solution-guide.csv`。日本語（Amazon 表記）・English・中文・定義（5 co. の要約）・当社で使う／使わない表記・出典 URL。生成元の収集 DB・生 HTML・スクリプトは git に入れない（共用作業箱に置く）。各 md 冒頭の「正本」行を template の `5co-CI-kit/vocab/` に、CSV への参照を同じフォルダに書き換えた（表の中身は不変）。使い方＝`vocab/README.md`。
- **検査 `vocab_check.py`**（stdlib・`--fail-on ng|all`・`--json`・`--list`・`--selftest`）：`vocab_book.csv` の avoid_5co 列から機械で拾える語（46語：当社NG語 15・表記ゆれ等 31）を取り出し、スライドの表示テキストに出たら `VOCAB?`（ページ・語・件数・直し方＝use_5co 列）。使ってよい長い語の一部は数えない（スポンサープロダクト広告・カテゴリー・リアルタイム入札）。文脈でしか決まらない書き方・1文字の語は拾わない。`data-vocab-exempt="理由"`（要素・section）で除外。kit が差し込む PDF ボタン（`data-ci-pdf-save`）の文言は数えない。`ci-gates.sh` に「語彙帳」として接続：**当社NG語（15語）は落とす・表記ゆれ（31語）は警告**（`--strict` では表記ゆれも落とす・`--json` の gates にも入る。2026-11-01 若松さん決定）。
- 導線：`CLAUDE.md` CI 節（Drive の CI 正本ブロックにも載る）・`COPY_GUIDE.md` ルール6／検収チェック3・`CI_KICKOFF.md` 必読・VERSION の `vocab:` 行。
- 型見本の VOCAB? 18件をゼロに：`5co_slide_template.html`「カテゴリ」→「カテゴリー」12件、`5co_biz_briefing_template.html`「カテゴリ」→「カテゴリー」4件・「CCCM（…）ダッシュボード」→「CCCM（…）」・「日次〜週次」→「毎営業日〜週次」（CSS コメントは触っていない）。`5co_slide_template.pdf` は作り直していない（文言1字の差）。
- リポ内の見本も当社NG語をゼロに（ゲートで止まらないように）：`ci-weekly-deck/assets/ci_base_sample.html`・`docs/SLIDE-md/SLIDE-md-5co/sample.html`（週次ダッシュボード→週次の状況一覧）・`docs/SLIDE-PATTERN` 8件（API・システム連携・リアルタイム・ダッシュボード・稼働の言い換え）。リポ内の HTML 142 本で当社NG語 0。表記ゆれの警告は SLIDE-PATTERN・スキル見本に 26 件残る（カテゴリ・顧客接点・転換率＝警告のみ）。
- **共有ドライブの写し**：AI-Objective-MGMT/5co-CI-kit/vocab/ に Google スプレッドシート2枚を作成（サービスアカウント・ID は `scripts/vocab-sheets.json`）。更新は `scripts/vocab_sheet_publish.py --apply`（BOM は送らない・中身が同じなら何もしない・書いた後に照合）と GitHub Actions `scripts/workflows-pending/vocab-sheet-publish.yml`（workflow 権限が付いたら `.github/workflows/` へ移す）。
- 語彙帳の更新担当＝コピーライター Bot（再生成して template へ PR）。
- テスト：`tests/ci-vocab.test.sh` 新設（語彙帳4ファイル・98概念・selftest・当社NG語で落ちる／表記ゆれは警告・exempt・ci-gates 接続・型見本がゼロ・Sheet 化スクリプトの dry-run と設定ファイル）。

## 2026-10-31 v3.13.2 — 持ち上げたフッター行と絶対配置の要素が重ならない（ダイジェスト切替 v1.9.2）

- 不具合（CIスライドが v3.13.1 で `--talk` をかけ直して発見）：全画面に近い大きさ（1124×794・1280×720）で T＋S がフッター行を持ち上げると、絶対配置の要素は動かないので重なっていた。p01 表紙右下の CI 説明（`.cover-ci`）に「CONFIDENTIAL・01」、p13 の「上記に同意して」（`.ci-agree-stack`）にコピーライト。v3.13.1 の確認は絶対配置を本文として数えていなかったので見落とした。
- `digest_toggle.py` の発表・台本ブロックを **`ci-digest-talk v1.9.2`** に（`--talk` で入れ替え・冪等）。持ち上げ中（`html.ci-talk-lift`）は、スライドの直下にある絶対配置の要素のうち**下半分にかかるもの**（下端がスライドの中ほどより下）に JS が印 `data-ci-tk-lift` を付け、フッター行と同じだけ `translate` で持ち上げる。全面の背景（スライドの8割以上を覆うもの）・フッター行・上半分の要素は動かさない。位置は translate の影響を受けない offset で測る。帯を閉じる・`#static`・印刷の前に印を外す＝DOM は元どおり。
- 確認とテストに絶対配置を入れた：フッター行の各要素とスライド直下の要素（絶対配置を含む・全面の背景は除く）が縦横とも重ならないことを見る（`tests/ci-kit-v3.13.1.test.sh` も同じ判定に）。テスト `tests/ci-kit-v3.13.2.test.sh` を追加（表紙の CI 説明・締めの同意欄・背景・右上ロゴの見本で、5つの画面サイズ×上合わせ/下合わせ。v1.9.1 のブロックでは失敗する）。
- ついで：`tests/ci-kit-v3.12.7.test.sh` の `printf | grep -q` が pipefail で時々落ちる（SIGPIPE）ので here-string に。
- 確認（CIスライドのかけ直し前のデッキに `--talk`・Chrome）：T＋S で全13ページ×全画面 1124×794・1280×900・1280×720・幅390・スマホ390×上/下合わせに重なりなし。通常表示・T だけの表示は v3.13.1 と画素まで同じ（全画面・幅390・スマホ390 の 13ページ）。

## 2026-10-31 v3.13.1 — 台本の帯がフッター行を隠さない（ダイジェスト切替 v1.9.1）

- 不具合：v1.9 の発表（T）＋台本（S）を全画面で映すと、画面下の台本の帯（約44px・2行なら約68px）がスライド最下段のフッター行に重なり、コピーライト・版スタック・頁番号・集計期間・「詳細に戻す」ボタンが隠れていた（OPI 定例サンプル・全13ページ）。デッキ側の CSS は `--talk` の入れ替えで上書きされるのでキットで直す。
- `digest_toggle.py` の発表・台本ブロックを **`ci-digest-talk v1.9.1`** に（切替ブロック本体は v1.9 のまま。`--talk` で入れ替え・冪等）。
  - 帯を出しているあいだ（`html.ci-script-on`）：帯の高さを測って `--ci-talk-bar-h` に入れ、`body` の下に同じ余白と `scroll-padding-bottom`＝最後のページも帯の上までスクロールでき、スクロールで合わせると帯の上で止まる。
  - スライドの横が画面に収まり、高さが「画面の高さ − 帯」を超えるとき（全画面・ノートPCの窓）は `html.ci-talk-lift`：フッター行（`.slide::before`／`::after`・`.period`・`.ci-stack`・`.ci-digest-btn`・`[data-talk-footer]`）を `translate` で帯の高さ＋4px だけ持ち上げ、ダイジェストの主役（`.ci-talk-main`）の下にも同じだけ余白を取る（スライドの縮小 zoom も換算）。横がはみ出す細い窓（幅 390 など）は持ち上げず、スクロールで帯の上に出す。
  - 帯を閉じる・`#static`・印刷の前は外して元どおり。CSS はすべて `html.ci-script-on:not(.ci-static)` の下＝通常表示・T だけの表示は変えない。
- 確認（OPI 定例サンプルを `--talk` で組み直し・Chrome）：通常表示と T だけの表示は v3.13 と画素まで同じ（全画面 1124×794・幅 390・スマホ 390 の 13ページ）。T＋S でフッター行が帯の上に全部出る（全画面 1124×794・1280×900・1280×720・幅 390・スマホ 390 の 13ページ×上合わせ／下合わせ）、持ち上げたフッター行と主役・本文が重ならない。
- テスト `tests/ci-kit-v3.13.1.test.sh` を追加（v3.13 のテストは発表ブロックの版 v1.9.x を受けるように）。
- 既知の限界：細い窓（横スクロールになる幅）では帯が数行になるので持ち上げず、スライドの下端までスクロールしたときにフッター行が帯の上に出る（上合わせのときは帯の下）。

## 2026-10-31 v3.13 — ダイジェストの発表（T）と台本（S）／組み方の偏りチェック／差し色イラスト

出典＝CIスライド提案 `_ci_ops/proposals/2026-10-31_uchita_talk-mode_accent-illustration.md`（うちた・note 2026-10-12「アニメーション・プレゼン、AIで簡単に作れた話」／2026-10-08「パワポに貼ると、資料の色に変わるイラストの作り方」）。記事の紙・方眼・蛍光ペン・付箋・手書きフォント・アンバー強調・Google Fonts・テラコッタ等の差し色は採らない（CI の3色トークンのみ）。CSS トークン・寸法は不変。

- **ダイジェスト切替 v1.9＝発表（T）と台本（S）**（`digest_toggle.py`・別の発表モードは作らない）
  - キー `T`／URL `#talk`：hero（`data-digest-keep="hero"`）のある**全ページを一度にダイジェスト**に（もう一度で各ページの元の状態に戻す）。各ページのボタンはそのまま（表示も合わせる）
  - 一括切替が ON のときだけ：見出し2行（1行目＝話題・2行目＝答えに crystal-25 の下線）・上の要点帯（`.gist`）と右の説明カード（`point`・`.dgx-side`／`.dgx-next`／`.dgx-card`・`data-talk-hide`）を外す・hero は最初の1つだけを大きく（`--talk-zoom` 既定 1.25）
  - キー `S`：画面下の台本の帯。文言は section の `data-talk-script`・見出しは `data-talk-h="話題｜答え"`（コピーライターの確定稿を入れる場所だけを kit が持つ）。無ければ「このページの要点」・既存の h2.title「話題｜答え」
  - 通常表示・`#static`・印刷・PDF・検査は不変（T・S を押すまで DOM を変えない・印刷の前に外して後で戻す）
  - 既にダイジェストの付いたデッキには `digest_toggle.py --talk deck.html`（発表と台本のブロック `ci-digest-talk v1.9` だけを足す／入れ替える・冪等）。版は v1.7 → v1.9（未マージの PR #1220 が v1.8 を使っているため飛ばした）
  - **既知の限界**：hero の無いページ（表だけのページ。OPI サンプルの p05・p08〜p12）は T でもダイジェストにならず表のまま映る（見出し2行・要点帯を外すのは同じ）。ダイジェストの図が無いページの見せ方は未定（kit は自動で図を作らない）＝発表に使うデッキは本文ページに hero を置く
- **組み方の偏りチェック**＝`layout_run_check.py`（stdlib・警告のみ・`--json`）。`LAYOUT_RUN?`＝同じ組み方（ページの主役の種類＝表／棒グラフ／図／数字ピル／カード列…・hero があるページは hero の種類）が3ページ以上続く、`ELEMS?`＝見出しと要点を除くページ直下の要素が6つ以上。`ci-gates.sh` に「組み方の偏り」として接続（落とさない・`--json` の gates にも入る）。OPI サンプルで p08〜p12（表5連続）を検出
- **差し色イラスト（2層）**＝FIGURES_GUIDE §2-3。グレーの土台＋差し色の層1か所。差し色は `mask-image` を `var(--crystal)` で塗る＝CI トークンに自動で追従（`ci-illus-v3.13.css` を VERSION の format: に追加・`.ci-illus` にしか効かない）。断片は `ci_figs.py illus base.png accent.png --alt …`、検品は `ci_figs.py lint`（差し色の層ちょうど1つ・土台あり・色の直書きなし・土台がグレー・人物写真は対象外）
- 版番号：未マージの PR #1219 も v3.13 を名乗っている（取扱注意の本人同意ゲート）。後からマージする方が採番し直す
- テスト：`tests/ci-kit-v3.13.test.sh` 新設。ci-cover-motion／ci-kit-v3.11／ci-kit-v3.12／ci-product-images の VERSION 範囲に v3.13 を追加

## 2026-10-31 v3.12.9 — 表紙CIブロックの幅

- 表紙CIブロックの幅を広げ、説明文v2を2行に収める（max-width 62%→68%、text-wrap:pretty）
  - `ci-format-v3.2.css` の `.cover-full .cover-ci` のみ。文言・マークアップは変更なし。
  - 1280幅: 本文2行・`.cover-ci` 上端 674.7→691.7px（`.cf-block` 下端 687.9px より下）。ci-gates の cover 関連 NEAR-MISS（cf-corner×cover-ci, lead×cover-ci）解消。

## 2026-10-31 v3.12.8 — 表紙タグライン・説明文の改訂

- 表紙タグライン改訂（若松さん決定 2026-10-31、サイトの『戦略は、磨き続ける。』にそろえた）：旧「…戦略を磨く」→ 新「水晶玉で市場を透視し、戦略を磨き続ける。」。英語「Strategy, refined.」は不変
- 表紙の説明文を改訂（見出しとの重複を削除、社名表記を「5 co.」に）：`ci_head.py` の `COVER_CI_BODY` と `5co_biz_briefing_template.html` の `.cover-ci` 本文を「…<br>市場は、いつも曇って見える。だから、曇りのない視点で、データの奥にある本質を捉える。「Strategy, refined.」には、その5 co.の姿勢を込めています。」に（決定記録 `2026-10-31_ci-slide_cover-body_v2_final.md`）。BRAND_GUIDELINE.md §0 の説明文（10行目）は変えていない
- 反映先：`ci_head.py` の `COVER_CI_TAGLINE`（`cover_ci_block()` の既定）・`5co_biz_briefing_template.html` の `.cover-ci-h`・`BRAND_GUIDELINE.md` §0・`LOGO_HANDOFF.md`・`V3.2_FORMAT.md`「表紙CIコンセプト」・`README.md`・`CI_KICKOFF.md`・template 側 `docs/SLIDE-md/SLIDE-md-5co/SLIDE.md`
- 決定記録：`/workspace/knowledge/copy/drafts/2026-10-31_ci-slide_cover-tagline_final.md`。過去の CHANGELOG の記述と BRAND_GUIDELINE の「戦略を磨く姿勢」（説明文）は変えていない
- `tests/ci-kit-v3.12.8.test.sh` を追加

## 2026-10-30 v3.12.7 — 人物素材の生成ルール（FIGURES_GUIDE §2-2 追補・文書のみ）

- **出所**: CIスライド依頼（2026-10-30）。同日にフォトディレクター・衣装ディレクターが確定し若松さんが確認した人物素材の作り方を kit の規定へ要約（素材・スクリプトは kit に入れない）
- **追加**: `FIGURES_GUIDE.md` §2-2「人物素材の生成ルール」7項目＝①プロンプトは撮影の状況を書く（美化・品質を盛る語を入れない） ②編集はマスターから1回（チェーン編集禁止） ③窓からの自然光のみ・明暗比 1:3 ④動きは自然に（移動中と会議だけ・大げさな動きなし） ⑤コンサルタント役はラグジュアリー層の装い ⑥肌＝美化語なし・顔の修復なし・AI アップスケールなし・CI の顔は顔幅 180px 以上 ⑦`skin_metrics.py` の出力をレビューに添付
- **変更**: 標準8「審査」＝衣装ディレクター＋フォトディレクターの2段審査を**両方通った素材だけ**を若松さんに見せる
- **出典**（CIスライド側のナレッジ・kit には同梱しない）: `/workspace/knowledge/design/photo_realism/2026-10-30_natural-person-photo-techniques.md`・`photo_director/2026-10-30_baseline-shooting-spec.md`・`photo_director/2026-10-30_portrait-movement-research.md`・`costume_director/2026-10-30_consultant-luxury-tier.md`・`photo_director/skin/`（`2026-10-30_skin-realism-knowledge.md`・`2026-10-30_skin-checklist.md`・`skin_metrics.py`）
- **版番号 v3.12.7**: 文書のみ（CSS・JS・検品ツールは不変）。#1231（v3.12.6／2026.10.12）・#1232（2026.10.13）のマージ後に rebase して積んだ
- `tests/ci-kit-v3.12.7.test.sh` を追加

## 2026-10-30 v3.12.6 — スマホ幅の縮小を既定に／表紙モーション既定 ON／ci-gates.sh --json

- **出所**: CIスライド依頼（2026-10-30）。案件ビルダー（2026-10-30 の週次デッキ）が個別に持っていた MOBILE_FIT・COVER_MOTION を正典へ回収し、検査結果の機械読みを1コマンドにする
- **1 スマホ幅の縮小（MOBILE_FIT）**: `ci_head.style_block()` が既定で `<style id="ci-mobile-fit">`＋`<script id="ci-mobile-fit-js">` を足す。画面幅がスライド幅より狭いときだけ `.slide` を CSS `zoom` で幅に合わせる（スマホ 390px で横スクロールなし）。印刷は `zoom:1`（`@media print`＋`beforeprint`）、URL の `#static`（検査・PDF）・動く資料の発表/一覧モードでは縮めない＝デスクトップ幅・PDF・検査結果は不変。案件側に旧 `deck-mobile-fit-js` があればそちらに任せる。外すときは `style_block(mobile_fit=False)`／`--no-mobile-fit`
- **2 表紙モーション既定 ON**: `style_block()` が `cover_motion/cover_motion.css` を既定で連結（`.cm-field` にしか効かない＝付けない表紙は不変）。新設 `ci_head.apply_cover_motion(html)`（CLI `ci_head.py --apply-cover-motion deck.html [-o out]`）が表紙 `.cover-full` と中扉 `.cover-full.pd-divider` に `cm-field`＋数字断片（kit のファイルをビルド時に読む・`--check` を先に通す・冪等）を足す。足し忘れは `ci-gates.sh` の新しい警告「表紙モーション」＝`cover_motion.py --lint`（COVER_MOTION?・cover has no motion・警告のみ）。外すときは `style_block(cover_motion=False)`／`--no-cover-motion`
- **4 `ci-gates.sh --json`**: 各検査の `--json` 出力（JSON Lines）を1つの JSON 文書にまとめて stdout へ（`--json` を持たない検査は表示文を `text` に）。スキーマ＝新設 `ci_gates_json.py`。終了コードは通常と同じ。**`--json` を付けないテキスト表示は不変**（「表紙モーション」の1行が増えるだけ）
- **検査**: 型見本（`ci_interactive.py --demo`）で `ci-gates.sh` を変更前後で比較＝所見は同一（新しい「表紙モーション OK」1行のみ増）。型見本 `5co_slide_template.html` に ci_head を入れた版で PDF 14頁・本文頁の画素差なし（印刷は不変）、390px で幅に収まることを目視
- **版番号 v3.12.6**: PR #1230（v3.12.5／template 2026.10.11・2026-10-30 16:14 JST マージ済み）の上に積む。並行 PR（キャッシュ同期 2026.10.13・人物素材の生成ルール v3.12.7／2026.10.14）とは番号を分けた＝後からマージする方が rebase して採番し直す
- `tests/ci-kit-v3.12.6.test.sh` を追加

## 2026-10-30 v3.12.5 — 承認済みの人物素材 marketer 3枚を同梱

- **追加**: `digest_person/photo/cutouts/facing_marketer_01_v5_fix.png`・`facing_marketer_02_v4.png`・`facing_marketer_03_v5.png`（alpha PNG）。衣装ディレクター＋フォトディレクターの2段審査を通過、若松さんが本番採用（2026-10-30）
- **配置条件**: `facing_marketer_01_v5_fix` は下端がカウンターの高さで水平に切れているため、スライドの下端か机・カウンター要素に接して置く
- 検品: `cutout_halo_check.py --resize … --bg-residue` 3/3 OK
- facing_*_v3 の5枚（marketer v1〜v3・consumer_01/03 v3）は未承認のまま（v3.12.4 追補のとおり）
- `tests/ci-kit-v3.12.5.test.sh` を追加、`tests/ci-kit-v3.12.2.test.sh` の同梱例外に3枚を追加

## 2026-10-30 v3.12.4 追補 — facing_*_v3 の5枚を「審査待ち（未承認）」に変更

- 人物素材の2段審査（衣装ディレクター＋フォトディレクター・2026-10-30 若松さんの決定）で、5枚ともフォトディレクター不合格（正面・中央・カメラ目線のストック写真型、平らな光）。推奨セットとして使わない・派生リポやサイトへ展開しない。ファイルは残す（削除・差し戻しは若松さんの判断）。差し替えは CIスライドが再生成中で、両審査の通過後に別PR
- 変更は文書のみ（cutouts/README.md・FIGURES_GUIDE §2-2・DIGEST_GUIDE）。VERSION は v3.12.4 のまま

## 2026-10-30 v3.12.4 — 人物素材 v3（正面向き facing_*_v3.png・5枚）を同梱（PR #1220 の v2 の置き換え）

- **出所**: PR #1220（v3.12.1・未マージ）の `facing_*_v2.png` 6枚は再検査で 6/6 が背景色の取り残し（bgres）NG、`make_alpha_facing_v2.py` は穴を不透明で埋める（v3.12.2 で不採用）。元写真から作り直した v3 を置く
- **追加**: `digest_person/photo/cutouts/facing_consumer_01_v3.png`・`facing_consumer_03_v3.png`・`facing_marketer_01_v3.png`・`facing_marketer_02_v3.png`・`facing_marketer_03_v3.png`（alpha PNG・alpha bleed 済み・下端フェードなし）＋`README.md`。**consumer_02 の v3 は未作成**。v2 の6枚・`make_alpha_facing_v2.py` は入れない
- **検品**: 5枚とも `cutout_halo_check.py --resize 1152,813,725,406,362,284,142 --bg-residue` OK（元写真に位置合わせした bgres 込み）。consumer_01（スマホ）は `phone_speck_check.py` も OK。#101820・#C3D7EE に合成して目視
- **規定の変更**: 「人物素材そのものは同梱しない」に例外＝検品済みの v3 の5枚だけ（`FIGURES_GUIDE.md` §2-2・`DIGEST_GUIDE.md`）。`tests/ci-kit-v3.12.2.test.sh` の「kit に人物素材が入っている」を v3 の5枚だけ許すように変更、`tests/ci-kit-v3.12.4.test.sh` を新設
- **版番号 v3.12.4**: 素材の追加と規定の例外のみ（CSS・JS・検品ツールは不変）。v3.12.3（型見本のキッカー削除・2026.10.8）の後に積むため、後からマージする側が版番号をそろえる

## 2026-10-30 v3.12.3 — 動く資料の型見本（ci_interactive.py --demo）のヘッダーからキッカー文字を削除

- **出所**: 若松さん決定（2026-10-29）「ヘッダー左上はロゴのみ・キッカー文字を置かない」（`V3.2_FORMAT.md` 不変条件・`SLIDE_DESIGN_GUIDELINES.md` §5）。v3.12.2 で規定は入ったが、`ci_interactive.py` の型見本だけ各ページのヘッダーに `<p class="kicker">`（例: 「Overview ｜ 流れと時間」）が残っていた
- **変更**: `ci_interactive.py` の `_slide()` から引数 `kicker` と `.hdr`（中身がキッカーだけ）を削除。型見本にはロゴが無いのでヘッダー要素ごと出さない。表紙のアイブロウ（cover eyebrow）は対象外で不変。見出し・要点・本体・操作・根拠パネルは不変
- **版番号 v3.12.3**: kit の出力（型見本 HTML）が変わるためパッチを上げる。CSS トークン・寸法・ライブラリ関数（panel／op／bar_rows ほか）は不変。人物素材 v3 の PR（v3.12.4・2026.10.9）と並行のため、後からマージする側が VERSION・CHANGELOG・manifest をそろえる
- **検査**: 型見本の出力で `ci-gates.sh` を変更前後で比較＝所見は同一（変更前から p4・p5 の重なり3件と FIG? 1件がある・本変更とは無関係で据え置き）

## 2026-10-30 v3.12.2 — 構造で決まる1枚1操作／背景色の取り残し検品／人物素材の標準／要点とギャップ／Branding Design Guidebook β0.6

- **出所**: CIスライド側の引き継ぎ（2026-10-30・若松さん依頼「全てのmdに展開させてください」）。比較の基準＝main `db45842`
- **版番号 v3.12.2**: CSS トークン・寸法は不変。動く資料の CSS/JS に不具合修正（挙動の変更）を含むため版スタンプを上げる。未マージの PR #1220（v3.12.1）・#1219（v3.13）と同じ番号にしない（どちらかが先にマージされた場合は、後からマージする側が VERSION を大きい方へそろえる）。**K1〜K8 をどの版の kit 修正として載せるか＝未決（若松さん回答待ち）**＝本版は暫定
- **1 動く資料（`V3.2_FORMAT.md`「動く資料」・記事 v3〔2026-10-24〕と OPI 試行）**: 構造→見出しの形→操作→静止状態→部品の5列の表に差し替え。全体像からズーム（通常表示でも）・O 一覧・#static／動きを減らす／印刷は組み上がった最終状態・根拠パネル 720px は**出所が書かれたページだけ**（旧「ほぼ全ページ」）・データの無いページは操作なし・表は原本と機械比較・通常表示の重なりも検査。`COPY_GUIDE.md` ルール10（根拠パネルの文言順・出所・alt 定型）・`FIGURES_GUIDE.md` §3-6・`DIGEST_GUIDE.md`（操作の枠は本文直下の子）・`EMPLOYEE_RUNBOOK.md`・`CI_KICKOFF.md`・スキル `5co-ci-slide` を更新
  - **kit 不具合 K1〜K8 を修正**（`ci-interactive-v3.9.css`／`.js`・`ci_interactive.py`。ファイル名は据え置き）: K1 `.ci-stack`→`.ci-vstack`（フッター版スタックと同名で値がフッター位置へ飛んだ）／K2 重ね置きの値は即時切替／K3 根拠パネル 720px／K4 通常表示でもズームで入る／K5 `data-ci-stagger`／K6 SVG の組み上がり原点（`transform-box:fill-box`）／K7 印刷でフォーカス枠を刷らない／K8 `bar_rows(fmt=…, unit=…)` が `{状態: 書式}` の辞書も受ける
  - **未決（若松さん回答待ち）**: ①根拠パネルを操作の数に数えるか ②因果スライダーは入出力ともデッキ内の値のみでよいか ③K1〜K8 を載せる版（上記）。各該当箇所に「未決」と明記
- **2 背景色の取り残し検品 [D] bgres**: 新設 `cutout_bg_residue.py`、`cutout_halo_check.py --bg-residue [--src …] [--bgr-dist 10 --bgr-tol 12 --bgr-margin 20 --bgr-min 30 --bgr-ymax 175] [--bgr-require-src]`。元写真に自動で位置合わせし、輪郭帯・閉じた穴に残った中間調の背景色の塊を NG（確認画像はシアン）。**付けなければ従来と同じ出力**（PNG／フォルダ／デッキ HTML 入力・`--json`・`--warn-only`・`--out`・終了コード 0／1／2・最終行「切り抜き白フチ（N枚）: OK」・`--resize` の既定は不変。デッキ内の画像には bgres を掛けない）。`--selftest --bg-residue` で bgres の自己テスト（clean／取り残し／元写真なし SKIP／`--bgr-require-src`）
  - **運用**: 人物素材（`facing_*`）は納品前に `--resize 1152,813,725,406,362,284,142 --bg-residue` が必須＋目視。シーン素材は警告＋目視（暗い服の毛羽・スマホのカメラの縁などで偽陽性寄り）。`ci-gates.sh --cutouts` は bgres を**当面警告のみ**で回す（`--strict` でも落とさない・`CI_HALO_BGRES=0` で省略・縮小幅 `CI_HALO_BGRES_RESIZE`）
  - **起点**: consumer_03（ボトルを持つ女性）の旧 alpha がポンプの隙間・ボトル左肩・髪右端に灰色の背景を残したまま白フチ検品を通っていた。原因＝旧透過化スクリプトの「囲まれた穴を不透明で埋める」規則（同スクリプトは kit に入れない）
  - `FIGURES_GUIDE.md` §2-2（④bgres・作り方③④・既知の弱点）・`V3.2_FORMAT.md` 規定2・`EMPLOYEE_RUNBOOK.md`・kit `README.md` を更新
- **3 人物素材の標準（`FIGURES_GUIDE.md` §2-2・9項目）**: 機器にもロゴを写さない／機器・小物の縮尺／画面の向き・手指・影／顔の写真らしさ／無地グレー・青で生成＋`alpha/`（alpha bleed 済み）／手前に水色を重ねない・**下端フェード禁止**／オフィス服（黒スーツ×白ブラウス不可）／衣装ディレクター審査／検品（`--bg-residue`・新設 `phone_speck_check.py`・目視）。`DIGEST_GUIDE.md` の旧規定「体の下端は素材側のアルファでフェード（下 14% smoothstep）」を削除し「人物素材（v2 待ち）」を解消。人物素材そのものは kit に同梱しない
- **4 要点とギャップ／ヘッダー**: `COPY_GUIDE.md` ルール9・`V3.2_FORMAT.md`「このページの要点」に「要点＝OKR から逆算した最大のギャップ要因1つ・施策と対（→施策 p○／施策（案）要確認）」を転記。ヘッダー左上はロゴのみ（キッカー文字を置かない）を `V3.2_FORMAT.md` 不変条件・`SLIDE_DESIGN_GUIDELINES.md` §5 に追加し、`SLIDE_DESIGN_GUIDELINES.md`・`DIGEST_GUIDE.md` のキッカーの記述を削除（正本＝ブランドガイドブック β0.1）
- **5 Branding Design Guidebook β0.6**: β0.3（人物の手前の水色・下端フェードの禁止）・β0.4（図版テンプレートの共通化）・β0.6（人物素材・切り抜き検品・動く資料の案）を同梱。β0.5 は社内限定章のため同梱しない
- **入れなかったもの**: PR #1220 の人物素材 `facing_*_v2.png` 6枚（再検査で 6/6 bgres NG）と透過化スクリプト、人物素材の画像（v3 の作り直し素材を含む）、ブランドガイドブック β0.5、衣装の社内スタイルガイド本文（要約のみ）
- テスト: `tests/ci-kit-v3.12.2.test.sh`（新設）・`tests/ci-kit-v3.12.test.sh`（版スタンプ・「v2 待ち」の更新に追従）

## 2026-10-30 — 切り抜き白フチ検品（v3.12 追補）

- **新設 `cutout_halo_check.py`（強化版＝CIスライド v2 の判定を移植）**: 切り抜き人物 PNG の白フチ（ハロー）を3種類で検出し、どれか1つでも塊があれば `HALO?`
  - **edge**: 輪郭3px以内で暗い髪に隣接した白っぽい画素の塊（40px以上・初版と同じ。元幅の半分未満への縮小判定では使わない）
  - **blob（新）**: 背景の白に近い不透明な塊で透明部に接し、周りの過半が髪・肌のもの。**帯より太い塊も大きさ不問**（`--min-blob 12`）。旧デフリンジで灰色に塗られた平坦な塊も拾う。服サイズの明色（不透明面積の `--cloth-frac 0.015` 以上）は対象外
  - **ink（新）**: 濃紺 #101820 に合成し、輪郭が内側より `--margin 0.16` 以上明るいもの（**暗い背景で光るフチ**・脱汚染していない毛先）
  - **`--resize W1,W2,…`（新）**: 各幅に普通の（非プリマルチプライ）縮小をかけて再検査（alpha bleed していない素材の**縮小時だけ出る白線**）。元幅以上は無視。推奨 `--resize 1152,813,406,284,142`
  - キット側の機能は維持: PNG／フォルダ（png/webp/avif/gif/tif・開けない形式は SKIP）／デッキ HTML（`<img>` のローカル PNG と `data:image/png`・透過を持つものだけ）、`--json`、`--warn-only`、`--selftest`（clean／edge／帯より太い blob／縮小時だけの白フチ／alpha bleed 済み／幅1px線）、`--out` の確認画像（濃紺背景に edge=赤・blob=マゼンタ・ink=橙）、終了コード 0／1／2、最終行「切り抜き白フチ（N枚）: OK」
  - **デッキ内の画像だけ**は幅か高さ1pxの塊と ink を数えない（グラフ線と、白地で抜いたロゴのアンチエイリアスが濃紺合成で光るだけの誤検知を防ぐ）。素材 PNG／フォルダは正本と同一判定
- **`ci-gates.sh` に接続（警告）**: デッキ内の透過 PNG を毎回検査（縮小判定なし・`CI_HALO_DECK_RESIZE` で有効化）。`--cutouts <alpha_dir>` で素材フォルダも検査し、こちらは既定で `--resize 1152,813,406,284,142` 込み（`CI_HALO_RESIZE` で変更・空で無効）。`--strict` で落とす
- **FIGURES_GUIDE §2-2**: 白フチ検品の3種類と縮小判定、人物素材の切り抜き標準（元写真から・髪だけ matting・脱汚染・alpha bleed 必須・縮小込み検品・#101820／#C3D7EE 合成の目視）を追記
- 起点: 5co.ltd「ECと店頭」記事の `ec_c01_phone_browse` 左肩の髪に白が残っていた（2026-10-30 若松さん指摘・既存ゲートは全 OK で見逃し）。初版（輪郭帯のみ）は作り直した `ec_c01_phone_browse_v3` の頬・耳横の白い塊を見逃したため、CIスライドの強化版（HALO_CHECK_HARDENING）に差し替え
- 検証: OPI サンプルの切り抜き28枚で、新規・作り直し9枚（v4 ×3・8歳の娘・タクシーのコンサル・オフィス/会議 v5 ×4）は `--resize` 込みで全 OK、`ec_c01_phone_browse_v3` は NG（左頬・右耳横の白い塊）。旧素材を含め NG 7枚（`--resize` 込み 9枚）＝CIスライド正本と同一結果。サンプルデッキはロゴ等の誤検知 0（旧素材を埋め込んだダイジェスト2本だけ実際の白フチで警告）
- VERSION スタンプは v3.12 のまま（後方互換の検査追加のみ）

## 2026-10-29 v3.12 — ダイジェスト Amazon人物型／固定要素の重なりゲート／Branding Design Guidebook β0.2

- **後方互換の docs/helpers/ゲート追加のみ**。CSS トークン・寸法は v3.11 から不変（版スタンプ v3.12）。付けない既存デッキの見た目は変わらない
- **A ダイジェスト Amazon人物型（2026-10-29 若松さん採用）**: `DIGEST_GUIDE.md` に型 `data-dg-layout="cutout"` を追加。人物（無加工・`.dgx-person`）は片側1/3、背後に #C3D7EE 角丸面・頭が上端からはみ出す。反対側に大きな数字ピル（`--serif-en` は数字と % だけ）＋施策1行＋`→ pNN` リンク／`← 戻る`／`#digest=pNN` フック。ダイジェストではアンバーの要点ラベルを出さない。部品＝新設 `digest_person/`（`digest_person.css`・`digest_jump.js`・`markup_example_p06.html`。人物素材は同梱しない）
- **B 人物素材・写真リアリティ手法は v2 待ち**: 人物素材の合否基準（10項目）・REALISM_METHODS・透過化スクリプト・facing_* v1 素材は kit に入れない（2026-10-29 若松さん: v1 は肌がイラスト調）。v2 で確定後に追加。v3.12 はレイアウト規定（人物は架空・無加工・alt 明記）のみ（`DIGEST_GUIDE.md`「人物素材（v2 待ち）」・`FIGURES_GUIDE.md` §2-2）
- **C 固定要素の重なりゲート**: 新設 `check_fixed_overlap.py`（コーナーロゴ・`.slide::before/::after`〔`counter()` 頁番号を実寸化〕・`.ci-stack`・`.period`・`.ci-digest-btn` × 文字・画像・色面ボックス、static／screen／digest × 7 ビューポート、4×4px 超で exit 1・`--json`・`--selftest`＝コーナーロゴ×色面ボックス／頁番号×本文）。`ci-gates.sh` に接続（落とす）。あわせて `data-digest-keep="hero"` があるデッキは `check_text_overlap.py --digest-mode` も落とす。起点＝p13 取扱注意×コーナーロゴ（既存ゲートは全 OK で見逃し）
- **D Branding Design Guidebook β0.2 を同梱**: 新設 `brand_guidebook/`（`BRANDING_DESIGN_GUIDEBOOK.md`・`DIGEST_DESIGN_RULES.md`・`VERSION`・`README.md`）
- **右余白ルール×人物型の使い分け（確定・2026-10-29 若松さん決定（CIスライド経由））**: 施策がそのページ（概要ページ）にあるときは右余白＝施策カード欄、施策を別ページに分割しているときは人物型（`DIGEST_GUIDE.md`「右余白ルールとの使い分け」・`brand_guidebook/README.md`）
- **既知の差分**: `digest_toggle.py` は v1.7 のまま（フッター位置修正 v1.8 は未承認の別ブランチ・本版に含めない）
- 検証: OPI 定例 v3.11 サンプル `*_digestCutout_all.html` で `ci-gates.sh` OK（固定要素の重なり 13頁×21実行 overlaps=0）
- テスト: `tests/ci-kit-v3.12.test.sh`

## 2026-10-29 — PRODUCT_IMG? 商品名検品／ダイジェスト定義

- **検品拡張**: `product_image_check.py` が ASIN に加え CamelCase／PascalCase 商品名トークン（例 NailEnvy）でも `PRODUCT_IMG?`。ロゴ（`cl-logo`）・ダイジェスト写真（`dg-photo`／`figs/digest`）は商品画像に数えない。`--selftest` 追補。正＝`FIGURES_GUIDE.md` §2-1 検品 bullet／`VERSION` `product-images:`（若松さん指示「検品を商品名にも効かせる」）。warn-only・VERSION スタンプは v3.11 のまま
- **ダイジェスト clar**: `DIGEST_GUIDE.md`／`digest_toggle.py` — 要点（`.gist`）＋視覚ちょうど1つ、または **数字＋写真**。切替ボタンは情報量の多い本文頁のみ（カバー／TOC／中扉／薄い頁は付けない）
- **ゲート追補**: `check_text_overlap.py` に `--digest-mode`／`CI_OVERLAP_NO_STATIC`（ダイジェスト見た目の重なり検査）。`svg_label_check.py` はカバーモーション（`.cm-field`／`cm-svg`）の数字 SVG を除外

## 2026-10-28 v3.11 — ダイジェスト／PDF承認制／画像必須強化

- **後方互換の docs/helpers 追加のみ**。CSS トークン・寸法は v3.10 から不変（版スタンプのみ v3.11）
- **A ダイジェストモード（APPROVED）**: 新設 `DIGEST_GUIDE.md`＋`digest_toggle.py`。「このページをダイジェストにして」で指定ページだけ薄くする（既定はフル密度）。ヘッダー／フッター／グリッド不変・数字は元ページのみ・Shelpha・`#static`/印刷は常にフル・Ads 橙禁止。切替ボタン＝フッター最左 `left:36px; bottom:12px`
- **B PDF 承認制＋手元確認用ダウンロード（APPROVED）**: 新設 `PDF_OUTPUT_RULE.md`＋`make_handout_pdf.py`＋`pdf_save_button_snippet.html`。既定 HTML のみ。メール送付用高品質 PDF は若松さん明示承認後のみ `ci-finalize --pdf`。HTML 最終ページに `a.download`（`window.print` 禁止）・取扱注意アンバー確定文
- **C 画像アセット強化**: `FIGURES_GUIDE.md` §2-1 を強化（写真多用・企業/組織/商品名→ロゴ必須・商品/ASIN→商品画像必須・カテゴリー→生成または取得）。`VERSION` `product-images:` 拡張（検品は従来どおり warn-only）
- **D 既定の明文化**: `interactive: true`／`figs_multiagent: true` が既定（オプトアウトはユーザー明示時のみ・standing 2026-10-06）。nudge／出力オプション文言を承認制 PDF に合わせて更新
- **VERSION**: 先頭 `v3.11`／`date: 2026-10-28`。`digest:`・`defaults:`・強化 `outputs:`／`product-images:`。format CSS 宣言は不変
- **E 表紙モーション同梱**: `cover_motion/` を **layer8_spin_spread_v3** に更新（表紙/中扉とも digits 620・全8帯・中扉=白地+#C3D7EE字）。Eddy/gust/v1.1 は入れない。正＝`COVER_MOTION_HANDOFF.md`
- **範囲外**: CHARACTER_FACES・案件ローカル写真資産
- テスト: `tests/ci-kit-v3.11.test.sh`

## 2026-10-28 v3.10 追補 — 表紙・中扉カバーモーション

- **任意層**: 表紙・中扉の CSS keyframes モーション（`cover_motion/`）。メール軽量＝動画/GIF/大画像なし。デッキごとに opt-in（付けない既存デッキは不変）
- **採用（2026-10-28・若松さん指定復元）**: keyframes `cmDriftNear/Mid/Mid2/Far` + `cmSpinSway/CW/CCW`；digits 表紙 620 / 中扉 310；NO sphere。Ignite 名禁止（データ元 Shelpha）
- **部品**: `cover_motion.css`（`html.ci-static` / print / reduced-motion 凍結込み）・`digits_{cover,div}.svgpart`・`cover_motion.py`（`--css`/`--cover`/`--div`/`--check`）・正＝`COVER_MOTION_HANDOFF.md`
- **関係**: 静的 Oracle（`assets/numfield_*.svg`・`NUMFIELD_HANDOFF.md`）は残す＝`.cover-full.cm-field` が `.numfield-full` を隠して `.cm` を載せる。`ci_head --interactive`（動く資料）とは独立
- **履歴**: Eddy 4-layer（`*.locked_eddy`・2580 digits）は demoted＝本 kit に入れない
- **VERSION**: `cover-motion:` 行を追加（先頭の `v3.10` は不変）。CSS トークン・寸法は不変
- テスト: `tests/ci-cover-motion.test.sh`

## 2026-10-26 v3.10 追補 — 商品画像

- **規定**: スライドに商品名・ASIN が出るときは、可能な限り商品写真を `data:image/...` で埋め込む（外部 URL 禁止）。枠組み図は従来どおり CI 描き直し；実物 SKU 識別用の写真は書籍表紙と同じ写真例外。置けないときは `data-product-img-exempt="理由"`。スライド上に「Ignite」と書かず、データ出典は Shelpha
- **正本**: `FIGURES_GUIDE.md` §2（画像の例外を拡張）・新設 §2-1／`V3.2_FORMAT.md` 図・イラスト節に横断参照／`VERSION` に `product-images:` 行（先頭の `v3.10` は不変）
- **検品**: 新設 `product_image_check.py`（`PRODUCT_IMG?`・`--warn-only`／`--selftest`）。`ci-gates.sh` に警告として接続（ゲートは落とさない＝`footer_stack_check` と同型）
- **スキル**: `.claude/skills/5co-ci-slide.md` の figs 手順に商品画像の1行を追加
- CSS／トークン／寸法は不変（v3.10 スタンプのまま・後方互換の規定追補）

## 2026-10-06 — フッター版スタック（CI / Shelpha / Template）

- **追加**: コピーライト左側に `CI vX.Y · Shelpha … · Template YYYY.MM.N` を常設（若松さん指示）
- **正本**: `VERSION` / 新設 `SHELPHA_VERSION`（未設定は `—`） / `template-manifest.json`
- **注入**: `ci_head.py`（`--footer-stack` / `style_block` 末尾）。`.period` 頁は中央右へ退避
- **検品**: `footer_stack_check.py`（`ci-gates.sh` 警告）
- **規定**: `SLIDE_DESIGN_GUIDELINES.md` §5.5・`V3.2_FORMAT.md` フッタ行・`CLAUDE.md` 1行
- CSSトークン・寸法は不変（v3.10 のまま・後方互換の表示追加）

## 2026-09-30 v3.10 追補3 — 図を自動で入れる（案A：マルチエージェントの選択／案B：表・箇条書きから自動で作図）

- **案A**：作成依頼時の質問（`ci-slide-options-nudge.sh`）に「④図・イラストをマルチエージェント（作成→レビュー）で仕上げる」を追加。
  `ci_options.py write … --figs-multi|--no-figs-multi` で `figs_multiagent`（任意・省略時 false）を記録。選ばれたら Claude が
  `workflows/ci-deck-figures.js` を実行する（④の選択＝利用者からのマルチエージェントの依頼）。`ci-finalize.sh` の出し分け（read）は不変
- **案B**：`ci_figs.py autofig`（と `ci_figs.autofig()`）を新設。図の無い本文ページに、表（数値の列→横棒・合計行は除外）／
  2列の箇条書き（左右の対応図）／順番のある箇条書き（流れ）／その他の箇条書き（一覧カード・矢印なし）から図を自動で作る。
  週次・月次ビルダー（`build_deck.py`・`build_wella_deck.py`）は `ci_v2_lib.add_autofigs` で生成の最後に自動で呼ぶ
- `ci_figs.py coverage` が ci-weekly-deck の章扉（`slide dark divider`）を本文と数えていた誤検知を修正
- スキル `5co-ci-slide`・`ci-weekly-deck`、FIGURES_GUIDE 0-1、V3.2_FORMAT（出力オプション表）、VERSION を更新
- 検証：見本データの週次（14枚）・WELLA 月次（8枚）デッキをビルダーで生成し、自動の図が要点ページに入り `ci-gates.sh` OK（図の無いページ OK）。
  旧見本（文章・表だけ）に autofig を当て、対応図・横棒・流れを PNG で目視。`ci_figs.py --selftest` に autofig の回帰を追加
- 外部 LLM は使わない（Claude のアカウントだけの社員でも同じ手順を再現できるように）

## 2026-09-30 v3.10 追補2 — 週次デッキの見本を「図を使う版」に更新

- `ci-weekly-deck/assets/ci_base_sample.html`：文章・表だけだった本文4ページに図を追加（課題→打ち手の対応図／投資と想定効果の横棒／時間をかける領域の同心円／4ステップのシェブロン）。章扉ページは `data-fig-exempt="章扉"` で明示。図の断片は `assets/figs/`（`ci_figs.py inject` の見本を兼ねる）
- 検証：`ci_figs.py coverage` OK・`ci-gates.sh --figs` OK（表紙の COVER_CI? 警告は従来からの既存事項）・4ページを PNG で目視

## 2026-09-30 v3.10 追補 — 図の既定を「止まる」まで徹底（スキル・仕上げゲート）

- **`ci-finalize.sh` に図ゲート**：本文ページに図（フレームワーク図・グラフ・イラスト）が無いと止まる（`ci_figs.py coverage --strict`）。
  表だけで足りるページは `data-fig-exempt="理由"`。今回だけ通すときは `--allow-no-figs "<理由>"`（理由が出力に残る・理由なしは止まる）。
  制作中の `ci-gates.sh` は従来どおり警告（作業を止めない）
- **スキルに手順を追加**：`5co-ci-slide`（手順6.5「図は既定で使う」・7.5「図の無いページをゼロに」・完了条件）、
  `ci-weekly-deck`（図は既定で使う・図の無いページ検査・禁止事項）
- **影響**：既存の週次・月次ビルダー（`ci-weekly-deck`）の出力は表中心のため、そのままでは仕上げで止まる。
  表の下にイラスト・ミニ図を添えるか、付録ページに `data-fig-exempt` を付ける（移行期は `--allow-no-figs "<理由>"`）
- **不具合修正（ci-finalize.sh）**：印刷用CSSの注入に使う awk へ改行を含む文字列を渡していたため、macOS の awk が「newline in string」で止まり、`</head>` のある通常のデッキで注入が失敗していた。CSS を1行にした。あわせて、変数の直後に全角文字が続く3か所（`$OUT_DESC（`・`$SRC（`・新設の理由表示）を `${…}` で囲んだ（macOS 標準の bash 3.2 が全角文字まで変数名と読み「unbound variable」で止まる・動く資料の仕上げで発生し得た）
- テスト：`tests/ci-figs.test.sh` に仕上げゲート（止まる・理由つきで通す・理由なしは止まる・例外は通す）とスキルの記述を追加

## 2026-09-29 v3.10 — 図・イラスト（figs）の標準化

**後方互換の追加のみ。CSS トークン・寸法は v3.9 から不変（`ci_head.py` の出力は版スタンプの版番号だけが変わる）。**

### 追加
- **既定で図を使う（0章）**：指示が無くても本文ページには原則すべてフレームワーク図・グラフかイラストを置く。`ci_figs.py coverage` が図の無い本文ページを `FIG?` で挙げ、`ci-gates.sh` が毎回警告する（表だけで足りる付録は `data-fig-exempt="理由"`、HTML/CSS の図解は `class="ci-fig"`）。作成依頼時のフック `ci-slide-options-nudge.sh` もこの既定を毎回伝える
- **規定 `FIGURES_GUIDE.md`**：図・イラストの描き方（3色の CSS 変数のみ・書体を書かない・文字10px以上・線画ピクトグラム）／置き方（本文の下に in-flow・1ページ1図・ページにない事実を足さない）／原本の図の再構成（画像を貼らず構成と言葉に忠実に描き直す・個人名は役割名へ）／検品と目視／マルチエージェントの進め方
- **`ci_figs.py`**：`inject`（figs/<ページID>.html を本文末尾＝出典の直前に差し込む・元デッキは上書きしない）／`lint`（3色トークン以外の色・外部参照・script・font-family・10px 未満の文字）／`preview`（指定ページだけを 1123×794 の PNG に＝#static）／`--selftest`
- **`ci-gates.sh --figs <dir>`**：図の断片の検品をゲートに同居（落とす）
- **`workflows/ci-deck-figures.js`**（ページグループごとに「作成→レビュー・修正」を pipeline）・**`workflows/ci-figure-competition.js`**（方向性の違う4案→観点の違う審査員3人が4観点×10点で採点→優勝案に他案の良い点を取り込んで仕上げ）

### 由来
- 自社OKR会「育成者の育成カリキュラム」デッキ（2026-09-29・29枚）で、17ページの図を10エージェントで並列制作（作成→レビューの2段・約7分）し、WISDOM サイクル図を4案のデザインコンペで決めた（エディトリアル案が 98 点で優勝し、リング型の矢印・番号付けを取り込んで仕上げ）。案件ローカルの `figs/` 差し込み・ページ単位プレビューのスクリプトを正典に回収した。
- 回収時に見つかった不具合を修正：根拠パネル（`<template>` 内の入れ子 `<section>`）があるページで、スライドの終端を「最初の `</section>`」と誤認し、差し込み位置・図の有無の判定がずれていた（次のスライドの直前にある最後の `</section>` を終端にする）。誤検知の修正：`border-radius` を色指定と誤読しない／数字を欧文にする `font-family:var(--serif-en)` は許可。

### 検証
- `ci_figs.py --selftest` 合格（差し込み位置・ページ番号キー・存在しないキーの報告・色/外部参照/script/書体/文字サイズの検出・data: 画像の中身を見ない）
- 実デッキ（29枚）の図 17 断片＋コンペ仕上げ版 1 点を `lint` で全件 OK、`ci-gates.sh --figs` でゲート OK、`preview` で section id とページ番号の両方のキーを確認
- `tests/ci-figs.test.sh` を新設

## 2026-09-28 v3.9 追補 — 出力の既定を HTML のみに（PDF は質問で選ばれたときだけ）

- `ci-finalize.sh` の既定を「PDF＋PPTX」から **HTML のみ** に変更（ユーザー指示 2026-09-28）。
  `<デッキ名>.ci-options.json` が無く、コマンドにも `--pdf/--pptx` が無いときは PDF・PPTX を作らない（検査ゲートは従来どおり走る）
- 作成依頼時の質問（`ci-slide-options-nudge.sh`）の文言に「既定は HTML のみ」を明記。PDF は質問で選ばれたときだけ出す
- 手順書（`V3.2_FORMAT.md`「出力オプション」・`CI_KICKOFF.md`・`VERSION` の outputs 行・`5co-ci-slide`・`ci-weekly-deck`）を同じ内容に更新
- 以前の既定（PDF＋PPTX）に頼っていた運用は `--pdf --pptx` を付けるか、質問で PDF・PPTX を選ぶ

## 2026-09-27 v3.9 — 動く資料（押すと根拠が開く）・出力オプション化（PDF を任意に）

**後方互換の追加のみ。CSS トークン・寸法は v3.8 から不変（`--interactive` を付けない既存デッキの見た目は変わらない。
`ci_head.py` の既定出力は版スタンプの版番号だけが変わる＝実測で差分1行）。**

### 追加
- **動く資料の層**：`ci-interactive-v3.9.css` / `ci-interactive-v3.9.js`（VERSION の `interactive:` 行が宣言・
  `ci_head.py --interactive` のときだけ連結）＋部品ヘルパ `ci_interactive.py`（型見本 `--demo`）
  - 根拠パネル（右から740px・タブ2つまで・出所必須）／1枚1操作（切り口・前後・スライダー・打ち手オン/オフ）／
    組み上がり（見出し→図→数字→根拠）／O 一覧・F 発表モード・数字キーで移動
  - 6構造→操作の対応を `V3.2_FORMAT.md`「動く資料」に規定。出典＝uchita_success 氏の X 記事（2026-09-26）。
    記事の色・書体・18px 下限・見出し36字は採らず CI v2 に合わせた
- **出力オプション**：`ci_options.py`（`<デッキ名>.ci-options.json` の記録・読み出し）。`ci-finalize.sh` に
  `--pdf/--no-pdf/--pptx/--no-pptx/--options` を追加し、ci-options.json を読んで出し分ける（ファイルが無ければ従来どおり PDF＋PPTX）
- **作成依頼時の自動質問**：`.claude/scripts/ci-slide-options-nudge.sh`（UserPromptSubmit・登録済みの
  `session-claudemd-nudge.sh` から呼ぶ）。作成依頼を検知すると「出力オプションを AskUserQuestion で1回聞く」を Claude に伝える

### 変更
- 検査スクリプト（`slide_overflow_check.py` / `check_text_overlap.py` / `graph_node_edge_check.py` /
  `slide_visual_regression.py`）と `scripts/html_to_pptx.py`・`ci-finalize.sh` の印刷は URL に `#static` を付けて開く
  （動く資料を組み上がった最終状態で検査・出力する。静的デッキでは何もしない）

### 修正（既存の不具合）
- **`ci-finalize.sh` に相対パスでデッキを渡すと PDF が1ページになっていた**。印刷用の一時ファイルを
  `file://./.ci-finalize…` という壊れた URL で開き、Chrome がエラーページを1枚だけ PDF にしていた
  （実測：10枚の型見本が1ページ）。一時ファイルを絶対パスにし、空白・日本語を含むパスも開けるよう URL エンコードした
  （実測：相対パス・「案件 フォルダ」とも 5枚→5ページ）

### 独立検品（Codex）で直したもの
- `#static`（検査・PDF）では操作を受け付けない／印刷の前に発表モード・一覧・根拠パネルを外し、印刷後に元の状態へ戻す
- 根拠パネル：Tab をパネル内で回す・入力欄の中からでも Esc で閉じる・`aria-label`／`role=tabpanel`。隠れた要素は `inert`
- 数字キーの途中で別の操作をしたら取り消す／値の検証（非数・負の値・0 の `data-ci-max`）／`<a href>` に付けても遷移しない
- 出力オプション：知らない項目（打ち間違い）・未決の項目で止める（既定値で埋めない）／選択と HTML の組み方の食い違いを両方向で止める／
  今回選んでいない物が前回分として出力先に残っていれば警告／finalize の引数検査（値なし・知らないオプション）
- 作成依頼の検知：大文字小文字を区別しない・「パワポ」「presentation」等を追加・「作らないで」では鳴らさない・
  バックグラウンド処理の完了通知では鳴らさない（このセッションで実際に誤って鳴ったため）

## 2026-09-08 v3.8 — 要点(gist)・琥珀の汎用化・Amazon用語の正典化

**後方互換の追加のみ。CSS トークン・寸法は v3.7 から不変（既存デッキの見た目は変わらない）。**

### 追加（ドリフトの回収）
- **`ci-gist-v3.8.css` 新設**（VERSION の `format:` に追加＝ci_head 経由で全案件へ自動配布）
  - `.gist` / `.gist-k` … 「このページの要点」。見出し直下に1つ置き、読者が要点だけ拾い読みできるようにする
  - `td.chl` … 洞察強調（琥珀）を **`table.sk` 限定から全テーブルへ汎用化**し、hex 直書きからトークン（`--insight` 系）へ。v3.2 の `table.sk td.chl` は互換のため残置
  - `.wrapcell` / `.sho-h.lite` … 表セルの折り返し・罫なしの軽量小見出し
  - 根拠: WELLA ProHair「7カテゴリ統合ASIN構成分析」と WELLA OPI「ネイル7カテゴリ統合ASIN構成分析」の
    2デッキが `.gist` `.gist-k` `.sho-h` `td.chl` `.wrapcell` を**同一値で自前定義**していた（正典に無いため）
- **`V3.2_FORMAT.md`** に「このページの要点（gist）」節を新設。順序＝見出し→要点→図の読み方→本体を規定。
  要点が1〜2文で書けないページは1ページ1メッセージになっていない＝分割を検討、と明記

### 文言（新ルール）
- **`COPY_GUIDE.md` ルール6「業界の正式用語を使う（独自の言い換えを作らない）」を制定**（5箇条→6箇条）。
  検収チェックに「用語集の禁止語を全文検索」を追加
- **`TERMS_AMAZON.md` 新設**（Amazon 案件の用語集）。カテゴリー／ブラウズノード／親ASIN・子ASIN／SKU／
  BSR／ACoS・TACoS・ROAS／NTB 等の正式用語と、使ってはいけない言い換え（棚・帯・天井・主戦場・稼働・
  定常月・未参入）を対で規定
  - 根拠: ULTIME 統合版で造語「併願」が Amazon 仕様と食い違い全ページ修正（2026-09-07）。
    翌日 OPI 統合版でカテゴリーを「棚」と書き（22枚中246箇所）、読み手から
    「棚数とは？カテゴリー数のこと？」と確認が入った。**2件続いたため正典化**

### 案件側の対応
- 既存デッキは**そのまま動く**（ローカル定義が正典と同値のため、上書きしても結果が変わらない）
- 次回改訂時にローカル定義を削除して正典に寄せる。**移行時の注意が1点**:
  ローカルの `.sho-h`（罫なし・淡色）は正典 `.sho-h`（crystal の縦罫付き）とは別物。
  ローカル定義を消すだけだと縦罫が付く。**`class="sho-h lite"` に書き換える**こと
- Amazon 案件の新規・改訂デッキは `TERMS_AMAZON.md` に従う

### フレームワーク図ヘルパーの追加（2026-09-08）

- **`ci_frameworks.py` 新設**：CI v2（A4横・3色）で描くフレームワーク図の SVG ヘルパー9型
  （mekko／heatmap／funnel／bubble／ranges／waterfall／slope／concentric／tree）
  - 案件ビルダーから**関数1本**で呼べる。返り値は `<svg>…</svg>` の文字列・外部依存なし
  - 色は正典トークンのみ。琥珀は「その図の洞察が言及する要素」だけ
  - `--demo` で9型の型見本 HTML を書き出す（そのままゲートを通せる＝動作確認を兼ねる）
  - `scripts/ci_pattern_adapter.py`（129種の静的見本を変換）とは用途が別。併存させる
- **`bars_line`（棒＋折線）を追加して10型に**。月次推移に自社シェアを重ねる定番。
  観測が無い月は**線を切り**、観測が薄い月は**棒を中抜き**にする＝欠測をごまかさずに描く
- **実戦投入の記録**：WELLA OPI ネイル統合版の12ページを表とテキストから図に置き換え、
  その過程で6箇所を改良した
  - mekko: シェア0の強調列を琥珀の点線枠で「空き」として見せる（最大市場が空白、が一目で伝わる）
  - bubble: `xlog` / `xticks` を追加＋ラベルの重なり回避（線形軸では左端に団子になっていた）
  - funnel: 幅の下限を25%に（比が122倍でも文字が図形に収まる）
  - slope: ラベルの上下ずらしと引き出し線、同じ上限値の点線は1本だけ
  - concentric: 円を左40%・凡例を右60%に分離（凡例が切れていた）
  - ranges: 右の注記が viewBox の外に出ないよう余白を拡張

### 軽量ランナーの追加（2026-09-08）

- **`ci-gates.sh` 新設**：検査だけをまとめて走らせる（`slide_overflow_check` → `check_text_overlap`
  → `graph_node_edge_check`（`.ne-graph` があるときだけ）→ `svg_label_check`）。**PDF/PPTX を作らない**
  - `ci-finalize.sh` は PDF・PPTX 変換まで走るため、制作中の「直す→検査」の往復には重かった
  - `--strict` で SVGラベル検査も落とす（既定は警告）／`-v` で生出力
  - 実測：25枚のデッキで検査4本が **3秒**（`ci-finalize.sh` は PDF 変換だけで十数秒）
- 運用を `V3.2_FORMAT.md` に明記：**制作中は `ci-gates.sh`／配布直前だけ `ci-finalize.sh`**。
  PDF は最終の目視確認と配布時だけ作る

### 検査の追加（2026-09-08）

- **`svg_label_check.py` 新設**：SVG 図版のラベルの重なり・枠外への切れ・地色と同色を機械検出する。
  既存の2ゲートは HTML 要素の箱しか見ないため、図の中の文字は死角だった
  - 判定は `CLIP` / `OVERLAP` / `CONTRAST` の3種。文字幅は東アジア文字幅から推定（レンダリング不要）
  - `--selftest` で検査自体の動作確認ができる（しきい値を触ったら必ず流す）
  - 白フチ（`paint-order="stroke"`）付きの文字は `CONTRAST` の対象外＝正当な可読化手法
- `ci-finalize.sh` に**警告として**組み込み（既存デッキ47本中17本に所見が出るため、当面は落とさない）
- **実証**：WELLA OPI ネイル統合版のフレームワーク図化で目視でしか見つからなかった2件
  （バブル図のブランド名の団子・レンジ図の右注記の切れ）を、退行させた版で再現して検出できることを確認

### データ統治（新ルール・2026-09-08 追加）

- `V3.2_FORMAT.md`「データ統治（重要）」に **「シェア目標の分母は『対処可能市場』にする」** を新設（全案件必須）
  - 出品済のカテゴリー＝カテゴリー全体／未出品＝参入する価格帯のみ／自社の価格がその市場に存在しない＝分母にしない
  - 分母として何を使ったかを表の列か注記で明示。分母が異なるカテゴリーの合計シェアは出さない
- `TERMS_AMAZON.md` に 4b 節（Amazon 案件版：未出品カテゴリー・ブラウズノード付け替えでは解決しない旨・親ASIN粒度の統一）
- `SLIDE_DESIGN_GUIDELINES.md`・`VERSION`（`share:` 行）に同旨を反映
- **根拠**：WELLA OPI ネイル統合デッキで、未出品のジェルネイルカテゴリー（月¥55.5M）全体を分母にしていたため、
  シェア上限までの余地を ¥14.80M と算出していた。対処可能な ¥2,000–2,999 帯（月¥8.7M）で計算すると **¥1.17M**＝**12倍の過大**。
  目標額は変わらないが、シェア表示が 1.5% → **11.7%** となり計画の意味が変わった

### 追補（2026-09-08・同版内）: 検査の機械可読化・LLM出力の検品・多言語の型

WELLA ProHair 統合デッキを**3版（本編／やさしい版／英語版・各23枚）**まで仕上げる過程で見つかった
正典の穴を回収する。いずれも実際に事故が起きたもの。**後方互換の追加のみ・日本語版の出力は不変。**

- **検査結果を機械可読に**（`slide_overflow_check.py` / `check_text_overlap.py` に `--json` / `--lines`）
  - **事故**：既定の1行書式を下流ツールが `OVERFLOW (\d+):` で拾っていたため**先頭1件しか取れず、
    残り19頁のはみ出しが素通り**した。PDF を目視するまで「はみ出しゼロ」と誤って扱っていた
  - `--json` は JSON Lines（1ファイル1行）。`{"slides":[{"n":2,"over_px":106,"kind":"v"}…]}`
  - **既定の1行書式は1バイトも変えていない**（既存の呼び出し・終了コードは不変）
- **LLM が書いた文章の検品ゲート `llm_output_check.py` を新設**
  - **事故**：やさしい版（リライト）・英語版（翻訳）で「¥9.5M27¥0.73億」（FY 脱落）「WELLA様→ウエラ」
    「¥3.7M個」「430位円」「個個」「鉤括弧が " に化ける」。**数字は合っているので数値チェックは全部通る**
  - 突合モード（原文あり）＝①英数トークンの保存 ②タグ構成 ③単位の崩れ・引用符の混入。
    NG段落だけ**原文へ戻し**、戻した件数と理由を出す。起案モード（原文なし）＝禁止語・
    データ由来でない数値・タグの破損。`--selftest` に10件の回帰テストを同梱
- **gist の本文差し替え規則を明記**（`V3.2_FORMAT.md`）＋ `.gist-t`（任意）を追加
  - **事故**：差し戻しでタグを正規表現 `^(<[^>]+>)(.*)(<[^>]+>)$` で組み直し、`span.gist-k`
    （要点ラベル）が十数ページで消えた。v3.8 で `.gist` を正典化すると全案件に同じ構造が増える
  - 規定＝**開始・終了タグは検出時の文字列をそのまま使い、正規表現で作り直さない**
- **多言語版の級数スケール `ci-lang-v3.8.css` を新設**（`ci_head.py --lang en`）
  - **事故**：英語は和文より2〜3割長く、v3.7 の級数のままだと**23枚中20枚がはみ出し**、案件側が
    `en-fit` を自前定義していた（最終0.80倍）＝ドリフト
  - `--lang-scale` 変数で級数を一括スケール（既定0.85）／表セルの折り返しは**空白位置のみ**
    （`overflow-wrap:anywhere` は「2.0」「1,715」を数字の途中で折る）／見出しの行間を詰める
  - **`format:` ではなく `lang:` 行で宣言**＝`--lang` を付けたときだけ連結。日本語版の
    `ci_head.py` 出力はバイト単位で従来と同一（実測で確認）
- **`TITLE?` 警告が英語版で必ず鳴る問題を修正**（`slide_overflow_check.py`）
  - 英語のタイトルは日本語トークンを持たないため必ず不一致になっていた。版サフィックス
    （`_EN` / `_やさしい版`）を落とし、ラテン文字トークンでも照合する。**発火条件は従来のまま**
    （ファイル名に日本語の主題語があるときだけ）＝警告を増やさない
- `ci_frameworks.py` の型見本の文言「未参入」→「未出品」（`TERMS_AMAZON.md` の禁止語。
  新設した検品ゲートがキット自身の型見本で検出した）

**検証**（このリポジトリで実測）

| 対象 | 結果 |
|---|---|
| `ci_head.py`（日本語）の出力 | 変更前と**バイト単位で同一**（3,564,528 bytes） |
| 1行書式の後方互換 | `OVERFLOW 2:+462px,3:+613px(横),3:clip(TABLE)` が旧実装と一致・終了コードも一致 |
| `llm_output_check.py --selftest` | 11件すべて期待どおり（差し戻しで `gist-k` が保たれることの回帰テストを含む） |
| 多言語スケールの効果 | 同一英語スライドで **+72px はみ出し → 解消**（0.85倍）。より重い版は +214px → +109px（0.85）／+73px（0.80） |
| `TITLE?` の回帰 | `_EN` 版で旧実装は警告 → 新実装は OK。日本語版・ラテンのみのファイル名の挙動は不変 |

### 追補（2026-09-09・同版内）: Amazon Ads 公式出典つき広告用語集 `TERMS_AMAZON_ADS.md`

A-4 の `TERMS_AMAZON.md` は「正式用語」を定めていたが、**根拠URLが無く後から検証できない**状態だった。
Amazon Ads 公式サイトの日本語ガイドを一次情報として採取し、**行ごとに出典URLと取得日を持つ**用語集を新設する。

- **採取方法**（再現手順を本文に記載）: `advertising.amazon.com` の sitemap から日本語ガイドのURLを列挙
  （2026-09-09 時点で **272ページ**）→ 該当ページの H1 とリード文から定義を抽出。
  定義は**公式の記述を引用**し、5co 側で要約・言い換えをしていない
- **収録**: 広告プロダクト（スポンサープロダクト広告／スポンサーブランド広告／ディスプレイ広告）・
  指標（ACOS／CPC／CPM／ビューアビリティ）・ターゲティング（キーワード／商品／マッチタイプ3種／
  除外キーワード／動的な入札 - アップとダウン／リマーケティング／フリークエンシーキャップ）・
  アドテック（DSP／SSP／RTB／広告インベントリ／AMC）・市場規模（TAM／SAM／SOM）・
  ファネル（マーケティングファネル／ブランドの認知／検討促進の広告／顧客維持／OKR）・ASIN／FBA
- **表記差分を明示**（社内表記の変更はオーナー判断）
  - `ACoS` → 公式は **ACOS**（広告費売上高比率）
  - 「スポンサープロダクト（SP）」→ 公式は **スポンサープロダクト広告**（「広告」まで含めて正式名称）
  - V3.2_FORMAT.md「シェア目標の分母」の「対処可能市場」→ 公式の **SAM / SOM** に対応する
- **出典が取れなかったものは正直に分ける**
  - ROAS・CVR・KPI は `ja-jp` URL でも英語ページが返る（日本語版なし）。日本語表記は 5co の暫定と明記
  - **NTB・TACoS は日本語ガイドに該当ページが無く、`TERMS_AMAZON.md` の定義は出典未確認**と明記
- `TERMS_AMAZON.md` から相互参照を張り、`VERSION` の `terms:` 行にも「広告側は TERMS_AMAZON_ADS.md が正」を追記

**検証**: `llm_output_check.py --terms TERMS_AMAZON.md` の禁止語抽出が編集後も同一
（`棚 帯 天井 主戦場 稼働 定常月 未参入` の7語）。`--selftest` 11件 OK。

**補足**: `advertising.amazon.com/academy` は受講コンテンツで用語集ではなく、
`getting-started/glossary` は現在リダイレクトされ用語集ページとして存在しない（2026-09-09 確認）。

### 追補（2026-09-09・同版内）: 統合分析デッキの推奨ページ順を制定

**事実**: 2026-09-07 の WELLA ProHair ULTIME 統合版（提案を冒頭へ）と WELLA OPI ネイル統合版
（年間計画を冒頭へ）で、別々の制作が**独立に同じ並びの判断**になった。さらに OPI 版（31枚）は
「目標／課題／目標阻害要因／解決策」の4グループ＋章扉に再構成された。**同じ判断が2件続いたが、
正典に並び順の規定が無く、次の制作の拠り所が無かった。**

**規定**（`SLIDE_DESIGN_GUIDELINES.md` 5.8・`VERSION` の `structure:` 行）

- 表紙 → **目標** → **課題** → **目標阻害要因** → **解決策** → 前提と限界／出典 の順
- 各グループの先頭に章扉（`pd-divider`）を置く
- **「年間計画（または提案）」＝目標**と明記（別物として二重に置かない。依頼 md の B-3 と
  4グループ構成は同じことを指していた）
- 目標は冒頭（p2）。分析（目標阻害要因）は目標と課題を説明するためにあり、分析から始めない

これにより依頼 md の **B-3（未提出だった軽微項目）を解決**する。

### 追補（2026-09-09・同版内）: ページ参照の直書き検出と見出し折り返し警告（B-1・B-2）

いずれも**非ゲート（表示のみ・終了コードは不変）**。5.8 の推奨ページ順を運用するとページを
並べ替える機会が増えるため、その事故を先に潰す。

- **B-1 `PAGEREF?`**: 「14ページ」「P14」「次ページ」等の直書きを警告する。
  **事故**: `VERSION` は `{{PG:タイトル}}` での解決を規定していたのに OPI 版・ULTIME 版とも直書きしており、
  ページを並べ替えたときに参照が全部ずれた（気付けたのは目視のみ）。規定はあったが**守られたかを
  機械で確認する手段が無かった**。
  **誤検出を防ぐ設計**: `ci_pagerefs.resolve_pagerefs()` が解決した番号を `<span class="pgref">N</span>` で
  包むようにし、検査はそれを除いてから探す。**正しい参照には鳴らない**（鳴り続ける警告は無視される
  ようになるため。`marker=False` で従来どおりの素の番号も出せる）。
- **B-2 `TITLE_LINES?`**: `h2.title` が3行以上に折り返しているスライドを警告する。
  **事故**: 用語を正式名に直すと見出しが伸び、2行想定が3行になってページが溢れた。あふれ検査は
  「溢れた」ことしか分からず、**原因が見出しであることが分からない**まま本文を削る往復が発生した。
  `V3.2_FORMAT.md` に**見出しは全角45字程度まで（2行以内）**の目安を明記（実測で全角46字前後が境目）。

**検証**（実測）: 直書き「14ページ」を入れたスライドは `PAGEREF? … slide:2`、全角60字の見出しは
`TITLE_LINES? 見出しが3行に折り返し slide:4` を検出。**同じデッキ内で `ci_pagerefs` により解決した
参照（span.pgref）には鳴らない**。無改変の型見本は `OK`（誤検出なし）、終了コードは 0 のまま。
`ci_pagerefs.py` の自己テストにマーカーと後方互換の assert を追加。

### 追補（2026-09-09・同版内）: 琥珀を付けるセルの選び方（B-4）

**事故**: 2026-09-08 WELLA OPI ネイル統合版で、「シェア上限までの余地が大きい」という理由で
**計画に置けないカテゴリー**（廃盤・自社価格が市場価格帯と不適合）にも琥珀を付けていた。
読み手には「ここを取りにいく」と読めるため修正した。

**規定**（`V3.2_FORMAT.md`）: **大きい値ではなく、そのページの洞察文が実際に言及するセルに付ける。**
迷ったら `.gist`（要点）と洞察文を読み返し、文中に出てこないセルの琥珀は外す。
これにより依頼 md の **B-4 を解決**する（`TERMS_AMAZON.md` の禁止語検索と同じく、書き終えてから
見直す運用チェックとして機能する）。

### 追補（2026-09-09・同版内）: 数値表記の規約（B-9）・kit の場所解決 `ci_paths.py`（B-12）・Codex astra レビュー4件

- **B-9 `COPY_GUIDE.md` ルール7・8**（5→6→8箇条）: ①金額の単位は1デッキ1系統（`¥M` か `億`）
  ②比率は必ず「A ÷ B ＝ C%」の式で書き、期間が違う値を割るときは按分を明示。検収チェックに
  「`÷` と `＝` を含む文を全文抽出して実際に割る」「`¥` の後ろの単位が混在していないか」を追加（人力）。
  **事故**: 「広告¥950万 ÷ FY27 ¥0.75億 ＝ 9.5%」（実際に割ると 12.7%）が本番HTMLに残った。
  単位が3系統混在していたため桁の取り違えに気づけず、**数値ゲートは全部通っていた**。
- **B-12 `ci_paths.py` 新設**: 案件スクリプトからの kit 参照を `parents[N]` の階層決め打ちにしない。
  上位ディレクトリを遡って `5co-CI-kit/VERSION` を探し、見つからなければ `SystemExit`（fail-closed）。
  **事故**: `HERE.parents[5]` が1つずれていて、はみ出し検査が「実行されずに成功扱い」になっていた（例外も出ない）。
  `EMPLOYEE_RUNBOOK.md` に雛形（スクリプト自身の場所を起点に遡る）を追加。`--selftest` 付き。
- **Codex astra レビュー（origin/main 比・P2 4件・全件採用）**:
  1. `ci_head.py --lang en --lang-scale 0.8` が `<html lang="en">` で 0.85 に固定されていた（CSS 側の保険
     `:root[lang="en"]` の方が詳細度が高い）→ 焼き込みを `:root, :root[lang], .lang-en` に
  2. `check_text_overlap.py --json/--lines` が近接警告41件超の「...打ち切り」を OVERLAP 側の raw に混ぜ、
     警告だけのデッキで exit 1 になっていた → `near_miss_raw` に分離（ok は overlaps/raw/probe失敗のみで決まる）
  3. `llm_output_check.py` が閉じ忘れタグと同位置のブロック種別の変化（h2→p）を見ていなかった
     → 「構造の破損」として不合格・`--restore` でも合格にしない（人が直す）
  4. `scan()` の入れ子判定が逆で最外側（td）を残していた → 最内側（td の中の p）を残す。壊れた1段落だけを
     戻し、無事な段落の翻訳を捨てない。**2回目のレビュー**で「外側の地の文（`<li>FY27<ul>…</ul></li>` の
     FY27）が突合から外れる」と再指摘 → 区間（segments）方式に変更。外側は子ブロックを除いた地の文の
     区間だけを持ち、差し戻しは全区間を平坦化して後ろから当てる（型見本の5段落を壊して戻し、原文と
     バイト単位で一致を確認）

**検証**: `llm_output_check.py --selftest` 13/13（2件追加）／`ci_paths.py --selftest` 2/2・kit 外の cwd で exit 1／
`ci-gates.sh ci_frameworks_demo.html` ✅／型見本を自分自身と突合 1325 段落 OK／日本語版 `ci_head.py` 出力
3,564,528 バイト不変／`tests/*.sh` PASS 19+46。

## 2026-07-14 ブランドステートメント制定（BRAND_GUIDELINE v2追補・版号据え置き）
- 「水晶玉で市場を透視し、戦略を磨く。」をCIの最上位に制定（オーナー裁定）。BRAND_GUIDELINE.md 冒頭に §0 として追加
- 全CI判断の従属関係を明文化（配色・タイポ・ロゴ・図解・コピー < ステートメント）

## バージョン管理ルール（2層・decisions.md 2026-06-29 準拠）

- **全体（ブランド）版** … `5co-CI`（Drive）が正。`tokens/`（色・タイポ・ロゴ・3色規律）に及ぶ＝
  **全媒体に影響する変更**で上げる。色相/トークン値の変更＝破壊的（全媒体を再検証）。
- **スライド媒体版（このファイル）** … スライド内だけの変更（型追加・レイアウト・検査）で上げる。
- **対応ブランド版を明記**：各スライド版は「準拠ブランド版」を併記する。
- **カスケード**：ブランド版が上がったら、本キットを新ブランド版で再検証し、必要なら版を上げる。

形式：`slide vMAJOR.MINOR（準拠 brand vX.Y）`。MAJOR＝既存デッキの作り直しを伴う非互換変更／MINOR＝後方互換の追加・修正。

---

## slide v3.7（準拠 brand v2） — 2026-08-03

> 後方互換の追加（MINOR）。CSS・トークン値・レイアウト寸法はすべて v3.6 から不変。
> WELLA様向け事業説明資料（2026-07-14 打ち合わせ版）からの汎用化。
> 版号は据え置き（v3.6 追補）裁定も可＝PR レビューで確定。

- **事業説明デッキ・テンプレを新設（`5co_biz_briefing_template.html`・6枚）**：
  表紙（cover-full＋cover-ci）／Agenda（ご質問4問形式・水晶玉イラスト）／会社紹介／
  「広告運用×データ×目標管理」サイクル／**OODA月次ループのプロセス図**
  （Observe→Orient→Decide→Act。DECIDE の「コンサルタントが自動生成資料に修正を加え
  完成させます」＝社員への確認提出工程）／本日のご確認事項。
  `{{CLIENT}}`・`{{MEETING_DATE}}`・CLIENT LOGO プレースホルダを差し替えて使用。
  実績・数値スライドは各案件で deck_data 由来の実値のみ追加（推測・手打ち禁止）
- 元資料ローカルの `.title-blue{color:#1B3F73}`（3色ルール外・2026-07-14 案件内追加）は
  テンプレでは既定の --ink に戻した（紺タイトルの正典化は別途オーナー裁定）
- ゲート実績: slide_overflow_check.py OK／check_text_overlap.py OK（Linux Chromium 実測）
  ＋PDF レンダリング目視（暗黙確認）

## slide v3.6 追補（準拠 brand v2） — 2026-07-13
> v3.6 の同版内追補（**版号据え置き**＝フレームワーク1種追加のためオーナー裁定・2026-07-13）。
> CSS（`ci-format-v3.2.css`/`ci-cover-light-v3.3.css`/`ci-charts.css`）・トークン値・レイアウト寸法は
> すべて不変。顧客OKR会ナレッジDB（data-analysis）の AI運用OODAループ資料で試作・検証した
> 実装知見の逆輸入。

- **ノード・エッジ型グラフ図を正典化（`SLIDE-PATTERN-node-edge-graph`・128種→129種）**：ノードを
  グリッド座標系（列×行・8列×5行基準）上に置き、エッジ（矢印）を別要素として明示的に描くグラフ図
  （フロー図・ネットワーク図）。エッジごとに線種で意味（実線＝自動／破線＝人手）を持たせられ、
  直線型・ブロック列群では表現できない「戻り・合流・参照」の関係構造を1枚で示せる。
  カテゴリ＝フロー・ステップ。3色QA 129/129 合格（`adapt_all_patterns.sh` 実測）。
- **グリッド座標系を規律化（`V3.2_FORMAT.md`「ノード・エッジ型グラフ図」節）**：ノードは絶対座標の
  手置きでなく「グリッド位置＋colspan」で定義（`col_x(i)=MARGIN+i*COL_W` 等）、エッジの始点・終点は
  必ずノードの縁の式（top/bottom/left/right-center）から機械的に算出（手の微調整禁止）。
  拡張時は行・列の追加のみ＝既存ノードの座標引き直し不要（5→12ノード拡張で無変更を実証済み）。
- **専用ゲートを新設（`graph_node_edge_check.py`）**：既存2ゲート（あふれ・要素重なり）はDOM/flexbox
  ベースでSVG内の `<rect>`/`<path>` 座標同士は死角のため、headless Chrome 実測で
  ①ノード同士のAABB交差（NODE_OVERLAP・1px未満の接触は許容）②エッジ端点がノードの縁±2.5pxに
  乗らない浮き（EDGE_DETACHED・`getPointAtLength` で厳密取得）③タグ付け漏れ（NO_NODES）を検出して
  `exit 1`。`ci-finalize.sh` にゲート配線（文字重なり検査の直後・`.ne-graph` を含まないデッキは
  無影響）。検査対象はオプトイン＝`.ne-graph`（svg/div）＋`.ne-node`＋`.ne-edge`（凡例の見本線は
  `.ne-skip` で除外）。試作段階で実バグ1件（隣接ノードとの 36×34px の重なり）を検出した実績あり。
- **ハイブリッド構成（node=HTML／edge=SVG）を正式サポート**：実運用のCIスライド本番化で最安定
  だった「ノード＝HTML div（既存CSSクラス流用・和文折返しはHTML任せ）＋エッジ＝absolute重ねSVG」
  構成を、純SVG構成と並ぶ正式な2構成として `V3.2_FORMAT.md`・パターン定義書に明記。ゲートは
  screen 座標系で突き合わせるため両構成を同一ロジックで検査（HTML div ノードで実測検証済み）。
- **`check_text_overlap.py` に NEAR-MISS 警告ティアを追加（非ブロッキング）**：4px 許容の設計により
  「0.8px の食い込み」（AI運用OODAループ資料の実インシデント）が OK 判定になる死角に対し、
  ①FAIL閾値以下の真の交差 ②absolute/fixed 要素が絡むペアの 8px 未満近接（`NEAR_MISS_PX` で
  変更可・0で無効）を**表示のみ**の警告として報告。FAIL（>4px 交差＝exit 1）の挙動は不変。
  通常の表組・flex の隣接（設計上の近接）はノイズになるため通常フロー同士の近接は対象外
  （既存7パターン＋正典テンプレで警告0件を実測確認）。
- **「暗黙確認」を全CI型共通ルールとして制定（`V3.2_FORMAT.md` 規定 2.5）**：自動ゲート OK でも
  **レンダリング結果（スクリーンショット/PDF）を目視確認するまで「完了」と報告しない**。
  自動ゲート＝機械的下限保証／目視＝「窮屈に見えるか」の知覚判断、の二段構え。
  `slide_visual_regression.py`（computed style 比較）では新規要素同士の視覚的密着を検知できない
  ための運用ルール。`CI_KICKOFF.md`・`EMPLOYEE_RUNBOOK.md`・`SLIDE_DESIGN_GUIDELINES.md` に反映。

---

## slide v3.4（準拠 brand v2） — 2026-07-09
NatureLab 週次定例デッキ（2026-07-08〜09）で確立・検証した運用改善6件を正典へ取り込み。
すべて後方互換の追加（既存セレクタ値・レイアウト寸法の変更なし＝既存デッキは不変）。

- **A-1: 文字重なり検査ゲートを新設（`check_text_overlap.py`）**：`slide_overflow_check.py` が拾えない
  スライド**内**の要素同士の衝突（`position:absolute` の凡例 × 洞察カード等）を headless Chrome で実測し、
  祖先子孫でないペアが 4px×4px を超えて重なれば `exit 1`。`ci-finalize.sh` にゲート配線（あふれ検査の直後）。
- **A-2: 文節単位の改行（`ci-format-v3.2.css`）**：文章系要素（`p,li,.lead,.sub,.note,.note-line,.t-note,.fine`）に
  `word-break:auto-phrase`（Chrome内蔵 BudouX）＋`line-break:strict`。非対応環境は従来動作にフォールバック。
- **A-3: 表の分離の忠実再現（`.skg`／`V3.2_FORMAT.md §1.5b`）**：原本PPTで隙間分離された指標群・ブロックを、
  透明スペーサー列(`.gp`)・行(`tr.brsp`)で同位置に再現（1格子へ統合しない）。ヘッダ・列幅整合を保ちはみ出しゲート1表通過。
- **B-1: ページ参照トークン（`ci_pagerefs.py`）**：`{{PG:タイトル部分文字列}}` をビルド時に実ページ番号へ解決。
  参照先が無ければ `SystemExit`（参照切れゲート）。並べ替え・増減に自動追従＝参照ズレを構造的に防ぐ。
- **B-2: 1ページ1メッセージ＋強弱（`COPY_GUIDE.md` 原則1追補・`.fine`/`.sho-lead`）**：タイトル末尾に「｜主張」（人手起案）、
  枝葉（注記・出典・凡例・単位）は `.fine`＝8.5px・淡い墨で弱く、洞察リードは `.sho-lead`＝17px で強く。
- **B-3: OKR基準の優先度背景（`.slide.refpg`）**：参考ページ（事前・事後読み）は `--crystal-25` 地＋`.period` に
  「参考」ラベル。会議中にめくるOKR直結ページは白。どのページを参考にするかの**分類は案件側**（`.refpg` 付与）。
- **C: 枝葉テキストの淡色化（3色規律遵守）**：`.fine`/`.refpg` の弱いテキストは、独立した色相トークンを
  足さず墨の不透明度トークン `--ink-60` で表現する（新色相 `--ink-blue #5B7C99` は導入しない＝白/crystal blue/ink の3色を厳守）。

---

## slide v3.6（準拠 brand v2） — 2026-07-11
> v3.5 に後続する非破壊追加。CSS（`ci-format-v3.2.css`/`ci-cover-light-v3.3.css`/`ci-charts.css`）・
> トークン値・レイアウト寸法はすべて不変。SLIDE-PATTERN ライブラリの拡張のみ。

- **SLIDE-PATTERN を 99種 → 128種へ拡張（コンサルフレームワーク29種追加）**：トップコンサル
  （McKinsey・BCG・Bain・Porter系）の正典約120型を3並列Webリサーチで照合したギャップ分析
  （`docs/SLIDE-PATTERN/FRAMEWORK-GAP-RESEARCH.md`）に基づき、欠落していた「分析を語る図」を補充。
  - **定量チャート10種**：waterfall-bridge-chart・stacked-bar-100pct・mekko-market-map・
    tornado-sensitivity-chart・butterfly-comparison-chart・scatter-bubble-positioning・
    radar-chart-comparison・slope-chart-before-after・heatmap-matrix-table・funnel-conversion-stages
  - **ロジック・ツリー5種**：issue-logic-tree・kpi-driver-tree・minto-pyramid-structure・
    decision-tree-options・fishbone-cause-analysis
  - **マトリクス・構造10種**：positioning-matrix-2x2（汎用2軸＝SWOT/Ansoff/優先度を1型でカバー）・
    nine-box-matrix-3x3・harvey-ball-comparison-table・layered-pyramid-hierarchy・
    concentric-circles-market（TAM/SAM/SOM）・venn-three-circle-overlap・value-chain-porter・
    strategy-house-framework・three-horizons-growth・business-model-canvas-grid
  - **プロセス・体験4種**：customer-journey-map・swimlane-process-flow・phase-workstream-roadmap・
    iceberg-visible-hidden
  - **品質ゲート**：全128種で `ci_pattern_adapter.py` CI v2 変換＋3色QA合格（pass=128/fail=0）、
    新規29種は DOM 実測の枠内収まり検査（Playwright・NG=0）も通過。グレースケール hex のみで作図
    （rgb()/色名/emoji 不使用）＝アダプタの3色畳み込みと完全整合。
  - **INDEX にカテゴリ「🧠 フレームワーク・分析」を新設**し、`framework_recommend.py` の発見枠
    加点対象に追加（未経験の型に触れさせる導線を強化）。

## slide v3.5（準拠 brand v2） — 2026-07-09
> v3.4（CI改善6件・PR #742）に後続する非破壊追加。CSSトークン値・レイアウト寸法は不変。

- **表紙CIコンセプト必須化（全CIスライド規則）**：すべての表紙（`cover-full`・章扉 `pd-divider` 除く）
  に、CIコンセプト説明ブロック `.cover-ci`（「水晶玉で市場を透視し、戦略を磨く。」＋ロゴ由来）を
  **必ず**載せるルールを制定。属人的な手書き（NatureLab 週次のみ手入れされていた）を排し、正典化。
  - **単一情報源＝`ci_head.cover_ci_block()`**（`COVER_CI_TAGLINE`/`COVER_CI_BODY`・由来 `LOGO_HANDOFF.md` §4）。
    共有ビルダー `ci_v2_lib.cover()` は既定で自動付与（`ci_concept_html` 省略時）。bespoke ビルダーも
    `import ci_head; ci_head.cover_ci_block()` で同一正典を消費（文言はブランド概念のみ＝Tier0安全）。
  - **CSS は既存の正典 `.cover-ci`/`.cover-ci-h`**（`ci-format-v3.2.css`・変更なし）。
  - **検査**：`slide_overflow_check.py` が `.cover-ci` の無い表紙を `COVER_CI?` として表示（非ゲート）。
  - 反映：`V3.2_FORMAT.md`（不変条件＋「表紙CIコンセプト」節）・`CI_KICKOFF.md`・`SLIDE_DESIGN_GUIDELINES.md`
    （Do/Don't＋チェックリスト）。
- **CI用語の呼称統一（水晶玉シリーズで一貫化）**：色＝**crystal blue**（`--crystal`・旧「アイスブルー/シアン/水色/ice」）、
  濃紺＝**ink**（`--ink`）、数字背景＝**Oracle**（`.numfield-full`・旧「数字フィールド/数字モチーフ」）、
  マーク＝**crystal ball（水晶玉）**、文言の正（`COPY_GUIDE.md`）＝**crystal text** に統一。
  - `CI_KICKOFF.md` に「CI用語」表を新設（正式名・CSSトークン・使わない旧称）。
  - `SLIDE_DESIGN_GUIDELINES.md` は v2 時代の**廃止トークン `--ice` 系を `--crystal` 系へ全面更新**
    （`check-slide-ci-parity.py` の DEPRECATED と整合）。誤称「シアン」（H198°・廃止色相）も除去。
  - `LOGO_HANDOFF.md`/`README.md`/`NUMFIELD_HANDOFF.md` のプロースも crystal blue / ink / Oracle に統一。
  - **CSSトークン値・レイアウト寸法の変更なし**（プロース/ドキュメントの呼称のみ＝非破壊）。

---

## slide v3.3（準拠 brand v2） — 2026-07-07
- **共通HEAD＝正典CSS連結の標準方式を制定（`ci_head.py`・data-analysis 依頼 2026-07-07）**：
  案件ビルダーが正典CSSをコピー・inline再実装する運用（正典改定が届かないフォーク化＝WELLA 事故の温床）を
  禁止し、`VERSION` の format: 宣言を読んで現行CSSを連結する共有ヘルパを唯一の連結方式として提供。
  出力冒頭に版スタンプを焼き込み（ci_head 経由の機械判定マーカー）。VERSION に `head:` 規定と
  ci-charts.css を format: 宣言へ追加。規定＝`V3.2_FORMAT.md` 1.6／`SLIDE_DESIGN_GUIDELINES.md` §5.7。
  - **同時に、ci_head の E2E ゲート検証が露呈した正典CSS内のパレット外色を是正**：
    `.pdstr .c-lo` の青灰 2色（→crystal-55/ink-60）・`.pdstr .tac` の淡青灰（→crystal-25）。
    琥珀の淡地 #fdeacb は `--insight-bg` として追認（#699 の #f6b44a と同型の実装追認・機能色）。
    これで「ci_head で組んだデッキが parity 検査 OK」が成立（連結＋ゲートの二重防御が閉じる）。
- **ライトバリアント（白地 × 水色 Oracle・全型対応）を正式化**：`ci-cover-light-v3.3.css`＋
  `assets/numfield_allover_crystal55.svg`／`_crystal25.svg`。クラシエ薬品デッキ（2026-07-07）の表現を全社CIへ。
  - 使い方: **表紙**は `class="slide cover-full light"`、**本文（任意の型）**は `class="slide <型> light"` を
    付けるだけ（既存スライドは不変＝後方互換）。表紙=crystal-55（濃）・本文=crystal-25（淡）の2段階。
  - 3色規律内（Oracle tint＝crystal-55 #DEE9F6／crystal-25 #F0F5FB・地=白・文字=ink）。ブランド版変更なし。
  - 元実装（`img.nf-bg`＋opacity .5/.35）の外部 `assets/` 参照を dataURI 埋込＋焼き込みtintへ是正
    （自己完結・opacity非依存＝PDF/PPTX出力でも決定論）。旧マークアップの `img.nf-bg` は自動非表示（互換）。
  - 実機検証: 表紙・本文の描画目視（白地・水色Oracle・ink/カード可読）＋はみ出しゲート OK。
- **はみ出し検査の横方向対応（現場報告 2026-07-07・クラシエ制作中に発見された死角）**：
  `slide_overflow_check.py` に 1:`scrollWidth` 検査（`+Npx(横)`） 2:`overflow:hidden` で
  「あふれず隠れて切れる」table/svg/img の右端クリップ検査（`clip(TAG)`） 3:幾何NG時の
  **exit 1**（gate として機能・TITLE? ヒューリスティックは表示のみ）を追加。
  `ci-finalize.sh` の検査を「警告のみ」→**NG で停止**（V3.2 規定「OK まで配布不可」を強制）。
  - 新検査が正本テンプレ自身の潜在不良（週次テンプレ7枚目 DSP 表・右端列+56px 見切れ）を
    検出 → dsp3 表を 8.5px/padding 1px に修正し解消（描画目視で右端列復元を確認）。

- **正典文書の世代整合（WELLA 世代遅れ調査 2026-07-07・docs/CI調査回答_WELLAスライド劣化_2026-07-07.md）**：
  WELLA 月次が CI_KICKOFF の旧導線（v2 週次雛形の複製）どおりに組まれ V3.1 タイポ・琥珀を取りこぼした事故を受け、
  1:CI_KICKOFF.md／SLIDE.md の入口を「VERSION 確認→現行フォーマット」へ改定 2:SLIDE_DESIGN_GUIDELINES.md に
  V3.1 タイポ（§3）を明文化・旧「明朝統一」記述と隅ロゴ 64px 表記を是正（列グループ縦罫禁止の§3.5は別途本日中に明文化済み・
  本件では table.sk の格子罫未追従を注記） 3:SLIDE.md の EB Garamond 残骸を Hoefler へ統一
  4:`check-slide-ci-parity.py` に Garamond 系残存の検査を追加。週次雛形 HTML 冒頭に
  「月次・新規に使わない」警告を焼き込み。フォーマット CSS 自体は不変（文書・検査のみ）。
- **正典準拠の是正2件（NatureLab準拠規定 2026-07-07 起点）**：
  1:standalone テンプレの旧トークン名 `--powder`/`--navy` を正準 `--crystal`/`--ink` 系へ改名
  （hex不変・クラス名は後方互換で不変・parity checker 適合化） 2:**洞察強調色＝琥珀 #f6b44a を正式化**
  （`--insight` 系トークンを ci-charts.css に追加。v3.2 実装 `td.chl`/`.pdstr .c-hi` の追認・
  意味にのみ使用可＝装飾禁止）。

## slide v3.2（準拠 brand v2） — 2026-07-06
- **月次 V3 デッキ形式を正本フォーマット化**：`ci-format-v3.2.css`（全24 styleブロック連結・
  表紙/扉 Oracle 埋込）＋ `V3.2_FORMAT.md`（スライド8型仕様）＋ `VERSION`（現行版宣言）を新設。
- **格納場所の一元化を明文化**：フォーマット/エンジンの唯一の格納場所＝本キット
  （`5co-hub/template:5co-CI-kit`）。全セッションは `VERSION` を確認し常に最新版で生成（CLAUDE.md に規定）。
- **欧文セリフを Hoefler Text（macOS標準）へ**（Garamond Premier Pro / Adobe Fonts 依存を解消・#642）。
  社員 Mac はフォント導入・CC アクティベート不要で忠実描画。名刺のみ Garamond 据え置き（別成果物）。
- 出力系を整備：`ci-finalize.sh`（PDF埋込＋画像PPTX＋Slides）／`slide_overflow_check.py` の全OS動作化
  （Chrome自動探索＋--no-sandbox）／`EMPLOYEE_RUNBOOK.md`（社員3ステップ・GitHub不要）。
- ※ MAJOR=3 は V3 系デッキ形式（月次28枚・anxs/blk/sof/pdstr/fnl 型）への移行を示す。v2 テンプレは残置（週次ベース雛形）。

## slide v2.2（準拠 brand v2） — 2026-06-30
- **隅ロゴ（本文右上）を 102px で確定**（V3 実デッキ準拠・実測 102×73px）。#603 の 64px は**撤回**。
  - `5co_slide_template.html` の `.corner`/`svg.corner` を 64px→102px。
  - `slide_overflow_check.py` のロゴ幅ガードを 72px→**112px** 基準へ（正準102px・102pxの誤検知防止）。
  - 視覚回帰基準 `baseline/template_signature.json` の corner を 64→102（本文12枚／表紙は null）。
  - `5co_slide_template_standalone.html` の `.corner-logo` も 102px に統一。
- ※表紙Oracle(numfield)のOL化は #617（slide media は同日反映済み）。

## slide v2.1（準拠 brand v2） — 2026-06-28
- 99種 SLIDE-PATTERN を CI v2 化するアダプタ（`ci_pattern_adapter.py`）＋一括QA（`adapt_all_patterns.sh`）。3色QA全合格。
- フレームワーク・レコメンダ（`framework_recommend.py`）標準搭載。
- 週次デッキエンジン `ci-weekly-deck` のデータ契約整合（単一DSP・エマージング_シリーズ受容）。
- アダプタ寸法仕様 `docs/SLIDE-PATTERN-CI-ADAPTER-SPEC.md`。

## slide v2.0（準拠 brand v2） — 2026-06-28
- CI v2 正本スライドテンプレ：`5co_slide_template.html`（`--crystal/--ink`・A4横297×210mm・隅ロゴ64px【→ v2.2 で 102px に改定】・φスケール）。
- 視覚回帰 `slide_visual_regression.py` ＋ `baseline/`、はみ出し検査 `slide_overflow_check.py`。
- 旧 `--powder/--navy`・16:9（1280×720）世代から A4・新トークン名へ移行。

---

## 版を上げる時の手順
1. 変更が `tokens/`（色・ロゴ・タイポ）に及ぶ → **まず `5co-CI`（Drive）のブランド版を上げ**、本キットを追従させてから slide 版を上げる。
2. スライド内のみ → 本ファイルに `slide vX.Y（準拠 brand vZ）` で1エントリ追記。
3. `slide_overflow_check.py` ＋ `slide_visual_regression.py` を通してからコミット。
