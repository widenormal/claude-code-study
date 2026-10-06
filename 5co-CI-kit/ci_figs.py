#!/usr/bin/env python3
"""
ci_figs.py — 図・イラスト（figs）の差し込み・検品・ページ単位プレビュー（v3.10）

何のためか:
  完成したCIデッキに、ページごとの図・イラスト（インラインSVG／HTML断片）を後から足す。
  図は「1ページ1ファイル」の断片として figs/ に置き、デッキ本体（ビルダーや本文）には触らない。
  こうすると、図の担当を複数人・複数エージェントに分けても衝突せず、差し替えもファイル1つで済む。
  規定は FIGURES_GUIDE.md（図の描き方・置き方・原本の再構成・マルチエージェントの進め方）。

使い方:
  python3 ci_figs.py inject  <deck.html> <figs_dir> [-o out.html] [--only p3,p5]
      figs_dir/<キー>.html を、そのページの本文末尾（出典の note-line の直前）に差し込む。
      キー＝ページの section の id（例 p3）か、2桁のページ番号（例 03）。
      -o を省略すると <deck>.figs.html に書く（元のデッキは上書きしない）。
  python3 ci_figs.py lint    <figs_dir | fig.html ...>
      断片を検品する（3色トークン以外の色・外部参照・script・font-family・10px 未満の文字）。
  python3 ci_figs.py autofig <deck.html> [-o out.html]
      図の無い本文ページに、そのページの表（数値の列→横棒）か箇条書き（3〜6項目→流れのカード）から図を自動で作る。
      週次・月次ビルダーは生成の最後に自動で呼ぶ（-o 省略時は上書き）。何度実行しても二重に入らない。
  python3 ci_figs.py coverage <deck.html> [--strict]
      本文ページのうち、フレームワーク図・グラフ・イラストが1つも無いページを FIG? で挙げる（既定で図を使う＝0章）。
  python3 ci_figs.py preview <deck.html> --pages p3,p5 [--out DIR]
      指定ページだけを 1123×794px（A4横）で #static（組み上がった最終状態）のPNGにする。
      図を描いた人・レビューする人が Read で目視するための道具。ゲートは ci-gates.sh を使う。
  python3 ci_figs.py --selftest

規則（要点・詳細は FIGURES_GUIDE.md）:
  - 色は CSS 変数だけ（var(--ink) / var(--crystal) / var(--crystal-55) / var(--crystal-25) / var(--white) /
    var(--ink-85) / var(--ink-60) / var(--ink-14)）。none・currentColor・transparent は可。
  - 書体はページ側が当てる（font-family を書かない。数字を欧文にするときだけ var(--serif-en) 可）。SVG の font-size は 10 以上。
  - 外部画像・外部フォント・JavaScript を使わない（data: の画像は可＝書籍の表紙など）。
"""
import argparse
import glob
import html as _h
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

NOTE = '<p class="note-line">'
SEC_RE = re.compile(r'<section class="slide[^"]*"[^>]*>', re.I)
ID_RE = re.compile(r'\bid="([^"]+)"')


# ---------------------------------------------------------------- inject
def _sections(html: str):
    """(start, end, id) を返す。end は </section> の直後。"""
    # 根拠パネル（<template> 内の <section data-ci-tab>）などの入れ子 section があるため、
    # 「最初の </section>」ではなく「次のスライドの直前にある最後の </section>」を終端にする
    ms = list(SEC_RE.finditer(html))
    out = []
    for i, m in enumerate(ms):
        s = m.start()
        limit = ms[i + 1].start() if i + 1 < len(ms) else len(html)
        e = html.rfind("</section>", m.end(), limit)
        if e == -1:
            continue
        e += len("</section>")
        mid = ID_RE.search(m.group(0))
        out.append((s, e, mid.group(1) if mid else ""))
    return out


def inject(html: str, figs: dict) -> tuple:
    """figs = {キー: 断片HTML}。差し込んだキーと、ページが見つからなかったキーを返す。"""
    secs = _sections(html)
    by_key = {}
    for n, (s, e, sid) in enumerate(secs, 1):
        by_key[f"{n:02d}"] = (s, e)
        if sid:
            by_key[sid] = (s, e)
    done, missing = [], []
    # 後ろのページから差し込むと、前のページの位置がずれない
    targets = []
    for k, frag in figs.items():
        if k not in by_key:
            missing.append(k)
            continue
        targets.append((by_key[k], k, frag))
    for (s, e), k, frag in sorted(targets, key=lambda t: -t[0][0]):
        sec = html[s:e]
        pos = sec.rfind(NOTE)
        if pos == -1:
            pos = sec.rfind("</section>")
        wrapped = f'<!--ci-figs:{k}-->{frag}<!--/ci-figs:{k}-->'
        html = html[:s] + sec[:pos] + wrapped + sec[pos:] + html[e:]
        done.append(k)
    return html, sorted(done), sorted(missing)


