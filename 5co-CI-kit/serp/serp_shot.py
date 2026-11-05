#!/usr/bin/env python3
"""serp_shot.py — Amazon.co.jp 検索結果の取得（最小アクセス・ログアウト・PC）。

規定の正＝FIGURES_GUIDE.md §2-4「Amazon検索順位の根拠ページ（SERP）」。顧客固有の値は
案件フォルダの `_context/serp_targets.yaml`（雛形＝SERP_TARGETS_TEMPLATE.yaml）だけに置く。

守ること（コードでも強制する）:
  - 未ログイン。新しいブラウザ context を毎回作り、**共有のログイン済みブラウザは使わない**
  - PC の画面。届け先は yaml の `capture.postal` に固定し、郵便番号は**1文字ずつキー入力**する
  - 再読込後の表示が指定の届け先と違うときは**検索しない**（スクショを残して停止）
  - 1回の実行で**最大5ページ**・読み込みの間隔は**12秒以上**（yaml で緩められない）
  - CAPTCHA・ブロックを見たら**その場で停止**（解かない・回避しない・リトライしない）
  - UA の末尾で自分から名乗る（Amazon Agent Terms）
  - 検索語は**一般語だけ**。`brand_regex` に当たる語（ブランド名入り）は実行前に落とす
  - 順位＝**スポンサー枠を除いたオーガニック順位**。「Amazonのおすすめ」「ベストセラー」の
    バッジが付いたカードは**順位に数える**（広告ではないため）
  - 毎回 `results.json`（と日付入りの写し）を書く＝取得日時・条件・順位の原本

Usage: python3 serp_shot.py [serp_targets.yaml] [-o outdir]
       python3 serp_shot.py --check-html FILE [FILE ...]   # 保存 HTML で届け先判定だけ（通信なし）
       python3 serp_shot.py --selftest                     # 純関数の確認（通信なし・数秒）
       python3 test_serp_mock.py                           # 127.0.0.1 の模擬ページで手順を通し確認
"""

import argparse, datetime, json, os, re, shutil, sys, time
from urllib.parse import urlparse
from pathlib import Path
from urllib.parse import quote_plus
import yaml
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

JST = datetime.timezone(datetime.timedelta(hours=9))
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
AMAZON = "https://www.amazon.co.jp"
# 実機（2026-11-01 診断）: modal は /portal-migration/hz/glow/get-rendered-address-selections で取得。保存先は glow 系 POST
ADDR_CHANGE_RE = re.compile(r"/glow/address-change|/gp/delivery/ajax/address-change|/glow/(?!get-rendered)[\w-]*(address|location|zip)", re.I)
ZIP_INPUT_SEL = "#GLUXZipUpdateInput_0, #GLUXZipUpdateInput"
# 「設定」後に出る確定/完了ボタン（押すと Amazon 側で location.reload される）
DONE_SEL = ("#GLUXConfirmClose, button[name='glowDoneButton'], input[name='glowDoneButton'], "
            "#GLUXConfirmClose-announce, .a-popover-footer .a-button-primary input")
VERIFY_TIMEOUT_S = 20
BLOCK_RE = re.compile(r"validateCaptcha|captchacharacters|ロボットではありません|automated access|api-services-support@amazon", re.I)

CARD_JS = r'''els=>els.map((e,i)=>{
  const h2=e.querySelector('h2'); const title=(h2&&h2.innerText||'').trim();
  const labSel='.puis-sponsored-label-text, .s-sponsored-label-text, .puis-label-popover-default, [aria-label*="スポンサー"], [data-component-type="sp-sponsored-result"]';
  const lab=e.querySelector(labSel);
  const txt=(e.innerText||'');
  const how=[];
  if(lab) how.push('label:'+(lab.className||lab.getAttribute('aria-label')||'el').toString().slice(0,60));
  if(/AdHolder/.test(e.className)) how.push('class:AdHolder');
  if(/^\s*スポンサー/m.test(txt)) how.push('text:スポンサー');
  // バッジ（Amazonのおすすめ／ベストセラー）は広告ではないので順位に数える。記録だけ残す
  const badges=[]; for(const b of ['Amazonのおすすめ','Amazon\'s Choice','ベストセラー','売れ筋ランキング']) if(txt.includes(b)) badges.push(b);
  const r=e.getBoundingClientRect();
  return {asin:e.getAttribute('data-asin'), data_index:e.getAttribute('data-index'), dom_order:i,
          sponsored:how.length>0, sponsored_how:how, badges:badges, title:title.slice(0,120),
          x:r.left+window.scrollX, y:r.top+window.scrollY, w:r.width, h:r.height};
})'''

