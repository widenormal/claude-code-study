<!-- 5co-CI-kit v3.12 同梱（brand_guidebook/）。原本＝strategy/_ci_ops/DIGEST_DESIGN_RULES.md（2026-10-29 JST）。kit の実装規定（DIGEST_GUIDE.md）と食い違うときは DIGEST_GUIDE.md が正。 -->
# CI ダイジェストページ デザインルール（DIGEST_DESIGN_RULES）

- 作成: 2026-10-29（若松さん FB「人物に水色のベタを半透明でのせるのは気持ち悪くない？Amazon や類似レイアウトを調べてルールを蓄積」を受けて）
- 対象: CI デッキ（HTML 1280×720）の `data-page-mode="digest"` ページ。ローカル規約 `_digest_mode_NOTE.md`（左1／右少数・v1.2 カード）を**上書きしない**。本書はその上に載せる「見た目の合格基準」。
- CI 制約（全ルール共通）: 色は CI 3色（リッチブラック #101820／クリスタル #C3D7EE 系／白）の派生だけ。Ads 橙 #E87722 は使わない。数字は元ページにある値だけ（新しい数字を作らない）。データ出所の表記は **Shelpha**（旧ツール名は書かない）。ヘッダー・フッター・版スタック・note-line は不変。
- 出典 URL は各ルール末尾の [番号]。番号は末尾「参考事例」に対応。px 値のうち出典にないものは「CI 提案値」と明記。

---

## 1. 原則

1. **1ページ1主張。** 主張を1文で言えないページはダイジェストにしない（分割する）。主張文に「〜と〜」が要るなら主張が2つ。[1][2][4]
2. **3秒で読める（Glance Test）。** 見た瞬間に「何の話で、結論は何か」がわかること。[1][3]
3. **主張文 → 証拠の数字 → 補足**の順に、大きさ・濃さで序列をつける。一番大きいのは証拠の数字、次が主張文。[1][5][6]
4. **本文の数字が主張文を証明していること。** 主張文で言ったことを、数字ブロックで読者が確かめられる配置にする（主張と別ページの根拠に頼らない）。[2][4]
5. **余白は「空き」ではなく強調装置。** 空いた場所をロゴ・飾り・写真で埋めない。[7][8][3]
6. **消して強くなるなら消す。** 1要素ずつ外してみて、主張がぼやけない要素は落とす（S/N 比）。[8][4]
7. **ダイジェスト = 要素を隠すだけ、ではない。** 隠した結果「大きな写真＋見出し」だけが残るなら不合格。数字ブロックを主役に組み直す。（若松さん FB 2026-10-29）[1][3]

## 2. 数字の置き方

1. **ページ内で一番大きい要素 = 証拠の数字。** タイトル（h2）より大きくてよい。[5][6]
2. **数は 1〜2 個（最大 3）。** 1個が基本。2個目は「比較相手」か「内訳の最大項目」に限る。4個以上並べるとどれも目立たない（ダッシュボード化）。[1][3][10]
3. **サイズ比（目安）:** 数字 : ラベル ≒ 3:1 以上。Stripe の数字帯は数字 42–52px／ラベル 15–17px、KPI 系の大サイズは数字 36–48px／ラベル 16px。[9][10]
   - CI 提案値（1280×720）: 主数字 72–96px、2個目 48–56px、ラベル 16–18px、単位 主数字の 45–55%。既存 v1.2 の濃紺カード数字 50px は「2個目」扱い。
4. **単位は数字より小さく、同じベースラインに。** 「¥1,457.8**億**」「**+**12**%**」の単位・符号は数字の約半分の大きさ・同じ色。上付きにしない（上付きは m³ など指数だけ）。[11][10]
5. **桁区切りと丸め。** 3桁カンマ必須（生の「1457800000」禁止）。小数は「主張が成り立つ精度」まで丸め、元ページの値と同じ桁で書く（ダイジェストで丸め直さない＝新しい数字を作らない）。[2][10]
6. **ラベルは数字の直下に1行、左揃え（数字と同じ左端）。** 何の数字か・期間・範囲を必ず含める（例: 「2026年1–9月 Amazon全体補正額」）。2行まで。[9][6]
7. **比較は向き＋符号で示す。** 増減は「+／−」や矢印を文字で添える。色だけで良し悪しを示さない。[10]
8. **数字の色はリッチブラック（白地）か白（濃紺地）。** クリスタル #C3D7EE は濃紺地の上でのみ数字色に使う（白地では淡くて読めない）。強調は1か所だけ。[6][12]
9. **出典を数字ブロックの下か note-line に。** Amazon Ads の insight ページは数字ごとに番号を振り、末尾に調査名・期間・N を明記している。CI では「出典: Shelpha（期間）」を note-line に残す。[13][4]
10. **等幅数字（tabular-nums）** を使い、2個並べたとき桁が揃うようにする。[10][9]

