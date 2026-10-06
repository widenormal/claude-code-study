/* =====================================================================
   5co CI 動く資料レイヤー v3.9（任意・正本 5co-CI-kit・編集は PR 経由のみ）
   ci_head.py --interactive のときだけ <script> として連結される。外部読み込みなし。

   デッキ側が書くのは data 属性だけ（JS を書かない。計算式だけは CIInteractive.define で登録）:
     根拠パネル    <button class="ci-ev-btn" data-ci-ev="ev-p2">内訳を見る</button>
                   <template id="ev-p2" data-crumb="現状 › 荷待ち" data-judge="…" data-src="…">
                     <section data-ci-tab="内訳">…</section><section data-ci-tab="出所と前提">…</section>
                   </template>
     ページへ飛ぶ  <div data-ci-goto="p3">…</div>（p3 = 飛び先 .slide の id、または 1 始まりのページ番号）
     1枚1操作      <div data-ci-op data-ci-static="後">          … 操作の入れ物（1ページに1つ）
                     <button data-ci-set="前">前</button><button data-ci-set="後">後</button>  切り口・前後
                     <button data-ci-toggle="打ち手A">…</button>                              オン/オフ
                     <input type="range" data-ci-var="単価" min=… max=… value=…>              条件
                     <div data-ci-when="後">…</div> <div data-ci-when="+打ち手A">…</div>       出し分け
                     <div data-ci-bar class="ci-h" data-ci-values='{"前":40,"後":25}'></div>   値で伸びる棒
                                                  （入れ物の最大値＝1。前後で目盛りをそろえるときは data-ci-max）
                     <div class="ci-ghost" data-ci-ghost="前"></div>（棒の隣）                  差分で前の値を点線で残す
                     <b data-ci-out="残り"></b>                                               計算結果
                   </div>
                   計算式（デッキの末尾で1回）: CIInteractive.define("残り", s => (s.vars.単価 * 12).toLocaleString())
     組み上がり    data-ci-step="1|2|3|4"（見出し→主役の図→数字→根拠）。棒は class="ci-grow"
   静止状態: URL の #static・「動きを減らす」設定・印刷では、組み上がった最終状態を出す。
     操作は data-ci-static（切り口）／data-ci-static-on（オンにするもの・省略時は全部オン）で
     「見出しの判断が見える状態」に固定する。検査と PDF はこの状態を見る。
   キー: →/Space/PageDown 次・← 前・数字＋少し待つ でそのページ・Esc 閉じる/戻る・O 一覧・F 発表モード
   ===================================================================== */
