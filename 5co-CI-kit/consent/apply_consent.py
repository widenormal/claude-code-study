#!/usr/bin/env python3
"""開いた直後の同意画面（#ci-consent）をデッキに足す（kit v3.18.0・正本＝候補者用 v22・2026-11-05 若松さん合格）。

使い方:
  apply_consent.py deck.html -o out.html --mode candidate --to recruit@5inc.jp \
      --doc-title "事業プランと期待役割" --name "氏名" [--when "面接が終了した時点" --mail-when "面接が終わった時点"]
  apply_consent.py deck.html -o out.html --mode internal --to recruit@5inc.jp --doc-title "…"
  apply_consent.py --selftest

--mode candidate（候補者用・既定）:
  - 5co ロゴ（#lk・Strategy, refined.）＋取扱注意＋「同意して閲覧する」を全面に出し、押すまで本文を見せない
  - ボタンは mailto（宛先＝--to・件名【破棄同意】・本文に破棄の同意と氏名）。押すと本文を表示
  - #static・JS 無効（noscript）・印刷のどれでも本文を出さない
--mode internal（社内用）:
  - 同意画面は出さない。印刷（PDF）だけ表紙の右上に取扱注意の注記を出す
冪等（すでに入っていれば足さない）。宛先・件名・氏名は案件ごとに引数で変える（キットに個人名を書かない）。
"""
import argparse, html as H, os, re, sys, urllib.parse as U
D = os.path.dirname(os.path.abspath(__file__))
def _r(n): return open(os.path.join(D, n), encoding="utf-8").read().strip("\n")

LOGO = '<svg class="ci-consent-logo" viewBox="0 0 50.857 36.507" role="img" aria-label="5 co. Strategy, refined."><use href="#lk"/></svg>'
NOJS_HEAD = '<noscript><style>body > *:not(noscript){display:none !important;}</style></noscript>'
NOJS_BODY = ('<noscript><p class="ci-nojs" style="margin:120px auto;max-width:640px;text-align:center;'
             'font:500 18px/1.8 sans-serif;color:#0B1F3A;">JavaScriptを有効にしてください</p></noscript>')

def mailto(to, doc_title, name, when):
    subj = f"【破棄同意】{doc_title}" + (f"（{name}）" if name else "")
    body = f"「{doc_title}」の資料は{when}で、本ファイルと複製をすべて破棄することに同意します。\r\n氏名：{name}"
    return "mailto:" + to + "?subject=" + U.quote(subj, safe="") + "&body=" + U.quote(body, safe="")

def note_html(to, when):
    return (f'<div class="ci-pdf-consent-note" role="note"><b>取扱注意</b>　本資料には5 co.の機密情報が含まれます。'
            f'{H.escape(when)}で、本ファイルとその複製を破棄してください。<br>同意の連絡先：{H.escape(to)}</div>')

def overlay_html(to, doc_title, name, when, mail_when=None):
    href = mailto(to, doc_title, name, mail_when or when).replace('"', "%22")
    return ('<div id="ci-consent" role="dialog" aria-modal="true" aria-labelledby="ci-consent-k">\n<div class="ci-consent-card">\n'
            + LOGO + '\n<aside class="ci-consent-block" role="note"><span class="ci-consent-k" id="ci-consent-k">取扱注意</span>'
            f'<p class="ci-consent-body">本資料には5 co.の機密情報が含まれます。<br>{H.escape(when)}で、本ファイルとその複製を破棄してください。</p></aside>\n'
            f'<a class="ci-consent-btn" id="ci-consent-btn" href="{href}">同意して閲覧する</a>\n'
            '<p class="ci-consent-note">メールアプリが開きます。送信ボタンを押すと同意が完了します。</p>\n'
            f'<p class="ci-consent-addr">メールアプリが無い場合の宛先：<b>{H.escape(to)}</b></p>\n</div></div>')

def apply_consent(src, mode="candidate", to="", doc_title="", name="", when="面接が終了した時点", mail_when="面接が終わった時点"):
    if not to or "@" not in to: raise ValueError("--to（宛先メール）が必要です")
    if not doc_title: raise ValueError("--doc-title が必要です")
    if 'id="ci-consent-css"' in src: return src
    head = [f'<style id="ci-consent-css">\n{_r("consent.css")}\n</style>']
    if mode == "candidate":
        head.append(f'<script id="ci-consent-head">\n{_r("consent_head.js")}\n</script>')
        head.append(f'<style id="ci-cand-print">\n{_r("candidate_print.css")}\n</style>')
        head.append(NOJS_HEAD)
    elif mode != "internal":
        raise ValueError("--mode は candidate か internal")
    if "</head>" not in src or "</body>" not in src: raise ValueError("</head> と </body> が必要です")
    src = src.replace("</head>", "\n".join(head) + "\n</head>", 1)
    # 表紙（最初の section.slide）の閉じタグの直前に PDF 用の注記
    m = re.search(r'<section\b[^>]*class="[^"]*\bslide\b[^"]*"[^>]*>', src)
    if m:
        k = src.index("</section>", m.end())
        src = src[:k] + note_html(to, when) + src[k:]
    if mode == "candidate":
        src = re.sub(r"(<body\b[^>]*>)", lambda x: x.group(1) + "\n" + NOJS_BODY, src, count=1)
        i = src.rindex("</body>")
        src = src[:i] + overlay_html(to, doc_title, name, when, mail_when) + f'\n<script id="ci-consent-js">\n{_r("consent.js")}\n</script>\n' + src[i:]
    return src

def selftest():
    base = '<html><head></head><body><section class="slide cover-full"><h1>t</h1></section><section class="slide"><p>b</p></section></body></html>'
    c = apply_consent(base, "candidate", "a@example.com", "資料", "氏名")
    ok = all(s in c for s in ['id="ci-consent"', 'ci-consent-pending', 'ci-cand-print', '<noscript>', 'mailto:a@example.com', 'ci-pdf-consent-note', '#lk'])
    ok &= apply_consent(c, "candidate", "a@example.com", "資料") == c
    i = apply_consent(base, "internal", "a@example.com", "資料")
    ok &= 'id="ci-consent"' not in i and 'ci-consent-head' not in i and 'ci-pdf-consent-note' in i and 'ci-cand-print' not in i
    return ok

def main(argv):
    if "--selftest" in argv:
        ok = selftest(); print("apply_consent.py --selftest:", "OK" if ok else "FAIL"); return 0 if ok else 1
    ap = argparse.ArgumentParser()
    ap.add_argument("deck"); ap.add_argument("-o", "--out")
    ap.add_argument("--mode", default="candidate", choices=["candidate", "internal"])
    ap.add_argument("--to", required=True); ap.add_argument("--doc-title", required=True)
    ap.add_argument("--name", default=""); ap.add_argument("--when", default="面接が終了した時点"); ap.add_argument("--mail-when", default="面接が終わった時点")
    a = ap.parse_args(argv)
    out = apply_consent(open(a.deck, encoding="utf-8").read(), a.mode, a.to, a.doc_title, a.name, a.when, a.mail_when)
    open(a.out or a.deck, "w", encoding="utf-8").write(out)
    print(f"{os.path.basename(a.out or a.deck)}: consent {a.mode} OK"); return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
