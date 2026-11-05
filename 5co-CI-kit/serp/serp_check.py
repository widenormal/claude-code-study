#!/usr/bin/env python3
"""serp_check.py — Amazon検索順位の根拠ページ（SERP）の検品。ci-gates.sh --serp から呼ぶ。

規定の正＝FIGURES_GUIDE.md §2-4。対象＝`<section data-serp-page>` のあるページだけ
（PRODUCT_IMG? とは別の検査。SERP の帯に写る商品カードは商品画像に数えない）。

落とす（ERR・--warn-only でも落ちる）:
  E1 出所に Amazon.co.jp 以外（データ事業者名・推計の手口）が書いてある
     ＝このページ型の出所は「出所：Amazon.co.jp検索結果（取得日時・条件）」だけ（若松さん決定 2026-11-02）
  E5 仕入れ先名（DMT・Acorn-i・Ignite・AMZ-POS と言い換え・競合ツール名）が
     **HTML のどこか**にある＝本文だけでなく フッター・`<style>`・`<script>`・HTML/CSS/JS の
     コメント・タグの属性まで見る（v3.14.1。本文しか見ていなかったため、共有CSSのコメントや
     フッター版スタックに残った名前を取りこぼしていた）。`data:` の画像本体だけは見ない（誤検知）。
     **「Shelpha」は既定で通す**（若松さん決定 2026-11-03・v3.14.2＝出典欄もフッター版スタックも出してよい）。
     伏せると決めた案件だけ `--ban-shelpha` で E1・E5 の対象に戻す。
     なお SERP ページの**出所の行**は Shelpha でも通らない＝E2 が
     「出所：Amazon.co.jp検索結果（取得日時・条件）」だけを許す（この規定は不変）
  E2 出所の行が上の形になっていない（「出所：」の後ろが Amazon.co.jp検索結果 ではない・括弧が無い）
  E3 郵便番号（nnn-nnnn）がページに出ている（場所は区まで）
  E4 画像が data: 以外（外部 URL の読み込み禁止＝ci_figs lint と同趣旨）

警告（SERP_SHOT?・既定は警告のまま）:
  W1 section に data-serp-at（取得日時）／data-serp-cond（条件）が無い
  W2 注記に必須の文言が無い（取得日時・Amazon.co.jp・ログアウト・PC・
     「スポンサー広告枠を除いた順位」「順位の要因は、このデータからは特定できない」）
  W3 帯（data-serp-shot）に data-serp-term／data-serp-rank が無い
  W4 スポンサー枠なのに「n位」とだけ書いている（「スポンサー n」と書く）
  W5 「入った」と書いている（1回の観測なので「入っている」と書く）
  W6 取得日が古い（既定14日より前）

使い方:
  python3 serp_check.py <deck.html> [<deck.html> …] [--warn-only] [--max-age-days 14] [--ban-shelpha]
  python3 serp_check.py --selftest

終了: 0=OK（または警告だけで --warn-only） / 1=所見あり / 2=引数誤り
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

JST = datetime.timezone(datetime.timedelta(hours=9))

RE_SECTION_OPEN = re.compile(r"<section\b[^>]*>", re.I)
RE_SECTION_ANY = re.compile(r"<section\b[^>]*>|</section\s*>", re.I)
RE_SERP_PAGE = re.compile(r"\bdata-serp-page\b", re.I)
RE_SERP_SHOT = re.compile(r"<(?:figure|div|aside)\b[^>]*\bdata-serp-shot\b[^>]*>", re.I)
RE_ATTR = lambda n: re.compile(r'\b%s\s*=\s*"([^"]*)"' % n, re.I)
RE_IMG_SRC = re.compile(r"<img\b[^>]*\bsrc\s*=\s*\"([^\"]*)\"", re.I)
RE_POSTAL = re.compile(r"(?<!\d)\d{3}-\d{4}(?!\d)")
RE_SRC_LINE = re.compile(r"出所[：:][^<。\n]*")
RE_SRC_OK = re.compile(r"^出所：Amazon\.co\.jp検索結果（[^（）]+）$")
RE_DATE = re.compile(r"(20\d\d)[-/年](\d{1,2})[-/月](\d{1,2})")

# このページ型に書いてはいけない名前（データ事業者・推計の手口）。出所は Amazon.co.jp だけ。
# 「Shelpha・シェルファ」は 2026-11-03（若松さん決定）に外した＝書いてよい。--ban-shelpha で戻す
# （SHELPHA_BANNED）。出所の行そのものは E2 が Amazon.co.jp検索結果 だけを許すので変わらない。
BANNED = (
    "DMT", "Acorn-i", "Acorn i", "Acorni", "AcornI",
    "Ignite", "AMZ-POS", "AMZPOS", "Jungle Scout", "JungleScout", "Helium 10", "Helium10",
    "Keepa", "SellerSprite", "セラースプライト", "DataHawk", "SmartScout", "Nint", "nint",
    "推計", "推定",
)
# 同じ名前を HTML 全文（<style>・<script>・コメント・属性・フッター）から拾うための版（E5・v3.14.1）。
# 前後が英数字でないときだけ数える＝「ignited」「print」等で誤検知しない。
# 「推計・推定」は表示テキストだけの検査のまま（CSSの語や社内コメントまでは見ない）。
SHELPHA_BANNED = ("Shelpha", "シェルファ")              # --ban-shelpha のときだけ E1 に足す（2026-11-03）
SHELPHA_PATTERN = ("Shelpha", r"shelpha|シェルファ")     # 同じく E5 に足す
VENDOR_PATTERNS = (
    ("DMT", r"(?<![a-z0-9])dmt(?![a-z0-9])"),
    ("Acorn-i", r"(?<![a-z0-9])acorn(?:[ _-]*i)?(?![a-z0-9])|アコーン"),
    ("Ignite", r"(?<![a-z0-9])ignite(?![a-z0-9])|イグナイト"),
    ("AMZ-POS", r"(?<![a-z0-9])amz[ _-]*pos(?![a-z0-9])"),
    ("Jungle Scout", r"jungle\s*scout"),
    ("Helium 10", r"helium\s*10"),
    ("Keepa", r"(?<![a-z0-9])keepa(?![a-z0-9])"),
    ("SellerSprite", r"seller\s*sprite|セラースプライト"),
    ("DataHawk", r"data\s*hawk"),
    ("SmartScout", r"smart\s*scout"),
    ("Nint", r"(?<![a-z0-9])nint(?![a-z0-9])"),
)
RE_VENDOR = tuple((n, re.compile(p, re.I)) for n, p in VENDOR_PATTERNS)
RE_SHELPHA = (SHELPHA_PATTERN[0], re.compile(SHELPHA_PATTERN[1], re.I))
# どの変種がどの名前かの対応（E1 で出した名前を E5 で二重に出さないため）
VENDOR_LABEL = {
    "Shelpha": "Shelpha", "シェルファ": "Shelpha", "DMT": "DMT",
    "Acorn-i": "Acorn-i", "Acorn i": "Acorn-i", "Acorni": "Acorn-i", "AcornI": "Acorn-i",
    "Ignite": "Ignite", "AMZ-POS": "AMZ-POS", "AMZPOS": "AMZ-POS",
    "Jungle Scout": "Jungle Scout", "JungleScout": "Jungle Scout",
    "Helium 10": "Helium 10", "Helium10": "Helium 10", "Keepa": "Keepa",
    "SellerSprite": "SellerSprite", "セラースプライト": "SellerSprite",
    "DataHawk": "DataHawk", "SmartScout": "SmartScout", "Nint": "Nint", "nint": "Nint",
}
# 画像の中身（data:…;base64,…）は英数字の羅列なので名前が偶然できる＝見ない（行数だけ保つ）
RE_DATA_URI = re.compile(r"data:[A-Za-z0-9.+/-]+;base64,[A-Za-z0-9+/=\s]+")
# 注記に必ず要る文言（§2-4「ページに出す注記」）
NOTE_MUST = (
    ("Amazon.co.jp", "Amazon.co.jp"),
    ("ログアウト", "ログアウト（未ログイン）であること"),
    ("PC", "PC の画面であること"),
    ("スポンサー広告枠を除いた順位", "「スポンサー広告枠を除いた順位」"),
    ("順位の要因は、このデータからは特定できない", "「順位の要因は、このデータからは特定できない」"),
)


def _visible(html):
    s = re.sub(r"<script\b[^>]*>.*?</script>", " ", html, flags=re.I | re.S)
    s = re.sub(r"<style\b[^>]*>.*?</style>", " ", s, flags=re.I | re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s.replace("&nbsp;", " "))


def sections(text):
    """(開始タグ, section 全体) を返す。根拠パネルのタブが入れ子の <section> なので深さを数える。"""
    out = []
    for m in RE_SECTION_OPEN.finditer(text):
        depth, pos = 1, m.end()
        for t in RE_SECTION_ANY.finditer(text, m.end()):
            depth += 1 if t.group(0).lower().startswith("<section") else -1
            if depth == 0:
                pos = t.end()
                break
        out.append((m.group(0), text[m.start():pos]))
    return out


def full_text(html):
    """全文検査用のテキスト（data: の画像本体だけ落とし、行番号は保つ）。"""
    return RE_DATA_URI.sub(lambda m: "data:…" + "\n" * m.group(0).count("\n"), html)


def vendor_hits(text, skip=(), ban_shelpha=False):
    """HTML 全文から仕入れ先名を拾う。skip に入れた名前（E1 で既出）は数えない。"""
    scan = full_text(text)
    out = []
    for name, pat in RE_VENDOR + ((RE_SHELPHA,) if ban_shelpha else ()):
        if name in skip:
            continue
        lines = sorted({scan.count("\n", 0, m.start()) + 1 for m in pat.finditer(scan)})
        if lines:
            out.append((name, lines))
    return out


def _label(open_tag, i):
    m = RE_ATTR("id").search(open_tag)
    return m.group(1) if m else f"section{i}"


def check_html(text, path, today=None, max_age_days=14, ban_shelpha=False):
    """(errors, warnings) を返す。どちらも表示用の文字列のリスト。"""
    errs, warns = [], []
    seen_vendor = set()
    today = today or datetime.datetime.now(JST).date()
    n_serp = 0
    for i, (open_tag, whole) in enumerate(sections(text), start=1):
        if not RE_SERP_PAGE.search(open_tag):
            continue
        n_serp += 1
        tag = f"{path}: " + _label(open_tag, i)
        vis = _visible(whole)
        # --- E1 事業者名・推計の手口（Shelpha は --ban-shelpha のときだけ・2026-11-03）
        for w in BANNED + (SHELPHA_BANNED if ban_shelpha else ()):
            if w in vis or w in open_tag:
                errs.append(f"{tag}: SERP_SRC 出所に書けない語「{w}」がある"
                            " — このページの出所は「出所：Amazon.co.jp検索結果（取得日時・条件）」だけ")
                if w in VENDOR_LABEL:
                    seen_vendor.add(VENDOR_LABEL[w])
        # --- E2 出所の行
        srcs = RE_SRC_LINE.findall(vis) + [v for v in RE_ATTR("data-src").findall(whole) if "出所" in v]
        if not srcs:
            errs.append(f"{tag}: SERP_SRC 出所の行が無い"
                        " — 「出所：Amazon.co.jp検索結果（取得日時・条件）」を入れる")
        for s in srcs:
            if not RE_SRC_OK.match(s.strip().rstrip("。")):
                errs.append(f"{tag}: SERP_SRC 出所の書き方が違う「{s.strip()[:60]}」"
                            " — 「出所：Amazon.co.jp検索結果（取得日時・条件）」")
        # --- E3 郵便番号
        for pc in set(RE_POSTAL.findall(vis)) | set(RE_POSTAL.findall(" ".join(RE_ATTR("alt").findall(whole)))):
            errs.append(f"{tag}: SERP_LOC 郵便番号 {pc} が出ている — 場所は区までにする（画像からも切り落とす）")
        # --- E4 外部画像
        for src in RE_IMG_SRC.findall(whole):
            if not src.startswith("data:"):
                errs.append(f"{tag}: SERP_IMG 外部の画像 {src[:60]} — data: で埋め込む")
        # --- W1 属性
        at = RE_ATTR("data-serp-at").search(open_tag)
        if not at:
            warns.append(f"{tag}: SERP_SHOT? data-serp-at（取得日時）が無い")
        if not RE_ATTR("data-serp-cond").search(open_tag):
            warns.append(f"{tag}: SERP_SHOT? data-serp-cond（条件）が無い")
        # --- W2 注記
        for needle, why in NOTE_MUST:
            if needle not in vis:
                warns.append(f"{tag}: SERP_SHOT? 注記に {why} が無い")
        if not RE_DATE.search(vis):
            warns.append(f"{tag}: SERP_SHOT? 注記に取得日時が無い")
        # --- W3/W4 帯
        shots = RE_SERP_SHOT.findall(whole)
        if not shots:
            warns.append(f"{tag}: SERP_SHOT? 検索結果の帯（data-serp-shot）が無い")
        for sh in shots:
            term = RE_ATTR("data-serp-term").search(sh)
            rank = RE_ATTR("data-serp-rank").search(sh)
            if not term:
                warns.append(f"{tag}: SERP_SHOT? 帯に data-serp-term（検索語）が無い")
            if not rank:
                warns.append(f"{tag}: SERP_SHOT? 帯に data-serp-rank（順位）が無い")
            elif "SP" in rank.group(1).upper() and "スポンサー" not in _visible(whole):
                warns.append(f"{tag}: SERP_SHOT? スポンサー枠なのに「スポンサー n」の表示が無い")
        # --- W5 言い方
        if re.search(r"入った", vis):
            warns.append(f"{tag}: SERP_SHOT? 「入った」→「入っている」（1回の時点観測なので状態で書く）")
        # --- W6 取得日の古さ
        if at:
            d = RE_DATE.search(at.group(1)) or RE_DATE.search(vis)
            if d:
                got = datetime.date(int(d.group(1)), int(d.group(2)), int(d.group(3)))
                if (today - got).days > max_age_days:
                    warns.append(f"{tag}: SERP_SHOT? 取得日 {got} が {max_age_days} 日より古い — 撮り直す")
    # --- E5 仕入れ先名を HTML 全文から（フッター・<style>・<script>・コメント・属性も見る・v3.14.1）
    if n_serp:
        for name, lines in vendor_hits(text, skip=seen_vendor, ban_shelpha=ban_shelpha):
            where = "/".join(f"{n}行目" for n in lines[:5]) + ("…" if len(lines) > 5 else "")
            errs.append(f"{path}: SERP_VENDOR HTML全文に書けない語「{name}」がある（{where}）"
                        " — 本文だけでなくフッター・<style>・<script>・コメント・属性も見る（社外に仕入れ先名を出さない）")
    return errs, warns


def _arg(argv, name, default):
    return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else default


def main(argv):
    if "--selftest" in argv:
        return selftest()
    warn_only = "--warn-only" in argv
    ban_shelpha = "--ban-shelpha" in argv
    max_age = int(_arg(argv, "--max-age-days", 14))
    skip = {"--max-age-days", str(max_age)}
    files = [a for a in argv if not a.startswith("-") and a not in skip]
    if not files:
        print("使い方: serp_check.py <deck.html>… [--warn-only] [--max-age-days 14] [--ban-shelpha]",
              file=sys.stderr)
        return 2
    errs, warns = [], []
    for f in files:
        p = Path(f)
        if not p.is_file():
            errs.append(f"{f}: ファイルが無い")
            continue
        e, w = check_html(p.read_text(encoding="utf-8", errors="replace"), f,
                          max_age_days=max_age, ban_shelpha=ban_shelpha)
        errs += e; warns += w
    for x in errs + warns:
        print(x)
    label = files[0] if len(files) == 1 else f"{len(files)} files"
    if not errs and not warns:
        print(f"{label}: OK")
        return 0
    print(f"{label}: NG")
    return 1 if errs or not warn_only else 0


GOOD = """<section class="slide" id="p01" data-serp-page="1"
 data-serp-at="2026-11-02 04:43 JST" data-serp-cond="ログアウトのPC・東京都港区">
