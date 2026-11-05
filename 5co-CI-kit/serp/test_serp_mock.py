#!/usr/bin/env python3
"""serp_shot.py の届け先手順を 127.0.0.1 の模擬 Amazon で通し確認する（Amazon への通信なし）。
顧客の値は使わない（この場で作る雛形の yaml で回す）。
serp_shot.py 側でも 127.0.0.1 以外へのリクエストは route で abort される。

シナリオ:
  done    : 設定→XHR→確定ボタン(location.reload)→表示 105-0003        → 検索まで進む
  nodone  : 確定ボタンなし → スクリプトが自前で reload               → 検索まで進む
  late    : 再読込直後は古い表示（登戸）、4 秒後に 105-0003 に更新     → 20 秒リトライで進む
  ignore  : XHR は 200 だが住所が保存されない（11/1 の症状）          → 検索前に停止＋スクショ
  reject  : XHR が successful=0                                        → 検索前に停止
  nagoya  : 保存後の表示が「名古屋市港区 455-0001」                    → 「港区」でも通さず停止
Usage: python3 test_postcode_mock.py
"""
import json, subprocess, sys, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
TARGETS = {"client": "テスト", "brand_regex": r"\bTESTBRAND\b",
           "terms": ["一般語A", "一般語B", "一般語C"],
           "asins": ["B0F5PXVPF7"], "top_threshold": {"pc": 10},
           "capture": {"login": "none", "postal": "105-0003",
                       "postal_area_keywords": ["西新橋", "港区"], "device": "pc",
                       "viewport": {"width": 1366, "height": 900}, "locale": "ja-JP",
                       "timezone": "Asia/Tokyo", "user_agent_suffix": "Agent/5co-serp-shot",
                       "delay_sec_min": 12, "max_page_loads": 5, "on_captcha": "stop"},
           "source_label": "Amazon.co.jp 検索結果（ログアウト・PC）"}
MODE = {"m": "done"}; HITS = {"s": 0}