def load_figs(figs_dir: str, only=None) -> dict:
    figs = {}
    for f in sorted(glob.glob(os.path.join(figs_dir, "*.html"))):
        k = os.path.basename(f)[:-5]
        if only and k not in only:
            continue
        figs[k] = pathlib.Path(f).read_text(encoding="utf-8")
    return figs



# ---------------------------------------------------------------- coverage（既定で図を使う）
VISUAL = re.compile(r'<svg\b(?![^>]*class="corner")(?![^>]*width="0")|<img\b(?![^>]*class="cl-logo")|'
                    r'class="[^"]*\b(ci-fig|ne-graph|bar-chart|ci-rows|flow|cyc4?|pyr|m22|stair|fnl3|kpis|tl|graph-wrap|northstar)\b', re.I)


def coverage(html: str) -> list:
    """本文ページのうち、フレームワーク図・グラフ・イラストが1つも無いページを返す [(番号, id)]。
    表紙（cover-full）・章扉（pd-divider・divider）と、data-fig-exempt="理由" を付けたページは対象外。
    HTML/CSS で組んだ図（グリッドの図解など）は、外枠に class="ci-fig" を付ければ図として数える。"""
    miss = []
    for n, (s, e, sid) in enumerate(_sections(html), 1):
        head = html[s:html.find(">", s) + 1]
        if re.search(r'cover-full|pd-divider|\bdivider\b|data-fig-exempt=', head):
            continue
        if not VISUAL.search(html[s:e]):
            miss.append((n, sid))
    return miss


# ---------------------------------------------------------------- autofig（表・箇条書きから図を自動で作る＝案B）
def _plain(x: str) -> str:
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def _num(txt: str):
    """セル文字列を数値へ。「1,200」「¥3.2億」「+18%」「△12」「(12)」に対応。数値でなければ None。"""
    t = _plain(txt).replace(",", "").replace("¥", "").replace("円", "").replace(" ", "")
    neg = t.startswith(("△", "▲", "-", "−")) or (t.startswith("(") and t.endswith(")"))
    t = t.strip("()").lstrip("△▲-−+")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(%|pt|億|万|千|百万|M|K|倍|件|名|人|h)?", t)
    if not m:
        return None
    v = float(m.group(1))
    return -v if neg else v


def _table_rows(tbl: str):
    rows = re.findall(r"<tr\b[^>]*>(.*?)</tr>", tbl, re.S | re.I)
    out = []
    for r in rows:
        cells = re.findall(r"<t([hd])\b[^>]*>(.*?)</t[hd]>", r, re.S | re.I)
        out.append([(k.lower(), c) for k, c in cells])
    return out


def _bar_svg(labels, values, col_name, unit_hint, dark):
    ink = "var(--crystal)" if dark else "var(--ink)"
    bar_main, bar = ("var(--crystal)", "var(--crystal-55)") if not dark else ("var(--crystal)", "var(--crystal-25)")
    n = len(labels)
    row = 24
    h = n * row + 8
    vmax = max(values) or 1
    lab_w = 150
    track = 560
    g = []
    top = values.index(max(values))
    for i, (l, v) in enumerate(zip(labels, values)):
        y = 4 + i * row
        w = max(2, round(track * v / vmax))
        l = (l[:14] + "…") if len(l) > 15 else l
        g.append(f'<text x="{lab_w - 8}" y="{y + 15}" font-size="12" text-anchor="end" fill="{ink}">{_h.escape(l)}</text>'
                 f'<rect x="{lab_w}" y="{y + 3}" width="{w}" height="16" rx="2" fill="{bar_main if i == top else bar}"/>'
                 f'<text x="{lab_w + w + 6}" y="{y + 15}" font-size="12" fill="{ink}" style="font-family:var(--serif-en)">{_h.escape(unit_hint[i])}</text>')
    return (f'<svg viewBox="0 0 900 {h}" width="100%" style="display:block;max-width:900px" role="img" '
            f'aria-label="{_h.escape(col_name)}の比較">{"".join(g)}'
            f'<line x1="{lab_w}" y1="0" x2="{lab_w}" y2="{h}" stroke="{ink}" stroke-opacity=".4" stroke-width="1"/></svg>')


