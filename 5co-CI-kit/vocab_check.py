#!/usr/bin/env python3
"""vocab_check.py — 語彙帳の「当社で使わない」表記をデッキから拾う（v3.13.3・2026-11-01・当社NG語は落とす／表記ゆれは警告）。stdlib のみ・ブラウザ不要。

何を見るか（正＝vocab/README.md・COPY_GUIDE.md ルール6／検収チェック3）:
  VOCAB?  語彙帳 vocab/vocab_book.csv の avoid_5co 列（当社で使わない表記）が、スライドの表示テキストに
          出ていたら警告。直し方として use_5co 列（当社で使う表記）を添える。
          区分 NG＝当社NG語（avoid_5co に「当社NG」とある行・category=banned_watch）／表記＝表記ゆれ・紛れる言い方。

avoid_5co 列は人が読む文なので、機械で拾える語だけを取り出す:
  - 「／」で区切り、「」で囲まれた語があればその語だけを使う（例:「Amazon公式」）
  - 囲みが無ければ（…）の補足を外し、「・」で区切った各語を使う（例: レポートサービス・定期配信）
  - 文脈でしか決まらない書き方（「だけで書く」「単独」「混用」「混同」「と区別」「すべて」「で数える」「略す」等）は拾わない
  - 1文字の語（例: 棚）は拾わない（誤検知が多い。TERMS_AMAZON.md と検収チェック3で人が見る）
  - 使ってよい長い語に含まれるときは数えない（例: スポンサープロダクト広告 の中の「スポンサープロダクト」、
    カテゴリー の中の「カテゴリ」、リアルタイム入札 の中の「リアルタイム」）
  - 英字を含む語は大文字小文字を区別し、前後が英数字でないときだけ数える（ACoS は拾い ACOS は拾わない）
  拾った語の一覧は --list で確認できる。

数えない場所: <script>/<style>/<template>/コメント・タグの属性、data-vocab-exempt="理由" を付けた要素（section ごとでも可・
  出典欄で Amazon のページ名をそのまま引くとき等）、kit が差し込む UI（data-ci-pdf-save＝手元確認用 PDF のボタン）。

使い方:
  python3 vocab_check.py <deck.html> [...] [--vocab <csv>] [--fail-on ng|all] [--warn-only] [--json]
    --fail-on ng   当社NG語（区分 NG）があるときだけ終了コード 1。表記ゆれだけなら 0（所見は表示＝警告）
                   ci-gates.sh はこれで呼ぶ（当社NG語＝落とす・表記ゆれ＝警告。--strict のときは all）
    --fail-on all  所見が1つでもあれば 1（既定）
    --warn-only    所見があっても終了コード 0
    --json       ファイルごとに JSON Lines 1行（{"file","ok","hits":[{"page","term","count","use","level","key"}]}）
  python3 vocab_check.py --list [--vocab <csv>]   # 拾う語の一覧
  python3 vocab_check.py --selftest
終了コード: 0=所見なし（または --warn-only・--fail-on ng で表記ゆれだけ）／1=所見あり（--fail-on ng では当社NG語あり）／2=引数誤り・語彙帳が読めない
"""
import csv
import html as htmlmod
import json
import os
import re
import sys

SELF_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_VOCAB = os.path.join(SELF_DIR, "vocab", "vocab_book.csv")

CONTEXT_ONLY = ("だけで書く", "とだけ書く", "単独", "混用", "混同", "混在", "と区別", "すべて", "で数える", "略す")
TAG = re.compile(r"<(/?)([a-zA-Z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^'\">])*)>", re.S)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SEC = re.compile(r'<section\b[^>]*\bclass="slide\b[^"]*"[^>]*>', re.I)
PAREN = re.compile(r"[（(][^（）()]*[）)]")
ASCII = re.compile(r"[A-Za-z0-9]")
EXEMPT_ATTRS = ("data-vocab-exempt", "data-ci-pdf-save")   # 理由つきの除外／kit が差し込む UI（PDF ボタンの文言）


def _parts(cell):
    return [p.strip() for p in (cell or "").split("／") if p.strip() and p.strip() != "—"]


def _allowed(rows):
    """使ってよい表記（ja 列＋use_5co 列の各語）。avoid 語を含む長い語の除外に使う。"""
    out = set()
    for r in rows:
        for cell in (r.get("ja", ""), r.get("use_5co", "")):
            for p in _parts(cell):
                for q in (p, PAREN.sub("", p)):
                    q = q.strip()
                    if q:
                        out.add(q)
    return out


