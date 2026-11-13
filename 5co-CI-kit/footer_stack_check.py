#!/usr/bin/env python3
"""
footer_stack_check.py — CIスライドHTMLのフッター版スタック検品

規定（SLIDE_DESIGN_GUIDELINES §5.5 / V3.2_FORMAT）:
  コピーライトの左側に CIキット版・Shelpha版・Template版を出す。
  ci_head.py 経由で組んだデッキは style 内に footer stack 注入が必須。
  Shelpha 版ラベルは顧客向けデッキも含めて出す（若松さん決定 2026-11-03・v3.14.2＝
  11-02 に外した v3.14.1 を戻した）。伏せると決めた案件だけ ci_head --no-shelpha で外し、
  ci-gates.sh --ban-shelpha と対で使う。他の仕入れ先名の混入検査は vocab_check.py（HTML全文）。

使い方:
  python3 footer_stack_check.py <deck.html> [<deck.html> …]
  python3 footer_stack_check.py --warn-only <deck.html>   # 所見あっても exit 0
  python3 footer_stack_check.py --selftest

終了: 0=OK（または warn-only） / 1=不足 / 2=引数誤り
  STACK_EMPTY（v3.18.1）: HTML に焼き込まれた版スタックの CI／Template の値が空・「—」・「-」なら
  --warn-only でも exit 1（kit を template の外へコピーして manifest が見えないまま組んだデッキが
  「CI v3.18.0 · Template —」で配られた事故の回収・2026-11-08）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import ci_head  # noqa: E402


_LABEL = re.compile(r'CI (\S*)(?: · Shelpha (\S*))? · Template ([^"<·\s]*)')
_EMPTY = {"", "—", "-", "–", "?"}


def empty_version_issues(text: str, path: str) -> list[str]:
    """HTML に実際に焼き込まれた版スタックの値を見る（kit 側の現在値ではなく出力そのもの）。"""
    issues = []
    for m in _LABEL.finditer(text):
        ci, _sh, tpl = m.groups()
        if ci.strip() in _EMPTY or not ci.startswith("v"):
            issues.append(f"{path}: STACK_EMPTY 版スタックの CI 版が空: {m.group(0)!r}")
        if tpl.strip() in _EMPTY:
            issues.append(f"{path}: STACK_EMPTY 版スタックの Template 版が空: {m.group(0)!r}"
                          "（template-manifest.json が見える場所の kit で組み直す）")
    return sorted(set(issues))


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
    return issues + empty_version_issues(text, path)


def selftest() -> int:
    ok = True
    label = ci_head.footer_stack_label()
    assert label.startswith("CI "), label
    assert "Template" in label, label
    assert "Shelpha" in label, f"版スタックに Shelpha 版を出す（若松さん決定 2026-11-03）: {label}"
    assert "Shelpha" not in ci_head.footer_stack_label(shelpha=False), "--no-shelpha で外せる"
    assert "Shelpha" in ci_head.footer_stack_label(internal=True), "--internal は既定と同じ（名残の別名）"
    assert "Shelpha" in ci_head.footer_stack_css(), ci_head.footer_stack_css()
    assert "Shelpha" not in ci_head.footer_stack_css(shelpha=False), ci_head.footer_stack_css(shelpha=False)
    css = ci_head.footer_stack_css()
    assert "footer stack" in css and "All rights reserved" in css
    # synthetic HTML
    good = f"<style>/* 5co-CI ci_head v3.10 — x */\n{css}\n</style>"
    bad = "<style>/* 5co-CI ci_head v3.10 — x */\n.slide::before{content:\"© only\";}</style>"
    if check_html(good, "good.html"):
        print("SELFTEST FAIL: good should pass"); ok = False
    if not check_html(bad, "bad.html"):
        print("SELFTEST FAIL: bad should fail"); ok = False
    dash = good.replace(f"Template {ci_head.template_version()}", "Template —")
    if not empty_version_issues(dash, "dash.html") or empty_version_issues(good, "good.html"):
        print("SELFTEST FAIL: Template — は STACK_EMPTY"); ok = False
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
    issues, hard = [], False
    for f in files:
        path = Path(f)
        if not path.is_file():
            issues.append(f"{f}: ファイルが無い")
            continue
        found = check_html(path.read_text(encoding="utf-8", errors="replace"), f)
        hard = hard or any("STACK_EMPTY" in i for i in found)
        issues.extend(found)
    if not issues:
        print(f"{files[0]}: OK" if len(files) == 1 else f"{len(files)} files: OK")
        return 0
    for i in issues:
        print(i)
    print(f"{files[0]}: NG" if len(files) == 1 else "NG")
    return 1 if hard or not warn_only else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
