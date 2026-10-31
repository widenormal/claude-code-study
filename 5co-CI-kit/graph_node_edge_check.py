#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ノード・エッジ型グラフ図の検査（2026-07-13 新設・顧客OKR会 AI運用OODAループ資料で確立）。

`slide_overflow_check.py`（あふれ）・`check_text_overlap.py`（DOM要素の重なり）は
いずれも DOM/flexbox ベースの検査で、SVG 内の `<rect>`/`<path>` 座標同士の
重なり・接続は死角だった。本ゲートはノード・エッジ型グラフ図（フロー図・
ネットワーク図）専用にその死角を埋める。

検査対象はオプトイン方式: `class="ne-graph"` を付けたコンテナ（svg または div）内の
  - ノード = `.ne-node` を付けた要素（純SVG構成＝rect 推奨。circle/ellipse/polygon も可。
    ハイブリッド構成＝HTML div も可＝いずれも AABB判定）
  - エッジ = `.ne-edge` を付けた path/line/polyline、または marker-end/marker-start 付きのもの
    （ハイブリッド構成ではコンテナ内の SVG に position:absolute で重ねる）
  - `.ne-skip` を付けた要素は検査から除外（凡例の見本矢印・装飾等）

ハイブリッド構成（node=HTML／edge=SVG・実運用で最安定）: ノードは HTML div（.ne-node 付与・
既存CSSクラス流用可・和文の折返しはHTML任せ）、エッジのみ SVG。本ゲートは screen 座標系で
突き合わせるため、純SVG・ハイブリッドのどちらの構成でも同一ロジックで検査できる。

検査内容（headless Chrome で実測）:
  1) NODE_OVERLAP … ノード同士の AABB 交差（1px 未満の接触は許容）
  2) EDGE_DETACHED … エッジの始点・終点が、いずれかのノードの縁
     （上下左右の境界線・許容誤差 ±2.5px）に乗っていない「浮いた」矢印
  3) NO_NODES … `.ne-graph` なのに `.ne-node` が 1 つも無い（タグ付け漏れ＝検査が空振り）

座標規律（グリッド座標系＝V3.2_FORMAT.md「ノード・エッジ型グラフ図」参照）に
従って作図していれば構造的に通る。手置き座標のズレ・文言変更後の引き直し漏れを検出する。

