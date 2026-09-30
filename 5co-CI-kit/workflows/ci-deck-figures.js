export const meta = {
  name: 'ci-deck-figures',
  description: 'CIデッキに図・イラストをページグループごとに並列制作し、グループごとにレビュー・修正する（FIGURES_GUIDE.md 6）',
  whenToUse: '完成したCIデッキの複数ページに、理解を助ける図・イラストをマルチエージェントで足したいとき',
  phases: [
    { title: 'Design', detail: 'グループごとに図を作成' },
    { title: 'Review', detail: '描画を確認し修正' },
  ],
}
// 引数（Workflow の args）:
// {
//   kit:      "5co-CI-kit" への絶対パス（例 "/path/to/repo/5co-CI-kit"）
//   deck:     完成したデッキ HTML の絶対パス
//   figs:     図の断片を置くディレクトリの絶対パス（figs/<ページID>.html）
//   work:     作業用ディレクトリの絶対パス（プレビューHTML・PNG の置き場）
//   context:  デッキの目的・読み手・守ること（任意・文字列）
//   groups:   [{ key: "intro", ids: ["p2","p3"], brief: "- p2: …の図\n- p3: …" }, …]
// }
const A = args || {}
if (!A.kit || !A.deck || !A.figs || !A.work || !Array.isArray(A.groups)) {
  throw new Error('args に kit / deck / figs / work / groups が必要です（ファイル冒頭のコメント参照）')
}

const COMMON = `
あなたは 5co. のCIスライドに、内容を理解しやすくする図・イラストを追加する担当です。
${A.context ? `## デッキについて\n${A.context}\n` : ''}
## 規定（必ず読む）
${A.kit}/FIGURES_GUIDE.md を最初に読み、2〜5 章に従う（色は CSS 変数のみ・書体を書かない・文字10px以上・ページにない事実を足さない・本文の下に in-flow・1ページ1図・原本は構成と言葉に忠実に）。

## 仕組み
- デッキ本体 ${A.deck} は編集しない（読むのは可）。
- 図は ${A.figs}/<ページID>.html に HTML 断片（インラインSVG または HTML/CSS）として書く。
- 担当ページ以外の断片は作らない・触らない。

## 確認手順（図を書いたら毎回）
1. python3 ${A.kit}/ci_figs.py lint ${A.figs}/<ページID>.html
2. python3 ${A.kit}/ci_figs.py inject ${A.deck} ${A.figs} --only <担当ID,…> -o ${A.work}/<あなたのラベル>.html
3. bash ${A.kit}/ci-gates.sh ${A.work}/<あなたのラベル>.html
4. python3 ${A.kit}/ci_figs.py preview ${A.work}/<あなたのラベル>.html --pages <担当ID,…> --out ${A.work}/png
   → PNG を Read で見て、重なり・切れ・小さすぎる文字・フッターとの近さがないか確かめる。
最初に、図を入れる前のページも preview して、空き領域と本文の言葉を把握すること。
`

const OUT = {
  type: 'object',
  properties: {
    pages: { type: 'array', items: { type: 'object', properties: {
      page_id: { type: 'string' },
      added: { type: 'boolean' },
      what: { type: 'string', description: '追加した図の説明（1〜2文）。追加しない場合はその理由' },
      gates_ok: { type: 'boolean' },
    }, required: ['page_id', 'added', 'what', 'gates_ok'] } },
  },
  required: ['pages'],
}

const results = await pipeline(
  A.groups,
  (g) => agent(`${COMMON}\n## あなたのラベル: design-${g.key}\n## 担当ページ: ${g.ids.join(', ')}\n${g.brief || ''}\n\n担当ページすべてについて、図を作るか「追加不要」を判断し、作ったものは確認手順を最後まで通すこと。`,
    { label: `design:${g.key}`, phase: 'Design', schema: OUT }),
  (res, g) => agent(`${COMMON}\n## あなたのラベル: review-${g.key}\n## 役割: レビューと修正（担当ページ: ${g.ids.join(', ')}）\n別の担当者が作った図を厳しく確認し、問題があれば断片を直接直す。観点：3色ルール／文字の大きさ・切れ・重なり／本文や表との重なり・フッターとの距離（8mm以上）／本文の言葉との一致・新しい事実の有無／品位（稚拙・装飾過多なら簡素化）／ゲートOK。直したら確認手順をやり直す。\n前段の報告: ${JSON.stringify(res)}`,
    { label: `review:${g.key}`, phase: 'Review', schema: OUT }),
)
return results.filter(Boolean).flatMap(r => r.pages)
