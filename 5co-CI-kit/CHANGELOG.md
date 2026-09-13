# 5co-CI-kit CHANGELOG（スライド媒体版）

> **これは「スライド媒体」の版ログ**です。スライドの正本は本キット（template `5co-CI-kit`）。
> 全媒体共通の**ブランド版**は Drive `5co-CI/CHANGELOG.md` ＋ `BRAND_GUIDELINE.md` が正。

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
