#!/usr/bin/env bash
# ci-finalize.sh — CIデッキHTMLを「フォントが揃った1台（ファイナライザ/Mac）」で最終成果物へ変換する。
#
# 方針（最堅牢・全員Mac × Adobe Fonts 前提）:
#   1) HTML → PDF（Chrome ヘッドレス印刷）。使用フォントの**サブセットがPDFへ自動埋め込み**され、
#      どのOS・どのビューアでも忠実表示になる（Adobe Fonts も PDF 埋め込みは許諾された通常利用）。
#   2) その PDF を scripts/html_to_pptx.py に渡し、**1スライド=1画像の PPTX** を生成（非編集＝ドリフト不可）。
#   3) Google スライド化は「PPTX を Drive にアップ → 右クリック→Google スライドで開く」で Drive が変換（追加描画不要）。
#   4) （任意）--outline: Ghostscript でテキストをベクター化した**フォント完全独立の不変版 PDF**も出す。
#
# セットアップ:
#   - CI フォントはすべて macOS 標準（英字=Hoefler Text／和文=Hiragino・Yu Mincho）。
#     → 各 Mac で追加のフォント導入も Adobe CC アクティベートも不要。そのまま忠実に描画できる。
#   - Linux ランナーで回す場合のみ同等フォントの導入が必要（基本は Mac 実行を推奨）。
#
# 使い方:
#   bash 5co-CI-kit/ci-finalize.sh <deck.html> [-o OUTDIR] [--outline] [--no-pptx] [--open]
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"
H2P="$REPO_ROOT/scripts/html_to_pptx.py"
OVF="$SELF_DIR/slide_overflow_check.py"
OVL="$SELF_DIR/check_text_overlap.py"
NEG="$SELF_DIR/graph_node_edge_check.py"
SVGL="$SELF_DIR/svg_label_check.py"
PARITY="$REPO_ROOT/scripts/check-slide-ci-parity.py"

say(){ printf '%s\n' "$*"; }
die(){ printf '❌ %s\n' "$*" >&2; exit 1; }

# ---- 引数 ----
SRC=""; OUTDIR="./ci-out"; DO_OUTLINE=0; DO_PPTX=1; DO_OPEN=0
while [ $# -gt 0 ]; do
  case "$1" in
    -o|--out) OUTDIR="$2"; shift 2;;
    --outline) DO_OUTLINE=1; shift;;
    --no-pptx) DO_PPTX=0; shift;;
    --open) DO_OPEN=1; shift;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    *) SRC="$1"; shift;;
  esac
done
[ -n "$SRC" ] || die "入力 HTML を指定してください: ci-finalize.sh <deck.html>"
[ -f "$SRC" ] || die "ファイルが見つかりません: $SRC"
mkdir -p "$OUTDIR"
BASE="$(basename "$SRC")"; STEM="${BASE%.*}"
PDF="$OUTDIR/$STEM.pdf"; PPTX="$OUTDIR/$STEM.pptx"; PDF_OL="$OUTDIR/${STEM}_outlined.pdf"

# ---- Chrome/Chromium 探索（Mac優先→Playwright同梱→PATH） ----
find_chrome(){
  local c
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/opt/pw-browsers"/chromium-*/chrome-linux/chrome \
    "/opt/pw-browsers"/chromium_headless_shell-*/chrome-linux/headless_shell; do
    [ -x "$c" ] && { printf '%s' "$c"; return 0; }
  done
  for c in google-chrome chromium chromium-browser chrome; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return 0; }
  done
  return 1
}
CHROME="$(find_chrome)" || die "Chrome/Chromium が見つかりません（Mac は Google Chrome を推奨）。"
say "Chrome: $CHROME"

# ---- 印刷用CSSを注入した一時HTML（1スライド=1ページ・余白0） ----
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
PRINT_CSS='<style id="ci-finalize-print">@media print{@page{size:297mm 210mm;margin:0}
 .slide{page-break-after:always;break-after:page;box-shadow:none!important;margin:0!important}
 .slide:last-child{page-break-after:auto}}</style>'
INJECTED="$TMP/$STEM.html"
# </head> 直前に注入（無ければ先頭に付与）。同ディレクトリの相対アセットも解決できるよう元の隣に置く。
INJECTED="$(dirname "$SRC")/.ci-finalize.$STEM.html"
if grep -qi '</head>' "$SRC"; then
  awk -v css="$PRINT_CSS" 'BEGIN{IGNORECASE=1} /<\/head>/ && !done{print css; done=1} {print}' "$SRC" > "$INJECTED"
else
  { printf '%s\n' "$PRINT_CSS"; cat "$SRC"; } > "$INJECTED"
