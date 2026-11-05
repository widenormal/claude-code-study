#!/usr/bin/env python3
"""serp_page.py — Amazon検索順位の根拠ページ（SERP）を組み立てる共通ビルダー。

規定の正＝FIGURES_GUIDE.md §2-4。案件側はページ設定 yaml（雛形＝SERP_PAGE_TEMPLATE.yaml）
だけを書き、HTML・CSS はここが出す（案件側で CSS を作り直さない＝ドリフト禁止）。

組み方（1ページ）:
  ヘッダー  … ロゴだけ（ブランド｜モール）。キッカー文字は置かない
  見出し    … 読者の問いへの答え（「〜に入っている」。1回の観測なので「入った」とは書かない）
  要点      … 琥珀の「このページの要点」。根拠パネル（順位の内訳と出所）へのボタンを添える
  本体      … キーワードごとに**実物の検索結果の帯を1本**
               顧客の商品＝実線の枠＋順位バッジ（半透明の色を重ねない）
               スポンサー枠＝点線の枠＋「スポンサー n」
               行ラベル＝キーワード／順位／判定
  ギャップ枠… 上位 N 位の外のキーワードは、施策と対で右の枠に置く（施策が無ければ「施策（案）要確認」）
  注記      … 取得日時・Amazon.co.jp・ログアウトのPC・区まで・スポンサー枠を除く・要因は特定できない
  出所      … 「出所：Amazon.co.jp検索結果（取得日時・条件）」だけ（若松さん決定 2026-11-02）

数値は results.json（と serp_diff.py の前回比）だけから取る。設定 yaml の文言に
results.json に無い順位が書いてあれば**組み立てを止める**。

使い方:
  python3 serp_page.py page.yaml            # 設定どおりに HTML を書き出す
  python3 serp_page.py page.yaml --check    # 書き出さずに数値の突き合わせだけ
  python3 serp_page.py --selftest           # 合成データで一通り組んで検品まで通す
"""
from __future__ import annotations

import argparse
import base64
import datetime
import html as H
import json
import re
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_kit = next(d / "5co-CI-kit" for d in (_here, *_here.parents) if (d / "5co-CI-kit" / "VERSION").is_file()) \
    if any((d / "5co-CI-kit" / "VERSION").is_file() for d in (_here, *_here.parents)) else _here.parent.parent
sys.path.insert(0, str(_kit))
sys.path.insert(0, str(_here.parent))

import serp_diff
import serp_strips

OUTSIDE = "圏外"
DEFAULT_MEASURE = "施策（案）要確認"


# ---------------------------------------------------------------- データ
def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def client_ranks(term_rec):
    """[(asin, organic, sponsored, title)] を順位順に。"""
    rows = {}
    for c in term_rec.get("client_cards", []):
        d = rows.setdefault(c["asin"], {"organic": None, "sponsored": None, "title": c.get("title", "")})
        if c.get("organic_rank"):
            d["organic"] = min(d["organic"], c["organic_rank"]) if d["organic"] else c["organic_rank"]
        if c.get("sponsored_rank"):
            d["sponsored"] = min(d["sponsored"], c["sponsored_rank"]) if d["sponsored"] else c["sponsored_rank"]
    out = [(a, v["organic"], v["sponsored"], v["title"]) for a, v in rows.items()]
    out.sort(key=lambda r: (r[1] if r[1] else 10 ** 6, r[2] if r[2] else 10 ** 6))
    return out


def term_view(term_rec):
    """1キーワードぶんの見え方（順位・判定・帯にする段）をまとめる。"""
    thr = term_rec.get("top_threshold") or 10
    cr = client_ranks(term_rec)
    tops = [r for r in cr if r[1] and r[1] <= thr]
    sps = [r for r in cr if r[2]]
    best = min([r[1] for r in cr if r[1]], default=None)
    return {
        "term": term_rec["term"], "threshold": thr, "ranks": cr, "tops": tops, "sponsored": sps,
        "best": best, "in_top": bool(tops),
        "verdict": f"上位{thr}位内" if tops else f"上位{thr}位外",
        "fetched_at": term_rec.get("fetched_at", ""),
        "rank_text": "・".join(f"{r[1]}位" for r in tops) if tops else (f"{best}位" if best else OUTSIDE),
    }


