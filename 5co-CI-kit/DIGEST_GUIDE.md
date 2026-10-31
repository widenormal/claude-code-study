# CI ダイジェストモード（DIGEST_GUIDE）

**Status: clarified 2026-10-29 by 若松さん**（「このページの要点」＋視覚ちょうど1つ。2026-10-28 の左1／右少数の見せ方は本 clar で置き換え）
**v3.12（2026-10-29）**: 型「Amazon人物型」（`data-dg-layout="cutout"`）・固定要素の重なりゲートを追加（人物素材の基準は v2 待ち）。右余白ルールとの使い分けは確定（下記「右余白ルールとの使い分け」）。
**2026-10-30 追補**: 人物素材の標準（`FIGURES_GUIDE.md` §2-2・9項目）を正とし「v2 待ち」を解消。**人物写真の下端フェードは禁止**（旧「下 14% smoothstep」の規定を削除）。ヘッダー左上はロゴのみ（キッカー文字を置かない）。納品前の検品に `--bg-residue` を追加。

- 正本: 本ファイル（`5co-CI-kit/DIGEST_GUIDE.md`）。実装ヘルパ＝`digest_toggle.py`。
- 試作リファレンス: Amazon全体補正 要因グループ図解 CI の p07（Factor A 二重カウント）ダイジェスト試作。OPI 定例 v3.11 サンプル（p03/p04/p06/p07）。
- Amazon人物型の正本サンプル: OPI 定例 v3.11 サンプル `*_digestCutout_all.html`（2026-10-29・人物は正面向き facing_*）。部品＝`digest_person/`（CSS・JS・マークアップ例）。承認済みで本番に使えるのは marketer の3枚（`facing_marketer_01_v5_fix.png`〔下端をスライド下端か机・カウンターに接して置く〕・`facing_marketer_02_v4.png`・`facing_marketer_03_v5.png`・v3.12.5）だけ。人物素材は検品済みの正面向き v3 の5枚（`digest_person/photo/cutouts/facing_*_v3.png`・v3.12.4）だけを同梱し（**審査待ち・未承認**＝2段審査でフォトディレクター不合格のため推奨セットとして使わない・2026-10-30）、それ以外は同梱しない（素材基準＝`FIGURES_GUIDE.md` §2-2「人物素材の標準」）。
- ブランド側の基準: `brand_guidebook/`（5 co. Branding Design Guidebook β0.6・`DIGEST_DESIGN_RULES.md`）。

## 要点

- トリガー: 「このページをダイジェストにして」（ほか「ダイジェスト」「ダイジェスト版」「digest」）→ 指定ページだけ薄くする。**既定はフル CI 密度**。指定がないページは従来どおりフル。
- 変えないもの: V3.x のグリッド／カラム枠（section のクラス種別、.cols 構成。.fpanel は必須ではない＝元ページにあれば保持してよい）、ヘッダー（左上はロゴのみ・h2.title・accent-bar・コーナーロゴ 102px）、A4 余白、フッター版スタック・ページ番号、出典の note-line。
- **ダイジェストの意味（確定・2026-10-29、同日追記）**: ダイジェスト＝元ページの「このページの要点」（`.gist`）を伝える。添える視覚は **図・数字・キーワード・写真のいずれか**、または **数字＋写真** の組み合わせ。
  - 図（グラフ）を選んだときは写真を足さない（図だけで足りる）。キーワードだけのときも写真は任意だが原則どちらか。
  - 出さない: 表、長い箇条書き、複数カード、2枚目のグラフ。
  - 数字は元ページにあるものだけ（捏造しない）。
  - 残す: タイトル、`.gist`（要点テキスト）、視覚1つ（または数字＋写真）。
- 動く資料の操作の枠（`data-ci-op`）は本文の直下の子に置く＝ダイジェスト時は既存規則どおり隠れる（主張＝要点＋視覚1つは不変・2026-10-30）。
- 落とす（フルから隠す）: 密な表全体、積み重ねた注記（t-note「図の読み方」など）、「内訳を見る」ボタンと template ドリルダウン、hero 以外の図・カード群。
- section に `data-page-mode="digest"` を付ける（ランタイム切替）。元ページ id とタイトルを HTML コメントに残す。
- データの出所表記は **Shelpha**（Ignite ではない）。UI 文言は日本語。
- Ads オレンジ（#E87722）禁止・**CI 3色のみ**（--ink / --crystal / 白）。

