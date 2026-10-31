#!/usr/bin/env python3
"""ランタイム「ダイジェスト」切替ボタン（軽量 CSS 方式）。
正本: DIGEST_GUIDE.md（clarified 2026-10-29 by 若松さん）
- ダイジェスト＝元ページの「このページの要点」（.gist）＋視覚（図／数字／キーワード／写真のいずれか、または「数字＋写真」）。
- 表・長い箇条書き・複数カード・2枚目のグラフは出さない。図（グラフ）hero には写真を足さない。
- DOM 二重化なし。data-digest-keep="hero"＝その1視覚。gist は属性なしで残す。
- 冪等: 既存の印・ブロックを外してから付け直す。
- v1.9（2026-10-31・v3.13）: 発表＝キー T／URL #talk で hero のある全ページを一括ダイジェストにし、
  見出し2行（data-talk-h か「話題｜答え」）・上の要点帯と右の説明カードを外す・hero を大きく。
  台本＝キー S で画面下の帯（data-talk-script か要点）。各ページのボタンはそのまま。#static/印刷は不変。
- v1.9.1（2026-10-31・v3.13.1）: 台本の帯がフッター行（コピーライト・頁番号・集計期間・ボタン）を隠さない。
  帯の高さぶん下に余白、スライドが「画面 − 帯」に収まらない全画面などではフッター行を帯の上へ持ち上げ hero の下も空ける。
- v1.9.2（2026-10-31・v3.13.2）: 持ち上げ中は、スライド下半分の絶対配置の要素（表紙の CI 説明・締めの同意欄など）も同じだけ持ち上げる。
使い方: python3 5co-CI-kit/digest_toggle.py <deck.html>
        python3 5co-CI-kit/digest_toggle.py --talk <deck.html>   … 既存のダイジェスト付きデッキに発表（T）と台本（S）だけを足す／入れ替える（冪等）"""
import re, sys

# PLAN v1.7（2026-10-29 若松さん追記）: 視覚は1つ、または「数字＋写真」。
#   visual='fig'（既定）→ .fig.ci-fig に hero。crop/--dg-ar は左パネル切り抜き用。図 hero には写真を足さない。
#   visual='photo' → figure.dg-photo に hero（fig は付けない）。写真パス必須。
#   visual='num' + photo → 数字ブロック（num_sel 正規表現で先頭タグ一致、既定 .okr）に hero、
#     figure.dg-photo に data-digest-keep="photo"（cutout 右下）。
#   point: 原則なし。.gist は CSS で自動表示。gist 以外の1キーワードだけ残すときだけ 'gist' 以外を1つ。
PLAN = {
 'p02': dict(crop=None),
 'p04': dict(crop='158%'),
 'p05': dict(crop=None),
 'p06': dict(crop='272%', ar='360/130'),
 'p07': dict(crop='194%'),
 'p08': dict(crop='208%'),
 'p09': dict(crop='153%'),
 'p10': dict(crop='208%'),
 'p11': dict(crop='208%'),
 'p12': dict(crop=None),
 'p13': dict(crop='166%'),
 'p14': dict(crop='204%'),
 'p15': dict(crop=None),
 'p16': dict(crop='194%'),
 'p17': dict(crop=None),
}

