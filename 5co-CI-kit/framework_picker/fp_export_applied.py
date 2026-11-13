#!/usr/bin/env python3
"""fp_export_applied.py — 社内版の選択JSON（テキスト修正・Framework確定・画像/表の挿入）を当てて、ピッカー痕跡のない HTML を書き出す（試作 2026-11-11）

  python3 fp_export_applied.py deck_社内.html state.json -o deck_修正反映.html
  python3 fp_export_applied.py deck_社内.html state.json -o deck_確定.html --confirm-only

- 数字を含むテキスト修正は既定で当てない（要確認として警告）。--allow-numbers で当てる。
- 表の行数・セル数・ヘッダー最終列・1列目の並びを、挿入した表を除いて前後照合する。合わなければ書かない。
- Framework 確定は JSON の figures[id].confirmed.html をその図へ差し込む。
- 挿入（inserts）はスライド内に絶対配置で焼き込む。
- 出力は必ず別名。正本キットは触らない。
"""
from __future__ import annotations
import argparse, html as _h, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fp_apply_edits as ae
import fp_build

INS_CSS = (
    ".ci-ins{position:absolute;box-sizing:border-box;overflow:hidden}"
    ".ci-ins-fig{margin:0;width:100%;height:100%;display:flex;flex-direction:column}"
    ".ci-ins-fig img{flex:1;min-height:0;object-fit:contain;width:100%;height:100%;display:block}"
    ".ci-ins-fig figcaption{font-size:11px;color:var(--ink-60);padding:2px 4px;flex:none}"
    ".ci-ins-table{width:100%;height:100%;overflow:auto;padding:4px;box-sizing:border-box}"
    ".ci-legacy-legend-off,p.legend[hidden]{display:none !important}"
)

NUM = ae.NUM


def _esc(s: str) -> str:
    return _h.escape(s or "", quote=True)


def bake_insert(rec: dict) -> str:
    pct = rec.get("pct") or {}
    st = ""
    if pct:
        st = "left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%" % (
            pct.get("l", 0), pct.get("t", 0), pct.get("w", 100), pct.get("h", 100)
        )
    if rec.get("type") == "image":
        inner = (
            '<figure class="ci-ins-fig"><img src="%s" alt="%s" style="object-fit:contain;width:100%%;height:100%%;display:block">'
            "<figcaption>%s</figcaption></figure>"
            % (_esc(rec.get("dataUrl") or rec.get("data_url") or ""), _esc(rec.get("caption") or ""), _esc(rec.get("caption") or ""))
        )
    else:
        inner = '<div class="ci-ins-table">%s</div>' % (rec.get("tableHtml") or rec.get("table_html") or "")
    return '<div class="ci-ins" data-region="%s" style="position:absolute;box-sizing:border-box;background:var(--white);%s">%s</div>' % (
        _esc(rec.get("region") or "full"), st, inner
    )


def sanitize_baked_classes(src: str) -> str:
    for a, b in (
        ("ci-fp-split", "ci-chart-split"),
        ("ci-fp-side", "ci-chart-side"),
        ("ci-fp-live-table", "ci-chart-live-table"),
    ):
        src = src.replace(a, b)
    return src


def hide_confirmed_legends(src: str, fids) -> str:
    """確定した図の直後の p.legend に hidden を付ける（本文は残す）。"""
    for fid in fids:
        pat = re.compile(
            r'(<(div|figure|article)[^>]*\bdata-fp-fig="%s"[^>]*>.*?</\2>)(\s*)(<p\b[^>]*\blegend\b[^>]*>)' % re.escape(fid),
            re.S | re.I)
        def add_hide(m, _fid=fid):
            ptag = m.group(4)
            if re.search(r"\bhidden\b", ptag) and "ci-legacy-legend-off" in ptag:
                return m.group(0)
            if 'class="' in ptag:
                ptag = re.sub(r'class="', 'class="ci-legacy-legend-off ', ptag, count=1)
            else:
                ptag = ptag.replace("<p", '<p class="ci-legacy-legend-off"', 1)
            if not re.search(r"\bhidden\b", ptag) and ptag.endswith(">"):
                ptag = ptag[:-1] + " hidden>"
            return m.group(1) + m.group(3) + ptag
        src = pat.sub(add_hide, src, count=1)
    return src



