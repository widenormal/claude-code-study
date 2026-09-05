# 5co-CI-kit CHANGELOG（スライド媒体版）

> **これは「スライド媒体」の版ログ**です。スライドの正本は本キット（template `5co-CI-kit`）。
> 全媒体共通の**ブランド版**は Drive `5co-CI/CHANGELOG.md` ＋ `BRAND_GUIDELINE.md` が正。

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
