export const meta = {
  name: 'ci-figure-competition',
  description: 'CIデッキの1枚の図をデザインコンペで決める：方向性の違う複数案を並列制作→観点の違う審査員が採点→優勝案に他案の良い点を取り込んで仕上げ（FIGURES_GUIDE.md 6）',
  whenToUse: '重要な概念図（全体マップ・サイクル図など）を、複数の見せ方から選んで決めたいとき',
  phases: [
    { title: 'Design', detail: '方向性ごとに図を制作' },
    { title: 'Judge', detail: '審査員が全案を採点' },
    { title: 'Finalize', detail: '優勝案を仕上げ' },
  ],
}
// 引数（Workflow の args）:
// {
//   kit:    "5co-CI-kit" への絶対パス
//   deck:   完成したデッキ HTML の絶対パス
//   page:   図を入れるページの ID（section の id か 2桁のページ番号）
//   work:   作業用ディレクトリの絶対パス（各案・PNG・仕上げ版の置き場）
//   brief:  図に必ず入れる内容・原本の構造・現行案の問題点・置き場所の大きさ（文字列）
//   directions: [{ id: "A_venn", dir: "…" }, …]   省略時は下の既定4案
//   lenses:     ["経営陣の視点：…", …]              省略時は下の既定3観点
// }
// 出力：work/<id>.html（各案）、work/final.html（仕上げ版）。採用するときは final.html を figs/<page>.html にコピーする。
const A = args || {}
if (!A.kit || !A.deck || !A.page || !A.work || !A.brief) {
  throw new Error('args に kit / deck / page / work / brief が必要です（ファイル冒頭のコメント参照）')
}
const DIRECTIONS = A.directions || [
  { id: 'A_faithful', dir: '原本に最も忠実な洗練版。構造・配置は原本のまま、重なり・余白・線の強弱を整えて読みやすくする。' },
  { id: 'B_cycle', dir: '流れ・循環を主役にした型。要素をリングや流路の上に置き、矢印そのものが構造になるようにする。' },
  { id: 'C_editorial', dir: 'エディトリアル／ミニマル。線画中心・塗りは最小限・大きな余白、タイポグラフィで階層をつくる。' },
  { id: 'D_panel', dir: 'パネル型インフォグラフィック。領域を角丸パネルにし、太めの矢印でつなぎ、要素をチップに整列させる。読みやすさ最優先。' },
]
const LENSES = A.lenses || [
  '経営陣の視点：会議で画面共有して一目で意味が伝わるか、ブランドの品位',
  'CIデザイン監修の視点：3色・余白・書体・整列・文字サイズ・静謐さ（Strategy, refined.）',
  '原本作成者の視点：原本の構造と言葉の意味がどれだけ正確に保たれているか',
]

const BRIEF = `
# デザインコンペ：${A.page} ページの図
${A.brief}

## 規定
${A.kit}/FIGURES_GUIDE.md の 2〜5 章に従う（色は CSS 変数のみ・書体を書かない・文字10px以上・原本の言葉を変えない・ページに収める）。
成果物は HTML 断片（インライン SVG を推奨）1ファイル。

## 確認手順（ID はあなたの案の ID）
1. 断片を ${A.work}/<ID>.html に書く
2. python3 ${A.kit}/ci_figs.py lint ${A.work}/<ID>.html
3. mkdir -p ${A.work}/figs_<ID> && cp ${A.work}/<ID>.html ${A.work}/figs_<ID>/${A.page}.html
4. python3 ${A.kit}/ci_figs.py inject ${A.deck} ${A.work}/figs_<ID> -o ${A.work}/<ID>_deck.html && bash ${A.kit}/ci-gates.sh ${A.work}/<ID>_deck.html
5. python3 ${A.kit}/ci_figs.py preview ${A.work}/<ID>_deck.html --pages ${A.page} --out ${A.work}/png → PNG を Read で目視し、OKになるまで直す
デッキ本体と他の人のファイルは触らない。
`

const JUDGE = {
  type: 'object',
  properties: {
    scores: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      fidelity: { type: 'number' }, clarity: { type: 'number' }, ci: { type: 'number' }, craft: { type: 'number' },
      comment: { type: 'string' },
    }, required: ['id', 'fidelity', 'clarity', 'ci', 'craft', 'comment'] } },
    winner: { type: 'string' },
    graft: { type: 'string', description: '優勝案に取り込むべき他案の良い点（具体的に）' },
  },
  required: ['scores', 'winner', 'graft'],
}

phase('Design')
const entries = (await parallel(DIRECTIONS.map(d => () =>
  agent(`${BRIEF}\n## あなたの ID: ${d.id}\n## 方向性\n${d.dir}\n\n完成したら、ファイルパスと狙いを2〜3文で返す。確認手順がOKになるまで返さない。`,
    { label: `design:${d.id}`, phase: 'Design' }).then(r => r ? { id: d.id, note: r } : null)))).filter(Boolean)
log(`${entries.length}/${DIRECTIONS.length} 案が提出されました`)
if (!entries.length) return { error: '提出なし' }

phase('Judge')
const PNG = id => `${A.work}/png/${id}_deck_${A.page}.png`
const js = (await parallel(LENSES.map((lens, i) => () =>
  agent(`あなたはデザインコンペの審査員${i + 1}です。${lens}\n${BRIEF}\n## 応募作品\n${entries.map(e => `- ${e.id}: 断片=${A.work}/${e.id}.html / プレビュー=${PNG(e.id)} / 制作者の説明: ${String(e.note).slice(0, 500)}`).join('\n')}\n\n各プレビューPNGを必ず Read で見て、4観点（原本への忠実さ fidelity・読みやすさ clarity・CI準拠と品位 ci・仕上がり craft）を各10点で採点する。ファイルは編集しない。`,
    { label: `judge:${i + 1}`, phase: 'Judge', schema: JUDGE })))).filter(Boolean)
const totals = {}
for (const j of js) for (const s of j.scores) totals[s.id] = (totals[s.id] || 0) + s.fidelity + s.clarity + s.ci + s.craft
const ranking = Object.entries(totals).sort((a, b) => b[1] - a[1])
const winner = ranking[0][0]
log(`集計: ${ranking.map(([k, v]) => `${k}=${v}`).join(' / ')} → 優勝 ${winner}`)

phase('Finalize')
const final = await agent(`${BRIEF}\n## 役割：優勝案の仕上げ\n優勝案 ${winner}（${A.work}/${winner}.html）に、審査員のコメントと「取り込むべき他案の良い点」を反映し、${A.work}/final.html に書く（元の案は残す）。確認手順は ID=final で行う。\n審査結果:\n${JSON.stringify(js).slice(0, 6000)}\n\n最後に、何を取り込んだかを箇条書きで返す。`,
  { label: 'finalize', phase: 'Finalize' })
return { ranking, winner, judges: js, final }
