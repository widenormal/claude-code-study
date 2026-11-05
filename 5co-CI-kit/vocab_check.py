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

  仕入れ先名  DMT・Acorn-i・Ignite・AMZ-POS（および アコーン・イグナイト・AMZPOS 等の言い換え）は
          当社NG語として必ず落とす。社外に出るものには仕入れ先名も推計のしかたも書かない
          （若松さん決定 2026-11-02）。この語だけは表示テキストではなく **HTML 全文** を見る＝
          <style>・<script>・HTML/CSS/JS のコメント・タグの属性も対象（CSSコメントに残った名前が
          そのまま配布されていたため・v3.14.1）。社内だけの資料は --allow-vendor で外せる。
          **「Shelpha」は書いてよい**（若松さん決定 2026-11-03・v3.14.2）＝出典欄（例「出典：Shelpha（取得日）」）も
          フッター版スタック（`CI … · Shelpha … · Template …`）も顧客向けデッキで出せる。
          案件の引き継ぎで Shelpha も伏せると決めた資料だけ --ban-shelpha で当社NG語に戻す
          （そのときは ci_head.py --no-shelpha で版スタックからも外す＝対で使う）。

数えない場所（仕入れ先名は除く＝全文を見る）: <script>/<style>/<template>/コメント・タグの属性、data-vocab-exempt="理由" を付けた要素（section ごとでも可・
  出典欄で Amazon のページ名をそのまま引くとき等）、kit が差し込む UI（data-ci-pdf-save＝手元確認用 PDF のボタン）。

使い方:
  python3 vocab_check.py <deck.html> [...] [--vocab <csv>] [--fail-on ng|all] [--warn-only] [--json]
    --fail-on ng   当社NG語（区分 NG）があるときだけ終了コード 1。表記ゆれだけなら 0（所見は表示＝警告）
                   ci-gates.sh はこれで呼ぶ（当社NG語＝落とす・表記ゆれ＝警告。--strict のときは all）
    --fail-on all  所見が1つでもあれば 1（既定）
    --warn-only    所見があっても終了コード 0
    --allow-vendor 仕入れ先名の検査を外す（社内だけの資料。社外に出すものには付けない）
    --ban-shelpha  「Shelpha」も当社NG語に戻す（既定は許可・伏せると決めた案件だけ。
                   ci_head.py --no-shelpha と対で使う＝版スタックにも出さない）
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

# ---------------------------------------------------------------- 仕入れ先・データ事業者の名前（v3.14.1／v3.14.2改）
# 若松さん決定（2026-11-02）: 社外に出るもの（お客様向けデッキ・営業資料・サイト）には仕入れ先名も
# 推計のしかたも書かない＝出所の注記も同じ。社内だけの資料は書いてよい（--allow-vendor）。
# 表示テキストだけでは足りない: <style> のCSSコメントに残った名前がそのまま配布されていた
# （ci-format-v3.2.css の「IGNITE…」・v3.14.1 で削除）。この検査だけは HTML 全文
# （<style>・<script>・HTML/CSS/JS のコメント・属性）を見て、見つかれば当社NG語として落とす。
# 若松さん決定（2026-11-03・v3.14.2）: **Shelpha は別扱い＝書いてよい**（出典欄・フッター版スタック）。
# 既定の VENDOR_TERMS から外し、伏せると決めた案件だけ --ban-shelpha（ban_shelpha=True）で戻す。
# DMT・Acorn-i・Ignite・AMZ-POS と推計のしかたは引き続きどこにも書かない。
VENDOR_TERMS = (
    ("DMT", r"(?<![a-z0-9])dmt(?![a-z0-9])"),
    ("Acorn-i", r"(?<![a-z0-9])acorn(?:[ _-]*i)?(?![a-z0-9])|アコーン"),
    ("Ignite", r"(?<![a-z0-9])ignite(?![a-z0-9])|イグナイト"),
    ("AMZ-POS", r"(?<![a-z0-9])amz[ _-]*pos(?![a-z0-9])"),
)
SHELPHA_TERM = ("Shelpha", r"shelpha|シェルファ")   # --ban-shelpha のときだけ足す（2026-11-03）
VENDOR_USE = "社外向けには書かない（仕入れ先名・推計のしかたを出さない・社内資料だけ可）"
SHELPHA_USE = "この案件では伏せる（--ban-shelpha。通常のデッキでは「Shelpha」と書いてよい）"
VENDOR_RE = tuple((n, re.compile(p, re.I)) for n, p in VENDOR_TERMS)
SHELPHA_RE = (SHELPHA_TERM[0], re.compile(SHELPHA_TERM[1], re.I))
# フッター版スタック「CI vX · Shelpha Y · Template Z」は既定で出す（2026-11-03 若松さん決定・§5.5）。
# --ban-shelpha で検査する資料は、組むときも ci_head.py --no-shelpha で版スタックから外す（対で使う）。


def vendor_hits(html, ban_shelpha=False):
    """HTML 全文から仕入れ先名を拾う（<style>・<script>・コメント・属性・フッターも見る）。すべて当社NG語。"""
    masked = html
    heads = [(m.start(), m.group(0)) for m in SEC.finditer(masked)]
    out = {}
    for name, pat in VENDOR_RE + ((SHELPHA_RE,) if ban_shelpha else ()):
        for m in pat.finditer(masked):
            n = sum(1 for s, _ in heads if s <= m.start())
            pid = None
            if n:
                mid = re.search(r'\bid="([^"]+)"', heads[n - 1][1])
                pid = mid.group(1) if mid else None
            use = SHELPHA_USE if name == SHELPHA_TERM[0] else VENDOR_USE
            h = out.setdefault((n, name), {"page": n, "id": pid, "term": name, "count": 0,
                                           "use": use, "level": "NG", "key": "vendor", "lines": []})
            h["count"] += 1
            if len(h["lines"]) < 5:
                h["lines"].append(masked.count("\n", 0, m.start()) + 1)
    return [out[k] for k in sorted(out)]


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


