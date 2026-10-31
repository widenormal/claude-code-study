#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""固定配置要素（コーナーロゴ・フッター・頁番号）× 見える要素 の重なり検査（kit v3.12・ci-gates.sh で落とす）。

起点: 2026-10-29 若松さん p13「取扱注意ブロックが左下の 5 co. コーナーロゴにかぶる」。
check_text_overlap.py は「テキストを直接持つ末端要素」同士しか比べないため、
  ・SVG/画像だけのロゴ（.cf-corner / svg.corner / .cf-logo）
  ・背景色や枠だけで見える箱（.ci-conf-block のアンバー面など）
  ・counter() を含む頁番号（.slide::after "CONFIDENTIAL ・ " counter(page)）
が死角だった。本スクリプトは各 .slide で

  FIXED = コーナーロゴ（.cf-corner, svg.corner, .corner, .cf-logo）
          + フッター（.slide::before / ::after の content を一時 span で実寸化、.ci-stack, .period, .ci-digest-btn）
  VIS   = その他の「見える」要素: 直接テキストを持つ要素 / img・svg・canvas・video /
          背景色・背景画像・枠線・影のいずれかを持つ箱
          （背景の数字フィールド .cm・.numfield-full と、スライド面積の 50% 超の全面背景は除外）

を集め、FIXED×VIS と FIXED×FIXED の矩形交差（祖先子孫は除く）が 4px×4px を超えたら
FIXED-OVERLAP として exit 1。近接（片軸が重なり・他軸 <NEAR_MISS_PX 空き・既定 6px）は警告表示のみ。

測定は headless Chrome で、モード×ビューポートを総当たり:
  モード: static（#static＝PDF/検査の最終状態）/ screen（通常画面・ダイジェストボタンあり）/
          digest（hero 付き頁を data-page-mode=digest）
  ビューポート既定: 1280x720,1366x768,1440x900,1536x864,1920x1080,1024x768,390x844

使い方: python3 check_fixed_overlap.py <deck.html> [...] [--json] [--lines]
          [--viewports=1280x720,...] [--modes=static,screen,digest]
        python3 check_fixed_overlap.py --selftest   … 「コーナーロゴ×色面ボックス」「頁番号 counter()×本文」を検出し、
                                                      きれいな頁は OK になることを確認
        環境変数 CI_FIXED_OVERLAP_VIEWPORTS / CI_FIXED_OVERLAP_MODES でも既定を変えられる（引数が優先）
出力:   所見1件1行（FIXED-OVERLAP / NEAR-MISS(警告) / PROBE-FAIL）→ 集計行 → 最終行 `<name>: OK` / `<name>: NG`
        --json は1ファイル1行の JSON（下流ツールはこちらを使う）