BLOCK = r'''<!-- ci-digest-toggle v1.9 (BEGIN) — 2026-10-29 若松さん clar: ダイジェスト＝.gist＋視覚（図／数字／キーワード／写真のいずれか、または数字＋写真）。表・複数カード・2枚目のグラフなし。フッター最左トグル・#static/印刷は常にフル。正＝DIGEST_GUIDE.md（5co-CI-kit v3.11） -->
<style id="ci-digest-toggle-css">
/* ボタン: 左下フッターの最左（版スタックのさらに左）。CI トークンのみ */
.ci-digest-btn{position:absolute; left:36px; bottom:12px; top:auto; right:auto; z-index:5; display:inline-flex; align-items:center; gap:.4em;
  border:1px solid var(--crystal); background:var(--white); color:var(--ink-60); border-radius:999px;
  padding:2px 11px; font-size:10px; line-height:1.5; letter-spacing:.04em; font-family:var(--sans-ja,inherit) !important;
  cursor:pointer; white-space:nowrap; transition:background .15s, border-color .15s, color .15s;}
.ci-digest-btn::before{content:""; width:6px; height:6px; border-radius:50%; background:var(--crystal);}
.ci-digest-btn:hover,.ci-digest-btn:focus-visible{border-color:var(--ink); color:var(--ink); background:var(--crystal-25); outline:none;}
.ci-digest-btn[aria-pressed="true"]{background:var(--crystal-25); color:var(--ink);}
.ci-digest-btn[aria-pressed="true"]::before{background:var(--ink);}
/* ボタンがあるページは版スタック（::before）を右へずらして重なり防止 */
section.slide:has(> .ci-digest-btn)::before{left:148px;}
section.slide:has(> .ci-digest-btn) > .ci-stack{left:148px;}
section.slide:has(> .ci-digest-btn) > .period{left:148px;}
/* 紙・#static（検査・PDF）・一覧では出さない＝印刷は常にフル。版スタック位置も戻す */
html.ci-static .ci-digest-btn, html.ci-overview .ci-digest-btn{display:none !important;}
html.ci-static section.slide:has(> .ci-digest-btn)::before,
html.ci-overview section.slide:has(> .ci-digest-btn)::before{left:36px;}
@media print{
  .ci-digest-btn{display:none !important;}
  section.slide:has(> .ci-digest-btn)::before{left:36px;}
}

/* 写真枠: フル・#static・印刷では出さない（ダイジェストで hero または数字 hero に添える photo keep のとき表示） */
.dg-photo{display:none;}

/* ダイジェスト（画面のみ）: ヘッダー・フッター・A4余白・頁番号は不変。.gist＋視覚1つ */
@media screen{
html:not(.ci-static) section.slide[data-page-mode="digest"]{display:flex; flex-direction:column; align-content:stretch;}
/* 絶対配置の子（ボタン・コーナーロゴ・版スタック）はフローに入れない */
html:not(.ci-static) section.slide[data-page-mode="digest"] > :is(.ci-digest-btn,.corner,.ci-stack,.period){position:absolute;}
/* 既定: hero / gist / ヘッダー類以外は隠す。表・複数カード・ドリルダウンも隠す */
html:not(.ci-static) section.slide[data-page-mode="digest"] > :not(.hdr):not(.title):not(.accent-bar):not(.gist):not(.note-line):not(.corner):not(.ci-digest-btn):not([data-digest-keep="hero"]):not([data-digest-keep="photo"]):not(:has([data-digest-keep="hero"])),
html:not(.ci-static) section.slide[data-page-mode="digest"] > .t-note,
html:not(.ci-static) section.slide[data-page-mode="digest"] .ci-ev-btn,
html:not(.ci-static) section.slide[data-page-mode="digest"] table,
html:not(.ci-static) section.slide[data-page-mode="digest"] .skyu,
html:not(.ci-static) section.slide[data-page-mode="digest"] [data-digest-keep="point"]{display:none !important;}
/* 要点（.gist）: 全幅の淡色帯。ヘッダー直下 */
html:not(.ci-static) section.slide[data-page-mode="digest"] > .gist{display:block !important; background:var(--crystal-25); border-left:4px solid var(--ink); border-radius:0 6px 6px 0;
  padding:12px 18px 12px 16px; margin:6px 0 0; font-size:15px; line-height:1.65; color:var(--ink-85); max-width:none;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .gist .gist-k{display:table; margin:0 0 6px;}
/* 視覚ちょうど1つ（hero）: 図・大きな数字ブロック・キーワード・写真 */
html:not(.ci-static) section.slide[data-page-mode="digest"] > [data-digest-keep="hero"]{display:flex !important; align-items:center; justify-content:center; flex:1 1 auto; margin:16px 0 0 !important; padding:16px 0 !important; overflow:hidden;
  background:var(--white); border:1px solid var(--ink-14); border-radius:10px; min-height:0; aspect-ratio:var(--dg-ar,auto);}
html:not(.ci-static) section.slide[data-page-mode="digest"] > [data-digest-keep="hero"] > svg{flex:none; width:var(--dg-w,100%) !important; max-width:none !important; height:auto; display:block;}
/* 大きな数字（ci-panel / okr が hero のとき） */
html:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-panel[data-digest-keep="hero"]{display:flex !important; flex-direction:column; justify-content:center; background:var(--ink); color:var(--white); border-radius:10px; padding:22px 28px !important; border:0;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-panel[data-digest-keep="hero"] .ci-big{color:var(--crystal); font-size:56px;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-panel[data-digest-keep="hero"] .ci-what{color:var(--white); font-size:16px; margin-top:4px;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-panel[data-digest-keep="hero"] .ci-sub,
html:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-panel[data-digest-keep="hero"] .ci-diff{color:var(--crystal-55); font-size:13px;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .okr[data-digest-keep="hero"]{display:block !important; overflow:auto; padding:12px 16px !important;}
/* キーワード1つが hero のとき */
html:not(.ci-static) section.slide[data-page-mode="digest"] > [data-digest-keep="hero"].dg-keyword,
html:not(.ci-static) section.slide[data-page-mode="digest"] li[data-digest-keep="hero"]{display:flex !important; align-items:center; justify-content:center; background:var(--crystal-25); border:0; border-radius:10px;
  font-size:22px; font-weight:700; line-height:1.45; padding:28px 32px !important; color:var(--ink);}
/* 写真が唯一の視覚（hero）: 切り抜きは下揃え・クリスタル板。通常写真は角丸カバー */
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"]{display:block !important; position:relative; width:min(520px,72%); max-width:100%; height:var(--dg-ph,360px); margin:18px auto 0 !important; padding:0 !important; border:0; background:transparent; aspect-ratio:auto; overflow:hidden;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"]::before{content:""; position:absolute; left:24px; right:0; top:40px; bottom:0; background:var(--crystal); border-radius:20px; z-index:-1;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"] img{position:relative; display:block; width:calc(100% - 24px); height:100%; object-fit:cover; border-radius:16px; will-change:transform; animation:dgPhotoKen 20s ease-in-out infinite alternate;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"][data-dg-photo="cutout"]{overflow:visible; isolation:isolate; width:var(--dg-pw,340px); height:var(--dg-ph,300px); margin:12px auto 0 !important;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"][data-dg-photo="cutout"]::before{left:0; right:0; top:34%; bottom:0; border-radius:20px; z-index:-1;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="hero"][data-dg-photo="cutout"] img{position:absolute; left:0; right:0; bottom:0; width:calc(100% - 16px); height:100%; border-radius:0;
  object-fit:contain; object-position:50% 100%; mix-blend-mode:multiply; clip-path:none; transform-origin:50% 100%; animation:dgCutoutBreath 18s ease-in-out infinite alternate;}
}
/* 数字＋写真: 数字 hero（.okr / .ci-panel）に cutout 写真（data-digest-keep="photo"）を右下で添える。図 hero には付けない */
html:not(.ci-static) section.slide[data-page-mode="digest"]:has(> .dg-photo[data-digest-keep="photo"]) > [data-digest-keep="hero"]:not(.dg-photo){margin-right:var(--dg-pw,260px) !important;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="photo"]{display:block !important; position:absolute; right:36px; bottom:44px; width:var(--dg-pw,240px); height:var(--dg-ph,220px); margin:0 !important; padding:0 !important; border:0; background:transparent; overflow:visible; isolation:isolate; z-index:1; pointer-events:none;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="photo"]::before{content:""; position:absolute; left:0; right:0; top:34%; bottom:0; background:var(--crystal); border-radius:20px; z-index:-1;}
html:not(.ci-static) section.slide[data-page-mode="digest"] > .dg-photo[data-digest-keep="photo"] img{position:absolute; left:0; right:0; bottom:0; width:calc(100% - 16px); height:100%; object-fit:contain; object-position:50% 100%; mix-blend-mode:multiply; transform-origin:50% 100%; animation:dgCutoutBreath 18s ease-in-out infinite alternate;}
@keyframes dgPhotoKen{
  from{transform:translate(0,0) scale(1.03); clip-path:inset(1.456% round 15.53px);}
  to{transform:translate(-1.5%,-1%) scale(1.09); clip-path:inset(5.046% 2.752% 3.211% 5.504% round 14.68px);}
}
@keyframes dgCutoutBreath{from{transform:scale(1);} to{transform:translateX(-1%) scale(1.035);}}
@media (prefers-reduced-motion: reduce){
  .dg-photo img{animation:none !important; clip-path:none !important; transform:none !important;}
}
html.ci-static .dg-photo img{animation:none !important;}
@media print{ .dg-photo img{animation:none !important;} }
</style>
<script id="ci-digest-toggle-js">
/* ci-digest-toggle v1.9: フッター最左にボタン。視覚1つ（data-digest-keep="hero"）があるページにだけボタンを付け、section の data-page-mode="digest" を付け外しする。.gist＋hero（＋数字 hero 時の photo keep）のみ。 */
(function(){
  var FULL = "ダイジェスト", DIG = "詳細に戻す";
  function init(){
    [].forEach.call(document.querySelectorAll("section.slide"), function(s){
      if (!s.querySelector('[data-digest-keep="hero"]') || s.querySelector(":scope > .ci-digest-btn")) return;
      var b = document.createElement("button");
      b.type = "button"; b.className = "ci-digest-btn"; b.textContent = FULL; b.setAttribute("aria-pressed", "false");
      b.title = "このページの要点と視覚1つだけの表示に切り替えます（画面のみ。印刷・PDF は詳細のまま）";
      s.appendChild(b);
    });
  }
  document.addEventListener("click", function(e){
    var b = e.target && e.target.closest && e.target.closest(".ci-digest-btn");
    if (!b) return;
    e.preventDefault(); e.stopPropagation();
    var s = b.closest("section.slide"), on = s.getAttribute("data-page-mode") !== "digest";
    if (on) s.setAttribute("data-page-mode", "digest"); else s.removeAttribute("data-page-mode");
    b.textContent = on ? DIG : FULL; b.setAttribute("aria-pressed", on ? "true" : "false");
  }, true);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
})();
</script>
<!-- ci-digest-toggle v1.9 (END) -->
'''