def _fig_from_table(sec: str, dark: bool):
    m = re.search(r"<table\b.*?</table>", sec, re.S | re.I)
    if not m:
        return None
    rows = _table_rows(m.group(0))
    if len(rows) < 3:
        return None
    head = [_plain(c) for _, c in rows[0]]
    body = [r for r in rows[1:] if r and not any(k == "th" for k, _ in r[1:])]
    body = [r for r in body if not re.search(r"合計|総計|計$|Total", _plain(r[0][1]))][:8]
    if len(body) < 2:
        return None
    ncol = min(len(r) for r in body)
    for j in range(1, ncol):
        vals = [_num(r[j][1]) for r in body]
        if all(v is not None for v in vals) and all(v >= 0 for v in vals) and max(vals) > 0:
            labels = [_plain(r[0][1]) or "—" for r in body]
            col = head[j] if j < len(head) else f"{j + 1}列目"
            texts = [_plain(r[j][1]) for r in body]
            svg = _bar_svg(labels, vals, col, texts, dark)
            note = f"図の読み方: 表の「{_h.escape(col)}」を棒の長さで比べた（最も大きい行を濃く表示・表から自動生成）"
            return "table", note, svg
    return None


def _wrap(t: str, n: int, lines: int):
    out = [t[i:i + n] for i in range(0, len(t), n)][:lines]
    if len(t) > n * lines and out:
        out[-1] = out[-1][:-1] + "…"
    return out


def _split_item(it: str):
    # 区切りは「｜」を優先（「打ち手:1｜…」の「:」で切らない）。無ければ「：」で見出しと説明に分ける
    if re.search(r"[｜|]", it):
        h, b = re.split(r"[｜|]", it, maxsplit=1)
    elif "：" in it:
        h, b = it.split("：", 1)
    else:
        return it.strip(), ""
    return h.strip(), b.strip().strip("（）()")


def _lists(sec: str):
    out = []
    for m in re.finditer(r"<(ul|ol)\b[^>]*>(.*?)</\1>", sec, re.S | re.I):
        items = [_plain(x) for x in re.findall(r"<li\b[^>]*>(.*?)</li>", m.group(2), re.S | re.I)]
        items = [x for x in items if x]
        if items:
            # 直前の小見出し（h3 等）を列の名前にする
            before = sec[:m.start()]
            hm = re.findall(r"<(?:p|div|h3|h4)[^>]*class=\"[^\"]*\bh3\b[^\"]*\"[^>]*>(.*?)</(?:p|div|h3|h4)>|<h[34][^>]*>(.*?)</h[34]>", before, re.S | re.I)
            name = _plain((hm[-1][0] or hm[-1][1])) if hm else ""
            out.append((m.group(1).lower(), items, name))
    return out


