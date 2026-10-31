#!/usr/bin/env python3
"""cutout_halo_check.py — 切り抜き人物PNGの白フチ（ハロー）検出（5co-CI-kit・2026-10-30 強化版）

なぜ要るか
  白い背景を色で抜いた切り抜きは、髪の毛先などの半透明部分や頬・耳の横に元の白が残る。
  白地のページでは見えないため、目視でもあふれ・重なりゲートでも見逃していた
  （5co.ltd「ECと店頭」記事の ec_c01_phone_browse 左肩の髪・2026-10-30 若松さん指摘）。

判定（どれか1つでも塊があれば HALO?）
  [A] edge : 輪郭の帯（透明から --band px 以内）の白っぽい画素で、すぐ内側が暗い（髪など）塊が
             --min-cluster px 以上。縮小判定（元幅の半分未満）では使わない（白い襟の誤検出防止）。
  [B] blob : 白地の取り残し。背景の白に近い不透明画素の塊で、透明部に接し、周囲の過半が髪・肌のもの
             （--min-blob px 以上・大きさの上限なし＝帯より太い塊も拾う）。旧デフリンジで灰色に塗られた
             平坦な無彩色の塊も拾う。服サイズの明色領域（不透明面積の --cloth-frac 以上）や周囲が服の塊は
             対象外（白ブラウス・クリームのニット・白Tを誤検出しない）。
  [C] ink  : 濃紺 #101820 に合成し、輪郭の明るさがすぐ内側の不透明部より --margin 以上明るい塊
             （半透明の白い縁・色の脱汚染をしていない毛先・暗い背景で光るフチ）。
  --resize W1,W2,... を付けると、各幅に普通の（非プリマルチプライの）縮小をかけてから再検査する
  （alpha=0 の画素の RGB が白のままだと、サイト側の縮小で白線が出る。alpha bleed 済みなら通る。
   元幅以上の値は無視）。素材の受け渡し前は --resize 1152,813,406,284,142 を推奨。
  デッキ HTML 内の画像では、幅か高さが 1px の塊（グラフの線・ロゴの水平/垂直の縁）と [C] ink は数えない
  （白地で抜いたロゴのアンチエイリアスが濃紺合成で光るだけの誤検知を防ぐ）。素材 PNG／フォルダでは正本どおり全部数える。
  [D] bgres（--bg-residue を付けた時だけ・2026-10-30 v3。付けなければ従来と同じ出力＝ci-gates 互換）:
             元写真（--src、未指定なら <alpha の親>/../src/ の同名系）に自動で位置合わせして背景色を推定し、
             輪郭帯（透明から --bgr-dist px 以内）か閉じた穴の中に残った「背景色に近く、前景の色では説明できない」
             中間調の塊（--bgr-min px 以上）を NG にする（灰色・茶系の背景の取り残しは白フチ [A][B][C] では見えない）。
             本体＝cutout_bg_residue.py。元写真が見つからない画像は「bgres SKIP」と表示するだけ（--bgr-require-src で NG）。
             デッキ HTML 内の画像には元写真が無いので bgres は掛けない（素材 PNG／フォルダだけ）。
  検出ロジックの正本＝CIスライド qa_tools/cutout_halo_check.py v3（HALO_CHECK_HARDENING・BG_RESIDUE_CHECK・2026-10-30）。

使い方
  cutout_halo_check.py <png | dir | deck.html> [...] [--band 3] [--min-cluster 40] [--min-blob 12]
                       [--margin 0.16] [--cloth-frac 0.015] [--resize 1152,813,406,284,142]
                       [--out dir] [--warn-only] [--json] [--selftest]
                       [--bg-residue [--src FILE|DIR|key=FILE ...] [--bgr-dist 10] [--bgr-tol 12]
                                     [--bgr-margin 20] [--bgr-min 30] [--bgr-ymax 175] [--bgr-require-src]]
  dir は png/webp/avif/gif/tif を検査（開けない形式は SKIP）。
  deck.html を渡すと <img src> のローカル PNG と data:image/png を、透過を持つものだけ検査する。
  --out を付けると、濃紺背景に重ねて edge=赤／blob=マゼンタ／ink=橙（／bgres=シアン）で塗った確認用 PNG を書き出す。
  人物素材の納品前: --resize 1152,813,725,406,362,284,142 --bg-residue ＋目視（背景と服・肌が同色だと色では拾えない）。
  終了コード: 問題なし 0／HALO? あり 1（--warn-only なら 0）／入力エラー 2。最終行は「…: OK」か件数。
"""
import argparse, base64, io, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