## ランタイム切替ボタン

- **対象ページ**: 表紙・目次・中扉（`cover-full` / agenda・TOC / `pd-divider`）以外の**本文**のうち、フル表示でも情報量が多い頁にボタンを付ける（各対象頁に `data-digest-keep="hero"` が必要。JS は hero がある頁にだけボタンを注入する）。
- **付けない本文**: 既に薄い頁（主役の図＋短い説明だけで、落とす密な表・長い箇条書き・二重グラフがほぼ無い／表1枚＋短文程度）。迷ったら付けない。カバー／TOC／中扉／既に薄い頁は除外。
- **位置**: 左下フッターの**最左**（`left:36px; bottom:12px`）。ヘッダー右・コーナーロゴ隣は使わない。
- ボタンがあるページは版スタック（`.slide::before`）を `left:148px` へずらして重なりを防ぐ。`#static`／印刷時はボタン非表示・版スタックを元位置へ戻す。
- 文言: フル時「ダイジェスト」／ダイジェスト時「詳細に戻す」。
- **既定はフル密度**: 開いた直後は従来どおりフル表示。ユーザーがボタンを押すまでダイジェストにしない。
- **DOM 二重化なし**: 既存要素に `data-digest-keep="hero"`（主役の視覚1つ。数字＋写真のときは写真側に `photo`）を付ける。`.gist` は属性なしでもダイジェストで残す（要点テキスト）。押すと section に `data-page-mode="digest"` を付け外し。`point` は原則使わない（要点が gist 以外の1キーワードだけのときだけ、その1つに限る）。
- 共通 CSS/JS は `</body>` 直前の1ブロック `<!-- ci-digest-toggle v1.x (BEGIN/END) -->` に集約。
- 画面のみ: `html.ci-static`（#static・検査・PDF）・印刷・一覧ではボタン非表示、ダイジェスト CSS も効かない＝**印刷/PDF/#static は常にフル**。

## 写真（視覚が写真のときだけ）

- 写真は相対パス `figs/digest/...`（例: `figs/digest/scenes/cutouts/slide/...jpg`）。フル・#static・印刷では出さない（`.dg-photo{display:none}` 既定）。
- **図（グラフ）hero には写真を足さない**。写真を唯一の視覚にするときは `figure.dg-photo` に `data-digest-keep="hero"`。**数字＋写真**のときは数字ブロック（`.okr` / `.ci-panel`）に `data-digest-keep="hero"`、`figure.dg-photo` に `data-digest-keep="photo"` + `data-dg-photo="cutout"`（右下に添える）。

## Amazon人物型（v3.12・`data-dg-layout="cutout"`）

2026-10-29 若松さん採用（「デザインは良くなった」）。ダイジェストの型の1つ。部品は `digest_person/`。

**適用範囲**: 画面表示 × ダイジェスト時のみ（`html:not(.ci-static) section.slide[data-dg-layout="cutout"][data-page-mode="digest"]`）。フル版・`#static`・印刷は不変（`.dg-cut` は非表示）。

