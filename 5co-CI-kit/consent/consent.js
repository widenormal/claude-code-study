/* 正本: 候補者用の事業プラン資料 v22（2026-11-05 若松さん合格）から抜き出し。kit consent/ v3.18.0 */
(function(w,d){var R=d.documentElement;function boids(){return (w.ciBoid||[]).concat(w.ciHB||[]);}
function hold(){if(!R.classList.contains("ci-consent-pending"))return;boids().forEach(function(s){s.paused=true;s.sync&&s.sync();});}
if(d.readyState==="loading")d.addEventListener("DOMContentLoaded",hold);else hold();w.addEventListener("load",hold);
function reveal(){if(!R.classList.contains("ci-consent-pending"))return;R.classList.remove("ci-consent-pending");
requestAnimationFrame(function(){boids().forEach(function(s){s.paused=false;if(s.resize)s.resize();if(s.ready&&s.draw)s.draw(1);s.sync&&s.sync();});w.dispatchEvent(new Event("resize"));});}
var b=d.getElementById("ci-consent-btn");if(b)b.addEventListener("click",reveal);
})(window,document);