def apply_confirms(src: str, figures: dict) -> str:
    for fid, fig in (figures or {}).items():
        conf = (fig or {}).get("confirmed") or {}
        html = conf.get("html")
        if not html:
            sel = (fig or {}).get("selected") or []
            if sel:
                last = (sel[-1] or {}).get("id") or "?"
                print("  WARN 図 %s は選択のみ（書き出し用の静的HTMLがJSONに無い）。社内版の「修正を反映した版を書き出す」で出してください（最後の選択: %s）" % (fid, last))
            continue
        # replace inner HTML of the element with data-fp-fig="fid"
        pat = re.compile(
            r'(<(div|table|figure|article|section|svg)[^>]*\bdata-fp-fig="%s"[^>]*>)(.*?)(</\2>)' % re.escape(fid),
            re.S | re.I,
        )
        m = pat.search(src)
        if not m:
            print("  WARN 図 %s の要素が見つからないので確定をスキップ" % fid)
            continue
        src = src[: m.start()] + m.group(1) + html + m.group(4) + src[m.end():]
        print("  OK 確定 %s → %s" % (fid, conf.get("id", "?")))
    src = sanitize_baked_classes(src)
    src = hide_confirmed_legends(src, [fid for fid, fig in (figures or {}).items() if (fig or {}).get('confirmed')])
    return src


def apply_inserts(src: str, inserts: list) -> str:
    # append baked inserts before </section> of the target slide; hide/remove replaced figs
    for rec in inserts or []:
        sid = rec.get("slide")
        if not sid:
            continue
        for fid in rec.get("replaces") or []:
            src = re.sub(
                r'<(div|table|figure|article|section|svg)[^>]*\bdata-fp-fig="%s"[^>]*>.*?</\1>' % re.escape(fid),
                "",
                src,
                count=1,
                flags=re.S | re.I,
            )
        baked = bake_insert(rec)
        # find section id="sid"
        ms = list(re.finditer(r'<section\b[^>]*\bid="%s"[^>]*>' % re.escape(sid), src, re.I))
        if not ms:
            print("  WARN スライド %s が無いので挿入をスキップ" % sid)
            continue
        start = ms[0].start()
        end = src.find("</section>", start)
        if end < 0:
            continue
        src = src[:end] + baked + src[end:]
        print("  OK 挿入 %s %s/%s" % (rec.get("id"), sid, rec.get("region")))
    return src


def inject_css(src: str) -> str:
    if "id=\"ci-ins-css\"" in src or "id='ci-ins-css'" in src:
        return src
    tag = '<style id="ci-ins-css">%s</style>' % INS_CSS
    if re.search(r"</head>", src, re.I):
        return re.sub(r"</head>", tag + "</head>", src, count=1, flags=re.I)
    return tag + src


def apply_text_edits(src: str, edits: list, allow_numbers: bool):
    """Reuse fp_apply_edits placement, but on the (still internal) source."""
    secs = {sid: (s, e) for sid, s, e in ae.sections(src)}
    plan, report, held = [], [], []
    for ed in edits or []:
        eid, old, new = ed.get("id", "?"), ed.get("old", ""), ed.get("new", "")
        if not old or old == new:
            report.append((eid, "SKIP 空・変更なし")); continue
        if NUM.search(old) or NUM.search(new):
            if not allow_numbers:
                held.append(ed)
                report.append((eid, "HOLD 数字を含む＝要確認（当てない）「%s」→「%s」" % (old, new)))
                continue
        if ed.get("slide") not in secs:
            report.append((eid, "NG スライド %s が無い" % ed.get("slide"))); continue
        runs = [r for r in ae.text_runs(src, *secs[ed["slide"]]) if r["text"] == ed.get("node_text")]
        k = int(ed.get("node_k", 0))
        if k >= len(runs):
            report.append((eid, "NG 元の文の段が見つからない")); continue
        r = runs[k]; off = int(ed.get("offset", -1))
        if r["text"][off:off + len(old)] != old:
            report.append((eid, "NG 位置の文字が元の文と一致しない")); continue
        if r["raw"] != r["text"]:
            report.append((eid, "NG 文字参照を含む段は自動では置換しない")); continue
        p = r["start"] + off
        plan.append((p, len(old), _h.escape(new, quote=False), eid, old, new))
        report.append((eid, "OK 「%s」→「%s」（%s）" % (old, new, ed["slide"])))
    res = src
    for p, l, rep, *_ in sorted(plan, key=lambda x: -x[0]):
        res = res[:p] + rep + res[p + l:]
    return res, report, held, plan