**レイアウト**（1122×794 の頁で実測）
- 人物は片側 1/3（右）: `figure.dg-cut`（`data-digest-keep="photo"`）＝ right:50px / width:340px / top:172px / bottom:56px。背後に **#C3D7EE（`var(--crystal)`）の角丸面** `.dg-cut-plate`（top:150px・radius 24px）。
- **頭が色面の上端からはみ出す**（人物画像の高さ 90%・下揃え＝`.dg-cut--facing`）。`clip-path:inset(-200px -60px 0 -60px)` で上と左右のはみ出しを見せ、下は色面の底で切る。
- 人物は **無加工**: `filter:none`／`opacity:1`／`mix-blend-mode:normal`／`animation:none`。色・透過・ブレンド・グラデを重ねない。人物の `img` には必ず **`.dgx-person`** を付ける（後でモーションを差し込む口）。
- **体の下端はフェードさせない（2026-10-30 若松さん決定・禁止）**。下端は色面の底で切る（上の `clip-path` の下辺）。素材側のアルファで下端をグラデーションにしない（旧規定「下 14% smoothstep」は削除）。
- 反対側（左 2/3、max-width 640px）: 要点1文（`.gist` を 22px で流用）→ **大きな数字ピル**（`.dgx.dgx-ph[data-digest-keep="hero"]` の `.dgx-nums` に 1〜2個、ink 地＋crystal 文字・76px・999px 角丸）＋直下ラベル（何の・いつの）→ **施策1行**＋`→ pNN` リンク。
- **セリフ体（`--serif-en`＝Hoefler Text）はピルの中の数字と % だけ**（lnum/tnum）。「万」「減」など和字の単位は `.dgx-u-ja`（`--sans-ja` 700・0.36em）。要点・ラベル・施策・リンクは基本フォント。
- **アンバーの要点ラベル（`.gist-k`「このページの要点」）はダイジェストでは出さない**。要点の文はラベルなしで残す。フル版・`#static`・印刷では従来どおり表示。
- 同じ人物を続く頁で繰り返さない。頁の文脈に合わせて人物と小物を選ぶ（例: 会議系＝腕組み、売上実績＝閉じたPC、広告配分＝タブレット、購入率＝スマホの買い物客）。
- 数字は元ページにある値だけ。施策の文言は施策ページの該当行をそのまま使う（資料内で案なら「施策（案）要確認」）。

**フックとリンク**（`digest_person/digest_jump.js`）
- `#digest=pNN`: URL ハッシュがこれなら、その頁をダイジェストにして先頭へ（`<script id="ci-digest-hash-hook">`・画面のみ）。
- `→ pNN`: `<a class="dgx-act-ref" href="#pNN" data-ci-jump="pNN">`。クリックで移動元の頁とダイジェスト状態を覚え、施策頁の左下に「← 戻る」（`.ci-back-btn`・left:36px／bottom:40px）を出す。戻るで元頁・元の表示状態に戻る（ブラウザの戻るでも同じ）。直接 pNN を開いたときは出さない。`#static`・印刷ではリンクは普通の文字、戻るは非表示（`<script id="ci-jump-back-js">`）。

**組み込み**: `digest_person/digest_person.css` を `<style id="dgx-cutout-v1">` 等として、`digest_jump.js` の2ブロックを `<script>` として `</body>` 直前（`ci-digest-toggle` ブロックの後）に入れる。マークアップ例＝`digest_person/markup_example_p06.html`。section に `data-dg-layout="cutout"`、ボタン対象頁の条件（`data-digest-keep="hero"`）は従来どおり。`digest_toggle.py` の `PLAN` には型 cutout をまだ持たない（v3.12 時点は部品を手で組む。下記「既知の差分」）。

### 人物素材（2026-10-30 標準・旧「v2 待ち」を解消）

- 人物素材の合否は **`FIGURES_GUIDE.md` §2-2「人物素材の標準（2026-10-29／30）」の9項目**で判定する（機器にもロゴを写さない・機器の縮尺・画面の向き/手指/影・顔の写真らしさ・無地グレー/青で生成し `alpha/` の PNG〔alpha bleed 済み〕を添える・手前に水色を重ねない・下端フェード禁止・オフィス服・衣装ディレクター審査・検品）。v1 素材（肌がイラスト調）・旧透過化スクリプト（穴を不透明で埋める `make_alpha_facing_v2.py`）は kit に入れない。人物素材そのものは kit に同梱しない（例外＝検品済みの `digest_person/photo/cutouts/facing_*_v3.png` 5枚・v3.12.4）（**審査待ち・未承認**＝2段審査でフォトディレクター不合格のため推奨セットとして使わない・2026-10-30）。
- **納品前の検品（人物素材＝必須）**: `python3 5co-CI-kit/cutout_halo_check.py <alpha.png> --resize 1152,813,725,406,362,284,142 --bg-residue` が OK、スマホを持つ素材は `phone_speck_check.py` も OK、加えて #101820・#C3D7EE に合成して目視（背景と服が同じ色だと色の検品では拾えない）。
- レイアウト側で守ること: 人物は架空・無加工（色・ベタ・半透明・ブレンドを重ねない）・**人物の手前に crystal blue（#C3D7EE 系）を半透明で重ねない**（色面・プレートは人物の後ろだけ）・下端フェードをしない・`alt` に「架空の人物・イメージ」と明記・**服だけでなく機器（スマホ・PC・タブレット・イヤホン）にもロゴ／ブランド文字を写さない**・**機器・小物の大きさは人物に対して実物どおり**・同じ人物を続く頁で繰り返さない・画像は `data:image/...` で埋め込む（外部 URL 禁止）。

