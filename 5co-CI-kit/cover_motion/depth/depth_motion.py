#!/usr/bin/env python3
"""表紙・中扉カバーモーション（奥行きの層 depth 版）ヘルパ。stdlib のみ。

Boid（../boid/boid_motion.py・v3.15.0）の後継＝Oracle 実験#4「奥行きの層」の本番版
（大きさ・濃さ・速さの3層）。API は Boid と同じ OracleSchool.mount(canvas,{mode})。
取り付け・CSS・重なり順は Boid と同一。正＝DEPTH_COVER_HANDOFF.md（depth_cover_v1・2026-11-05 試作）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS = HERE / "depth_motion.css"
LIB = HERE / "oracle-school-depth.min.js"
MOUNT = HERE / "depth_mount.js"
PART_COVER = HERE / "digits_cover.htmlpart"
PART_DIV = HERE / "digits_div.htmlpart"

# 本番 oracle-school.js の gzip 上限（モーションディレクター審査基準）。取り付けは別枠。
GZIP_BUDGET_LIB = 6700
GZIP_BUDGET_MOUNT = 900


def _print_file(path: Path) -> int:
    sys.stdout.write(path.read_text(encoding="utf-8"))
    return 0


def script_js() -> str:
    """インライン埋め込みする JS（OracleSchool 本体＋取り付け）。"""
    return LIB.read_text(encoding="utf-8").rstrip("\n") + "\n" + MOUNT.read_text(encoding="utf-8")


def _gzip_bytes(text: str) -> int:
    import gzip
    return len(gzip.compress(text.encode("utf-8"), 9))


def gzip_size() -> int:
    return _gzip_bytes(script_js())


def cmd_check() -> int:
    errs: list[str] = []
    for p in (CSS, LIB, MOUNT, PART_COVER, PART_DIV):
        if not p.is_file():
            errs.append(f"missing: {p.name}")
    if errs:
        print("FAIL:", "; ".join(errs), file=sys.stderr)
        return 1

    lib = LIB.read_text(encoding="utf-8")
    for key in ("OracleSchool", "mount", "renderStatic", "prefers-reduced-motion"):
        if key not in lib:
            errs.append(f"lib missing {key}")
    for color in ("#C3D7EE", "#FFFFFF"):
        if color not in lib:
            errs.append(f"lib missing CI color {color}")

    css = CSS.read_text(encoding="utf-8")
    if ".cm-canvas" not in css:
        errs.append("CSS missing .cm-canvas")
    if ".cover-full.cm-field" not in css:
        errs.append("CSS missing .cover-full.cm-field")

    if 'data-cm-engine="depth"' not in PART_COVER.read_text(encoding="utf-8"):
        errs.append('digits_cover.htmlpart missing data-cm-engine="depth"')
    if 'data-cm-engine="depth"' not in PART_DIV.read_text(encoding="utf-8"):
        errs.append('digits_div.htmlpart missing data-cm-engine="depth"')

    gz_lib = _gzip_bytes(LIB.read_text(encoding="utf-8"))
    gz_mount = _gzip_bytes(MOUNT.read_text(encoding="utf-8"))
    gz_all = gzip_size()
    if gz_lib > GZIP_BUDGET_LIB:
        errs.append(f"oracle-school gzip {gz_lib}B > {GZIP_BUDGET_LIB}B")
    if gz_mount > GZIP_BUDGET_MOUNT:
        errs.append(f"depth_mount gzip {gz_mount}B > {GZIP_BUDGET_MOUNT}B")

    if errs:
        print("FAIL:", "; ".join(errs), file=sys.stderr)
        return 1
    print(
        f"OK: depth_cover_v1 lib gzip={gz_lib}B (<= {GZIP_BUDGET_LIB}B) "
        f"mount gzip={gz_mount}B (<= {GZIP_BUDGET_MOUNT}B) "
        f"inline total gzip={gz_all}B css=.cm-canvas modes=cover/divider"
    )
    return 0


_SEC = re.compile(r'<section\b[^>]*\bclass="([^"]*)"')


def lint_html(html: str) -> dict:
    """表紙・中扉の depth 層の漏れ。警告のみ（cover_motion.py --lint と同じ作法）。"""
    missing, broken = [], []
    n = 0
    for m in _SEC.finditer(html):
        cls = m.group(1).split()
        if "slide" not in cls:
            continue
        n += 1
        if "cover-full" not in cls:
            continue
        kind = "divider" if "pd-divider" in cls else "cover"
        if "cm-field" not in cls:
            missing.append({"n": n, "kind": kind})
            continue
        rest = html[m.end():].split(">", 1)[-1]
        if not re.match(r'\s*<div class="cm cm-(cover|div)"', rest):
            broken.append({"n": n, "kind": kind, "why": "数字断片（div.cm）が直下に無い"})
        elif 'data-cm-engine="depth"' not in rest[:400]:
            broken.append({"n": n, "kind": kind, "why": "depth の canvas が無い（Boid か Euclidean のまま）"})
    if n and "cm-field" in html:
        if "OracleSchool" not in html:
            broken.append({"n": 0, "kind": "js", "why": "OracleSchool が埋め込まれていない"})
        if ".cm-canvas" not in html:
            broken.append({"n": 0, "kind": "css", "why": "depth_motion.css が連結されていない"})
    return {"ok": not missing and not broken, "slides": n, "missing": missing, "broken": broken}


def cmd_lint(files: list[str], as_json: bool) -> int:
    for f in files:
        name = Path(f).name
        try:
            r = lint_html(Path(f).read_text(encoding="utf-8"))
        except OSError as e:
            print(json.dumps({"file": name, "skip": str(e)}, ensure_ascii=False) if as_json else f"{name}: SKIP {e}")
            continue
        if as_json:
            print(json.dumps({"file": name, **r}, ensure_ascii=False))
            continue
        for x in r["missing"]:
            what = "表紙" if x["kind"] == "cover" else "中扉"
            print(f"{name}: DEPTH_MOTION? p{x['n']:02d} {what}にモーションが無い（cover has no motion）"
                  "→ ci_head.apply_cover_motion(html) か ci_head.py --apply-cover-motion")
        for x in r["broken"]:
            print(f"{name}: DEPTH_MOTION? p{x['n']:02d} {x['why']}")
        print(f"{name}: {'OK' if r['ok'] else 'WARN'}")
    return 0  # 警告のみ（ゲートを落とさない）


def usage_ja() -> str:
    return """使い方: python3 depth_motion.py [--css|--js|--cover|--div|--check]

  --css    depth_motion.css を標準出力へ
  --js     埋め込む JS（OracleSchool 本体＋取り付け）を標準出力へ
  --cover  表紙の断片（canvas・mode=cover）を標準出力へ
  --div    中扉の断片（canvas・mode=divider）を標準出力へ
  --check  素材の有無・CI色・埋め込み JS の gzip 上限（6.7KB）を検品（失敗時は非0）
  --lint deck.html [...] [--json]
           表紙・中扉に depth 層が無いと DEPTH_MOTION? を出す（警告のみ・終了コード0）

