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
# 出力オプション（v3.9・PDF は必須でなく任意）:
#   何を出すかは作成依頼のたびに選ぶ（Claude Code ではフックが質問を促す）。選んだ結果はデッキの隣の
#   <デッキ名>.ci-options.json（ci_options.py write で書く）に残し、本スクリプトが読む。
#   優先順位＝コマンドの --pdf/--no-pdf/--pptx/--no-pptx ＞ ci-options.json ＞ 既定（HTML のみ＝PDF・PPTX は出さない）。
#   既定を HTML のみにした（2026-09-28・ユーザー指示）: PDF は作成依頼時の質問で選ばれたときだけ出す。
#   PDF を出さずに PPTX だけ出すときも、PPTX は内部で一時 PDF を経由して作る（一時 PDF は残さない）。
#   PDF・PPTX とも出さないときは検査だけ走らせ、配布物＝HTML（動く資料ならそのまま開いて使う）。
#   PDF・PPTX は #static（組み上がった最終状態）で印刷する＝動く資料でも静止した資料として読める。
#
# セットアップ:
#   - CI フォントはすべて macOS 標準（英字=Hoefler Text／和文=Hiragino・Yu Mincho）。
#     → 各 Mac で追加のフォント導入も Adobe CC アクティベートも不要。そのまま忠実に描画できる。
#   - Linux ランナーで回す場合のみ同等フォントの導入が必要（基本は Mac 実行を推奨）。
#
# 使い方:
#   bash 5co-CI-kit/ci-finalize.sh <deck.html> [-o OUTDIR] [--pdf|--no-pdf] [--pptx|--no-pptx]
#                                  [--options <file.json>] [--outline] [--open] [--allow-no-figs "<理由>"]
#
# 図の既定（v3.10）: 本文ページに図（フレームワーク図・グラフ・イラスト）が無いと止める（ci_figs.py coverage --strict）。
#   表だけで足りるページは section に data-fig-exempt="理由" を付ける。どうしても今回だけ通す場合は
#   --allow-no-figs "<理由>" を付ける（理由が出力に残る・黙って通さない）。
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
SRC=""; OUTDIR="./ci-out"; DO_OUTLINE=0; DO_OPEN=0; OPTS=""; ALLOW_NOFIG=""
CLI_PDF=""; CLI_PPTX=""
while [ $# -gt 0 ]; do
  case "$1" in
    -o|--out) [ $# -ge 2 ] || die "$1 の後に出力先を指定してください"; OUTDIR="$2"; shift 2;;
    --outline) DO_OUTLINE=1; shift;;
    --pdf) CLI_PDF=1; shift;;
    --no-pdf) CLI_PDF=0; shift;;
    --pptx) CLI_PPTX=1; shift;;
    --no-pptx) CLI_PPTX=0; shift;;
    --options) [ $# -ge 2 ] || die "--options の後にファイルを指定してください"; OPTS="$2"; shift 2;;
    --open) DO_OPEN=1; shift;;
    --allow-no-figs) [ $# -ge 2 ] && [ -n "$2" ] || die "--allow-no-figs の後に理由を書いてください"; ALLOW_NOFIG="$2"; shift 2;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
    -*) die "知らないオプション: $1（--help 参照）";;
    *) [ -z "$SRC" ] || die "入力 HTML は1つだけ指定してください（$SRC と $1）"; SRC="$1"; shift;;
  esac
done
[ -n "$SRC" ] || die "入力 HTML を指定してください: ci-finalize.sh <deck.html>"
[ -f "$SRC" ] || die "ファイルが見つかりません: $SRC"
mkdir -p "$OUTDIR"
BASE="$(basename "$SRC")"; STEM="${BASE%.*}"
PDF="$OUTDIR/$STEM.pdf"; PPTX="$OUTDIR/$STEM.pptx"; PDF_OL="$OUTDIR/${STEM}_outlined.pdf"

