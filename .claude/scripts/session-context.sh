#!/usr/bin/env bash
# session-context.sh: SessionStart hook で 10 ブロック構造の文脈を additionalContext に投入する。
#
# 注入するブロック（詳細：docs/active-context-template.md）:
#   ① 状態層 — memory/active-context.md（進行中タスク・直近の確定事項）
#   ② 辞書層 — profile/preferences.md / profile/resources.md（"今日のルール"）
#   ③ 学習層 — learnings/insights.md の見出し（過去事例の罠インデックス）
#   ④ 除外層 — destinations/visited/ ほか（既消化アイテム・ドメイン依存・任意）
#   ⑤ 未来層 — 任意（将来の予定・締切等）
#   ⑥ ツール可用性 — scripts/probe-tools.sh の実測表（op key / wrapper 疎通）
#   ⑦ サブエージェント規範 — docs/subagent-orchestration.md の「適用ルール」節
#   ⑧ 肥大化検知 — memory/learnings の行数・サイズ閾値超過警告（超過時のみ・memory-dream 誘導）
#   ⑨ CIスライドエンジン版 — 5co-CI-kit/VERSION の版番号・更新日を毎セッション自動アナウンス
#      （従来 CLIENT_CLAUDE_TEMPLATE.md がセッション起動時に手動で読ませていたものを決定論化）
#   ⑩ テンプレ未カスタマイズ検知 — CLAUDE.md / README.md の {{プレースホルダ}} 残置を検出
#      （bootstrap 後に置換されないまま運用される派生リポ対策・超過時のみ表示）
#   ⑪ テンプレ版 — .claude/.template-state.json（apply-template.sh が書く版マーカー）の
#      版番号・source SHA を毎セッション自動アナウンス。「適用済み」と「整合性確認済み」は
#      別物のため integrity は not checked と明示（検査 = apply-template.sh --verify）。
#      詳細 = docs/template-versioning.md
#
# 失敗時もセッション起動を妨げないため exit 0 で抜ける。

set -u

PROJ="${CLAUDE_PROJECT_DIR:-.}"
JST_NOW=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M (%a) JST')

# 記憶ファイル肥大化検知（⑧ブロック）の閾値。決定論のみ・LLM 呼び出しなし。
BLOAT_LINES=300
BLOAT_BYTES=24576

# ──────────────────────────────────────────────
# ① 状態層：active-context
#
#   担当者キー（SHORTNAME）の決定:
#     - env `ACTIVE_CONTEXT_USER` があればそれを使う（推奨。各自 .claude/settings.local.json
#       の env に設定。共有コンテナで $HOME が全員同じ環境でも個人を識別できる）
#     - 無ければ basename $HOME にフォールバック（後方互換）
#
#   優先順位（user-aware loading）:
#     1. memory/active-context/<SHORTNAME>.md があれば、それ 1 件だけ読む
#     2. なければ memory/active-context/ 配下の `_` で始まらない全 .md を concat（旧挙動）
#     3. それも空なら旧形式の単一ファイル memory/active-context.md にフォールバック
#
#   `_README.md` / `_template.md` 等の運用文書は常に除外。
# ──────────────────────────────────────────────
SHORTNAME="${ACTIVE_CONTEXT_USER:-$(basename "$HOME")}"
USER_CTX_FILE="$PROJ/memory/active-context/${SHORTNAME}.md"

STATE=""
LOAD_MODE=""

if [ -f "$USER_CTX_FILE" ]; then
  # 1. user-specific ファイルが存在
  STATE=$(cat "$USER_CTX_FILE")
  LOAD_MODE="per-user (${SHORTNAME}.md)"
