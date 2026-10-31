#!/usr/bin/env python3
"""layout_run_check.py — 組み方の偏りチェック（v3.13・2026-10-31・警告のみ）。stdlib のみ・ブラウザ不要。

何を見るか（正＝V3.2_FORMAT.md「発表版（話す場で映す）」の「組み方の偏り」）:
  LAYOUT_RUN?  同じ組み方（ページの主役の種類＝表／棒グラフ／図／数字ピル／カード列／箇条書き…）が
               3ページ以上続いたら警告。話す場で単調になり、要点が埋もれる（OPI サンプル p08〜p12 の表5連続）。
  ELEMS?       見出しと要点を除くページ直下の要素（注記・出典・ダイジェスト専用の部品は数えない）が
               6つ以上なら警告（主役は1つ、ほかは小さく少なく）。

主役の決め方:
  1. data-digest-keep="hero" があるページは、最初の hero の種類（＝発表版で映る主役）。
  2. 無いページは、ページ直下の要素の種類を 棒グラフ＞図＞イラスト＞写真＞数字ピル＞表＞カード列＞箇条書き＞文章
     の順で一番上のもの。
  表紙（cover-full）・章扉（pd-divider／divider）は数えず、連続もそこで切る。
  section に data-layout-exempt="理由" を付けたページも数えない（連続はそこで切る）。

使い方:
  python3 layout_run_check.py <deck.html> [...] [--min-run 3] [--max-elems 6] [--warn-only] [--json] [--kinds]
    --warn-only  所見があっても終了コード 0（ci-gates.sh はこれで呼ぶ）
    --json       ファイルごとに JSON Lines 1行（{"file","ok","pages","kinds","runs","elems"}）
    --kinds      各ページの主役の種類も表示する（調べるとき用）
  python3 layout_run_check.py --selftest
終了コード: 0=所見なし（または --warn-only）／1=所見あり／2=引数誤り
"""
import json
import os
import re
import sys

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
TAG = re.compile(r"<(/?)([a-zA-Z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>", re.S)
CLS = re.compile(r'\bclass\s*=\s*"([^"]*)"')
SEC = re.compile(r'<section\b[^>]*\bclass="slide\b[^"]*"[^>]*>', re.I)

# 見出し・要点・注記・固定要素・ダイジェスト専用の部品＝組み方に数えない
SKIP = {"hdr", "title", "accent-bar", "gist", "corner", "period", "ci-stack", "t-note", "note-line", "legend",
        "sub", "blank-note", "sho-h", "ci-digest-btn", "dg-photo", "ci-talk-script", "kicker", "eyebrow", "src",
        "source", "note", "footnote"}
SKIP_PREFIX = ("dgx",)          # ダイジェスト専用（フル版では出ない）
ORDER = ["棒グラフ", "図", "イラスト", "写真", "数字ピル", "表", "カード列", "箇条書き", "文章"]


def _strip(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r"<(script|style|template)\b.*?</\1\s*>", "", html, flags=re.S | re.I)
    return re.sub(r'data:[^"\')\s]+', "data:", html)


def children(body):
    """ページ直下の要素 [(tag, classes, attrs, inner)]（入れ子は数えない）。"""
    out, depth, cur = [], 0, None
    for m in TAG.finditer(body):
        close, tag, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
        selfclose = attrs.rstrip().endswith("/") or tag in VOID
        if close:
            depth = max(0, depth - 1)
            if depth == 0 and cur is not None:
                out.append((cur[0], cur[1], cur[2], body[cur[3]:m.start()]))
                cur = None
            continue
        if depth == 0:
            c = CLS.search(attrs)
            info = (tag, (c.group(1) if c else "").split(), attrs, m.end())
            if selfclose:
                out.append((tag, info[1], attrs, ""))
                continue
            cur = info
        if not selfclose:
            depth += 1
    return out


def kind_of(tag, cls, attrs, inner):
    c = " ".join(cls)
    svg = len(re.findall(r'<svg\b(?![^>]*class="corner")', inner, re.I)) + (tag == "svg" and "corner" not in cls)
    if "ci-illus" in c or "ci-illus" in inner:
        return "イラスト"
    if svg:
        return "棒グラフ" if len(re.findall(r"<rect\b", inner, re.I)) >= 3 else "図"
    if re.search(r"\b(ci-fig|fig|ci-chart|ne-graph)\b", c):
        return "図"
    if tag == "figure" or tag == "img" or re.search(r'<img\b(?![^>]*class="[^"]*logo)', inner, re.I):
        if not re.search(r"<table\b", inner, re.I):
            return "写真"
    if re.search(r"(^|\s)(dgx[\w-]*|okr|ci-panel|kpi[\w-]*|[\w-]*pill[\w-]*|ci-big|num[\w-]*)(\s|$)", c):
        return "数字ピル"
    if tag == "table" or "skyu" in cls or re.search(r"<table\b", inner, re.I):
        return "表"
    if re.search(r"card", c) or len(re.findall(r'class="[^"]*\bcard\b', inner)) >= 2:
        return "カード列"
    if tag in ("ol", "ul") or re.search(r"<(ol|ul)\b", inner, re.I):
        return "箇条書き"
    return "文章"


def skipped(cls):
    return any(x in SKIP for x in cls) or any(x.startswith(SKIP_PREFIX) for x in cls)


