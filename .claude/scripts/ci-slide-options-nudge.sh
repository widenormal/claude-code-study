#!/usr/bin/env bash
# ci-slide-options-nudge.sh — CIスライドの作成依頼を検知し、「出力オプションを質問して」と Claude に伝える
#
# 何のためか（2026-09-27 制定・5co-CI-kit v3.9）:
#   CIスライドの出力は「HTML は常に作る／動く資料・PDF・PPTX は任意」になった。何を出すかは
#   作成依頼のたびに選ぶ。人が毎回「PDF は要らない」と言い添えるのは忘れるので、依頼を受けた時点で
#   Claude の側から1回だけ質問させる。答えはデッキの隣の <デッキ名>.ci-options.json に残り、
#   ci-finalize.sh がそれを読んで出し分ける（5co-CI-kit/ci_options.py）。
#
# 呼ばれ方:
#   UserPromptSubmit フックの入力 JSON を標準入力で受け、該当すれば Claude に渡す文を標準出力へ出す
#   （該当しなければ何も出さない）。いまは session-claudemd-nudge.sh（登録済みの UserPromptSubmit
#   フック）から呼ばれ、その JSON の additionalContext に合流する。.claude/settings.json は保護
#   ファイルのため、単独のフックとして登録するのは管理者の作業（--hook を付ければ単独でも JSON を出す）。
#
# 判定（誤爆より取りこぼしを避ける。CIスライド以外なら Claude が無視する指示にしてある）:
#   「スライド／デッキ／プレゼン／定例資料・報告資料・提案資料」と、「作って／作成／作る／生成／組んで…」の
#   両方を含むプロンプト。「直して」「修正」だけの依頼では鳴らさない（作成時だけ聞く）。
#
# 失敗してもプロンプト処理を止めないため、常に exit 0 で抜ける。
set -uo pipefail

MODE="${1:-}"
INPUT=$(cat 2>/dev/null || true)

prompt=""
if command -v jq >/dev/null 2>&1; then
  prompt=$(printf '%s' "$INPUT" | jq -r '.prompt // empty' 2>/dev/null)
elif command -v python3 >/dev/null 2>&1; then
  prompt=$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("prompt",""))
except Exception: pass' 2>/dev/null)
fi
[ -n "$prompt" ] || exit 0

# 人の依頼ではない入力（バックグラウンド処理の完了通知・PR 等の外部イベント）には鳴らさない。
# 実測（2026-09-27）: 完了通知に載ったコマンド文「…CIスライド出力オプション（作成依頼の検知…」で誤って鳴った
case "$prompt" in
  *"<task-notification>"*|*"[SYSTEM NOTIFICATION"*|*"<wake reason="*|*"<webhook-payload>"*) exit 0 ;;
esac

NOUN='(スライド|デッキ|プレゼン|パワポ|定例資料|報告資料|提案資料|説明資料|報告書|slides?|deck|presentation|powerpoint)'
VERB='(作って|作成|作る|作りたい|つくって|制作|生成|組んで|組む|起こして|仕上げて|まとめて|用意して|お願い|にして|化して|build|create|make|prepare)'
NEG='(作らない|作らず|作成不要)'
printf '%s' "$prompt" | grep -Eqi "$NOUN" || exit 0
printf '%s' "$prompt" | grep -Eqi "$VERB" || exit 0
printf '%s' "$prompt" | grep -Eq "$NEG" && exit 0

CTX='【CIスライド出力オプションの確認（自動・5co-CI-kit v3.11）】この依頼はCIスライドの作成に見えます。作り始める前に、AskUserQuestion を1回だけ使って出力オプションを確認してください（1問・multiSelect: true）。
- 問い: 「HTML は必ず作ります（既定は HTML のみ）。動く資料と図のマルチエージェントは既定オンです。ほかに何を出しますか？（メール送付用 PDF は若松さん承認後のみ）」
- 選択肢: ①動く資料をオフにする（既定オン・押すと根拠パネルが開く） ②PDF（メール送付用・**若松さん明示承認後のみ**・承認前は作らない＝PDF_OUTPUT_RULE.md） ③PPTX（1枚1画像・Googleスライド化向け） ④図マルチエージェントをオフにする（既定オン・作成→レビュー）
- 何も選ばなければ HTML＋動く資料オン＋図マルチエージェントオン（PDF・PPTX なし）。
回答を得たら `python3 5co-CI-kit/ci_options.py write <deck.html> --interactive|--no-interactive --pdf|--no-pdf --pptx|--no-pptx --figs-multi|--no-figs-multi` で記録し（ci-finalize.sh がこれを読む。記録が無いと HTML のみで、PDF・PPTX は出ない）。既定どおりなら --interactive --figs-multi --no-pdf。動く資料オンなら ci_head.py --interactive、部品は ci_interactive.py、規定は V3.2_FORMAT.md「動く資料」。
ただし、依頼文で出力形式がすでに指定されている／このセッションで同じデッキについて決定済み／既存の <デッキ名>.ci-options.json がある場合は質問せずそれに従う（質問を省いた場合も、ci-options.json が無ければ同じコマンドで必ず記録する）。CIスライドの作成でなければこの指示は無視する。
図マルチエージェントがオンなら、デッキの本文ができた時点で Workflow（scriptPath: 5co-CI-kit/workflows/ci-deck-figures.js）を実行。オフなら Claude が描き、表・箇条書きは `python3 5co-CI-kit/ci_figs.py autofig <deck.html>`。
【図・イラストの既定（v3.11）】指示が無くても本文ページにはフレームワーク図・グラフかイラストを置く。写真を多用。企業名・組織名・商品名→ロゴ必須／商品・ASIN→商品画像必須／カテゴリー→生成または取得（FIGURES_GUIDE.md 2-1）。仕上げ前に FIG? をゼロに。ダイジェスト要求時は DIGEST_GUIDE.md。'

if [ "$MODE" = "--hook" ]; then
  if command -v jq >/dev/null 2>&1; then
    jq -n --arg c "$CTX" '{hookSpecificOutput:{hookEventName:"UserPromptSubmit", additionalContext:$c}}'
  else
    python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":sys.argv[1]}}, ensure_ascii=False))' "$CTX"
  fi
else
  printf '%s\n' "$CTX"
fi
exit 0
