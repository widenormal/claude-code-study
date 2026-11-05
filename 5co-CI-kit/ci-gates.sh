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
#   ci-gates.sh --figs <figs_dir> <deck>
#                                  … 図・イラストの断片（figs/）の検品も走らせる（v3.10）
#   ci-gates.sh --source <原文> <deck>
#                                  … LLM が書き直した版（やさしい版・英語版）の検品も走らせる
#   ci-gates.sh --serp <deck>      … Amazon検索順位の根拠ページ（SERP）の検品も必ず走らせる（v3.14.0）
#                                    デッキに data-serp-page があればオプション無しでも走る。
#                                    SERP_SHOT? は警告・出所/郵便番号/外部画像/仕入れ先名の違反は落とす。
#                                    --serp と言ったのに data-serp-page のページが1枚も無いときは
#                                    「SERP_SHOT? 対象ゼロ」を警告で出す（黙って通さない・v3.14.1）。
#                                    --strict と併せたときだけ落とす（--serp --strict）
#   ci-gates.sh --ban-shelpha <deck>
#                                  … この案件だけ「Shelpha」も当社NG語として落とす（v3.14.2）。
#                                    既定は書いてよい（出典欄・フッター版スタック・若松さん決定 2026-11-03）。
#                                    付けるときは組み立ても ci_head.py --no-shelpha と対にする
#   ci-gates.sh --cutouts <alpha_dir> <deck>
#                                  … 切り抜き人物 PNG の白フチ検品をフォルダ単位でも走らせる（2026-10-30）
#                                    フォルダは縮小判定 --resize 1152,813,406,284,142 込み（CI_HALO_RESIZE で変更・空で無効）
#                                    さらに背景色の取り残し [D] bgres（--bg-residue）を警告のみで回す（2026-10-30・
#                                    --strict でも落とさない。CI_HALO_BGRES=0 で省略・縮小幅は CI_HALO_BGRES_RESIZE）
#   ci-gates.sh --json <deck>      … 各検査の --json 出力を1つの JSON 文書にまとめて stdout へ（v3.12.6）
#                                    テキスト表示は出さない。終了コードは通常と同じ（0=OK／1=NG／2=引数誤り）
#                                    スキーマ＝ci_gates_json.py。--json を持たない検査は表示文を "text" に入れる
#
# 検査（VERSION の gates 行が正）
#   1. slide_overflow_check.py   … あふれ            （落とす）
#   2. check_text_overlap.py     … 要素の重なり      （落とす）
#   3. graph_node_edge_check.py  … ノード・エッジ図   （.ne-graph があるときだけ・落とす）
#   4. svg_label_check.py        … SVG図版のラベル   （既定は警告・--strict で落とす）
#   5. llm_output_check.py       … LLM出力の破損     （--source を渡したときだけ・落とす）
#   6. ci_figs.py coverage       … 図の無い本文ページ（FIG?・既定で図を使う＝FIGURES_GUIDE.md 0章／警告）
#   7. ci_figs.py lint           … 図・イラストの断片（--figs <dir> を渡したときだけ・落とす）
#   8. footer_stack_check.py     … フッター版スタック（ci_head 経由なら必須・既定は警告）
#   9. product_image_check.py    … 商品名・ASIN に商品画像（PRODUCT_IMG?・既定は警告・FIGURES_GUIDE 2-1）
#  10. check_fixed_overlap.py    … 固定要素（コーナーロゴ・フッター・頁番号）× 本文／色面／画像（落とす・v3.12）
#  10b. check_content_overlap.py … 本文の見える要素どうし（SVG 内の図形・写真・色面）の重なり／COL-OVERFLOW（警告のみ・v3.17.2）
#                                  static/screen/digest × 7 ビューポート。CI_FIXED_OVERLAP_VIEWPORTS で絞れる
#  11. check_text_overlap.py --digest-mode
#                                … ダイジェスト見た目の重なり（data-digest-keep="hero" がある頁だけ・落とす・v3.12）
#  12. cutout_halo_check.py      … 切り抜き PNG の白フチ（HALO?・デッキ内の透過 PNG／--cutouts のフォルダ・
#                                  既定は警告・--strict で落とす・2026-10-30）
#                                  デッキ内の画像は縮小判定なし（ロゴの縁が縮小で誤検知するため。CI_HALO_DECK_RESIZE=1152,… で有効）
#  13. cutout_halo_check.py --bg-residue
#                                … 背景色の取り残し（bgres・--cutouts のフォルダだけ・元写真は <alpha の親>/../src/・
#                                  当面は警告のみ・2026-10-30。人物素材 facing_* の納品前は単体で必須＝FIGURES_GUIDE §2-2）
#  14. cover_motion.py --lint     … 表紙・中扉にモーションが無い（COVER_MOTION?・警告のみ・v3.12.6）
#      boid/boid_motion.py --lint … 同じく Boid 版（BOID_MOTION?・data-boid-mode があるデッキだけ・
#                                  警告のみ・2026-11-04 試作）
#      depth/depth_motion.py --lint … 奥行きの層版（DEPTH_MOTION?・data-cm-engine="depth" があるデッキだけ・
#                                  警告のみ・2026-11-05 試作）
#  15. layout_run_check.py       … 組み方の偏り（LAYOUT_RUN?＝同じ主役の種類が3ページ以上続く／ELEMS?＝要素6つ以上・
#                                  警告のみ・v3.13。正＝V3.2_FORMAT.md「発表版」）
#  16. vocab_check.py            … 語彙帳の「当社で使わない」表記（VOCAB?・当社NG語は落とす／表記ゆれは警告・
#                                  --strict では表記ゆれも落とす・v3.13.3。正＝vocab/README.md）
#                                  仕入れ先名（DMT・Acorn-i・Ignite・AMZ-POS と言い換え）は
#                                  HTML 全文＝<style>・<script>・HTML/CSS/JS のコメント・属性まで見て落とす
#                                  （v3.14.1・若松さん決定 2026-11-02。社内資料だけ --allow-vendor で外せる）。
#                                  「Shelpha」は書いてよい（2026-11-03・v3.14.2）＝伏せる案件だけ --ban-shelpha
#  17. serp/serp_check.py        … Amazon検索順位の根拠ページ（SERP_SHOT?・data-serp-page があるページだけ・
#                                  v3.14.0）。出所は「出所：Amazon.co.jp検索結果（取得日時・条件）」だけ＝
#                                  事業者名・推計の手口・郵便番号・外部画像は落とす。正＝FIGURES_GUIDE.md 2-4
#                                  仕入れ先名は HTML 全文（フッター・<style>・<script>・コメント・属性）を
#                                  見て落とす（SERP_VENDOR・v3.14.1。data: の画像本体だけ見ない）。
#                                  「Shelpha」は既定で通す（出所の行だけは Amazon.co.jp検索結果 のまま・v3.14.2）
set -uo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HALO_RESIZE="${CI_HALO_RESIZE-1152,813,406,284,142}"   # --cutouts フォルダの縮小判定（サイトの srcset 幅）
HALO_DECK_RESIZE="${CI_HALO_DECK_RESIZE-}"             # デッキ内画像の縮小判定（既定なし）
HALO_BGRES="${CI_HALO_BGRES-1}"                          # --cutouts で bgres も回す（0 で省略・当面は警告のみ）
HALO_BGRES_RESIZE="${CI_HALO_BGRES_RESIZE-$HALO_RESIZE}" # bgres の縮小判定（既定は CI_HALO_RESIZE と同じ）