## 3. 主張文

1. **主張文 = 主語＋述語のある1文。** 「要因 A の内訳」のような名詞句は不可。「二重カウントが補正額の過半を占める」型。[2][4]
2. **長さ: 2行以内（日本語でおおむね 40 字以内が目安）。** 収まらないのは文字を縮めるサインではなく、主張が2つあるサイン。[2][4]
3. **数字を1つ含めると強い**（確かめられる主張になる）。ただし本文の主数字と同じ値を使う。[2]
4. **動詞は主張の型で選ぶ:** 比較＝「上回る／占める」、推移＝「増えた／反転した」、関係＝「連動する」（因果を言い切らない）。[2]
5. **主張文は h2 か右上の帯（v1.2 インサイト帯）に1か所だけ。** 同じ内容を本文で言い直さない。[4][6]
6. **左揃え。** 中央揃えは短い見出し1行のときだけ。[4]

## 4. 写真・人物

1. **写真は任意・従属。** ダイジェストの主役は数字。写真は「主張の対象が人／売場である」ことを示すときだけ、本文面積の 1/3 以下。[4][8]
2. **人物写真に色ベタ・半透明ティント・デュオトーンをかけない。** 顔がわかる写真に色をのせると本人の見た目を変え、肌が不自然に見える（大学ブランド指針でも禁止）。フラットな半透明ベタは写真を「隠す」側の処理。[14][15][16]
   - 人物の手前のレイヤーに crystal blue（#C3D7EE系）を半透明で重ねるのは禁止。色面やプレートは人物の後ろにだけ置く。（2026-10-30 若松さん・サイトと共通）
   - 人物写真の下部をグラデーションでフェードさせる（下端を透明や色で消す）のは禁止。（2026-10-30 若松さん・サイトと共通）
3. **文字を顔・目・手の上に置かない。** 文字は写真の空いた側（または写真の外）に。人物は画面の左右どちらかの 1/3 に寄せ、反対側を数字・主張用に空ける。[17][18]
4. **写真と文字を重ねる必要があるときだけ「グラデーションのスクリム」**：人物の上は透明、文字側だけ濃くする。それでも読めないなら写真を変えるかレイアウトを分ける（重ねない）。[15]
5. **切り抜き（カットアウト）は1被写体だけ。** 縁がきれいな高解像度素材に限る。髪・透明部分が粗いなら使わない。小さな切り抜きを複数並べない。[19]
6. **トリミングは被写体で決める。** 余った枠を埋めるために拡大しない。顔を切らない。人物写真を数字ブロックの背景にしない。[19][18]
7. **写真に CI 色を合わせたいときは「写真の外」で合わせる**（写真の外枠・隣の帯をクリスタル系にする）。写真の上に色を置かない。[14][16]

## 5. 色

1. **CI 3色の派生のみ。** 地＝白、主要文字＝リッチブラック #101820、面・帯＝クリスタル #C3D7EE 系（25% 等の淡色）。Ads 橙 #E87722 は使わない。
2. **強調色はページに1か所。** 主数字（または主数字のカード）だけを最も強いコントラストにし、ほかは中間色・グレー寄りへ下げる。[6][12][4]
3. **補助要素（罫線・軸・ラベル）は淡く。** 罫線は 1px の淡いクリスタル／グレー。影・3D・グラデーション面は使わない。[6][9][4]
4. **色だけで意味を持たせない。** 増減・良否は符号や文字でも示す。[10]
5. **コントラスト:** ラベル文字は背景に対して 4.5:1 以上、大きな数字でも 3:1 以上。白地にクリスタル文字は不可。[10]

