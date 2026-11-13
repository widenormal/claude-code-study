/* ws-photo.js — 余白に人物写真を差し込む（オプトイン・CI kit 試作 2026-11-11・CIスライド）
 * ci_head.py --fill-whitespace-photo / ws_photo.py が入れる。素材は審査済みの切り抜きだけ（JSON に data: で同梱）。
 * 判定は描画後に毎回やり直す（通常表示・ダイジェスト・発表・印刷）。本文エリアを 12 列グリッドに切り、
 * 何も無いマス（余白 8px）を探し、条件に合う最大の長方形に置く。文字・図・表に重ねない。条件に合わなければ置かない。
 */
(function () {
  'use strict';
  var D = document, H = D.documentElement;
  var cfgEl = D.getElementById('ws-photo-cfg'); if (!cfgEl) return;
  var CFG; try { CFG = JSON.parse(cfgEl.textContent); } catch (e) { return; }
  var R = CFG.rule || {};
  var COLS = R.cols || 12, GAP = R.gap || 8, PAD = R.pad || 8;
  var MIN_PCT = R.min_pct || 15, MIN_COLS = R.min_cols || 3, MIN_ROWS = R.min_rows || 2, MIN_H = R.min_h_px || 150;
  var ASPECT = R.person_aspect || 0.7;
  var LEAF = /^(IMG|SVG|CANVAS|TABLE|INPUT|BUTTON|VIDEO|PICTURE|svg)$/;
  function vis(el) {
    if (el.checkVisibility && !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return false;
    var r = el.getBoundingClientRect(); return r.width > 0.5 && r.height > 0.5;
  }
  function solid(cs) {
    var bg = cs.backgroundColor; if (bg && bg !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(bg)) return true;
    if (cs.backgroundImage && cs.backgroundImage !== 'none') return true;
    return ['Top', 'Right', 'Bottom', 'Left'].some(function (s) { return parseFloat(cs['border' + s + 'Width']) > 0 && cs['border' + s + 'Style'] !== 'none'; });
  }
  function ownText(el) { for (var n = el.firstChild; n; n = n.nextSibling) if (n.nodeType === 3 && n.nodeValue.trim()) return true; return false; }
  function textRects(el, out) {
    for (var n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType !== 3 || !n.nodeValue.trim()) continue;
      var rg = D.createRange(); rg.selectNodeContents(n);
      [].forEach.call(rg.getClientRects(), function (q) { if (q.width > 0.5 && q.height > 0.5) out.push({ left: q.left, right: q.right, top: q.top, bottom: q.bottom, el: el }); });
    }
  }
  function obstacles(slide) {
    var out = [];
    (function walk(el) {
      for (var c = el.firstElementChild; c; c = c.nextElementSibling) {
        if (c.classList.contains('ws-photo') || /^ci-f[p]-/.test(c.id || '')) continue;  /* 写真自身・ピッカーの層は数えない */
        var cs = getComputedStyle(c);
        if (cs.display === 'none') continue;
        if (!vis(c)) { if (cs.display === 'contents') walk(c); continue; }
        /* 箱は「中身」の大きさで測る：色面・線・画像・表はその箱、文字は文字そのものの範囲（行の右の空きは余白に数える） */
        if (LEAF.test(c.tagName) || solid(cs)) { var rr = c.getBoundingClientRect(); out.push({ left: rr.left, right: rr.right, top: rr.top, bottom: rr.bottom, el: c }); }
        else if (ownText(c)) textRects(c, out);
        if (!LEAF.test(c.tagName)) walk(c);
      }
    })(slide);
    return out;
  }
  function contentBox(slide) {
    var sq = slide.getBoundingClientRect(), cs = getComputedStyle(slide);
    var pl = parseFloat(cs.paddingLeft) || 40, pr = parseFloat(cs.paddingRight) || 40;
    var top = sq.top + (parseFloat(cs.paddingTop) || 40);
    ['.hdr', 'h2.title', '.accent-bar', '.gist'].forEach(function (s) {
      var e = slide.querySelector(s); if (!e || !vis(e)) return;
      var r = e.getBoundingClientRect(); if (r.bottom < sq.top + sq.height * 0.5) top = Math.max(top, r.bottom + GAP);
    });
    var bot = sq.bottom - Math.max(parseFloat(cs.paddingBottom) || 0, 44);
    ['.period', '.ci-digest-btn', '.ci-stack'].forEach(function (s) {
      var e = slide.querySelector(':scope > ' + s); if (!e || !vis(e)) return;
      var r = e.getBoundingClientRect(); if (r.top > sq.top + sq.height * 0.7) bot = Math.min(bot, r.top - GAP);
    });
    return { x: sq.left + pl, y: top, w: sq.width - pl - pr, h: bot - top, sq: sq };
  }
  function hit(a, b) { return a.left < b.x + b.w && a.right > b.x && a.top < b.y + b.h && a.bottom > b.y; }
  /* 空き長方形（マス単位）のうち、人物（幅:高さ≒0.7:1）を一番大きく置けるもの。同じなら広い方・右下寄り */
  function bestRect(free, rows, cols) {
    var hgt = new Array(cols).fill(0), best = null;
    for (var r = 0; r < rows; r++) {
      for (var c = 0; c < cols; c++) hgt[c] = free[r][c] ? hgt[c] + 1 : 0;
      for (var c0 = 0; c0 < cols; c0++) {
        var mh = Infinity;
        for (var c1 = c0; c1 < cols; c1++) {
          mh = Math.min(mh, hgt[c1]); if (!mh) break;
          var w = c1 - c0 + 1, area = w * mh, he = Math.min(mh, w / ASPECT), score = he * he + area * 0.01 + (c1 + r) * 0.0001;
          if (w >= MIN_COLS && mh >= MIN_ROWS && (!best || score > best.score)) best = { c: c0, r: r - mh + 1, w: w, h: mh, score: score, area: area };
        }
      }
    }
    return best;
  }
  function measure(slide) {
    var cb = contentBox(slide); if (cb.h < MIN_H) return null;
    var colW = (cb.w - GAP * (COLS - 1)) / COLS, rowH = colW, rows = Math.floor((cb.h + GAP) / (rowH + GAP));
    if (rows < MIN_ROWS) return null;
    var y0 = cb.y + (cb.h - (rows * rowH + (rows - 1) * GAP)); /* 下端に揃える */
    var obs = obstacles(slide), free = [];
    for (var r = 0; r < rows; r++) { free.push([]); for (var c = 0; c < COLS; c++) {
      var cell = { x: cb.x + c * (colW + GAP) - PAD, y: y0 + r * (rowH + GAP) - PAD, w: colW + 2 * PAD, h: rowH + 2 * PAD };
      free[r][c] = !obs.some(function (o) { return hit(o, cell); });
    } }
    var b = bestRect(free, rows, COLS); slide.__wsFree = free.map(function (r) { return r.map(function (x) { return x ? '.' : '#'; }).join(''); }).join('/'); if (!b) return null;
    var box = { x: cb.x + b.c * (colW + GAP), y: y0 + b.r * (rowH + GAP), w: b.w * colW + (b.w - 1) * GAP, h: b.h * rowH + (b.h - 1) * GAP };
    var pct = 100 * box.w * box.h / (cb.w * cb.h);
    return { box: box, cells: b, pct: pct, cb: cb, colW: colW, rowH: rowH, ok: pct >= MIN_PCT && box.h >= MIN_H };
  }
  function excluded(slide, mode) {
    var why = slide.getAttribute('data-ws-photo-skip'); if (why) return why;
    if (mode !== 'digest') {
      var t = [].filter.call(slide.querySelectorAll('table'), vis);
      if (t.length >= (R.max_tables || 1)) return '表が主役';
    }
    if (H.classList.contains('ci-overview')) return '一覧表示';
    var other = [].filter.call(slide.querySelectorAll('.ci-swap-photo, .dg-photo, .dgx-person, .ci-ins-fig img'), vis);
    if (other.length) return '写真あり（1ページ1枚）';
    return '';
  }
  /* 写真の横にある文字の箱（行の右が空いている見出し・箇条書き）は、写真の手前で幅を止める＝文字は動かさず、箱も重ねない */
  function unnarrow(slide) {
    [].forEach.call(slide.querySelectorAll('[data-ws-narrow]'), function (e) { var v = e.getAttribute('data-ws-narrow'); e.style.removeProperty('max-width'); if (v) e.style.maxWidth = v; e.removeAttribute('data-ws-narrow'); });
  }
  function narrow(slide, f) {
    var fr = f.getBoundingClientRect(), k = slide.offsetWidth / (slide.getBoundingClientRect().width || 1), changed = [], bad = false;
    [].forEach.call(slide.querySelectorAll('*'), function (e) {
      if (e === f || f.contains(e) || e.contains(f) || !ownText(e) || !vis(e)) return;  /* 文字を持つ箱だけ（入れ物は触らない） */
      var cs = getComputedStyle(e); if (cs.position === 'absolute' || cs.position === 'fixed' || cs.display === 'inline') return;
      var r = e.getBoundingClientRect();
      if (!(r.left < fr.left && r.right > fr.left - GAP && r.top < fr.bottom && r.bottom > fr.top)) return;
      changed.push([e, r.height, r.width]);
    });
    changed.forEach(function (c) { var e = c[0], r = e.getBoundingClientRect(), ke = r.width ? e.offsetWidth / r.width : k; /* 発表（T）では hero が拡大されるので要素ごとの倍率で */ e.setAttribute('data-ws-narrow', e.style.maxWidth || ''); e.style.setProperty('max-width', ((fr.left - GAP - r.left) * ke).toFixed(1) + 'px', 'important'); });
    changed.forEach(function (c) { if (Math.abs(c[0].getBoundingClientRect().height - c[1]) > 0.5) bad = true; });
    return !bad;
  }
  function place(slide) {
    var old = slide.querySelector(':scope > .ws-photo'); if (old) old.remove();
    unnarrow(slide);
    var persona = slide.getAttribute('data-ws-photo'); var a = CFG.assets[persona];
    if (!a) { slide.setAttribute('data-ws-photo-state', 'skip:素材なし:' + ((CFG.missing || {})[persona] || '')); return; }
    var mode = slide.getAttribute('data-page-mode') === 'digest' ? 'digest' : 'normal';
    var ex = excluded(slide, mode); if (ex) { slide.setAttribute('data-ws-photo-state', mode + ':skip:' + ex); return; }
    var m = measure(slide);
    if (!m || !m.ok) { slide.setAttribute('data-ws-photo-state', mode + ':none' + (m ? ':' + m.pct.toFixed(1) + '%' : '')); return; }
    /* 人物の幅に合わせて列を詰め、右寄せ。キャプション 16px を下に取る */
    var capH = 16, ph = m.box.h - capH, need = ph * a.w / a.h + 24, nc = Math.min(m.cells.w, Math.max(MIN_COLS, Math.ceil((need + GAP) / (m.colW + GAP))));
    var w = nc * m.colW + (nc - 1) * GAP, x = m.box.x + m.box.w - w;
    var sq = slide.getBoundingClientRect(), k = slide.offsetWidth / sq.width || 1;
    var f = D.createElement('figure'); f.className = 'ws-photo'; f.setAttribute('data-ws-persona', persona);
    f.style.cssText = 'left:' + ((x - sq.left) * k).toFixed(1) + 'px;top:' + ((m.box.y - sq.top) * k).toFixed(1) + 'px;width:' + (w * k).toFixed(1) + 'px;height:' + (m.box.h * k).toFixed(1) + 'px';
    var pn = D.createElement('span'); pn.className = 'ws-panel'; pn.setAttribute('aria-hidden', 'true');
    var im = D.createElement('img'); im.alt = a.alt; im.decoding = 'async'; im.src = a.src;
    var fc = D.createElement('figcaption'); fc.textContent = a.caption;
    f.appendChild(pn); f.appendChild(im); f.appendChild(fc);
    slide.appendChild(f);
    if (!narrow(slide, f)) { unnarrow(slide); f.remove(); slide.setAttribute('data-ws-photo-state', mode + ':none:折り返しが変わる'); return; }
    slide.setAttribute('data-ws-photo-state', mode + ':placed:' + m.pct.toFixed(1) + '%:' + nc + 'x' + m.cells.h);
  }
  var busy = false;
  function run() {
    if (busy) return; busy = true;
    try { [].forEach.call(D.querySelectorAll('section.slide[data-ws-photo]'), place); } finally { setTimeout(function () { busy = false; }, 0); }
  }
  /* 切り替え直後は組み上がりの動きで位置が変わるので、落ち着くまで数回測り直す */
  var t = [], WAITS = [120, 700, 1600];
  function soon() { t.forEach(clearTimeout); t = WAITS.map(function (ms) { return setTimeout(run, ms); }); }
  window.CIWSPhoto = { run: run, measure: measure, obstacles: obstacles, contentBox: contentBox };
  if (D.readyState === 'complete') run(); else addEventListener('load', run);
  addEventListener('resize', soon); D.addEventListener('transitionend', function (e) { if (!(e.target.closest && e.target.closest('.ws-photo'))) { clearTimeout(t[3]); t[3] = setTimeout(run, 150); } }, true); addEventListener('hashchange', soon); addEventListener('beforeprint', run);
  new MutationObserver(function (ms) {
    if (busy) return;
    if (ms.some(function (m) { return !(m.target.closest && m.target.closest('.ws-photo')) && !(m.type === 'attributes' && m.attributeName === 'data-ws-photo-state') && !(m.type === 'attributes' && m.target.hasAttribute && m.target.hasAttribute('data-ws-narrow')); })) soon();
  }).observe(D.documentElement, { attributes: true, attributeFilter: ['class', 'data-page-mode'], subtree: true, childList: true });
})();