### 右余白ルールとの使い分け（確定・2026-10-29 若松さん決定（CIスライド経由））

- **施策がそのページ（概要ページ）にあるとき** → ダイジェストの右余白＝**施策カード欄**（ブランドガイドブック β0.2 の右余白ルール: ①施策カード→②小さな比較→③代表商品の画像/ロゴ）。人物型は使わない。
- **施策を別ページに分割しているとき** → **Amazon人物型**（人物は片側1/3・反対側に数字ピルと施策1行＋`→ pNN` リンク／施策頁に `← 戻る`）。
- 根拠: ブランドガイドブック β0.2（`brand_guidebook/BRANDING_DESIGN_GUIDEBOOK.md`）の右余白ルールと人物ルールが、人物を右に置くと食い違っていた点の決着。出典＝2026-10-29 若松さん決定（CIスライド経由）。

### 既知の差分（v3.12 時点）

- OPI サンプルが内包する `ci-digest-toggle v1.8` ブロック（フッター `.period` × 版スタックの位置修正）は kit 未承認の別ブランチ（`fix/ci-digest-footer-overlap-2026-10-29`）の内容で、kit の `digest_toggle.py` は v1.7 のまま。v3.12 はこの差分を取り込まない（承認後に別 PR）。

## 発表（T）と台本（S）（v1.9・v3.13・2026-10-31）

話す場で映すときの見せ方。**ダイジェスト切替の拡張**で、別の発表モードは作らない（若松さん方針 2026-10-31・CIスライド経由）。

| 操作 | 動き |
|---|---|
| キー `T`／URL `#talk` | **hero（`data-digest-keep="hero"`）のある全ページを一度にダイジェストにする**（もう一度 T で元に戻る＝各ページの元の状態に戻す）。各ページの「ダイジェスト」ボタンはそのまま使える（表示も合わせる） |
| 一括切替が ON のときだけの見せ方 | ①見出しを2行に＝1行目が話題（小さく）、2行目が答え（crystal-25 の下線）②上の要点の帯（`.gist`）を外す ③右の説明カード（`data-digest-keep="point"`・v1.8 型の `.dgx-side`／`.dgx-next`／`.dgx-card`・`data-talk-hide` を付けた要素）を外す ④hero は最初の1つだけを大きく（`--talk-zoom`・既定 1.25） |
| キー `S` | 画面下の台本の帯（発表者用）に今のページの一言。帯の印＝「台本」（確定稿）／「要点」（代わりに要点を出したとき） |