V=0; STRICT=0; JSON=0; SERP=0; BAN_SHELPHA=(); SOURCE=""; FIGS=""; CUTOUTS=""; FILES=()
while [ $# -gt 0 ]; do case "$1" in
  -v|--verbose) V=1;;
  --strict) STRICT=1;;
  --json) JSON=1;;                     # 1つの JSON 文書にまとめて出す（v3.12.6）
  --serp) SERP=1;;                     # 検索順位の根拠ページの検品を必ず走らせる（v3.14.0）
  --ban-shelpha) BAN_SHELPHA=(--ban-shelpha);;  # この案件は「Shelpha」も伏せる（既定は書いてよい・v3.14.2）
  --source) SOURCE="${2:-}"; shift;;   # LLM が書き直した版の原文（llm_output_check.py へ渡す）
  --figs) FIGS="${2:-}"; shift;;       # 図・イラストの断片ディレクトリ（ci_figs.py lint）
  --cutouts) CUTOUTS="${2:-}"; shift;; # 切り抜き人物 PNG のフォルダ（cutout_halo_check.py）
  -h|--help) sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 0;;
  *) FILES+=("$1");;
esac; shift; done
[ ${#FILES[@]} -gt 0 ] || { echo "❌ 入力 HTML を指定してください: ci-gates.sh <deck.html>" >&2; exit 2; }

# --json: テキスト表示は捨て（本来の stdout は fd 3 に退避）、検査ごとの結果を JSON Lines で $JREC に溜める
JREC=""; CUR=""
if [ $JSON -eq 1 ]; then
  JREC="$(mktemp)"; trap 'rm -f "$JREC"' EXIT
  exec 3>&1 1>/dev/null
fi
jrec() {  # jrec <対象> <ラベル> <検査> <落とすか> <rc> <status> <出力> <JSONあり(1/0)>
  [ $JSON -eq 1 ] || return 0
  printf '%s' "$7" | python3 "$SELF_DIR/ci_gates_json.py" rec "$1" "$2" "$3" "$4" "$5" "$6" "$8" >>"$JREC"
}

FAIL=0
gate() {  # gate <ラベル> <スクリプト> <html> <落とすか(1/0)> [追加引数…]
  local label="$1" script="$2" html="$3" hard="$4"; shift 4
  [ -f "$script" ] || { printf '  – %-18s (スクリプト無し)\n' "$label"; jrec "$CUR" "$label" "$(basename "$script")" "$hard" 0 skip "スクリプト無し" 0; return 0; }
  local out rc hj=0 st
  # --json のときは --json を持つ検査にだけ --json を渡す（持たない検査は表示文を "text" に入れる）
  if [ $JSON -eq 1 ] && grep -q -- '--json' "$script"; then hj=1; set -- "$@" --json; fi
  out="$(python3 "$script" "$html" "$@" 2>&1)"; rc=$?
  # --warn-only は所見があっても終了コード0で返るため、本文が「: OK」で終わるかで判定する
  # （--json で走らせたときは各レコードの "ok" で判定する）
  if [ $hj -eq 1 ]; then
    printf '%s\n' "$out" | python3 "$SELF_DIR/ci_gates_json.py" ok && st=ok || st=warn
  elif printf '%s' "$out" | tail -1 | grep -q ': *OK$'; then st=ok; else st=warn; fi
  if [ $rc -eq 0 ] && [ "$st" = ok ]; then
    printf '  ✔ %-18s OK\n' "$label"
  elif [ $rc -eq 0 ]; then
    st=warn; printf '  ⚠ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /' 
  elif [ "$hard" = "1" ]; then
    st=fail; FAIL=1; printf '  ✘ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /'
  else
    st=warn; printf '  ⚠ %-18s\n' "$label"; printf '%s\n' "$out" | tr '|' '\n' | sed 's/^/      /'
  fi
  [ $V -eq 1 ] && printf '%s\n' "$out" | sed 's/^/      /'
  jrec "$CUR" "$label" "$(basename "$script")" "$hard" "$rc" "$st" "$out" "$hj"
  return 0
}

for f in "${FILES[@]}"; do
  CUR="$f"
  [ -f "$f" ] || { echo "❌ ファイルが見つかりません: $f" >&2; FAIL=1; jrec "$f" "入力" "-" 1 2 fail "ファイルが見つかりません" 0; continue; }
  echo "▶ $(basename "$f")"
  gate "あふれ"        "$SELF_DIR/slide_overflow_check.py" "$f" 1
  gate "要素の重なり"  "$SELF_DIR/check_text_overlap.py"   "$f" 1
  gate "固定要素の重なり" "$SELF_DIR/check_fixed_overlap.py" "$f" 1
  # 本文の見える要素どうし（SVG 内の図形×写真など）の重なり・列からのはみ出し（v3.17.2・まず警告のみ）
  gate "本文の重なり" "$SELF_DIR/check_content_overlap.py" "$f" 0 --warn-only
  grep -q 'data-digest-keep="hero"' "$f" && gate "重なり(ダイジェスト)" "$SELF_DIR/check_text_overlap.py" "$f" 1 --digest-mode
  grep -q 'ne-graph' "$f" && gate "ノード・エッジ図" "$SELF_DIR/graph_node_edge_check.py" "$f" 1
  if [ $STRICT -eq 1 ]; then gate "SVGラベル" "$SELF_DIR/svg_label_check.py" "$f" 1
  else                       gate "SVGラベル" "$SELF_DIR/svg_label_check.py" "$f" 0 --warn-only; fi
  if [ -n "$SOURCE" ]; then
    if [ -f "$SOURCE" ]; then gate "LLM出力の検品" "$SELF_DIR/llm_output_check.py" "$f" 1 --source "$SOURCE"
    else echo "  ✘ LLM出力の検品     原文が見つかりません: $SOURCE"; FAIL=1; fi
  fi
  # フッター版スタック（ci_head 経由デッキは必須・旧デッキは警告のみ）
  gate "版スタック"     "$SELF_DIR/footer_stack_check.py" "$f" 0 --warn-only
  # 商品名・ASIN の商品画像（FIGURES_GUIDE 2-1・警告のみ）
  gate "商品画像"       "$SELF_DIR/product_image_check.py" "$f" 0 --warn-only
  # 人物写真のキャプション・alt に「イメージ写真」と書かない（COPY_GUIDE ルール11・警告のみ）
  gate "写真のキャプション" "$SELF_DIR/photo_caption_check.py" "$f" 0 --warn-only
  # Amazon検索順位の根拠ページ（SERP_SHOT?・FIGURES_GUIDE 2-4・v3.14.0）
  # 警告は警告のまま、出所ルール・郵便番号・外部画像の違反は落とす（--warn-only でも rc=1 で返る）
  if grep -q 'data-serp-page' "$f"; then
    gate "検索順位の根拠" "$SELF_DIR/serp/serp_check.py" "$f" 1 --warn-only "${BAN_SHELPHA[@]}"
  elif [ $SERP -eq 1 ]; then
    # --serp と言われたのに対象ページが無い（マーカーの付け忘れ・組み立て失敗）。黙って通さない（v3.14.1）
    ZMSG="SERP_SHOT? 対象ゼロ: data-serp-page のページがありません"
    if [ $STRICT -eq 1 ]; then
      FAIL=1; printf '  ✘ %-18s\n' "検索順位の根拠"; printf '      %s\n' "$ZMSG"
      jrec "$f" "検索順位の根拠" "serp_check.py" 1 1 fail "$ZMSG" 0
    else
      printf '  ⚠ %-18s\n' "検索順位の根拠"; printf '      %s\n' "$ZMSG"
      jrec "$f" "検索順位の根拠" "serp_check.py" 0 0 warn "$ZMSG" 0
    fi
  fi
  # 語彙帳の「当社で使わない」表記（VOCAB?・当社NG語は落とす／表記ゆれは警告・v3.13.3・vocab/README.md）
  # 仕入れ先名は HTML 全文（<style>・<script>・コメント含む）を見て落とす（v3.14.1・社内資料は --allow-vendor）
  # 「Shelpha」は既定で通す（v3.14.2）＝伏せる案件だけ --ban-shelpha で落とす
  if [ $STRICT -eq 1 ]; then gate "語彙帳" "$SELF_DIR/vocab_check.py" "$f" 1 --fail-on all "${BAN_SHELPHA[@]}"
  else                       gate "語彙帳" "$SELF_DIR/vocab_check.py" "$f" 1 --fail-on ng "${BAN_SHELPHA[@]}"; fi
  # 切り抜き PNG の白フチ（髪の毛先に元の白が残る・既定は警告・--strict で落とす）
  if [ $STRICT -eq 1 ]; then gate "切り抜き白フチ" "$SELF_DIR/cutout_halo_check.py" "$f" 1 --resize "$HALO_DECK_RESIZE"
  else                       gate "切り抜き白フチ" "$SELF_DIR/cutout_halo_check.py" "$f" 0 --warn-only --resize "$HALO_DECK_RESIZE"; fi
  # 表紙・中扉のモーション漏れ（COVER_MOTION?・警告のみ・v3.12.6）
  gate "表紙モーション"  "$SELF_DIR/cover_motion/cover_motion.py" --lint 0 "$f"
  # Boid 版の数字背景（BOID_MOTION?・警告のみ・2026-11-04 試作）。canvas を使うデッキだけ見る
  # 奥行きの層（depth）版（DEPTH_MOTION?・警告のみ・2026-11-05 試作）。depth の canvas を使うデッキは depth だけ見る
  if grep -q 'data-cm-engine="depth"' "$f"; then
    gate "表紙モーション(depth)" "$SELF_DIR/cover_motion/depth/depth_motion.py" --lint 0 "$f"
  else
    grep -q 'data-boid-mode' "$f" && gate "表紙モーション(Boid)" "$SELF_DIR/cover_motion/boid/boid_motion.py" --lint 0 "$f"
  fi
  # 組み方の偏り（LAYOUT_RUN?・ELEMS?・警告のみ・v3.13）
  gate "組み方の偏り"    "$SELF_DIR/layout_run_check.py" "$f" 0 --warn-only
  cov="$(python3 "$SELF_DIR/ci_figs.py" coverage "$f" 2>&1)"; crc=$?
  if printf '%s' "$cov" | grep -q 'FIG?'; then
    printf '  ⚠ %-18s\n' "図の無いページ"; printf '%s\n' "$cov" | sed 's/^/      /'
    jrec "$f" "図の無いページ" "ci_figs.py coverage" 0 "$crc" warn "$cov" 0
  else printf '  ✔ %-18s OK\n' "図の無いページ"; jrec "$f" "図の無いページ" "ci_figs.py coverage" 0 "$crc" ok "$cov" 0; fi
  N=$(grep -c '<section class="slide' "$f")
  printf '  %sスライド %s枚\n' "" "$N"
  jrec "$f" "スライド枚数" "-" 0 0 info "$N" 0
done

CUR=""
if [ -n "$FIGS" ]; then
  echo "▶ figs: $FIGS"
  if [ -d "$FIGS" ]; then
    out="$(python3 "$SELF_DIR/ci_figs.py" lint "$FIGS" 2>&1)"; rc=$?
    if [ $rc -eq 0 ]; then printf '  ✔ %-18s %s\n' "図・イラスト" "$(printf '%s' "$out" | tail -1)"; jrec "figs:$FIGS" "図・イラスト" "ci_figs.py lint" 1 "$rc" ok "$out" 0
    else FAIL=1; printf '  ✘ %-18s\n' "図・イラスト"; printf '%s\n' "$out" | grep '^NG' | sed 's/^/      /'; jrec "figs:$FIGS" "図・イラスト" "ci_figs.py lint" 1 "$rc" fail "$out" 0; fi
    [ $V -eq 1 ] && printf '%s\n' "$out" | sed 's/^/      /'
  else echo "  ✘ 図・イラスト       ディレクトリが見つかりません: $FIGS"; FAIL=1; jrec "figs:$FIGS" "図・イラスト" "ci_figs.py lint" 1 2 fail "ディレクトリが見つかりません" 0; fi
fi

if [ -n "$CUTOUTS" ]; then
  CUR="cutouts:$CUTOUTS"
  echo "▶ cutouts: $CUTOUTS"
  if [ -d "$CUTOUTS" ]; then
    if [ $STRICT -eq 1 ]; then gate "切り抜き白フチ" "$SELF_DIR/cutout_halo_check.py" "$CUTOUTS" 1 --resize "$HALO_RESIZE"
    else                       gate "切り抜き白フチ" "$SELF_DIR/cutout_halo_check.py" "$CUTOUTS" 0 --warn-only --resize "$HALO_RESIZE"; fi
    # 背景色の取り残し（bgres）: 偽陽性がシーン素材で出るため当面は警告のみ（--strict でも落とさない・2026-10-30）
    if [ "$HALO_BGRES" != "0" ]; then
      gate "背景色の取り残し" "$SELF_DIR/cutout_halo_check.py" "$CUTOUTS" 0 --warn-only --resize "$HALO_BGRES_RESIZE" --bg-residue
    fi
  else echo "  ✘ 切り抜き白フチ     ディレクトリが見つかりません: $CUTOUTS"; FAIL=1; jrec "$CUR" "切り抜き白フチ" "cutout_halo_check.py" 1 2 fail "ディレクトリが見つかりません" 0; fi
fi

[ $FAIL -eq 0 ] && echo "✅ ゲートOK" || echo "❌ ゲートNG（上を参照）"
[ $JSON -eq 1 ] && python3 "$SELF_DIR/ci_gates_json.py" merge "$JREC" "$FAIL" "$STRICT" "$SELF_DIR" >&3
exit $FAIL