## 6. 禁止事項

- ❌ **人物（顔がわかる写真）に半透明の水色ベタ・ティント・デュオトーンをのせる。**（若松さん FB 2026-10-29）[14][15][16]
- ❌ **人物の手前のレイヤーに crystal blue（#C3D7EE系）を半透明で重ねるのは禁止。色面やプレートは人物の後ろにだけ置く。**（若松さん 2026-10-30・サイトと共通）
- ❌ **人物写真の下部をグラデーションでフェードさせる（下端を透明や色で消す）のは禁止。**（若松さん 2026-10-30・サイトと共通）
- ❌ **写真だけのダイジェスト**（要素を隠して大きな写真＋タイトルだけが残る状態）。主数字ブロックが無いページはダイジェスト不合格。[1][3]
- ❌ **横に広いツリー・タイムライン図を半分幅に縮めて入れる。** 縮めて読めなくするくらいならダイジェスト対象外にする（p03 と同じ扱い）か、主張を支える1枝だけを数字として抜き出す。[4][8]
- ❌ 文字・数字を収めるためにフォントを縮める（主張を削るか分ける）。[4]
- ❌ 数字を 4 個以上並べる／同じ大きさで並べて主役を消す。[1][10]
- ❌ 元ページにない数字・丸め直した数字・新しい比率を作る。
- ❌ 単位を数字と同じ大きさにする／上付きにする（指数以外）。[11]
- ❌ 文字を顔の上に置く・顔を切るトリミング。[17][18]
- ❌ 3D・影・装飾アイコン・クリップアートで余白を埋める。[4][7]
- ❌ CI 外の色（Ads 橙 #E87722 など）、ヘッダー／フッター／版スタックの変更。
- ❌ 出典に Shelpha 以外の旧ツール名を書く（データ出所は Shelpha）。出典の欠落。

## 7. 合格チェックリスト（目視 QA 用・Yes/No）

| # | チェック | 期待 |
|---|---|---|
| 1 | 3秒見て、主張を1文で言える | Yes |
| 2 | 主張文は主語＋述語のある1文で、2行以内 | Yes |
| 3 | ページで一番大きい要素は証拠の数字 | Yes |
| 4 | 大きな数字は 1〜2 個（最大 3） | Yes |
| 5 | 数字の直下に「何の・いつの」ラベルが1〜2行ある | Yes |
| 6 | 単位・符号は数字より小さく、同じベースライン（上付きでない） | Yes |
| 7 | 数字はすべて元ページに同じ値・同じ桁で存在する | Yes |
| 8 | 写真が無くても主張が伝わる（写真は面積 1/3 以下） | Yes |
| 9 | 人物写真に色ベタ・半透明ティント・デュオトーンがかかっている | **No** |
| 10 | 文字が顔・目・手に重なっている | **No** |
| 11 | 大きな写真＋見出しだけで、数字ブロックが無い | **No** |
| 12 | 横長ツリー／タイムラインを縮小して読めない | **No** |
| 13 | 強調色（最強コントラスト）はページに1か所だけ | Yes |
| 14 | 使用色は CI 3色の派生のみ（#E87722 なし） | Yes |
| 15 | ヘッダー・フッター・版スタック・note-line は元ページと同一 | Yes |
| 16 | 出典は Shelpha 表記で残り、旧ツール名の表記が無い | Yes |
| 17 | 要素はすべて同じ左端／グリッドに揃っている | Yes |
| 18 | 1要素を消しても主張が弱まらない要素が残っていない | Yes |

## 8. 参考事例（URL）

