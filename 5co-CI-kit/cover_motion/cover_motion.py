#!/usr/bin/env python3
"""表紙・中扉カバーモーション（cover_motion）ヘルパ。stdlib のみ。

CSS keyframes＋数字断片をデッキへ載せるための読み出し／検品。
正＝COVER_MOTION_HANDOFF.md（layer8_spin_spread_v3・2026-10-28 v3.11）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS = HERE / "cover_motion.css"
DIGITS_COVER = HERE / "digits_cover.svgpart"
DIGITS_DIV = HERE / "digits_div.svgpart"

COVER_TEXT_N = 620
DIV_TEXT_N = 620


def _print_file(path: Path) -> int:
    sys.stdout.write(path.read_text(encoding="utf-8"))
    if not sys.stdout.isatty() or True:
        # ensure trailing newline if missing so pipes stay clean
        pass
    return 0


def cmd_check() -> int:
    errs: list[str] = []
    for p in (CSS, DIGITS_COVER, DIGITS_DIV):
        if not p.is_file():
            errs.append(f"missing: {p.name}")
    if errs:
        print("FAIL:", "; ".join(errs), file=sys.stderr)
        return 1

    css = CSS.read_text(encoding="utf-8")
    if "cmDriftN1" not in css:
        errs.append("CSS missing cmDriftN1")
    if "cmSpinSway" not in css:
        errs.append("CSS missing cmSpinSway")
    if "html.ci-static" not in css:
        errs.append("CSS missing html.ci-static freeze")

    cover_n = DIGITS_COVER.read_text(encoding="utf-8").count("<text")
    div_n = DIGITS_DIV.read_text(encoding="utf-8").count("<text")
    if cover_n != COVER_TEXT_N:
        errs.append(f"digits_cover <text> count {cover_n} != {COVER_TEXT_N}")
    if div_n != DIV_TEXT_N:
        errs.append(f"digits_div <text> count {div_n} != {DIV_TEXT_N}")

    if errs:
        print("FAIL:", "; ".join(errs), file=sys.stderr)
        return 1
    print(f"OK: cover={cover_n} div={div_n} css=cmDriftN1+cmSpinSway+html.ci-static (layer8_spin_spread_v3)")
    return 0


_SEC = re.compile(r'<section\b[^>]*\bclass="([^"]*)"')


def lint_html(html: str) -> dict:
    """表紙・中扉のモーション漏れ（COVER_MOTION?）。警告のみ（v3.12.6・2026-10-30）。

    表紙＝section.cover-full（pd-divider 以外）、中扉＝section.cover-full.pd-divider。
    cm-field が無いもの・cm-field はあるのに数字断片（.cm）か CSS（cmDriftN1）が無いものを拾う。
    """
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
        elif not re.match(r'\s*<div class="cm cm-(cover|div)"', html[m.end():].split(">", 1)[-1]):
            broken.append({"n": n, "kind": kind, "why": "数字断片（div.cm）が直下に無い"})
    if (n and "cm-field" in html) and "cmDriftN1" not in html:
        broken.append({"n": 0, "kind": "css", "why": "cover_motion.css が連結されていない"})
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
            print(f"{name}: COVER_MOTION? p{x['n']:02d} {what}にモーションが無い（cover has no motion）"
                  "→ ci_head.apply_cover_motion(html) か ci_head.py --apply-cover-motion")
        for x in r["broken"]:
            print(f"{name}: COVER_MOTION? p{x['n']:02d} {x['why']}")
        print(f"{name}: {'OK' if r['ok'] else 'WARN'}")
    return 0  # 警告のみ（ゲートを落とさない）


def usage_ja() -> str:
    return """使い方: python3 cover_motion.py [--css|--cover|--div|--check]

  --css    cover_motion.css を標準出力へ
  --cover  digits_cover.svgpart（表紙・620 <text>）を標準出力へ
  --div    digits_div.svgpart（中扉・620 <text>）を標準出力へ
  --check  断片の桁数と CSS 必須キーを検品（失敗時は非0）
  --lint deck.html [...] [--json]
           表紙・中扉にモーション（cm-field＋数字断片）が無いと COVER_MOTION? を出す（警告のみ・終了コード0）

表紙・中扉の CSS keyframes モーション（任意層）。手順は COVER_MOTION_HANDOFF.md。
静的 Oracle（assets/numfield_*.svg）とは別。ci_head --interactive とも独立。
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="cover_motion.py",
        description="表紙・中扉カバーモーションの CSS／数字断片ヘルパ",
        add_help=False,
    )
    p.add_argument("-h", "--help", action="store_true")
    p.add_argument("--css", action="store_true")
    p.add_argument("--cover", action="store_true")
    p.add_argument("--div", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--lint", nargs="+", metavar="deck.html")
    p.add_argument("--json", action="store_true")
    p.add_argument("--warn-only", action="store_true")  # ci-gates.sh 互換（常に警告のみ）
    args = p.parse_args(argv)
    if args.lint:
        return cmd_lint(args.lint, args.json)

    flags = sum(bool(x) for x in (args.css, args.cover, args.div, args.check))
    if args.help or flags == 0:
        sys.stdout.write(usage_ja())
        return 0
    if flags > 1:
        print("ERROR: --css / --cover / --div / --check はどれか1つ", file=sys.stderr)
        return 2
    if args.css:
        return _print_file(CSS)
    if args.cover:
        return _print_file(DIGITS_COVER)
    if args.div:
        return _print_file(DIGITS_DIV)
    if args.check:
        return cmd_check()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