使い方: python3 graph_node_edge_check.py <file.html> [<file2.html> ...]
出力:   <name>: OK  /  <name>: NE-GRAPH slide番号:種別 詳細
戻り値: 検出が1件でもあれば 1（ゲートとして ci-finalize.sh から呼ばれる）
※ ne-graph が1つも無いファイルは OK（本ゲートはノード・エッジ図を含むデッキのみに効く）
"""
import sys, os, glob, shutil, subprocess, tempfile, re, pathlib, urllib.parse

def find_chrome():
    """Chrome/Chromium を自動探索（Mac → Playwright 同梱 → PATH）。
    slide_overflow_check.py / check_text_overlap.py と同一の探索順。"""
    cands=["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Chromium.app/Contents/MacOS/Chromium"]
    pw=os.environ.get("PLAYWRIGHT_BROWSERS_PATH","/opt/pw-browsers")
    cands+=sorted(glob.glob(f"{pw}/chromium-*/chrome-linux/chrome"))
    cands+=sorted(glob.glob(f"{pw}/chromium_headless_shell-*/chrome-linux/headless_shell"))
    for c in cands:
        if os.path.isfile(c) and os.access(c,os.X_OK): return c
    for n in ("google-chrome","chromium","chromium-browser","chrome"):
        p=shutil.which(n)
        if p: return p
    sys.exit("ERROR: Chrome/Chromium が見つかりません（Mac は Google Chrome を、"
             "Linux は chromium か PLAYWRIGHT_BROWSERS_PATH を用意してください）。")

CHROME=find_chrome()
PROBE="""
<script>
window.addEventListener('load', () => {
  const out=[];
  const slides=[...document.querySelectorAll('.slide')];
  const lab=el=>{
    const c=(el.getAttribute('class')||'').split(/\\s+/).filter(x=>x&&x!=='ne-node'&&x!=='ne-edge')[0];
    let pos='';
    try{ const b=el.getBBox(); pos='@'+Math.round(b.x)+','+Math.round(b.y); }
    catch(e){ const t=(el.textContent||'').trim().replace(/\\s+/g,' ').slice(0,10); if(t) pos='"'+t+'"'; }
    return el.tagName.toLowerCase()+(c?'.'+c:'')+pos;
  };
  // p が矩形 r の縁（上下左右の境界線）に乗っているか（許容誤差 t）
  const onBorder=(p,r,t)=>{
    const inX=p.x>=r.left-t&&p.x<=r.right+t, inY=p.y>=r.top-t&&p.y<=r.bottom+t;
    return (inX&&(Math.abs(p.y-r.top)<=t||Math.abs(p.y-r.bottom)<=t))
         ||(inY&&(Math.abs(p.x-r.left)<=t||Math.abs(p.x-r.right)<=t));
  };
  document.querySelectorAll('.ne-graph').forEach(g=>{
    const si=slides.indexOf(g.closest('.slide'))+1||'?';
    // 縮尺: 純SVG構成＝コンテナSVGのCTM／ハイブリッド構成（divコンテナ）＝CSS px（=1）
    const m=(typeof g.getScreenCTM==='function')?g.getScreenCTM():null;
    const sc=m?Math.hypot(m.a,m.b):1;                 // 許容誤差を作図座標系で一定に保つ
    const TOL_TOUCH=1*sc;
    const nodes=[...g.querySelectorAll('.ne-node')]
      .filter(n=>!n.classList.contains('ne-skip'))
      .map(n=>({el:n,r:n.getBoundingClientRect()}));
    if(!nodes.length){ out.push(si+':NO_NODES .ne-graph に .ne-node がありません'); return; }
    // 1) ノード同士の重なり（AABB交差・1px未満の接触は許容）
    for(let a=0;a<nodes.length;a++)for(let b=a+1;b<nodes.length;b++){
      const A=nodes[a].r,B=nodes[b].r;
      const ix=Math.min(A.right,B.right)-Math.max(A.left,B.left);
      const iy=Math.min(A.bottom,B.bottom)-Math.max(A.top,B.top);
      if(ix>TOL_TOUCH&&iy>TOL_TOUCH)
        out.push(si+':NODE_OVERLAP '+lab(nodes[a].el)+'×'+lab(nodes[b].el)
                 +'('+Math.round(ix/sc)+'x'+Math.round(iy/sc)+'px)');
    }
    // 2) エッジの始点・終点がノードの縁に乗っているか（div コンテナ内の SVG エッジも拾う）
    g.querySelectorAll('path,line,polyline').forEach(e=>{
      if(e.closest('defs')||e.closest('marker')) return;
      if(e.classList.contains('ne-skip')||e.classList.contains('ne-node')) return;
      const isEdge=e.classList.contains('ne-edge')
        ||e.hasAttribute('marker-end')||e.hasAttribute('marker-start');
      if(!isEdge) return;
      if(typeof e.getTotalLength!=='function') return;
      let L; try{ L=e.getTotalLength(); }catch(err){ return; }
      if(!L||L<1) return;
      const em=e.getScreenCTM(); if(!em) return;
      const TOL_EDGE=2.5*Math.hypot(em.a,em.b);       // エッジ自身のSVG縮尺で±2.5pxを担保
      [['始点',e.getPointAtLength(0)],['終点',e.getPointAtLength(L)]].forEach(([k,p])=>{
        const q={x:em.a*p.x+em.c*p.y+em.e, y:em.b*p.x+em.d*p.y+em.f};
        if(!nodes.some(n=>onBorder(q,n.r,TOL_EDGE)))
          out.push(si+':EDGE_DETACHED '+lab(e)+' '+k+'('+Math.round(p.x)+','+Math.round(p.y)+')');
        if(out.length>40){out.push('...打ち切り');}
      });
    });
  });
  document.title='NEGRAPH_REPORT['+out.slice(0,42).join(' | ')+']';
});
</script>"""

def check(path):
    html=open(path,encoding="utf-8").read()
    html=html.replace("</body>",PROBE+"</body>",1) if "</body>" in html else html+PROBE
    with tempfile.NamedTemporaryFile("w",suffix=".html",delete=False,encoding="utf-8",
                                     dir=os.path.dirname(os.path.abspath(path))) as f:
        f.write(html); tmp=f.name
    try:
        # --no-sandbox: CI コンテナ等 root 実行時に必須（Mac では無害）
        r=subprocess.run([CHROME,"--headless=new","--disable-gpu","--no-sandbox","--hide-scrollbars",
                          "--virtual-time-budget=15000","--dump-dom","file://"+urllib.parse.quote(tmp)+"#static"],  # #static＝動く資料（v3.9）を組み上がった最終状態で開く。静的デッキでは何もしない
                         capture_output=True,text=True,timeout=120)
        m=re.search(r"NEGRAPH_REPORT\[(.*?)\]</title>",r.stdout,re.S)
        rep=m.group(1).strip() if m else "(probe失敗)"
        name=pathlib.Path(path).name
        if not rep:
            print(f"{name}: OK"); return 0
        if rep=="(probe失敗)":
            print(f"{name}: ERROR {rep}"); return 1
        print(f"{name}: NE-GRAPH {rep}"); return 1
    finally:
        os.unlink(tmp)

if __name__=="__main__":
    if len(sys.argv)<2:
        sys.exit("使い方: python3 graph_node_edge_check.py <file.html> [...]")
    sys.exit(max(check(p) for p in sys.argv[1:]))
