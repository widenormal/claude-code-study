#!/usr/bin/env python3
"""
photo_caption_check.py — 人物写真のキャプション・alt に「イメージ写真」と書いていないか（警告）

規定（COPY_GUIDE ルール11・2026-11-05 若松さん決定）:
  人物写真のキャプションと alt 属性には「イメージ写真」と書かず、写真が表すペルソナ
  （例: Amazonユーザー、コンサルタント）を書く。ペルソナはデッキ内の表記に従い、
  表記がないときは役割名にする。

  alt の定型は「ペルソナ名（架空の人物）」（COPY_GUIDE ルール10・2026-11-05）。
検出: HTML 全文（本文・figcaption・alt/title/aria-label 属性など）の「イメージ写真」、
      および alt に残った「イメージ」（旧定型「架空の人物・イメージ」など）。

使い方:
  python3 photo_caption_check.py <deck.html> [<deck.html> …]
  python3 photo_caption_check.py --warn-only <deck.html>   # 所見あっても exit 0
  python3 photo_caption_check.py --selftest
終了: 0=OK（または warn-only） / 1=所見あり / 2=引数誤り
所見行は PHOTO_CAPTION? で始まる。
"""
from __future__ import annotations
import re, sys
from pathlib import Path

PAT = re.compile(r"イメージ\s*写真")
ATTR = re.compile(r'\b(alt|title|aria-label)\s*=\s*"([^"]*)"', re.I)

def findings(html: str) -> list[str]:
    out = []
    for m in ATTR.finditer(html):
        if PAT.search(m.group(2)) or (m.group(1).lower() == "alt" and "イメージ" in m.group(2)):
            line = html.count("\n", 0, m.start()) + 1
            out.append(f'PHOTO_CAPTION? L{line} {m.group(1)}="{m.group(2)[:60]}" → 「ペルソナ名（架空の人物）」（例: Amazonユーザー（架空の人物））にする')
    stripped = ATTR.sub("", html)
    for m in PAT.finditer(stripped):
        ctx = stripped[max(0, m.start()-20):m.end()+20].replace("\n", " ")
        out.append(f"PHOTO_CAPTION? 本文/キャプション「…{ctx}…」→ ペルソナ名にする")
    return out

def selftest() -> bool:
    bad = '<figure><img alt="イメージ写真"><figcaption>イメージ写真</figcaption></figure>'
    good = '<figure><img alt="Amazonユーザー（架空の人物）"><figcaption>コンサルタント</figcaption></figure>'
    old = '<img alt="架空の人物・イメージ">'
    return len(findings(bad)) == 2 and findings(good) == [] and len(findings(old)) == 1

def main(argv: list[str]) -> int:
    warn_only = "--warn-only" in argv
    args = [a for a in argv if not a.startswith("--")]
    if "--selftest" in argv:
        ok = selftest(); print("photo_caption_check.py --selftest:", "OK" if ok else "FAIL"); return 0 if ok else 1
    if not args:
        print(__doc__); return 2
    allf = []
    for f in args:
        allf += [f"{f}: {x}" if len(args) > 1 else x for x in findings(Path(f).read_text(encoding="utf-8", errors="replace"))]
    if not allf:
        print(f"{args[0]}: OK" if len(args) == 1 else f"{len(args)} files: OK"); return 0
    for x in allf: print(x)
    print(f"{args[0]}: NG" if len(args) == 1 else "NG")
    return 0 if warn_only else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