戻り値: FIXED-OVERLAP または PROBE-FAIL が1件でもあれば 1
"""
import sys, os, glob, json, shutil, subprocess, tempfile, re, pathlib, urllib.parse
from concurrent.futures import ThreadPoolExecutor

def find_chrome():
    cands=["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    pw=os.environ.get("PLAYWRIGHT_BROWSERS_PATH","/opt/pw-browsers")
    cands+=sorted(glob.glob(f"{pw}/chromium-*/chrome-linux/chrome"))
    for c in cands:
        if os.path.isfile(c) and os.access(c,os.X_OK): return c
    for n in ("google-chrome","chromium","chromium-browser","chrome"):
        p=shutil.which(n)
        if p: return p
    sys.exit("ERROR: Chrome/Chromium が見つかりません")
CHROME=None

DIGEST_PREP = """<script>
window.addEventListener('DOMContentLoaded', () => {
  try { document.documentElement.classList.remove('ci-static'); } catch (e) {}
  document.querySelectorAll('section.slide').forEach(s => {
    if (s.querySelector('[data-digest-keep="hero"]')) s.setAttribute('data-page-mode', 'digest');
  });
});
</script>"""

PROBE = r"""<script>
window.addEventListener('load', () => setTimeout(() => {
  const NEAR=__NEAR__, out=[], warn=[];
  const FIXED_SEL='.cf-corner, svg.corner, .corner, .cf-logo, .ci-stack, .period, .ci-digest-btn';
  const BG_SEL='.cm, .numfield-full, .cm-field > .cm';
  const PROPS=['position','left','top','fontFamily','fontSize','fontWeight','fontStyle','letterSpacing',
    'lineHeight','whiteSpace','textTransform','fontFeatureSettings','paddingLeft','paddingRight','paddingTop','paddingBottom'];
  const lab=el=>{
    if(el.classList&&el.classList.contains('cfo-probe')) return 'section'+el.dataset.pe+'"'+el.textContent.trim().slice(0,16)+'"';
    const t=(el.textContent||'').trim().replace(/\s+/g,' ').slice(0,12);
    const cn=(el.getAttribute('class')||'').split(' ')[0];
    return el.tagName.toLowerCase()+(cn?'.'+cn:'')+(t?'"'+t+'"':'');
  };
  const probes=[];
  document.querySelectorAll('section.slide').forEach((s,i)=>{
    for(const pe of ['::before','::after']){
      const cs=getComputedStyle(s,pe); let c=cs.content||'';
      if(!c||c==='none'||c==='normal'||cs.display==='none'||cs.visibility==='hidden'||parseFloat(cs.opacity)===0) continue;
      if(cs.position!=='absolute'&&cs.position!=='fixed') continue;
      // counter()/counters() は頁番号で置換（kit 版は純粋な文字列 content のみ＝頁番号が死角）
      c=c.replace(/counters?\([^)]*\)/g,'"'+(i+1)+'"');
      const parts=[...c.matchAll(/"((?:[^"\\]|\\.)*)"/g)].map(m=>m[1].replace(/\\(.)/g,'$1'));
      const txt=parts.join(''); if(!txt.trim()) continue;
      const sp=document.createElement('span'); sp.className='cfo-probe'; sp.dataset.pe=pe; sp.textContent=txt;
      for(const k of PROPS) sp.style[k]=cs[k];
      sp.style.right=cs.left==='auto'?cs.right:'auto'; sp.style.left=cs.left;
      sp.style.top=cs.top==='auto'?'auto':cs.top; sp.style.bottom=cs.top==='auto'?cs.bottom:'auto';
      sp.style.margin='0'; sp.style.visibility='hidden';
      s.appendChild(sp); probes.push(sp);
    }
  });
  const visible=el=>{
    for(let e=el;e&&e.nodeType===1;e=e.parentElement){
      const st=getComputedStyle(e);
      if(st.display==='none'||parseFloat(st.opacity)===0) return false;
      if(e.tagName==='SECTION') break;
    }
    const st=getComputedStyle(el);
    return el.classList.contains('cfo-probe')||st.visibility!=='hidden';
  };
  const paints=el=>{
    const st=getComputedStyle(el), tag=el.tagName.toLowerCase();
    if(['img','svg','canvas','video','picture'].includes(tag)) return true;
    for(const n of el.childNodes) if(n.nodeType===3&&n.textContent.trim()) return true;
    const bg=st.backgroundColor; if(bg&&!/rgba\(.*,\s*0\)$/.test(bg)&&bg!=='transparent') return true;
    if(st.backgroundImage&&st.backgroundImage!=='none') return true;
    if(['Top','Right','Bottom','Left'].some(k=>parseFloat(st['border'+k+'Width'])>0&&st['border'+k+'Style']!=='none')) return true;
    if(st.boxShadow&&st.boxShadow!=='none') return true;
    return false;
  };
  document.querySelectorAll('section.slide').forEach((s,i)=>{
    const sr=s.getBoundingClientRect(), SA=sr.width*sr.height;
    if(sr.width<10) return;
    const fixed=[], vis=[];
    const isFixed=el=>el.classList.contains('cfo-probe')||!!el.closest(FIXED_SEL);
    s.querySelectorAll('*').forEach(el=>{
      if(el.closest(BG_SEL)) return;
      if(el.closest('svg')&&el.tagName.toLowerCase()!=='svg') return;   // svg は外枠で測る
      if(!visible(el)) return;
      const r=el.getBoundingClientRect(); if(r.width<2||r.height<2) return;
      if(isFixed(el)){
        // 固定要素は最上位（.cf-corner 等）と疑似プローブを1つの箱として扱う
        const top=el.classList.contains('cfo-probe')?el:el.closest(FIXED_SEL);
        if(top===el) fixed.push({el,r});
        return;
      }
      if(!paints(el)) return;
      if(r.width*r.height>SA*0.5) return;  // 全面背景・ラッパ
      vis.push({el,r});
    });
    const cmp=(A,B,kind)=>{
      if(A.el.contains(B.el)||B.el.contains(A.el)) return;
      const ox=Math.min(A.r.right,B.r.right)-Math.max(A.r.left,B.r.left);
      const oy=Math.min(A.r.bottom,B.r.bottom)-Math.max(A.r.top,B.r.top);
      if(ox>4&&oy>4){ out.push({n:i+1,kind,a:lab(A.el),b:lab(B.el),ox:Math.round(ox),oy:Math.round(oy)}); }
      else if(NEAR>0&&((ox>0.5&&oy>0.5)||(ox>4&&oy>-NEAR&&oy<=0.5)||(oy>4&&ox>-NEAR&&ox<=0.5))){
        warn.push({n:i+1,kind,a:lab(A.el),b:lab(B.el),ox:Math.round(ox*10)/10,oy:Math.round(oy*10)/10});
      }
    };
    for(const F of fixed) for(const V of vis) cmp(F,V,'fixed×vis');
    for(let a=0;a<fixed.length;a++) for(let b=a+1;b<fixed.length;b++) cmp(fixed[a],fixed[b],'fixed×fixed');
  });
  probes.forEach(p=>p.remove());
  document.title='CFO_REPORT['+JSON.stringify({out,warn,n:document.querySelectorAll('section.slide').length})+']CFO_END';
}, 300));
</script>"""

def run(src, mode, vp, near):
    global CHROME
    CHROME=CHROME or find_chrome()
    tail=(DIGEST_PREP if mode=="digest" else "")+PROBE.replace("__NEAR__",str(near))
    html=src.replace("</body>",tail+"</body>",1) if "</body>" in src else src+tail
    with tempfile.NamedTemporaryFile("w",suffix=".html",delete=False,encoding="utf-8") as f:
        f.write(html); tmp=f.name
    try:
        url="file://"+urllib.parse.quote(tmp)+("#static" if mode=="static" else "")
        w,h=vp.split("x")
        r=subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars",
                          f"--window-size={w},{h}","--virtual-time-budget=15000","--dump-dom",url],
                         capture_output=True,text=True,timeout=180)
        m=re.search(r"CFO_REPORT\[(.*?)\]CFO_END",r.stdout,re.S)
        if not m: return None
        import html as H
        return json.loads(H.unescape(m.group(1)))
    finally:
        os.unlink(tmp)

SELFTEST_BASE = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0} section.slide{position:relative;width:1122px;height:794px;overflow:hidden;background:#fff;font:14px sans-serif;counter-increment:page}
.cf-corner{position:absolute;left:24px;bottom:24px;width:110px;height:80px}
.box{position:absolute;left:120px;bottom:30px;width:600px;height:60px;background:#F2B544}
section.slide::after{position:absolute;right:36px;bottom:12px;content:"CONFIDENTIAL ・ " counter(page);font-size:10px}
.body{position:absolute;right:30px;bottom:8px;margin:0;width:200px}
</style></head><body>__BODY__</body></html>"""
SELFTEST_CASES = [
  ("corner_logo_x_box", True,
   '<section class="slide" id="p01"><div class="cf-corner"><svg width="110" height="80"><rect width="110" height="80" fill="#101820"/></svg></div>'
   '<aside class="box"></aside></section>'),
  ("page_counter_x_body", True,
   '<section class="slide" id="p01"><p class="body">本文テキストが頁番号にかぶる本文テキスト</p></section>'),
  ("clean", False,
   '<section class="slide" id="p01"><div class="cf-corner"><svg width="110" height="80"><rect width="110" height="80" fill="#101820"/></svg></div>'
   '<p style="position:absolute;left:300px;top:300px;margin:0">本文</p></section>'),
]