- 文言：見出しは section の `data-talk-h="話題｜答え"`、台本は `data-talk-script="…"`（**コピーライターの確定稿**・CIスライドは書かない）。無ければ見出しは既存の h2.title の「話題｜答え」、台本は「このページの要点」をそのまま使う。台本は要点の短縮版なので、要点の数字を直したら台本も直す。
- `#static`・印刷・PDF・検査（ゲート）では何もしない＝フル版のまま（印刷の前に外し、後で戻す）。通常表示の見た目・DOM は T・S を押すまで変わらない。
- hero の無いページ（表だけのページ）は T でもダイジェストにならず、表のまま映る（見出し2行・要点帯を外すのは同じ）＝**既知の限界**。発表に使うデッキは本文ページすべてに hero を置く（`layout_run_check.py` の LAYOUT_RUN? が表の連続を知らせる）。
- 台本の帯とフッター行（v1.9.1・v3.13.1）：帯を出しているあいだも、コピーライト・版スタック・集計期間・頁番号・「ダイジェスト／詳細に戻す」ボタンを隠さない。①帯の高さぶん下に余白を足す（最後のページも帯の上までスクロールでき、スクロールで合わせると帯の上で止まる）②スライドの横が画面に収まり、高さが「画面の高さ − 帯」を超えるとき（全画面で映す・ノートPCの窓）は**フッター行を帯の高さだけ持ち上げ、主役（hero）の下にも同じだけ余白を取る**（`html.ci-talk-lift`・`--ci-talk-lift`）。横がはみ出す細い窓（幅 390 など）は持ち上げず、スクロールで帯の上に出す。帯を閉じれば元どおり（T だけ・通常表示は変えない）。デッキ側の別 CSS で直さない（`--talk` で上書きされる）。足元に独自の要素を置くデッキは `data-talk-footer` を付けると一緒に持ち上がる。**v1.9.2（v3.13.2）**：持ち上げ中は、スライドの**下半分にある絶対配置の要素**（表紙右下の CI 説明・締めの「上記に同意して」の欄など。全面の背景＝スライドの8割以上を覆うもの・フッター行は除く）も同じだけ持ち上げ、持ち上げたフッター行と重ならない（JS が `data-ci-tk-lift` の印を付け、帯を閉じると外す）。上半分の絶対配置・本文の流れの中の要素は動かさない。
- 付け方：新しく付けるときは `digest_toggle.py <deck.html>`（ブロックに入っている）。**既にダイジェストの付いたデッキ（v1.4〜v1.9）には `digest_toggle.py --talk <deck.html>`**＝発表と台本のブロック（`ci-digest-talk v1.9.2`）だけを切替ブロックの末尾に足す／入れ替える（PLAN・hero の印・ほかの CSS には触らない・冪等）。

## 使い方

```bash
python3 5co-CI-kit/digest_toggle.py <deck.html>
```

- 冪等（再実行で外して付け直す）。ページごとの主役はスクリプト内 `PLAN` をデッキに合わせて編集する（各頁＝fig hero／photo hero／数字 hero＋photo keep のいずれか）。
- 付与後に `ci-gates.sh` を回し、本番デッキの結果と差分がないことを確認する。

## 重なり検査（ダイジェスト見た目）

既定の `check_text_overlap.py` は `#static` で開くため、ダイジェスト CSS は効かない（印刷/PDF と同じフル）。
ダイジェスト配置の重なりを見るときは:

```bash
python3 5co-CI-kit/check_text_overlap.py deck.html --digest-mode --lines
# または（#static だけ外す・digest 強制なし）
CI_OVERLAP_NO_STATIC=1 python3 5co-CI-kit/check_text_overlap.py deck.html --lines
```

`--digest-mode` は `data-digest-keep="hero"` がある頁に `data-page-mode="digest"` を付けてから測定する。既定の `check_text_overlap.py` は従来どおり `#static`。

**v3.12**: `ci-gates.sh` は `data-digest-keep="hero"` があるデッキで `--digest-mode` も回し（落とす）、さらに `check_fixed_overlap.py`（固定要素＝コーナーロゴ・`.slide::before/::after`〔`counter()` の頁番号を含む〕・`.ci-stack`・`.period`・`.ci-digest-btn` × 文字・画像・色面ボックス、static／screen／digest × 7 ビューポート）を回す（落とす）。

```bash
python3 5co-CI-kit/check_fixed_overlap.py deck.html          # 21 実行（3 モード × 7 ビューポート）
python3 5co-CI-kit/check_fixed_overlap.py --selftest         # コーナーロゴ×色面ボックス／頁番号 counter()×本文
CI_FIXED_OVERLAP_VIEWPORTS=1280x720 python3 5co-CI-kit/check_fixed_overlap.py deck.html   # 制作中の早回し
```

## 関連

- VERSION `digest:` 行／`V3.2_FORMAT.md`／`CI_KICKOFF.md`／スキル `5co-ci-slide`
- `digest_person/`（Amazon人物型の部品）／`brand_guidebook/`（Branding Design Guidebook β0.6）／`FIGURES_GUIDE.md` §2-2（人物写真・人物素材の標準・切り抜き検品）
