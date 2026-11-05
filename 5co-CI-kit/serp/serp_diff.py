#!/usr/bin/env python3
"""serp_diff.py — 同じ条件で撮った2回分の results.json を突き合わせ、キーワード×商品の前回比を出す。

規定の正＝FIGURES_GUIDE.md §2-4「Amazon検索順位の根拠ページ（SERP）」。

出すもの（キーワード×ASIN ごと）:
  前回順位 / 今回順位 / 前回比（↑n・↓n・→・圏外の出入り）と、両方の取得日時。
  順位は**スポンサー枠を除いたオーガニック順位**だけを比べる（広告枠は別列に出す）。
  「圏外」＝その回の検索結果（1ページ目）にその商品が出ていない。

条件が違う2回は比べない（届け先・端末・ログイン状態・画面幅が違えば順位は動く）。
既定では条件が違うと落ちる（--allow-cond-diff で警告にできる）。

使い方:
  python3 serp_diff.py prev/results.json curr/results.json
  python3 serp_diff.py prev/results.json curr/results.json --json
  python3 serp_diff.py prev/results.json curr/results.json --md      # 表（qa/ に残す用）
  python3 serp_diff.py --selftest

終了: 0=OK / 1=条件が違う / 2=引数誤り
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 条件がそろっているか見るキー（これが違う2回は順位を比べない）
COND_KEYS = ("login", "postal", "device", "viewport", "locale", "timezone")
OUT = "圏外"   # その回の検索結果（1ページ目）に出ていない


def _terms(res):
    return {t["term"]: t for t in res.get("terms", [])}


def _ranks(term_rec):
    """ASIN -> {organic, sponsored, title}（同じ ASIN が広告と自然で2回出ることがある）"""
    out = {}
    for c in term_rec.get("client_cards", []):
        d = out.setdefault(c["asin"], {"organic": None, "sponsored": None, "title": c.get("title", "")})
        if c.get("organic_rank"):
            d["organic"] = c["organic_rank"] if d["organic"] is None else min(d["organic"], c["organic_rank"])
        if c.get("sponsored_rank"):
            d["sponsored"] = c["sponsored_rank"] if d["sponsored"] is None else min(d["sponsored"], c["sponsored_rank"])
    return out


def change(prev, curr):
    """(記号, 文言, 差) を返す。prev/curr は順位（int）か None（圏外）。"""
    if prev is None and curr is None:
        return "→", f"{OUT}のまま", None
    if prev is None:
        return "↑", f"{OUT}→{curr}位", None
    if curr is None:
        return "↓", f"{prev}位→{OUT}", None
    d = prev - curr          # 数字が小さいほど上位なので、減ったら上がった
    if d > 0:
        return "↑", f"＋{d}", d
    if d < 0:
        return "↓", f"−{-d}", d
    return "→", "変わらず", 0


def cond_of(res):
    c = res.get("conditions", {})
    return {k: c.get(k) for k in COND_KEYS}


def diff(prev_res, curr_res):
    """2つの results.json（辞書）から前回比をまとめる。"""
    pt, ct = _terms(prev_res), _terms(curr_res)
    rows = []
    for term in list(ct) + [t for t in pt if t not in ct]:
        pr = _ranks(pt[term]) if term in pt else {}
        cr = _ranks(ct[term]) if term in ct else {}
        for asin in list(cr) + [a for a in pr if a not in cr]:
            p = pr.get(asin, {}); c = cr.get(asin, {})
            sym, label, d = change(p.get("organic"), c.get("organic"))
            rows.append({
                "term": term, "asin": asin,
                "title": c.get("title") or p.get("title") or "",
                "prev_rank": p.get("organic"), "curr_rank": c.get("organic"),
                "prev_sponsored": p.get("sponsored"), "curr_sponsored": c.get("sponsored"),
                "symbol": sym, "change_label": label, "delta": d,
                "prev_fetched_at": pt.get(term, {}).get("fetched_at"),
                "curr_fetched_at": ct.get(term, {}).get("fetched_at"),
            })
    rows.sort(key=lambda r: (r["term"], r["curr_rank"] if r["curr_rank"] else 10 ** 6, r["asin"]))
    up = sum(1 for r in rows if r["symbol"] == "↑")
    down = sum(1 for r in rows if r["symbol"] == "↓")
    same = sum(1 for r in rows if r["symbol"] == "→")
    return {
        "prev": {"started_at": prev_res.get("started_at"), "finished_at": prev_res.get("finished_at"),
                 "conditions": cond_of(prev_res)},
        "curr": {"started_at": curr_res.get("started_at"), "finished_at": curr_res.get("finished_at"),
                 "conditions": cond_of(curr_res)},
        "same_conditions": cond_of(prev_res) == cond_of(curr_res),
        "summary": {"rows": len(rows), "up": up, "down": down, "unchanged": same},
        "rows": rows,
    }


def _rank(v):
    return f"{v}位" if v else OUT


def to_text(d, md=False):
    p, c = d["prev"], d["curr"]
    ls = [f"取得: 前回 {p['started_at']} → 今回 {c['started_at']}",
          f"条件: {'同じ' if d['same_conditions'] else '違う（比較しない）'}"
          f"（ログアウト・届け先と端末をそろえて撮る）"]
    if md:
        ls += ["", "| キーワード | ASIN | 前回 | 今回 | 前回比 | 商品名 |",
               "|---|---|---|---|---|---|"]
        for r in d["rows"]:
            ls.append(f"| {r['term']} | {r['asin']} | {_rank(r['prev_rank'])} | {_rank(r['curr_rank'])} | "
                      f"{r['symbol']} {r['change_label']} | {r['title'][:38]} |")
    else:
        ls.append("")
        ls.append(f"{'キーワード':<12} {'ASIN':<12} {'前回':>6} {'今回':>6}  前回比")
        for r in d["rows"]:
            ls.append(f"{r['term']:<12} {r['asin']:<12} {_rank(r['prev_rank']):>6} {_rank(r['curr_rank']):>6}  "
                      f"{r['symbol']} {r['change_label']}")
    s = d["summary"]
    ls += ["", f"合計 {s['rows']}件: 上がった {s['up']}／下がった {s['down']}／変わらず {s['unchanged']}"]
    return "\n".join(ls)


def selftest():
    def rec(term, cards, at):
        return {"term": term, "fetched_at": at,
                "client_cards": [{"asin": a, "organic_rank": o, "sponsored_rank": sp, "title": a}
                                 for a, o, sp in cards]}
    cond = {"login": "none", "postal": "105-0003", "device": "pc",
            "viewport": {"width": 1366, "height": 900}, "locale": "ja-JP", "timezone": "Asia/Tokyo"}
    prev = {"started_at": "2026-11-01 10:22:16 JST", "conditions": cond,
            "terms": [rec("語A", [("B01", 7, None), ("B02", 9, None), ("B03", 37, None)], "2026-11-01 10:22:48 JST")]}
    curr = {"started_at": "2026-11-02 04:42:54 JST", "conditions": cond,
            "terms": [rec("語A", [("B01", 6, None), ("B02", 11, None), ("B04", 42, None)], "2026-11-02 04:43:27 JST")]}
    d = diff(prev, curr)
    got = {r["asin"]: (r["prev_rank"], r["curr_rank"], r["symbol"], r["change_label"]) for r in d["rows"]}
    assert got["B01"] == (7, 6, "↑", "＋1"), got["B01"]
    assert got["B02"] == (9, 11, "↓", "−2"), got["B02"]
    assert got["B03"] == (37, None, "↓", "37位→圏外"), got["B03"]
    assert got["B04"] == (None, 42, "↑", "圏外→42位"), got["B04"]
    assert d["summary"] == {"rows": 4, "up": 2, "down": 2, "unchanged": 0}, d["summary"]
    assert d["same_conditions"] is True
    assert change(5, 5) == ("→", "変わらず", 0)
    assert change(None, None)[1] == "圏外のまま"
    # 条件が違えば same_conditions=False
    curr2 = dict(curr, conditions=dict(cond, postal="100-0001"))
    assert diff(prev, curr2)["same_conditions"] is False
    # 取得日時が両方入る
    r0 = d["rows"][0]
    assert r0["prev_fetched_at"].startswith("2026-11-01") and r0["curr_fetched_at"].startswith("2026-11-02")
    print("serp_diff selftest: OK（前回比4件・圏外の出入り・条件の一致）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prev", nargs="?", help="前回の results.json")
    ap.add_argument("curr", nargs="?", help="今回の results.json")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--md", action="store_true", help="Markdown の表で出す")
    ap.add_argument("-o", "--out", help="出力先ファイル（既定は標準出力）")
    ap.add_argument("--allow-cond-diff", action="store_true", help="条件が違っても落とさない（警告のみ）")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.prev and a.curr):
        ap.error("prev と curr の results.json を指定してください")
    d = diff(json.loads(Path(a.prev).read_text(encoding="utf-8")),
             json.loads(Path(a.curr).read_text(encoding="utf-8")))
    body = json.dumps(d, ensure_ascii=False, indent=1) if a.json else to_text(d, md=a.md)
    if a.out:
        Path(a.out).write_text(body + "\n", encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        print(body)
    if not d["same_conditions"]:
        print("条件が違う2回です（届け先・端末・ログイン状態・画面幅をそろえて撮り直す）", file=sys.stderr)
        sys.exit(0 if a.allow_cond_diff else 1)
    sys.exit(0)


if __name__ == "__main__":
    main()
