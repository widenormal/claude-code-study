#!/usr/bin/env python3
"""
header_band_check.py — 本文ヘッダーの数字の帯（.ci-hb）の付け忘れ検品（v3.18.1）

背景（2026-11-08 CIスライド）: 版スタンプが v3.18.0 なのに .ci-hb / ci-hb-on が0件のデッキが
「最新版」として出ていた。v3.17.0 で帯はオプトイン（apply_header_motion）だったため、呼び忘れても
版番号だけが上がり、どの検査も鳴らなかった。

規定（v3.18.1〜）: ci_head 版スタンプが v3.17.0 以上のデッキは、直下に .hdr を持つ本文ページ
（表紙 cover-full・中扉 pd-divider/divider・dark は対象外＝ci_head._SKIP_HB と同じ判定）に
ci-hb-on と .ci-hb を付ける。付けない本文ページ（目次・静的な資料など）は
<section class="slide" data-hb="off" data-hb-reason="理由"> と書く。
reduced-motion・#static・印刷は帯の静止画になるだけ（マークアップは同じ）なので例外にしない。

  HB_MISSING   … 対象の本文ページに帯が無い（落とす）
  HB_REASON?   … data-hb="off" に data-hb-reason が無い（警告のみ）

使い方:
  python3 header_band_check.py <deck.html> [...]   # NG で exit 1
  python3 header_band_check.py --warn-only <deck.html>
  python3 header_band_check.py --selftest
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
import ci_head  # noqa: E402

MIN_VER = (3, 17, 0)
_STAMP = re.compile(r"5co-CI ci_head v(\d+)\.(\d+)(?:\.(\d+))?")
_SKIP = tuple(c for c in ci_head._SKIP_HB if c != "ci-hb-on")


def _stamp_ver(text: str):
    m = _STAMP.search(text)
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def check_html(text: str, path: str):
    """返り値 (落とす所見, 警告)。"""
    errs, warns = [], []
    ver = _stamp_ver(text)
    if ver is None or ver < MIN_VER:
        return errs, warns
    parts = re.split(r"(<section\b[^>]*>)", text)
    page = 0
    for i in range(1, len(parts), 2):
        m = ci_head._SECTION_OPEN.match(parts[i])
        if not m:
            continue
        cls = m.group(2).split()
        if "slide" not in cls:
            continue
        page += 1
        body = (parts[i + 1] if i + 1 < len(parts) else "").split("</section>")[0]
        if any(c in cls for c in _SKIP) or '<div class="hdr"' not in body:
            continue
        if 'data-hb="off"' in parts[i]:
            r = re.search(r'data-hb-reason="([^"]*)"', parts[i])
            if not (r and r.group(1).strip()):
                warns.append(f"{path}: p{page:02d} HB_REASON? data-hb=\"off\" に data-hb-reason（理由）が無い")
            continue
        if "ci-hb-on" not in cls or 'class="ci-hb"' not in body:
            errs.append(f"{path}: p{page:02d} HB_MISSING 本文ヘッダーの数字の帯が無い"
                        f"（版スタンプ v{'.'.join(map(str, ver))}・→ ci_head.py --apply-header-motion"
                        f"／外すなら data-hb=\"off\" data-hb-reason=\"理由\"）")
    return errs, warns


def _fixture(sections: str, ver: str = "v3.18.1") -> str:
    return (f"<html><head><style>/* 5co-CI ci_head {ver} — x */</style></head><body>"
            f"{sections}</body></html>")


def selftest() -> int:
    hdr = '<div class="hdr"><h2 class="title">見出し</h2><div class="accent-bar"></div></div>'
    cover = '<section class="slide cover-full"><h1>表紙</h1></section>'
    plain = _fixture(cover + f'<section class="slide">{hdr}</section>')
    good, n = ci_head.apply_header_motion(plain)
    excl = _fixture(cover + f'<section class="slide" data-hb="off" data-hb-reason="目次">{hdr}</section>')
    nores = _fixture(f'<section class="slide" data-hb="off">{hdr}</section>')
    old = _fixture(f'<section class="slide">{hdr}</section>', "v3.16.0")
    cases = [
        ("帯なし本文ページは落ちる", check_html(plain, "a")[0] != []),
        ("apply_header_motion の出力は通る", n == 1 and check_html(good, "b") == ([], [])),
        ("理由付きの data-hb=off は通る", check_html(excl, "c") == ([], [])),
        ("理由なしの data-hb=off は警告のみ", check_html(nores, "d")[0] == [] and check_html(nores, "d")[1] != []),
        ("v3.17.0 より前の版スタンプは対象外", check_html(old, "e") == ([], [])),
    ]
    ok = all(c for _, c in cases)
    for name, c in cases:
        print(("  ✔ " if c else "  ✘ ") + name)
    print("header_band_check.py --selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    warn_only = "--warn-only" in argv
    files = [a for a in argv if not a.startswith("-")]
    if not files:
        print("使い方: header_band_check.py <deck.html>…", file=sys.stderr)
        return 2
    errs, warns = [], []
    for f in files:
        p = Path(f)
        if not p.is_file():
            errs.append(f"{f}: ファイルが無い")
            continue
        e, w = check_html(p.read_text(encoding="utf-8", errors="replace"), f)
        errs += e
        warns += w
    for line in errs + warns:
        print(line)
    if errs:
        print("NG")
        return 0 if warn_only else 1
    print(f"{files[0]}: 警告あり" if warns else (f"{files[0]}: OK" if len(files) == 1 else f"{len(files)} files: OK"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