<h2>Amazon検索の順位｜「語A」で4位に入っている</h2>
<div data-serp-shot data-serp-term="語A" data-serp-rank="4"><img src="data:image/jpeg;base64,xx" alt="語Aの段"></div>
<p>2026年11月2日 4:43時点。Amazon.co.jp、ログアウト状態のPC、届け先は東京都港区。
スポンサー広告枠を除いた順位。順位の要因は、このデータからは特定できない。</p>
<p>出所：Amazon.co.jp検索結果（2026年11月2日 4:43時点・ログアウトのPC・届け先は東京都港区）</p>
</section>"""


def selftest():
    ok = True

    def want(html, n_err, n_warn, note, ban_shelpha=False):
        nonlocal ok
        e, w = check_html(html, "t.html", today=datetime.date(2026, 11, 2), ban_shelpha=ban_shelpha)
        if (len(e), len(w)) != (n_err, n_warn):
            ok = False
            print(f"  ✘ {note}: err={len(e)} warn={len(w)}（期待 {n_err}/{n_warn}）")
            for x in e + w:
                print("     ", x)
        else:
            print(f"  ✔ {note}")

    want(GOOD, 0, 0, "規定どおりのページは所見なし")
    # 出所の行は Shelpha でも通らない（E2＝Amazon.co.jp検索結果 だけ。E1 は「推計」で1件）
    want(GOOD.replace("Amazon.co.jp検索結果（2026年11月2日 4:43時点・ログアウトのPC・届け先は東京都港区）",
                      "Shelpha 推計（2026年11月）"), 2, 0, "SERP の出所に Shelpha → 出所の形で落とす")
    for name in ("DMT", "Acorn-i", "Ignite", "AMZ-POS"):
        want(GOOD.replace("<h2>", f"<p>データ元 {name}</p><h2>"), 1, 0, f"本文に {name} → 落とす")
    want(GOOD.replace("順位の要因は、このデータからは特定できない。",
                      "順位の要因は、このデータからは特定できない。独自推計で補正した。"), 1, 0, "推計の手口 → 落とす")
    want(GOOD.replace("東京都港区。", "東京都港区 105-0003。"), 1, 0, "郵便番号 → 落とす")
    want(GOOD.replace('src="data:image/jpeg;base64,xx"', 'src="https://example.com/a.png"'), 1, 0, "外部画像 → 落とす")
    want(GOOD.replace("出所：Amazon.co.jp検索結果", "出所：Amazon.co.jp 検索結果のスクリーンショット"), 1, 0,
         "出所の書き方違い → 落とす")
    want(GOOD.replace('data-serp-at="2026-11-02 04:43 JST" ', ""), 0, 1, "data-serp-at 無し → 警告")
    want(GOOD.replace("スポンサー広告枠を除いた順位。", ""), 0, 1, "注記の文言欠け → 警告")
    want(GOOD.replace(' data-serp-term="語A"', ""), 0, 1, "帯の検索語 無し → 警告")
    want(GOOD.replace("4位に入っている", "4位に入った"), 0, 1, "「入った」 → 警告")
    want(GOOD.replace("2026-11-02 04:43 JST", "2026-10-01 04:43 JST").replace("2026年11月2日", "2026年10月1日"),
         0, 1, "取得日が古い → 警告")
    want('<section class="slide" id="p02"><p>Acorn-i 推計</p></section>', 0, 0, "SERP ページでなければ対象外")
    # --- Shelpha は既定で通る（若松さん決定 2026-11-03・v3.14.2）／伏せる案件は --ban-shelpha
    want(GOOD.replace("<h2>", "<p>市場規模は Shelpha。</p><h2>"), 0, 0, "本文の Shelpha → 既定では通す")
    want(GOOD.replace("<h2>", "<p>市場規模は Shelpha。</p><h2>"), 1, 0, "--ban-shelpha では落とす",
         ban_shelpha=True)
    # --- E5 HTML 全文（本文の外）を見る（v3.14.1）
    want('<style>/* 参考シェア（IGNITE昨年同月×YoY分母） */\n.x{color:red}</style>' + GOOD, 1, 0,
         "共有CSSのコメントに IGNITE → 落とす")
    want(GOOD + '<style>.slide::before{content:"CI v3.14.2 · Shelpha 9.1.0 · Template 2026.11.5";}</style>', 0, 0,
         "フッター版スタックの Shelpha → 既定では通す（2026-11-03）")
    want(GOOD + '<style>.slide::before{content:"CI v3.14.2 · Shelpha 9.1.0 · Template 2026.11.5";}</style>', 1, 0,
         "--ban-shelpha では版スタックの Shelpha も落とす", ban_shelpha=True)
    want(GOOD + "<!-- 元データ: Acorn-i の月次 -->", 1, 0, "HTMLコメントの事業者名 → 落とす")
    want(GOOD + '<script>var SRC="AMZPOS";</script>', 1, 0, "<script> の中の名前 → 落とす")
    want(GOOD.replace('alt="語Aの段"', 'alt="イグナイト調べ"'), 1, 0, "属性の言い換え（イグナイト） → 落とす")
    want(GOOD + '<style>.slide::before{content:"CI v3.14.2 · Template 2026.11.5";}</style>', 0, 0,
         "Shelpha を外した版スタック（--no-shelpha）も通る", ban_shelpha=True)
    want(GOOD + '<style>/* ignited な市場・@media print */</style><p>POS データ</p>', 0, 0,
         "似た語（ignited・print・POS）で誤検知しない")
    want(GOOD.replace('src="data:image/jpeg;base64,xx"',
                      'src="data:image/jpeg;base64,AAdmtAAkeepaAAcornAA"'), 0, 0,
         "data: の画像本体は見ない（偶然の一致で落とさない）")
    # 本文にある名前は E1 の1件だけ（E5 と二重に出さない）
    want(GOOD.replace("<h2>", "<p>データ元 DMT</p><h2>"), 1, 0, "本文の名前は1件だけ報告する")
    print("serp_check selftest:", "OK" if ok else "NG")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
