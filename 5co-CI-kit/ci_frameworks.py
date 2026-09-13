#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ci_frameworks.py — CI v2（A4横・3色）で描くフレームワーク図の SVG ヘルパー。

SLIDE-PATTERN 129種のうち、分析デッキで使用頻度の高い型を、案件ビルダーから
関数1本で呼べるようにしたもの。色は正典トークンのみ（--ink / --crystal / --crystal-55 /
--crystal-25 / --ink-60 / --ink-20 と、機能色 --insight 系）を使い、新しい色を足さない。

収録（対応する SLIDE-PATTERN）
  mekko        … mekko-market-map            幅=市場規模 × 高さ=シェア
  bars_line    … bar-line-combo              棒＋折線（月次推移に自社シェアを重ねる）
  heatmap      … heatmap-matrix-table        行×列の濃淡マトリクス
  funnel       … funnel-conversion-stages    段階的な絞り込み
  bubble       … scatter-bubble-positioning  2軸＋バブルサイズ
  ranges       … （3ケースのレンジ比較）      保守〜楽観の幅と基準線
  waterfall    … waterfall-bridge-chart      増減の橋渡し
  slope        … slope-chart-before-after    時点間の推移（傾き）
  concentric   … concentric-circles-market   市場の入れ子（TAM/SAM/SOM 型）
  tree         … kpi-driver-tree             指標の親子関係

共通の約束
  - 数値ラベルは図の中に置く（凡例だけに逃さない）
  - 琥珀（--insight）は「その図の洞察が言及する要素」だけに使う（装飾禁止）
  - 返り値は <svg>…</svg> の文字列。案件側はそのままスライド本文へ差し込む