# ---- 検出ロジック（CIスライド v2 と同一。変更する時は正本と揃える） ----
INK = np.array([16, 24, 32], np.float32) / 255
EXTS = (".png", ".webp", ".avif", ".gif", ".tif", ".tiff")

def lum(rgb): return rgb @ np.array([0.2126, 0.7152, 0.0722], np.float32)

def boxes_of(mask, min_px, cap=None):
    lab, n = ndi.label(mask, structure=np.ones((3, 3)))
    if not n: return [], lab, []
    sizes = ndi.sum(mask, lab, range(1, n + 1)); objs = ndi.find_objects(lab)
    keep = [i for i in range(n) if sizes[i] >= min_px]
    return [(objs[i][1].start, objs[i][0].start, objs[i][1].stop - 1, objs[i][0].stop - 1, int(sizes[i])) for i in keep], lab, [i + 1 for i in keep]

def analyse(rgba, band=3, min_cluster=40, min_blob=12, margin=0.16, cloth_frac=0.015, scale=1.0):
    """rgba: uint8 HxWx4. 戻り値 dict(check -> list of boxes), 各マスク"""
    a = rgba.astype(np.float32) / 255; rgb, al = a[..., :3], a[..., 3]
    s2 = max(scale * scale, 0.02)
    mcl = max(12, int(round(min_cluster * s2))); mbl = max(6, int(round(min_blob * s2)))
    bnd = max(1, int(round(band * max(scale, 0.5))))
    transparent = al <= 0.1; opaque = al > 0.1
    near_tr = ndi.binary_dilation(transparent, iterations=bnd)
    edge = opaque & near_tr
    mx, mn = rgb.max(-1), rgb.min(-1); Y = lum(rgb)
    res, masks = {}, {}
    # [A] 旧版
    whiteish = (mx > 200 / 255) & ((mx - mn) < 30 / 255)
    dark_in = ndi.binary_dilation(opaque & ~near_tr & (Y < 90 / 255), iterations=bnd + 3)
    mA = edge & whiteish & dark_in
    # 旧検査は小さく縮小した時（scale<0.5）は使わない（白い襟などが暗い服と1〜2pxで接して誤検出するため。縮小時は [B][C] で見る）
    if scale < 0.5: mA = np.zeros_like(mA)
    res["edge"], _, _ = boxes_of(mA, mcl); masks["edge"] = mA
    # [B] 白地の取り残し（大きさ不問）
    solid = al > 0.5
    bgw = solid & (mn > 222 / 255) & ((mx - mn) < 20 / 255)
    touch = ndi.binary_dilation(transparent, iterations=2)
    # 服サイズ判定は「ゆるい明色領域」の連結成分で行う（明るい服は縮小やシワで細切れになるため）
    light = solid & (mn > 185 / 255) & ((mx - mn) < 32 / 255)
    llab, ln = ndi.label(light, structure=np.ones((3, 3)))
    lsize = np.concatenate([[0], ndi.sum(light, llab, range(1, ln + 1))]) if ln else np.zeros(1)
    def clothish(comp_mask_full_idx, opaque_area):
        ids = np.unique(llab[comp_mask_full_idx]); ids = ids[ids > 0]
        return len(ids) and lsize[ids].max() > cloth_frac * opaque_area
    lab, n = ndi.label(bgw, structure=np.ones((3, 3)))
    mB = np.zeros_like(bgw); boxesB = []
    if n:
        sizes = ndi.sum(bgw, lab, range(1, n + 1)); objs = ndi.find_objects(lab)
        touching = set(np.unique(lab[touch & bgw])) - {0}
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        skin = solid & (r > g) & (g > b) & ((r - b) > 0.06) & ((r - b) < 0.40) & (Y > 0.30) & (Y < 0.92) & ~bgw
        hair = solid & (Y < 0.35)
        opaque_area = max(solid.sum(), 1)
        for i in touching:
            sz = sizes[i - 1]
            if sz < mbl or sz > cloth_frac * opaque_area: continue
            sl = tuple(slice(max(s.start - 8, 0), s.stop + 8) for s in objs[i - 1])
            comp = lab[sl] == i
            if clothish(tuple(np.add(np.nonzero(comp), [[sl[0].start], [sl[1].start]])), opaque_area): continue
            ring = ndi.binary_dilation(comp, iterations=6) & ~comp & solid[sl] & ~bgw[sl]
            nr = ring.sum()
            if nr < 4: 
                # 周りに人物画素がほぼ無い＝宙に浮いた白い塊 → NG
                frac = 1.0
            else:
                frac = (hair[sl][ring].sum() + skin[sl][ring].sum()) / nr
            if frac >= 0.5:
                mB[sl] |= comp; ys, xs = np.where(comp)
                boxesB.append((int(xs.min() + sl[1].start), int(ys.min() + sl[0].start), int(xs.max() + sl[1].start), int(ys.max() + sl[0].start), int(sz)))
    # [B2] 白地の取り残しが灰色に塗られた塊（旧デフリンジ後に残る、平坦な明るい無彩色）。小さめの塊だけ・周囲が髪/肌・平坦
    flat = ndi.uniform_filter(Y, 5); flat = np.sqrt(np.maximum(ndi.uniform_filter(Y * Y, 5) - flat * flat, 0)) < 0.03
    neu = solid & (mn > 150 / 255) & ((mx - mn) < 14 / 255)
    lab2, n2 = ndi.label(neu, structure=np.ones((3, 3)))
    if n2:
        sizes2 = ndi.sum(neu, lab2, range(1, n2 + 1)); objs2 = ndi.find_objects(lab2)
        r_, g_, b_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        skin2 = solid & (r_ > g_) & (g_ > b_) & ((r_ - b_) > 0.06) & ((r_ - b_) < 0.40) & (Y > 0.30) & (Y < 0.92)
        hair2 = solid & (Y < 0.30) & ~flat   # 髪は質感がある（平坦な紺の上着などは除外）
        opaque_area = max(solid.sum(), 1)
        for i in set(np.unique(lab2[touch & neu])) - {0}:
            sz = sizes2[i - 1]
            if sz < 3 * mbl or sz > 0.003 * opaque_area: continue
            sl = tuple(slice(max(q.start - 8, 0), q.stop + 8) for q in objs2[i - 1])
            comp = lab2[sl] == i
            if clothish(tuple(np.add(np.nonzero(comp), [[sl[0].start], [sl[1].start]])), opaque_area): continue
            per = comp & ~ndi.binary_erosion(comp)
            if (per & touch[sl]).sum() < 0.15 * max(per.sum(), 1): continue
            ring = ndi.binary_dilation(comp, iterations=6) & ~comp & solid[sl] & ~neu[sl]
            nr = ring.sum()
            if nr < 4: continue
            hf = hair2[sl][ring].sum() / nr; sf = skin2[sl][ring].sum() / nr
            if hf >= 0.5 and hf + sf >= 0.6:
                mB[sl] |= comp; ys, xs = np.where(comp)
                boxesB.append((int(xs.min() + sl[1].start), int(ys.min() + sl[0].start), int(xs.max() + sl[1].start), int(ys.max() + sl[0].start), int(sz)))
    res["blob"] = boxesB; masks["blob"] = mB
    # [C] #101820 合成で輪郭が内側より明るい
    comp_rgb = rgb * al[..., None] + INK * (1 - al[..., None]); Yc = lum(comp_rgb)
    dist = ndi.distance_transform_edt(~transparent)
    inner = (al > 0.98) & (dist > bnd) & (dist <= bnd + 8 * max(scale, 0.5))
    # すぐ内側（半径 bnd+5）の不透明部の「最も明るい値」を基準にする（平均だと、明るい物体の縁が暗い服の隣にあるだけで誤検出する）
    r = int(round(bnd + 5 * max(scale, 0.5)))
    ref = ndi.maximum_filter(np.where(inner, Yc, -1.0), size=2 * r + 1)
    ref = np.where(ref < 0, np.nan, ref)
    rim = opaque & (dist <= max(2, bnd - 1))
    with np.errstate(invalid="ignore"):
        mC = rim & (Yc - ref > margin) & (Yc > 0.35)
    res["ink"], _, _ = boxes_of(mC, mcl); masks["ink"] = mC
    return res, masks

