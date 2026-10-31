#!/usr/bin/env python3
"""[D] bgres: 元写真の背景色（灰色・中間調）の取り残し検出（2026-10-30, cutout_halo_check.py --bg-residue から呼ぶ）。
白フチ検査 [A][B][C] は「白っぽい」画素しか見ないため、ポンプの注ぎ口の隙間・手とボトルの間・肩の縁などに残った
灰色／中間調の元背景（半透明でも不透明でも）を見逃す。ここでは元写真 src を使って背景色を推定し、それに近い画素を拾う。

背景色の推定（2系統の和集合）:
  (1) 枠の画素: src の外周（幅 --bgr-border, 既定 3%）の画素をサンプル → 全体パレット
  (2) 近傍の背景: 切り抜きを src に自動で位置合わせ（倍率・平行移動を探索。不透明部は元画素のままなので一致する）できた場合、
      切り抜きで透明（alpha≤0.02）な場所の src の色＝その場所の本当の背景色。各画素の周囲 R px 以内の背景サンプル
対象画素: alpha>0.1 で、透明部から D px 以内（輪郭帯）か、閉じた穴（alpha>0.5 の穴埋めで囲まれた半透明部）にあるもの。
判定（画素ごと）: 背景サンプルとの最小色差 d_bg < T、かつ近傍の不透明な内側（人物・物）の画素との最小色差 d_fg が d_bg + M より大きい
  （＝人物・物の色では説明できず、背景の色で説明できる）、かつ灰色／中間調（彩度 max-min < 48, 40<輝度<--bgr-ymax=175。明るい色は白フチ検査 [B2] の担当、
  かつ白い物の陰影 ≒ 明るいベージュの背景、のような誤検出を避けるため）。原寸〜1/2 では 2x2 の opening で点・細線を除く。
  白い物と白い壁のように前景と背景が同色の所は d_fg も小さいので拾わない（白フチは [A][B][C] の担当）。
連結成分が --bgr-min px（面積比で縮小に追従, 下限16）以上で NG。
"""
import os, re, numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.signal import fftconvolve

LAST = {}
SRC_EXTS = (".jpg", ".jpeg", ".png", ".webp")

def _gray(a): return a[..., :3].astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)

def _resize(arr, w, h, mode=Image.BILINEAR):
    if arr.ndim == 2: return np.asarray(Image.fromarray(arr.astype(np.float32), "F").resize((w, h), mode))
    return np.asarray(Image.fromarray(arr.astype(np.uint8)).resize((w, h), mode)).astype(np.float32)

def _ssd_map(S, T, M):
    """masked SSD of template T (mask M) at every valid offset in S. returns (H-h+1, W-w+1) map / sum(M)."""
    h, w = T.shape
    TM = T * M
    c1 = (TM * T).sum()
    c2 = fftconvolve(S, TM[::-1, ::-1], mode="valid")
    c3 = fftconvolve(S * S, M[::-1, ::-1], mode="valid")
    return (c1 - 2 * c2 + c3) / max(M.sum(), 1)

def align(rgba, src_rgb):
    """切り抜き rgba を src に合わせる。戻り値 (scale, ox, oy, err) : target ≈ resize(src, scale)[oy:oy+h, ox:ox+w]。err=不透明部の平均絶対差(0-255)"""
    H, W = rgba.shape[:2]; SH, SW = src_rgb.shape[:2]
    m = ndi.binary_erosion(rgba[..., 3] >= 254, iterations=2)
    if m.sum() < 200: return None
    Tg = _gray(rgba); Sg = _gray(src_rgb)
    k = 160.0 / SW; Sc = _resize(Sg, max(8, round(SW * k)), max(8, round(SH * k)))
    best = (np.inf, 1, 0, 0)
    for s in np.geomspace(0.08, 1.05, 70):
        tw, th = round(W * k / s), round(H * k / s)
        if tw < 6 or th < 6 or tw > Sc.shape[1] or th > Sc.shape[0]: continue
        Tc = _resize(Tg, tw, th); Mc = (_resize(m.astype(np.float32), tw, th) > 0.99).astype(np.float32)
        if Mc.sum() < 10: continue
        d = _ssd_map(Sc, Tc, Mc); i = np.unravel_index(np.argmin(d), d.shape)
        if d[i] < best[0]: best = (d[i], s, i[1] / k * s, i[0] / k * s)
    if not np.isfinite(best[0]): return None
    _, s0, ox0, oy0 = best
    sub = 4  # 照合は 1/4 間引きの画素で（速度のため）
    mm = m[::sub, ::sub]
    res = (np.inf, s0, 0, 0)
    for span, n in ((0.05, 11), (0.01, 9), (0.002, 5)):
        c = res[1] if np.isfinite(res[0]) else s0
        grid = list(np.linspace(c * (1 - span), c * (1 + span), n)) + [v for v in (1.0, W / SW, 0.5) if abs(v - c) <= c * span]
        for s in grid:
            Sw, Sh = round(SW * s), round(SH * s)
            if Sw < W or Sh < H: continue
            Sr = _resize(Sg, Sw, Sh, Image.LANCZOS)
            if np.isfinite(res[0]): px, py = res[2] * s / res[1], res[3] * s / res[1]
            else: px, py = ox0 * s / s0, oy0 * s / s0
            mg = 8 if span >= 0.05 else 3
            x0 = int(np.clip(round(px) - mg, 0, Sw - W)); y0 = int(np.clip(round(py) - mg, 0, Sh - H))
            x1 = min(Sw, x0 + W + 2 * mg); y1 = min(Sh, y0 + H + 2 * mg)
            d = _ssd_map(Sr[y0:y1, x0:x1], Tg, m.astype(np.float32)); i = np.unravel_index(np.argmin(d), d.shape)
            if d[i] < res[0]: res = (d[i], s, x0 + i[1], y0 + i[0])
    _, s, ox, oy = res
    Sr = _resize(src_rgb, round(SW * s), round(SH * s), Image.LANCZOS)[oy:oy + H, ox:ox + W]
    err = float(np.abs(Sr - rgba[..., :3].astype(np.float32)).mean(-1)[m].mean())
    return s, int(ox), int(oy), err

