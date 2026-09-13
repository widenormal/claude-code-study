#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_label_check.py — デッキ内の SVG 図版で、ラベルが重なる・枠から切れる・地色と同色になる
のを機械的に検出する（v3.8 追加ゲート）。

なぜ要るか
  slide_overflow_check.py と check_text_overlap.py は **HTML要素** の箱を見る。SVG の中で
  描いている <text> は1つの要素として扱われるため、図の中でラベル同士が重なっても、
  viewBox の外へはみ出して切れても検出できない。実際に次が目視でしか見つからなかった:
    - バブル図で近接ブランド名が団子になる（横軸が線形で左端に集まる）
    - レンジ図の右の注記が viewBox の外に出て「…の 1」で切れる
    - ファネルの最小段が細くなりすぎ、ラベルが図形からはみ出す
    - 濃い塗りの上に濃い文字を置いて読めない

使い方
    python3 svg_label_check.py <html> [<html> …] [--verbose] [--warn-only]
    python3 svg_label_check.py --selftest        # 検査自体が働くかの確認

判定（すべて幾何のみ・レンダリング不要）
  CLIP     … <text> の推定ボックスが viewBox の外へ出ている（＝表示が切れる）
  OVERLAP  … <text> 同士の推定ボックスが 4×4px を超えて重なっている
             （文字幅は推定なので、しきい値は「明らかに読めない」ものだけが出る強さ）
  CONTRAST … 濃い塗り（<rect>）の上に濃い文字が完全に収まっている＝読めない
             ※ <path>（ファネルの台形など）は対象外。矩形の塗りだけを見る