def resize_np(rgba, w):
    """非プリマルチプライの普通の縮小（RGB と A を別々に）。"""
    h = max(1, round(rgba.shape[0] * w / rgba.shape[1]))
    rgb = Image.fromarray(rgba[..., :3]).resize((w, h), Image.LANCZOS)
    a = Image.fromarray(rgba[..., 3]).resize((w, h), Image.LANCZOS)
    return np.dstack([np.asarray(rgb), np.asarray(a)])

# ---- ここからキット側（入力・1px線の除外・出力・selftest） ----

def deck_filter(res, masks, in_deck=True):
    """デッキ HTML 内の画像だけの除外（素材 PNG／フォルダでは何も除外しない＝CIスライド正本と同じ判定）。
    ・幅か高さが 1px の塊（グラフの線・ロゴの水平/垂直の縁）
    ・[C] ink（デッキにはロゴ等の白地アンチエイリアス画像が混ざり、濃紺合成では縁が光るが白地スライドでは見えないため）
    除外したものは確認画像からも消す。"""
    out = {}
    for k, boxes in res.items():
        if in_deck and k == "ink":
            masks[k][:] = False; continue
        keep = []
        for b in boxes:
            x0, y0, x1, y1, _ = b
            if in_deck and (x0 == x1 or y0 == y1):
                masks[k][y0:y1 + 1, x0:x1 + 1] = False
            else:
                keep.append(b)
        if keep: out[k] = keep
    return out