elif [ -d "$PROJ/memory/active-context" ]; then
  # 2. ディレクトリはあるが該当ユーザのファイルが無い → 全件 concat（fallback）
  PER_PERSON=""
  for f in "$PROJ/memory/active-context"/*.md; do
    case "$(basename "$f")" in
      _*) ;;  # _README.md, _template.md 等は除外
      *)
        [ -f "$f" ] && PER_PERSON+=$'\n\n--- '"$(basename "$f")"$' ---\n'"$(cat "$f")"
        ;;
    esac
  done
  if [ -n "$PER_PERSON" ]; then
    STATE="⚠️ user-specific file 'memory/active-context/${SHORTNAME}.md' が無いため全員分を読み込み中。自分専用のファイルを作成してください（_README.md 参照）。${PER_PERSON}"
    LOAD_MODE="fallback-all (no ${SHORTNAME}.md)"
  fi
fi

# 3. それでも空なら旧形式の単一ファイルを試す
if [ -z "$STATE" ] && [ -f "$PROJ/memory/active-context.md" ]; then
  STATE=$(cat "$PROJ/memory/active-context.md")
  LOAD_MODE="legacy single file"
fi

[ -z "$STATE" ] && STATE="(no active-context found)"
[ -n "$LOAD_MODE" ] && STATE=$(printf '[loaded: %s]\n\n%s' "$LOAD_MODE" "$STATE")

# ──────────────────────────────────────────────
# ② 辞書層：プロファイル（好み・残高・期限）
# section 名は派生リポの実ファイルに合わせて書き換える
# ──────────────────────────────────────────────
PREFS=""
if [ -f "$PROJ/profile/preferences.md" ]; then
  # awk のレンジ /start/,/end/ は start と end が同一行でマッチすると 1 行で ON→OFF してしまう。
  # ## レベル見出し配下を ## レベル終端で切る場合、両方とも /^## / にマッチするため
  # 見出し行だけが抽出されて本文が落ちる。フラグ方式で修正。
  PREFS=$(awk '
    /^## (好み|判断基準|制約|要件|loyalty)/ {p=1; print; next}
    /^## / && p {p=0}
    p
  ' "$PROJ/profile/preferences.md" 2>/dev/null | head -120)
fi
[ -z "$PREFS" ] && PREFS="(no preferences extracted)"

RESOURCES=""
if [ -f "$PROJ/profile/resources.md" ]; then
  RESOURCES=$(awk '
    /^## (予算|残高|利用可能|inventory|期限)/ {p=1; print; next}
    /^## / && p {p=0}
    p
  ' "$PROJ/profile/resources.md" 2>/dev/null | head -200)
fi
[ -z "$RESOURCES" ] && RESOURCES="(no resources extracted)"

# ──────────────────────────────────────────────
# ③ 学習層：learnings の見出しインデックス
# 全文ではなく見出しのみで「該当する罠を覚えている」を Claude に判断させる
# ──────────────────────────────────────────────
LEARNINGS_INDEX=""
if [ -f "$PROJ/learnings/insights.md" ]; then
  LEARNINGS_INDEX=$(grep -h '^### ' "$PROJ/learnings/insights.md" 2>/dev/null | head -50)
fi
[ -z "$LEARNINGS_INDEX" ] && LEARNINGS_INDEX="(no learnings index)"

# ──────────────────────────────────────────────
# ④ 除外層：既消化アイテム（ドメイン依存・任意）
# パスは派生リポで適宜変更：destinations/visited/ / projects/done/ / books/read/ 等
# ──────────────────────────────────────────────
VISITED=""
for visited_dir in destinations/visited projects/done books/read episodes/resolved; do
  if [ -d "$PROJ/$visited_dir" ]; then
    VISITED+=$(cat "$PROJ/$visited_dir"/*.md 2>/dev/null | head -120)
  fi
done
[ -z "$VISITED" ] && VISITED="(no exclusion list configured)"

# ──────────────────────────────────────────────
# ⑦ サブエージェント運用ルール（正典: docs/subagent-orchestration.md）
# 「適用ルール」節のみ抽出注入（全文注入はトークン浪費のため避ける）。
# ファイルが無い派生リポでは黙ってスキップ。
# ──────────────────────────────────────────────
SUBAGENT_RULES=""
SUBAGENT_DOC="$PROJ/docs/subagent-orchestration.md"
if [ -f "$SUBAGENT_DOC" ]; then
  SUBAGENT_RULES=$(sed -n '/^## 適用ルール/,/^## [^適]/p' "$SUBAGENT_DOC" | sed '$d')
  [ -n "$SUBAGENT_RULES" ] && SUBAGENT_RULES+=$'\n\n（全文・3軸ランキング表・5co適用注意: docs/subagent-orchestration.md）'
fi
[ -z "$SUBAGENT_RULES" ] && SUBAGENT_RULES="(subagent rules doc not present)"

# ──────────────────────────────────────────────
# ⑥ ツール可用性層：実測されたツール疎通テーブル
# .claude/hooks/session-start-tool-probe.sh が 24h キャッシュ付きで stdout に出す
# ──────────────────────────────────────────────
TOOL_AVAILABILITY=""
TOOL_PROBE_HOOK="$PROJ/.claude/hooks/session-start-tool-probe.sh"
if [ -x "$TOOL_PROBE_HOOK" ]; then
  TOOL_AVAILABILITY=$(bash "$TOOL_PROBE_HOOK" 2>/dev/null || true)
fi
[ -z "$TOOL_AVAILABILITY" ] && TOOL_AVAILABILITY="(tool availability probe unavailable)"

# ──────────────────────────────────────────────
# ⑧ 記憶ファイル肥大化検知：決定論のみ・LLM 呼び出しなし
#   対象: **本スクリプトが SessionStart 注入に使うファイルだけ**（存在するもののみ）。
#     この警告の目的は「起動時コンテキストの肥大＝毎セッションのトークン消費」を止めること
#     なので、注入に一切使わないファイルを混ぜると警告の意味がぼやける。
#     ※ memory/decisions.md は①〜⑪のどのブロックでも注入していないため対象外
#       （参照性の観点での保守は必要になり得るが、起動コストの問題ではない）
#   既知の限界（sol 検品 2026-07-26・P2 として記録）:
#     判定はファイル全文の行数・バイト数で行うが、注入形態はファイルごとに違う。
#       - memory/active-context.md / profile/preferences.md … 全文注入（判定＝実コストと一致）
#       - profile/resources.md … awk 抽出のみ注入／learnings/insights.md … 見出しのみ注入
#     後者2つは本文が増えても注入量は比例しないため、判定は**代理指標**（過剰警告寄り）。
#     それでも対象に含めるのは、剪定する対象が抽出結果ではなくファイル本体であり、
#     閾値を全ファイルで揃えた方が運用が単純なため。抽出結果の実測に変えるなら
#     ①〜③で組み立てた変数（RESOURCES / LEARNINGS 等）を測る改修が別途必要。
#     ※ per-user 形式（memory/active-context/<name>.md）は対象外のまま
#       （decisions.md 2026-07-09 に既知の限界として記録済み）
#   閾値: 行数 $BLOAT_LINES 超 または サイズ $BLOAT_BYTES バイト超
#   超過ゼロなら MEMORY_BLOAT_LIST は空のまま → build_context で何も出力しない
# ──────────────────────────────────────────────
MEMORY_BLOAT_LIST=""
for bloat_file in memory/active-context.md profile/preferences.md profile/resources.md learnings/insights.md; do
  f="$PROJ/$bloat_file"
  if [ -f "$f" ]; then
    bloat_lines=$(wc -l < "$f")
    bloat_bytes=$(wc -c < "$f")
    if [ "$bloat_lines" -gt "$BLOAT_LINES" ] || [ "$bloat_bytes" -gt "$BLOAT_BYTES" ]; then
      bloat_kb=$(( (bloat_bytes + 1023) / 1024 ))
      MEMORY_BLOAT_LIST+="- ${bloat_file} (${bloat_lines}行 / ${bloat_kb}KB)"$'\n'
    fi
  fi
done

# ──────────────────────────────────────────────
# ⑨ CIスライドエンジン版：5co-CI-kit/VERSION の版番号・更新日を毎セッション自動アナウンス
#   正データ源＝本ファイルの1行目（vX.Y）と `date:` 行。派生リポでは sync-template 経由の
#   コピーを同一相対パスで参照する。ファイルが無いリポ（CI と無関係な派生リポ）は
#   「CI kit未導入」と明記する（他ブロックと同様、常に表示しノイズは増やさない）。
# ──────────────────────────────────────────────
CI_VERSION_FILE="$PROJ/5co-CI-kit/VERSION"
CI_VERSION_ANNOUNCE=""
if [ -f "$CI_VERSION_FILE" ]; then
  ci_ver=$(head -1 "$CI_VERSION_FILE")
  ci_date=$(grep '^date:' "$CI_VERSION_FILE" 2>/dev/null | head -1 | sed 's/^date:[[:space:]]*//')
  if [ -n "$ci_ver" ]; then
    CI_VERSION_ANNOUNCE="CIスライドエンジン: ${ci_ver}${ci_date:+（${ci_date}）}"
  fi