def selftest():
    ok_all=True
    for name,expect,body in SELFTEST_CASES:
        r=run(SELFTEST_BASE.replace("__BODY__",body),"static","1280x720",0)
        got = None if r is None else bool(r["out"])
        ok = (got is expect)
        ok_all &= ok
        print(f"  {'✔' if ok else '✘'} {name}: expect_overlap={expect} got={got}" + (f" {r['out'][:1]}" if r and r['out'] else ""))
    print("check_fixed_overlap.py --selftest:", "OK" if ok_all else "FAIL")
    return 0 if ok_all else 1

def main():
    args=sys.argv[1:]
    if "--selftest" in args: sys.exit(selftest())
    vps=next((a.split("=",1)[1] for a in args if a.startswith("--viewports=")),
             os.environ.get("CI_FIXED_OVERLAP_VIEWPORTS") or
             "1280x720,1366x768,1440x900,1536x864,1920x1080,1024x768,390x844").split(",")
    modes=next((a.split("=",1)[1] for a in args if a.startswith("--modes=")),
               os.environ.get("CI_FIXED_OVERLAP_MODES") or "static,screen,digest").split(",")
    as_json="--json" in args
    near=float(os.environ.get("NEAR_MISS_PX","6"))
    files=[a for a in args if not a.startswith("--")]
    if not files: sys.exit(__doc__)
    bad=0
    for p in files:
        src=open(p,encoding="utf-8").read(); name=pathlib.Path(p).name
        jobs=[(m,v) for m in modes for v in vps]
        with ThreadPoolExecutor(max_workers=int(os.environ.get("CI_FIXED_OVERLAP_JOBS","4"))) as ex:
            res=list(ex.map(lambda mv: run(src,mv[0],mv[1],near), jobs))
        ovl={}; warn={}; fails=[]; npages=0
        for (m,v),r in zip(jobs,res):
            if r is None: fails.append(f"{m}@{v}"); continue
            npages=r["n"]
            for o in r["out"]:
                k=(o["n"],o["kind"],o["a"],o["b"]); ovl.setdefault(k,[]).append((f"{m}@{v}",o["ox"],o["oy"]))
            for o in r["warn"]:
                k=(o["n"],o["kind"],o["a"],o["b"]); warn.setdefault(k,[]).append(f"{m}@{v}({o['ox']},{o['oy']})")
        ok=not ovl and not fails
        if as_json:
            print(json.dumps({"file":name,"ok":ok,"pages":npages,"runs":len(jobs),"probe_fail":fails,
                "overlaps":[{"n":k[0],"kind":k[1],"a":k[2],"b":k[3],"where":v} for k,v in sorted(ovl.items())],
                "near_miss":[{"n":k[0],"kind":k[1],"a":k[2],"b":k[3],"where":v} for k,v in sorted(warn.items())]},ensure_ascii=False))
        else:
            for k,v in sorted(ovl.items()):
                where=", ".join(f"{w}({ox}x{oy})" for w,ox,oy in v[:4])+(f" …他{len(v)-4}" if len(v)>4 else "")
                print(f"{name}: FIXED-OVERLAP p{k[0]:02d} [{k[1]}] {k[2]} × {k[3]}  @ {where}")
            for k,v in sorted(warn.items()):
                print(f"{name}: NEAR-MISS(警告) p{k[0]:02d} [{k[1]}] {k[2]} × {k[3]}  @ {', '.join(v[:3])}")
            for f in fails: print(f"{name}: PROBE-FAIL {f}")
            print(f"{name}: pages={npages} runs={len(jobs)} ({'/'.join(modes)} × {len(vps)} viewports) overlaps={len(ovl)} near={len(warn)}")
            print(f"{name}: {'OK' if ok else 'NG'}")
        bad|=not ok
    sys.exit(1 if bad else 0)

if __name__=="__main__": main()