def debug_png(rgba, masks, path):
    im = Image.fromarray(rgba, "RGBA"); bg = Image.new("RGBA", im.size, (16, 24, 32, 255)); bg.alpha_composite(im)
    c = np.asarray(bg).copy()
    for k, col in (("edge", (255, 0, 0, 255)), ("blob", (255, 0, 255, 255)), ("ink", (255, 160, 0, 255)), ("bgres", (0, 255, 255, 255))):
        if k in masks: c[masks[k]] = col
    Image.fromarray(c).save(path)


def check_rgba(rgba, o, name=None, in_deck=False):
    """rgba: uint8 HxWx4。戻り値 [(tag, 幅, {check: boxes})]（boxes が空のものも含む）。"""
    if not (rgba[..., 3] <= 25).any():
        return []                                    # 透過の無い画像は対象外
    variants = [("orig", rgba, 1.0)]
    for w in o.resize:
        if w < rgba.shape[1]: variants.append((f"w{w}", resize_np(rgba, w), w / rgba.shape[1]))
    results = []
    bgr = None
    if getattr(o, "bg_residue", False) and not in_deck and name:
        # [D] bgres（--bg-residue の時だけ）。デッキ内の画像は元写真が無いので対象外
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import cutout_bg_residue as BR
        sp, S, alp = BR.best_src(rgba, BR.src_candidates(name, o.src))
        if S is None:
            o._notes.append(f"bgres SKIP {name}（元写真なし）")
            if o.bgr_require_src: results.append(("orig", rgba.shape[1], {"bgres-nosrc": [(0, 0, 0, 0, 0)]}))
        else:
            bgr = (BR, S, alp)
            o._notes.append(f"bgres src {os.path.basename(name)} <- {os.path.basename(sp)} "
                            + (f"scale={alp[0]:.4f} off=({alp[1]},{alp[2]}) err={alp[3]:.2f}" if alp else "位置合わせ不可→外周パレットのみ"))
    for tag, arr, sc in variants:
        res, masks = analyse(arr, o.band, o.min_cluster, o.min_blob, o.margin, o.cloth_frac, sc)
        if bgr:
            BR, S, alp = bgr
            res["bgres"], masks["bgres"] = BR.residue(arr, S, alp, sc, D=o.bgr_dist, T=o.bgr_tol, M=o.bgr_margin,
                                                      ymax=o.bgr_ymax, min_px=o.bgr_min)
        bad = deck_filter(res, masks, in_deck)
        results.append((tag, arr.shape[1], bad))
        if bad and o.out and name:
            os.makedirs(o.out, exist_ok=True)
            stem = re.sub(r"[^\w-]+", "_", re.sub(r"\.(png|webp|avif|gif|tiff?|html?)$", "", os.path.basename(name), flags=re.I))
            debug_png(arr, masks, os.path.join(o.out, f"{stem}_halo_{tag}.png"))
    return results