# ---- 出力オプション（既定 → <デッキ名>.ci-options.json → コマンド引数 の順に上書き） ----
DO_PDF=0; DO_PPTX=0; WANT_INTERACTIVE=""   # 既定＝HTML のみ（PDF・PPTX は選ばれたときだけ）
if [ -z "$OPTS" ] && [ -f "$(dirname "$SRC")/$STEM.ci-options.json" ]; then
  OPTS="$(dirname "$SRC")/$STEM.ci-options.json"
fi
if [ -n "$OPTS" ]; then
  # 形式が壊れていたら止める（黙って既定に戻すと、要らない PDF や足りない PPTX が出る）
  RD="$(python3 "$SELF_DIR/ci_options.py" read "$OPTS")" || die "出力オプションを読めません: $OPTS"
  read -r O_PDF O_PPTX O_INT <<< "$RD"
  DO_PDF="$O_PDF"; DO_PPTX="$O_PPTX"; WANT_INTERACTIVE="$O_INT"
  say "出力オプション: $OPTS"
fi
[ -z "$CLI_PDF" ] || DO_PDF="$CLI_PDF"
[ -z "$CLI_PPTX" ] || DO_PPTX="$CLI_PPTX"
[ "$DO_OUTLINE" = 1 ] && DO_PDF=1   # アウトライン版は PDF から作る
# 選んだ形と HTML の組み方が食い違っていたら止める（版スタンプ＝ci_head.py --interactive だけが書く）
if grep -q 'ci_head v[0-9.]* interactive' "$SRC"; then HAS_INT=1; else HAS_INT=0; fi
if [ "$WANT_INTERACTIVE" = 1 ] && [ "$HAS_INT" = 0 ]; then
  die "動く資料（interactive:true）を選んでいますが、HTML が ci_head.py --interactive で組まれていません"
fi
if [ "$WANT_INTERACTIVE" = 0 ] && [ "$HAS_INT" = 1 ]; then
  die "動く資料を選んでいない（interactive:false）のに、HTML が --interactive で組まれています（選び直すか組み直す）"
fi
[ -z "$WANT_INTERACTIVE" ] && [ "$HAS_INT" = 1 ] && WANT_INTERACTIVE=1   # オプション無し＝HTML の組み方に従う
OUT_DESC="HTML"
[ "$WANT_INTERACTIVE" = 1 ] && OUT_DESC="${OUT_DESC}（動く資料）"
[ "$DO_PDF" = 1 ] && OUT_DESC="$OUT_DESC ＋ PDF"
[ "$DO_PPTX" = 1 ] && OUT_DESC="$OUT_DESC ＋ PPTX"
say "出す物: $OUT_DESC"
# 今回選んでいない物が前回の出力として残っていたら知らせる（消さない＝誤って配らないよう名指しする）
for _f in "$PDF:$DO_PDF" "$PPTX:$DO_PPTX"; do
  _p="${_f%:*}"; _on="${_f##*:}"
  if [ "$_on" = 0 ] && [ -e "$_p" ]; then
    say "⚠ 今回は作らない物が前回の出力として残っています: $_p（配布物に含めない・不要なら削除）"
  fi
done

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
# 1行で持つ：macOS の awk は -v の値に改行があると「newline in string」で止まり、</head> のある
# 通常のデッキで注入が失敗していた（2026-09-30 実測）
PRINT_CSS='<style id="ci-finalize-print">@media print{@page{size:297mm 210mm;margin:0} .slide{page-break-after:always;break-after:page;box-shadow:none!important;margin:0!important} .slide:last-child{page-break-after:auto}}</style>'
INJECTED="$TMP/$STEM.html"
# </head> 直前に注入（無ければ先頭に付与）。同ディレクトリの相対アセットも解決できるよう元の隣に置く。
# 絶対パスにする：相対パス（例 deck.html）だと file://./.ci-finalize… になり、Chrome がエラーページを
# 1枚だけ PDF にしていた（2026-09-27 実測・10枚のデッキが1ページの PDF になった）
INJECTED="$(cd "$(dirname "$SRC")" && pwd)/.ci-finalize.$STEM.html"
if grep -qi '</head>' "$SRC"; then
  awk -v css="$PRINT_CSS" 'BEGIN{IGNORECASE=1} /<\/head>/ && !done{print css; done=1} {print}' "$SRC" > "$INJECTED"