def band_rows(term_rec, view, max_rows=2):
    """帯にする段を選ぶ＝顧客が上位に入っている段（＋顧客のスポンサー枠がある段）。"""
    rows = serp_strips.rows_of(term_rec.get("cards", []))
    want_org = {r[1] for r in view["tops"]}
    want_sp = {r[2] for r in view["sponsored"]}
    picked = []
    for row in rows:
        if any(c.get("sponsored_rank") in want_sp for c in row) or any(c.get("organic_rank") in want_org for c in row):
            picked.append(row)
    return picked[:max_rows]


# ---------------------------------------------------------------- 数値の突き合わせ
RE_RANK = re.compile(r"(\d+)\s*位")


def verify_numbers(texts, results, extra_ok=()):
    """文言に出てくる「n位」が results.json にある順位（か上位 N 位の閾値）かを確かめる。"""
    ok = set(extra_ok)
    for t in results.get("terms", []):
        ok.add(t.get("top_threshold") or 10)
        for c in t.get("client_cards", []):
            for k in ("organic_rank", "sponsored_rank"):
                if c.get(k):
                    ok.add(c[k])
    bad = []
    for label, text in texts:
        for n in RE_RANK.findall(text or ""):
            if int(n) not in ok:
                bad.append(f"{label}: 「{n}位」は results.json に無い")
    return bad


# ---------------------------------------------------------------- HTML
def uri(path, mime=None):
    p = Path(path)
    mime = mime or {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".svg": "image/svg+xml", ".webp": "image/webp"}.get(p.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def jp_datetime(s):
    """'2026-11-02 04:43:48 JST' → '2026年11月2日 4:43時点'"""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})", s or "")
    if not m:
        return s or ""
    y, mo, d, hh, mi = m.groups()
    return f"{int(y)}年{int(mo)}月{int(d)}日 {int(hh)}:{mi}時点"


def cond_text(cfg):
    return f"ログアウトのPC・届け先は{cfg['area']}"


def source_line(at_jp, cfg):
    """このページ型の出所はこの形だけ（若松さん決定 2026-11-02）。"""
    return f"出所：Amazon.co.jp検索結果（{at_jp}・{cond_text(cfg)}）"


def note_line(at_jp, cfg):
    return (f"{at_jp}。Amazon.co.jp、ログアウト状態のPC、届け先は{cfg['area']}。"
            "スポンサー広告枠を除いた順位。順位の要因は、このデータからは特定できない。")


CSS = """
<style id="ci-serp-page">
/* Amazon検索順位の根拠ページ（SERP）— 5co-CI-kit serp/serp_page.py。案件側で作り直さない */
.cl-logo{height:28px; width:auto; display:block; align-self:center;}
.hdr .hdr-logos{display:flex; align-items:flex-start; flex:none; height:28px; gap:0;}
.hdr .hdr-logos .cl-logo{align-self:flex-start;}
section.slide .hdr .hdr-div{display:block; flex:none; width:1px; height:18px; margin:5px 12px 0 4px; border:0 !important; background:var(--ink-60) !important;}
.hdr .mall-logo{display:block; height:24px; width:auto; margin-top:7px; flex:none;}
.sx-an{display:inline-block; padding:0 6px; font-size:.86em; font-weight:700; border:1px dashed var(--ink-60); border-radius:3px; color:var(--ink-85); white-space:nowrap;}
/* 検索結果の帯（スクリーンショットに色を重ねない） */
.sv{display:grid; gap:18px; margin-top:4px; align-items:start; width:100%;}
.sv-col{min-width:0;}
.gist .gb{display:block; padding-left:1em; text-indent:-1em;}
.gist .gb::before{content:"・";}
.sv-lb{display:flex; flex-wrap:wrap; gap:4px 14px; margin:0 0 5px; padding-bottom:3px; border-bottom:2px solid var(--ink); align-items:baseline;}
.sv-lb > div{display:flex; align-items:baseline; gap:5px; min-width:0;}
.sv-lb dt{font-size:10px; color:var(--ink-60); white-space:nowrap;}
.sv-lb dd{margin:0; font-size:13.5px; font-weight:700; color:var(--ink); white-space:nowrap;}
.sv-lb dd b{font-size:16px;}
.sv-lb dd .sv-d{font-size:11px; font-weight:700; color:var(--ink-85); margin-left:2px;}
.sv-lb-v{display:block; border-bottom:0; margin:6px 0 8px;}
.sv-lb-v > div{justify-content:space-between; padding:2px 0; border-bottom:1px solid var(--ink-14);}
.sv-r{margin-top:6px;}
.sv-bar{display:block; width:100%; height:auto; border:1px solid var(--ink-14);}
.sv-row{display:block; width:100%; height:auto; border:1px solid var(--ink-14);}
.sv-gap{border:1px solid var(--ink-14); border-radius:6px; background:var(--white); padding:10px 12px 12px;}
.sv-gt{margin:4px 0 6px; font-size:13px; font-weight:700; color:var(--ink); line-height:1.35;}
.sv-gt .nw, h2.title .nw{white-space:nowrap;}
.sv-thumb{display:block; width:100%; height:auto; border:1px solid var(--ink-14);}
.sv-gap .ci-ev-btn{font-size:10.5px;}
/* ダイジェスト（画面のみ）: 帯は各キーワード1段だけにし、ギャップ枠は要点に書いてあるので外す */
html:not(.ci-static) section.slide[data-page-mode="digest"] > .fig[data-fig="serp"]{align-items:flex-start !important; padding:0 !important; margin-top:10px !important;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .fig[data-fig="serp"] .sv{grid-template-columns:repeat(var(--sv-cols,2), minmax(0,1fr)) !important; gap:22px;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .fig[data-fig="serp"] .sv-gap{display:none;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .fig[data-fig="serp"] .sv-dg-off{display:none;}
</style>"""


