#!/usr/bin/env python3
"""手元確認用 PDF（ダウンロードボタン用）を作り、HTML に埋め込む。ci-pdf-save-btn v7（取扱注意の下に同意+PDF中央・ボタン1.5×・agree-stack bottom:48・pad:320・2026-10-28）
使い方: python3 5co-CI-kit/make_handout_pdf.py <deck.html> [...]
 1) 最終ページの BLOCK / STYLE / SCRIPT を v3 に差し替え（window.print() は使わない）
 2) Chrome ヘッドレスで #static を印刷→ <stem>_手元確認用.pdf（同じフォルダ）
 3) その PDF を base64 で HTML に埋め込み、ボタンは Blob ダウンロード（file:// でもメール添付でも動く）
    埋め込みが無い／失敗時は <a href=隣のPDF download> にフォールバック。
※ これはメール送付用の正式 PDF ではない（正式版は承認後 ci-finalize.sh --pdf）。"""
import base64, os, re, subprocess, sys, urllib.parse

CONF_L1 = "複数社の機密保持契約の対象・社外秘。許可なき転送・再配布・数値の抽出転載を禁じます。"
CONF_L2 = "漏洩時は契約違反として請求・是正の対象になり得ます。使用後は必ずシュレッダーにかけてください。"
CAP = "上記に同意して"

def block(pdfname):
    conf = ('<aside class="ci-conf-block" role="note" aria-label="取扱注意">'
            '<span class="ci-conf-k">取扱注意</span>'
            f'<p class="ci-conf-body">{CONF_L1}<br>{CONF_L2}</p></aside>')
    pdf = ('<div class="ci-pdf-save-wrap"><div class="ci-pdf-save-row">'
           f'<span class="ci-pdf-save-cap">{CAP}</span>'
           f'<a class="ci-pdf-save" href="{urllib.parse.quote(pdfname)}" download="{pdfname}" data-ci-pdf-save '
           'aria-label="手元確認用PDFをダウンロード" title="手元確認用PDF（正式版ではありません）をダウンロードします">PDFをダウンロード</a></div></div>')
    return f'<div class="ci-agree-stack">{conf}{pdf}</div>'



STYLE = """<style id="ci-pdf-save-btn-css">
/* ci-pdf-save-btn v7 — 取扱注意の下に「上記に同意して」+PDF（中央）；ボタン1.5×；footer空き≥16px（2026-10-28） */
:root{ --insight:#f6b44a; --insight-ink:#5a3500; --insight-line:#d97706; --insight-bg:#fdeacb; }
/* 画面でも底を確保：agree-stack（アンバー+PDF行）全体ぶん */
section.slide:has(> .ci-agree-stack){padding-bottom:320px;}
.ci-agree-stack{
  position:absolute; left:50%; bottom:48px; transform:translateX(-50%); z-index:5;
  width:min(860px, calc(100% - 72px)); box-sizing:border-box;
  display:flex; flex-direction:column; align-items:center; gap:16px;
}
.ci-conf-block{
  position:relative; left:auto; bottom:auto; transform:none; z-index:auto;
  width:100%; box-sizing:border-box;
  display:flex; flex-direction:column; align-items:center; gap:6px;
  padding:8px 20px 8px;
  background:var(--insight-bg); border:2.5px solid var(--insight); border-radius:10px;
  text-align:center; color:var(--insight-ink);
  box-shadow:0 0 0 4px rgba(246,180,74,.18);
}
.ci-conf-block .ci-conf-k{
  display:inline-block; margin:0; padding:3px 14px;
  background:var(--insight); color:var(--insight-ink);
  border:1px solid var(--insight-line); border-radius:4px;
  font-family:var(--sans-ja, inherit); font-size:13px; font-weight:700;
  letter-spacing:.14em;
}
.ci-conf-block .ci-conf-body{
  margin:0; font-family:var(--serif-ja, inherit); font-size:13.5px; line-height:1.55;
  font-weight:600; color:var(--insight-ink); text-align:center; max-width:52em;
}
/* PDF行＝アンバー直下・中央（1.5× pill: 12→18 / 4 14→6 21 / dot 7→10.5） */
.ci-pdf-save-wrap{position:relative; right:auto; bottom:auto; left:auto; z-index:auto;
  display:flex; justify-content:center; width:100%;}
.ci-pdf-save-row{display:flex; align-items:center; gap:16px;}
.ci-pdf-save-cap{font-family:var(--serif-ja); font-size:14px; line-height:1.4; color:var(--ink-60); white-space:nowrap;}
.ci-pdf-save{display:inline-flex; align-items:center; gap:.4em; text-decoration:none;
  border:1px solid var(--ink-14); background:var(--white); color:var(--ink);
  border-radius:999px; padding:6px 21px; font-size:18px; line-height:1.4;
  font-family:var(--sans-ja, inherit); letter-spacing:.04em; cursor:pointer; white-space:nowrap;
  transition:border-color .15s, background .15s;}
.ci-pdf-save::before{content:""; width:10.5px; height:10.5px; border-radius:50%; background:var(--crystal);}
.ci-pdf-save:hover,.ci-pdf-save:focus-visible{border-color:var(--ink); background:var(--crystal-25); outline:none;}
.slide.dark .ci-pdf-save{background:transparent; color:var(--crystal); border-color:rgba(195,215,238,.45);}
.slide.dark .ci-pdf-save-cap{color:rgba(195,215,238,.75);}
@media print{
  .ci-pdf-save-row{display:none !important;}
  .ci-agree-stack{gap:0;}
  section.slide:has(> .ci-agree-stack){padding-bottom:180px;}
  .ci-conf-block{box-shadow:none; -webkit-print-color-adjust:exact; print-color-adjust:exact;}
}
</style>"""