def _fig_from_list(sec: str, dark: bool):
    ls = _lists(sec)
    if not ls:
        return None
    ink = "var(--crystal)" if dark else "var(--ink)"
    fill = "none" if dark else "var(--crystal-25)"
    fill2 = "none" if dark else "var(--crystal-55)"
    arrow = lambda x1, x2, y: (f'<path d="M{x1:.1f},{y} L{x2 - 2:.1f},{y}" stroke="{ink}" stroke-width="1.5"/>'
                               f'<path d="M{x2 - 7:.1f},{y - 4} L{x2 - 1:.1f},{y} L{x2 - 7:.1f},{y + 4}" fill="none" stroke="{ink}" stroke-width="1.5"/>')
    # 同じ数の箇条書きが2つ並ぶ → 左右の対応図（例：課題 → 方向性）
    if len(ls) >= 2 and len(ls[0][1]) == len(ls[1][1]) and 2 <= len(ls[0][1]) <= 6:
        L, R = ls[0], ls[1]
        n = len(L[1]); row = 40
        h = 22 + n * row
        g = [f'<text x="170" y="14" font-size="12" text-anchor="middle" fill="{ink}" fill-opacity=".7">{_h.escape(L[2][:20])}</text>',
             f'<text x="730" y="14" font-size="12" text-anchor="middle" fill="{ink}" fill-opacity=".7">{_h.escape(R[2][:20])}</text>']
        for i, (l, r) in enumerate(zip(L[1], R[1])):
            y = 22 + i * row
            g.append(f'<rect x="10" y="{y}" width="320" height="32" rx="6" fill="{fill}" stroke="{ink}" stroke-opacity=".4"/>'
                     f'<text x="170" y="{y + 21}" font-size="12" text-anchor="middle" fill="{ink}">{_h.escape(_wrap(l, 24, 1)[0])}</text>'
                     f'<rect x="570" y="{y}" width="320" height="32" rx="6" fill="{fill2}" stroke="{ink}" stroke-opacity=".4"/>'
                     f'<text x="730" y="{y + 21}" font-size="12" text-anchor="middle" fill="{ink}">{_h.escape(_wrap(r, 24, 1)[0])}</text>'
                     + arrow(338, 564, y + 16))
        svg = (f'<svg viewBox="0 0 900 {h}" width="100%" style="display:block;max-width:900px" role="img" aria-label="左右の対応">'
               f'{"".join(g)}</svg>')
        return "list-pair", "図の読み方: 左の項目それぞれに、右の項目が同じ順で対応する（箇条書きから自動生成）", svg
    kind, items, _ = ls[0]
    if not 3 <= len(items) <= 6:
        return None
    ordered = kind == "ol" or sum(bool(re.search(r"打ち手|ステップ|STEP|Step|^\d|第.", x)) for x in items) >= len(items) - 1
    n = len(items)
    gap = 18 if ordered else 12
    w = (900 - gap * (n - 1)) / n
    per = max(6, int((w - 20) / 12))
    g = []
    for i, it in enumerate(items):
        head, sub = _split_item(it)
        x = i * (w + gap)
        hl = _wrap(head, per, 2 if not sub else 1)
        sl = _wrap(sub, int(per * 1.2), 2) if sub else []
        g.append(f'<rect x="{x:.1f}" y="4" width="{w:.1f}" height="80" rx="8" fill="{fill}" stroke="{ink}" stroke-opacity=".5"/>')
        yy = 28
        for t in hl:
            g.append(f'<text x="{x + 12:.1f}" y="{yy}" font-size="13" font-weight="600" fill="{ink}">{_h.escape(t)}</text>'); yy += 18
        yy += 2
        for t in sl:
            g.append(f'<text x="{x + 12:.1f}" y="{yy}" font-size="11" fill="{ink}">{_h.escape(t)}</text>'); yy += 15
        if ordered and i < n - 1:
            g.append(arrow(x + w + 3, x + w + gap - 1, 44))
    svg = (f'<svg viewBox="0 0 900 88" width="100%" style="display:block;max-width:900px" role="img" '
           f'aria-label="要点">{"".join(g)}</svg>')
    note = ("図の読み方: 項目を左から順に並べた" if ordered else "図の読み方: 項目を並べて一覧にした") + "（箇条書きから自動生成）"
    return ("list-flow" if ordered else "list-cards"), note, svg


def autofig(html: str):
    """図の無い本文ページに、そのページの表（数値の列→横棒）か箇条書き（3〜6項目→流れのカード）から
    図を自動で作って差し込む。どちらも無いページはそのまま（FIG? が残る＝人か Claude が描く）。
    戻り値: (新しい html, [(ページ番号, 種類)])。何度実行しても二重に入らない（ci-autofig を持つページは飛ばす）。"""
    secs = _sections(html)
    added = []
    for n, (s, e, sid) in reversed(list(enumerate(secs, 1))):
        sec = html[s:e]
        head = sec[:sec.find(">") + 1]
        if re.search(r'cover-full|pd-divider|\bdivider\b|data-fig-exempt=', head) or "ci-autofig" in sec:
            continue
        if VISUAL.search(sec):
            continue
        dark = bool(re.search(r'class="[^"]*\bdark\b', head))
        body = re.sub(r"<template\b.*?</template>", "", sec, flags=re.S | re.I)
        fig = _fig_from_table(body, dark) or _fig_from_list(body, dark)
        if not fig:
            continue
        kind, note, svg = fig
        color = "color:var(--crystal);" if dark else ""
        frag = (f'<div class="ci-fig ci-autofig" data-autofig="{kind}" style="margin-top:14px">'
                f'<div class="t-note" style="{color}margin-bottom:4px">{note}</div>{svg}</div>')
        pos = sec.rfind(NOTE)
        if pos == -1:
            pos = sec.rfind("</section>")
        html = html[:s] + sec[:pos] + frag + sec[pos:] + html[e:]
        added.append((n, kind))
    return html, sorted(added)

