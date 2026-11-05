#!/usr/bin/env python3
"""serp_strips.py — 検索結果のフルページ画像から「段（帯）」を切り出し、枠と順位バッジを描く。

規定の正＝FIGURES_GUIDE.md §2-4「Amazon検索順位の根拠ページ（SERP）」。

  - 顧客の商品 … 実線の枠＋順位バッジ（黒地）。スクリーンショットに半透明の色を重ねない
  - スポンサー枠 … 点線の枠＋「スポンサー n」（白地）。順位には数えない
  - 段の並びと座標は results.json のカード座標（x/y/w/h）だけから決める（手で座標を書かない）
  - 届け先の郵便番号が写る左上は切り出さない（検索窓から右だけ＝header_strip）

python3 serp_strips.py --selftest   # Pillow だけで合成画像を作って確認（通信・原本不要）
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

INK = (16, 24, 32)
WHITE = (255, 255, 255)
FONT_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
ROW_TOL = 24          # 同じ段とみなす y のずれ（px）
BAND_HEIGHT = 400     # 段の高さ（商品画像＋商品名が入る範囲）
PAD = 8
# 検索窓の帯（届け先の表示が入らない範囲）。1366x900 の画面での実測を比率にしたもの
HEADER_RATIO = (0.246, 0.0, 0.700, 0.067)


def font(size, bold=True):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except Exception:
        return ImageFont.load_default()


def rows_of(cards, tol=ROW_TOL):
    """カードを段ごとにまとめる。戻り値＝[[card, …], …]（上から順）。"""
    cs = [c for c in cards if c.get("asin") and c.get("w")]
    out = []
    for c in sorted(cs, key=lambda c: (c["y"], c["x"])):
        if out and abs(out[-1][0]["y"] - c["y"]) <= tol:
            out[-1].append(c)
        else:
            out.append([c])
    return out


def row_label(row):
    """段の説明（alt 文用）。例 '1〜4位'。"""
    org = [c["organic_rank"] for c in row if c.get("organic_rank")]
    sp = [c["sponsored_rank"] for c in row if c.get("sponsored_rank")]
    parts = []
    if org:
        parts.append(f"オーガニック{min(org)}〜{max(org)}位" if len(org) > 1 else f"オーガニック{org[0]}位")
    if sp:
        parts.append(f"スポンサー{min(sp)}〜{max(sp)}枠" if len(sp) > 1 else f"スポンサー{sp[0]}枠")
    return "・".join(parts) or "検索結果"


def _badge(d, x_right, y, text, solid, size):
    f = font(size)
    tw = d.textlength(text, font=f)
    pad = max(8, size // 3)
    box = (x_right - tw - 2 * pad, y, x_right, y + int(size * 1.5))
    if solid:
        d.rounded_rectangle(box, 8, fill=INK)
    else:
        d.rounded_rectangle(box, 8, fill=WHITE, outline=INK, width=3)
    d.text((box[0] + pad, y + int(size * 0.12)), text, font=f, fill=WHITE if solid else INK)


def _dashed(d, box, w=5, dash=18, gap=10):
    x0, y0, x1, y1 = box
    for a, c, horiz, fixed in ((x0, x1, True, y0), (x0, x1, True, y1), (y0, y1, False, x0), (y0, y1, False, x1)):
        p = a
        while p < c:
            q = min(p + dash, c)
            d.line([(p, fixed), (q, fixed)] if horiz else [(fixed, p), (fixed, q)], fill=INK, width=w)
            p = q + gap


def band(fullpage, row, client_asins, out_path, height=BAND_HEIGHT, scale=1.0, quality=88):
    """段を1枚の画像にする。顧客カード＝実線＋順位、スポンサー枠＝点線＋「スポンサー n」。"""
    im = Image.open(fullpage).convert("RGB")
    x0 = max(0, int(min(c["x"] for c in row)) - PAD)
    x1 = min(im.width, int(max(c["x"] + c["w"] for c in row)) + PAD)
    y0 = max(0, int(min(c["y"] for c in row)) - 6)
    y1 = min(im.height, y0 + height)
    s = im.crop((x0, y0, x1, y1)).copy()
    d = ImageDraw.Draw(s)
    for c in row:
        box = (int(c["x"]) - x0 + 3, 3, int(c["x"] + c["w"]) - x0 - 3, s.height - 3)
        if c.get("sponsored_rank"):
            _dashed(d, box)
            _badge(d, box[2] - 10, 14, f"スポンサー {c['sponsored_rank']}", False, 28)
        elif c.get("asin") in client_asins and c.get("organic_rank"):
            d.rectangle(box, outline=INK, width=8)
            _badge(d, box[2] - 10, 14, f"{c['organic_rank']}位", True, 40)
    if scale != 1.0:
        s = s.resize((max(1, round(s.width * scale)), max(1, round(s.height * scale))), Image.LANCZOS)
    out_path = Path(out_path)
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        s.save(out_path, "JPEG", quality=quality, optimize=True)
    else:
        s.save(out_path, optimize=True)
    return out_path


def header_strip(viewport_png, out_path, header_box=None, scale=1.0, quality=88):
    """検索窓の帯。届け先の表示（郵便番号）が入らないよう、検索窓の左端より右だけを切る。"""
    im = Image.open(viewport_png).convert("RGB")
    if header_box and header_box.get("search_bar"):
        sb = header_box["search_bar"]
        x0 = int(sb["x"]); x1 = int(sb["x"] + sb["w"]); y1 = int(sb["y"] + sb["h"]) + 6
        dl = header_box.get("delivery")
        if dl and x0 < dl["x"] + dl["w"]:      # 届け先の表示に重なるなら右へ寄せる
            x0 = int(dl["x"] + dl["w"]) + 8
    else:
        rx = HEADER_RATIO
        x0, x1 = round(im.width * rx[0]), round(im.width * rx[2])
        y1 = round(im.height * rx[3])
    s = im.crop((max(0, x0), 0, min(im.width, x1), min(im.height, y1)))
    if scale != 1.0:
        s = s.resize((max(1, round(s.width * scale)), max(1, round(s.height * scale))), Image.LANCZOS)
    out_path = Path(out_path)
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        s.save(out_path, "JPEG", quality=quality, optimize=True)
    else:
        s.save(out_path, optimize=True)
    return out_path


def thumb(fullpage, card, out_path, scale=1.0, quality=88):
    """ギャップ枠に置く商品カードの画像（商品写真の部分だけ・注記は焼き込まない）。"""
    im = Image.open(fullpage).convert("RGB")
    x0 = int(card["x"]); x1 = int(card["x"] + card["w"])
    y0 = int(card["y"]); y1 = min(im.height, y0 + round((x1 - x0) * 0.98))
    s = im.crop((x0, y0, x1, y1))
    if scale != 1.0:
        s = s.resize((max(1, round(s.width * scale)), max(1, round(s.height * scale))), Image.LANCZOS)
    out_path = Path(out_path)
    if out_path.suffix.lower() in (".jpg", ".jpeg"):
        s.save(out_path, "JPEG", quality=quality, optimize=True)
    else:
        s.save(out_path, optimize=True)
    return out_path


def selftest():
    import tempfile
    t = Path(tempfile.mkdtemp(prefix="serp_strips_"))
    # 1366x2000 の疑似フルページ（4列×2段）
    im = Image.new("RGB", (1366, 2000), (245, 245, 245))
    d = ImageDraw.Draw(im)
    cards = []
    for r, y in enumerate((215, 912)):
        for i, x in enumerate((284, 551, 819, 1086)):
            d.rectangle((x, y, x + 268, y + 600), fill=(255, 255, 255), outline=(200, 200, 200))
            cards.append({"asin": f"B{r}{i}", "x": x, "y": y, "w": 268, "h": 600,
                          "organic_rank": None if r == 0 else i + 1,
                          "sponsored_rank": i + 1 if r == 0 else None})
    fp = t / "full.png"; im.save(fp)
    rows = rows_of(cards)
    assert len(rows) == 2 and len(rows[0]) == 4, [len(r) for r in rows]
    assert row_label(rows[0]) == "スポンサー1〜4枠", row_label(rows[0])
    assert row_label(rows[1]) == "オーガニック1〜4位", row_label(rows[1])
    b0 = band(fp, rows[0], {"B01"}, t / "sp.jpg")        # スポンサーの段（点線＋「スポンサー n」）
    b1 = band(fp, rows[1], {"B11", "B13"}, t / "org.jpg")  # オーガニックの段（実線＋順位）
    for b in (b0, b1):
        w, h = Image.open(b).size
        assert h == BAND_HEIGHT and 1080 < w < 1140, (b, w, h)
    # 縮小・ヘッダー帯・サムネイル
    assert Image.open(band(fp, rows[1], {"B11"}, t / "half.jpg", scale=0.5)).size[1] == BAND_HEIGHT // 2
    vp = Image.new("RGB", (1366, 900), (20, 24, 32)); vpp = t / "vp.png"; vp.save(vpp)
    hs = header_strip(vpp, t / "hdr.jpg")
    assert Image.open(hs).size == (620, 60), Image.open(hs).size      # 比率から 336..956 / 高さ 60
    hb = {"search_bar": {"x": 400, "y": 10, "w": 500, "h": 40}, "delivery": {"x": 150, "y": 10, "w": 180, "h": 40}}
    assert Image.open(header_strip(vpp, t / "hdr2.jpg", hb)).size == (500, 56)
    hb2 = {"search_bar": {"x": 200, "y": 10, "w": 700, "h": 40}, "delivery": {"x": 150, "y": 10, "w": 180, "h": 40}}
    assert Image.open(header_strip(vpp, t / "hdr3.jpg", hb2)).size == (562, 56)   # 届け先に重なるぶん右へ寄せた
    th = thumb(fp, cards[4], t / "th.jpg")
    assert Image.open(th).size == (268, 263), Image.open(th).size
    print("serp_strips selftest: OK（段分け・実線/点線・縮小・検索窓の帯・サムネイル）")
    return 0


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else
             (print(__doc__) or 0))