# v1.9（2026-10-31・v3.13）: 発表（T／#talk）と台本（S）。BLOCK の END の直前に入れる（手組みデッキには --talk で足す）
TALK_BLOCK = r'''<!-- ci-digest-talk v1.9.2 (BEGIN) — 2026-10-31 発表（キー T／URL #talk で hero のある全ページを一括ダイジェスト＋発表の見せ方・キー S で台本の帯）。通常表示・#static・印刷・検査は不変。正＝DIGEST_GUIDE.md「発表（T）と台本（S）」（5co-CI-kit v3.13） -->
<style id="ci-digest-talk-css">
/* 発表の見せ方は html.ci-talk（キー T／#talk）のときだけ。各ページのボタンでダイジェストにしただけでは変わらない */
@media screen{
/* 見出し2行: 1行目＝話題（小さく）、2行目＝答え（crystal-25 の下線）。文言は data-talk-h か既存の「話題｜答え」 */
html.ci-talk:not(.ci-static) .ci-tk-t{display:block; font-size:.62em; font-weight:700; color:var(--ink-60); letter-spacing:.02em;}
html.ci-talk:not(.ci-static) .ci-tk-sep{display:none;}
html.ci-talk:not(.ci-static) .ci-tk-a{display:inline; background:linear-gradient(transparent 62%, var(--crystal-25) 62%);}
/* 上の要点の帯（.gist）は画面から外す＝台本（S）に出す。ボタンは残す */
html.ci-talk:not(.ci-static) section.slide > .gist,
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] > .gist{display:none !important;}
/* 右の説明カード（point・v1.8 型の .dgx-side／.dgx-next／.dgx-card・data-talk-hide）は外す */
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] [data-digest-keep="point"],
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] :is(.dgx-side,.dgx-next,.dgx-card),
html.ci-talk:not(.ci-static) section.slide [data-talk-hide]{display:none !important;}
/* hero は最初の1つだけ・大きく（--talk-zoom で調整・既定 1.25） */
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] > [data-digest-keep="hero"]:not(.ci-talk-main){display:none !important;}
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-talk-main{flex:1 1 auto; margin-right:0 !important;}
html.ci-talk:not(.ci-static) section.slide[data-page-mode="digest"] > .ci-talk-main > *{zoom:var(--talk-zoom,1.25);}
/* 台本の帯（発表者用・画面下）: S を押したときに JS が作る */
.ci-talk-bar{display:none;}
html.ci-script-on:not(.ci-static) .ci-talk-bar{display:flex; gap:12px; align-items:baseline; position:fixed; left:0; right:0; bottom:0; z-index:9000;
  background:var(--ink); color:var(--white); font-size:15px; line-height:1.6; padding:10px 22px;}
.ci-talk-bar .ci-talk-pg{flex:none; color:var(--crystal-55); font-weight:700;}
.ci-talk-bar .ci-talk-src{flex:none; font-size:11px; color:var(--crystal-25); border:1px solid var(--crystal-55); border-radius:999px; padding:0 8px;}
.ci-talk-bar .ci-talk-txt{flex:1 1 auto;}
/* v1.9.1: 台本の帯がフッター行（コピーライト・版スタック・集計期間・頁番号・ダイジェスト/詳細に戻すボタン）を隠さない。
   ①帯の分だけ下に余白（最後のページも帯の上までスクロールでき、scrollIntoView も帯の上で止まる）
   ②スライドの横が画面に収まり、高さが「画面の高さ − 帯」より高いとき（全画面で映す等）は html.ci-talk-lift＝フッター行を帯の高さだけ持ち上げ、
     主役（hero）の下にも同じだけ余白を取る（--ci-talk-lift はスライド内の px・スマホ幅の縮小 zoom も換算済み）。
   帯を閉じれば元どおり（S を押していない表示・T だけの表示は変えない） */
html.ci-script-on:not(.ci-static){scroll-padding-bottom:var(--ci-talk-bar-h,44px);}
html.ci-script-on:not(.ci-static) body{padding-bottom:var(--ci-talk-bar-h,44px) !important;}
html.ci-script-on:not(.ci-static).ci-talk-lift section.slide::before,
html.ci-script-on:not(.ci-static).ci-talk-lift section.slide::after,
html.ci-script-on:not(.ci-static).ci-talk-lift section.slide > :is(.period,.ci-stack,.ci-digest-btn,[data-talk-footer]){translate:0 calc(-1 * var(--ci-talk-lift,0px));}
html.ci-script-on:not(.ci-static).ci-talk-lift section.slide[data-page-mode="digest"] > .ci-talk-main{margin-bottom:var(--ci-talk-lift,0px) !important;}
/* v1.9.2: 持ち上げ中は、スライド下半分にある絶対配置の要素（表紙の CI 説明・締めの同意欄など。全面の背景は除く）も
   同じだけ持ち上げる＝持ち上げたフッター行と重ならない。印（data-ci-tk-lift）は JS が付け外しする */
html.ci-script-on:not(.ci-static).ci-talk-lift section.slide > [data-ci-tk-lift]{translate:0 calc(-1 * var(--ci-talk-lift,0px));}
}
@media print{ .ci-talk-bar{display:none !important;} }
</style>
<script id="ci-digest-talk-js">
/* ci-digest-talk v1.9.2: T／#talk＝hero のある全ページを一括でダイジェスト＋発表の見せ方、S＝台本の帯。
   台本＝section の data-talk-script（無ければ「このページの要点」）。見出し＝section の data-talk-h「話題｜答え」（無ければ h2.title の「話題｜答え」）。
   各ページのボタンはそのまま（表示を合わせる）。#static・印刷では何もしない（印刷の前に外し、後で戻す）。 */
(function(){
  if (window.CIDigestTalk) return;
  var R = document.documentElement, D = document, SEP = "｜", FULL = "ダイジェスト", DIG = "詳細に戻す";
  function isStatic(){ return R.classList.contains("ci-static") || /(^|[#&])static\b/.test(location.hash); }
  function slides(){ return [].slice.call(D.querySelectorAll("section.slide")); }
  function esc(t){ var d = D.createElement("div"); d.textContent = t; return d.innerHTML; }
  function sepAt(h){ var depth = 0; for (var k = 0; k < h.length; k++){ var c = h.charAt(k);
    if (c === "<") depth++; else if (c === ">") depth = Math.max(0, depth - 1); else if (c === SEP && depth === 0) return k; } return -1; }
  function splitTitle(s){
    var t = s.querySelector(":scope > h2.title"); if (!t || t.hasAttribute("data-ci-tk-orig")) return;
    var h = s.hasAttribute("data-talk-h") ? esc(s.getAttribute("data-talk-h")) : t.innerHTML, i = sepAt(h);
    if (i <= 0 && !s.hasAttribute("data-talk-h")) return;
    t.setAttribute("data-ci-tk-orig", t.innerHTML);
    t.innerHTML = i > 0 ? '<span class="ci-tk-t">' + h.slice(0, i) + '</span><span class="ci-tk-sep">' + SEP + '</span><span class="ci-tk-a">' + h.slice(i + 1) + "</span>"
                        : '<span class="ci-tk-a">' + h + "</span>";
  }
  function restoreTitle(s){ var t = s.querySelector(":scope > h2.title"); if (!t || !t.hasAttribute("data-ci-tk-orig")) return;
    t.innerHTML = t.getAttribute("data-ci-tk-orig"); t.removeAttribute("data-ci-tk-orig"); }
  function syncBtn(s){ var b = s.querySelector(":scope > .ci-digest-btn"); if (!b) return;
    var on = s.getAttribute("data-page-mode") === "digest"; b.textContent = on ? DIG : FULL; b.setAttribute("aria-pressed", on ? "true" : "false"); }
  function talk(on){
    on = !!on && !isStatic();
    R.classList.toggle("ci-talk", on);
    slides().forEach(function(s){
      if (s.classList.contains("cover-full")) return;
      var hero = s.querySelector(':scope > [data-digest-keep="hero"]');
      if (on){
        splitTitle(s);
        if (hero && !s.hasAttribute("data-ci-tk-mode")){
          s.setAttribute("data-ci-tk-mode", s.getAttribute("data-page-mode") || "");
          s.setAttribute("data-page-mode", "digest"); hero.classList.add("ci-talk-main");
        }
      } else {
        restoreTitle(s);
        if (s.hasAttribute("data-ci-tk-mode")){
          var m = s.getAttribute("data-ci-tk-mode");
          if (m) s.setAttribute("data-page-mode", m); else s.removeAttribute("data-page-mode");
          s.removeAttribute("data-ci-tk-mode");
          [].forEach.call(s.querySelectorAll(":scope > .ci-talk-main"), function(x){ x.classList.remove("ci-talk-main"); });
        }
      }
      syncBtn(s);
    });
    script();
    return on;
  }
  function current(){
    var best = -1, area = 0, vh = innerHeight, vw = innerWidth;
    slides().forEach(function(s, i){ var r = s.getBoundingClientRect();
      var a = Math.max(0, Math.min(r.bottom, vh) - Math.max(r.top, 0)) * Math.max(0, Math.min(r.right, vw) - Math.max(r.left, 0));
      if (a > area){ area = a; best = i; } });
    return best;
  }
  function txt(el){ return el ? (el.textContent || "").replace(/\s+/g, " ").trim() : ""; }
  function scriptFor(s){
    var a = (s.getAttribute("data-talk-script") || "").trim();
    if (a) return { text: a, src: "台本" };
    var g = s.querySelector(":scope > .gist") || s.querySelector(".gist");
    if (g){ var c = g.cloneNode(true); [].forEach.call(c.querySelectorAll(".gist-k"), function(k){ k.remove(); });
      if (txt(c)) return { text: txt(c), src: "要点" }; }
    return { text: "（このページに台本・要点なし）", src: "" };
  }
  var bar = null;
  function script(){
    if (!R.classList.contains("ci-script-on")) return;
    var i = current(), s = slides()[i]; if (!s) return;
    if (!bar){ bar = D.createElement("div"); bar.className = "ci-talk-bar"; bar.setAttribute("role", "note"); bar.setAttribute("aria-live", "polite");
      bar.innerHTML = '<b class="ci-talk-pg"></b><span class="ci-talk-src"></span><span class="ci-talk-txt"></span>'; D.body.appendChild(bar); }
    var x = scriptFor(s), src = bar.querySelector(".ci-talk-src");
    bar.querySelector(".ci-talk-pg").textContent = "p" + String(i + 1).padStart(2, "0");
    src.textContent = x.src; src.style.display = x.src ? "" : "none";
    bar.querySelector(".ci-talk-txt").textContent = x.text;
    lift(s);
  }
  function lift(s){   // v1.9.1: 帯の高さを測り、スライドが画面に収まらないときだけフッター行を持ち上げる
    if (!R.classList.contains("ci-script-on") || !bar || !s){ R.classList.remove("ci-talk-lift"); R.style.removeProperty("--ci-talk-lift"); R.style.removeProperty("--ci-talk-bar-h"); tagAbs(false); return; }
    var h = Math.ceil(bar.getBoundingClientRect().height);
    R.style.setProperty("--ci-talk-bar-h", h + "px");
    var r = s.getBoundingClientRect(), k = s.offsetHeight ? r.height / s.offsetHeight : 1;
    if (!(k > 0)) k = 1;
    // 横がはみ出す細い窓は持ち上げず、スクロール（帯の上で止まる）で見せる
    if (r.width <= innerWidth + 2 && r.height > innerHeight - h){ R.style.setProperty("--ci-talk-lift", Math.ceil((h + 4) / k) + "px"); R.classList.add("ci-talk-lift"); tagAbs(true); }
    else { R.classList.remove("ci-talk-lift"); R.style.removeProperty("--ci-talk-lift"); tagAbs(false); }
  }
  var FOOT = ".period,.ci-stack,.ci-digest-btn,[data-talk-footer]", tagged = false;
  function tagAbs(on){   // v1.9.2: スライド下半分の絶対配置（全面の背景・フッター行を除く）に持ち上げの印。位置は translate の影響を受けない offset で測る
    if (on === tagged) return; tagged = on;
    [].forEach.call(D.querySelectorAll("[data-ci-tk-lift]"), function(e){ e.removeAttribute("data-ci-tk-lift"); });
    if (!on) return;
    slides().forEach(function(s){
      var H = s.offsetHeight, W = s.offsetWidth; if (!H) return;
      [].forEach.call(s.children, function(e){
        if (e.matches(FOOT) || e.offsetParent !== s) return;
        var cs = getComputedStyle(e); if (cs.position !== "absolute") return;
        var t = e.offsetTop, eh = e.offsetHeight, ew = e.offsetWidth;
        if (!eh || !ew || (eh >= H * 0.8 && ew >= W * 0.8)) return;
        if (t + eh > H / 2) e.setAttribute("data-ci-tk-lift", "");
      });
    });
  }
  function scriptToggle(on){
    on = (on === undefined ? !R.classList.contains("ci-script-on") : !!on) && !isStatic();
    R.classList.toggle("ci-script-on", on); script(); if (!on) lift(null); return on;
  }
  D.addEventListener("keydown", function(e){
    if (e.metaKey || e.ctrlKey || e.altKey || isStatic()) return;
    var t = e.target; if (t && t.closest && t.closest("input,select,textarea,[contenteditable]")) return;
    if (R.classList.contains("ci-drawer-open")) return;
    if (e.key === "t" || e.key === "T") talk(!R.classList.contains("ci-talk"));
    else if (e.key === "s" || e.key === "S") scriptToggle();
    else setTimeout(script, 0);
  });
  var tick = 0;
  function later(){ if (!R.classList.contains("ci-script-on") || tick) return; tick = requestAnimationFrame(function(){ tick = 0; script(); }); }
  addEventListener("scroll", later, { passive: true }); addEventListener("resize", later);
  D.addEventListener("click", function(){ setTimeout(later, 0); });
  addEventListener("hashchange", function(){ if (isStatic()){ talk(false); scriptToggle(false); } else if (/(^|[#&])talk\b/.test(location.hash)) talk(true); });
  var saved = null;
  addEventListener("beforeprint", function(){ if (saved) return;
    saved = { talk: R.classList.contains("ci-talk"), script: R.classList.contains("ci-script-on") }; talk(false); R.classList.remove("ci-script-on"); lift(null); });
  addEventListener("afterprint", function(){ if (!saved) return; var p = saved; saved = null; if (p.talk) talk(true); if (p.script) scriptToggle(true); });
  window.CIDigestTalk = { talk: talk, script: scriptToggle, scriptFor: function(i){ var s = slides()[i]; return s ? scriptFor(s) : null; } };
  function boot(){ if (/(^|[#&])talk\b/.test(location.hash) && !isStatic()) talk(true); }
  if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", boot); else boot();
})();
</script>
<!-- ci-digest-talk v1.9.2 (END) -->
'''
BLOCK = BLOCK.replace('<!-- ci-digest-toggle v1.9 (END) -->', TALK_BLOCK + '<!-- ci-digest-toggle v1.9 (END) -->', 1)