fi
trap 'rm -rf "$TMP"; rm -f "$INJECTED"' EXIT

# ---- 任意ゲート: はみ出し検査（best-effort・止めない） ----
if [ -f "$OVF" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ はみ出し検査（gate）"
  python3 "$OVF" "$SRC" 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "はみ出し検査 NG（V3.2 規定: OK になるまで配布不可。上の行のスライドを修正してから再実行）"
fi

# ---- ゲート: 文字重なり検査（absolute配置要素同士の衝突＝はみ出し検査の死角） ----
if [ -f "$OVL" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ 文字重なり検査（gate）"
  python3 "$OVL" "$SRC" 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "文字重なり検査 NG（要素同士が重なっています。上の行のスライドを修正してから再実行）"
fi

# ---- ゲート: ノード・エッジ図検査（.ne-graph のノード重なり・矢印接続＝DOM検査の死角） ----
if [ -f "$NEG" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ ノード・エッジ図検査（gate）"
  python3 "$NEG" "$SRC" 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "ノード・エッジ図検査 NG（ノードの重なり/浮いた矢印。グリッド座標系＝V3.2_FORMAT.md「ノード・エッジ型グラフ図」に従い修正してから再実行）"
fi

# ---- 警告: SVG図版のラベル検査（DOM検査の死角＝図の中の文字の重なり・切れ・地色同色） ----
#   既存デッキに未修正のものが残るため、当面は警告のみ（--warn-only で終了コードを0に固定）。
#   新規・改訂したページで出たら必ず直す。
if [ -f "$SVGL" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ SVG図版ラベル検査（warn）"
  python3 "$SVGL" "$SRC" --warn-only 2>&1 | sed 's/^/  /'
fi

# ---- ゲート: CIトークン整合検査（廃止トークン --navy/--powder・旧hex・Georgia混入を検出） ----
if [ -f "$PARITY" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ CIトークン整合検査（gate）"
  python3 "$PARITY" "$SRC" 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "CIトークン整合検査 NG（廃止トークン/旧hex/Georgia混入。上の行を修正してから再実行）"
fi

# ---- 1) HTML → PDF（フォントサブセット自動埋込） ----
say "▶ HTML → PDF"
"$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
  --print-to-pdf="$PDF" "file://$INJECTED" >/dev/null 2>&1 \
  || die "PDF 生成に失敗（Chrome ヘッドレス）。"
[ -s "$PDF" ] || die "PDF が空です: $PDF"
say "  ✓ $PDF"

# ---- 2) PDF → 画像PPTX（既存 html_to_pptx.py） ----
if [ "$DO_PPTX" = 1 ]; then
  if [ -f "$H2P" ] && command -v python3 >/dev/null 2>&1; then
    say "▶ PDF → PPTX（1スライド=1画像）"
    python3 "$H2P" "$PDF" -o "$PPTX" --aspect a4 2>&1 | sed 's/^/  /' \
      && say "  ✓ $PPTX" || say "  ⚠ PPTX 生成に失敗（python-pptx / pdf2image を確認）"
  else
    say "▶ PPTX スキップ（$H2P が無い or python3 不在）"
  fi
fi

# ---- 3) （任意）アウトライン版 PDF（フォント完全独立の不変版） ----
if [ "$DO_OUTLINE" = 1 ]; then
  if command -v gs >/dev/null 2>&1; then
    say "▶ アウトライン版 PDF（テキスト→ベクター）"
    gs -o "$PDF_OL" -sDEVICE=pdfwrite -dNoOutputFonts "$PDF" >/dev/null 2>&1 \
      && say "  ✓ ${PDF_OL}（フォント非依存の完全忠実マスター）" || say "  ⚠ Ghostscript 変換に失敗"
  else
    say "▶ アウトライン: Ghostscript(gs) 未導入のためスキップ（brew install ghostscript）"
  fi
fi

# ---- 4) 案内 ----
say ""
say "=== 完了 ==="
say "  PDF : $PDF"
[ "$DO_PPTX" = 1 ] && [ -s "$PPTX" ] && say "  PPTX: $PPTX"
[ "$DO_OUTLINE" = 1 ] && [ -s "$PDF_OL" ] && say "  PDF(outlined): $PDF_OL"
say ""
say "Google スライド化：上記 PPTX を共有ドライブへアップ → 右クリック→「Google スライドで開く」"
say "  （Drive が自動変換。追加のレンダリングは不要＝PPTX と Slides を1ソースで両取り）"
if [ "$DO_OPEN" = 1 ] && command -v open >/dev/null 2>&1; then open "$PDF" || true; fi
