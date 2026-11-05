/* 5co-CI kit v3.17.1 本文ヘッダーの数字の帯の取り付け（rev4・バリアントB 速さ1.0倍・数字126個）。エンジン（oracle-school-depth.min.js）は表紙と同じものを使い、オプションだけ渡す。 */
(function(w,d){"use strict";
var BASE={world:{w:1920,h:202},mode:'site',paintBg:false,edgeFade:0,rAli:40,rCoh:60,mill:0,predator:0,
 sink:[0.35,0.5,400,0.5],bgSpacing:70,margin:60,goal:0,coh:0.2,ali:0.6,wander:2.0,bgFrac:0.75,bgSpeed:0.9,field:2.0,
 calm:{x:0.05,y:0.50,w:0.76,h:0.50,alpha:0.65,push:0.2,feather:60},preroll:6,staticTime:6,
 modeAlpha:{site:1.0},alphaFar:0.78,alphaNear:1.0,sizeFar:24,sizeNear:44,bgAlpha:[0.75,0.8],bgSize:[24,30],speed:1.0,count:126};
w.CI_HB={BASE:BASE,cfg:function(seed){var c=JSON.parse(JSON.stringify(BASE));c.seed=seed>>>0;return c;}};
function fitCut(){var B=d.querySelectorAll('.slide.ci-hb-on > .ci-hb');for(var i=0;i<B.length;i++){var h=B[i],a=h.parentNode.querySelector(':scope > .accent-bar');if(!a)continue;var r0=h.parentNode.getBoundingClientRect(),r1=a.getBoundingClientRect(),z=(r0.height/h.parentNode.offsetHeight)||1,y=Math.floor((r1.bottom-r0.top)/z);if(y>0){h.style.setProperty('--hb-cut',y+'px');if(!h.style.getPropertyValue('--hb-ch'))h.style.setProperty('--hb-ch',Math.max(118,y)+'px');}}}
w.CI_HB.fitCut=fitCut;w.addEventListener('load',fitCut);if(d.fonts&&d.fonts.ready)d.fonts.ready.then(fitCut);
function mountAll(){fitCut();if(!w.OracleSchool)return;var st=d.documentElement.classList.contains('ci-static')||w.location.hash==='#static';
 var L=d.querySelectorAll('canvas.ci-hb-canvas');for(var i=0;i<L.length;i++){var c=L[i];if(c.getAttribute('data-hb-mounted'))continue;c.setAttribute('data-hb-mounted','1');
  var cfg=w.CI_HB.cfg(+c.getAttribute('data-hb-seed')||(20261105+i));if(st)cfg.preroll=cfg.staticTime;
  var s=w.OracleSchool.mount(c,cfg);if(st){s.paused=true;s.sync();}(w.ciHB=w.ciHB||[]).push(s);}}
w.CI_HB.mountAll=mountAll;
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',mountAll,{once:true});else mountAll();
})(window,document);