def build(cfg, base_dir, write=True):
    """設定（dict）からページを組む。(html, report) を返す。"""
    import ci_head
    import ci_interactive as ci

    base = Path(base_dir)
    res = load(base / cfg["results"])
    prev = load(base / cfg["prev_results"]) if cfg.get("prev_results") else None
    dif = serp_diff.diff(prev, res) if prev else None
    if dif and not dif["same_conditions"]:
        raise SystemExit("前回と条件が違うので前回比を出せない（届け先・端末・ログイン状態をそろえる）")
    recs = {t["term"]: t for t in res["terms"]}
    order = cfg.get("terms") or list(recs)
    views = {t: term_view(recs[t]) for t in order if t in recs}
    missing = [t for t in order if t not in recs]
    if missing:
        raise SystemExit(f"results.json に無いキーワード: {missing}")

    at_jp = jp_datetime(res.get("started_at", ""))
    shots = Path(cfg.get("shots_dir") or (base / cfg["results"]).parent)
    figs = base / cfg.get("figs_dir", "figs/serp")
    figs.mkdir(parents=True, exist_ok=True)
    scale = float(cfg.get("scale", 1.0))
    asins = {a for v in views.values() for a, *_ in v["ranks"]}

    # --- 前回比（キーワード×ASIN）
    delta = {}
    if dif:
        for r in dif["rows"]:
            delta[(r["term"], r["asin"])] = r

    def short_delta(d):
        """順位の右に出す前回比。↑n／↓n／→／圏外の出入り。"""
        if not d:
            return ""
        if d["delta"] is None:          # 圏外の出入り
            return "↑圏外から" if d["symbol"] == "↑" else "↓圏外へ"
        return "→" if d["delta"] == 0 else f"{d['symbol']}{abs(d['delta'])}"

    def rank_html(term):
        """「4位 →・6位 ↓4」。前回データが無ければ順位だけ。"""
        v = views[term]
        rows = v["tops"] or ([(None, v["best"], None, "")] if v["best"] else [])
        if not rows:
            return OUTSIDE
        out = []
        for a, o, _sp, _t in rows:
            d = short_delta(delta.get((term, a))) if dif else ""
            out.append(f"{o}位" + (f'<span class="sv-d">{d}</span>' if d else ""))
        return "・".join(out)

    # --- 帯（上位に入っているキーワード）
    cols, bands_meta = [], []
    for term in order:
        v = views[term]
        if not v["in_top"]:
            continue
        rows = band_rows(recs[term], v, max_rows=int(cfg.get("max_rows", 2)))
        if not rows:
            continue
        tag = f"t{order.index(term) + 1:02d}"
        imgs = []
        fp = shots / recs[term]["shots"]["fullpage"]
        for i, row in enumerate(rows):
            out = figs / f"{tag}_band{i + 1}.jpg"
            serp_strips.band(fp, row, asins, out, height=int(cfg.get("band_height", 400)), scale=scale)
            alt = f"検索語「{term}」の検索結果（{serp_strips.row_label(row)}）"
            imgs.append((out, alt))
        head_img = None
        if cfg.get("search_bar", True) and recs[term]["shots"].get("viewport"):
            head_img = figs / f"{tag}_searchbar.jpg"
            serp_strips.header_strip(shots / recs[term]["shots"]["viewport"], head_img,
                                     recs[term].get("header_box"), scale=scale)
        ranks_attr = ",".join([str(r[1]) for r in v["tops"]] + [f"SP{r[2]}" for r in v["sponsored"]])
        rs = "".join(
            f'<div class="sv-r{" sv-dg-off" if i else ""}">'
            f'<img class="sv-row" src="{uri(p)}" alt="{H.escape(alt)}"></div>'
            for i, (p, alt) in enumerate(imgs))
        bar = (f'<img class="sv-bar" src="{uri(head_img)}" '
               f'alt="Amazon.co.jp 検索画面の検索窓（検索語「{H.escape(term)}」）">' if head_img else "")
        cols.append(
            f'<div class="sv-col" data-serp-shot data-serp-term="{H.escape(term)}" data-serp-rank="{ranks_attr}">'
            f'<dl class="sv-lb">'
            f'<div><dt>キーワード</dt><dd>{H.escape(term)}</dd></div>'
            f'<div><dt>{H.escape(cfg.get("rank_label", "順位"))}</dt><dd><b>{rank_html(term)}</b></dd></div>'
            f'<div><dt>判定</dt><dd>{v["verdict"]}</dd></div></dl>{bar}{rs}</div>')
        bands_meta.append({"term": term, "ranks": ranks_attr, "rows": len(rows)})

    # --- ギャップ枠（上位の外のキーワード）
    gaps = []
    for term in order:
        v = views[term]
        if v["in_top"]:
            continue
        measure = (cfg.get("measures") or {}).get(term) or DEFAULT_MEASURE
        best_card = None
        for c in recs[term].get("cards", []):
            if c.get("organic_rank") == v["best"]:
                best_card = c
                break
        th = ""
        if best_card:
            tp = figs / f"gap_{re.sub(r'[^0-9A-Za-z]+', '', best_card['asin'])}.jpg"
            serp_strips.thumb(shots / recs[term]["shots"]["fullpage"], best_card, tp, scale=scale)
            th = (f'<img class="sv-thumb" src="{uri(tp)}" '
                  f'alt="検索語「{H.escape(term)}」でオーガニック{v["best"]}位の商品カード">')
        dh = ""
        gaps.append(
            f'<aside class="sv-gap" data-serp-shot data-serp-term="{H.escape(term)}" '
            f'data-serp-rank="{v["best"] or OUTSIDE}">'
            f'<p class="sv-gt">次のギャップ：<span class="nw">「{H.escape(term)}」</span>'
            f'{v["rank_text"]} → <span class="sx-an">{H.escape(measure)}</span></p>{th}'
            f'<dl class="sv-lb sv-lb-v">'
            f'<div><dt>キーワード</dt><dd>{H.escape(term)}</dd></div>'
            f'<div><dt>{H.escape(cfg.get("rank_label", "順位"))}</dt><dd><b>{v["rank_text"]}</b>{dh}</dd></div>'
            f'<div><dt>判定</dt><dd>{v["verdict"]}</dd></div></dl>'
            f'{ci.ev_button("ev-" + cfg.get("page_id", "p01"), "順位の内訳と出所 ›")}</aside>')

    # --- 根拠パネル（順位の内訳と出所）
    head = ["キーワード", cfg.get("rank_label", "順位"), "スポンサー", "判定", "取得（JST）"]
    if dif:
        head.insert(2, "前回比")
    trs = ""
    for term in order:
        v = views[term]
        sp = "・".join(f"スポンサー {r[2]}" for r in v["sponsored"]) or "—"
        cells = [H.escape(term), v["rank_text"]]
        if dif:
            d = next((delta.get((term, a)) for a, *_ in v["ranks"] if delta.get((term, a))), None)
            cells.append(f"{d['symbol']} {d['change_label']}" if d else "—")
        cells += [sp, v["verdict"], (v["fetched_at"] or "")[11:16]]
        trs += "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"
    table = "<table><tr>" + "".join(f"<th>{h}</th>" for h in head) + "</tr>" + trs + "</table>"
    # 根拠パネルのタブは2つまで（ci_interactive の規定）。前回比は内訳の列＋1行の説明で見せる
    dnote = ""
    if dif:
        dnote = (f'<p>前回比＝前回 {H.escape(dif["prev"]["started_at"])} → '
                 f'今回 {H.escape(dif["curr"]["started_at"])}（同じ条件で取得）。'
                 f'上がった {dif["summary"]["up"]}件／下がった {dif["summary"]["down"]}件／'
                 f'変わらず {dif["summary"]["unchanged"]}件。{OUTSIDE}＝検索結果の先頭ページに出ていない。</p>')
    tabs = [("内訳", table + dnote),
            ("出所と前提", f'<p data-vocab-exempt="このページ型の注記（語句を変えない）">{H.escape(note_line(at_jp, cfg))}</p>')]
    pid = cfg.get("page_id", "p01")
    ev = ci.ev_panel(f"ev-{pid}", cfg.get("crumb", "Amazon検索の順位"), cfg["judge"], tabs,
                     src=source_line(at_jp, cfg))

    # --- 数値の突き合わせ（results.json に無い順位は書かせない）
    checks = [("見出し", cfg["title"]), ("要点", " ".join(cfg["gist"])), ("判定文", cfg["judge"])]
    checks += [(f"施策（{k}）", v) for k, v in (cfg.get("measures") or {}).items()]
    bad = verify_numbers(checks, res)
    if bad:
        raise SystemExit("数値が results.json と合わない:\n  " + "\n  ".join(bad))

    gist = "".join(f'<span class="gb">{H.escape(g)}</span>' for g in cfg["gist"])
    n_cols = len(cols)
    grid = f"grid-template-columns:{'minmax(0,1fr) ' * n_cols}{'168px' if gaps else ''};--sv-cols:{max(1, n_cols)};"
    note = cfg.get("read_note") or (
        "図の読み方: 検索結果を段ごとに切り出し、自社商品に黒枠を付けた。実線の数字＝オーガニック順位"
        "（スポンサーの掲載枠を除く）、点線＝スポンサー（広告・順位に数えない）。"
        + ("順位の右の記号＝前回比（↑＝上がった・↓＝下がった・→＝変わらず）。" if dif else ""))
    section = f"""<section class="slide" id="{pid}" data-serp-page="1"
 data-serp-at="{H.escape(res.get('started_at',''))}" data-serp-cond="{H.escape(cond_text(cfg))}">
<svg class="corner" viewBox="0 0 50.857 36.507"><use href="#lk"/></svg>
<div class="hdr"><span class="hdr-logos"><img class="cl-logo" src="{uri(base / cfg['brand_logo'])}" alt="{H.escape(cfg['brand_name'])}"><span class="hdr-div" aria-hidden="true"></span><img class="mall-logo" src="{uri(base / cfg['mall_logo'])}" alt="{H.escape(cfg.get('mall_name','Amazon'))}"></span></div>
<h2 class="title">{cfg['title_html'] if cfg.get('title_html') else H.escape(cfg['title'])}</h2><div class="accent-bar"></div>
<p class="gist"><span class="gist-k">このページの要点</span><span class="gist-t">{gist}</span></p>
<p class="t-note">{H.escape(note)}</p>
<div class="fig ci-fig" data-fig="serp"><div class="sv" style="{grid}">{''.join(cols)}{''.join(gaps)}</div></div>
{ev}
<p class="note-line"><span data-vocab-exempt="このページ型の注記（語句を変えない）">{H.escape(note_line(at_jp, cfg))}</span>　{H.escape(source_line(at_jp, cfg))}</p>
</section>"""

    tpl = (Path(_kit) / "5co_slide_template.html").read_text(encoding="utf-8")
    lk = re.search(r'<svg width="0" height="0"[^>]*>.*?</svg>', tpl, re.S).group(0)
    page = (f'<!DOCTYPE html>\n<html lang="ja">\n<head>\n<meta charset="UTF-8">\n'
            f'<meta name="viewport" content="width=1280, initial-scale=1">\n'
            f'<title>{H.escape(cfg.get("doc_title", cfg["title"]))}</title>\n'
            f'{ci_head.style_block(interactive=True)}\n{CSS}\n</head>\n<body>\n{lk}\n{section}\n</body>\n</html>\n')

    # 出所ルール（Amazon.co.jp だけ）・郵便番号・外部画像はビルド時にも落とす
    import serp_check
    errs, _ = serp_check.check_html(page, str(cfg.get("out", "(メモリ)")))
    if errs:
        raise SystemExit("SERP ページの検品で落ちた:\n  " + "\n  ".join(errs))

    report = {"terms": {t: {k: views[t][k] for k in ("rank_text", "verdict", "best", "in_top")} for t in order},
              "bands": bands_meta, "gaps": [g["term"] for g in [{"term": t} for t in order if not views[t]["in_top"]]],
              "diff": dif["summary"] if dif else None, "source": source_line(at_jp, cfg)}
    if write:
        out = base / cfg["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
        report["out"] = str(out)
    return page, report


def build_file(path, write=True):
    import yaml
    p = Path(path).resolve()
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    return build(cfg, p.parent, write=write)


# ---------------------------------------------------------------- selftest
def _fake_run(dirpath, day, ranks, sponsored=()):
    """合成の results.json と fullpage/viewport PNG を作る（Amazon に触れない）。"""
    from PIL import Image, ImageDraw
    d = Path(dirpath); d.mkdir(parents=True, exist_ok=True)
    terms = []
    for ti, (term, rk) in enumerate(ranks.items(), 1):
        im = Image.new("RGB", (1366, 2400), (245, 245, 245)); dr = ImageDraw.Draw(im)
        cards, o, s = [], 0, 0
        sp_for = dict(sponsored).get(term, {})
        for r, y in enumerate((215, 912, 1581)):
            for i, x in enumerate((284, 551, 819, 1086)):
                dr.rectangle((x, y, x + 268, y + 600), fill=(255, 255, 255), outline=(210, 210, 210))
                is_sp = r == 0 and sp_for
                if is_sp:
                    s += 1; rank_o, rank_s = None, s
                else:
                    o += 1; rank_o, rank_s = o, None
                asin = sp_for.get(rank_s) if is_sp else rk.get(rank_o)
                cards.append({"asin": asin or f"X{r}{i}", "x": x, "y": y, "w": 268, "h": 600,
                              "organic_rank": rank_o, "sponsored_rank": rank_s, "is_client": bool(asin),
                              "title": asin or "other"})
        im.save(d / f"t{ti:02d}_fullpage.png")
        Image.new("RGB", (1366, 900), (20, 24, 32)).save(d / f"t{ti:02d}_viewport.png")
        cc = [{"asin": c["asin"], "organic_rank": c["organic_rank"], "sponsored_rank": c["sponsored_rank"],
               "sponsored_how": [], "badges": [], "asin_listed": True, "title": c["asin"]}
              for c in cards if c["is_client"]]
        terms.append({"term": term, "fetched_at": f"{day} 04:43:0{ti} JST", "top_threshold": 10,
                      "client_cards": cc, "best_client_organic_rank": min([c["organic_rank"] for c in cc if c["organic_rank"]], default=None),
                      "shots": {"viewport": f"t{ti:02d}_viewport.png", "fullpage": f"t{ti:02d}_fullpage.png"},
                      "cards": cards})
    res = {"client": "テスト", "started_at": f"{day} 04:42:54 JST", "finished_at": f"{day} 04:43:48 JST",
           "conditions": {"login": "none", "postal": "105-0003", "device": "pc",
                          "viewport": {"width": 1366, "height": 900}, "locale": "ja-JP", "timezone": "Asia/Tokyo"},
           "terms": terms}
    (d / "results.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    return d / "results.json"


def selftest():
    import tempfile
    from PIL import Image
    import serp_check
    t = Path(tempfile.mkdtemp(prefix="serp_page_"))
    prev = _fake_run(t / "d1", "2026-11-01", {"語A": {2: "B001", 4: "B002"}, "語B": {7: "B003"}, "語C": {12: "B004"}},
                     sponsored=[("語A", {3: "B001"})])
    curr = _fake_run(t / "d2", "2026-11-02", {"語A": {4: "B001", 6: "B002"}, "語B": {6: "B003"}, "語C": {11: "B004"}},
                     sponsored=[("語A", {3: "B001"})])
    Image.new("RGBA", (120, 40), (0, 0, 0, 255)).save(t / "brand.png")
    (t / "mall.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="80" height="24"></svg>', encoding="utf-8")
    cfg = {
        "page_id": "p01", "out": "out.html", "results": str(curr), "prev_results": str(prev),
        "shots_dir": str(curr.parent), "figs_dir": "figs/serp", "scale": 0.5,
        "brand_logo": "brand.png", "mall_logo": "mall.svg", "brand_name": "テストブランド", "mall_name": "Amazon",
        "area": "東京都港区", "rank_label": "順位",
        "title": "Amazon検索の順位｜「語A」で4位・6位、「語B」で6位に自社商品が入っている",
        "doc_title": "テスト",
        "gist": ["一般キーワード2語で、自社商品はオーガニック順位の上位10位に入っている（語A 4位・6位／語B 6位）。",
                 "次のギャップは「語C」（11位、上位10位の外）。施策（案）要確認。"],
        "judge": "上位10位内は「語A」「語B」の2語。「語C」は11位で上位10位外。",
        "measures": {},
    }
    html, rep = build(cfg, t)
    assert rep["terms"]["語A"]["rank_text"] == "4位・6位", rep["terms"]["語A"]
    assert rep["terms"]["語C"]["in_top"] is False
    assert rep["diff"]["rows"] == 4, rep["diff"]
    assert "スポンサー 3" in html or "SP3" in html, "スポンサー枠の表示が無い"
    assert "前回比" in html, "前回比が出ていない"
    assert "施策（案）要確認" in html, "施策の既定文が無い"
    assert "出所：Amazon.co.jp検索結果（2026年11月2日 4:42時点" in html, "出所の形が違う"
    assert "105-0003" not in html, "郵便番号がページに出ている"
    print("  ✔ 組み立て（帯・スポンサー枠・ギャップ枠・前回比・出所）")
    e, w = serp_check.check_html(html, "selftest.html", today=datetime.date(2026, 11, 2))
    assert not e and not w, (e, w)
    print("  ✔ serp_check が 0 件（エラー・警告とも）")
    # 数値が合わなければ止まる
    bad = dict(cfg, title="Amazon検索の順位｜「語A」で1位に入っている", out="bad.html")
    try:
        build(bad, t, write=False)
        raise AssertionError("results.json に無い順位で止まらなかった")
    except SystemExit as ex:
        assert "1位" in str(ex), ex
    print("  ✔ results.json に無い数値で組み立てが止まる")
    # 条件が違う2回は前回比を出さない
    p2 = json.loads(Path(prev).read_text(encoding="utf-8"))
    p2["conditions"]["postal"] = "100-0001"
    (t / "d1" / "other.json").write_text(json.dumps(p2, ensure_ascii=False), encoding="utf-8")
    try:
        build(dict(cfg, prev_results=str(t / "d1" / "other.json"), out="x.html"), t, write=False)
        raise AssertionError("条件違いで止まらなかった")
    except SystemExit as ex:
        assert "条件が違う" in str(ex), ex
    print("  ✔ 条件が違う前回データでは前回比を出さない")
    # 出所ルール: 事業者名・推計の手口を書こうとしたら組み立てが止まる
    # （「Shelpha」は 2026-11-03 の若松さん決定で書いてよい＝ここでは止めない。
    #   このページ型の出所の行は E2 が「Amazon.co.jp検索結果（…）」だけを許すので規定は変わらない）
    for word in ("DMT", "Acorn-i", "Ignite", "AMZ-POS", "推計"):
        try:
            build(dict(cfg, measures={"語C": f"{word}の数字で判断"}, out="ng.html"), t, write=False)
            raise AssertionError(f"{word} で止まらなかった")
        except SystemExit as ex:
            assert "検品で落ちた" in str(ex), (word, ex)
    print("  ✔ 出所に書けない語（DMT・Acorn-i・Ignite・AMZ-POS・推計）で組み立てが止まる")
    print("serp_page selftest: OK")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", help="ページ設定 yaml")
    ap.add_argument("--check", action="store_true", help="書き出さずに数値の突き合わせだけ")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not a.config:
        ap.error("ページ設定 yaml を指定してください")
    html, rep = build_file(a.config, write=not a.check)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    sys.exit(0)


if __name__ == "__main__":
    main()