def check_tables(before_src, after_src, n_added_tables, plan):
    before, after = ae.tables_sig(before_src), ae.tables_sig(after_src)
    broken = []
    if len(after) != len(before) and len(after) != len(before) + n_added_tables:
        broken.append("表の数 %d→%d（挿入表 %d）" % (len(before), len(after), n_added_tables))
    def explained(b, c):
        return b == c or any(o in b and b.replace(o, n, 1) == c for *_, o, n in plan) or \
            any(o in b and re.sub(r"\s+", " ", b.replace(o, n, 1)).strip() == c for *_, o, n in plan)
    for i, (b, c) in enumerate(zip(before, after)):
        if b["rows"] != c["rows"] or b["ncells"] != c["ncells"]:
            broken.append("表%d 行・セル数" % (i + 1))
        if not explained(b["hdr_last"], c["hdr_last"]):
            broken.append("表%d ヘッダー最終列「%s」→「%s」" % (i + 1, b["hdr_last"], c["hdr_last"]))
        if len(b["col1"]) != len(c["col1"]) or not all(explained(x, y) for x, y in zip(b["col1"], c["col1"])):
            broken.append("表%d 行順（1列目）" % (i + 1))
    return broken, len(before)


def numbers_in_fig_match(src: str, fid: str) -> list:
    """確定後の図に出ている生の数字が、同じスライドの表セルと一致するか（軸目盛りは除外）。"""
    m = re.search(
        r'<(div|table|figure|article|section|svg)[^>]*\bdata-fp-fig="%s"[^>]*>.*?</\1>' % re.escape(fid),
        src, re.S | re.I,
    )
    if not m:
        # after strip, data-fp-fig is gone; skip
        return []
    fig_html = m.group(0)
    # slide
    # find enclosing section
    sec_s = src.rfind("<section", 0, m.start())
    sec_e = src.find("</section>", m.end())
    sec = src[sec_s:sec_e + 10] if sec_s >= 0 and sec_e >= 0 else src
    cells = [re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", c))).strip()
             for c in re.findall(r"<t[hd]\b[^>]*>.*?</t[hd]>", sec, flags=re.S | re.I)]
    texts = [re.sub(r"\s+", " ", _h.unescape(t)).strip()
             for t in re.findall(r">([^<]+)<", fig_html)]
    issues = []
    for t in texts:
        if not re.search(r"[0-9０-９]", t):
            continue
        if re.fullmatch(r"¥?\d+M", t) or re.fullmatch(r"-?\d+(\.\d+)?%", t):
            continue  # 軸
        if t in cells:
            continue
        if any(t == c or t in c or c in t for c in cells if c):
            continue
        # labels like series names without numbers already skipped
        if len(t) <= 1:
            continue
        issues.append(t)
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck"); ap.add_argument("state"); ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--allow-numbers", action="store_true")
    ap.add_argument("--confirm-only", action="store_true", help="Framework 確定だけ当て、テキスト修正と挿入はしない")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    inp = pathlib.Path(a.deck); out = pathlib.Path(a.out)
    if out.resolve() == inp.resolve() or out.exists():
        sys.exit("❌ 上書きしません（別名で出してください）: %s" % out)
    src = inp.read_text(encoding="utf-8")
    data = json.loads(pathlib.Path(a.state).read_text(encoding="utf-8"))
    figures = data.get("figures") or {}
    edits = [] if a.confirm_only else (data.get("edits") or [])
    inserts = [] if a.confirm_only else (data.get("inserts") or [])

    src1 = apply_confirms(src, figures)
    src2, report, held, plan = apply_text_edits(src1, edits, a.allow_numbers)
    src3 = apply_inserts(src2, inserts)
    src3 = inject_css(src3)
    # strip picker after applying (needs data-fp-fig during confirm)
    src4 = fp_build.strip_fp(src3)
    # drop runtime-only nodes if any were serialized (usually not in source)
    src4 = re.sub(r'<div id="ci-fp-(layer|bar)"[\s\S]*?</div>\s*', "", src4)
    n_added = sum(1 for r in inserts if r.get("type") == "table")
    broken, ntab = check_tables(src, src4, n_added, plan)
    for eid, msg in report:
        print("  %s %s" % (eid, msg))
    if held:
        print("要確認（数字を含む修正 %d 件は当てていない）" % len(held))
    if broken:
        print("❌ 表が崩れるため中止（書き出さない）: " + " / ".join(broken))
        return 1
    print("表の照合 OK（元の表 %d ・挿入表 %d）" % (ntab, n_added))
    if a.dry_run:
        print("dry-run: 書き出さない")
        return 0
    out.write_text(src4, encoding="utf-8")
    print("出力: %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