IMG_RE = re.compile(r'<img\b[^>]*?\bsrc\s*=\s*["\']([^"\']+)["\']', re.I)


def targets(target):
    """(表示名, 開く関数, デッキ内の画像か) を返す。開けないものは呼び出し側で SKIP。"""
    if os.path.isdir(target):
        for f in sorted(os.listdir(target)):
            if f.lower().endswith(EXTS):
                p = os.path.join(target, f); yield p, (lambda p=p: Image.open(p)), False
        return
    if target.lower().endswith((".html", ".htm")):
        html = open(target, encoding="utf-8", errors="ignore").read(); base = os.path.dirname(os.path.abspath(target))
        seen = set()
        for k, src in enumerate(IMG_RE.findall(html)):
            if src in seen: continue
            seen.add(src)
            if src.startswith("data:image/png;base64,"):
                yield f"{os.path.basename(target)}#img{k+1}(data:png)", (lambda s=src: Image.open(io.BytesIO(base64.b64decode(s.split(",", 1)[1])))), True
            elif src.lower().split("?")[0].endswith(".png") and not re.match(r"^[a-z]+:", src, re.I):
                p = os.path.normpath(os.path.join(base, src.split("?")[0]))
                if os.path.isfile(p): yield p, (lambda p=p: Image.open(p)), True
        return
    yield target, (lambda: Image.open(target)), False


