// 5co-CI-kit v3.12 digest_person — 「→ pNN」施策リンク＋「← 戻る」（ci-jump-back-js）と #digest=pNN フック（ci-digest-hash-hook）。正＝DIGEST_GUIDE.md「Amazon人物型」。
// デッキには各ブロックを <script id="…"> として </body> 直前（ci-digest-toggle ブロックの後）に入れる。画面のみ・#static／印刷には影響しない。
// ===== <script id="ci-jump-back-js"> =====
/* 施策ページ参照リンク（a[data-ci-jump]）: 移動元の頁・ダイジェスト表示を覚えて施策頁へ移動し、施策頁に「← 戻る」を出す。
   「← 戻る」で元の頁へ戻り、ダイジェスト表示も元の状態に戻す。ブラウザの戻るでも同じ。画面のみ（#static・印刷では出ない）。 */
(function(){
  var ret = null;
  function backBtn(t){
    var b = t.querySelector(":scope > .ci-back-btn");
    if (!b){ b = document.createElement("button"); b.type = "button"; b.className = "ci-back-btn"; b.textContent = "← 戻る"; b.hidden = true; t.appendChild(b); }
    return b;
  }
  function place(t, b){
    b.style.left = "36px"; b.style.bottom = "40px"; b.style.right = "auto"; b.style.top = "auto";  /* 左下・フッターの上（ダイジェスト切替ボタンと同じ側）。コーナーロゴ・表・フッターに重ねない */
  }
  function hideAll(){ [].forEach.call(document.querySelectorAll(".ci-back-btn"), function(b){ b.hidden = true; }); }
  function goBack(fromPop){
    if (!ret) return;
    var r = ret; ret = null; hideAll();
    var s = document.getElementById(r.id); if (!s) return;
    var isD = s.getAttribute("data-page-mode") === "digest";
    if (isD !== r.digest){ var t = s.querySelector(":scope > .ci-digest-btn"); if (t) t.click(); }
    var go = function(){ s.scrollIntoView({block: "start"}); };
    go(); requestAnimationFrame(go); setTimeout(go, 60);  /* ブラウザのスクロール復元より後に元頁の先頭へ */
  }
  document.addEventListener("click", function(e){
    var a = e.target && e.target.closest && e.target.closest("a[data-ci-jump]");
    if (a){
      var from = a.closest("section.slide"), to = document.getElementById(a.getAttribute("data-ci-jump"));
      if (!to || !from) return;
      e.preventDefault(); e.stopPropagation();
      ret = {id: from.id, digest: from.getAttribute("data-page-mode") === "digest"};
      var b = backBtn(to); place(to, b); b.title = from.id + " へ戻る（表示の状態も元に戻します）"; b.setAttribute("data-ci-back-to", from.id); b.hidden = false;
      try { history.pushState({ciJump: 1, from: from.id}, "", location.href.split("#")[0] + "#" + to.id); } catch (err) {}
      to.scrollIntoView({block: "start"});
      return;
    }
    var bb = e.target && e.target.closest && e.target.closest(".ci-back-btn");
    if (bb){ e.preventDefault(); e.stopPropagation();
      if (history.state && history.state.ciJump){ history.back(); setTimeout(function(){ if (ret) goBack(true); }, 300); }  /* popstate で goBack。履歴に #p12 を残さない */
      else goBack(false); }
  }, true);
  window.addEventListener("popstate", function(){ if (ret) goBack(true); });
})();

// ===== <script id="ci-digest-hash-hook"> =====
/* 比較ページ（compare_p06_ABC.html）用: URL が #digest=p06 のとき、その頁をダイジェスト表示にして先頭へスクロール（画面のみ。#static・印刷・通常の閲覧には影響なし） */
(function(){
  function go(){
    var m=/digest=(p\d+)/.exec(location.hash||""); if(!m) return;
    var s=document.getElementById(m[1]); if(!s) return;
    var b=s.querySelector(":scope > .ci-digest-btn");
    if(b && s.getAttribute("data-page-mode")!=="digest") b.click();
    s.scrollIntoView({block:"start"});
  }
  if(document.readyState==="complete") setTimeout(go,50); else window.addEventListener("load",function(){setTimeout(go,50);});
})();