else
  { printf '%s\n' "$PRINT_CSS"; cat "$SRC"; } > "$INJECTED"
fi
trap 'rm -rf "$TMP"; rm -f "$INJECTED"' EXIT
# 空白・日本語を含むパス（Drive の案件フォルダ等）でも開けるよう URL エンコードする
if command -v python3 >/dev/null 2>&1; then
  INJECTED_URL="file://$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$INJECTED")"
else
  INJECTED_URL="file://$INJECTED"
fi

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

# ---- ゲート: 図の無い本文ページ（既定で図を使う＝FIGURES_GUIDE.md 0章・v3.10） ----
FIGS_PY="$SELF_DIR/ci_figs.py"
if [ -f "$FIGS_PY" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ 図の無いページ検査（gate）"
  # set -e 下でパイプの失敗が即終了にならないよう、結果を変数に受けてから判定する
  COV_OUT="$(python3 "$FIGS_PY" coverage "$SRC" --strict 2>&1)" && COV_RC=0 || COV_RC=$?
  printf '%s\n' "$COV_OUT" | sed 's/^/  /'
  if [ "$COV_RC" -ne 0 ]; then
    if [ -n "$ALLOW_NOFIG" ]; then say "  ⚠ --allow-no-figs で通過（理由: ${ALLOW_NOFIG}）"
    else die "図の無い本文ページがあります（FIG?）。フレームワーク図・グラフかイラストを置くか、表だけで足りるページは section に data-fig-exempt=\"理由\" を付けてから再実行（FIGURES_GUIDE.md 0章）"; fi
  fi
fi

# ---- ゲート: CIトークン整合検査（廃止トークン --navy/--powder・旧hex・Georgia混入を検出） ----
if [ -f "$PARITY" ] && command -v python3 >/dev/null 2>&1; then
  say "▶ CIトークン整合検査（gate）"
  python3 "$PARITY" "$SRC" 2>&1 | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || die "CIトークン整合検査 NG（廃止トークン/旧hex/Georgia混入。上の行を修正してから再実行）"
fi

# ---- 1) HTML → PDF（フォントサブセット自動埋込・#static＝組み上がった最終状態で印刷） ----
if [ "$DO_PDF" = 1 ] || [ "$DO_PPTX" = 1 ]; then
  if [ "$DO_PDF" = 1 ]; then say "▶ HTML → PDF"
  else PDF="$TMP/$STEM.pdf"; say "▶ HTML → PDF（PPTX 用の一時ファイル・配布物に残さない）"; fi
  "$CHROME" --headless --disable-gpu --no-sandbox --no-pdf-header-footer \
    --print-to-pdf="$PDF" "$INJECTED_URL#static" >/dev/null 2>&1 \
    || die "PDF 生成に失敗（Chrome ヘッドレス）。"
  [ -s "$PDF" ] || die "PDF が空です: $PDF"
  if [ "$DO_PDF" = 1 ]; then say "  ✓ $PDF"; fi
fi

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
if [ "$WANT_INTERACTIVE" = 1 ]; then say "  HTML: ${SRC}（動く資料＝ブラウザで開いて使う・URL末尾 #static で静止版）"
else say "  HTML: $SRC"; fi
if [ "$DO_PDF" = 1 ]; then say "  PDF : $PDF"; fi
[ "$DO_PPTX" = 1 ] && [ -s "$PPTX" ] && say "  PPTX: $PPTX"
[ "$DO_OUTLINE" = 1 ] && [ -s "$PDF_OL" ] && say "  PDF(outlined): $PDF_OL"
say ""
if [ "$DO_PPTX" = 1 ]; then
  say "Google スライド化：上記 PPTX を共有ドライブへアップ → 右クリック→「Google スライドで開く」"
  say "  （Drive が自動変換。追加のレンダリングは不要＝PPTX と Slides を1ソースで両取り）"
fi
if [ "$DO_OPEN" = 1 ] && command -v open >/dev/null 2>&1; then
  if [ "$DO_PDF" = 1 ]; then open "$PDF" || true; else open "$SRC" || true; fi
fi