def selftest_bgres():
    """[D] bgres の selftest（--selftest --bg-residue の時だけ）。灰色背景の元写真から切り抜いた円で、
    輪郭に背景の灰色を不透明で残すと bgres、きれいに抜けば OK、元写真が無ければ SKIP（--bgr-require-src なら NG）。"""
    import tempfile
    o = argparse.Namespace(band=3, min_cluster=40, min_blob=12, margin=0.16, cloth_frac=0.015, resize=[], out=None,
                           bg_residue=True, src=[], bgr_dist=10, bgr_tol=12.0, bgr_margin=20.0, bgr_min=30, bgr_ymax=175,
                           bgr_require_src=False, _notes=[])
    h = w = 320; yy, xx = np.ogrid[:h, :w]; r2 = (yy - 160) ** 2 + (xx - 160) ** 2
    disk = r2 < 110 ** 2
    rng = np.random.default_rng(1)
    src = np.empty((h, w, 3), np.uint8); src[:] = (122, 118, 112)                 # 中間調の灰色の背景
    tex = (np.sin(xx / 7.0) * np.cos(yy / 9.0) * 25).astype(np.int16)
    fg = np.stack([200 + tex, 150 + tex, 120 + tex // 2], -1) + rng.integers(-6, 7, (h, w, 3))
    src[disk] = np.clip(fg, 0, 255).astype(np.uint8)[disk]                    # 模様のある肌色の円（位置合わせ用）
    tmp = tempfile.mkdtemp(prefix="halo_bgres_"); sp = os.path.join(tmp, "src.png"); Image.fromarray(src).save(sp)
    def cut(extra=None):
        a = np.zeros((h, w, 4), np.uint8); a[..., :3] = src; a[..., 3] = np.where(disk, 255, 0)
        if extra is not None: a[extra, 3] = 255
        a[a[..., 3] == 0, :3] = (200, 150, 120)                                   # alpha bleed（縮小でも白線を出さない）
        return a
    def bad(rgba, **kw):
        oo = argparse.Namespace(**{**vars(o), **kw}); oo._notes = []
        return {k for _, _, b in check_rgba(rgba, oo, name=os.path.join(tmp, "x.png")) for k in b}
    ok = {}
    ok["bgres:clean=OK"] = not bad(cut(), src=[sp])
    notch = (yy >= 40) & (yy < 62) & (xx >= 150) & (xx < 172) & ~disk         # 円の上端に背景の灰色を不透明で残す
    ok["bgres:residue=HALO?"] = "bgres" in bad(cut(notch), src=[sp])
    ok["bgres:nosrc=SKIP"] = not bad(cut(notch), src=[os.path.join(tmp, "none")])
    ok["bgres:require-src=HALO?"] = bool(bad(cut(notch), src=[os.path.join(tmp, "none")], bgr_require_src=True))
    print("selftest " + " ".join(f"{k}:{v}" for k, v in ok.items()))
    return all(ok.values())


def selftest(bg_residue=False):
    o = argparse.Namespace(band=3, min_cluster=40, min_blob=12, margin=0.16, cloth_frac=0.015, resize=[], out=None)
    h = w = 160
    yy, xx = np.ogrid[:h, :w]; r2 = (yy - 80) ** 2 + (xx - 80) ** 2
    disk = r2 < 60 ** 2
    def base(bg_rgb=(16, 24, 32)):
        a = np.zeros((h, w, 4), np.uint8); a[..., :3] = bg_rgb
        a[disk] = (30, 25, 20, 255); return a       # 暗い髪の円
    def bad(rgba, **kw):
        deck = kw.pop("in_deck", False); oo = argparse.Namespace(**{**vars(o), **kw})
        return {k for _, _, b in check_rgba(rgba, oo, in_deck=deck) for k in b}
    ok = {}
    ok["clean=OK"] = not bad(base())
    a = base(); a[disk & ~(r2 < 58 ** 2) & (xx < 80)] = (245, 245, 245, 255)
    ok["edge=HALO?"] = "edge" in bad(a)                # 左半分の輪郭2pxに白フチ
    a = base(); a[(yy >= 20) & (yy < 30) & (xx >= 74) & (xx < 86) & (r2 < 60 ** 2)] = (250, 250, 250, 255)
    ok["blob=HALO?"] = "blob" in bad(a)                # 上端に帯(3px)より太い白い塊（深さ約9px）
    # 縮小でだけ出る白フチ: 髪の束のすき間（透明）の RGB が白のまま（alpha bleed なし）
    big = 600; yy2, xx2 = np.ogrid[:big, :big]; d2 = (yy2 - 300) ** 2 + (xx2 - 300) ** 2 < 250 ** 2
    d2 &= ((xx2 + yy2) % 40) >= 5                     # 斜めのすき間（幅約3px）
    a = np.zeros((big, big, 4), np.uint8); a[..., :3] = 255; a[d2] = (30, 25, 20, 255)
    ok["resize:orig=OK"] = not bad(a)
    ok["resize:w406=HALO?"] = bool(bad(a, resize=[1152, 406]))   # 1152 は元幅以上なので無視される
    a[~d2, :3] = (30, 25, 20)                         # alpha bleed 済みなら縮小しても OK
    ok["resize:bleed=OK"] = not bad(a, resize=[1152, 406, 284, 142])
    # デッキ内の画像では幅1pxの白線（グラフの線など）は数えない（素材 PNG としては拾う）
    a = base(); a[80, 10:150] = (250, 250, 250, 255)
    ok["deck:1px-line=OK"] = not bad(a, in_deck=True)
    ok["png:1px-line=HALO?"] = bool(bad(a))
    print("selftest " + " ".join(f"{k}:{v}" for k, v in ok.items()))
    good = all(ok.values())
    if bg_residue: good = selftest_bgres() and good
    return 0 if good else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*"); ap.add_argument("--band", type=int, default=3)
    ap.add_argument("--min-cluster", type=int, default=40); ap.add_argument("--min-blob", type=int, default=12)
    ap.add_argument("--margin", type=float, default=0.16); ap.add_argument("--cloth-frac", type=float, default=0.015)
    ap.add_argument("--resize", default="", help="例: 1152,813,406,284,142（元幅以上の値は無視）")
    ap.add_argument("--out")
    ap.add_argument("--warn-only", action="store_true"); ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    # [D] bgres（v3・2026-10-30）。付けなければ従来と同じ出力
    ap.add_argument("--bg-residue", action="store_true", help="[D] 元写真の背景色（灰色・中間調）の取り残し検査を追加")
    ap.add_argument("--src", nargs="*", default=[], help="元写真: FILE / DIR / key=FILE（target 名が key で始まる時）")
    ap.add_argument("--bgr-dist", type=int, default=10, help="輪郭帯の幅 px（原寸）")
    ap.add_argument("--bgr-tol", type=float, default=12.0, help="背景色との色差の上限（RGB 0-255 のユークリッド）")
    ap.add_argument("--bgr-margin", type=float, default=20.0, help="前景色との色差が背景色との色差よりこれ以上大きいこと")
    ap.add_argument("--bgr-min", type=int, default=30, help="NG にする塊の最小 px（原寸。縮小時は面積比・下限16）")
    ap.add_argument("--bgr-ymax", type=float, default=175, help="対象にする輝度の上限（0-255・中間調まで）")
    ap.add_argument("--bgr-require-src", action="store_true", help="元写真が見つからない画像を NG にする")
    o = ap.parse_args(); o._notes = []
    if o.selftest: sys.exit(selftest(bg_residue=o.bg_residue))
    try: o.resize = [int(v) for v in o.resize.split(",") if v.strip()]
    except ValueError:
        print(f"❌ --resize は幅の整数をカンマ区切りで: {o.resize}", file=sys.stderr); sys.exit(2)
    if not o.targets:
        print("❌ 入力を指定してください: cutout_halo_check.py <png | dir | deck.html>", file=sys.stderr); sys.exit(2)
    for t in o.targets:
        if not os.path.exists(t):
            print(f"❌ 入力が見つかりません: {t}", file=sys.stderr); sys.exit(2)
    bad = n = nskip = 0
    for t in o.targets:
        for name, opener, in_deck in targets(t):
            try:
                im = opener(); im.load(); rgba = np.asarray(im.convert("RGBA"))
            except Exception as e:
                nskip += 1
                if o.json: print(json.dumps({"file": name, "skip": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
                else: print(f"SKIP  {name}  （開けない: {type(e).__name__}: {e}）")
                continue
            n += 1
            nn = len(o._notes)
            results = check_rgba(rgba, o, name, in_deck=in_deck)
            notes = o._notes[nn:]
            bads = [(tg, w, b) for tg, w, b in results if b]
            if o.json:
                rec = {"file": name, "ok": not bads, "checked": [f"{tg}(w={w})" for tg, w, _ in results],
                       "halos": [{"at": tg, "w": w, "check": k, "x0": x0, "y0": y0, "x1": x1, "y1": y1, "px": s}
                                 for tg, w, b in bads for k, v in b.items() for x0, y0, x1, y1, s in v]}
                if o.bg_residue and notes: rec["bgres"] = "; ".join(notes)   # --bg-residue の時だけ（無しなら従来と同じ JSON）
                print(json.dumps(rec, ensure_ascii=False))
            if not bads: continue
            bad += 1
            if not o.json:
                for tg, w, b in bads:
                    msg = "; ".join(f"{k}:{len(v)}か所[" + ", ".join(f"x{x0}-{x1},y{y0}-{y1}({s}px)" for x0, y0, x1, y1, s in v[:3]) + "]" for k, v in b.items())
                    print(f"HALO? {name}  @{tg}(w={w})  {msg}")
    if not o.json:
        for n_ in o._notes: print("  # " + n_)   # --bg-residue の時だけ（元写真の対応・SKIP）
        sk = f"・SKIP {nskip}" if nskip else ""
        rs = f"・縮小 {','.join(map(str, o.resize))}" if o.resize else ""
        if nskip or o.resize: print(f"（検査 {n}枚{rs}{sk}）")
        # 最終行は ci-gates.sh が「: OK」終わりで判定するので形を変えない
        print(f"切り抜き白フチ（{n}枚）: OK" if not bad else f"切り抜き白フチ: HALO? {bad}/{n}枚{rs}{sk}（--out で確認画像: edge赤／blobマゼンタ／ink橙" + ("／bgresシアン" if o.bg_residue else "") + "）")
    sys.exit(0 if (not bad or o.warn_only) else 1)


if __name__ == "__main__":
    main()