fi
[ -z "$CI_VERSION_ANNOUNCE" ] && CI_VERSION_ANNOUNCE="(5co-CI-kit未導入のリポジトリ)"

# 鮮度ハートビート（層2）: Drive 作業場では sync-ci-kit-drive.sh が本番同期の完走ごとに
# _sync_heartbeat.txt を書く。7日以上更新が無ければ「配送インフラが止まっている」疑い
# （2026-07-10 の cron 空振り事故の再発検知）。git リポにはこのファイルは無い＝黙ってスキップ。
CI_HEARTBEAT_FILE="$PROJ/5co-CI-kit/_sync_heartbeat.txt"
CI_STALE_DAYS=7
if [ -f "$CI_HEARTBEAT_FILE" ]; then
  # mtime取得の可搬性: GNU stat は -c %Y、BSD/macOS は -f %m。GNU に -f を先に渡すと
  # 「ファイルシステム情報」として成功してしまう（複数行のゴミが返る）ため -c を先に試す。
  hb_epoch=$(stat -c %Y "$CI_HEARTBEAT_FILE" 2>/dev/null || stat -f %m "$CI_HEARTBEAT_FILE" 2>/dev/null || echo 0)
  case "$hb_epoch" in *[!0-9]*) hb_epoch=0 ;; esac   # 数値以外が混じったら安全側で無効化
  if [ "$hb_epoch" -gt 0 ]; then
    hb_days=$(( ($(date +%s) - hb_epoch) / 86400 ))
    if [ "$hb_days" -gt "$CI_STALE_DAYS" ]; then
      CI_VERSION_ANNOUNCE+=$'\n'"⚠ Drive 同期の最終実行から ${hb_days} 日経過（_sync_heartbeat.txt）。kit が古い可能性があります。ユーザーへの冒頭報告で「フォーマットが古い可能性」を一度だけ伝え、管理者に drive-canonical-refresh の稼働確認を依頼するよう案内してください。"
    else
      CI_VERSION_ANNOUNCE+=$'\n'"最終同期: ${hb_days} 日前（_sync_heartbeat.txt・正常）"
    fi
  fi
