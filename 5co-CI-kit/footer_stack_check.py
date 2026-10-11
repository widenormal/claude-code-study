#!/usr/bin/env python3
"""
footer_stack_check.py — CIスライドHTMLのフッター版スタック検品

規定（SLIDE_DESIGN_GUIDELINES §5.5 / V3.2_FORMAT）:
  コピーライトの左側に CIキット版・Shelpha版・Template版を出す。
  ci_head.py 経由で組んだデッキは style 内に footer stack 注入が必須。

使い方:
  python3 footer_stack_check.py <deck.html> [<deck.html> …]
  python3 footer_stack_check.py --warn-only <deck.html>   # 所見あっても exit 0
  python3 footer_stack_check.py --selftest

終了: 0=OK（または warn-only） / 1=不足 / 2=引数誤り
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import ci_head  # noqa: E402


def check_html(text: str, path: str) -> list[str]:
    issues = []
    has_ci_head = bool(re.search(r"5co-CI ci_head v[\d.]+", text))
    has_stack_css = "footer stack" in text and "CI " in text and "Template " in text
    has_stack_html = bool(re.search(r'class=["\']ci-stack["\']', text))
    if has_ci_head and not (has_stack_css or has_stack_html):
        issues.append(f"{path}: ci_head 経由なのにフッター版スタック（CI / Shelpha / Template）が無い")
    if has_stack_css or has_stack_html:
        # 実値が解決できているか（プレースホルダだけの嘘は許すが、空は不可）
        label = ci_head.footer_stack_label()
        if "CI " not in label or "Template " not in label:
            issues.append(f"{path}: footer_stack_label が不正: {label!r}")
    return issues


def selftest() -> int:
    ok = True
    label = ci_head.footer_stack_label()
    assert label.startswith("CI "), label
    assert "Shelpha" in label and "Template" in label, label
    css = ci_head.footer_stack_css()
    assert "footer stack" in css and "All rights reserved" in css
    # synthetic HTML
    good = f"<style>/* 5co-CI ci_head v3.10 — x */\n{css}\n</style>"
    bad = "<style>/* 5co-CI ci_head v3.10 — x */\n.slide::before{content:\"© only\";}</style>"
    if check_html(good, "good.html"):
        print("SELFTEST FAIL: good should pass"); ok = False
    if not check_html(bad, "bad.html"):
        print("SELFTEST FAIL: bad should fail"); ok = False
    print("footer_stack_check.py --selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    warn_only = "--warn-only" in argv
    files = [a for a in argv if not a.startswith("-")]
    if not files:
        print("使い方: footer_stack_check.py <deck.html>…", file=sys.stderr)
        return 2
    issues = []
    for f in files:
        path = Path(f)
        if not path.is_file():
            issues.append(f"{f}: ファイルが無い")
            continue
        issues.extend(check_html(path.read_text(encoding="utf-8", errors="replace"), f))
    if not issues:
        print(f"{files[0]}: OK" if len(files) == 1 else f"{len(files)} files: OK")
        return 0
    for i in issues:
        print(i)
    print(f"{files[0]}: NG" if len(files) == 1 else "NG")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