def avoid_terms(rows):
    """語彙帳の行 → [{"term","key","use","level"}]（同じ語は1つにまとめる）。"""
    seen = {}
    for r in rows:
        avoid = r.get("avoid_5co", "")
        level = "NG" if ("当社NG" in avoid or r.get("category") == "banned_watch") else "表記"
        use = r.get("use_5co", "").strip()
        use = "（使わない・言い換えは文脈で）" if use in ("", "—") else use
        for part in _parts(avoid):
            quoted = re.findall(r"「([^」]+)」", part)
            if quoted:
                rest = re.sub(r"「[^」]*」", "", part)
                if any(m in rest for m in ("だけで書く", "とだけ書く", "単独")):
                    continue
                cands = quoted
            else:
                if any(m in part for m in CONTEXT_ONLY):
                    continue
                cands = [c.strip() for c in PAREN.sub("", part).split("・")]
            for c in cands:
                c = c.strip()
                if len(c) < 2 or len(c) > 24 or c == "—":
                    continue
                if c in seen:
                    if level == "NG":
                        seen[c]["level"] = "NG"
                    # その語そのものの行（ja 列が同じ語）があれば、直し方はその行の use_5co を採る
                    if PAREN.sub("", r.get("ja", "")).strip() == c or r.get("category") == "banned_watch":
                        seen[c].update(key=r.get("key", ""), use=use)
                    continue
                seen[c] = {"term": c, "key": r.get("key", ""), "use": use, "level": level}
    return list(seen.values())


def load_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def compile_terms(rows):
    allowed = _allowed(rows)
    out = []
    for t in avoid_terms(rows):
        c = t["term"]
        longer = sorted((a for a in allowed if c in a and a != c), key=len, reverse=True)
        if ASCII.search(c):
            pat = re.compile(r"(?<![A-Za-z0-9])" + re.escape(c) + r"(?![A-Za-z0-9])")
        else:
            pat = re.compile(re.escape(c))
        out.append(dict(t, pat=pat, longer=longer))
    return out


def _drop_exempt(html):
    """data-vocab-exempt を付けた要素（入れ子ごと）を消す。"""
    out, i, depth, start = [], 0, 0, None
    for m in TAG.finditer(html):
        close, tag, attrs = m.group(1) == "/", m.group(2).lower(), m.group(3)
        selfclose = attrs.rstrip().endswith("/") or tag in VOID
        if start is None:
            if not close and any(k in attrs for k in EXEMPT_ATTRS):
                out.append(html[i:m.start()])
                if selfclose:
                    i = m.end()
                    continue
                start, depth = m.start(), 1
            continue
        if close:
            depth -= 1
            if depth == 0:
                i, start = m.end(), None
        elif not selfclose:
            depth += 1
    out.append(html[i:] if start is None else "")
    return "".join(out)


def visible_text(fragment):
    s = re.sub(r"<!--.*?-->", " ", fragment, flags=re.S)
    s = re.sub(r"<(script|style|template)\b.*?</\1\s*>", " ", s, flags=re.S | re.I)
    s = _drop_exempt(s)
    s = TAG.sub(" ", s)
    return htmlmod.unescape(s)


def pages(html):
    starts = [m.start() for m in SEC.finditer(html)]
    if not starts:
        return [(1, None, html)]
    out = []
    for n, s in enumerate(starts):
        e = starts[n + 1] if n + 1 < len(starts) else len(html)
        head = html[s:html.index(">", s) + 1]
        m = re.search(r'\bid="([^"]+)"', head)
        out.append((n + 1, m.group(1) if m else None, html[s:e]))
    return out


def check(html, terms):
    hits = []
    for n, pid, body in pages(html):
        text = visible_text(body)
        for t in terms:
            masked = text
            for a in t["longer"]:
                masked = masked.replace(a, "□" * len(a))
            k = len(t["pat"].findall(masked))
            if k:
                hits.append({"page": n, "id": pid, "term": t["term"], "count": k,
                             "use": t["use"], "level": t["level"], "key": t["key"]})
    return hits


