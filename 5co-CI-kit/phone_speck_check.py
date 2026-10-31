#!/usr/bin/env python3
# phone_speck_check.py — スマホ周りの浮いた点・細線（低 alpha の取り残し）検品（5co-CI-kit・2026-10-30）
# 人物素材でスマホを持つものは納品前に OK にする（FIGURES_GUIDE.md §2-2「人物素材の標準」9）。
# --box はスマホの範囲（--ref-w 幅の座標系。既定値はタクシーのコンサル v8〔幅 861〕のスマホ位置）。素材ごとに指定する。
# 終了コード: すべて OK 0／NG あり 1。出所＝CIスライド qa_tools（qa_out/v7）。
"""Check for thin isolated low-alpha lines/specks around the phone.
usage: phone_speck_check.py a.png [b.png ...] [--box 480,400,650,640] [--ref-w 861]
NG if, inside the box (scaled from 861-wide coords):
 - orphan: an alpha>lo connected component contains no opaque (>=hi) pixel (floating speck/line), or
 - detached: a semi pixel farther than --dist px from the opaque body is NOT on a monotonic ramp, i.e. none of its
   8-neighbours closer to the body has alpha >= 0.9*own (a line hanging beyond a transparent gap). Normal soft
   edges (alpha falling off away from the body) pass.
"""
import argparse, numpy as np
from PIL import Image
from scipy import ndimage as ndi
ap = argparse.ArgumentParser(); ap.add_argument('pngs', nargs='+')
ap.add_argument('--box', default='480,400,650,640'); ap.add_argument('--ref-w', type=int, default=861)
ap.add_argument('--lo', type=float, default=0.02); ap.add_argument('--hi', type=float, default=0.9)
ap.add_argument('--dist', type=float, default=2.0)
o = ap.parse_args(); ng = 0
for p in o.pngs:
    a = np.array(Image.open(p).convert('RGBA'))[..., 3] / 255.; s = a.shape[1] / o.ref_w
    x0, y0, x1, y1 = [int(round(v * s)) for v in map(int, o.box.split(','))]
    # pad by 4px so components/distances near the box border see their context
    X0, Y0 = max(x0 - 4, 0), max(y0 - 4, 0); sub = a[Y0:y1 + 4, X0:x1 + 4]
    opaque = sub >= o.hi; semi = (sub > o.lo) & ~opaque
    dist = ndi.distance_transform_edt(~opaque)
    far = semi & (dist > o.dist)
    ok = np.zeros_like(far); P = np.pad(sub, 1); D = np.pad(dist, 1, constant_values=1e9)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == dx == 0: continue
            na = P[1 + dy:1 + dy + sub.shape[0], 1 + dx:1 + dx + sub.shape[1]]; nd = D[1 + dy:1 + dy + sub.shape[0], 1 + dx:1 + dx + sub.shape[1]]
            ok |= (nd < dist - 0.3) & (na >= 0.9 * sub - 0.005)
    far &= ~ok
    lab, n = ndi.label(sub > o.lo, np.ones((3, 3)))
    has_op = np.zeros(n + 1, bool); has_op[np.unique(lab[opaque])] = True
    orphan = (lab > 0) & ~has_op[lab]
    inner = np.zeros_like(far); inner[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    far &= inner; orphan &= inner
    bad = far | orphan; k = int(bad.sum())
    msg = 'OK ' if k == 0 else 'NG '; ng += k > 0
    extra = ''
    if k:
        ys, xs = np.nonzero(bad); extra = ' bbox=(%d,%d)-(%d,%d) rows=%s' % (xs.min() + X0, ys.min() + Y0, xs.max() + X0, ys.max() + Y0,
                                                                         sorted(set((ys + Y0).tolist()))[:12])
    print('%s %s  detached=%d orphan=%d%s' % (msg, p, int(far.sum()), int(orphan.sum()), extra))
print('--- %d files: NG %d' % (len(o.pngs), ng)); raise SystemExit(1 if ng else 0)