TALK_RE = re.compile(r'<!-- ci-digest-talk v\d+(?:\.\d+)* \(BEGIN\).*?<!-- ci-digest-talk v\d+(?:\.\d+)* \(END\) -->\n?', re.S)
TOGGLE_END = re.compile(r'<!-- ci-digest-toggle v1(?:\.\d+)? \(END\) -->')


def apply_talk(html):
    """既にダイジェストの切替（ci-digest-toggle 任意の版）が入ったデッキに、発表（T）と台本（S）だけを足す／入れ替える。
    PLAN・hero の印・ほかの CSS には触らない。冪等。切替ブロックが無ければ ValueError。"""
    html = TALK_RE.sub('', html)
    m = list(TOGGLE_END.finditer(html))
    if not m:
        raise ValueError('ci-digest-toggle のブロックがありません（先に digest_toggle.py でダイジェストを付ける）')
    i = m[-1].start()
    return html[:i] + TALK_BLOCK + html[i:]


def add_attr(tag, attr):
    return tag[:-1] + ' ' + attr + '>' if not tag.endswith('/>') else tag[:-2] + ' ' + attr + '/>'

def main(path):
    s = open(path, encoding='utf-8').read()
    n0 = len(s.encode('utf-8'))
    s = re.sub(r'<!-- ci-digest-toggle v1(?:\.\d+)? \(BEGIN\).*?<!-- ci-digest-toggle v1(?:\.\d+)? \(END\) -->\n?', '', s, flags=re.S)
    s = re.sub(r' data-digest-keep="(?:hero|point|photo)"', '', s)
    s = re.sub(r'--dg-w:[\d.]+%; ?', '', s)
    s = re.sub(r'--dg-ar:[\d./]+; ?', '', s)
    s = re.sub(r' data-dg-card="action"', '', s)
    s = re.sub(r' data-digest-layout="[a-z0-9]+"', '', s)
    s = re.sub(r'<figure class="dg-photo"[^>]*>.*?</figure>', '', s, flags=re.S)
    s = re.sub(r'<span class="dg-(?:gap|t|num)">(.*?)</span>', r'\1', s)
    for pid, plan in PLAN.items():
        a = s.find(f'<section class="slide" id="{pid}"'); assert a >= 0, pid
        b = s.find('<section class="slide', a + 10); b = len(s) if b < 0 else b
        sec = s[a:b]
        visual = plan.get('visual', 'fig')
        if visual == 'fig':
            m = re.search(r'<div class="fig ci-fig" data-fig="%s"[^>]*>' % pid, sec); assert m, pid
            tag = m.group(0)
            if plan.get('crop'):
                tag = tag.replace('style="', f'style="--dg-w:{plan["crop"]}; ' + (f'--dg-ar:{plan["ar"]}; ' if plan.get('ar') else ''), 1)
            sec = sec[:m.start()] + add_attr(tag, 'data-digest-keep="hero"') + sec[m.end():]
        elif visual == 'num':
            assert plan.get('photo'), pid
            m = re.search(plan.get('num_sel', r'<div class="okr"[^>]*>'), sec); assert m, pid
            sec = sec[:m.start()] + add_attr(m.group(0), 'data-digest-keep="hero"') + sec[m.end():]
            i = sec.rfind('<p class="note-line"'); i = i if i > 0 else sec.rfind('</section>'); assert i > 0, pid
            size = plan.get('photo_size')
            style = f' style="--dg-pw:{size[0]}; --dg-ph:{size[1]};"' if size else ''
            sec = sec[:i] + f'<figure class="dg-photo" data-digest-keep="photo" data-dg-photo="cutout"{style} aria-hidden="true"><img src="{plan["photo"]}" alt="{plan.get("photo_alt", "")}" loading="lazy" decoding="async"></figure>' + sec[i:]
        elif visual == 'photo':
            assert plan.get('photo'), pid
            i = sec.rfind('<p class="note-line"'); assert i > 0, pid
            size = plan.get('photo_size')
            style = f' style="--dg-pw:{size[0]}; --dg-ph:{size[1]};"' if size else ''
            kind = f' data-dg-photo="{plan["photo_kind"]}"' if plan.get('photo_kind') else ''
            sec = sec[:i] + f'<figure class="dg-photo" data-digest-keep="hero"{kind}{style} aria-hidden="true"><img src="{plan["photo"]}" alt="{plan.get("photo_alt", "")}" loading="lazy" decoding="async"></figure>' + sec[i:]
        else:
            raise ValueError(f'{pid}: unknown visual={visual!r}')
        # .gist is shown by CSS (no point attr). visual='photo' = photo-as-sole-hero; visual='num' = 数字 hero ＋ photo keep.
        s = s[:a] + sec + s[b:]
    i = s.rfind('</body>'); assert i > 0
    s = s[:i] + BLOCK + s[i:]
    open(path, 'w', encoding='utf-8').write(s)
    print('ok', path, n0, '->', len(s.encode('utf-8')), f'(+{len(s.encode("utf-8"))-n0} B)')

if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--talk':   # 発表（T）と台本（S）だけを足す（v1.9・PLAN を使わない）
        for p in args[1:]:
            h = open(p, encoding='utf-8').read()
            open(p, 'w', encoding='utf-8').write(apply_talk(h))
            print('talk ok', p)
    else:
        for p in args: main(p)