def main(argv):
    vocab, warn, js, lst, files, fail_on = DEFAULT_VOCAB, False, False, False, [], "all"
    it = iter(argv)
    for a in it:
        if a == "--vocab":
            vocab = next(it, "")
        elif a == "--fail-on":
            fail_on = next(it, "")
            if fail_on not in ("ng", "all"):
                print("--fail-on は ng か all", file=sys.stderr)
                return 2
        elif a == "--warn-only":
            warn = True
        elif a == "--json":
            js = True
        elif a == "--list":
            lst = True
        elif a == "--selftest":
            return selftest()
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("-"):
            print(f"不明な引数: {a}", file=sys.stderr)
            return 2
        else:
            files.append(a)
    try:
        terms = compile_terms(load_rows(vocab))
    except (OSError, csv.Error) as e:
        print(f"語彙帳が読めません: {vocab}: {e}", file=sys.stderr)
        return 2
    if lst:
        for t in terms:
            print(f"{t['level']}\t{t['term']}\t→ {t['use']}\t({t['key']})")
        return 0
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
        hits = check(html, terms)
        ok = not hits
        ng = sum(h["count"] for h in hits if h["level"] == "NG")
        bad += (1 if ng else 0) if fail_on == "ng" else (0 if ok else 1)
        if js:
            print(json.dumps({"file": f, "ok": ok, "ng": ng, "hits": hits}, ensure_ascii=False))
            continue
        for h in hits:
            where = f"p{h['page']:02d}" + (f"（#{h['id']}）" if h["id"] else "")
            print(f"{name}: VOCAB? {where} 「{h['term']}」×{h['count']} → {h['use']}（{h['level']}・語彙帳 {h['key']}）")
        n = sum(h["count"] for h in hits)
        if ok:
            print(f"{name}: OK")
        elif ng:
            print(f"{name}: NG（VOCAB? {n}件・うち当社NG語 {ng}件・直すか data-vocab-exempt=\"理由\"）")
        else:
            print(f"{name}: WARN（VOCAB? {n}件・表記ゆれのみ・直すか data-vocab-exempt=\"理由\"）")
    return 0 if (warn or not bad) else 1


def selftest():
    rows = [
        {"key": "sp", "category": "product", "ja": "スポンサープロダクト広告", "use_5co": "スポンサープロダクト広告（略記SPは図中のみ）",
         "avoid_5co": "スポンサードプロダクト／「スポンサープロダクト」で切る"},
        {"key": "acos", "category": "metric", "ja": "ACOS", "use_5co": "ACOS（大文字）", "avoid_5co": "ACoS（社内正典は公式表記に寄せる）／「広告効率」だけで書く"},
        {"key": "dash", "category": "banned_watch", "ja": "ダッシュボード", "use_5co": "状況を一覧で把握", "avoid_5co": "ダッシュボード（当社NG語）"},
        {"key": "api", "category": "banned_watch", "ja": "API", "use_5co": "仕組み", "avoid_5co": "API・システム連携（当社NG語）"},
        {"key": "rtb", "category": "adtech", "ja": "リアルタイム入札", "use_5co": "RTB", "avoid_5co": "「リアルタイム」単独の使用（当社NG語）"},
        {"key": "rt", "category": "banned_watch", "ja": "リアルタイム", "use_5co": "速やかに", "avoid_5co": "リアルタイム（当社NG語）"},
        {"key": "cat", "category": "shopping", "ja": "カテゴリー", "use_5co": "カテゴリー", "avoid_5co": "カテゴリ（長音なし）・棚"},
        {"key": "seller", "category": "actor", "ja": "出品者", "use_5co": "出品者（セラー）", "avoid_5co": "ベンダーと混用"},
    ]
    terms = compile_terms(rows)
    names = {t["term"] for t in terms}
    ok = names == {"スポンサードプロダクト", "スポンサープロダクト", "ACoS", "ダッシュボード", "API", "システム連携", "リアルタイム", "カテゴリ"}
    deck = ('<section class="slide" id="p1"><h2 class="title">スポンサープロダクト広告とカテゴリーの話</h2>'
            '<p>ACOS は 12%。リアルタイム入札（RTB）は Amazon の方式。</p><style>.x{content:"API"}</style></section>'
            '<section class="slide"><p>スポンサープロダクトで APIs と API を見る。ACoS も。カテゴリの数。</p>'
            '<p class="src" data-vocab-exempt="出典のページ名">Amazon ダッシュボード <b>ガイド</b></p></section>'
            '<section class="slide" data-vocab-exempt="付録"><p>ダッシュボード</p></section>')
    hits = check(deck, terms)
    got = sorted((h["page"], h["term"], h["count"], h["level"]) for h in hits)
    ok &= got == [(2, "ACoS", 1, "表記"), (2, "API", 1, "NG"), (2, "カテゴリ", 1, "表記"), (2, "スポンサープロダクト", 1, "表記")]
    ok &= check('<section class="slide"><p>速やかに一覧で把握</p></section>', terms) == []
    ok &= check('<section class="slide"><a class="ci-pdf-save" data-ci-pdf-save>PDFをダッシュボード</a></section>', terms) == []
    ok &= next(t for t in terms if t["term"] == "リアルタイム")["key"] == "rt"   # 語そのものの行の直し方を採る
    # 本物の語彙帳が読め、拾う語があること
    if os.path.isfile(DEFAULT_VOCAB):
        real = compile_terms(load_rows(DEFAULT_VOCAB))
        rn = {t["term"] for t in real}
        ok &= len(load_rows(DEFAULT_VOCAB)) >= 90 and {"スポンサード広告", "ダッシュボード", "ACoS", "Amazon公式"} <= rn
        ok &= "棚" not in rn and "ベンダー" not in rn
    print("selftest", "OK" if ok else f"NG {sorted(names)} {got}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