PAGE_ADS_JS = r'''()=>{
  const q=s=>document.querySelectorAll(s).length;
  const body=document.body?document.body.innerText:'';
  return {
    sponsored_text_occurrences:(body.match(/スポンサー/g)||[]).length,
    adholder_elements:q('.AdHolder'),
    sp_label_elements:q('.puis-sponsored-label-text, .s-sponsored-label-text'),
    sponsored_brand_widgets:q('[cel_widget_id*="sb_"], [data-component-type*="sbv"], [cel_widget_id*="MAIN-SHOPPING_ADVISER"], [class*="sbx-"]'),
    sp_widgets:q('[cel_widget_id*="sp_atf"], [cel_widget_id*="sp_mtf"], [cel_widget_id*="sp_btf"], [cel_widget_id*="sp-"]'),
    video_widgets:q('[data-component-type="s-searchgrid-carousel"], [cel_widget_id*="VIDEO"]'),
  };
}'''

HEADER_JS = r'''()=>{
  // 帯の切り出しに使う座標。届け先の表示（郵便番号）が入らないよう、検索窓の左端より右だけを渡す
  const bb=el=>{if(!el)return null;const r=el.getBoundingClientRect();
                return {x:r.left+window.scrollX, y:r.top+window.scrollY, w:r.width, h:r.height};};
  return {search_bar:bb(document.querySelector('#nav-search-bar-form, #nav-search')),
          delivery:bb(document.querySelector('#glow-ingress-block, #nav-global-location-slot'))};
}'''

def now_jst():
    return datetime.datetime.now(JST)

def is_blocked(status, html, title):
    if status in (403, 429, 503):
        return f"HTTP {status}"
    if BLOCK_RE.search(html or ""):
        return "captcha/robot-check marker in HTML"
    if title and re.search(r"Sorry|申し訳", title) and "s-search-result" not in html:
        return f"error page title: {title}"
    return None