SCRIPT = """<script>
/* ci-pdf-save-btn v3: 印刷ダイアログは開かない。埋め込みの手元確認用PDFを Blob にしてブラウザのダウンロードを開始。
   埋め込みが無いときは <a download>（隣の PDF）にそのまま任せる。 */
(function(){
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest && e.target.closest("[data-ci-pdf-save]");
    if (!a) return;
    var src = document.getElementById("ci-handout-pdf");
    if (!src || !window.Blob || !window.URL) return;
    try {
      var b64 = src.textContent.replace(/\\s+/g, ""), bin = atob(b64), n = bin.length, u8 = new Uint8Array(n);
      for (var i = 0; i < n; i++) u8[i] = bin.charCodeAt(i);
      var url = URL.createObjectURL(new Blob([u8], {type: "application/pdf"}));
      var t = document.createElement("a");
      t.href = url; t.download = src.getAttribute("data-name") || a.getAttribute("download") || "handout.pdf";
      t.style.display = "none"; document.body.appendChild(t);
      e.preventDefault(); e.stopPropagation();
      t.click();
      setTimeout(function(){ URL.revokeObjectURL(url); t.remove(); }, 4000);
    } catch (err) { /* 失敗時は <a download> の既定動作 */ }
  }, true);
})();
</script>"""

PRINT_CSS = ('<style id="ci-finalize-print">@media print{@page{size:297mm 210mm;margin:0} .slide{page-break-after:always;'
             'break-after:page;box-shadow:none!important;margin:0!important} .slide:last-child{page-break-after:auto}}</style>')

def chrome_pdf(html_path, pdf_path):
    d = os.path.dirname(os.path.abspath(html_path)); stem = os.path.basename(html_path)[:-5]
    inj = os.path.join(d, f".ci-handout.{stem}.html")
    s = open(html_path, encoding="utf-8").read()
    s = re.sub(r'<script type="application/pdf;base64" id="ci-handout-pdf".*?</script>', "", s, flags=re.S)
    s = s.replace("</head>", PRINT_CSS + "</head>", 1)
    open(inj, "w", encoding="utf-8").write(s)
    try:
        url = "file://" + urllib.parse.quote(inj) + "#static"
        subprocess.run(["google-chrome", "--headless", "--disable-gpu", "--no-sandbox", "--no-pdf-header-footer",
                        "--virtual-time-budget=8000", f"--print-to-pdf={pdf_path}", url],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    finally:
        os.remove(inj)
    assert os.path.getsize(pdf_path) > 10000, pdf_path

def process(path):
    d = os.path.dirname(os.path.abspath(path)); stem = os.path.basename(path)[:-5]
    pdfname = f"{stem}_手元確認用.pdf"; pdf = os.path.join(d, pdfname)
    s = open(path, encoding="utf-8").read()
    # BLOCK: agree-stack 優先、なければ旧 conf+pdf / pdf-only を差し替え
    if '<div class="ci-agree-stack">' in s:
        s, n1 = re.subn(r'<div class="ci-agree-stack">.*?</div>\s*</div>', lambda m: block(pdfname), s, count=1, flags=re.S)
    else:
        s, n1 = re.subn(
            r'(?:<aside class="ci-conf-block"[^>]*>.*?</aside>\s*)?<div class="ci-pdf-save-wrap">.*?</div></div>',
            lambda m: block(pdfname), s, count=1, flags=re.S)
    # STYLE+SCRIPT: id付き（現行）または旧コメント付きブロックを差し替え
    s, n2 = re.subn(
        r'(?:<!-- ci-pdf-save-btn v\d+ -->\s*)?<style(?: id="ci-pdf-save-btn-css")?>\s*/\* ci-pdf-save-btn v\d+.*?</style>\s*<script>\s*/\* ci-pdf-save-btn v3:.*?</script>',
        lambda m: "<!-- ci-pdf-save-btn v7 -->\n" + STYLE + "\n" + SCRIPT, s, count=1, flags=re.S)
    s = re.sub(r'<script type="application/pdf;base64" id="ci-handout-pdf".*?</script>\n?', "", s, flags=re.S)
    assert n1 == 1 and n2 == 1, (path, n1, n2)
    assert "window.print()" not in s.split("ci-pdf-save-btn v3", 1)[1]
    open(path, "w", encoding="utf-8").write(s)
    chrome_pdf(path, pdf)
    b64 = base64.b64encode(open(pdf, "rb").read()).decode()
    emb = f'<script type="application/pdf;base64" id="ci-handout-pdf" data-name="{pdfname}">{b64}</script>\n'
    s = s.replace("</body>", emb + "</body>", 1)
    open(path, "w", encoding="utf-8").write(s)
    print(f"{path}\n  PDF: {pdf} ({os.path.getsize(pdf):,} B)  HTML: {os.path.getsize(path):,} B")

if __name__ == "__main__":
    for p in sys.argv[1:]: process(p)