文字幅は東アジア文字幅（W/F/A＝全角）で推定する。等幅ではないため厳密ではないので、
しきい値は「明らかに読めない」ものだけが出る強さにしてある。
"""
import re
import sys
import unicodedata

# ---- CI の色トークン → 明度（0=暗い / 1=明るい）。トークン名だけで判定する ----
DARK = {"var(--ink)", "var(--ink-85)", "#101820", "var(--insight-ink)"}
LIGHT = {"var(--crystal-25)", "var(--crystal-55)", "var(--white)", "#fff", "#ffffff", "none"}
MID = {"var(--crystal)", "var(--insight)", "var(--ink-60)", "var(--ink-20)", "var(--insight-line)"}

SVG_RE = re.compile(r'<svg[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)"[^>]*>(.*?)</svg>', re.S)
TEXT_RE = re.compile(r'<text\b([^>]*)>(.*?)</text>', re.S)
RECT_RE = re.compile(r'<rect\b([^>]*?)/>', re.S)
ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')


def attrs(s):
    return dict(ATTR_RE.findall(s))


def char_w(ch):
    """1文字の幅（em単位）。全角＝1.0、半角英数＝0.55、細い記号＝0.3。"""
    if unicodedata.east_asian_width(ch) in "WFA":
        return 1.0
    if ch in " .,:;'|!":
        return 0.3
    if ch in "()[]/-–—":
        return 0.42
    return 0.55


def text_box(a, body, dflt_fs=11.0):
    """<text> の推定ボックス (x0, y0, x1, y1) を返す。"""
    s = re.sub(r"<[^>]+>", "", body)
    s = (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&nbsp;", " ").replace("&#8212;", "—"))
    if not s.strip():
        return None, s
    fs = float(a.get("font-size", dflt_fs))
    x, y = float(a.get("x", 0)), float(a.get("y", 0))
    w = sum(char_w(c) for c in s) * fs
    anc = a.get("text-anchor", "start")
    x0 = x - w / 2 if anc == "middle" else (x - w if anc == "end" else x)
    return (x0, y - fs * 0.78, x0 + w, y + fs * 0.20), s


def tone(color):
    c = (color or "").strip().lower()
    if c in {v.lower() for v in DARK}:
        return "dark"
    if c in {v.lower() for v in LIGHT}:
        return "light"
    if c in {v.lower() for v in MID}:
        return "mid"
    if c.startswith("color-mix"):
        m = re.search(r"(\d+(?:\.\d+)?)%", c)
        return "dark" if m and float(m.group(1)) > 55 else "mid"
    return "mid"


def has_halo(a):
    """白（明るい色）のフチを付けた文字か。paint-order="stroke" の袋文字は地色を選ばない。"""
    return (tone(a.get("stroke")) == "light"
            and float(a.get("stroke-width", 0) or 0) >= 1.5)


def overlap(b1, b2):
    ox = min(b1[2], b2[2]) - max(b1[0], b2[0])
    oy = min(b1[3], b2[3]) - max(b1[1], b2[1])
    return ox, oy


def check_svg(vw, vh, body, tol=1.0):
    """1つの SVG を検査して所見のリストを返す。"""
    out = []
    texts = []
    for m in TEXT_RE.finditer(body):
        a = attrs(m.group(1))
        box, s = text_box(a, m.group(2))
        if box:
            texts.append((box, s, a))

    # ---- CLIP: viewBox の外へ出ている ----
    for box, s, a in texts:
        if box[0] < -tol or box[2] > vw + tol or box[1] < -tol or box[3] > vh + tol:
            over = max(-box[0], box[2] - vw, -box[1], box[3] - vh)
            out.append(("CLIP", f'"{s[:22]}" が枠の外へ {over:.0f}px'))

    # ---- OVERLAP: ラベル同士 ----
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ox, oy = overlap(texts[i][0], texts[j][0])
            if ox > 4.0 and oy > 4.0:
                out.append(("OVERLAP",
                            f'"{texts[i][1][:16]}"×"{texts[j][1][:16]}" が {ox:.0f}×{oy:.0f}px 重なる'))

    # ---- CONTRAST: 塗りと同じ明度の文字が乗っている ----
    rects = []
    for m in RECT_RE.finditer(body):
        a = attrs(m.group(1))
        try:
            x, y = float(a.get("x", 0)), float(a.get("y", 0))
            w_, h_ = float(a.get("width", 0)), float(a.get("height", 0))
        except ValueError:
            continue
        if w_ > 6 and h_ > 6 and float(a.get("fill-opacity", 1)) > 0.6:
            rects.append(((x, y, x + w_, y + h_), tone(a.get("fill"))))
    for box, s, a in texts:
        tt = tone(a.get("fill"))
        if tt != "dark":
            continue
        if has_halo(a):        # 白フチ付きは地色によらず読める（正当な手法）
            continue
        for (rx0, ry0, rx1, ry1), rt in rects:
            # 文字ボックスが図形に「完全に収まっている」ときだけ地色の上と見なす
            # （枠の外に半分出ている注記を誤検出しないため）
            if rt == "dark" and rx0 <= box[0] and box[2] <= rx1 and ry0 <= box[1] and box[3] <= ry1:
                out.append(("CONTRAST", f'"{s[:22]}" が濃い塗りの上に濃い文字'))
                break
    return out


def check_file(path, verbose=False):
    html = open(path, encoding="utf-8").read()
    # スライド単位で見出しを付けられるよう、section ごとに切る
    secs = re.split(r'(?=<section class="slide)', html)
    findings = []
    for pi, sec in enumerate(secs):
        if not sec.startswith('<section class="slide'):
            continue
        for si, m in enumerate(SVG_RE.finditer(sec), 1):
            vw, vh = float(m.group(1)), float(m.group(2))
            for kind, msg in check_svg(vw, vh, m.group(3)):
                findings.append((pi, si, kind, msg))
    return findings


SELFTEST = [
    # (期待する種別, SVG)
    ("CLIP", '<svg viewBox="0 0 200 60"><text x="150" y="30" font-size="11">はみ出す長い注記の文字列</text></svg>'),
    ("OVERLAP", '<svg viewBox="0 0 200 60"><text x="20" y="30" font-size="11">甘皮ケアオイル</text>'
                '<text x="20" y="33" font-size="11">ベースコート</text></svg>'),
    ("CONTRAST", '<svg viewBox="0 0 200 60"><rect x="10" y="10" width="150" height="40" fill="var(--ink)"/>'
                 '<text x="20" y="34" font-size="12" fill="var(--ink)">読めない文字</text></svg>'),
    ("", '<svg viewBox="0 0 200 60"><rect x="10" y="10" width="150" height="40" fill="var(--ink)"/>'
         '<text x="20" y="34" font-size="12" fill="var(--crystal-25)">読める文字</text>'
         '<text x="20" y="52" font-size="10" fill="var(--ink)">下の行</text></svg>'),
]


def selftest():
    """検査自体が働いているかを確かめる（しきい値を触ったら必ず流す）。"""
    ng = 0
    for want, svg in SELFTEST:
        m = SVG_RE.search(svg)
        got = {k for k, _ in check_svg(float(m.group(1)), float(m.group(2)), m.group(3))}
        ok = (got == {want}) if want else (not got)
        print(("  OK  " if ok else "  NG  ") + f"期待={want or '所見なし':9} 実際={sorted(got) or '所見なし'}")
        ng += 0 if ok else 1
    print("セルフテスト:", "合格" if ng == 0 else f"{ng}件 不一致")
    return 0 if ng == 0 else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    verbose = "--verbose" in sys.argv
    warn_only = "--warn-only" in sys.argv
    if not args:
        print(__doc__.strip().split("使い方")[1].strip())
        return 2
    bad = 0
    for path in args:
        f = check_file(path, verbose)
        name = path.split("/")[-1]
        if not f:
            print(f"{name}: OK")
            continue
        bad += 1
        seen = {}
        for pi, si, kind, msg in f:
            seen.setdefault((pi, kind), []).append(msg)
        parts = []
        for (pi, kind), msgs in sorted(seen.items()):
            head = f"{pi}:{kind}"
            body = msgs[0] if (len(msgs) == 1 or not verbose) else " / ".join(msgs)
            extra = "" if len(msgs) == 1 else f"（他 {len(msgs)-1} 件）"
            parts.append(f"{head} {body}{extra}")
        print(f"{name}: " + " | ".join(parts))
    if bad and not warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