def border_palette(src_rgb, frac=0.03, n=3000):
    SH, SW = src_rgb.shape[:2]; b = max(2, int(round(min(SH, SW) * frac)))
    fr = np.zeros((SH, SW), bool); fr[:b] = fr[-b:] = True; fr[:, :b] = fr[:, -b:] = True
    px = src_rgb[fr].reshape(-1, 3).astype(np.float32)
    rng = np.random.default_rng(0)
    return px[rng.choice(len(px), min(n, len(px)), replace=False)]

def src_candidates(target, src_args):
    """--src の指定から、この target の元写真候補を返す。指定形式: FILE / DIR / key=FILE（target のファイル名が key で始まる時だけ）。
    未指定なら target と同階層の ../src/ を見る。DIR からは「target 名の key（末尾の -幅, _vN, _nologo 等を除いた語幹）」を含むものだけ。"""
    base = os.path.basename(target).rsplit(".", 1)[0]
    key = re.sub(r"-\d+$", "", base)
    key = re.sub(r"(_v\d+[a-z]?(_\w+)?|_before|_rejected\w*)$", "", key)
    out = []
    specs = list(src_args) or [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(target))), "src")]
    for sp in specs:
        if "=" in sp:
            k, p = sp.split("=", 1)
            if base.startswith(k): out.append(p)
            continue
        if os.path.isdir(sp):
            out += sorted(os.path.join(sp, f) for f in os.listdir(sp) if f.lower().endswith(SRC_EXTS) and key in f)
        elif os.path.isfile(sp):
            out.append(sp)
    return out

def best_src(rgba, cands, max_err=10.0):
    """候補の中で位置合わせ誤差が最小のもの。戻り値 (path, src_rgb, (s,ox,oy,err) or None)"""
    best = None
    for p in cands:
        try: S = np.asarray(Image.open(p).convert("RGB")).astype(np.float32)
        except Exception: continue
        al = align(rgba, S)
        if al is None: continue
        if best is None or al[3] < best[2][3]: best = (p, S, al)
    if best is None:
        if cands:
            try: return cands[0], np.asarray(Image.open(cands[0]).convert("RGB")).astype(np.float32), None
            except Exception: pass
        return None, None, None
    if best[2][3] > max_err: return best[0], best[1], None   # 位置が合わない → 枠のパレットだけ使う
    return best