# ---------------------------------------------------------------- lint
COLOR_ATTR = re.compile(r'\b(fill|stroke|color|background(?:-color)?|stop-color|border(?:-(?:top|right|bottom|left))?(?:-color)?)(?![-\w])\s*[:=]\s*"?([^";>]+)', re.I)
ALLOWED_COLOR = re.compile(r'^\s*(none|currentColor|transparent|inherit|url\(#[^)]+\)|var\(--(ink|ink-85|ink-60|ink-14|ink-20|crystal|crystal-55|crystal-25|white)\))', re.I)
HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')
FUNC_COLOR = re.compile(r'\b(rgba?|hsla?)\(', re.I)


def lint_text(text: str) -> list:
    errs = []
    body = re.sub(r'data:[^"\')\s]+', 'data:…', text)  # data: 画像の中身は見ない
    if re.search(r'<script\b', body, re.I):
        errs.append("script を使っている（図は静的に描く）")
    if re.search(r'(?:href|src)\s*=\s*"(?:https?:)?//', body, re.I) or re.search(r'url\((?:["\'])?(?:https?:)?//', body, re.I):
        errs.append("外部の画像・フォントを参照している")
    for m in re.finditer(r'font-family\s*[:=]\s*"?([^";>]+)', body, re.I):
        if not re.match(r'\s*var\(--serif-(en|ja)\)', m.group(1)):
            errs.append("font-family を書いている（書体はページ側が当てる。数字を欧文にするときだけ var(--serif-en) 可）")
    for m in HEX.finditer(re.sub(r'url\(#[^)]+\)|href="#[^"]+"|id="[^"]*"', '', body)):
        errs.append(f"色を直接指定している: {m.group(0)}（CSS 変数を使う）")
    if FUNC_COLOR.search(body):
        errs.append("rgb()/hsl() で色を指定している（CSS 変数を使う）")
    for m in COLOR_ATTR.finditer(body):
        v = m.group(2).strip()
        if not v or v.startswith("var(") or ALLOWED_COLOR.match(v):
            continue
        # border の太さ・種類だけの指定（1px solid var(--ink)）は var を含めば可
        if "var(--" in v and not HEX.search(v) and not FUNC_COLOR.search(v):
            continue
        if re.fullmatch(r'[\d.]+(px|mm|em)?(\s+(solid|dashed|dotted))?', v):
            continue
        errs.append(f"3色トークン以外の色: {m.group(1)}={v}")
    for m in re.finditer(r'font-size\s*[=:]\s*"?\s*([\d.]+)', body):
        try:
            if float(m.group(1)) < 10:
                errs.append(f"文字が小さい: font-size {m.group(1)}（10 以上）")
        except ValueError:
            pass
    return sorted(set(errs))


def lint_paths(paths) -> int:
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "*.html"))) if os.path.isdir(p) else [p]
    bad = 0
    for f in files:
        errs = lint_text(pathlib.Path(f).read_text(encoding="utf-8"))
        name = os.path.basename(f)
        if errs:
            bad += 1
            for e in errs:
                print(f"NG {name}: {e}")
        else:
            print(f"OK {name}")
    print(f"figs lint: {len(files) - bad}/{len(files)} OK")
    return 1 if bad else 0


# ---------------------------------------------------------------- preview
def find_chrome() -> str:
    """slide_overflow_check.py と同じ探索順（Mac → Playwright 同梱 → PATH）。"""
    cands = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
             "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    pw = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    cands += sorted(glob.glob(f"{pw}/chromium-*/chrome-linux/chrome"))
    cands += sorted(glob.glob(f"{pw}/chromium_headless_shell-*/chrome-linux/headless_shell"))
    for c in cands:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    for n in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    sys.exit("ERROR: Chrome/Chromium が見つかりません。")