表紙・中扉の数字背景を「奥行きの層」にする層。Boid（../boid/）・Euclidean（../cover_motion.py）と併存。
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="depth_motion.py", add_help=False)
    p.add_argument("-h", "--help", action="store_true")
    p.add_argument("--css", action="store_true")
    p.add_argument("--js", action="store_true")
    p.add_argument("--cover", action="store_true")
    p.add_argument("--div", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--lint", nargs="+", metavar="deck.html")
    p.add_argument("--json", action="store_true")
    p.add_argument("--warn-only", action="store_true")  # ci-gates.sh 互換（常に警告のみ）
    args = p.parse_args(argv)
    if args.lint:
        return cmd_lint(args.lint, args.json)

    flags = sum(bool(x) for x in (args.css, args.js, args.cover, args.div, args.check))
    if args.help or flags == 0:
        sys.stdout.write(usage_ja())
        return 0
    if flags > 1:
        print("ERROR: --css / --js / --cover / --div / --check はどれか1つ", file=sys.stderr)
        return 2
    if args.css:
        return _print_file(CSS)
    if args.js:
        sys.stdout.write(script_js())
        return 0
    if args.cover:
        return _print_file(PART_COVER)
    if args.div:
        return _print_file(PART_DIV)
    if args.check:
        return cmd_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