(function () {
  "use strict";
  var doc = document, root = doc.documentElement;
  var fns = Object.create(null);
  // FIXED＝#static（検査・PDF）：最終状態に固定し、操作も受け付けない。
  // STATIC＝動きを出さない（FIXED か OS の「動きを減らす」）。動きを減らす人は操作はできる。
  // どちらも起動時に1回だけ判定する（途中で OS 設定や hash を変えても追従しない）。
  var FIXED = /(^|[#&])static\b/.test(location.hash);
  var STATIC = FIXED || !!(window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  function num(v, d) { var n = parseFloat(v); return isFinite(n) ? n : d; }

  function $all(sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); }
  function slides() { return $all(".slide"); }
  function words(v) { return (v || "").split(/\s+/).filter(Boolean); }

  /* ---------- 1枚1操作 ---------- */
  function opState(op) {
    if (!op._ci) {
      var sets = $all("[data-ci-set]", op).map(function (b) { return b.getAttribute("data-ci-set"); });
      var toggles = $all("[data-ci-toggle]", op).map(function (b) { return b.getAttribute("data-ci-toggle"); });
      var vars = {};
      $all("[data-ci-var]", op).forEach(function (i) { vars[i.getAttribute("data-ci-var")] = num(i.defaultValue, num(i.min, 0)); });
      var mode, on;
      if (STATIC) {
        mode = op.getAttribute("data-ci-static") || sets[0] || "";
        on = op.hasAttribute("data-ci-static-on") ? words(op.getAttribute("data-ci-static-on")) : toggles;
      } else {
        mode = op.getAttribute("data-ci-initial") || sets[0] || "";
        on = words(op.getAttribute("data-ci-initial-on"));
      }
      op._ci = { mode: mode, on: new Set(on), vars: vars };
    }
    return op._ci;
  }

  function render(op) {
    var s = opState(op);
    op.setAttribute("data-ci-mode", s.mode);
    $all("[data-ci-set]", op).forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-ci-set") === s.mode));
    });
    $all("[data-ci-toggle]", op).forEach(function (b) {
      b.setAttribute("aria-pressed", String(s.on.has(b.getAttribute("data-ci-toggle"))));
    });
    $all("[data-ci-var]", op).forEach(function (i) {
      var k = i.getAttribute("data-ci-var");
      if (parseFloat(i.value) !== s.vars[k]) i.value = s.vars[k];
      op.style.setProperty("--ci-" + k, s.vars[k]);
    });
    $all("[data-ci-when]", op).forEach(function (el) {
      var ok = words(el.getAttribute("data-ci-when")).every(function (w) {
        if (w.charAt(0) === "+") return s.on.has(w.slice(1));
        if (w.charAt(0) === "-") return !s.on.has(w.slice(1));
        return w === s.mode;
      });
      el.classList.toggle("ci-off", !ok);
      el.setAttribute("aria-hidden", String(!ok));
      if (ok) el.removeAttribute("inert"); else el.setAttribute("inert", "");   // 隠れた中のボタンに Tab で入らない
    });
    // 値で伸びる棒：入れ物ごとの最大値を1として比で描く（量を表す動きは値から計算する）
    var bars = $all("[data-ci-bar]", op), vals = bars.map(function (b) {
      var raw = b.getAttribute("data-ci-values");
      if (raw) { try { var o = JSON.parse(raw); return Math.max(0, num(o[s.mode], 0)); } catch (e) { return 0; } }
      return Math.max(0, num(b.getAttribute("data-ci-value"), 0));
    });
    var max = num(op.getAttribute("data-ci-max"), 0);
    if (!(max > 0)) max = Math.max.apply(null, vals.concat([0])) || 1;   // 0・負・非数は値の最大へ
    bars.forEach(function (b, i) {
      b.style.setProperty("--ci-v", String(Math.max(0, vals[i]) / max));
      // 差分：比べる前の値を点線で残す（同じ目盛り＝data-ci-max で前後をそろえる）
      var g = (b.closest("[data-ci-row]") || b.parentNode).querySelector("[data-ci-ghost]");
      if (g) {
        var gs = g.getAttribute("data-ci-ghost"), gv = 0;
        try { gv = Math.max(0, num(JSON.parse(b.getAttribute("data-ci-values"))[gs], 0)); } catch (e) { gv = 0; }
        g.style.width = (Math.max(0, gv) / max * 100) + "%";
        g.classList.toggle("ci-off", s.mode === gs);
      }
    });
    if (op.getAttribute("data-ci-sort") === "desc" || op.getAttribute("data-ci-sort") === "asc") {
      var dir = op.getAttribute("data-ci-sort") === "desc" ? -1 : 1;
      var rows = bars.map(function (b, i) { return { el: b.closest("[data-ci-row]") || b, v: vals[i] }; });
      rows.slice().sort(function (a, b) { return dir * (a.v - b.v); })
        .forEach(function (r, rank) { r.el.style.order = String(rank); });
    }
    $all("[data-ci-out]", op).forEach(function (el) {
      var f = fns[el.getAttribute("data-ci-out")];
      if (!el.hasAttribute("aria-live")) el.setAttribute("aria-live", "polite");
      if (typeof f === "function") { try { el.textContent = f(s); } catch (e) { el.textContent = "—"; } }
    });
  }

  function renderAll() { $all("[data-ci-op]").forEach(render); }

  doc.addEventListener("click", function (e) {
    var t = e.target.closest("[data-ci-set],[data-ci-toggle],[data-ci-ev],[data-ci-goto]");
    if (!t) return;
    e.preventDefault();   // <a href>・フォーム内 <button> に付いても遷移・送信しない
    if (t.hasAttribute("data-ci-ev")) { openDrawer(t.getAttribute("data-ci-ev"), t); return; }
    if (t.hasAttribute("data-ci-goto")) { goTo(t.getAttribute("data-ci-goto"), true); return; }
    if (FIXED) return;   // #static（検査・PDF）では状態を動かさない
    var op = t.closest("[data-ci-op]");
    if (!op) return;
    var s = opState(op);
    if (t.hasAttribute("data-ci-set")) s.mode = t.getAttribute("data-ci-set");
    else { var k = t.getAttribute("data-ci-toggle"); if (s.on.has(k)) s.on.delete(k); else s.on.add(k); }
    render(op);
  });
  doc.addEventListener("input", function (e) {
    var i = e.target.closest && e.target.closest("[data-ci-var]");
    var op = i && i.closest("[data-ci-op]");
    if (!op) return;
    if (FIXED) { render(op); return; }   // 値を戻す
    opState(op).vars[i.getAttribute("data-ci-var")] = num(i.value, 0);
    render(op);
  });

  /* ---------- 根拠パネル ---------- */
  var drawer, bg, lastFocus;
  function buildDrawer() {
    if (drawer) return;
    bg = doc.createElement("div"); bg.className = "ci-drawer-bg";
    drawer = doc.createElement("aside"); drawer.className = "ci-drawer";
    drawer.setAttribute("role", "dialog"); drawer.setAttribute("aria-modal", "true");
    drawer.setAttribute("aria-label", "根拠");
    drawer.innerHTML = '<header><div class="ci-crumb"></div><div class="ci-judge"></div>' +
      '<button class="ci-close" aria-label="閉じる">×</button></header>' +
      '<nav class="ci-tabs" role="tablist"></nav><div class="ci-body"></div><div class="ci-src"></div>';
    doc.body.appendChild(bg); doc.body.appendChild(drawer);
    bg.addEventListener("click", closeDrawer);
    // 開いている間は Tab をパネルの中で回す（背面へ抜けない）
    drawer.addEventListener("keydown", function (e) {
      if (e.key !== "Tab") return;
      var f = $all("button,a[href],input,select,textarea,[tabindex]:not([tabindex='-1'])", drawer)
        .filter(function (el) { return !el.disabled && el.offsetParent !== null; });
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && doc.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && doc.activeElement === last) { e.preventDefault(); first.focus(); }
    });
    drawer.querySelector(".ci-close").addEventListener("click", closeDrawer);
  }
  function openDrawer(id, from) {
    var tpl = doc.getElementById(id);
    if (!tpl || tpl.tagName !== "TEMPLATE") { console.warn("CI: 根拠パネルが見つかりません: " + id); return; }
    buildDrawer();
    lastFocus = from || doc.activeElement;
    drawer.querySelector(".ci-crumb").textContent = tpl.getAttribute("data-crumb") || "";
    drawer.querySelector(".ci-judge").textContent = tpl.getAttribute("data-judge") || "";
    var src = tpl.getAttribute("data-src") || "";
    var srcEl = drawer.querySelector(".ci-src");
    srcEl.textContent = src; srcEl.style.display = src ? "" : "none";
    var frag = tpl.content.cloneNode(true);
    var tabs = $all("section[data-ci-tab]", frag).slice(0, 2);   // タブは2つまで
    var nav = drawer.querySelector(".ci-tabs"), body = drawer.querySelector(".ci-body");
    nav.innerHTML = ""; body.innerHTML = "";
    if (tabs.length) {
      tabs.forEach(function (sec, i) {
        var b = doc.createElement("button");
        b.setAttribute("role", "tab"); b.textContent = sec.getAttribute("data-ci-tab");
        sec.setAttribute("role", "tabpanel");
        b.addEventListener("click", function () { showTab(i); });
        nav.appendChild(b); body.appendChild(sec);
      });
      nav.style.display = "";
      showTab(0);
    } else { nav.style.display = "none"; body.appendChild(frag); }
    root.classList.add("ci-drawer-open");
    drawer.removeAttribute("aria-hidden");
    drawer.querySelector(".ci-close").focus();
  }
  function showTab(n) {
    $all(".ci-tabs button", drawer).forEach(function (b, i) { b.setAttribute("aria-selected", String(i === n)); });
    $all(".ci-body > section[data-ci-tab]", drawer).forEach(function (s, i) { s.hidden = i !== n; });
  }
  function closeDrawer() {
    if (!root.classList.contains("ci-drawer-open")) return false;
    root.classList.remove("ci-drawer-open");
    drawer.setAttribute("aria-hidden", "true");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
    return true;
  }

  /* ---------- 移動・一覧・発表モード ---------- */
  var cur = 0, SW = 0, SH = 0;
  function fit() {
    // 寸法は通常表示のうちに測っておく（発表モード中は他のスライドが display:none で 0 になる）
    var s = slides()[cur] || slides()[0];
    if (!SW && s && s.offsetWidth) { SW = s.offsetWidth; SH = s.offsetHeight; }
    var w = SW || 1122.5, h = SH || 793.7;   // 既定＝A4横 297×210mm @96dpi
    var k = Math.min(innerWidth / w, innerHeight / h) * 0.98;
    root.style.setProperty("--ci-fit", String(isFinite(k) && k > 0 ? k : 1));
  }
  function nearest() {
    var best = 0, bestD = Infinity, mid = innerHeight / 2;
    slides().forEach(function (s, i) {
      var r = s.getBoundingClientRect(), d = Math.abs((r.top + r.bottom) / 2 - mid);
      if (d < bestD) { bestD = d; best = i; }
    });
    return best;
  }
  function build(s) {
    if (STATIC) { s.classList.add("ci-built"); return; }
    s.classList.remove("ci-built");
    void s.offsetWidth;
    var done = false, go = function () { if (!done) { done = true; s.classList.add("ci-built"); } };
    requestAnimationFrame(function () { requestAnimationFrame(go); });
    setTimeout(go, 50);   // 背景タブ等で rAF が止まっても組み上がる
  }
  function show(i, zoom) {
    var all = slides(); if (!all.length) return;
    cur = Math.max(0, Math.min(all.length - 1, i));
    all.forEach(function (s, k) { s.classList.toggle("ci-cur", k === cur); s.classList.remove("ci-zoom-in"); });
    var s = all[cur];
    if (root.classList.contains("ci-present")) {
      if (zoom && !STATIC) { void s.offsetWidth; s.classList.add("ci-zoom-in"); }
      build(s);
    } else {
      s.scrollIntoView({ behavior: STATIC ? "auto" : "smooth", block: "center" });
    }
  }
  function goTo(ref, zoom) {
    closeDrawer();
    if (root.classList.contains("ci-overview")) root.classList.remove("ci-overview");
    // id（スライド内の要素）を先に見て、無ければ「数字だけ」のときに限りページ番号として扱う
    var all = slides(), el = doc.getElementById(ref), sl = el && el.closest(".slide");
    var i = sl ? all.indexOf(sl) : (/^\d+$/.test(String(ref)) ? parseInt(ref, 10) - 1 : -1);
    if (i >= 0 && i < all.length) show(i, zoom);
  }
  function step(d) {
    if (!root.classList.contains("ci-present")) cur = nearest();
    show(cur + d, false);
  }
  function toggleOverview() {
    if (!root.classList.contains("ci-present")) cur = nearest();
    root.classList.toggle("ci-overview");
    slides().forEach(function (s, k) { s.classList.toggle("ci-cur", k === cur); });
    if (!root.classList.contains("ci-overview")) show(cur, false);
    else slides()[cur].scrollIntoView({ block: "center" });
  }
  function togglePresent() {
    if (!root.classList.contains("ci-present")) cur = nearest();
    root.classList.remove("ci-overview");
    fit();   // 切り替える前（全スライドが見えている状態）で測る
    root.classList.toggle("ci-present");
    show(cur, false);
  }
  doc.addEventListener("click", function (e) {
    if (!root.classList.contains("ci-overview")) return;
    var s = e.target.closest(".slide"); if (!s) return;
    e.preventDefault(); e.stopPropagation();
    root.classList.remove("ci-overview"); show(slides().indexOf(s), true);
  }, true);

  var digits = "", digitTimer = 0;
  doc.addEventListener("keydown", function (e) {
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var t = e.target;
    if (e.key === "Escape" && closeDrawer()) { e.preventDefault(); return; }   // 入力欄の中からでも閉じられる
    if (t.closest && t.closest("input,select,textarea,[contenteditable],[role=tablist]")) return;
    if ((e.key === " " || e.key === "Enter") && t.closest && t.closest("button,a,[data-ci-ev],[data-ci-goto]")) return;
    if (root.classList.contains("ci-drawer-open") && e.key !== "Escape") return;
    var k = e.key;
    if (!/^[0-9]$/.test(k)) { digits = ""; clearTimeout(digitTimer); }   // 数字の途中で別の操作をしたら取り消す
    if (k === "ArrowRight" || k === " " || k === "PageDown") { e.preventDefault(); step(1); }
    else if (k === "ArrowLeft" || k === "PageUp") { e.preventDefault(); step(-1); }
    else if (k === "Escape") {
      if (root.classList.contains("ci-overview")) toggleOverview();
      else if (root.classList.contains("ci-present")) togglePresent();
    }
    else if (k === "o" || k === "O") toggleOverview();
    else if (k === "f" || k === "F") togglePresent();
    else if (/^[0-9]$/.test(k)) {
      digits += k; clearTimeout(digitTimer);
      digitTimer = setTimeout(function () { var n = parseInt(digits, 10); digits = ""; if (n > 0) goTo(String(n), true); }, 600);
    }
  });
  addEventListener("resize", fit);

  /* ---------- 起動 ---------- */
  // 印刷：発表モード・一覧・パネルを外し、最終状態で刷る。終わったら元に戻す（印刷をやめた場合も）
  var printSaved = null;
  function beforePrint() {
    if (printSaved) return;
    printSaved = { cls: ["ci-present", "ci-overview", "ci-drawer-open", "ci-static"].filter(function (c) { return root.classList.contains(c); }),
                   ops: $all("[data-ci-op]").map(function (op) { return [op, op._ci]; }), fixed: FIXED, stat: STATIC };
    root.classList.remove("ci-present", "ci-overview", "ci-drawer-open");
    FIXED = STATIC = true; root.classList.add("ci-static");
    $all("[data-ci-op]").forEach(function (op) { op._ci = null; });
    renderAll(); slides().forEach(function (s) { s.classList.add("ci-built"); });
  }
  function afterPrint() {
    if (!printSaved) return;
    var p = printSaved; printSaved = null;
    FIXED = p.fixed; STATIC = p.stat;
    root.classList.remove("ci-static");
    p.cls.forEach(function (c) { root.classList.add(c); });
    p.ops.forEach(function (x) { x[0]._ci = x[1]; });
    renderAll();
  }
  function init() {
    root.classList.add("ci-interactive");
    if (STATIC) root.classList.add("ci-static");
    slides().forEach(function (s) {
      var count = {};
      $all("[data-ci-step]", s).forEach(function (el) {
        var n = parseInt(el.getAttribute("data-ci-step"), 10) || 0;
        count[n] = (count[n] || 0);
        el.style.setProperty("--ci-step", String(n - 1 < 0 ? 0 : n - 1));
        el.style.setProperty("--ci-i", String(count[n]++));
      });
      // カードのページ番号は飛び先から数える（直書きしない＝並べ替えてもずれない。pgref で包む）
      $all("[data-ci-goto] .ci-card-go", s).forEach(function (lab) {
        if (lab.textContent.trim()) return;
        var ref = lab.closest("[data-ci-goto]").getAttribute("data-ci-goto"), el = doc.getElementById(ref);
        var n = el ? slides().indexOf(el.closest(".slide") || el) + 1 : parseInt(ref, 10);
        if (n > 0) lab.innerHTML = 'p.<span class="pgref">' + n + "</span>";
      });
      $all("[data-ci-ev],[data-ci-goto]", s).forEach(function (el) {
        el.classList.add("ci-hint");
        if (!/^(BUTTON|A)$/.test(el.tagName)) { el.setAttribute("tabindex", "0"); el.setAttribute("role", "button"); }
      });
    });
    renderAll();
    if (STATIC) { slides().forEach(function (s) { s.classList.add("ci-built"); }); return; }
    var keys = doc.createElement("div"); keys.className = "ci-keys";
    keys.textContent = "→ 次　← 前　O 一覧　F 発表　Esc 閉じる";
    doc.body.appendChild(keys);
    setTimeout(function () { keys.style.transition = "opacity .6s"; keys.style.opacity = "0"; }, 8000);   // 本文に重ならないよう数秒で消す
    if ("IntersectionObserver" in window) {
      // 4割見えたら組み上げる。画面が小さく4割に届かないときは、画面の6割を占めたら組み上げる
      var io = new IntersectionObserver(function (es) {
        es.forEach(function (en) {
          var enough = en.intersectionRatio >= 0.4 || en.intersectionRect.height >= innerHeight * 0.6;
          if (en.isIntersecting && enough && !root.classList.contains("ci-present") && !en.target.classList.contains("ci-built")) build(en.target);
        });
      }, { threshold: [0, 0.1, 0.2, 0.3, 0.4] });
      slides().forEach(function (s) { io.observe(s); });
    } else { slides().forEach(function (s) { s.classList.add("ci-built"); }); }
  }
  addEventListener("beforeprint", beforePrint);
  addEventListener("afterprint", afterPrint);
  addEventListener("keydown", function (e) {
    // Enter / Space で押せる要素（div 等に付けた data-ci-ev / data-ci-goto）
    if ((e.key === "Enter" || e.key === " ") && e.target.matches && e.target.matches("[data-ci-ev]:not(button),[data-ci-goto]:not(button):not(a)")) {
      e.preventDefault(); e.target.click();
    }
  });

  window.CIInteractive = {
    define: function (name, fn) { if (typeof fn === "function") { fns[name] = fn; renderAll(); } },
    open: openDrawer, close: closeDrawer, go: goTo, isStatic: function () { return STATIC; }
  };
  if (doc.readyState === "loading") doc.addEventListener("DOMContentLoaded", init); else init();
})();