fi

# ──────────────────────────────────────────────
# ⑩ テンプレ未カスタマイズ検知：{{プレースホルダ}} 残置の警告
#   対象: CLAUDE.md / README.md（template 由来の {{...}} が残っていれば未 adopt とみなす）
#   template リポ自身（origin が 5co-hub/template）ではプレースホルダが正であるため黙ってスキップ
# ──────────────────────────────────────────────
PLACEHOLDER_WARN=""
origin_url=$(git -C "$PROJ" remote get-url origin 2>/dev/null || true)
case "$origin_url" in
  *5co-hub/template*|*5co-hub/template.git*) : ;;  # template 本体では警告しない
  *)
    for ph_file in CLAUDE.md README.md; do
      f="$PROJ/$ph_file"
      if [ -f "$f" ] && grep -qE '\{\{[^}]+\}\}' "$f" 2>/dev/null; then
        ph_sample=$(grep -oE '\{\{[^}]+\}\}' "$f" | sort -u | head -3 | tr '\n' ' ')
        PLACEHOLDER_WARN+="- ${ph_file}: ${ph_sample}"$'\n'
      fi
    done
    ;;
esac

# ──────────────────────────────────────────────
# ⑪ テンプレ版：.claude/.template-state.json の版番号・source SHA をアナウンス
#   マーカーは決定的値のみ（適用日時なし）。integrity は毎起動で検査しない（起動コスト回避）ため
#   「not checked」と明示する＝「適用済み」を「改変なし」と誤読させない。
#   マーカーが無い展開先は legacy 扱いとし、ファイル有無から版を推定しない。
#   ※ マーカーはデータとして sed 抽出のみ（eval / source 禁止＝改変マーカーによる注入防止）
# ──────────────────────────────────────────────
TEMPLATE_STATE_FILE="$PROJ/.claude/.template-state.json"
TEMPLATE_VERSION_ANNOUNCE=""
# マーカー値は形式検証を通ったものだけ表示する（CalVer / 40hex SHA）。
# 改変マーカー経由の制御文字・長大文字列・指示文の注入をコンテキストに通さない（fail-closed）。
TPL_VER_RE='^[0-9]{4}\.[0-9]{2}\.[0-9]+$'
TPL_SRC_RE='^([0-9a-f]{40}(-dirty)?|unknown)$'
if [ -f "$TEMPLATE_STATE_FILE" ]; then
  tpl_ver=$(sed -n 's/^  "template_version": "\(.*\)",\{0,1\}$/\1/p' "$TEMPLATE_STATE_FILE" | head -1)
  tpl_src=$(sed -n 's/^  "source_revision": "\(.*\)",\{0,1\}$/\1/p' "$TEMPLATE_STATE_FILE" | head -1)
  if printf '%s' "$tpl_ver" | grep -qE "$TPL_VER_RE" && printf '%s' "$tpl_src" | grep -qE "$TPL_SRC_RE"; then
    TEMPLATE_VERSION_ANNOUNCE="テンプレ版: ${tpl_ver}（source: ${tpl_src:0:12}・integrity: not checked）"
    TEMPLATE_VERSION_ANNOUNCE+=$'\n'"capability一覧 = template-manifest.json／整合性検査 = template側で apply-template.sh <このdir> --verify"
  else
    TEMPLATE_VERSION_ANNOUNCE="⚠ 版マーカーが形式不正（改変・破損の可能性。値は表示しない）。apply-template.sh --repair で再生成を"
  fi