def check(html, terms, vendor=True, ban_shelpha=False):
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
    if vendor:
        hits += vendor_hits(html, ban_shelpha)
    return hits


def main(argv):
    vocab, warn, js, lst, files, fail_on, vendor = DEFAULT_VOCAB, False, False, False, [], "all", True
    ban_shelpha = False
    it = iter(argv)
    for a in it:
        if a == "--allow-vendor":
            vendor = False
        elif a == "--ban-shelpha":
            ban_shelpha = True
        elif a == "--vocab":
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
        hits = check(html, terms, vendor=vendor, ban_shelpha=ban_shelpha)
        ok = not hits
        ng = sum(h["count"] for h in hits if h["level"] == "NG")
        bad += (1 if ng else 0) if fail_on == "ng" else (0 if ok else 1)
        if js:
            print(json.dumps({"file": f, "ok": ok, "ng": ng, "hits": hits}, ensure_ascii=False))
            continue
        for h in hits:
            where = "全体" if h["page"] == 0 else f"p{h['page']:02d}" + (f"（#{h['id']}）" if h["id"] else "")
            if h.get("lines"):
                where += "・" + "/".join(f"{n}行目" for n in h["lines"])
            print(f"{name}: VOCAB? {where} 「{h['term']}」×{h['count']} → {h['use']}（{h['level']}・語彙帳 {h['key']}）")
        n = sum(h["count"] for h in hits)
        if ok:
            print(f"{name}: OK")
        elif ng:
            v = "・仕入れ先名は除外できません＝書き換える" if any(h["key"] == "vendor" for h in hits) else ""
            print(f"{name}: NG（VOCAB? {n}件・うち当社NG語 {ng}件・直すか data-vocab-exempt=\"理由\"{v}）")
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
    # 仕入れ先名は HTML 全文を見る（v3.14.1）: CSSコメントに隠れていても落とす／きれいな版は通る
    hidden = ('<style>/* カテゴリ名下の推計シェア（参考・IGNITE昨年同月×YoY分母） */\n.x{color:red}</style>'
              '<section class="slide" id="p1"><p>市場規模の推移</p></section>')
    ok &= [(h["term"], h["level"], h["page"]) for h in check(hidden, terms)] == [("Ignite", "NG", 0)]
    ok &= check(hidden, terms, vendor=False) == []            # --allow-vendor（社内資料）では見ない
    clean = ('<style>/* カテゴリ名下の参考シェア（昨年同月比の分母） */\n.x{color:red}</style>'
             '<section class="slide" id="p1"><p>市場規模の推移（当社の補正データ）</p></section>')
    ok &= check(clean, terms) == []
    # HTMLコメント・表示テキスト・言い換えも拾う（ページ番号つき）。Shelpha は既定では拾わない（v3.14.2）
    mixed = '<section class="slide" id="p1"><!-- Shelpha 調べ --><p>DMT と Acorn-i、AMZ-POS、アコーン</p></section>'
    ok &= [(h["term"], h["count"], h["page"]) for h in check(mixed, terms)] == [
        ("AMZ-POS", 1, 1), ("Acorn-i", 2, 1), ("DMT", 1, 1)]
    ok &= [(h["term"], h["count"]) for h in check(mixed, terms, ban_shelpha=True)] == [
        ("AMZ-POS", 1), ("Acorn-i", 2), ("DMT", 1), ("Shelpha", 1)]
    # <script> とタグの属性に隠しても拾う
    ok &= [h["term"] for h in check('<script>var src="AMZPOS";</script>', terms)] == ["AMZ-POS"]
    ok &= [h["term"] for h in check('<section class="slide"><img alt="イグナイト" src="x.png"></section>', terms)] == ["Ignite"]
    # 出典欄・フッターの版スタックの「Shelpha」は既定で通る（若松さん決定 2026-11-03・v3.14.2）
    stack = '<style>.slide::before{content:"CI v3.14.2 · Shelpha 9.1.0 · Template 2026.11.5  ·  © 2026 5co.";}</style>'
    ok &= check(stack, terms) == []
    ok &= [h["term"] for h in check(stack, terms, ban_shelpha=True)] == ["Shelpha"]
    src_line = '<section class="slide" id="p1"><p class="src">出典：Shelpha（2026年11月3日取得）</p></section>'
    ok &= check(src_line, terms) == []
    ok &= [h["term"] for h in check(src_line, terms, ban_shelpha=True)] == ["Shelpha"]
    # kit が注入する版スタックに Shelpha 版が入り、他の仕入れ先名は無いこと（既定・2026-11-03）
    sys.path.insert(0, SELF_DIR)
    import ci_head  # noqa: E402
    ok &= not vendor_hits(ci_head.footer_stack_css())
    ok &= "Shelpha" in ci_head.footer_stack_css()
    ok &= "Shelpha" not in ci_head.footer_stack_css(shelpha=False)
    # 似た語で誤検知しない
    ok &= check('<section class="slide"><p>ignited な市場・POS データ・DMTS</p></section>', terms) == []
    # kit が配る CSS・テンプレートに仕入れ先名が残っていないこと（Shelpha は可・版スタック以外）
    for f in ("ci-format-v3.2.css", "ci-charts.css", "ci-gist-v3.8.css", "5co_biz_briefing_template.html"):
        fp = os.path.join(SELF_DIR, f)
        if os.path.isfile(fp):
            left = vendor_hits(open(fp, encoding="utf-8").read())
            ok &= not left
            if left:
                print(f"  {f}: {[h['term'] for h in left]}")
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