def preview(deck: str, pages, out_dir: str) -> list:
    html = pathlib.Path(deck).read_text(encoding="utf-8")
    secs = _sections(html)
    keys = {}
    for n, (s, e, sid) in enumerate(secs, 1):
        keys[f"{n:02d}"] = sid or f"__n{n}"
        if sid:
            keys[sid] = sid
    os.makedirs(out_dir, exist_ok=True)
    chrome = find_chrome()
    pngs = []
    for k in pages:
        if k not in keys:
            print(f"missing {k}")
            continue
        sid = keys[k]
        if sid.startswith("__n"):
            # id の無いページは n 番目の section だけを見せる
            n = int(sid[3:])
            css = (f'section.slide{{display:none!important}}section.slide:nth-of-type({n}){{display:block!important;margin:0!important}}')
        else:
            css = f'section.slide{{display:none!important}}section.slide#{sid}{{display:block!important;margin:0!important}}'
        solo = html.replace("</head>", f"<style>{css}body{{margin:0!important;background:#fff!important}}</style></head>", 1)
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8",
                                         dir=os.path.dirname(os.path.abspath(deck))) as t:
            t.write(solo)
            tmp = t.name
        png = os.path.join(out_dir, f"{pathlib.Path(deck).stem}_{k}.png")
        url = "file://" + urllib.parse.quote(os.path.abspath(tmp)) + "#static"
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                        "--window-size=1123,794", f"--screenshot={png}", url], capture_output=True)
        os.unlink(tmp)
        print(f"PNG {png}")
        pngs.append(png)
    return pngs