def analyze(html, min_run=3, max_elems=6):
    html = _strip(html)
    ms = list(SEC.finditer(html))
    pages = []   # (番号, kind or None, 要素数)
    for i, m in enumerate(ms):
        head = m.group(0)
        end = ms[i + 1].start() if i + 1 < len(ms) else len(html)
        body = html[m.end():end]
        e = body.rfind("</section>")
        body = body[:e] if e != -1 else body
        n = i + 1
        if re.search(r'cover-full|pd-divider|\bdivider\b|data-layout-exempt=', head):
            pages.append((n, None, 0))
            continue
        kids = children(body)
        hero = [k for k in kids if re.search(r'data-digest-keep\s*=\s*"hero"', k[2])]
        cand = [k for k in kids if not skipped(k[1]) and not re.search(r'data-digest-keep\s*=\s*"(hero|photo|point)"', k[2])]
        if hero:
            kind = kind_of(*hero[0])
        else:
            kinds = [kind_of(*k) for k in cand]
            kind = min(kinds, key=ORDER.index) if kinds else None
        pages.append((n, kind, len(cand)))
    runs, cur = [], []
    for n, kind, _ in pages + [(None, None, 0)]:
        if kind is not None and cur and cur[-1][1] == kind:
            cur.append((n, kind))
            continue
        if len(cur) >= min_run:
            runs.append({"from": cur[0][0], "to": cur[-1][0], "kind": cur[0][1], "n": len(cur)})
        cur = [(n, kind)] if kind is not None else []
    elems = [{"page": n, "n": k} for n, kind, k in pages if kind is not None and k >= max_elems]
    return pages, runs, elems


def pg(n):
    return f"p{n:02d}"


def main(argv):
    if "--selftest" in argv:
        return selftest()
    files, js, warn, show = [], "--json" in argv, "--warn-only" in argv, "--kinds" in argv
    min_run, max_elems, it = 3, 6, iter(argv)
    for a in it:
        if a == "--min-run":
            min_run = int(next(it, "3"))
        elif a == "--max-elems":
            max_elems = int(next(it, "6"))
        elif a.startswith("--"):
            continue
        else:
            files.append(a)
    if not files:
        print(__doc__, file=sys.stderr)
        return 2
    bad = 0
    for f in files:
        name = os.path.basename(f)
        try:
            html = open(f, encoding="utf-8").read()
        except OSError as e:
            print(f"{name}: NG 読めません: {e}")
            bad += 1
            continue
        pages, runs, elems = analyze(html, min_run, max_elems)
        ok = not runs and not elems
        bad += 0 if ok else 1
        if js:
            print(json.dumps({"file": f, "ok": ok, "pages": len(pages),
                              "kinds": [{"page": n, "kind": k, "elems": e} for n, k, e in pages],
                              "runs": runs, "elems": elems}, ensure_ascii=False))
            continue
        if show:
            print(f"{name}: 主役 " + " ".join(f"{pg(n)}={k or '—'}" for n, k, _ in pages))
        for r in runs:
            print(f"{name}: LAYOUT_RUN? {pg(r['from'])}〜{pg(r['to'])} の{r['n']}ページが同じ組み方（{r['kind']}）"
                  "— 主役の種類を変えるか（図・数字ピル・カード列）、発表に使うなら hero を置く")
        for e in elems:
            print(f"{name}: ELEMS? {pg(e['page'])} 見出しと要点を除く要素が{e['n']}つ（{max_elems}つ以上）— 主役は1つ、ほかは小さく少なく")
        if ok:
            print(f"{name}: OK")
    return 0 if (warn or not bad) else 1


def selftest():
    def deck(*bodies):
        return "".join(f'<section class="slide{c}"{a}><h2 class="title">t｜a</h2><p class="gist">g</p>{b}</section>'
                       for c, a, b in bodies)
    T = ("", "", '<div class="skyu"><table><tr><td>1</td></tr></table></div><p class="t-note">注</p>')
    B = ("", "", '<div class="fig ci-fig"><svg viewBox="0 0 9 9"><rect/><rect/><rect/></svg></div><div class="skyu"><table></table></div>')
    H = ("", "", '<div class="dgx dgx-pair" data-digest-keep="hero"><b>20%</b></div><div class="skyu"><table></table></div>')
    D = (" cover-full pd-divider", "", "<h2>扉</h2>")
    ok = True
    _, r, e = analyze(deck(T, T, T))
    ok &= r == [{"from": 1, "to": 3, "kind": "表", "n": 3}] and e == []
    _, r, _ = analyze(deck(T, T, B, T))
    ok &= r == []                                            # 図が挟まれば切れる
    _, r, _ = analyze(deck(T, T, D, T))
    ok &= r == []                                            # 章扉で切れる
    _, r, _ = analyze(deck(T, H, T, T))
    ok &= r == []                                            # hero（数字ピル）が主役のページは表に数えない
    _, r, _ = analyze(deck(T, T, T, T, T), min_run=6)
    ok &= r == []
    X = ("", "", "<p>a</p><p>b</p><ul><li>c</li></ul><div>d</div><div>e</div><div>f</div><p class=\"t-note\">注</p>")
    _, _, e = analyze(deck(X))
    ok &= e == [{"page": 1, "n": 6}]
    _, r, _ = analyze(deck(T, ("", ' data-layout-exempt="付録"', T[2]), T, T))
    ok &= r == []
    nested = '<section class="slide"><h2 class="title">x</h2><template><section data-ci-tab="a"><table></table></section></template><div class="skyu"><table></table></div></section>'
    ok &= analyze(nested * 3)[1] == [{"from": 1, "to": 3, "kind": "表", "n": 3}]
    print("selftest", "OK" if ok else "NG")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