"""
import math

INK = "var(--ink)"
CRY = "var(--crystal)"
CRY55 = "var(--crystal-55)"
CRY25 = "var(--crystal-25)"
INK60 = "var(--ink-60)"
INK20 = "var(--ink-20)"
AMB = "var(--insight)"
AMB_INK = "var(--insight-ink)"
AMB_LINE = "var(--insight-line)"


def _open(w, h, mt=6):
    return [f'<svg viewBox="0 0 {w} {h}" width="100%" style="display:block;margin-top:{mt}px;">']


def _t(x, y, s, size=11, fill=INK, anchor="start", weight=None):
    w = ' font-weight="700"' if weight else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}"{w}>{s}</text>'


# ---------------------------------------------------------------- mekko
def mekko(rows, w=980, h=250, unit="M", note=None):
    """幅＝市場規模／高さ＝自社シェアのマーケコ図。
    rows: [(ラベル, 市場規模, 自社シェア%, 強調bool, 補足文字列)] を規模の降順で渡す。
    列の幅は市場規模に比例。塗り高さはシェアに比例（列の全高＝その区分の100%）。
    note: 図の上に置く説明。案件の語彙に合わせて渡す（既定は汎用の言い回し）。"""
    pad_l, pad_t, pad_b = 6, 30, 46
    plot_h = h - pad_t - pad_b
    total = sum(r[1] for r in rows) or 1
    gap = 3
    avail = w - pad_l * 2 - gap * (len(rows) - 1)
    o = _open(w, h)
    o.append(_t(pad_l, 13, note or "各列の幅＝市場規模／塗り＝自社の金額シェア（列の全高＝その区分の100%）", 10, INK60))
    x = pad_l
    for lab, size, share, hi, note in rows:
        cw = avail * size / total
        empty_hi = hi and share <= 0
        o.append(f'<rect x="{x:.1f}" y="{pad_t}" width="{cw:.1f}" height="{plot_h}" '
                 f'fill="{"var(--insight)" if empty_hi else CRY25}" fill-opacity="{0.28 if empty_hi else 1}" '
                 f'stroke="{AMB_LINE if empty_hi else INK20}" stroke-width="{1.6 if empty_hi else 0.6}"'
                 + (' stroke-dasharray="5 4"' if empty_hi else "") + '/>')
        fh = plot_h * min(share, 100) / 100
        fill = AMB if hi else INK
        o.append(f'<rect x="{x:.1f}" y="{pad_t + plot_h - fh:.1f}" width="{cw:.1f}" height="{fh:.1f}" fill="{fill}"/>')
        cx = x + cw / 2
        if share >= 8:
            o.append(_t(cx, pad_t + plot_h - fh + 15, f"{share:.1f}%", 12, AMB_INK if hi else CRY, "middle", True))
        elif share > 0:
            o.append(_t(cx, pad_t + plot_h - fh - 5, f"{share:.1f}%", 11, INK, "middle", True))
        else:
            o.append(_t(cx, pad_t + plot_h - 8, note or "0%", 11, AMB_INK, "middle", True))
        # 下のラベル（幅が狭い列は2行に折らずフォントを落とす）
        fs = 11 if cw > 96 else (9.5 if cw > 62 else 8.2)
        o.append(_t(cx, h - pad_b + 16, lab, fs, INK, "middle", hi))
        o.append(_t(cx, h - pad_b + 30, f"¥{size:.1f}{unit}", fs - 0.5, INK60, "middle"))
        x += cw + gap
    o.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{w - pad_l}" y2="{pad_t + plot_h}" stroke="{INK20}" stroke-width="1"/>')
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- heatmap
def heatmap(cols, rows, w=980, h=250, note="", hi_cells=()):
    """行×列の濃淡マトリクス。rows: [(行ラベル, [値…], 右端の補足)]。値は % を想定（None は該当なし）。
    hi_cells: 琥珀にする (行index, 列index) の集合。"""
    lab_w, rlab_w, pad_t, pad_b = 150, 92, 28, 22
    n = len(cols)
    cw = (w - lab_w - rlab_w) / n
    ch = (h - pad_t - pad_b) / len(rows)
    mx = max((v for _, vals, _ in rows for v in vals if v is not None), default=1)
    o = _open(w, h)
    if note:
        o.append(_t(0, 11, note, 10, INK60))
    for j, c in enumerate(cols):
        o.append(_t(lab_w + cw * (j + .5), pad_t - 7, c, 10, INK60, "middle"))
    for i, (lab, vals, extra) in enumerate(rows):
        y = pad_t + ch * i
        o.append(_t(lab_w - 8, y + ch / 2 + 4, lab, 11, INK, "end"))
        for j, v in enumerate(vals):
            x = lab_w + cw * j
            if v is None:
                o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw - 2:.1f}" height="{ch - 2:.1f}" fill="none" stroke="{INK20}" stroke-width="0.5" stroke-dasharray="2 2"/>')
                o.append(_t(x + cw / 2, y + ch / 2 + 4, "—", 10, INK20, "middle"))
                continue
            k = v / mx if mx else 0
            amber = (i, j) in hi_cells
            fill = AMB if amber else f"color-mix(in srgb, {INK} {k*88:.0f}%, {CRY25})"
            tc = AMB_INK if amber else (CRY25 if k > .5 else INK)
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cw - 2:.1f}" height="{ch - 2:.1f}" fill="{fill}"'
                     + (f' stroke="{AMB_LINE}" stroke-width="1.5"' if amber else "") + '/>')
            o.append(_t(x + cw / 2, y + ch / 2 + 4, f"{v:.0f}%", 11, tc, "middle", amber))
        o.append(_t(w - rlab_w + 6, y + ch / 2 + 4, extra, 10.5, INK60))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- funnel
def funnel(stages, w=470, h=250):
    """段階的な絞り込み。stages: [(ラベル, 値, 補足, 強調bool)]。幅が値に比例した台形を縦に積む。"""
    pad_t, pad_b = 6, 6
    n = len(stages)
    sh = (h - pad_t - pad_b) / n
    mx = stages[0][1] or 1
    o = _open(w, h)
    for i, (lab, v, note, hi) in enumerate(stages):
        y = pad_t + sh * i
        def _fw(val):                 # 幅は 25% を下限にする（比が大きくても文字が収まるように）
            return w * (0.25 + 0.75 * (val / mx) ** .5)
        w0 = _fw(v)
        w1 = _fw(stages[i + 1][1]) if i + 1 < n else w0 * .82
        x0, x1 = (w - w0) / 2, (w - w1) / 2
        fill = AMB if hi else (INK if i == 0 else CRY)
        tc = AMB_INK if hi else (CRY25 if i == 0 else INK)
        o.append(f'<path d="M{x0:.1f} {y:.1f} L{x0+w0:.1f} {y:.1f} L{x1+w1:.1f} {y+sh-8:.1f} L{x1:.1f} {y+sh-8:.1f} Z" fill="{fill}"/>')
        o.append(_t(w / 2, y + sh / 2 - 4, f"{v:,}", 19, tc, "middle", True))
        o.append(_t(w / 2, y + sh / 2 + 12, lab, 10.5, tc, "middle"))
        if note:
            o.append(_t(w - 2, y + sh / 2 + 2, note, 10, INK60, "end"))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- bubble
def bubble(pts, w=980, h=250, xlab="", ylab="", xlog=False, xticks=()):
    """2軸＋バブル。pts: [(x, y, size, ラベル, 強調bool)]。
    xlog=True で横軸を対数にする（値が数倍〜十数倍に散らばるとき、左端に固まるのを防ぐ）。"""
    pad_l, pad_r, pad_t, pad_b = 46, 34, 16, 34
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; ss = [p[2] for p in pts]
    _f = (lambda v: math.log10(max(v, 1e-9))) if xlog else (lambda v: v)
    span = (_f(max(xs)) - _f(min(xs))) or 1
    x0, x1 = _f(min(xs)) - span * .10, _f(max(xs)) + span * .10
    y1 = max(ys) * 1.12
    smax = max(ss) or 1
    def X(v): return pad_l + (w - pad_l - pad_r) * (_f(v) - x0) / (x1 - x0)
    def Y(v): return h - pad_b - (h - pad_t - pad_b) * v / y1
    o = _open(w, h)
    for gy in range(0, int(y1) + 1, max(1, int(y1 // 4))):
        o.append(f'<line x1="{pad_l}" y1="{Y(gy):.1f}" x2="{w-pad_r}" y2="{Y(gy):.1f}" stroke="{INK20}" stroke-width="0.5"/>')
        o.append(_t(pad_l - 6, Y(gy) + 4, f"{gy}", 9.5, INK60, "end"))
    placed = []                       # ラベルの重なり回避（同じ帯に来たら上下にずらす）
    for x, y, s, lab, hi in sorted(pts, key=lambda p: -p[2]):
        r = 6 + 22 * (s / smax) ** .5
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r:.1f}" fill="{AMB if hi else CRY}" '
                 f'stroke="{AMB_LINE if hi else INK}" stroke-width="{1.6 if hi else 0.8}" fill-opacity="{1 if hi else .85}"/>')
        lx, ly = X(x), Y(y) - r - 5
        for px, py in placed:
            if abs(px - lx) < 52 and abs(py - ly) < 11:
                ly = py - 11
        placed.append((lx, ly))
        o.append(_t(lx, max(ly, 9), lab, 9.6, INK, "middle", hi))
    o.append(f'<line x1="{pad_l}" y1="{h-pad_b}" x2="{w-pad_r}" y2="{h-pad_b}" stroke="{INK20}"/>')
    for v in (xticks or (min(xs), max(xs))):      # x軸の目盛り
        o.append(_t(X(v), h - pad_b + 14, f"{v:g}", 9.5, INK60, "middle"))
    o.append(_t(w - pad_r, h - 6, xlab, 10, INK60, "end"))
    o.append(_t(0, 11, ylab, 10, INK60))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- ranges
def ranges(items, w=980, h=210, ref=None, ref_label="", unit="億"):
    """レンジ比較。items: [(ラベル, 低, 中, 高, 補足)]。ref を縦の基準線として引く。"""
    lab_w, pad_r, pad_t = 128, 152, 24
    lo = min(min(i[1] for i in items), ref or 1e18) * .93
    hi = max(max(i[3] for i in items), ref or 0) * 1.06
    def X(v): return lab_w + (w - lab_w - pad_r) * (v - lo) / (hi - lo)
    rh = (h - pad_t - 14) / len(items)
    o = _open(w, h)
    if ref is not None:
        o.append(f'<line x1="{X(ref):.1f}" y1="{pad_t-12}" x2="{X(ref):.1f}" y2="{h-16}" stroke="{AMB_LINE}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        o.append(_t(X(ref), pad_t - 16, ref_label, 10.5, AMB_INK, "middle", True))
    for i, (lab, a, m, b, note) in enumerate(items):
        y = pad_t + rh * i + rh / 2
        o.append(_t(lab_w - 10, y + 4, lab, 12, INK, "end", True))
        o.append(f'<line x1="{X(a):.1f}" y1="{y:.1f}" x2="{X(b):.1f}" y2="{y:.1f}" stroke="{CRY}" stroke-width="9" stroke-linecap="round"/>')
        for v, r_, c in ((a, 4.5, INK20), (b, 4.5, INK20)):
            o.append(f'<circle cx="{X(v):.1f}" cy="{y:.1f}" r="{r_}" fill="{c}"/>')
        o.append(f'<circle cx="{X(m):.1f}" cy="{y:.1f}" r="7" fill="{AMB}" stroke="{AMB_LINE}" stroke-width="1.5"/>')
        o.append(_t(X(a) - 8, y + 4, f"{a:.2f}", 10, INK60, "end"))
        o.append(_t(X(b) + 8, y + 4, f"{b:.2f}", 10, INK60))
        o.append(_t(w - pad_r + 10, y + 4, note, 10.5, INK))
    o.append(_t(0, 11, f"単位: {unit}／丸＝基準ケース、バーの両端＝保守と楽観", 10, INK60))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- waterfall
def waterfall(steps, w=980, h=250, unit="M", note=""):
    """増減の橋渡し。steps: [(ラベル, 値, 種別)]。種別: 'start' | 'delta' | 'end'。"""
    pad_t, pad_b = 26, 44
    n = len(steps)
    bw = (w - 16) / n * .62
    pitch = (w - 16) / n
    vals, cum, base = [], 0, []
    for lab, v, kind in steps:
        if kind in ("start", "end"):
            base.append(0); vals.append(v); cum = v
        else:
            base.append(cum); vals.append(v); cum += v
    mx = max([b + v for b, v in zip(base, vals)] + [v for v in vals]) * 1.14
    def Y(v): return h - pad_b - (h - pad_t - pad_b) * v / mx
    o = _open(w, h)
    if note: o.append(_t(0, 11, note, 10, INK60))
    prev_top = None
    for i, ((lab, v, kind), b) in enumerate(zip(steps, base)):
        x = 8 + pitch * i + (pitch - bw) / 2
        lo, hi_ = (b, b + v) if v >= 0 else (b + v, b)
        y, hh = Y(hi_), abs(Y(lo) - Y(hi_))
        if kind == "start": fill = INK
        elif kind == "end": fill = AMB
        else: fill = CRY if v >= 0 else CRY55
        o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(hh,1.5):.1f}" fill="{fill}"'
                 + (f' stroke="{AMB_LINE}" stroke-width="1.5"' if kind == "end" else "") + '/>')
        sign = "" if kind in ("start", "end") else ("+" if v >= 0 else "−")
        o.append(_t(x + bw / 2, y - 6, f"{sign}{abs(v):.2f}", 11, INK, "middle", kind in ("start", "end")))
        o.append(_t(x + bw / 2, h - pad_b + 16, lab, 10, INK, "middle", kind in ("start", "end")))
        if prev_top is not None:
            o.append(f'<line x1="{prev_top[0]:.1f}" y1="{prev_top[1]:.1f}" x2="{x:.1f}" y2="{prev_top[1]:.1f}" stroke="{INK20}" stroke-width="1" stroke-dasharray="3 2"/>')
        prev_top = (x + bw, Y(b + v) if kind == "delta" else Y(v))
    o.append(f'<line x1="8" y1="{h-pad_b}" x2="{w-8}" y2="{h-pad_b}" stroke="{INK20}"/>')
    o.append(_t(w - 8, h - 6, f"単位: {unit}", 10, INK60, "end"))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- slope
def slope(series, xlabels, w=980, h=250, ceil_label="シェア上限"):
    """時点間の推移（傾き）。series: [(ラベル, [値…], 上限値 or None, 強調bool)]。値は %。"""
    pad_l, pad_r, pad_t, pad_b = 132, 150, 24, 26
    n = len(xlabels)
    mx = max([max(v) for _, v, _, _ in series] + [c for _, _, c, _ in series if c]) * 1.1
    def X(i): return pad_l + (w - pad_l - pad_r) * i / (n - 1)
    def Y(v): return h - pad_b - (h - pad_t - pad_b) * v / mx
    o = _open(w, h)
    for i, xl in enumerate(xlabels):
        o.append(f'<line x1="{X(i):.1f}" y1="{pad_t}" x2="{X(i):.1f}" y2="{h-pad_b}" stroke="{INK20}" stroke-width="0.6"/>')
        o.append(_t(X(i), h - pad_b + 16, xl, 10.5, INK60, "middle"))
    def _spread(ys, gap=12.5):
        """近すぎるラベルを上下にずらす（描画順を保ったまま）。"""
        order = sorted(range(len(ys)), key=lambda i: ys[i])
        out = list(ys)
        for k in range(1, len(order)):
            a, b = order[k - 1], order[k]
            if out[b] - out[a] < gap:
                out[b] = out[a] + gap
        return out
    ys_l = _spread([Y(v[0]) for _, v, _, _ in series])
    ys_r = _spread([Y(v[-1]) for _, v, _, _ in series])
    for k, (lab, vals, ceil_, hi) in enumerate(series):
        col = AMB_LINE if hi else CRY
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="{2.4 if hi else 1.6}"/>')
        for i, v in enumerate(vals):
            o.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{3.4 if hi else 2.6}" fill="{col}"/>')
        if abs(ys_l[k] - Y(vals[0])) > 2:       # ずらした分は引き出し線でつなぐ
            o.append(f'<line x1="{pad_l-6:.1f}" y1="{ys_l[k]-3.5:.1f}" x2="{pad_l:.1f}" y2="{Y(vals[0]):.1f}" stroke="{INK20}" stroke-width="0.8"/>')
        o.append(_t(pad_l - 8, ys_l[k], lab, 10.5, INK, "end", hi))
        o.append(_t(X(n - 1) + 8, ys_r[k], f"{vals[-1]:.1f}%", 10.5, INK, "start", hi))
    drawn = set()                                # 同じ上限値は1本だけ描く
    for lab, vals, ceil_, hi in series:
        if ceil_ and round(ceil_, 1) not in drawn:
            drawn.add(round(ceil_, 1))
            o.append(f'<line x1="{X(n-1)+52:.1f}" y1="{Y(ceil_):.1f}" x2="{X(n-1)+104:.1f}" y2="{Y(ceil_):.1f}" stroke="{AMB_LINE}" stroke-width="1.4" stroke-dasharray="4 3"/>')
            o.append(_t(X(n - 1) + 108, Y(ceil_) + 4, f"{ceil_:.1f}%", 10, AMB_INK))
    o.append(_t(w - 8, 11, f"右端の点線＝{ceil_label}", 10, AMB_INK, "end"))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- concentric
def concentric(circles, w=470, h=250):
    """入れ子の市場（TAM/SAM/SOM 型）。circles: 外側から [(ラベル, 値, 補足, 強調bool)]。"""
    cw_ = w * .40                       # 左40%が円、右60%が凡例
    cx, cy = cw_ / 2, h / 2
    rmax = min(h / 2 - 10, cw_ / 2 - 6)
    mx = circles[0][1] or 1
    o = _open(w, h)
    for i, (lab, v, note, hi) in enumerate(circles):
        r = max(7.0, rmax * (v / mx) ** .38)
        fill = AMB if hi else (CRY25 if i == 0 else (CRY55 if i == 1 else CRY))
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{AMB_LINE if hi else INK20}" stroke-width="{1.6 if hi else 0.8}"/>')
        if hi:                          # 円の中に置く値は強調ひとつだけ（重なりを避ける）
            o.append(_t(cx, cy - r + 13, note, 10.5, AMB_INK, "middle", True))
    o.append(_t(cx, cy - rmax - 4, circles[0][2], 10.5, INK, "middle"))
    lx = w * .44
    for i, (lab, v, note, hi) in enumerate(circles):
        y = 26 + i * (h - 34) / len(circles)
        o.append(f'<rect x="{lx:.1f}" y="{y-9:.1f}" width="11" height="11" fill="{AMB if hi else (CRY25 if i==0 else (CRY55 if i==1 else CRY))}" stroke="{INK20}" stroke-width="0.6"/>')
        o.append(_t(lx + 17, y, lab, 10, INK, "start", hi))
        o.append(_t(lx + 17, y + 13, note, 11, AMB_INK if hi else INK60, "start", hi))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- tree
def tree(root, branches, w=980, h=250):
    """指標の親子関係（KPIドライバーツリー）。
    root: (ラベル, 値)。branches: [(ラベル, 値, [ (子ラベル, 子値) … ], 強調bool)]。"""
    rw, rh_ = 190, 52
    rx, ry = 8, h / 2 - rh_ / 2
    o = _open(w, h)
    o.append(f'<rect x="{rx}" y="{ry:.1f}" width="{rw}" height="{rh_}" fill="{INK}" rx="3"/>')
    o.append(_t(rx + rw / 2, ry + 21, root[0], 10.5, CRY, "middle"))
    o.append(_t(rx + rw / 2, ry + 40, root[1], 15, CRY25, "middle", True))
    bx, bw = rx + rw + 54, 232
    n = len(branches)
    bh = (h - 10) / n
    for i, (lab, val, kids, hi) in enumerate(branches):
        by = 5 + bh * i + (bh - 46) / 2
        o.append(f'<path d="M{rx+rw} {ry+rh_/2:.1f} C{rx+rw+26} {ry+rh_/2:.1f} {bx-26} {by+23:.1f} {bx} {by+23:.1f}" fill="none" stroke="{INK20}" stroke-width="1.2"/>')
        o.append(f'<rect x="{bx}" y="{by:.1f}" width="{bw}" height="46" fill="{AMB if hi else CRY}" rx="3"'
                 + (f' stroke="{AMB_LINE}" stroke-width="1.4"' if hi else "") + '/>')
        o.append(_t(bx + 10, by + 18, lab, 10.5, AMB_INK if hi else INK))
        o.append(_t(bx + bw - 10, by + 32, val, 13, AMB_INK if hi else INK, "end", True))
        kx = bx + bw + 40
        kw = w - kx - 8
        for j, (kl, kv) in enumerate(kids):
            ky = by + j * 23 + 2
            o.append(f'<path d="M{bx+bw} {by+23:.1f} C{bx+bw+18} {by+23:.1f} {kx-18} {ky+11:.1f} {kx} {ky+11:.1f}" fill="none" stroke="{INK20}" stroke-width="0.9"/>')
            o.append(f'<rect x="{kx}" y="{ky:.1f}" width="{kw}" height="21" fill="{CRY25}" rx="2"/>')
            o.append(_t(kx + 8, ky + 15, kl, 10, INK))
            o.append(_t(kx + kw - 8, ky + 15, kv, 10.5, INK, "end", True))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- bars_line
_hatch_id = "ci-est-hatch"


def bars_line(points, w=470, h=175, ylab="", y2lab="", bar_unit="M",
              break_at=None, break_label="観測断層", title=None):
    """棒＋折れ線の複合図（月次推移に自社シェアを重ねる、の定番）。

    points: [(x軸ラベル, 棒の値, 折れ線の値 or None, 棒が信頼できるか bool)]
      - 折れ線が None の月は**線を描かない**（点をつながず切る）＝観測が無い月をごまかさない
      - 棒の状態は3値。True＝正常／"warn" 等の真値＝要確認（実販売の減少か観測の欠落か
        切り分けられない）／False＝値として成立しない（提供元の納品崩壊・補正係数が未決着 等）
      - 要確認は**値の高さのまま琥珀の薄塗り＋破線**（実販売かもしれないので値を消さない）
      - 成立しない月は**高さを持たない全高の帯＋NA**（値の高さで描くと「売れなかった」と読まれる。
        独立レビュー astra 2026-09-09：棒の高さは色や破線より強く量を伝えるため、壊れた低値を
        描けば読者は注記より先に「急減した」と理解する）
      - "est" を渡すと**斜線ハッチ＋輪郭のみ**で描く＝観測ではなく推計。塗りを持たせないことで
        観測値の棒と一目で区別する（astra 2026-09-09：推計値を通常の棒で描くと観測事実として
        読まれる。区別は色だけに依存させず、斜線または白抜きにする）。
        **推計を使う側の責任**＝計算方法・仮定・感応度を図の外に明記し、見出しの数値には
        単独で算入しない（観測ベースを主値、推計算入を感応度として併記する）
    break_at: その位置に縦の破線を引く（データの断層・年度の境目など）。x軸ラベルの値で指定。
    """
    pad_l, pad_r, pad_t, pad_b = 34, 30, 16, 26
    n = len(points)
    bw = (w - pad_l - pad_r) / n
    bars = [p[1] for p in points]
    lns = [p[2] for p in points if p[2] is not None]
    ymax = (max(bars) or 1) * 1.14
    y2max = (max(lns) if lns else 1) * 1.30 or 1
    def X(i): return pad_l + bw * (i + .5)
    def Y(v): return h - pad_b - (h - pad_t - pad_b) * v / ymax
    def Y2(v): return h - pad_b - (h - pad_t - pad_b) * v / y2max
    o = _open(w, h)
    if any(p[3] == "est" for p in points):
        o.append(f'<defs><pattern id="{_hatch_id}" width="4" height="4" patternUnits="userSpaceOnUse" '
                 f'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" '
                 f'stroke="{AMB_LINE}" stroke-width="1.4"/></pattern></defs>')
    if title:
        o.append(_t(0, 10, title, 10.5, INK, "start", True))
    # 目盛り（左＝棒／右＝折れ線）
    has_line = bool(lns)
    for k in (0, .5, 1):
        v = ymax * k
        o.append(f'<line x1="{pad_l}" y1="{Y(v):.1f}" x2="{w-pad_r}" y2="{Y(v):.1f}" stroke="{INK20}" stroke-width="0.5"/>')
        o.append(_t(pad_l - 4, Y(v) + 3.5, f"{v:,.0f}", 8.5, INK60, "end"))
        if has_line:      # 折れ線が1点も無いときは右軸を描かない（意味のない目盛りを出さない）
            o.append(_t(w - pad_r + 4, Y2(y2max * k) + 3.5, f"{y2max*k:.0f}%", 8.5, INK60, "start"))
    for i, (lab, bv, lv, ok) in enumerate(points):
        x = pad_l + bw * i + bw * .16
        bwid = bw * .68
        y, hh = Y(bv), h - pad_b - Y(bv)
        if ok == "est":   # 推計＝斜線ハッチ＋輪郭のみ（塗りを持たせない＝観測と区別する）
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bwid:.1f}" height="{max(hh,0.8):.1f}" '
                     f'fill="url(#{_hatch_id})" stroke="{AMB_LINE}" stroke-width="1"/>')
        elif ok is True:
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bwid:.1f}" height="{max(hh,0.8):.1f}" fill="{CRY}"/>')
        elif ok:          # 要確認＝値の高さのまま琥珀の薄塗り＋破線（実販売かもしれないので消さない）
            o.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bwid:.1f}" height="{max(hh,0.8):.1f}" '
                     f'fill="{AMB}" fill-opacity="0.45" stroke="{AMB_LINE}" stroke-width="1" stroke-dasharray="2 2"/>')
        else:             # 成立しない月＝高さを持たない全高の帯＋NA（量として読ませない）
            o.append(f'<rect x="{x:.1f}" y="{pad_t:.1f}" width="{bwid:.1f}" height="{h-pad_b-pad_t:.1f}" '
                     f'fill="{AMB}" fill-opacity="0.16" stroke="{AMB_LINE}" stroke-width="1" stroke-dasharray="3 3"/>')
            o.append(_t(x + bwid / 2, (pad_t + h - pad_b) / 2 + 3, "NA", 8, AMB_LINE, "middle", True))
        if n <= 9 and ok:  # 値を出すのは成立している月だけ
            o.append(_t(x + bwid / 2, y - 4, f"{bv:,.0f}", 9, INK, "middle", ok is not True))
    # 折れ線（None の区間で切る）
    seg = []
    for i, (lab, bv, lv, ok) in enumerate(points):
        if lv is None:
            if len(seg) > 1:
                o.append(f'<polyline points="{" ".join(seg)}" fill="none" stroke="{INK}" stroke-width="1.8"/>')
            seg = []
            continue
        seg.append(f"{X(i):.1f},{Y2(lv):.1f}")
        o.append(f'<circle cx="{X(i):.1f}" cy="{Y2(lv):.1f}" r="2.4" fill="{INK}"/>')
    if len(seg) > 1:
        o.append(f'<polyline points="{" ".join(seg)}" fill="none" stroke="{INK}" stroke-width="1.8"/>')
    # 断層の縦線
    if break_at is not None:
        idx = [i for i, p in enumerate(points) if p[0] == break_at]
        if idx:
            bx = pad_l + bw * idx[0]
            o.append(f'<line x1="{bx:.1f}" y1="{pad_t-4}" x2="{bx:.1f}" y2="{h-pad_b}" stroke="{AMB_LINE}" stroke-width="1.3" stroke-dasharray="4 3"/>')
            o.append(_t(bx + 3, pad_t + 4, break_label, 8.5, AMB_INK))
    # x軸ラベルは年の頭だけ
    o.append(f'<line x1="{pad_l}" y1="{h-pad_b}" x2="{w-pad_r}" y2="{h-pad_b}" stroke="{INK20}"/>')
    every = (n <= 9)          # 点が少ないときは全部ラベルを出す
    for i, (lab, *_r) in enumerate(points):
        if every or str(lab).endswith("-01") or i == 0:
            o.append(_t(X(i), h - pad_b + 13, str(lab)[:7], 8.5 if every else 8.5, INK60, "middle"))
    if ylab: o.append(_t(0, h - 3, ylab, 8.5, INK60))
    if y2lab and lns: o.append(_t(w, h - 3, y2lab, 8.5, INK60, "end"))
    return "".join(o) + "</svg>"


# ---------------------------------------------------------------- 型見本（--demo）
DEMO = [
    ("mekko", "幅＝市場規模／高さ＝自社シェア。未出品の区分は琥珀の空き枠になる",
     lambda: mekko([("区分A", 55.5, 0.0, True, "出品なし"), ("区分B", 40.3, 17.9, False, ""),
                    ("区分C", 25.0, 25.0, False, ""), ("区分D", 24.7, 26.3, False, ""),
                    ("区分E", 21.1, 4.1, False, "")], h=210)),
    ("heatmap", "行×列の濃淡。琥珀＝洞察が言及するセル",
     lambda: heatmap(["〜999", "1,000–1,999", "2,000–2,999", "3,000–"],
                     [("区分A", [25, 57, 13, 5], "¥1,357"), ("区分B", [20, 49, 6, 25], "¥3,643"),
                      ("区分C", [31, 53, 15, 1], "¥1,701"), ("区分D", [43, 31, 4, 22], "¥2,567")],
                     h=180, hi_cells={(1, 3), (3, 2)})),
    ("funnel", "段階的な絞り込み。幅は下限25%なので比が大きくても文字が収まる",
     lambda: funnel([("登録", 1594, "", False), ("売上あり", 358, "22.5%", False),
                     ("主力", 13, "", True)], w=330, h=156)),
    ("bubble", "2軸＋大きさ。値が数倍〜十数倍に散るときは xlog=True",
     lambda: bubble([(5, 4.6, 3, "ブランドA", False), (6, 2.8, 4, "ブランドB", False),
                     (10, 10.5, 5, "ブランドC", False), (30, 25.4, 6, "自社", True),
                     (53, 2.5, 5, "ブランドD", False)], w=430, h=150, xlog=True,
                    xticks=(5, 10, 30, 53), xlab="ASIN数（対数）", ylab="月商（百万円）")),
    ("ranges", "低・中・高の幅と基準線。丸＝中央ケース",
     lambda: ranges([("今期 着地", 3.30, 3.67, 4.30, "必達の 94.9%"),
                     ("来期", 3.17, 3.74, 4.71, "今期比 102.0%")], h=104, ref=3.87, ref_label="必達 ¥3.87億")),
    ("waterfall", "増減の橋渡し。start＝濃紺／end＝琥珀",
     lambda: waterfall([("現状値", 30.02, "start"), ("追加", 2.26, "delta"), ("市場", -0.45, "delta"),
                        ("上限", -0.04, "delta"), ("廃盤", -0.88, "delta"), ("目標", 30.91, "end")],
                       w=560, h=168, note="単位は案件に合わせる")),
    ("slope", "時点間の推移。ラベルは自動で上下にずらす／上限は点線",
     lambda: slope([("区分A", [17.9, 18.9, 18.9], 26.7, True), ("区分B", [17.6, 19.1, 19.1], 31.5, True),
                    ("区分C", [25.0, 26.7, 26.7], 26.7, False)],
                   ["現在", "1年後", "2年後"], w=452, h=170)),
    ("concentric", "入れ子の市場（全体 ⊃ 対処可能 ⊃ 目標 ⊃ 現在）",
     lambda: concentric([("市場全体", 55.5, "¥55.5M", False), ("対処可能な範囲", 7.3, "¥7.3M", True),
                         ("目標", 0.97, "¥0.97M", False), ("現在", 0.049, "¥0.049M", False)], w=372, h=176)),
    ("bars_line", "棒＋折線。観測が無い月は線を切り、観測が薄い月は棒を中抜きにする",
     lambda: bars_line([("2025-01", 40, 19, True), ("2025-02", 26, 18, True), ("2025-03", 34, 19, True),
                        ("2025-04", 40, 17, True), ("2025-05", 39, None, False), ("2025-06", 37, 21, True),
                        ("2025-07", 57, 22, True), ("2025-08", 24, None, False), ("2025-09", 36, None, False),
                        ("2025-10", 39, None, False), ("2025-11", 14, None, False), ("2025-12", 14, 25, True),
                        ("2026-01", 21, 27, True), ("2026-02", 21, 25, True), ("2026-03", 30, 23, True),
                        ("2026-04", 23, 31, True)], w=470, h=175, break_at="2025-05",
                       title="例: 市場月商と自社シェア", ylab="市場 百万円", y2lab="自社シェア")),
    ("tree", "指標の親子関係（KPIドライバーツリー）",
     lambda: tree(("着地（中央ケース）", "¥3.67億"),
                  [("プライマリ指標", "3区分", [("区分A", "17.9% → 18.9%"), ("区分B", "25.0% → 26.7%")], True),
                   ("先行指標", "30 → 41", [("1件当たり", "上位25%以上")], False)], h=146)),
]


def demo(path="ci_frameworks_demo.html"):
    """9型の見本を1枚ずつ並べた HTML を書き出す（型選びの参考＋動作確認を兼ねる）。
    ci_head.py が同じディレクトリにあれば正典CSSを連結する。"""
    import pathlib
    import sys as _sys
    here = pathlib.Path(__file__).resolve().parent
    head = ""
    for cand in (here, here.parent):
        if (cand / "ci_head.py").exists():
            _sys.path.insert(0, str(cand))
            try:
                import ci_head
                head = ci_head.style_block()
            except Exception:
                pass
            break
    secs = []
    for name, desc, fn in DEMO:
        secs.append(
            f'<section class="slide"><div class="hdr"><p class="kicker">Framework ｜ {name}</p>'
            f'<h2 class="title">{name}</h2></div>'
            f'<p class="t-note">{desc}</p>{fn()}</section>')
    html = ('<!DOCTYPE html>\n<html lang="ja"><head><meta charset="UTF-8">\n'
            '<title>ci_frameworks 型見本</title>\n' + head + '\n</head><body>\n'
            + "\n".join(secs) + "\n</body></html>\n")
    pathlib.Path(path).write_text(html, encoding="utf-8")
    print(f"型見本を書き出しました: {path}（{len(DEMO)}型）")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        i = sys.argv.index("--demo")
        demo(sys.argv[i + 1] if len(sys.argv) > i + 1 else "ci_frameworks_demo.html")
    else:
        print(__doc__.strip())
        print("\n型見本を出す: python3 ci_frameworks.py --demo [out.html]")