# ---------------------------------------------------------------- selftest
def selftest() -> int:
    deck = ('<html><head></head><body>'
            '<section class="slide" id="p1"><h2>a</h2><p class="note-line">出典</p></section>'
            '<section class="slide"><h2>b</h2></section></body></html>')
    out, done, miss = inject(deck, {"p1": "<svg/>", "02": "<div>X</div>", "p9": "<i/>"})
    ok = True
    ok &= done == ["02", "p1"] and miss == ["p9"]
    ok &= out.index("<svg/>") < out.index('<p class="note-line">')           # 出典の前に入る
    ok &= out.index("<div>X</div>") < out.rindex("</section>")               # note-line が無ければ末尾
    ok &= out.count("<!--ci-figs:") == 2
    good = '<svg viewBox="0 0 10 10"><rect fill="var(--crystal)" stroke="var(--ink)"/><text font-size="11">a</text></svg>'
    ok &= lint_text(good) == []
    ok &= any("#f00" in e for e in lint_text('<rect fill="#f00"/>'))
    ok &= any("小さい" in e for e in lint_text('<text font-size="8">a</text>'))
    ok &= any("script" in e for e in lint_text('<script>1</script>'))
    ok &= any("外部" in e for e in lint_text('<img src="https://x/a.png">'))
    ok &= lint_text('<img src="data:image/jpeg;base64,/9j/4AAQ#fff">') == []   # data: 画像の中身は見ない
    ok &= any("font-family" in e for e in lint_text('<text font-family="Arial">a</text>'))
    ok &= lint_text('<div style="font-family:var(--serif-en)">2.75</div>') == []
    cov_deck = ('<section class="slide cover-full" id="c"></section>'
                '<section class="slide" id="a"><svg class="corner"></svg><p>文だけ</p></section>'
                '<section class="slide" id="b"><svg viewBox="0 0 1 1"></svg></section>'
                '<section class="slide" id="x" data-fig-exempt="付録の表"><table></table></section>')
    ok &= coverage(cov_deck) == [(2, "a")]
    # 根拠パネル（入れ子の section）があっても、スライドの終端と note-line を正しく見つける
    nested = ('<section class="slide" id="n"><h2>t</h2><template id="ev"><section data-ci-tab="内訳"><p>x</p></section></template>'
              '<p class="note-line">出典</p></section><section class="slide" id="m"></section>')
    o2, d2, _ = inject(nested, {"n": "<svg/>"})
    ok &= o2.index("<svg/>") > o2.index("</template>") and o2.index("<svg/>") < o2.index('<p class="note-line">')
    t_deck = ('<section class="slide" id="t"><table><tr><th>領域</th><th>投資</th><th>効果</th></tr>'
              '<tr><td>獲得</td><td>1,200</td><td>+18%</td></tr><tr><td>育成</td><td>680</td><td>+12%</td></tr>'
              '<tr><td>合計</td><td>1,880</td><td>—</td></tr></table><p class="note-line">出典</p></section>'
              '<section class="slide dark" id="l"><ul><li><b>着地</b>｜全体</li><li>打ち手:1｜（A）</li><li>打ち手:2｜B</li></ul></section>'
              '<section class="slide" id="x"><p>文だけ</p></section>'
              '<section class="slide dark divider" id="d"><h2>扉</h2></section>')
    o3, a3 = autofig(t_deck)
    ok &= a3 == [(1, "table"), (2, "list-flow")]
    ok &= o3.index('data-autofig="table"') < o3.index('<p class="note-line">')
    ok &= "合計" not in o3[o3.index('data-autofig="table"'):o3.index('<p class="note-line">')]   # 合計行は棒にしない
    ok &= ">打ち手:1<" in o3 and ">A<" in o3
    pair = ('<section class="slide"><p class="h3">課題</p><ul><li>a</li><li>b</li></ul><p class="h3">方向性</p><ul><li>c</li><li>d</li></ul></section>')
    ok &= autofig(pair)[1] == [(1, "list-pair")] and ">課題<" in autofig(pair)[0]
    plain = '<section class="slide"><ul><li>価格競争から価値訴求への転換が必要</li><li>b</li><li>c</li></ul></section>'
    op, ap = autofig(plain)
    frag = op[op.index('ci-autofig'):]
    ok &= ap == [(1, "list-cards")] and '<path' not in frag and '価格競争から価値訴求への' in frag   # 順番の無い列挙に矢印を付けない・切らずに折り返す
    ok &= coverage(o3) == [(3, "x")]                                          # 表も箇条書きも無いページだけ残る
    ok &= autofig(o3)[1] == []                                                # 二重に入らない
    for frag in re.findall(r'<div class="ci-fig ci-autofig".*?</svg></div>', o3, re.S):
        ok &= lint_text(frag) == []                                          # 自動の図も CI 規定を満たす
    print("selftest", "OK" if ok else "NG")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("inject"); a.add_argument("deck"); a.add_argument("figs_dir")
    a.add_argument("-o", "--out"); a.add_argument("--only", default="")
    b = sub.add_parser("lint"); b.add_argument("paths", nargs="+")
    f = sub.add_parser("autofig"); f.add_argument("deck"); f.add_argument("-o", "--out")
    d = sub.add_parser("coverage"); d.add_argument("deck"); d.add_argument("--strict", action="store_true")
    c = sub.add_parser("preview"); c.add_argument("deck"); c.add_argument("--pages", required=True)
    c.add_argument("--out", default="")
    ns = ap.parse_args(argv)
    if ns.selftest:
        return selftest()
    if ns.cmd == "inject":
        only = [x for x in ns.only.split(",") if x]
        figs = load_figs(ns.figs_dir, only)
        html = pathlib.Path(ns.deck).read_text(encoding="utf-8")
        out, done, missing = inject(html, figs)
        dest = ns.out or str(pathlib.Path(ns.deck).with_suffix(".figs.html"))
        pathlib.Path(dest).write_text(out, encoding="utf-8")
        print(f"差し込み: {', '.join(done) or 'なし'} → {dest}")
        if missing:
            print(f"ページが見つからない: {', '.join(missing)}", file=sys.stderr)
            return 1
        return 0
    if ns.cmd == "lint":
        return lint_paths(ns.paths)
    if ns.cmd == "autofig":
        html = pathlib.Path(ns.deck).read_text(encoding="utf-8")
        out, added = autofig(html)
        dest = ns.out or ns.deck
        pathlib.Path(dest).write_text(out, encoding="utf-8")
        print(f"自動の図: {', '.join(f'{n}:{k}' for n, k in added) or 'なし'} → {dest}")
        return 0
    if ns.cmd == "coverage":
        miss = coverage(pathlib.Path(ns.deck).read_text(encoding="utf-8"))
        name = os.path.basename(ns.deck)
        if miss:
            print(f"{name}: FIG? " + ",".join(f"{n}:{sid or '-'}" for n, sid in miss)
                  + "（本文ページにフレームワーク図・グラフ・イラストが無い。FIGURES_GUIDE.md 0章。"
                  "表だけで足りるページは section に data-fig-exempt=\"理由\" を付ける）")
            return 1 if ns.strict else 0
        print(f"{name}: OK")
        return 0
    if ns.cmd == "preview":
        pages = [x for x in ns.pages.split(",") if x]
        out = ns.out or os.path.join(os.path.dirname(os.path.abspath(ns.deck)), "_preview")
        preview(ns.deck, pages, out)
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
