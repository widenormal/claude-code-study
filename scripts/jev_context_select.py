#!/usr/bin/env python3
"""Jev（TypeSafe の分類モデル・OpenRouter 経由）で、依頼に関係する記憶の項目だけを選ぶ。

目的: SessionStart で毎回全文注入している memory/active-context.md（約 8k tokens）のうち、
今回の依頼に関係する項目だけを全文で渡し、残りは見出しだけにしてトークンと文脈ノイズを減らす。

仕組み:
  1. Markdown を `## ` / `### ` 見出しで項目に分割する
  2. 各項目の「見出し＋太字キーワード」だけを Jev に送り、依頼との関係を Noul（確率）で判定
     （本文は送らない。Tier0 ガード語は伏せ字にしてから送る＝scripts/openrouter.py と同じ語彙。
       語彙を読めない・伏せ字後もガード語が残る場合は送信しない＝外部送信は fail-closed）
  3. 確率がしきい値以上の項目は全文、それ以外は見出しのみを出力する。一覧型の項目（中身4件以上）は
     中身を1件ずつ判定し、関係する行だけを残す
  4. 判定できないとき（鍵なし・通信エラー・タイムアウト・応答不正・送信停止）は全文を返す
     （fail-open＝現状の SessionStart 全文注入と同じ挙動。外部へは何も送らない）

使い方:
  jev_context_select.py "依頼文" [--file memory/active-context.md] [--threshold 0.10] [--report]
  echo '{"prompt":"...","session_id":"..."}' | jev_context_select.py --hook
    # UserPromptSubmit フック用。セッション初回の依頼でだけ additionalContext を JSON で返す
  jev_context_select.py --stats            # 実行回数・判定不能率・費用・取りこぼし率
  jev_context_select.py --audit 5          # 省略の抜き取り点検シート（未点検から無作為に5件）
  jev_context_select.py --label <id> miss --note "QWEN の件で Rutzbo 項目が必要だった"
    # フック実行ごとに ledger（既定 ~/.local/state/jev-context/ledger.jsonl・env JEV_LEDGER）へ1行記録

接続: TypeSafe 直接 API（env TYPESAFE_API_KEY／op「TYPESAFE_API_KEY JEV」）を優先し、使えなければ
OpenRouter 経由（env OPENROUTER_API_KEY／op「OpenRouter Fusion」）。鍵を env で渡すと判定は約 0.4 秒。
評価（2026-09-28・独立データ＝実在の作業 81 件・正解は Codex astra が付与）: 一覧型の個別判定＋しきい値 0.10 で
取りこぼし 3/78（3.8%）・注入量 約 46% 減。詳細 = docs/jev-context-select.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

# 接続経路: TypeSafe 直接 API を優先し、使えないとき（鍵なし・通信失敗・応答不正）は OpenRouter 経由へ。
# 2026-09-28 の実測（81 件）で品質・速度・費用は同等。直接は事業者が 1 社少なく、版を固定でき、上限 64k（決定: decisions.md）
VAULT = "claude-code-secrets"
ROUTES = [
    # (経路名, エンドポイント, モデル, 鍵の環境変数, 1Password の項目名)
    ("direct", "https://api.typesafe.ai/v1/systemone",
     os.environ.get("JEV_DIRECT_MODEL", "jev-1.13.0"), "TYPESAFE_API_KEY", "TYPESAFE_API_KEY JEV"),
    ("openrouter", "https://openrouter.ai/api/alpha/decisions",
     os.environ.get("JEV_MODEL", "typesafe/jev-1.13"), "OPENROUTER_API_KEY", "OpenRouter Fusion"),
]
PRICE_PER_TOKEN = 0.042e-6  # 入力のみ課金（出力は無料）。直接 API は応答に費用欄が無いのでここから計算
PROJ = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent)
DEFAULT_FILE = "memory/active-context.md"
# Jev への指示文は英語（Jev の得意言語。判定対象の日本語テキストはそのまま渡す）
QUESTION = "Would someone handling `user_request` need the background in the memory item \"{item}\"?"
CRITERIA = {"true": "The item concerns the same tool, system, account, document, error, or ongoing task "
                    "that the request mentions or implies.",
            "false": "The item concerns a different topic, so the request can be handled without it."}
# 本文がこの文字数以下の項目は判定せず常に全文で残す（削っても得が小さい）
ALWAYS_KEEP_CHARS = 300
# 1 リクエストで判定する件数の上限（Jev の context 64k tokens に余裕を持たせる。超えたら全文）
MAX_CANDIDATES = 120
# 中身がこの件数以上の項目は「一覧型」として中身を1件ずつ判定する
LIST_MIN = 4

try:  # Tier0 ガード語は openrouter.py を正とする。読めなければ外部送信しない（fail-closed）
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from openrouter import FORBIDDEN  # type: ignore
except Exception:  # noqa: BLE001
    FORBIDDEN = None

_ZERO_WIDTH = re.compile(r"[​-‏⁠﻿]")


def normalize(text: str) -> str:
    """すり抜け対策: NFKC（全半角統一）・ゼロ幅文字除去・Markdown 強調記号除去。"""
    text = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", text))
    return re.sub(r"[*_`~]", "", text)


def mask(text: str) -> str:
    """Tier0 ガード語を伏せ字にする（依頼側と項目側で同じ置換になるので一致判定は保たれる）。"""
    if FORBIDDEN is None:
        raise RuntimeError("Tier0 ガード語彙を読み込めないため外部送信しない")
    text = normalize(text)
    words = sorted({normalize(w) for w in FORBIDDEN}, key=len, reverse=True)
    for i, w in enumerate(words):
        text = re.sub(re.escape(w), f"[機密語{i}]", text, flags=re.IGNORECASE)
    return text


def assert_clean(payload: str) -> None:
    """送信直前の最終確認: 正規化後の送信内容にガード語が1つでも残れば送らない。"""
    flat = normalize(payload).lower()
    hit = [w for w in (FORBIDDEN or []) if normalize(w).lower() in flat]
    if FORBIDDEN is None or hit:
        raise RuntimeError(f"Tier0 ガード語が残っているため送信停止: {len(hit)} 語")


def split_blocks(md: str) -> list[dict]:
    """`## ` / `### ` 見出しで分割。先頭の見出し前テキストは preamble として常に残す。"""
    blocks: list[dict] = []
    cur = {"heading": "", "lines": []}
    in_code = False
    for line in md.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{2,3} ", line):
            blocks.append(cur)
            cur = {"heading": line, "lines": []}
            continue
        cur["lines"].append(line)
    blocks.append(cur)
    for b in blocks:
        b["body"] = "\n".join(b["lines"])
        b["always"] = (not b["heading"]) or len(b["body"].strip()) <= ALWAYS_KEEP_CHARS \
            or bool(re.match(r"^#{2,3} +📌", b["heading"]))  # 📌＝恒久的な制約・常に全文
    return blocks


def summary(block: dict, max_chars: int = 300) -> str:
    """Jev に送る要約＝見出し＋本文中の太字キーワード（本文そのものは送らない）。"""
    title = re.sub(r"^#+\s*", "", block["heading"])
    bolds = re.findall(r"\*\*(.+?)\*\*", block["body"])
    s = title + (" ／ " + " / ".join(bolds) if bolds else "")
    return mask(normalize(s))[:max_chars]  # 伏せ字→切り詰めの順（断片を送らない）


_KEYS: dict[str, str] = {}  # 同じプロセス内では 1Password を 1 回だけ引く（剪定チェックは数百回呼ぶ）。失敗は記憶しない
import threading  # noqa: E402
_KEY_LOCK = threading.Lock()  # 並列時に 1Password を同時に何度も呼ばない
FALLBACK_RESERVE = 1.5  # 直接 API の待ち時間の上限を「残り時間 − この秒数」にし、OpenRouter の分を残す


def route_key(route: str, deadline: float) -> str | None:
    """経路の鍵: 環境変数 → 1Password（残り時間内）。取れなければ None。"""
    _, _, _, env, item = next(r for r in ROUTES if r[0] == route)
    k = os.environ.get(env)
    if k:
        return k
    with _KEY_LOCK:
        if route in _KEYS:
            return _KEYS[route]
        remain = deadline - time.monotonic()
        if remain <= 0.5:
            return None
        try:
            k = subprocess.run(["op", "item", "get", item, "--vault", VAULT, "--fields", "credential",
                                "--reveal"], capture_output=True, text=True, timeout=remain).stdout.strip() or None
        except Exception:  # noqa: BLE001
            k = None
        if k:
            _KEYS[route] = k
        return k


def call_jev(state, questions: dict, deadline: float) -> tuple[dict, dict, str]:
    """直接 API → OpenRouter の順に試し、(応答, usage, 使った経路) を返す。両方だめなら例外。
    送信前に必ず Tier0 の最終確認をする（経路に関係なく同じ内容しか送らない）。"""
    errors = []
    for n, (route, endpoint, model, _, _) in enumerate(ROUTES):
        key = route_key(route, deadline)
        if not key:
            errors.append(f"{route}: 鍵なし")
            continue
        payload = json.dumps({"model": model, "state": state, "questions": questions}, ensure_ascii=False)
        assert_clean(payload)
        remain = deadline - time.monotonic()
        if n < len(ROUTES) - 1:  # 後ろに経路が残っていれば、その分の時間を残す
            remain = max(min(remain, 0.5), remain - FALLBACK_RESERVE)
        if remain <= 0.2:
            errors.append(f"{route}: 時間切れ")
            break
        try:
            req = urllib.request.Request(endpoint, data=payload.encode(),
                                         headers={"Authorization": f"Bearer {key}",
                                                  "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=remain) as r:
                d = json.load(r)
            if not isinstance(d.get("answers"), dict):
                raise ValueError("answers が無い")
        except urllib.error.HTTPError as e:  # 次の経路へ（認証切れ・上限・障害など。理由は記録）
            errors.append(f"{route}: HTTP {e.code}")
            continue
        except Exception as e:  # noqa: BLE001  次の経路へ
            errors.append(f"{route}: {type(e).__name__}")
            continue
        usage = dict(d["usage"]) if isinstance(d.get("usage"), dict) else {}
        if errors:
            usage["route_errors"] = errors  # 切り替えが起きた理由（ledger に残る）
        if usage.get("cost") is None and isinstance(usage.get("input_tokens"), int):
            usage["cost"] = usage["input_tokens"] * PRICE_PER_TOKEN
            usage["cost_estimated"] = True
        return d, usage, route
    raise RuntimeError("Jev に接続できない（" + " / ".join(errors) + "）")


def judge(prompt: str, cands: list[tuple[str, str]], deadline: float) -> tuple[dict, dict]:
    """cands=[(id, 伏せ字済み要約)] → ({id: 確率 or None}, usage)。例外は呼び出し側で fail-open。"""
    questions = {
        cid: {
            "type": "noul",
            "instructions": QUESTION.format(item=s),
            "criteria": CRITERIA,
        }
        for cid, s in cands
    }
    d, usage, route = call_jev({"user_request": mask(prompt)[:2000]}, questions, deadline)
    usage["route"] = route
    probs = {}
    for cid, a in (d.get("answers") or {}).items():
        v = a.get("noul") if isinstance(a, dict) else None
        ok = isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) and 0 <= v <= 1
        probs[cid] = float(v) if ok else None  # 不正値は「判定なし」＝全文で残す
    return probs, usage


def list_items(body: str) -> list[str]:
    """箇条書き・番号付き・表の各行を1件とする（継続行を含む）。一覧型の判定と中身の切り出しに使う。"""
    out: list[list[str]] = []
    cur: list[str] | None = None
    for l in body.splitlines():
        if re.match(r"^(\d+\.|-|\|)\s", l) and not re.match(r"^\|\s*-", l):
            cur = [l]
            out.append(cur)
        elif cur is not None and l.startswith(" "):
            cur.append(l)
    return ["\n".join(x) for x in out]


def select(md: str, prompt: str, threshold: float, timeout: float) -> tuple[str, dict]:
    """一覧型の項目（中身が LIST_MIN 件以上）は中身を1件ずつ判定し、関係する行だけ残す。
    （見出し＋太字だけでは、一覧に埋もれた個別案件と依頼を結びつけられない＝独立評価で取りこぼしの主因）"""
    deadline = time.monotonic() + timeout
    blocks = split_blocks(md)
    info: dict = {"candidates": 0, "probs": {}, "fallback": None}
    try:
        cands: list[tuple[str, str]] = []
        for i, b in enumerate(blocks):
            if b["always"]:
                continue
            its = list_items(b["body"])
            b["items"] = its if len(its) >= LIST_MIN else None
            if b["items"]:
                head = re.sub(r"^#+\s*", "", b["heading"])
                for n, it in enumerate(its):
                    cands.append((f"b{i}_{n}", mask(normalize(head + " ／ " + it.splitlines()[0]))[:220]))
            else:
                cands.append((f"b{i}", summary(b)))
        if len(cands) > MAX_CANDIDATES:
            raise RuntimeError(f"判定対象が多すぎる（{len(cands)} > {MAX_CANDIDATES}）")
        info["candidates"] = len(cands)
        if not cands:
            return md, info
        probs, usage = judge(prompt, cands, deadline)
        info.update(probs=probs, usage=usage)
    except Exception as e:  # noqa: BLE001  fail-open: 全文を返す（外部には送っていない or 送信済みで応答不良）
        info["fallback"] = f"{type(e).__name__}: {e}"
        return md, info
    keep = lambda cid: probs.get(cid) is None or probs[cid] >= threshold  # 判定なしは残す
    out, omitted, partial, omitted_blocks = [], [], 0, []
    for i, b in enumerate(blocks):
        head = re.sub(r"^#+\s*", "", b["heading"])
        if b["always"]:
            out.append((b["heading"] + "\n" if b["heading"] else "") + b["body"])
        elif b.get("items"):
            kept = [n for n in range(len(b["items"])) if keep(f"b{i}_{n}")]
            if len(kept) == len(b["items"]):
                out.append(b["heading"] + "\n" + b["body"])
                continue
            dropped = [n for n in range(len(b["items"])) if n not in kept]
            ps = [probs.get(f"b{i}_{n}") for n in dropped]
            omitted_blocks.append({"i": i, "title": head, "sha": body_sha(b["body"]),
                                   "p": max((x for x in ps if x is not None), default=None),
                                   "items_omitted": dropped})
            if kept:
                partial += 1
                out.append(b["heading"] + "\n" + "\n".join(b["items"][n] for n in kept)
                           + f"\n（この項目の他の {len(dropped)} 行は Jev により省略・必要なら元ファイルを Read）")
            else:
                omitted.append(b["heading"])
        elif keep(f"b{i}"):
            out.append(b["heading"] + "\n" + b["body"])
        else:
            omitted.append(b["heading"])
            omitted_blocks.append({"i": i, "title": head, "sha": body_sha(b["body"]), "p": probs.get(f"b{i}")})
    if omitted:
        out.append("### （Jev により省略した項目＝見出しのみ。必要なら元ファイルを Read）\n"
                   + "\n".join("- " + re.sub(r"^#+\s*", "", h) for h in omitted))
    info["omitted"] = len(omitted)
    info["partial"] = partial
    # 点検用: 位置番号・見出し・本文ハッシュ（同名見出しや記録後の書き換えを点検時に見分ける）
    info["omitted_blocks"] = omitted_blocks
    return "\n".join(out), info


def body_sha(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def claim_first(session_id: str) -> bool:
    """このプロジェクト×セッションで初回なら True。O_EXCL で原子的に作成（同時実行でも1回だけ）。"""
    if not session_id:
        return True  # ID が無ければ毎回注入（取りこぼすより重複の方が安全）
    key = hashlib.sha256(f"{PROJ.resolve()}\0{session_id}".encode()).hexdigest()[:32]
    d = Path(tempfile.gettempdir()) / f"jev-context-{os.getuid()}"
    d.mkdir(mode=0o700, exist_ok=True)
    try:
        os.close(os.open(d / f"{key}.done", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
        return True
    except FileExistsError:
        return False


def deferred_by_session_start() -> bool:
    """SessionStart（.claude/scripts/session-context.sh）が全文注入を後回しにした場合だけ True。
    同じ条件を再現する: env JEV_CONTEXT_SELECT=1 かつ per-user 形式でない かつ 旧形式の単一ファイルがある。
    （per-user 形式のリポで旧ファイルを重ねて注入しない・無効時は何もしない）"""
    if os.environ.get("JEV_CONTEXT_SELECT") != "1":
        return False
    shortname = os.environ.get("ACTIVE_CONTEXT_USER") or Path.home().name
    per_user = PROJ / "memory" / "active-context"
    if (per_user / f"{shortname}.md").is_file():
        return False
    if per_user.is_dir() and any(f.is_file() and not f.name.startswith("_") for f in per_user.glob("*.md")):
        return False
    return (PROJ / DEFAULT_FILE).is_file()


def hook_main(args: argparse.Namespace) -> None:
    """UserPromptSubmit フック: セッション初回の依頼でだけ絞り込み済み記憶を注入する。
    marker を取ったら必ず何かを出力する（選別に失敗しても全文を出す）ので、注入が消えることはない。"""
    try:
        ev = json.load(sys.stdin)
    except Exception:  # noqa: BLE001
        ev = {}
    if args.file == DEFAULT_FILE and not deferred_by_session_start():
        return
    if not claim_first(str(ev.get("session_id") or "")):
        return
    # 処理全体の上限（urlopen の timeout は全体の期限ではないため）。フック側 timeout 10 秒より先に必ず切れる
    import signal

    def _deadline(signum, frame):  # noqa: ARG001
        raise TimeoutError("hook deadline")
    signal.signal(signal.SIGALRM, _deadline)
    signal.alarm(max(1, math.ceil(args.timeout) + 1))
    state = {"printed": False}
    try:
        _hook_inject(args, ev, state)
    except BaseException as e:  # noqa: BLE001  時間切れ・予期しない失敗でも記憶は必ず全文で届ける
        signal.alarm(0)
        if state["printed"]:
            return  # 注入は出力済み（記録中の失敗）
        try:
            md = (PROJ / args.file).read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            md = f"(active-context を読めませんでした: {type(e).__name__})"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": f"=== Active Context (Jev 失敗のため全文) ===\n{md}"}}, ensure_ascii=False))


def _hook_inject(args: argparse.Namespace, ev: dict, state: dict) -> None:
    prompt = str(ev.get("prompt") or "")
    t0 = time.monotonic()
    try:
        md = (PROJ / args.file).read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        md = f"(active-context を読めませんでした: {type(e).__name__})"
        text, info = md, {"fallback": f"read: {type(e).__name__}"}
    else:
        text, info = select(md, prompt, args.threshold, args.timeout)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": f"=== Active Context (Jev で依頼関連のみ) ===\n{text}"}},
        ensure_ascii=False))
    sys.stdout.flush()  # 注入を先に確定させてから記録する（記録が詰まっても注入は届いている）
    state["printed"] = True
    import signal
    signal.alarm(0)
    ledger_append({"type": "run", "file": args.file, "file_sha": body_sha(md),
                   "prompt": safe_text(prompt), "threshold": args.threshold,
                   "ms": int((time.monotonic() - t0) * 1000), "fallback": info.get("fallback"),
                   "cost": (info.get("usage") or {}).get("cost"),
                   "route": (info.get("usage") or {}).get("route"),
                   "route_errors": (info.get("usage") or {}).get("route_errors"),
                   "proj": proj_id(),
                   "omitted": [{**o, "title": safe_text(o["title"])} for o in info.get("omitted_blocks", [])]})


# ---- 抜き取り点検（ledger）------------------------------------------------------------
# 「見出しのみ」にした項目＝黙って捨てた側。ここの誤りは誰も見ないので、記録して抜き取り点検する。
# 保存先はローカルのみ（git 管理外・権限 600）。依頼文とメモは Tier0 伏せ字・先頭 300 文字だけ残す。
# 記録するのは「セッション初回の判定」だけ（2回目以降の依頼ではフックは何もしない）。

def proj_id() -> str:
    """ledger は複数リポで共有されるため、プロジェクトを識別して点検時に取り違えない。"""
    return hashlib.sha256(str(PROJ.resolve()).encode()).hexdigest()[:12]


def ledger_path() -> Path:
    p = os.environ.get("JEV_LEDGER")
    if p:
        return Path(p)
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    return base / "jev-context" / "ledger.jsonl"


def safe_text(s: str) -> str:
    try:
        return mask(s)[:300]
    except Exception:  # noqa: BLE001  語彙が読めないなら残さない
        return ""


def ledger_append(entry: dict) -> bool:
    """1行を1回の write で追記（flock で排他）。失敗しても例外は出さない。
    通常ファイル以外（FIFO 等）とシンボリックリンクには書かない（詰まり・書き換え先の差し替え防止）。"""
    import fcntl
    import stat
    try:
        p = ledger_path()
        p.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if p.exists() or p.is_symlink():
            st = os.lstat(p)
            if not stat.S_ISREG(st.st_mode):
                return False
        entry = {"id": hashlib.sha256(os.urandom(16)).hexdigest()[:12],
                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **entry}
        data = (json.dumps(entry, ensure_ascii=False) + "\n").encode("utf-8")
        fd = os.open(p, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 待たない（取れなければ記録を諦める）
            os.write(fd, data)
        finally:
            os.close(fd)
        return True
    except Exception:  # noqa: BLE001
        return False


def _valid_run(e: dict) -> bool:
    om = e.get("omitted")
    return (isinstance(e.get("id"), str) and isinstance(e.get("ts"), str) and isinstance(om, list)
            and all(isinstance(o, dict) and isinstance(o.get("i"), int) for o in om))


def ledger_read() -> tuple[list[dict], dict[str, dict]]:
    """(run の一覧, id → 最新の label)。壊れた行・必須キーの欠けた行は読み飛ばす。"""
    runs, labels = [], {}
    p = ledger_path()
    if not p.is_file():
        return runs, labels
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            e = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(e, dict):
            continue
        if e.get("type") == "run" and _valid_run(e):
            runs.append(e)
        elif e.get("type") == "label" and isinstance(e.get("run_id"), str) \
                and e.get("verdict") in ("ok", "miss"):
            labels[e["run_id"]] = e
    return runs, labels


def audit_main(n: int) -> None:
    """未点検で省略ありの run から n 件を無作為に選び、点検シート（Markdown）を出す。
    本文は記録時のファイルから引き、ハッシュが変わっていれば「記録後に変更」と明示する。"""
    import random
    runs, labels = ledger_read()
    pool = [r for r in runs if r["omitted"] and r["id"] not in labels and r.get("proj") in (None, proj_id())]
    pick = random.sample(pool, min(max(n, 0), len(pool)))
    if not pick:
        print("点検対象なし（未点検で省略ありの記録がない）")
        return
    print("# Jev 省略の抜き取り点検\n")
    print("各記録について「依頼に取り組むうえで、省略された項目の本文が必要だったか」を判定し、\n"
          "`jev_context_select.py --label <id> ok|miss [--note '...']` で記録する。\n"
          "本文が「記録後に変更」の項目は判定材料として不確か。判定できなければ記録しない。\n")
    for r in pick:
        try:
            md = (PROJ / str(r.get("file") or DEFAULT_FILE)).read_text(encoding="utf-8")
            blocks = split_blocks(md)
        except Exception:  # noqa: BLE001
            blocks = []
        print(f"## {r['id']}（{r['ts']}・{r.get('file')}）\n\n依頼: {r.get('prompt') or '(記録なし)'}\n")
        for o in r["omitted"]:
            b = blocks[o["i"]] if 0 <= o["i"] < len(blocks) else None
            same = b is not None and body_sha(b["body"]) == o.get("sha")
            if b is None:
                excerpt = "(現在のファイルに無い)"
            elif o.get("items_omitted"):  # 一覧型: 省略した行だけを出す
                its = list_items(b["body"])
                excerpt = "\n".join(its[n] for n in o["items_omitted"] if n < len(its))[:800]
            else:
                excerpt = b["body"].strip()[:400] + "…"
            mark = "" if same else "（⚠ 記録後に変更）"
            print(f"- **{o.get('title')}**（p={o.get('p')}）{mark}\n  > " + excerpt.replace("\n", "\n  > "))
        print()


def label_main(run_id: str, verdict: str, note: str) -> None:
    runs, _ = ledger_read()
    if not any(r["id"] == run_id for r in runs):
        sys.exit(f"記録 {run_id} が見つかりません")
    if not ledger_append({"type": "label", "run_id": run_id, "verdict": verdict, "note": safe_text(note)}):
        sys.exit("記録に失敗しました（ledger に書けない）")
    print(f"記録しました: {run_id} = {verdict}")


def stats_main() -> None:
    runs, labels = ledger_read()
    if not runs:
        print("記録なし")
        return
    fb = sum(1 for r in runs if r.get("fallback"))
    om = [len(r["omitted"]) for r in runs if not r.get("fallback")]
    cost = sum(r.get("cost") or 0 for r in runs if isinstance(r.get("cost"), (int, float)))
    ms = sorted(r.get("ms") if isinstance(r.get("ms"), int) else 0 for r in runs)
    lab = [labels[r["id"]]["verdict"] for r in runs if r["id"] in labels]
    miss = lab.count("miss")
    print(f"セッション初回の判定 {len(runs)} 回 / 判定不能→全文 {fb} 回（{fb / len(runs):.0%}）")
    if om:
        print(f"省略した項目 平均 {sum(om) / len(om):.1f} 件/回")
    print(f"所要 中央値 {ms[len(ms) // 2]} ms・最大 {ms[-1]} ms / Jev 費用 合計 ${cost:.5f}")
    print(f"点検済み {len(lab)} 件 / 取りこぼし（miss） {miss} 件"
          + (f"（抜き取り分の取りこぼし率 {miss / len(lab):.0%}）" if lab else "（未点検）"))


def count_arg(s: str) -> int:
    v = int(s)
    if not 0 <= v <= 1000:
        raise argparse.ArgumentTypeError("0〜1000 の整数を指定してください")
    return v


def unit_float(s: str) -> float:
    v = float(s)
    if not (math.isfinite(v) and 0 <= v <= 1):
        raise argparse.ArgumentTypeError("0〜1 の有限値を指定してください")
    return v


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt", nargs="?", default="")
    ap.add_argument("--file", default=DEFAULT_FILE)
    ap.add_argument("--threshold", type=unit_float, default=0.10)
    ap.add_argument("--timeout", type=float, default=5.0, help="鍵取得＋判定の全体上限（秒）")
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--report", action="store_true", help="確率と選別結果を JSON で出す（評価用）")
    ap.add_argument("--audit", type=count_arg, metavar="N", help="省略の抜き取り点検シートを N 件出す")
    ap.add_argument("--label", nargs=2, metavar=("ID", "ok|miss"), help="点検結果を記録する")
    ap.add_argument("--note", default="", help="--label に添えるメモ")
    ap.add_argument("--stats", action="store_true", help="ledger の集計（取りこぼし率・費用・所要）")
    args = ap.parse_args()
    if args.hook:
        hook_main(args)
        return
    if args.audit is not None:
        audit_main(args.audit)
        return
    if args.label:
        if args.label[1] not in ("ok", "miss"):
            ap.error("--label の判定は ok か miss")
        label_main(args.label[0], args.label[1], args.note)
        return
    if args.stats:
        stats_main()
        return
    md = (PROJ / args.file).read_text(encoding="utf-8")
    text, info = select(md, args.prompt, args.threshold, args.timeout)
    if args.report:
        blocks = split_blocks(md)
        def label(k: str) -> str:
            i, _, n = k[1:].partition("_")
            b = blocks[int(i)]
            head = re.sub(r"^#+\s*", "", b["heading"])[:30]
            if not n:
                return head
            its = list_items(b["body"])
            return f"{head} » {its[int(n)].splitlines()[0][:40] if int(n) < len(its) else n}"
        info["probs"] = {label(k): v for k, v in info["probs"].items()}
        print(json.dumps(info, ensure_ascii=False, indent=1))
    else:
        print(text)


if __name__ == "__main__":
    main()