1. Duarte「19 powerful presentation stats」— Glance Test（3秒）、1スライド1アイデア、1スライド1統計: https://www.duarte.com/blog/19-powerful-presentation-stats/
2. consultantlearning「One Message Per Chart: the Action Title」— 主張は主語＋動詞＋数字、"and" が要れば2枚、丸めは主張が成り立つ精度まで、動詞の選び方: https://consultantlearning.org/learn/PR2.03/
3. Duarte「3 secrets to choosing and designing unforgettable visual aids」— 信号を増やしノイズを減らす、1スライド1アイデア: https://www.duarte.com/blog/secrets-to-choosing-designing-unforgettable-visual-aids/
4. Deckary「Consulting Slide Standards (MBB)」— アクションタイトル2行以内、フォントを縮めない、出典必須、色3–4色・強調は戦略的に、装飾・ストック写真を排除、グリッド揃え: https://deckary.com/blog/consulting-slide-standards
5. Design Atlas「Big Number Slide」— 数字を画面最大に、説明は1行、単位を曖昧にしない: https://design.solhun.com/en/presentation/big-number-slide/
6. Duarte（Nancy Duarte）「5 Ways to Display Data Effectively in Presentations」— 結論だけ見せる、補助要素は淡いグレー、強調点だけ強い色: https://www.duarte.com/blog/display-data-in-presentations/
7. Garr Reynolds「How to Design a Great Presentation」— 余白を埋めない、S/N 比、画像は大きく1枚: https://www.garrreynolds.com/design-tips
8. Presentation Zen（O'Reilly 抄）Empty Space / Signal-to-Noise: https://www.oreilly.com/library/view/presentation-zen-simple/9780132901529/ch06lev1sec5.html ／ https://www.oreilly.com/library/view/presentation-zen-simple/9780132901529/ch06lev1sec3.html
9. Kage「Centered commerce stats band (stripe.com)」— 主張見出し＋等幅4指標、数字 42–52px／ラベル 15–17px、tabular nums、カード・影なし、1px 罫線: https://kage.design/component/stripe-stats
10. Stellae「Stat Component」— 数字/ラベルのサイズ表、指標は多くても3–6、最重要を先頭、桁区切り、色だけで増減を示さない、コントラスト基準: https://www.stellae.design/en/components/stat
11. Maersk Design System「Units of measurement」— 単位の表記、上付きは指数だけ: https://designsystem.maersk.com/content/numbers/units-of-measurement/
12. Google Design「Six Principles for Designing Any Chart」— 認知負荷を減らす、色は意味のある所だけ、データの出所を明示: https://medium.com/google-design/redefining-data-visualization-at-google-9bdcf2e447c6
13. Amazon Ads「5 top marketing trends of 2026」— 統計ごとに番号脚注、末尾に調査名・期間・N: https://advertising.amazon.com/library/news/marketing-trends-2026 ／ 参考: aboutamazon「Prime Day 2018: by the numbers」（数字＋短い見出し＋1文の反復）: https://www.aboutamazon.com/news/amazon-prime/prime-day-2018-by-the-numbers
14. University of Oregon「Duotones」— 顔がはっきり写る写真にデュオトーンをかけない（本人の見た目を変えない）: https://communications.uoregon.edu/duotones
15. Gradiently「Gradient overlays」— 全面のフラット半透明は写真を隠す、被写体の上は透明・文字側だけ濃く、肌をくすませる: https://gradiently.design/guide/gradient-overlay
16. Gradiently「The duotone effect」— 明度差の小さい色対や淡いシャドウ色は顔を平板にする: https://gradiently.design/guide/duotone-effect
17. aitaskbytask「Speaker portrait with room for event text」／検索要約 — 文字を顔・目・手に重ねない、空き側に置く: https://www.aitaskbytask.com/guides/speaker-portrait-text-space/
18. University of Derby「Subject in image and headline breaks」— 被写体を中央1/3の右寄りに置き見出しの場所を確保、寄りでも顔は残す: https://www.derby.ac.uk/digital-guidelines/image-hero/subject-in-image-and-headline-breaks/
19. PPTX.gallery「Cutout Subject」— 切り抜きは1被写体、縁のきれいな素材、粗い切り抜きは避ける: https://www.pptx.gallery/image-treatments/cutout-subject
20. Duarte「Creating high-impact visuals for AWS re:Invent」— 1枚で1つを語る "hero" スライド、大胆な一文: https://www.duarte.com/approach/case-studies/creating-high-impact-visuals-for-aws/
21. Business Insider「Jeff Bezos email against PowerPoint」— 箇条書きは重要度の差と関係を潰す → ダイジェストでも箇条書きを並べず、序列をつける: https://www.businessinsider.com/jeff-bezos-email-against-powerpoint-presentations-2015-7

画像リファレンス: `digest_refs/`（`digest_refs/refs.md` に出典 URL）。
