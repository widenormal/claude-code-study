#!/usr/bin/env python3
"""OpenRouter ラッパー（5co用・機密ガード内蔵）。

全モデル横断ゲートウェイ。認証は1Password(op)から取得。
- ZDR固定: provider.data_collection="deny"（データ保持する提供元を除外）
- Tier0ガード: AMZ-POS/Shelpha/ASIN/ベンダーセントラル/個別売上 等を含む入力は既定でブロック。
  生データ送信は「環境オプトイン＋--allow-raw＋ZDR strict」の三重ゲートを満たした時のみ許可。
- 既定モデルは安価。--model で上位に切替。

使い方:
  openrouter.py "要約して: ..." [--model openai/gpt-4o-mini] [--system "..."] [--json]
  # Tier0生データを通す場合（契約OK済の環境のみ）:
  OPENROUTER_TIER0_RAW_OK=1 openrouter.py "..." --allow-raw

Tier0生データ送信の解禁条件（三重ゲート・すべて必須）:
  1) 環境オプトイン: env `OPENROUTER_TIER0_RAW_OK=1` を設定。
     ★これは「当該クライアントの NDA/委託契約上、機密を OpenRouter＋各プロバイダ（追加サブ
       プロセッサ）へ開示してよいと確認済み」かつ「OpenRouter アカウントの ZDR を全 ON
       （Non-frontier＋Anthropic/OpenAI/Google）に設定済み」であることを、環境の管理者が
       明示的に宣言する行為。未設定の環境（template 同期先の他リポ含む）は従来どおり生ブロック。
  2) 呼び出しごとに `--allow-raw` を明示（うっかり送信の防止）。
  3) リクエストを ZDR strict 強制（data_collection=deny ＋ allow_fallbacks=false）で送信。
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import urllib.request
import urllib.error

VAULT, ITEM = "claude-code-secrets", "OpenRouter Fusion"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-4o-mini"
# Tier0生データ送信の環境オプトイン（既定 未設定＝生ブロック）。詳細は上部 docstring。
RAW_ENV = "OPENROUTER_TIER0_RAW_OK"
# Tier0(最高機密)を外部送信しないためのガード語
FORBIDDEN = ["AMZ-POS", "AMZ POS", "amz-pos", "Shelpha", "shelpha", "IGNITE",
             "ASIN", "ベンダーセントラル", "vendor central", "個別売上", "POS_RAW"]


def op_read(field: str, tries: int = 3) -> str:
    ref = f"op://{VAULT}/{ITEM}/{field}"
    for _ in range(tries):
        r = subprocess.run(["op", "read", ref], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    sys.exit(f"[op] {field} を取得できませんでした（vaultアクセス権/サインインを確認）")


def guard(text: str, allow_raw: bool) -> bool:
    """Tier0ガード語を検査。生送信が許可されたら True（呼び出し側で ZDR strict 強制）。

    生送信は「環境オプトイン(RAW_ENV=1)＋--allow-raw」の両方が揃った時のみ許可。
    どちらか欠けたらブロックして終了。ガード語が無ければ通常送信(False)。
    """
    hit = sorted(set(w for w in FORBIDDEN if w in text))
    if not hit:
        return False
    env_ok = os.environ.get(RAW_ENV) == "1"
    if allow_raw and env_ok:
        sys.stderr.write(
            "⚠️ Tier0生データ送信を許可（ZDR strict）: " + ", ".join(hit) +
            f"\n   前提: {RAW_ENV}=1（契約OK＋アカウントZDR全ON）・--allow-raw 指定。\n")
        return True
    why = []
    if not env_ok:
        why.append(f"{RAW_ENV}=1 未設定（この環境では生送信は無効）")
    if not allow_raw:
        why.append("--allow-raw 未指定")
    sys.exit("⛔ Tier0機密の疑い（" + ", ".join(hit) + "）。" + " / ".join(why) +
             "。集約値・仮名化に直すか、解禁条件を満たしてください（docstring参照）。")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--system", default="")
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--json", action="store_true", help="生JSONを出力")
    ap.add_argument("--allow-raw", action="store_true",
                    help=f"Tier0生データ送信を許可（要 {RAW_ENV}=1・ZDR strict・契約確認済み）")
    a = ap.parse_args()
    raw = guard(a.prompt + " " + a.system, a.allow_raw)

    key = op_read("credential")
    msgs = ([{"role": "system", "content": a.system}] if a.system else []) + \
           [{"role": "user", "content": a.prompt}]
    # ★ZDR固定: データ保持する提供元を除外。生データ許可時は ZDR strict（フォールバック禁止）。
    provider = {"data_collection": "deny"}
    if raw:
        provider["allow_fallbacks"] = False  # ZDR準拠経路が無ければ黙って降格せず拒否
    body = {
        "model": a.model,
        "messages": msgs,
        "max_tokens": a.max_tokens,
        "provider": provider,
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "HTTP-Referer": "https://5co.ltd", "X-Title": "5co"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            d = json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"[HTTP {e.code}] {e.read().decode()[:300]}")
    if a.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return
    ch = (d.get("choices") or [{}])[0].get("message", {}).get("content")
    print(ch if ch else json.dumps(d, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
