#!/bin/bash
# Claude Code SessionStart フック
# Ollama と Qwen モデルを自動セットアップする。マルチLLMオーケストレーションのうち
# 「ローカル無料の手足（Qwen）」を確実に動作可能にしておく。
#
# 動作（すべて best effort、失敗しても exit 0）:
#   0. qwen ルートを使う設定か判定。使わないなら何も起動せず抜ける
#   1. ollama CLI 未インストールなら導入（Linux: curl, macOS: brew）
#   2. Ollama サーバ未起動ならバックグラウンド起動
#   3. QWEN_MODEL（既定 qwen3.5:7b-instruct）未取得なら pull（バックグラウンド）
#   4. ECO_MODE 状態を表示

set -u

log() { printf '[multi-llm-setup] %s\n' "$*" >&2; }

QWEN_MODEL="${QWEN_MODEL:-qwen3.5:7b-instruct}"
OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
SETUP_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/claude-template-setup"
OLLAMA_MARKER="$SETUP_CACHE_DIR/ollama-installed.ok"
mkdir -p "$SETUP_CACHE_DIR" 2>/dev/null || true

# --- 0. 起動要否の判定（2026-08-13 追加）---
# qwen ルートに処理が流れるのは ECO_MODE=1 / DRIVE_CONTEXT=1 のときだけ
# （分岐の実体 = scripts/llm-router.sh。scripts/qwen-call.sh はサーバを自動起動しない）。
# それ以外で ollama serve を起こすと、一度も使われないまま常駐し続ける
# ——本番 Mac mini で 18 日間・CPU 11 分の常駐を実測（2026-08-13 の残留プロセス調査）。
# 常駐させたい運用なら .claude/settings.local.json の env に ECO_MODE=1 を置く。
if [ "${ECO_MODE:-0}" != "1" ] && [ "${DRIVE_CONTEXT:-0}" != "1" ]; then
  log "ECO_MODE=0 / DRIVE_CONTEXT=0 のため ollama の自動起動をスキップ（qwen ルート未使用）"
  log "qwen を使うときは ECO_MODE=1 を設定するか、手動で 'ollama serve' を起動してください"
  log "Drive 共有フォルダ操作時は eco-mode-drive.sh が自動誘導"
  exit 0
fi

# キャッシュマーカーが ollama 実体と整合していれば version 起動を省略する。
ollama_marker_valid() {
  [ -f "$OLLAMA_MARKER" ] || return 1
  local bin
  bin="$(command -v ollama 2>/dev/null)" || return 1
  [ -e "$bin" ] || return 1
  [ "$bin" -nt "$OLLAMA_MARKER" ] && return 1
  return 0
}

# --- 1. ollama CLI ---
if ! command -v ollama >/dev/null 2>&1; then
  log "ollama 未検出。インストールを試行..."
  case "$(uname -s)" in
    Linux)
      if curl -fsSL https://ollama.com/install.sh -o /tmp/ollama-install.sh 2>/dev/null; then
        if sh /tmp/ollama-install.sh >/tmp/ollama-install.log 2>&1; then
          log "ollama インストール完了: $(ollama --version 2>/dev/null || echo unknown)"
          touch "$OLLAMA_MARKER" 2>/dev/null || true
        else
          log "ollama インストール失敗。/tmp/ollama-install.log を確認"
        fi
        rm -f /tmp/ollama-install.sh
      else
        log "ollama インストールスクリプトの取得失敗。https://ollama.com/download を参照"
      fi
      ;;
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        if brew install ollama >/tmp/ollama-install.log 2>&1; then
          log "ollama インストール完了 (brew): $(ollama --version 2>/dev/null || echo unknown)"
          touch "$OLLAMA_MARKER" 2>/dev/null || true
        else
          log "brew install ollama 失敗。/tmp/ollama-install.log を確認"
        fi
      else
        log "macOS: brew install ollama を推奨。または https://ollama.com/download から手動"
      fi
      ;;
    *)
      log "未対応 OS ($(uname -s))。手動で ollama を入れてください: https://ollama.com/download"
      ;;
  esac
elif ollama_marker_valid; then
  log "ollama 確認 (cached)"
else
  log "ollama 確認: $(ollama --version 2>/dev/null || echo unknown)"
  touch "$OLLAMA_MARKER" 2>/dev/null || true
fi

# --- 2. ollama サーバ ---
if command -v ollama >/dev/null 2>&1; then
  if ! curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
    log "ollama サーバ未起動。バックグラウンドで起動..."
    nohup ollama serve >/tmp/ollama-serve.log 2>&1 &
    disown 2>/dev/null || true
    for i in 1 2 3 4 5; do
      sleep 1
      if curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
        log "ollama サーバ起動確認 ($OLLAMA_HOST)"
        break
      fi
    done
    if ! curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
      log "ollama サーバ起動に時間がかかっています。次回呼び出し時に再確認してください"
    fi
  else
    log "ollama サーバ確認済 ($OLLAMA_HOST)"
  fi

  # --- 3. Qwen モデル pull ---
  if curl -fsS "$OLLAMA_HOST/api/tags" >/dev/null 2>&1; then
    HAS_MODEL=$(curl -fsS "$OLLAMA_HOST/api/tags" 2>/dev/null \
      | jq -r --arg m "$QWEN_MODEL" '.models[]? | select(.name == $m) | .name' 2>/dev/null || echo "")
    if [ -z "$HAS_MODEL" ]; then
      log "$QWEN_MODEL 未取得。バックグラウンドで pull します（数 GB の DL に数分かかります）"
      nohup ollama pull "$QWEN_MODEL" >/tmp/ollama-pull.log 2>&1 &
      disown 2>/dev/null || true
      log "pull 進行中: tail -f /tmp/ollama-pull.log で確認可"
    else
      log "$QWEN_MODEL 取得済"
    fi
  fi
fi

# --- 4. ECO_MODE 状態 ---
if [ "${ECO_MODE:-0}" = "1" ]; then
  log "ECO_MODE=1: 軽処理は qwen/haiku ルートに自動振り分け"
else
  log "DRIVE_CONTEXT=1 のため起動（ECO_MODE=0）。Drive 共有フォルダ操作時は eco-mode-drive.sh が自動誘導"
fi

exit 0