def annotate_crop(full_png, card, lines, out_png, pad=8):
    im = Image.open(full_png).convert("RGB")
    x0 = max(0, int(card["x"]) - pad); y0 = max(0, int(card["y"]) - pad)
    x1 = min(im.width, int(card["x"] + card["w"]) + pad); y1 = min(im.height, int(card["y"] + card["h"]) + pad)
    crop = im.crop((x0, y0, x1, y1))
    font = ImageFont.truetype(FONT, 14)
    # wrap lines to crop width (min 420px canvas)
    W = max(crop.width, 420)
    wrapped = []
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for ln in lines:
        cur = ""
        for ch in ln:
            if d0.textlength(cur + ch, font=font) > W - 16:
                wrapped.append(cur); cur = ch
            else:
                cur += ch
        wrapped.append(cur)
    H = crop.height + 10 + 20 * len(wrapped) + 8
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(crop, ((W - crop.width) // 2, 0))
    d = ImageDraw.Draw(canvas)
    d.line([(0, crop.height + 4), (W, crop.height + 4)], fill=(180, 180, 180))
    yy = crop.height + 10
    for ln in wrapped:
        d.text((8, yy), ln, font=font, fill=(30, 30, 30)); yy += 20
    canvas.save(out_png)

# ---------------------------------------------------------------- 届け先（純関数：保存 HTML でも検証できる）
def _clean(s):
    return re.sub(r"\s+", " ", (s or "").replace("\u200c", "").replace("\u200b", "")).strip()

def glow_from_html(html):
    """保存 HTML から (line1, line2) を取り出す。無ければ (None, None)。"""
    out = []
    for n in (1, 2):
        m = re.search(r'id="glow-ingress-line%d"[^>]*>(.*?)</span>' % n, html or "", re.S)
        out.append(_clean(re.sub(r"<[^>]+>", " ", m.group(1))) if m else None)
    return tuple(out)

DEFAULT_AREA_KEYS = {"105-0003": ["西新橋", "港区"], "100-0001": ["千代田区"]}

def area_keys_for(postal, cap=None):
    keys = (cap or {}).get("postal_area_keywords")
    return list(keys) if keys else DEFAULT_AREA_KEYS.get(postal, [])

def _has_key(text, k):
    if k == "港区":   # 名古屋市港区・大阪市港区 を除外（東京の表示は「港区西新橋」）
        return re.search(r"(?<!市)港区", text) is not None
    return k in text

def delivery_ok(line1, line2, postal, area_keys=None):
    """届け先郵便番号（または地名キーワード。105-0003 なら 西新橋/港区）が出ていれば True。
    基本は line2（旧レイアウト: line1=「お届け先」, line2=「港区西新橋 105-0003」）。
    11/1 に出た新レイアウト（line1=「お届け先: 登戸 214-0014」, line2=「場所を更新する」）では住所が line1 に入るので line1 も見る。"""
    keys = [postal] + list(area_keys if area_keys is not None else area_keys_for(postal))
    l1, l2 = _clean(line1), _clean(line2).replace("場所を更新する", "")
    l1 = l1.replace("お届け先", "")
    return any(_has_key(l2, k) for k in keys) or any(_has_key(l1, k) for k in keys)

def read_glow(pg):
    try:
        return pg.evaluate("""()=>{const g=id=>{const e=document.getElementById(id);return e?e.innerText:null};
                              return [g('glow-ingress-line1'), g('glow-ingress-line2')]}""")
    except Exception:
        return [None, None]

def wait_delivery(pg, postal, timeout_s=VERIFY_TIMEOUT_S, area_keys=None):
    """再読込後の #glow-ingress-line2 を最大 timeout_s 秒ポーリング（描画途中・古い表示の読み取り対策）。"""
    t_end = time.time() + timeout_s; l1 = l2 = None
    while True:
        l1, l2 = read_glow(pg)
        if delivery_ok(l1, l2, postal, area_keys):
            return True, _clean(f"{l1 or ''} {l2 or ''}")
        if time.time() >= t_end:
            return False, _clean(f"{l1 or ''} {l2 or ''}")
        pg.wait_for_timeout(1000)

def same_search(u1, u2):
    from urllib.parse import parse_qs
    a, b = urlparse(u1), urlparse(u2)
    return (a.netloc, a.path, parse_qs(a.query).get("k")) == (b.netloc, b.path, parse_qs(b.query).get("k"))

def cookie_names(ctx):
    # 値は記録しない（名前だけ。セッション維持の確認用）
    return sorted({c["name"] for c in ctx.cookies()})

def set_postcode(pg, postal, log, nav, area_keys=None, diag_dir=None):
    """届け先を通常 UI で設定。nav(kind, fn) はページ読み込みを数えて間隔を守るラッパー。
    返り値: (ok, delivery_text, http_status_of_reloaded_page)"""
    a, b = postal.split("-")
    xhrs = []   # 診断用: 設定中の XHR/fetch のパスだけ記録（クエリ・本文は残さない）
    def _on_req(r):
        if r.resource_type in ("xhr", "fetch"):
            u = urlparse(r.url); xhrs.append(f"{r.method} {u.netloc}{u.path}")
    pg.on("request", _on_req)
    def _diag(name):
        if diag_dir:
            try:
                pg.screenshot(path=str(Path(diag_dir) / f"{name}.png"))
                m = pg.evaluate("()=>{const e=document.querySelector('.a-popover-modal, .a-modal-scroller, #a-popover-content-1, [id^=a-popover-content]');return e?e.outerHTML:''}")
                if m: (Path(diag_dir) / f"{name}_modal.html").write_text(m, encoding="utf-8")
            except Exception:
                pass
    pg.click("#nav-global-location-popover-link", timeout=10000)
    pg.wait_for_selector(ZIP_INPUT_SEL, state="visible", timeout=15000)
    # 実機の欄は 3 桁 + 4 桁の 2 分割（#GLUXZipUpdateInput_0/_1, data-action=GLUXPostalInputAction）。
    # Amazon の JS はキー入力イベントで郵便番号を内部に保持するため、fill()（value 代入＋input イベントのみ）では
    # 「保存」を押しても何も送られない（11/1 10:15 診断: 欄の値は 105/0003 なのに POST なし・modal そのまま）。
    # → 1 文字ずつキー入力する。
    def _type(sel, txt):
        loc = pg.locator(sel)
        loc.click(); loc.fill(""); loc.press_sequentially(txt, delay=120)
    if pg.locator("#GLUXZipUpdateInput_0").count():
        _type("#GLUXZipUpdateInput_0", a); _type("#GLUXZipUpdateInput_1", b)
    else:
        _type("#GLUXZipUpdateInput", postal)
    pg.wait_for_timeout(500)
    try:
        vals = pg.evaluate("()=>['GLUXZipUpdateInput_0','GLUXZipUpdateInput_1','GLUXZipUpdateInput'].map(i=>{const e=document.getElementById(i);return e?i+'='+e.value:null}).filter(Boolean)")
        log.append("zip inputs after fill: " + ", ".join(vals))
    except Exception:
        pass
    _diag("postcode_1_filled")
    apply_sel = "#GLUXZipUpdate input" if pg.locator("#GLUXZipUpdate input").count() else "#GLUXZipUpdate"
    # 1) 「設定」→ address-change XHR の完了を待って中身を確認（旧版は 3 秒固定待ちで結果未確認）
    resp = None
    is_save = lambda r: bool(ADDR_CHANGE_RE.search(r.url)) and r.request.method == "POST"
    try:
        with pg.expect_response(is_save, timeout=10000) as ri:
            pg.click(apply_sel, timeout=6000)          # 「保存」(#GLUXZipUpdate .a-button-input)
        resp = ri.value
    except Exception as e:
        log.append("save POST not observed after 保存 click (" + type(e).__name__ + "); trying Enter in last zip field")
        try:
            last = "#GLUXZipUpdateInput_1" if pg.locator("#GLUXZipUpdateInput_1").count() else "#GLUXZipUpdateInput"
            with pg.expect_response(is_save, timeout=8000) as ri:
                pg.press(last, "Enter")
            resp = ri.value
        except Exception as e2:
            log.append("save POST not observed after Enter either (" + type(e2).__name__ + "); verifying after reload anyway")
    try:
        err = pg.evaluate("()=>['GLUXZipError','GLUXZipServerError'].filter(i=>{const e=document.getElementById(i);return e&&e.offsetParent!==null})")
        if err: log.append("zip error shown: " + ",".join(err))
    except Exception:
        pass
    if resp is not None:
        log.append(f"save POST: {urlparse(resp.url).path}")
    if resp is not None:
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        log.append(f"address-change XHR: HTTP {resp.status}, isValidAddress={body.get('isValidAddress')}, "
                   f"successful={body.get('successful')}")
        if resp.status != 200 or str(body.get("successful", 1)) in ("0", "False", "false"):
            return False, f"address-change rejected (HTTP {resp.status}, body={str(body)[:120]})", None
    _diag("postcode_2_after_apply")
    log.append("xhr/fetch during postcode step: " + "; ".join(dict.fromkeys(xhrs))[:1500])
    # 2) 確定/完了ボタン（出る版のみ）。押すと再読込が走るので 1 ページ読み込みとして数える
    st = None; reloaded = False
    try:
        pg.wait_for_selector(DONE_SEL, state="visible", timeout=5000)
        def click_done():
            with pg.expect_navigation(wait_until="domcontentloaded", timeout=10000) as ni:
                pg.locator(DONE_SEL).first.click(timeout=5000)
            return ni.value
        r = nav("done-button reload", click_done)
        st = r.status if r else None; reloaded = True
        log.append("done/確定 button clicked → page reloaded")
    except Exception as e:
        log.append("no done-button reload (" + type(e).__name__ + ")")
    # 3) 自前で再読込（確定ボタンで再読込されなかった場合）
    if not reloaded:
        r = nav("explicit reload", lambda: pg.reload(wait_until="domcontentloaded", timeout=45000))
        st = r.status if r else None
        log.append("explicit page reload after address-change")
    # 4) 再読込後の表示を最大 20 秒再読
    ok, text = wait_delivery(pg, postal, area_keys=area_keys)
    log.append(f"delivery after reload: '{text}' → {'OK' if ok else 'NG'}")
    return ok, text, st

def cond_delivery(delivery, postal):
    d = (delivery or "").replace("\u200c", "")
    if postal in d:
        return f"届け先{postal}"
    return f"届け先:{d.replace('お届け先','').strip() or '不明'}（{postal}の設定は未反映）"

def read_delivery(pg):
    try:
        return re.sub(r"\s+", " ", pg.inner_text("#glow-ingress-block", timeout=3000)).strip()
    except Exception:
        return None

# ---------------------------------------------------------------- 実行前の確認（純関数）
BRAND_FREE_MSG = "検索語にブランド名が入っています（一般語だけで撮る）"

def generic_terms_only(terms, brand_regex):
    """ブランド名に当たる検索語を返す。空なら一般語だけ＝OK。"""
    rx = re.compile(brand_regex, re.I)
    return [t for t in terms if rx.search(t)]

SHARED_BROWSER_ENV = ("CHROME_USER_DATA_DIR", "PLAYWRIGHT_USER_DATA_DIR", "PLAYWRIGHT_CHROMIUM_USER_DATA_DIR")

def shared_browser_risk(cap, env):
    """共有のログイン済みブラウザを使おうとしていないか。使っていたら理由を返す。"""
    if str(cap.get("login", "none")).lower() != "none":
        return f"capture.login は none のみ（指定: {cap.get('login')}）"
    for k in ("user_data_dir", "profile", "storage_state", "executable_path", "cdp_url"):
        if cap.get(k):
            return f"capture.{k} は使えない（毎回まっさらな context で撮る）"
    for k in SHARED_BROWSER_ENV:
        if env.get(k):
            return f"環境変数 {k} が設定されている（共有のログイン済みブラウザを指している）"
    return None

def selftest():
    """通信しない確認。届け先の判定・一般語の確認・共有ブラウザの禁止。"""
    P = "105-0003"; K = area_keys_for(P, {"postal_area_keywords": ["西新橋", "港区"]})
    cases = [(("お届け先", "港区西新橋 105-0003\u200c"), True), (("お届け先: 港区西新橋 105-0003", "場所を更新する"), True),
             (("お届け先", "港区西新橋"), True), (("お届け先", "東京都港区"), True),
             (("お届け先: 登戸 214-0014", "場所を更新する"), False), (("お届け先", "アメリカ合衆国"), False),
             (("お届け先", "名古屋市港区 455-0001"), False), (("お届け先", "千代田区千代田 100-0001"), False),
             ((None, None), False)]
    for (l1, l2), want in cases:
        got = delivery_ok(l1, l2, P, K)
        assert got == want, (l1, l2, got, want)
    print(f"OK 届け先の判定 {len(cases)}件")
    br = r"\bBRANDX\b|ブランドX"
    assert generic_terms_only(["マニキュア", "ネイル 強化剤"], br) == []
    assert generic_terms_only(["BRANDX 強化剤", "マニキュア"], br) == ["BRANDX 強化剤"]
    assert generic_terms_only(["ブランドX 爪"], br) == ["ブランドX 爪"]
    print("OK 一般語だけの確認 3件")
    assert shared_browser_risk({"login": "none"}, {}) is None
    assert shared_browser_risk({"login": "shared"}, {}) is not None
    assert shared_browser_risk({"login": "none", "user_data_dir": "/home/box/.config/chrome"}, {}) is not None
    assert shared_browser_risk({"login": "none"}, {"CHROME_USER_DATA_DIR": "/x"}) is not None
    print("OK 共有ブラウザの禁止 4件")
    assert cap_limits({"delay_sec_min": 1, "max_page_loads": 50}) == (12, 5)
    assert cap_limits({"delay_sec_min": 30, "max_page_loads": 3}) == (30, 3)
    print("OK 上限（間隔12秒以上・5ページまで）2件")
    print("selftest: OK")
    return 0

def cap_limits(cap):
    """yaml で緩められない上限。(待ち秒, ページ上限)"""
    return max(12, cap.get("delay_sec_min", 12)), min(5, cap.get("max_page_loads", 5))

# ---------------------------------------------------------------- オフライン確認
def check_html(paths, postal, area_keys):
    """保存 HTML で判定（純関数）＋ 通信を全遮断した Chromium で read_glow/wait_delivery も確認。"""
    rc = 0
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True); ctx = br.new_context()
        ctx.route("**/*", lambda route: route.abort())   # 一切外に出さない
        pg = ctx.new_page()
        for f in paths:
            html = open(f, encoding="utf-8", errors="replace").read()
            l1, l2 = glow_from_html(html)
            ok_static = delivery_ok(l1, l2, postal, area_keys)
            html_noscript = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
            pg.set_content(html_noscript, wait_until="domcontentloaded")
            ok_dom, text = wait_delivery(pg, postal, timeout_s=2, area_keys=area_keys)
            print(f"{'OK' if ok_static else 'NG'} static | {'OK' if ok_dom else 'NG'} dom | line1='{l1}' line2='{l2}' | {f}")
            if ok_static != ok_dom:
                rc = 2
        br.close()
    return rc

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="?", default="serp_targets.yaml")
    ap.add_argument("-o", "--outdir", default=".")
    ap.add_argument("--check-html", nargs="+", metavar="FILE", help="保存 HTML で届け先判定だけ行う（通信なし）")
    ap.add_argument("--selftest", action="store_true", help="純関数の確認だけ（Amazon に通信しない）")
    ap.add_argument("--max-loads", type=int, default=None, help="上限をさらに下げる（診断用。5 を超える値は無視）")
    ap.add_argument("--postal", default=None, help="--check-html 用の郵便番号（既定は yaml の capture.postal）")
    ap.add_argument("--base-url", default=AMAZON, help="テスト用。127.0.0.1 の模擬サーバー以外を指定しないこと")
    ap.add_argument("--test-delay", type=float, default=None, help="--base-url が 127.0.0.1 の時だけ有効")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if args.check_html:
        c = yaml.safe_load(open(args.targets, encoding="utf-8"))["capture"] if Path(args.targets).exists() else {}
        postal = args.postal or c.get("postal", "105-0003")
        sys.exit(check_html(args.check_html, postal, area_keys_for(postal, c if postal == c.get("postal") else None)))
    base = args.base_url.rstrip("/")
    is_mock = urlparse(base).hostname in ("127.0.0.1", "localhost")
    if base != AMAZON and not is_mock:
        sys.exit("--base-url は Amazon 本番か 127.0.0.1 の模擬サーバーのみ")
    cfg = yaml.safe_load(open(args.targets, encoding="utf-8"))
    cap = cfg["capture"]; out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    brand_re = re.compile(cfg["brand_regex"], re.I); asins = set(cfg.get("asins", []))
    # 実行前の確認（どちらも止める。あとから直せない取得をしないため）
    why = shared_browser_risk(cap, os.environ)
    if why:
        sys.exit(f"共有のログイン済みブラウザは使わない: {why}")
    branded = generic_terms_only(cfg["terms"], cfg["brand_regex"])
    if branded:
        sys.exit(f"{BRAND_FREE_MSG}: {branded}")
    thr = cfg["top_threshold"]["pc"]; delay, max_loads = cap_limits(cap)
    if args.max_loads is not None:
        max_loads = min(max_loads, args.max_loads)
    if is_mock and args.test_delay is not None:
        delay = args.test_delay
    src = cfg["source_label"]
    results = {"client": cfg["client"], "conditions": cap, "source_label": src, "page_loads": 0,
               "started_at": now_jst().strftime("%Y-%m-%d %H:%M:%S JST"), "log": [], "terms": [], "stopped": None}
    if is_mock:
        results["mock_base_url"] = base
    captions = []
    loads = 0; last_load = 0.0

    def nav(kind, fn):
        """全ページ読み込み（goto / reload / 確定ボタンによる再読込）をここで数え、間隔を守る。"""
        nonlocal loads, last_load
        if loads >= max_loads:
            raise RuntimeError(f"max_page_loads reached before {kind}")
        wait = delay - (time.time() - last_load)
        if last_load and wait > 0:
            time.sleep(wait)
        loads += 1; results["page_loads"] = loads   # 試行した時点で数える（失敗しても上限側に寄せる）
        try:
            return fn()
        finally:
            last_load = time.time()

    def polite_goto(pg, url):
        resp = nav("goto", lambda: pg.goto(url, wait_until="domcontentloaded", timeout=45000))
        pg.wait_for_timeout(3500)
        return resp.status if resp else None

    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        tmp = br.new_context(); tp = tmp.new_page(); base_ua = tp.evaluate("navigator.userAgent"); tmp.close()
        ua = f"{base_ua} {cap.get('user_agent_suffix','')}".strip()
        results["user_agent"] = ua
        # 1 つの context を最初から最後まで使う（Cookie/session-id を検索ページまで保持）
        ctx = br.new_context(locale=cap["locale"], timezone_id=cap["timezone"], viewport=cap["viewport"], user_agent=ua)
        if is_mock:
            ctx.route("**/*", lambda route: route.continue_() if urlparse(route.request.url).hostname in ("127.0.0.1", "localhost") else route.abort())
        pg = ctx.new_page()
        reuse_first = False; st2 = None   # 届け先確認済みの再読込ページを 1 語目に再利用
        try:
            first_url = base + "/s?k=" + quote_plus(cfg["terms"][0])
            st = polite_goto(pg, first_url)
            html = pg.content(); why = is_blocked(st, html, pg.title())
            if why:
                pg.screenshot(path=str(out / "blocked_setup.png"))
                results["stopped"] = f"setup: {why}"; raise SystemExit
            results["log"].append("cookies before postcode: " + ",".join(cookie_names(ctx)))
            try:
                ok, dtext, st2 = set_postcode(pg, cap["postal"], results["log"], nav, area_keys_for(cap["postal"], cap), diag_dir=out)
            except Exception as e:
                ok, dtext, st2 = False, "postcode step error: " + str(e)[:200], None
                results["log"].append(dtext)
            results["log"].append("cookies after postcode: " + ",".join(cookie_names(ctx)))
            html = pg.content(); why = is_blocked(st2, html, pg.title())
            if why:
                pg.screenshot(path=str(out / "blocked_postcode.png"))
                results["stopped"] = f"postcode step: {why}"; raise SystemExit
            if not ok:
                pg.screenshot(path=str(out / "postcode_not_applied.png"))
                (out / "postcode_not_applied.html").write_text(html, encoding="utf-8")
                results["stopped"] = (f"delivery not {cap['postal']} after reload+{VERIFY_TIMEOUT_S}s re-read "
                                      f"('{dtext}'); aborted before searches")
                raise SystemExit
            reuse_first = same_search(pg.url, first_url)
            for ti, term in enumerate(cfg["terms"], 1):
                url = base + "/s?k=" + quote_plus(term)
                if ti == 1 and reuse_first:
                    st = st2; results["log"].append("t01 = reloaded page after postcode (no extra load)")
                else:
                    st = polite_goto(pg, url)
                ts = now_jst()
                html = pg.content(); why = is_blocked(st, html, pg.title())
                tag = f"t{ti:02d}"
                if why:
                    pg.screenshot(path=str(out / f"{tag}_blocked.png"))
                    results["stopped"] = f"{term}: {why}"; break
                (out / f"{tag}_raw.html").write_text(html, encoding="utf-8")
                # 描画途中の古い表示で誤停止しないよう、各語でも最大 20 秒再読してから判定
                postal_ok, _ = wait_delivery(pg, cap["postal"], area_keys=area_keys_for(cap["postal"], cap))
                delivery = read_delivery(pg)
                if not postal_ok:
                    results["stopped"] = f"delivery shows '{delivery}', not {cap['postal']}; aborted at {tag}"
                    pg.screenshot(path=str(out / f"{tag}_wrong_delivery.png")); break
                vp = out / f"{tag}_viewport.png"; pg.screenshot(path=str(vp))
                # scroll within the same page to trigger lazy images (no extra loads)
                for _ in range(12):
                    pg.mouse.wheel(0, 900); pg.wait_for_timeout(350)
                pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(800)
                fp = out / f"{tag}_fullpage.png"; pg.screenshot(path=str(fp), full_page=True)
                cards = pg.eval_on_selector_all('div[data-component-type="s-search-result"]', CARD_JS)
                page_ads = pg.evaluate(PAGE_ADS_JS)
                header_box = pg.evaluate(HEADER_JS)   # 帯の切り出し用（検索窓の左端より右だけを使う）
                o = s = 0
                for c in cards:
                    if not c["asin"]:
                        c["organic_rank"] = c["sponsored_rank"] = None; continue
                    if c["sponsored"]:
                        s += 1; c["sponsored_rank"] = s; c["organic_rank"] = None
                    else:
                        o += 1; c["organic_rank"] = o; c["sponsored_rank"] = None
                    c["is_client"] = bool(c["asin"] in asins or brand_re.search(c["title"]))
                    c["asin_listed"] = c["asin"] in asins
                cond = f"ログアウト・{cond_delivery(delivery, cap['postal'])}・PC {cap['viewport']['width']}x{cap['viewport']['height']}"
                tstr = ts.strftime("%Y-%m-%d %H:%M JST")
                src_eff = src if postal_ok else src.replace(f"届け先{cap['postal']}", "届け先" + cond_delivery(delivery, cap["postal"]).replace("届け先:", "").split("（")[0])
                for kind, path in (("viewport", vp), ("fullpage", fp)):
                    captions.append(f"{path.name}\t検索語「{term}」／{tstr}／{cond}／出所: {src_eff}")
                crops = []
                client_cards = [c for c in cards if c.get("is_client")]
                for c in client_cards[:6]:
                    rank_txt = (f"通常順位 {c['organic_rank']}位（スポンサー枠を除く）" if c["organic_rank"]
                                else f"スポンサー枠 SP{c['sponsored_rank']}")
                    in_top = bool(c["organic_rank"] and c["organic_rank"] <= thr)
                    name = f"{tag}_crop_{'org%02d' % c['organic_rank'] if c['organic_rank'] else 'sp%02d' % c['sponsored_rank']}_{c['asin']}.png"
                    lines = [f"検索語「{term}」／{rank_txt}／ASIN {c['asin']}",
                             f"取得 {tstr}／{cond}",
                             f"出所: {src_eff}（5 co. 取得）"]
                    annotate_crop(fp, c, lines, out / name)
                    crops.append({"file": name, "asin": c["asin"], "organic_rank": c["organic_rank"],
                                  "sponsored_rank": c["sponsored_rank"], "in_top": in_top})
                    captions.append(f"{name}\t" + "／".join(lines))
                results["terms"].append({
                    "term": term, "url": url, "http_status": st, "fetched_at": ts.strftime("%Y-%m-%d %H:%M:%S JST"),
                    "delivery_shown": delivery, "n_cards": len(cards), "n_sponsored_cards": s, "page_ad_markers": page_ads,
                    "client_cards": [{k: c[k] for k in ("asin", "organic_rank", "sponsored_rank", "sponsored_how", "badges", "asin_listed", "title")} for c in client_cards],
                    "best_client_organic_rank": min([c["organic_rank"] for c in client_cards if c["organic_rank"]], default=None),
                    "top_threshold": thr, "shots": {"viewport": vp.name, "fullpage": fp.name}, "crops": crops,
                    "header_box": header_box,
                    "cards": cards})
                print(f"[{tag}] {term}: HTTP {st}, cards={len(cards)}, sponsored={s}, delivery={delivery}, "
                      f"顧客 organic={[c['organic_rank'] for c in client_cards if c['organic_rank']][:8]} sp={[c['sponsored_rank'] for c in client_cards if c['sponsored_rank']]}", flush=True)
        except SystemExit:
            pass
        except Exception as e:
            results["stopped"] = (results["stopped"] or "") + f" error: {e}"[:300]
        finally:
            br.close()
    results["finished_at"] = now_jst().strftime("%Y-%m-%d %H:%M:%S JST")
    results["run_date"] = results["started_at"][:10]
    json.dump(results, open(out / "results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    # 毎回の原本を日付つきでも残す（前回比＝serp_diff.py はこの2つを突き合わせる）
    dated = out / ("results_%s.json" % results["started_at"][:16].replace(" ", "_").replace(":", ""))
    shutil.copyfile(out / "results.json", dated)
    (out / "captions.tsv").write_text("\n".join(captions) + "\n", encoding="utf-8")
    print("page_loads:", results["page_loads"], "stopped:", results["stopped"])

if __name__ == "__main__":
    main()
