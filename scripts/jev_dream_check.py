#!/usr/bin/env python3
"""memory-dream（記憶の剪定）の「埋もれた未解決作業の救出」を Jev で補強する読み取り専用の検査。

剪定で削除した行＝黙って捨てた側。ここに未解決の作業が混ざっていても誰も気づかない。
従来の grep（未完|未実施|…）はキーワードを含む行しか拾えず、「〜の要否確認」「今後行う」
「切り替え推奨」のような書き方を取りこぼす。そこで削除された各項目について、Jev に
「未完了・未検証・保留の作業を含むか」を Noul（確率）で判定させ、grep の結果と合わせて
人が1件ずつ判定するための一覧を出す。

- 読み取り専用。ファイルは一切変更しない（--fix は持たせない＝.claude/skills/memory-dream.md の方針）
- 別ファイルへ移しただけの行（同じ diff で追加された行）は対象外
- Jev への指示文は英語（Jev の得意言語）。判定対象の日本語テキストはそのまま、Tier0 語は伏せ字で送る
- Jev が使えない（鍵なし・通信失敗）項目は「判定不能」として一覧に残す（黙って除外しない）

使い方:
  python3 scripts/jev_dream_check.py                      # origin/main と作業ツリーの差分
  # git の無い場所（共有ドライブ等）: 剪定の前に写しを取り、剪定後に写しと比べる
  cp memory/active-context/若松.md "${TMPDIR:-/tmp}/dream-before.md"      # 剪定前
  python3 scripts/jev_dream_check.py --before "${TMPDIR:-/tmp}/dream-before.md" memory/active-context/若松.md
  python3 scripts/jev_dream_check.py --base 282604e^ --head 282604e   # 過去の剪定を検査
  python3 scripts/jev_dream_check.py --no-jev             # grep のみ（外部送信なし）

評価（2026-09-28・初回剪定 282604e の削除 582 行＝307 項目・当時救出した 7 件が正解）:
  grep のみ 4/7（見出し「未完了:」配下の項目を拾えない）・Jev（しきい値 0.5）7/7・約 30 秒・約 $0.006
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_context_select as J  # noqa: E402  Tier0 伏せ字・送信前検査・鍵取得を共用

DEFAULT_FILES = ["memory/active-context.md"]
# 移動先の判定に使う（ここに同じ行が追加されていれば「移しただけ」）
MOVE_TARGETS = ["memory/", "learnings/", "profile/"]
GREP = re.compile(r"未完|未実施|要確認|要フォロー|残タスク|未検証|未調査|所在未確認")
# 見出し継承: 「**未完了**:」「### 次セッションへの引継ぎ」などの配下にある項目は、本文にキーワードが
# 無くても未解決の候補にする（無料・外部送信なし。astra 検証の指摘で追加）
OPEN_LABEL = re.compile(r"未完|未実施|未検証|未調査|残タスク|次セッション|引継ぎ|今後|TODO|要対応|要確認|要フォロー")
QUESTION = ("Does this memory entry describe work that is still unfinished, unverified, or pending "
            "(a remaining task, a follow-up, an open question, or something to check later), "
            "rather than only reporting work that is already done?")
CRITERIA = {"true": "The entry contains at least one task, check, or follow-up that has not been completed yet.",
            "false": "The entry only records completed work, facts, history, or references."}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True,
                          cwd=J.PROJ).stdout


def diff_lines(base: str, head: str | None, paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    """(削除行, 追加行, 検査できなかった理由)。外部 diff / textconv は実行しない（読み取り専用の担保）。"""
    rng = [base, head] if head else [base]
    out = git("diff", "--no-color", "--no-ext-diff", "--no-textconv", "-U0", *rng, "--", *paths)
    removed = [l[1:] for l in out.splitlines() if l.startswith("-") and not l.startswith("---")]
    added = [l[1:] for l in out.splitlines() if l.startswith("+") and not l.startswith("+++")]
    problems = [l for l in out.splitlines() if l.startswith("Binary files")]
    if not head:  # 作業ツリー比較: 未追跡の対象は git diff に現れない
        for pth in paths:
            if (J.PROJ / pth).is_file() and subprocess.run(
                    ["git", "ls-files", "--error-unmatch", pth], cwd=J.PROJ,
                    capture_output=True).returncode != 0:
                problems.append(f"未追跡のため差分を取れない: {pth}")
    return removed, added, problems


def snapshot_lines(before: Path, target: str) -> tuple[list[str], list[str], list[str]]:
    """git を使わない差分（写しと現在のファイル）。(削除行, 移動先の候補行, 検査できなかった理由)。
    移動先の候補行 = memory/・learnings/・profile/ の現在のファイル（対象自身を除く）の全行。写しが無いので
    「剪定で追加された行」までは絞れないが、移動候補は印を付けるだけで除外しないため安全側に倒れる。"""
    problems = []
    try:
        old = before.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as e:
        return [], [], [f"剪定前の写しを読めない: {before}（{type(e).__name__}）"]
    cur_path = J.PROJ / target
    try:
        new = cur_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        new = []  # 対象ごと削除した場合は全行が削除扱い
    except (OSError, UnicodeDecodeError) as e:
        return [], [], [f"対象を読めない: {target}（{type(e).__name__}）"]
    removed = [l[2:] for l in difflib.ndiff(old, new) if l.startswith("- ")]
    others: list[str] = []
    for d in MOVE_TARGETS:
        for p in sorted((J.PROJ / d).rglob("*.md")) if (J.PROJ / d).is_dir() else []:
            if p.resolve() == cur_path.resolve():
                continue
            try:
                others += p.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                pass
    return removed, others, problems


def in_git_repo() -> bool:
    return subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=J.PROJ,
                          capture_output=True).returncode == 0


def norm(s: str) -> str:
    return re.sub(r"[\s*`~_]+", "", s)


def to_units(lines: list[str]) -> list[dict]:
    """箇条書き1項目（継続行を含む）を1単位にする。「**未完了**:」のような分類ラベルだけの行は単位にしない。
    Markdown 見出し（### …）は単位にする（「### TODO: 本番切替の要否確認」のような見出しを見逃さない）。
    ※ 直近の見出しを文脈として Jev に渡す案は評価で悪化したため採らない（7 件中 7→6 件）。"""
    units: list[dict] = []
    open_ctx = False  # 直近の見出し・分類ラベルが未解決系か
    for l in lines:
        if not l.strip():
            continue
        bare = norm(l)
        if re.fullmatch(r"[^#]{0,40}[:：]", bare):  # 分類ラベルだけの行
            open_ctx = bool(OPEN_LABEL.search(l))
            continue
        if l.startswith("#"):
            open_ctx = bool(OPEN_LABEL.search(l))
            units.append({"lines": [l], "inh": False})
            continue
        is_item = re.match(r"^\s*(- |\d+\. |[①-⑩]|\*\*|~~)", l)
        if not is_item and not l.startswith(" "):
            open_ctx = False  # 箇条書きでない地の文で区切る
        if is_item or not l.startswith(" ") or not units:
            units.append({"lines": [l], "inh": open_ctx})
        else:
            units[-1]["lines"].append(l)
    for u in units:
        u["text"] = "\n".join(u["lines"]).strip()
    return units


def judge_units(units: list[dict], timeout: float) -> None:
    """各項目を Jev で判定（直接 API 優先・だめなら OpenRouter＝J.call_jev）。失敗した項目は判定不能として残す。"""
    for route, *_ in J.ROUTES:  # 鍵は並列処理の前に 1 回だけ取る（1Password を同時に何度も呼ばない）
        J.route_key(route, time.monotonic() + 30)

    def one(u: dict) -> None:
        try:
            d, usage, route = J.call_jev(
                J.mask(u["text"])[:6000],
                {"open": {"type": "noul", "instructions": QUESTION, "criteria": CRITERIA}},
                time.monotonic() + timeout)
            v = (d.get("answers") or {}).get("open", {}).get("noul")
            ok = isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 1
            u["p"], u["err"] = (float(v), None) if ok else (None, "応答不正")
            u["cost"], u["route"] = usage.get("cost") or 0, route
        except Exception as e:  # noqa: BLE001  判定不能＝一覧に残す（除外しない）
            msg = str(e) if isinstance(e, RuntimeError) else type(e).__name__
            u["p"], u["err"] = None, msg[:80]

    with ThreadPoolExecutor(8) as ex:
        list(ex.map(one, units))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--head", default=None, help="省略時は作業ツリー")
    ap.add_argument("--before", type=Path, default=None,
                    help="git を使わず、剪定前の写し（ファイル）と現在の対象1件を比べる（共有ドライブ用）")
    ap.add_argument("--threshold", type=J.unit_float, default=0.5)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--no-jev", action="store_true", help="grep のみ（外部に何も送らない）")
    ap.add_argument("--json", metavar="PATH", help="全項目の判定結果（伏せ字済み）を JSON で保存")
    ap.add_argument("files", nargs="*", default=DEFAULT_FILES)
    args = ap.parse_args()

    if args.before:
        if len(args.files) != 1:
            ap.error("--before は対象ファイルを1つだけ指定する（写し1つと対象1つを比べる）")
        removed, added_all, problems = snapshot_lines(args.before, args.files[0])
        label = f"{args.before} → {args.files[0]}"
    else:
        if not in_git_repo():
            print("git の管理下ではないため差分を取れません。剪定の前に写しを取り、--before で比べてください:\n"
                  f"  cp {args.files[0]} \"${{TMPDIR:-/tmp}}/dream-before.md\"   # 剪定前\n"
                  f"  python3 scripts/jev_dream_check.py --before \"${{TMPDIR:-/tmp}}/dream-before.md\" {args.files[0]}",
                  file=sys.stderr)
            sys.exit(2)
        removed, _, problems = diff_lines(args.base, args.head, args.files)
        _, added_all, _ = diff_lines(args.base, args.head, MOVE_TARGETS)
        label = f"{args.base}..{args.head or '作業ツリー'}"
    moved = {norm(a) for a in added_all if norm(a)}
    units = to_units(removed)
    for u in units:  # 移動候補: 除外はせず印を付けるだけ（引用・複製でも一致するため）
        u["moved"] = all(norm(l) in moved for l in u["lines"] if norm(l))
    print(f"# 剪定で削除された項目の未解決チェック（{label}）\n")
    for pr in problems:
        print(f"⚠ 検査不能: {pr}")
    if not units:
        print("削除された項目なし")
        sys.exit(1 if problems else 0)
    if not args.no_jev:
        judge_units(units, args.timeout)
    rows, near = [], []
    for u in units:
        g = bool(GREP.search(u["text"])) or u.get("inh", False)  # grep または見出し継承
        p = u.get("p")
        j = p is not None and p >= args.threshold
        if g or j or u.get("err"):
            rows.append((p if p is not None else 2.0, g, j, u))  # 判定不能は先頭に出す
        elif p is not None and p >= args.threshold / 2:
            near.append(u)
    rows.sort(key=lambda r: (r[3]["moved"], -r[0]))  # 移動候補は後ろへ
    cost = sum(u.get("cost", 0) for u in units)
    print(f"削除項目 {len(units)} 件 / 要判定 {len(rows)} 件"
          f"（grep・見出し継承 {sum(r[1] for r in rows)}・Jev {sum(r[2] for r in rows)}・判定不能 "
          f"{sum(1 for r in rows if r[3].get('err'))}・うち移動候補 {sum(r[3]['moved'] for r in rows)}）"
          f" / Jev 費用 ${cost:.4f}")
    if args.no_jev:
        print(f"※ --no-jev: grep・見出し継承に該当しない {len(units) - len(rows)} 件は未判定（Jev を使えば判定される）")
    print("\n各項目について「現在も未解決 → active-context に残す（次アクションを動詞で）」"
          "「解決済み・記録済み → 削除でよい」を判定する。判定せずに削除しない。"
          "「移動候補」は同じ文が memory/・learnings/・profile/ に追加されている項目（移動先を確認して判定）。\n")
    for p, g, j, u in rows:
        print(render(u, g, j, p))
    if near:
        print(f"\n## しきい値の近く（{args.threshold / 2:.2f}〜{args.threshold:.2f}・参考）\n")
        for u in sorted(near, key=lambda x: -x["p"]):
            print(render(u, False, False, u["p"]))
    if args.json:
        Path(args.json).write_text(json.dumps(
            [{"text": J.mask(u["text"]), "p": u.get("p"), "err": u.get("err"), "moved": u["moved"],
              "grep": bool(GREP.search(u["text"])), "inherited": u.get("inh", False)} for u in units], ensure_ascii=False, indent=1),
            encoding="utf-8")
    sys.exit(1 if problems else 0)


def render(u: dict, g: bool, j: bool, p: float | None) -> str:
    """表示も Tier0 伏せ字（ログ・端末履歴に残さない）。長い項目は省略を明示する。"""
    tag = "見出し" if (g and u.get("inh") and not GREP.search(u["text"])) else "grep"
    src = "+".join(x for x, f in ((tag, g), ("Jev", j)) if f) or "近傍"
    pv = "判定不能:" + u["err"] if u.get("err") else f"p={p:.2f}"
    mv = "・移動候補" if u.get("moved") else ""
    try:
        text = J.mask(u["text"])
    except Exception:  # noqa: BLE001  語彙が読めなければ本文は出さない
        text = "(Tier0 語彙を読めないため本文を表示しない)"
    body = text[:800] + ("…（以下略・全文は --json）" if len(text) > 800 else "")
    return f"- [{src}{mv}] {pv}\n  > " + body.replace("\n", "\n  > ")


if __name__ == "__main__":
    main()
