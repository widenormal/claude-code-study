#!/bin/bash
# ci-gates.sh — 配布前の検査だけをまとめて走らせる軽量ランナー（PDF/PPTX は作らない）。
#
# なぜ要るか
#   ci-finalize.sh は PDF・PPTX 変換まで走るため、制作中の「直した→検査」の往復には重い。
#   検査は数秒で終わるので、制作ループ用に検査だけを1コマンドにまとめる。
#   コマンドを1本にすると、AI（Claude Code）に作業させる場合の往復も減り、トークン消費が下がる。
#
# 使い方
#   ci-gates.sh <deck.html> [<deck.html> …]
#   ci-gates.sh -v <deck.html>     … 各検査の生出力も表示
#   ci-gates.sh --strict <deck>    … SVGラベル検査も落とす（既定は警告）
#   ci-gates.sh --source <原文> <deck>
#                                  … LLM が書き直した版（やさしい版・英語版）の検品も走らせる
#
# 検査（VERSION の gates 行が正）
#   1. slide_overflow_check.py   … あふれ            （落とす）
#   2. check_text_overlap.py     … 要素の重なり      （落とす）
#   3. graph_node_edge_check.py  … ノード・エッジ図   （.ne-graph があるときだけ・落とす）
#   4. svg_label_check.py        … SVG図版のラベル   （既定は警告・--strict で落とす）
#   5. llm_output_check.py       … LLM出力の破損     （--source を渡したときだけ・落とす）
set -uo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

V=0; STRICT=0; SOURCE=""; FILES=()
while [ $# -gt 0 ]; do case "$1" in
  -v|--verbose) V=1;;
  --strict) STRICT=1;;
  --source) SOURCE="${2:-}"; shift;;   # LLM が書き直した版の原文（llm_output_check.py へ渡す）
  -h|--help) sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
  *) FILES+=("$1");;
esac; shift; done
[ ${#FILES[@]} -gt 0 ] || { echo "❌ 入力 HTML を指定してください: ci-gates.sh <deck.html>" >&2; exit 2; }

FAIL=0
gate() {  # gate <ラベル> <スクリプト> <html> <落とすか(1/0)> [追加引数…]
  local label="$1" script="$2" html="$3" hard="$4"; shift 4
  [ -f "$script" ] || { printf '  – %-18s (スクリプト無し)\n' "$label"; return 0; }
  local out rc
  out="$(python3 "$script" "$html" "$@" 2>&1)"; rc=$?
  # --warn-only は所見があっても終了コード0で返るため、本文が「: OK」で終わるかで判定する
  if [ $rc -eq 0 ] && printf '%s' "$out" | tail -1 | grep -q ': *OK$'; then
    printf '  ✔ %-18s OK\n' "$label"
  elif [ $rc -eq 0 ]; then
    printf '  ⚠ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /' 
  elif [ "$hard" = "1" ]; then
    FAIL=1; printf '  ✘ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /'
  else
    printf '  ⚠ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /'
  fi
  [ $V -eq 1 ] && printf '%s\n' "$out" | sed 's/^/      /'
  return 0
}

for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "❌ ファイルが見つかりません: $f" >&2; FAIL=1; continue; }
  echo "▶ $(basename "$f")"
  gate "あふれ"        "$SELF_DIR/slide_overflow_check.py" "$f" 1
  gate "要素の重なり"  "$SELF_DIR/check_text_overlap.py"   "$f" 1
  grep -q 'ne-graph' "$f" && gate "ノード・エッジ図" "$SELF_DIR/graph_node_edge_check.py" "$f" 1
  if [ $STRICT -eq 1 ]; then gate "SVGラベル" "$SELF_DIR/svg_label_check.py" "$f" 1
  else                       gate "SVGラベル" "$SELF_DIR/svg_label_check.py" "$f" 0 --warn-only; fi
  if [ -n "$SOURCE" ]; then
    if [ -f "$SOURCE" ]; then gate "LLM出力の検品" "$SELF_DIR/llm_output_check.py" "$f" 1 --source "$SOURCE"
    else echo "  ✘ LLM出力の検品     原文が見つかりません: $SOURCE"; FAIL=1; fi
  fi
  N=$(grep -c '<section class="slide' "$f")
  printf '  %sスライド %s枚\n' "" "$N"
done

[ $FAIL -eq 0 ] && echo "✅ ゲートOK" || echo "❌ ゲートNG（上を参照）"
exit $FAIL
