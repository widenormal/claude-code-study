#!/usr/bin/env python3
"""試作: 本文の見える要素どうし（SVG内の図形・文字・画像・色面）の重なり検査。
check_text_overlap は「直接テキストを持つHTML要素」だけ・SVG内は除外、
check_fixed_overlap は「固定要素×その他」だけ、のため図形×写真が死角だった。
ここでは SVG の内側の rect/path/text/circle 等も1つずつ測り、
祖先子孫でなく・同じSVGでない・同じ人物figureでないペアが 4x4px 超で交差したら報告。
追加で「子孫の描画が親カラムの外へはみ出す（COL-OVERFLOW）」も報告。
使い方: check_content_overlap.py deck.html [...] [--viewport=1280x720] [--warn-only]
（kit v3.17.2 で ci-gates.sh に警告だけで組み込み。様子を見てから落とす扱いにする予定）
終了: 0=OK（または --warn-only）／1=所見あり
"""
import sys,json,os
from playwright.sync_api import sync_playwright
BG_SEL='.cm, .numfield-full, .cm-field, .ci-hb, .cf-corner, svg.corner, .corner, .cf-logo, .ci-stack, .period, .ci-digest-btn'
JS=r"""(BG)=>{const out=[];
const lab=e=>{const c=(e.getAttribute('class')||'').split(' ')[0];const t=(e.textContent||'').trim().replace(/\s+/g,' ').slice(0,14);
 const a=['x','y','width'].map(k=>e.getAttribute(k)).filter(v=>v!=null).join(',');
 return e.tagName.toLowerCase()+(c?'.'+c:'')+(e.closest('svg')&&e.tagName!=='svg'?'['+a+']':'')+(t?'"'+t+'"':'')};
document.querySelectorAll('section.slide').forEach((s,i)=>{
 const sr=s.getBoundingClientRect(),SA=sr.width*sr.height;if(sr.width<10)return;
 const items=[];
 const paints=(el)=>{const tag=el.tagName.toLowerCase();
  if(el.closest('svg')){ if(el.closest('defs,marker,clipPath,mask,symbol'))return false;
    if(['rect','path','circle','ellipse','line','polyline','polygon','text','image'].includes(tag)){
      const st=getComputedStyle(el);const f=st.fill,k=st.stroke;
      return tag==='text'||(f&&f!=='none'&&!/,\s*0\)$/.test(f))||(k&&k!=='none');}
    return false;}
  if(['img','canvas','video'].includes(tag))return true;
  if(getComputedStyle(el).display==='inline')return false;   // 折り返したインラインは外接矩形が行をまたぐ＝文字同士は check_text_overlap の担当
  for(const n of el.childNodes) if(n.nodeType===3&&n.textContent.trim())return true;
  const st=getComputedStyle(el);const bg=st.backgroundColor;
  if(bg&&!/,\s*0\)$/.test(bg)&&bg!=='transparent')return true;
  if(st.backgroundImage&&st.backgroundImage!=='none')return true;
  if(['Top','Right','Bottom','Left'].some(k=>parseFloat(st['border'+k+'Width'])>0&&st['border'+k+'Style']!=='none'))return true;
  return false;};
 s.querySelectorAll('*').forEach(el=>{
  if(el.closest(BG))return; if(el.tagName.toLowerCase()==='svg')return;
  let vis=true;for(let e=el;e&&e!==s;e=e.parentElement){const st=getComputedStyle(e);if(st.display==='none'||st.visibility==='hidden'||parseFloat(st.opacity)===0){vis=false;break}}
  if(!vis||!paints(el))return;
  const r=el.getBoundingClientRect();if(r.width<2||r.height<2)return;if(r.width*r.height>SA*0.5)return;
  items.push({el,r,svg:el.closest('svg'),fig:el.closest('figure')});});
 for(let a=0;a<items.length;a++)for(let b=a+1;b<items.length;b++){const A=items[a],B=items[b];
  if(A.el.contains(B.el)||B.el.contains(A.el))continue;
  if(A.svg&&A.svg===B.svg)continue;            // 同じ図の中は svg_label_check の担当
  if(A.fig&&A.fig===B.fig)continue;            // 人物figure内（plate×img）は設計上の重ね
  // 重ねの設計が明示されたもの（一方が他方の内側に完全に入る通常フローのカード等）は残す＝まずは全部出す
  const ox=Math.min(A.r.right,B.r.right)-Math.max(A.r.left,B.r.left),oy=Math.min(A.r.bottom,B.r.bottom)-Math.max(A.r.top,B.r.top);
  if(ox>4&&oy>4)out.push({n:i+1,kind:'OVERLAP',a:lab(A.el),b:lab(B.el),ox:Math.round(ox),oy:Math.round(oy),
    ra:[A.r.left-sr.left,A.r.top-sr.top,A.r.right-sr.left,A.r.bottom-sr.top].map(Math.round),rb:[B.r.left-sr.left,B.r.top-sr.top,B.r.right-sr.left,B.r.bottom-sr.top].map(Math.round)});}
 // COL-OVERFLOW: 段組の列（flex/grid の子）から中身がはみ出す
 s.querySelectorAll('*').forEach(c=>{const p=c.parentElement;if(!p||c.closest(BG))return;const d=getComputedStyle(p).display;
  if(!/flex|grid/.test(d)||p.children.length<2)return;const cr=c.getBoundingClientRect();if(cr.width<2)return;
  let mx=cr.right;c.querySelectorAll('svg,img,table,div').forEach(e=>{const r=e.getBoundingClientRect();if(r.width>1)mx=Math.max(mx,r.right)});
  // 自身が固定幅で列より広いケースも拾うため、列の「割当幅」= cr を基準
  if(mx-cr.right>4)out.push({n:i+1,kind:'COL-OVERFLOW',a:lab(c),b:'右へ+'+Math.round(mx-cr.right)+'px',ox:Math.round(mx-cr.right),oy:0});});
});return out}"""
vp=next((a.split('=')[1] for a in sys.argv if a.startswith('--viewport=')),'1280x720');w,h=map(int,vp.split('x'))
files=[a for a in sys.argv[1:] if not a.startswith('--')];bad=0
with sync_playwright() as p:
 b=p.chromium.launch()
 for f in files:
  pg=b.new_page(viewport={'width':w,'height':h});pg.goto('file://'+os.path.abspath(f)+'#static');pg.wait_for_timeout(1500)
  r=pg.evaluate(JS,BG_SEL);pg.close();name=f.split('/')[-1]
  for o in r: print(f"{name}: {o['kind']} p{o['n']:02d} {o['a']} × {o['b']} ({o['ox']}x{o['oy']})"+(f" A={o['ra']} B={o['rb']}" if 'ra' in o else ''))
  print(f"{name}: OK" if not r else f"{name}: NG findings={len(r)}");bad|=bool(r)
 b.close()
sys.exit(0 if '--warn-only' in sys.argv else int(bad))