elif [ -f "$PROJ/template-manifest.json" ] && git -C "$PROJ" remote get-url origin 2>/dev/null | grep -qE '[:/]5co-hub/template(\.git)?$'; then
  tpl_ver=$(sed -n 's/^  "template_version": "\(.*\)",\{0,1\}$/\1/p' "$PROJ/template-manifest.json" | head -1)
  printf '%s' "$tpl_ver" | grep -qE "$TPL_VER_RE" || tpl_ver="unknown"
  TEMPLATE_VERSION_ANNOUNCE="テンプレ版: ${tpl_ver}（正本リポ 5co-hub/template — マーカーなしが正）"
else
  TEMPLATE_VERSION_ANNOUNCE="(版マーカーなし＝バージョン管理導入前の展開 = legacy。版をファイル有無から推定しないこと。apply-template.sh --repair で導入)"
fi
if [ -f "$PROJ/.claude/.sync-disabled" ]; then
  TEMPLATE_VERSION_ANNOUNCE+=$'\n'"sync: disabled（.claude/.sync-disabled = 自動同期 opt-out。最新版とは限らない）"
fi

# ──────────────────────────────────────────────
# JSON 出力（jq が無い環境でも heredoc で対応）
# ──────────────────────────────────────────────
build_context() {
  printf '=== Current JST Time ===\n%s\n\n' "$JST_NOW"
  printf '=== Active Context (state) ===\n%s\n\n' "$STATE"
  printf '=== Profile Preferences (must-haves) ===\n%s\n\n' "$PREFS"
  printf '=== Resources Inventory ===\n%s\n\n' "$RESOURCES"
  printf '=== Learnings Index (見出し) ===\n%s\n\n' "$LEARNINGS_INDEX"
  printf '=== Visited / Done (除外リスト) ===\n%s\n\n' "$VISITED"
  printf '=== Subagent Model Rules (適用ルール) ===\n%s\n\n' "$SUBAGENT_RULES"
  printf '=== Tool Availability (実測) ===\n%s\n' "$TOOL_AVAILABILITY"
  printf '\n\n=== CI Slide Engine Version (5co-CI-kit) ===\n%s\n' "$CI_VERSION_ANNOUNCE"
  printf '\n=== Template Version (template-manifest) ===\n%s\n' "$TEMPLATE_VERSION_ANNOUNCE"
  if [ -n "$MEMORY_BLOAT_LIST" ]; then
    printf '\n\n=== Memory Bloat Check (肥大化検知) ===\n'
    printf '⚠ 以下の記憶ファイルが閾値（%s行 or %sKB）を超えています:\n' "$BLOAT_LINES" "$((BLOAT_BYTES / 1024))"
    printf '%s' "$MEMORY_BLOAT_LIST"
    printf 'これらは SessionStart 注入に使われるため、超過分は起動時のトークン消費とノイズになります。\n'
    printf '（active-context / preferences は全文注入。resources は抽出のみ・insights は見出しのみ注入のため、\n'
    printf ' 行数・バイト数は実注入量の代理指標です。詳細と剪定の考え方は下記の手順書に記載。）\n'
    printf '手順書 = .claude/skills/memory-dream.md（対象ファイル・保存先の判断基準・完了条件を規定）。\n'
    printf '会話の流れ上そぐわない場合を除き、ユーザーに剪定を提案してください\n'
    printf '（提案文例: 「記憶ファイルが閾値を超えています。memory-dream の手順で剪定PRを起案しますか？」）。\n'
    printf 'この警告は閾値を下回るまで毎セッション出ます（フックは状態を持たないため抑止できません）。\n'
    printf '直近で提案済み・見送り済みなら、再提案は控えて作業を進めて構いません。\n'
    printf '承認されたら手順書に従い、剪定結果は必ず PR としてレビュー可能な形で出すこと（直接 main へ反映しない）。\n'
    printf '※ 剪定は不可逆な削除を含むため、PR の適用（マージ）にはユーザーの承認が必要です。\n'
  fi
  if [ -n "$PLACEHOLDER_WARN" ]; then
    printf '\n\n=== Template Placeholder Check (未カスタマイズ検知) ===\n'
    printf '⚠ template 由来の {{プレースホルダ}} が置換されないまま残っています:\n'
    printf '%s' "$PLACEHOLDER_WARN"
    printf 'このリポは bootstrap 後のカスタマイズ（README「セットアップ」手順 2-4）が未完了の可能性があります。\n'
    printf 'ユーザーに一度だけ提案してください:「CLAUDE.md/README.md にテンプレのプレースホルダが残っています。このリポの用途に合わせて置換・不要ルールの削ぎ落としを行いますか？」\n'
  fi
}

CTX=$(build_context)

if command -v jq >/dev/null 2>&1; then
  jq -n \
    --arg ctx "$CTX" \
    '{
      hookSpecificOutput: {
        hookEventName: "SessionStart",
        additionalContext: $ctx
      }
    }'
else
  # heredoc fallback: " と \ を最低限エスケープ
  esc_ctx=$(printf '%s' "$CTX" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr '\n' '\f' | sed 's/\f/\\n/g')
  cat <<JSON
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"${esc_ctx}"}}
JSON
fi

exit 0