def residue(rgba, src_rgb, al_params, scale_rel=1.0, D=10, R=24, T=12.0, M=20.0, chroma=48, ymax=175, min_px=30, open_px=3, grow=40, gap=4, deep_r=64, border=0.03):
    """rgba: 検査する画像（縮小版も可）。al_params: 原寸 target に対する (s, ox, oy, err)。scale_rel: この画像の幅 / 原寸の幅。
    戻り値 (boxes, mask)"""
    H, W = rgba.shape[:2]
    a = rgba.astype(np.float32); rgb, al = a[..., :3], a[..., 3] / 255
    s2 = max(scale_rel * scale_rel, 0.02)
    d_ = max(2, int(round(D * scale_rel))); r_ = max(4, int(round(R * scale_rel))); mpx = max(16, int(round(min_px * s2)))
    transparent = al <= 0.02
    dist = ndi.distance_transform_edt(~transparent)
    solid = al > 0.5
    holes = ndi.binary_fill_holes(solid) & ~solid & (al > 0.1)
    Y = rgb @ np.array([0.299, 0.587, 0.114], np.float32); chrom = rgb.max(-1) - rgb.min(-1)
    seed_dom = (dist <= d_) | holes
    d2 = max(d_ + 1, int(round(grow * scale_rel)))
    # 取り残しが輪郭帯より厚い（ポンプの隙間に不透明で残った背景など）場合のため、grow px まで判定し、輪郭帯/穴につながる塊だけ採る
    cand = (al > 0.1) & ((dist <= d2) | holes) & (chrom < chroma) & (Y > 40) & (Y < ymax)
    ys, xs = np.nonzero(cand)
    mask = np.zeros((H, W), bool)
    if not len(ys): return [], mask
    P = rgb[ys, xs]
    # (1) 枠のパレット
    pal = border_palette(src_rgb, border)
    dbg = np.full(len(ys), np.inf, np.float32)
    for i in range(0, len(P), 4000):
        dd = np.sqrt(((P[i:i + 4000, None, :] - pal[None]) ** 2).sum(-1)).min(1); dbg[i:i + 4000] = dd
    # (2) 位置合わせできた時: 近傍の本当の背景
    if al_params is not None:
        s, ox, oy, _ = al_params; s *= scale_rel; ox *= scale_rel; oy *= scale_rel
        SH, SW = src_rgb.shape[:2]
        Sr = _resize(src_rgb, round(SW * s), round(SH * s), Image.LANCZOS)
        x0, y0 = int(round(ox)), int(round(oy))
        Sw = np.zeros((H, W, 3), np.float32); inb = np.zeros((H, W), bool)
        ys0, ys1 = max(0, -y0), min(H, Sr.shape[0] - y0); xs0, xs1 = max(0, -x0), min(W, Sr.shape[1] - x0)
        if ys1 > ys0 and xs1 > xs0:
            Sw[ys0:ys1, xs0:xs1] = Sr[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1]; inb[ys0:ys1, xs0:xs1] = True
        # 背景サンプルは、切り抜きの縁から gap px 以上離れた透明部だけ（縁のすぐ外の src 画素は人物と背景の混色なので使わない）
        bgok = transparent & inb & (ndi.distance_transform_edt(al <= 0.004) > max(1.5, gap * scale_rel))
        offs = [(dy, dx) for dy in range(-r_, r_ + 1, max(1, r_ // 8)) for dx in range(-r_, r_ + 1, max(1, r_ // 8)) if dy * dy + dx * dx <= r_ * r_]
        for dy, dx in offs:
            yy = np.clip(ys + dy, 0, H - 1); xx = np.clip(xs + dx, 0, W - 1)
            ok = bgok[yy, xx]
            dd = np.sqrt(((P - Sw[yy, xx]) ** 2).sum(-1)); dd[~ok] = np.inf
            dbg = np.minimum(dbg, dd)
    def min_dist(sample_ok, rad):
        out = np.full(len(ys), np.inf, np.float32)
        offs = [(dy, dx) for dy in range(-rad, rad + 1, max(1, rad // 8)) for dx in range(-rad, rad + 1, max(1, rad // 8)) if dy * dy + dx * dx <= rad * rad]
        for dy, dx in offs:
            yy = np.clip(ys + dy, 0, H - 1); xx = np.clip(xs + dx, 0, W - 1)
            dd = np.sqrt(((P - rgb[yy, xx]) ** 2).sum(-1)); dd[~sample_ok[yy, xx]] = np.inf
            out = np.minimum(out, dd)
        return out
    # 前景の見本は2段階:
    #  1) 深い内側（透明部から grow px 超）の不透明画素（半径 deep_r）。灰色の服・ニットの縁は、同じ服の内側で説明できるので拾わない
    #  2) 1) で説明できなかった背景色の画素（＝取り残し候補）を除いた、輪郭から d+2 px 超の不透明画素（半径 R）
    #     （ポンプの隙間に不透明で残った背景の塊が、自分自身を前景の見本にして見逃されるのを防ぐ）
    deep = (al >= 0.99) & (dist > d2)
    dfg_deep = min_dist(deep, max(8, int(round(deep_r * scale_rel))))
    sus = np.zeros((H, W), bool); f1 = (dbg < T) & (dfg_deep > dbg + M); sus[ys[f1], xs[f1]] = True
    dfg = np.minimum(dfg_deep, min_dist((al >= 0.99) & (dist > d_ + 2) & ~sus, r_))
    LAST.update(ys=ys, xs=xs, dbg=dbg, dfg=dfg, al=al)   # デバッグ用
    flag = (dbg < T) & (dfg > dbg + M)
    mask[ys[flag], xs[flag]] = True
    k = max(2, int(round(open_px * scale_rel)))
    if k >= 2:   # 細い帯・点（服や物の縁の陰影が偶然背景色に近いだけのもの）は落とす。取り残しは塊なので残る
        mask = ndi.binary_opening(mask, structure=np.ones((k, k)))
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    if n:
        ok = np.zeros(n + 1, bool); ok[np.unique(lab[mask & seed_dom])] = True; ok[0] = False
        mask = ok[lab]
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    boxes = []
    if n:
        sizes = ndi.sum(mask, lab, range(1, n + 1)); objs = ndi.find_objects(lab)
        keep = np.zeros(n + 1, bool)
        for i in range(n):
            if sizes[i] >= mpx:
                keep[i + 1] = True
                boxes.append((objs[i][1].start, objs[i][0].start, objs[i][1].stop - 1, objs[i][0].stop - 1, int(sizes[i])))
        mask = keep[lab]
    return boxes, mask