PAGE = """<!doctype html><html lang="ja"><head><meta charset="utf-8"><title>Amazon.co.jp : mock</title></head><body>
<div id="nav-global-location-slot"><a id="nav-global-location-popover-link" href="">
<div id="glow-ingress-block"><span id="glow-ingress-line1">%(l1)s</span> <span id="glow-ingress-line2">%(l2)s</span></div></a></div>
<div id="modal"></div>
<div class="s-main-slot">
 <div data-component-type="s-search-result" data-asin="B0F5PXVPF7" data-index="1" style="width:300px;height:200px"><h2>テスト商品 mock</h2></div>
 <div data-component-type="s-search-result" data-asin="B000000000" data-index="2" style="width:300px;height:200px"><h2>Other</h2></div>
</div>
<script>
const MODE=%(mode)s;
%(late)s
document.getElementById('nav-global-location-popover-link').addEventListener('click',e=>{e.preventDefault();
 setTimeout(()=>{document.getElementById('modal').innerHTML=
  '<input id="GLUXZipUpdateInput_0" maxlength="3"><input id="GLUXZipUpdateInput_1" maxlength="4"><span class="a-button" id="GLUXZipUpdate"><span class="a-button-inner"><input class="a-button-input" type="submit"><span class="a-button-text">保存</span></span></span><div id="done"></div>';
  // 実機同様: 郵便番号はキー入力(keyup)でのみ内部状態に入る。fill() だけでは保存しても何も送らない
  const st={};
  ['GLUXZipUpdateInput_0','GLUXZipUpdateInput_1'].forEach(i=>document.getElementById(i).addEventListener('keyup',e=>{st[i]=e.target.value}));
  const save=async ()=>{
    const z=(st.GLUXZipUpdateInput_0||'')+'-'+(st.GLUXZipUpdateInput_1||'');
    if(!/^[0-9]{3}-[0-9]{4}$/.test(z)) return;
    await new Promise(r=>setTimeout(r,800));
    await fetch('/portal-migration/hz/glow/address-change?actionSource=glow',{method:'POST',body:JSON.stringify({zipCode:z})});
    if(MODE!=='nodone'){document.getElementById('done').innerHTML='<span id="GLUXConfirmClose-announce"><input id="GLUXConfirmClose" type="submit" value="完了"></span>';
      document.getElementById('GLUXConfirmClose').addEventListener('click',()=>setTimeout(()=>location.reload(),300));}
  };
  document.querySelector('#GLUXZipUpdate .a-button-inner').addEventListener('click',save);
  },500);});
</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/s":
            self.send_response(404); self.end_headers(); return
        HITS["s"] += 1
        zipped = "mockzip=105-0003" in (self.headers.get("Cookie") or "")
        old = ("お届け先: 登戸 214-0014", "場所を更新する"); new = ("お届け先", "港区西新橋 105-0003\u200c")
        late = ""
        if zipped and MODE["m"] == "nagoya":
            l1, l2 = ("お届け先", "名古屋市港区 455-0001")
        elif zipped and MODE["m"] == "late":
            l1, l2 = old
            late = "setTimeout(()=>{document.getElementById('glow-ingress-line1').innerText='%s';document.getElementById('glow-ingress-line2').innerText='%s'},4000);" % new
        else:
            l1, l2 = new if zipped else old
        body = (PAGE % {"l1": l1, "l2": l2, "mode": json.dumps(MODE["m"]), "late": late}).encode()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); self.rfile.read(n)
        self.send_response(200); self.send_header("Content-Type", "application/json")
        if MODE["m"] not in ("ignore", "reject"):
            self.send_header("Set-Cookie", "mockzip=105-0003; Path=/")
        self.end_headers()
        ok = 0 if MODE["m"] == "reject" else 1
        self.wfile.write(json.dumps({"isValidAddress": ok, "successful": ok}).encode())

def targets_file():
    import yaml
    f = Path(tempfile.mkdtemp(prefix="mock_targets_")) / "serp_targets.yaml"
    f.write_text(yaml.safe_dump(TARGETS, allow_unicode=True), encoding="utf-8")
    return f


def run(mode, port, targets):
    MODE["m"] = mode; HITS["s"] = 0
    out = Path(tempfile.mkdtemp(prefix=f"mock_{mode}_"))
    p = subprocess.run([sys.executable, str(HERE / "serp_shot.py"), str(targets), "-o", str(out),
                        "--base-url", f"http://127.0.0.1:{port}", "--test-delay", "0.5"],
                       capture_output=True, text=True, timeout=240)
    r = json.load(open(out / "results.json", encoding="utf-8"))
    return r, out, p

def unit_checks():
    sys.path.insert(0, str(HERE)); import serp_shot as S
    S.selftest()      # 純関数（届け先の判定・一般語・共有ブラウザの禁止・上限）
    P = "105-0003"; K = S.area_keys_for(P, TARGETS["capture"])
    cases = [(("お届け先", "港区西新橋 105-0003\u200c"), True), (("お届け先: 港区西新橋 105-0003", "場所を更新する"), True),
             (("お届け先", "港区西新橋"), True), (("お届け先", "東京都港区"), True),
             (("お届け先: 登戸 214-0014", "場所を更新する"), False), (("お届け先", "アメリカ合衆国"), False),
             (("お届け先", "名古屋市港区 455-0001"), False), (("お届け先", "千代田区千代田 100-0001"), False), ((None, None), False)]
    for (l1, l2), want in cases:
        got = S.delivery_ok(l1, l2, P, K)
        assert got == want, (l1, l2, got)
    print(f"PASS unit delivery_ok ({len(cases)} cases)")

def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), H); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    unit_checks()
    targets = targets_file()
    expect = {"done": True, "nodone": True, "late": True, "ignore": False, "reject": False, "nagoya": False}
    fails = 0
    for mode, should_search in expect.items():
        r, out, p = run(mode, port, targets)
        searched = len(r["terms"]) == 3
        stop_shot = (out / "postcode_not_applied.png").exists()
        ok = (searched == should_search) and (should_search or (stop_shot and not r["terms"])) \
             and r["page_loads"] <= 5 and r["page_loads"] == HITS["s"]
        fails += not ok
        print(f"{'PASS' if ok else 'FAIL'} {mode:7s} terms={len(r['terms'])} page_loads={r['page_loads']} server_hits={HITS['s']} "
              f"stopped={r['stopped']!r}")
        for ln in r["log"]:
            print("      ", ln)
        if not ok:
            print(p.stdout[-800:], p.stderr[-1500:])
    srv.shutdown()
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True); main()
