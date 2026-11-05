#!/usr/bin/env python3
"""serp_redact.py — results.json から配布用の写しを作る（届け先の郵便番号・番地を落とす）。

社内の原本（serp_shot.py の出力）は郵便番号を持つ。デッキのフォルダや見本に添えるのは
**区までに丸めた写し**にする（FIGURES_GUIDE §2-4「ページに出す注記」と同じ考え方）。
順位・取得日時・条件のその他は変えないので、前回比もページの組み立ても同じ結果になる。

使い方:
  python3 serp_redact.py 原本/results.json -o 配布用/results.json --area 東京都港区
  python3 serp_redact.py --selftest
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RE_POSTAL = re.compile(r"(?<!\d)\d{3}-\d{4}(?!\d)")


def redact(res, area="東京都港区"):
    """郵便番号を落とし、届け先の表示を区までにする（順位・日時はそのまま）。"""
    out = json.loads(json.dumps(res, ensure_ascii=False))
    c = out.get("conditions", {})
    if "postal" in c:
        c["postal"] = None
    c["area"] = area
    c.pop("postal_area_keywords", None)
    if out.get("source_label"):
        out["source_label"] = RE_POSTAL.sub("", out["source_label"]).replace("届け先", f"届け先{area}")
    out.pop("log", None)          # Cookie 名・XHR のパスは配布しない
    out.pop("user_agent", None)
    for t in out.get("terms", []):
        t["delivery_shown"] = f"お届け先 {area}"
        t.pop("cards_html", None)
    s = json.dumps(out, ensure_ascii=False)
    assert not RE_POSTAL.search(s), "郵便番号が残っている"
    return json.loads(s)


def selftest():
    src = {"conditions": {"login": "none", "postal": "105-0003", "postal_area_keywords": ["西新橋"],
                          "device": "pc"},
           "source_label": "Amazon.co.jp 検索結果（ログアウト・届け先105-0003・PC）",
           "log": ["cookies: a,b"], "user_agent": "…Agent/5co-serp-shot",
           "started_at": "2026-11-02 04:42:54 JST",
           "terms": [{"term": "語A", "delivery_shown": "お届け先 港区西新橋 105-0003",
                      "client_cards": [{"asin": "B001", "organic_rank": 4, "sponsored_rank": None}],
                      "cards": [{"asin": "B001", "organic_rank": 4, "x": 1, "y": 2, "w": 3, "h": 4}]}]}
    r = redact(src)
    s = json.dumps(r, ensure_ascii=False)
    assert "105-0003" not in s and "西新橋" not in s, s
    assert r["conditions"]["area"] == "東京都港区"
    assert r["terms"][0]["client_cards"][0]["organic_rank"] == 4   # 順位は変えない
    assert r["terms"][0]["cards"][0]["x"] == 1                     # 座標は残す（帯の切り出しに要る）
    assert r["started_at"] == src["started_at"]                    # 取得日時は変えない
    assert "log" not in r and "user_agent" not in r
    assert src["conditions"]["postal"] == "105-0003"               # 原本は壊さない
    print("serp_redact selftest: OK（郵便番号・地名を落として順位と日時は不変）")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--area", default="東京都港区")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.src and a.out):
        ap.error("原本と -o 出力先を指定してください")
    r = redact(json.loads(Path(a.src).read_text(encoding="utf-8")), a.area)
    Path(a.out).write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {a.out}")
    sys.exit(0)


if __name__ == "__main__":
    main()
