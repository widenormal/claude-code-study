#!/bin/bash
# Qwen (Ollama ローカル) 呼び出しラッパー。
# 用途: API 代ゼロでの軽処理。要約、分類、フォーマット変換、プロンプトドラフト、
#       機密情報を含むテキストの下ごしらえなど。
#
# 認証不要（ローカル動作）。Ollama サーバが起動している必要がある。
# 既定モデル: scripts/llm-models.conf の QWEN_DEFAULT_MODEL（env QWEN_MODEL で上書き可）
#
# 使い方:
#   bash scripts/qwen-call.sh "この日本語を 50 字に要約して: ..."
#   cat doc.txt | bash scripts/qwen-call.sh --model qwen3.5:14b-instruct --task summarize
#   bash scripts/qwen-call.sh --task classify "件名: 請求書 → カテゴリ?"

set -euo pipefail

# モデル既定値は llm-models.conf（正データ・申請制で自動更新）から解決
_CONF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/llm-models.conf"
[ -f "$_CONF" ] && . "$_CONF"
MODEL="${QWEN_MODEL:-${QWEN_DEFAULT_MODEL:-qwen3.5:7b-instruct}}"
HOST="${OLLAMA_HOST:-http://localhost:11434}"
TASK="generic"
PROMPT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --model) MODEL="${2:-}"; shift 2 ;;
    --host) HOST="${2:-}"; shift 2 ;;
    --task) TASK="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) PROMPT="${PROMPT}${PROMPT:+ }$1"; shift ;;
  esac
done

if [ ! -t 0 ]; then
  STDIN_CTX="$(cat)"
  if [ -n "$STDIN_CTX" ]; then
    PROMPT="${PROMPT}

${STDIN_CTX}"
  fi
fi

if [ -z "$PROMPT" ]; then
  echo "ERROR: プロンプトを指定してください（引数または stdin）" >&2
  exit 1
fi

# task に応じて system プロンプトを切替
case "$TASK" in
  summarize)
    SYSTEM="日本語で 200 字以内に簡潔に要約してください。重要な数値や固有名詞は保持。"
    ;;
  classify)
    SYSTEM="入力テキストをカテゴリ判定し、カテゴリ名と短い理由のみ出力してください。"
    ;;
  draft-prompt)
    SYSTEM="後段のより高性能な LLM に渡すプロンプトのドラフトを 3 案、それぞれ 1〜2 行で出力してください。"
    ;;
  format)
    SYSTEM="入力テキストの内容は変えず、構造化（Markdown 見出し+箇条書き）だけ整えてください。"
    ;;
  *)
    SYSTEM="日本語で簡潔に答えてください。"
    ;;
esac

if ! curl -fsS "$HOST/api/tags" >/dev/null 2>&1; then
  cat >&2 <<EOF
ERROR: Ollama サーバ ($HOST) に接続できません。
  - Ollama が起動しているか確認: ollama serve
  - SessionStart フック（.claude/hooks/session-start-multi-llm-setup.sh）の実行ログを確認
EOF
  exit 1
fi

PAYLOAD=$(jq -n \
  --arg model "$MODEL" \
  --arg system "$SYSTEM" \
  --arg prompt "$PROMPT" \
  '{
    model: $model,
    stream: false,
    messages: [
      {role: "system", content: $system},
      {role: "user", content: $prompt}
    ]
  }')

RESPONSE=$(curl -fsS "$HOST/api/chat" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

echo "$RESPONSE" | jq -r '.message.content // empty'

EVAL_COUNT=$(echo "$RESPONSE" | jq -r '.eval_count // 0')
PROMPT_EVAL=$(echo "$RESPONSE" | jq -r '.prompt_eval_count // 0')
echo "" >&2
echo "[qwen-call] model=$MODEL task=$TASK tokens=${PROMPT_EVAL}/${EVAL_COUNT} (local, \$0)" >&2
