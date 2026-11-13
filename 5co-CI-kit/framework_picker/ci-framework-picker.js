/* ci-framework-picker.js — 社内用「図の型を選ぶ」ピッカー（CI kit 試作 2026-11-11）
 * 社内版（fp_build.py internal）にだけ入る。社外版（fp_build.py external）はこのファイルごと外す。
 * - 各図（data-fp-fig）の下に「型を選ぶ」ボタン → 型の一覧（1つの図に Framework は1つ＝単一選択。v3.21.0・若松さん指摘 2026-11-11）
 *   押すとその型に切り替え／別の型を押すと置き換え／同じ型をもう一度押すと元の図。件数の表示は出さない
 * - 型はこのページの数字（表の値）で描けるものだけを出す。数字で描けない型（見本だけの型）は一覧に出さない
 * - OKR は必ず使う Framework。目標と実績がページにあればおすすめの先頭に出す（無いときは出さない）。ページの実データだけで描く。社外版には入らない（v3.21.1・若松さん指示 2026-11-11）
 * - 選択・文言の修正・写真の置き換えは localStorage にその場で自動保存。バーに「保存」は置かず、JSON のダウンロードもしない（v3.21.0・若松さん指摘 2026-11-11）。
 *   反映は「修正を反映した版を書き出す」だけ
 * - #static・印刷では出さない。Shift+P か右下のバーで「提出プレビュー」と「編集モード」を切り替える（旧「表示中」「非表示」。v3.21.1・若松さん指示 2026-11-11 19:20）
 */
(function () {
  'use strict';
  var D = document, H = D.documentElement;
  var catEl = D.getElementById('ci-fp-catalog');
  if (!catEl) return;
  var CAT; try { CAT = JSON.parse(catEl.textContent); } catch (e) { return; }
  if (/(^|[#&])static\b/.test(location.hash)) { H.classList.add('ci-fp-static'); return; }
  var DECK = H.getAttribute('data-fp-deck') || 'deck';
  var KEY = 'ci-fp:' + DECK;
  var BY = {}; CAT.patterns.forEach(function (p) { BY[p.id] = p; });
  var INK = '#101820', CR = '#C3D7EE', G1 = '#E3E7EC', G2 = '#9AA3AD';

  /* ---------- 状態 ---------- */
  var S = load();
  function load() {
    try { var s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s && s.figures) {
      Object.keys(s.figures).forEach(function (k) { var f = s.figures[k]; if (f.selected && f.selected.length > 1) f.selected = f.selected.slice(-1); });   // 旧版の複数選択は最後の1つだけ残す
      return s; } } catch (e) {}
    return { schema: 'ci-framework-selections/1', deck: DECK, catalog_version: CAT.version, figures: {} };
  }
  function save() {
    S.updated = new Date().toISOString();
    try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {}
  }
  function fig(id) {
    if (!id) return { selected: [], preview: null };
    var f = S.figures[id];
    if (!f) { var el = D.querySelector('[data-fp-fig="' + id + '"]');
      f = S.figures[id] = { page: el ? el.getAttribute('data-fp-page') : '', kind: el ? el.getAttribute('data-fp-kind') : '', selected: [], preview: null }; }
    return f;
  }

  /* ---------- 型見本（数値・文字なしの模式図） ---------- */
  function r(x, y, w, h, f, rx) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="' + f + '"' + (rx ? ' rx="' + rx + '"' : '') + '/>'; }
  function c(x, y, rr, f, s) { return '<circle cx="' + x + '" cy="' + y + '" r="' + rr + '" fill="' + f + '"' + (s ? ' stroke="' + s + '" stroke-width="2"' : '') + '/>'; }
  function l(x1, y1, x2, y2, s, w) { return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="' + (s || INK) + '" stroke-width="' + (w || 2) + '"/>'; }
  function p(d, f, s) { return '<path d="' + d + '" fill="' + (f || 'none') + '"' + (s ? ' stroke="' + s + '" stroke-width="2"' : '') + '/>'; }
  var base = l(20, 160, 300, 160, G2, 1.5);
  var FAM = {
    bars: function () { var o = base; [60, 95, 80, 120, 105, 135].forEach(function (h, i) { o += r(34 + i * 44, 160 - h, 28, h, i === 5 ? INK : CR); }); return o; },
    stacked: function () { var o = ''; for (var i = 0; i < 5; i++) { var a = [40, 55, 35, 60, 45][i], b = [50, 35, 60, 40, 55][i]; o += r(36 + i * 54, 20, 34, a, INK) + r(36 + i * 54, 20 + a, 34, b, CR) + r(36 + i * 54, 20 + a + b, 34, 140 - a - b, G1); } return o; },
    waterfall: function () { var o = base, y = 160, s = [[-90, INK], [-25, CR], [-20, CR], [15, G2], [-30, CR]]; s.forEach(function (v, i) { var h = Math.abs(v[0]); var top = v[0] < 0 ? y - h : y; o += r(30 + i * 50, top, 34, h, v[1]); y = v[0] < 0 ? y - h : y + h; }); o += r(280, y, 30, 160 - y, INK); return o; },
    mekko: function () { var o = '', x = 20, ws = [90, 70, 60, 40, 30]; ws.forEach(function (w, i) { var a = [60, 45, 70, 50, 80][i]; o += r(x, 20, w - 3, a, INK) + r(x, 20 + a, w - 3, 50, CR) + r(x, 70 + a, w - 3, 70 - a + 20, G1); x += w; }); return o; },
    tornado: function () { var o = l(160, 14, 160, 166, INK, 1.5); [120, 95, 75, 55, 35, 20].forEach(function (w, i) { o += r(160 - w, 18 + i * 25, w, 18, CR) + r(160, 18 + i * 25, w * 0.8, 18, INK); }); return o; },
    butterfly: function () { var o = ''; [100, 80, 120, 60, 90].forEach(function (w, i) { var w2 = [70, 110, 50, 95, 65][i]; o += r(150 - w, 20 + i * 29, w, 20, INK) + r(170, 20 + i * 29, w2, 20, CR); }); return o + r(152, 14, 16, 152, G1); },
    scatter: function () { var o = l(30, 160, 300, 160, G2, 1.5) + l(30, 160, 30, 15, G2, 1.5); [[70, 120, 14], [120, 80, 22], [190, 110, 10], [230, 50, 26], [270, 130, 8], [160, 40, 12]].forEach(function (b, i) { o += c(b[0], b[1], b[2], i === 3 ? INK : CR); }); return o; },
    radar: function () { var o = '', cx = 160, cy = 92, R = 70, pts = function (k) { var s = ''; for (var i = 0; i < 6; i++) { var a = Math.PI / 3 * i - Math.PI / 2, rr = R * k[i]; s += (i ? 'L' : 'M') + (cx + rr * Math.cos(a)).toFixed(1) + ' ' + (cy + rr * Math.sin(a)).toFixed(1); } return s + 'Z'; }; o += p(pts([1, 1, 1, 1, 1, 1]), 'none', G2) + p(pts([.5, .5, .5, .5, .5, .5]), 'none', G1); o += p(pts([.9, .6, .8, .5, .7, .85]), CR) + p(pts([.6, .85, .5, .8, .45, .6]), 'none', INK); return o; },
    slope: function () { var o = l(70, 20, 70, 165, G2, 1.5) + l(250, 20, 250, 165, G2, 1.5); [[40, 70], [90, 50], [110, 140], [140, 100]].forEach(function (v, i) { o += l(70, v[0], 250, v[1], i === 0 ? INK : G2, i === 0 ? 3 : 2) + c(70, v[0], 5, i === 0 ? INK : CR) + c(250, v[1], 5, i === 0 ? INK : CR); }); return o; },
    heatmap: function () { var o = '', sh = [G1, CR, '#8FB1D9', INK]; for (var y = 0; y < 5; y++) for (var x = 0; x < 7; x++) o += r(30 + x * 38, 18 + y * 29, 35, 26, sh[(x * 3 + y * 5 + x * y) % 4]); return o; },
    funnel: function () { var o = ''; [260, 210, 160, 110, 70].forEach(function (w, i) { o += p('M' + (160 - w / 2) + ' ' + (16 + i * 30) + 'h' + w + 'l-' + 22 + ' 26h-' + (w - 44) + 'Z', i === 4 ? INK : CR); }); return o; },
    tree: function () { var o = r(20, 78, 60, 26, INK, 3); [30, 92, 150].forEach(function (y) { o += p('M80 91H105V' + (y + 13) + 'H125', 'none', G2) + r(125, y, 70, 26, CR, 3); [y - 10, y + 16].forEach(function (y2) { o += p('M195 ' + (y + 13) + 'H210V' + (y2 + 8) + 'H225', 'none', G2) + r(225, y2, 75, 16, G1, 2); }); }); return o; },
    matrix: function () { return r(40, 15, 120, 75, G1) + r(162, 15, 120, 75, CR) + r(40, 92, 120, 75, G1) + r(162, 92, 120, 75, G1) + c(220, 50, 10, INK) + c(110, 130, 7, G2) + c(200, 120, 8, G2) + c(90, 55, 6, G2); },
    fishbone: function () { var o = l(30, 92, 260, 92, INK, 3) + r(260, 76, 45, 32, INK, 3); [70, 130, 190].forEach(function (x) { o += l(x, 30, x + 40, 92, G2) + l(x, 154, x + 40, 92, G2) + r(x - 25, 20, 50, 14, CR, 2) + r(x - 25, 150, 50, 14, CR, 2); }); return o; },
    concentric: function () { return c(160, 92, 78, G1) + c(160, 108, 55, CR) + c(160, 124, 30, INK); },
    venn: function () { return '<g opacity=".75">' + c(130, 75, 50, CR) + c(190, 75, 50, G1) + c(160, 120, 50, CR) + '</g>' + c(160, 92, 8, INK); },
    pyramid: function () { var o = ''; [[160, 20, 60], [160, 60, 120], [160, 100, 180], [160, 140, 240]].forEach(function (v, i) { o += p('M' + (v[0] - v[2] / 2 + 20) + ' ' + v[1] + 'h' + (v[2] - 40) + 'l20 36h-' + v[2] + 'Z', i === 0 ? INK : (i % 2 ? CR : G1)); }); return o; },
    cycle: function () { var o = c(160, 92, 55, 'none', G2); for (var i = 0; i < 5; i++) { var a = Math.PI * 2 / 5 * i - Math.PI / 2; o += c(160 + 62 * Math.cos(a), 92 + 62 * Math.sin(a), 18, i ? CR : INK); } return o; },
    hub: function () { var o = ''; for (var i = 0; i < 6; i++) { var a = Math.PI / 3 * i, x = 160 + 100 * Math.cos(a), y = 92 + 62 * Math.sin(a); o += l(160, 92, x, y, G2) + c(x, y, 16, CR); } return o + c(160, 92, 26, INK); },
    donut: function () { return '<g transform="rotate(-90 110 92)"><circle cx="110" cy="92" r="55" fill="none" stroke="' + CR + '" stroke-width="28"/><circle cx="110" cy="92" r="55" fill="none" stroke="' + INK + '" stroke-width="28" stroke-dasharray="120 400"/></g>' + [0, 1, 2, 3].map(function (i) { return r(200, 45 + i * 26, 12, 12, i ? CR : INK) + r(220, 47 + i * 26, 70, 8, G1); }).join(''); },
    timeline: function () { var o = l(20, 92, 300, 92, INK, 2); [50, 110, 170, 230, 285].forEach(function (x, i) { o += c(x, 92, 7, i === 2 ? INK : CR, INK) + r(x - 24, i % 2 ? 108 : 42, 48, 30, G1, 3); }); return o; },
    flow: function () { var o = ''; [0, 1, 2, 3].forEach(function (i) { o += p('M' + (20 + i * 72) + ' 60h58l14 32l-14 32h-58l14-32Z', i === 3 ? INK : CR); }); return o; },
    table: function () { var o = r(20, 18, 280, 24, INK); for (var y = 0; y < 5; y++) { o += r(20, 46 + y * 23, 280, 20, y % 2 ? '#fff' : G1); } return o + r(200, 46 + 23 * 2, 50, 20, CR) + l(110, 18, 110, 160, '#fff', 2); },
    cards: function () { var o = ''; for (var i = 0; i < 6; i++) { var x = 22 + (i % 3) * 96, y = 20 + Math.floor(i / 3) * 76; o += r(x, y, 88, 68, G1, 4) + r(x, y, 88, 14, i ? CR : INK, 4); } return o; },
    text: function () { var o = ''; for (var i = 0; i < 5; i++) { o += c(36, 32 + i * 30, 6, i ? CR : INK) + r(52, 27 + i * 30, 230 - (i % 3) * 40, 10, G1); } return o; },
    /* OKR：上段 Objective・枝分かれのシリーズカード・下段 KR・考察帯（数字・文字は入れない） */
    okr: function () {
      var o = r(70, 8, 180, 44, G1, 4) + r(82, 16, 72, 12, CR, 2) + r(166, 16, 72, 12, INK, 2) + r(82, 32, 156, 14, CR, 2);
      o += l(160, 52, 160, 66, G2, 1.5) + l(40, 66, 280, 66, G2, 1.5);
      [28, 118, 208].forEach(function (x, i) {
        o += l(x + 42, 66, x + 42, 76, G2, 1.5);
        o += r(x, 76, 84, 58, G1, 3) + r(x + 6, 82, 72, 8, i ? CR : INK, 2);
        o += r(x + 6, 94, 72, 8, CR, 2) + r(x + 6, 106, 34, 6, G2, 1) + r(x + 44, 106, 34, 6, G2, 1) + r(x + 6, 116, 72, 10, CR, 2);
      });
      [20, 116, 212].forEach(function (x) { o += r(x, 140, 88, 20, G1, 3); });
      return o + r(20, 164, 280, 12, CR, 2);
    }
  };
  function schematic(pid) {
    var pt = BY[pid], fn = FAM[(pt && pt.family) || 'text'] || FAM.text;
    return '<svg viewBox="0 0 320 180" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Framework見本">' + fn() + '</svg>';
  }

  /* ---------- このページの数字だけで描く（無い値は描かない・数字は作らない） ---------- */
  var FAM_JP = { bars: '棒グラフ', stacked: '積み上げ', waterfall: 'ウォーターフォール', table: '表', slope: '前後比較', heatmap: 'ヒートマップ', tornado: 'トルネード', butterfly: '左右比較', scatter: '散布図', radar: 'レーダー', mekko: 'メッコ', funnel: 'ファネル', donut: 'ドーナツ', tree: 'ツリー', cards: 'カード', flow: '流れ', timeline: 'タイムライン', pyramid: 'ピラミッド', hub: 'ハブ', cycle: '循環', matrix: 'マトリクス', fishbone: '特性要因', concentric: '同心円', venn: 'ベン図', text: 'テキスト' };
  var SHORT = { 'bar-chart-full': '棒グラフ', 'kpi-bar-chart': 'KPIの棒', 'chart-with-callout': '注釈つき棒', 'two-col-list-and-chart': 'リスト＋棒', 'chart-left-text-right': '棒＋説明', 'slope-chart-before-after': '前後比較', 'comparison-table-with-highlight': '強調つき表', 'heatmap-matrix-table': 'ヒートマップ', 'waterfall-bridge-chart': 'ウォーターフォール', 'stacked-bar-100pct': '積み上げ100%', 'tornado-sensitivity-chart': 'トルネード', 'butterfly-comparison-chart': '左右比較', 'feature-metrics-four-cells': '4つの指標', 'three-col-kpi-with-chart': '3列のKPI', 'two-chart-panel': '2つの図', 'headline-three-chart-grid': '3つの図', 'three-kpi-big-number': '大きなKPI', 'goal-kgi-kpi-dashboard': '目標の看板', 'comparison-matrix-table': '比較表', 'comparison-table-with-highlight': '強調つき表', 'status-progress-table': '進捗の表', 'pricing-comparison-table': '料金比較', 'two-col-icon-list-comparison': '対比リスト', 'pricing-plan-cards': 'プラン表' };
  function shortName(pt) { return (pt && (SHORT[pt.id] || FAM_JP[pt.family] || pt.label)) || ''; }

  /* OKR は必ず使う Framework（129 型カタログの外。目標と実績があるときだけおすすめ先頭・社内版のみ） */
  var OKR_ID = 'okr-objective-kr';
  var OKR_PT = { id: OKR_ID, family: 'okr', label: 'OKR', figure: true };
  if (!BY[OKR_ID]) { CAT.patterns = [OKR_PT].concat(CAT.patterns); BY[OKR_ID] = OKR_PT; }
  SHORT[OKR_ID] = 'OKR';
  FAM_JP.okr = 'OKR';

  function parseCell(raw) {
    var raw0 = String(raw == null ? '' : raw).trim();
    var s = raw0.replace(/\s+/g, '').replace(/,/g, '').replace(/[¥￥円]/g, '');
    if (!s || s === '—' || s === '–' || s === '−' || s === '-' || s === '‐') return { v: null, raw: raw0 || '—', pct: false };
    s = s.replace(/^[▲△]/, '-');
    var pct = /[%％]$/.test(s); if (pct) s = s.replace(/[%％]$/, '');
    var mul = 1, um = s.match(/^([+-]?[0-9]+(?:\.[0-9]+)?)(億|万|千)?(?:円|件|人|回|個|本|pt)?$/);
    if (!um) return { v: null, raw: raw0, pct: false };
    if (um[2] === '億') mul = 10000; else if (um[2] === '千') mul = 0.1;   // 値は「万」単位にそろえる（ラベルは元の表記のまま）
    s = um[1];
    var n = parseFloat(s) * (um[2] ? mul : 1);
    return { v: isFinite(n) ? n : null, raw: raw0, pct: pct };
  }
  function extractData(el) {
    if (!el) return { cats: [], series: [], raws: [], ok: false };
    var slide = el.closest('section.slide') || el;
    var table = (el.tagName === 'TABLE' ? el : el.querySelector('table')) || slide.querySelector('table.sk, table');
    if (!table) return { cats: [], series: [], raws: [], ok: false };
    var rows = [].slice.call(table.querySelectorAll('tr'));
    if (rows.length < 2) return { cats: [], series: [], raws: [], ok: false };
    var heads = [].slice.call(rows[0].querySelectorAll('th,td')).map(function (c) { return c.textContent.trim(); });
    var cats = [], cidx = [];
    heads.forEach(function (h, i) {
      if (i === 0) return;
      if (/合計|^計$|total/i.test(h)) return;
      cats.push(h); cidx.push(i);
    });
    var series = [], rawRows = [];
    rows.slice(1).forEach(function (r) {
      var cells = [].slice.call(r.querySelectorAll('th,td')).map(function (c) { return c.textContent.trim(); });
      if (!cells.length) return;
      rawRows.push(cells);
      if (/^(合計|計|総計|total)$/i.test(cells[0])) return;   // 合計の行は描かない（表で描くときは残す）
      var parsed = cidx.map(function (i) { return parseCell(cells[i] || ''); });
      if (!parsed.some(function (p) { return p.v != null; })) return;
      var pct = parsed.filter(function (p) { return p.v != null; }).every(function (p) { return p.pct; });
      series.push({ name: cells[0], vals: parsed.map(function (p) { return p.v; }), raws: parsed.map(function (p) { return p.raw; }), pct: pct });
    });
    var raw = { heads: heads, rows: rawRows };
    /* 行が多い表（シリーズ別・日別など）は、行を横軸・列を系列にする */
    if (series.length > cats.length && series.length >= 2) {
      var tc = series.map(function (s) { return s.name; });
      var ts = cats.map(function (c, j) {
        var vals = series.map(function (s) { return s.vals[j]; }), raws = series.map(function (s) { return s.raws[j]; });
        var pv = series.map(function (s) { return parseCell(s.raws[j]); }).filter(function (p) { return p.v != null; });
        return { name: c, vals: vals, raws: raws, pct: pv.length > 0 && pv.every(function (p) { return p.pct; }) };
      }).filter(function (s) { return s.vals.some(function (v) { return v != null; }); });
      return { cats: tc, series: ts, raw: raw, transposed: true, ok: tc.length > 0 && ts.length > 0 };
    }
    return { cats: cats, series: series, raw: raw, ok: cats.length > 0 && series.length > 0 };
  }
  function seriesForDraw(data, preferAmt) {
    if (!data || !data.series) return [];
    var amt = data.series.filter(function (s) { return !s.pct && s.vals.some(function (v) { return v != null; }); });
    var pct = data.series.filter(function (s) { return s.pct && s.vals.some(function (v) { return v != null; }); });
    if (preferAmt !== false && amt.length) return amt;
    return amt.length ? amt : pct;
  }

  function written(raw) {
    var s = String(raw == null ? '' : raw).replace(/\s+/g, ' ').trim();
    return !!(s && s !== '—' && s !== '–' && s !== '−' && s !== '-' && s !== '‐');
  }
  function okrTxt(n) { return (n && String(n.textContent || '').replace(/\s+/g, ' ').trim()) || ''; }
  function isTargetLbl(s) { return /目標|必達|適正/.test(String(s || '')); }
  function isActualLbl(s) { return /実績|着地/.test(String(s || '')); }
  function parseOkrBox(el) {
    if (!el) return null;
    var lblEl = el.querySelector('.lbl'), bEl = el.querySelector('b'), s2El = el.querySelector('.s2');
    var lbl = okrTxt(lblEl), val = okrTxt(bEl), s2 = okrTxt(s2El);
    var rest = '', judge = '';
    function walk(n) {
      if (n === lblEl || n === bEl || n === s2El) return;
      if (n.nodeType === 3) { rest += n.nodeValue; return; }
      if (n.nodeType !== 1) return;
      var t = okrTxt(n);
      if (/^[○△×]$/.test(t)) { judge = t; return; }
      [].slice.call(n.childNodes).forEach(walk);
    }
    [].slice.call(el.childNodes).forEach(walk);
    rest = rest.replace(/\s+/g, ' ').trim();
    return { lbl: lbl, val: val, rest: rest, judge: judge, s2: s2, mark: !!(el.classList && el.classList.contains('mk')) };
  }
  function boxHasTarget(b) { return !!(b && isTargetLbl(b.lbl) && (written(b.val) || written(b.rest))); }
  function boxHasActual(b) { return !!(b && isActualLbl(b.lbl) && (written(b.val) || written(b.rest))); }
  function parseOkrNode(nd) {
    if (!nd) return null;
    var nmEl = nd.querySelector(':scope > .nm') || nd.querySelector('.nm');
    var img = nmEl && nmEl.querySelector('img');
    var name = okrTxt(nmEl).replace(/\s+/g, ' ').trim();
    var boxes = [].slice.call(nd.querySelectorAll(':scope > .box')).map(parseOkrBox).filter(Boolean);
    var trendEl = nd.querySelector(':scope > .trend');
    return {
      name: name,
      img: img ? { src: img.getAttribute('src') || '', alt: img.getAttribute('alt') || name } : null,
      boxes: boxes,
      trend: trendEl ? trendEl.innerHTML : '',
      hasTarget: boxes.some(boxHasTarget),
      hasActual: boxes.some(boxHasActual)
    };
  }
  function parseKr(el) {
    if (!el) return null;
    var name = okrTxt(el.querySelector('.kr-n'));
    var vEl = el.querySelector('.kr-v');
    var small = vEl && vEl.querySelector('small');
    var value = '';
    if (vEl) {
      var copy = vEl.cloneNode(true);
      if (copy.querySelector('small')) copy.querySelector('small').remove();
      value = okrTxt(copy);
    }
    var meta = small ? okrTxt(small) : '';
    var judge = '';
    var jm = meta.match(/[○△×]/);
    if (jm) judge = jm[0];
    return { name: name, value: value, meta: meta, judge: judge, period: okrTxt(el.querySelector('.kr-s')) };
  }
  function findCol(heads, re) {
    for (var i = 0; i < heads.length; i++) if (re.test(String(heads[i] || '').replace(/\s+/g, ''))) return i;
    return -1;
  }
  function rowToBoxes(cells, idx) {
    var boxes = [];
    function add(i, lbl, mark) {
      if (i < 0 || !written(cells[i])) return;
      boxes.push({ lbl: lbl, val: String(cells[i]).trim(), rest: '', judge: '', s2: '', mark: !!mark });
    }
    add(idx.target, '目標', false);
    if (idx.tekisei >= 0 && idx.tekisei !== idx.target) add(idx.tekisei, '適正', false);
    if (idx.hittatsu >= 0 && idx.hittatsu !== idx.target) add(idx.hittatsu, '必達', false);
    if (idx.actual >= 0 && written(cells[idx.actual])) {
      var rest = '', judge = '', s2 = '';
      if (idx.rate >= 0 && written(cells[idx.rate])) rest += (rest ? '・' : '') + String(cells[idx.rate]).trim();
      if (idx.yoy >= 0 && written(cells[idx.yoy])) rest += (rest ? '・' : '') + 'YoY' + String(cells[idx.yoy]).trim();
      if (idx.judge >= 0 && written(cells[idx.judge])) {
        var j = String(cells[idx.judge]).trim();
        var m = j.match(/[○△×]/);
        if (m) judge = m[0];
        else rest += (rest ? '・' : '') + j;
      }
      if (rest) rest = '（' + rest + '）';
      boxes.push({ lbl: '実績', val: String(cells[idx.actual]).trim(), rest: rest, judge: judge, s2: s2, mark: true });
    }
    add(idx.ad, '広告費', false);
    if (idx.adSales >= 0 && written(cells[idx.adSales])) {
      var s2b = (idx.roas >= 0 && written(cells[idx.roas])) ? ('ROAS' + String(cells[idx.roas]).trim()) : '';
      boxes.push({ lbl: '広告経由売上', val: String(cells[idx.adSales]).trim(), rest: '', judge: '', s2: s2b, mark: false });
    }
    return boxes;
  }
  function trendFromRow(cells, heads, monthIdx) {
    if (!monthIdx.length) return '';
    var parts = monthIdx.map(function (it) { return written(cells[it.i]) ? String(cells[it.i]).trim() : ''; }).filter(Boolean);
    if (parts.length < 2) return '';
    var labs = monthIdx.map(function (it) { return it.lab; }).filter(Boolean);
    return '達成率 ' + labs.join('→') + ' <b>' + parts.join('→') + '</b>';
  }
  function extractOkrFromTable(el) {
    var slide = (el && (el.closest && el.closest('section.slide'))) || el;
    var table = (el && el.tagName === 'TABLE' ? el : (el && el.querySelector && el.querySelector('table'))) || (slide && slide.querySelector && slide.querySelector('table.sk, table'));
    if (!table) return null;
    var rows = [].slice.call(table.querySelectorAll('tr'));
    if (rows.length < 2) return null;
    var heads = [].slice.call(rows[0].querySelectorAll('th,td')).map(function (c) { return c.textContent.trim(); });
    var idx = {
      target: findCol(heads, /^(目標|適正目標)$|目標/),
      tekisei: findCol(heads, /適正/),
      hittatsu: findCol(heads, /必達/),
      actual: findCol(heads, /実績|着地/),
      yoy: findCol(heads, /YoY|前年比|前年/),
      rate: findCol(heads, /達成率/),
      judge: findCol(heads, /判定|○|評価/),
      ad: findCol(heads, /広告費/),
      adSales: findCol(heads, /広告経由/),
      roas: findCol(heads, /ROAS/)
    };
    if (idx.target < 0 || idx.actual < 0) return null;
    var monthIdx = [];
    heads.forEach(function (h, i) {
      var m = String(h || '').match(/([1-9]|1[0-2])\s*月/);
      if (m) monthIdx.push({ i: i, lab: m[1] + '月' });
    });
    var obj = null, series = [];
    rows.slice(1).forEach(function (r) {
      var cells = [].slice.call(r.querySelectorAll('th,td')).map(function (c) { return c.textContent.trim(); });
      if (!cells.length) return;
      var boxes = rowToBoxes(cells, idx);
      var node = { name: cells[0] || '', img: null, boxes: boxes, trend: trendFromRow(cells, heads, monthIdx), hasTarget: boxes.some(boxHasTarget), hasActual: boxes.some(boxHasActual) };
      if (!node.hasTarget && !node.hasActual) return;
      if (/^(合計|計|総計|全体|total|objective)$/i.test(cells[0]) || /objective/i.test(cells[0])) obj = node;
      else series.push(node);
    });
    return { obj: obj, series: series };
  }
  function extractOkr(el) {
    var slide = (el && el.closest && el.closest('section.slide')) || el || null;
    var root = null;
    if (el && el.classList && el.classList.contains('okr')) root = el;
    else if (el && el.querySelector) root = el.querySelector('.okr');
    if (!root && slide && slide.querySelector) root = slide.querySelector('.okr');
    var obj = null, series = [], krs = [], insight = null, krHead = '', note = '';
    var lowerOutside = false;
    if (root) {
      var big = root.querySelector('.nd.big');
      if (big) obj = parseOkrNode(big);
      root.querySelectorAll('.nd.cat, .nd.mid, .nd.s').forEach(function (nd) {
        if (nd.classList.contains('big')) return;
        var n = parseOkrNode(nd);
        if (n && (n.hasTarget || n.hasActual || n.boxes.length)) series.push(n);
      });
    }
    if (slide) {
      var krBand = slide.querySelector('.kr-band');
      if (krBand && (!root || !root.contains(krBand))) lowerOutside = true;
      if (krBand) {
        var hh = slide.querySelector('.kr-band-h');
        if (hh) krHead = okrTxt(hh);
        krs = [].slice.call(krBand.querySelectorAll('.kr')).map(parseKr).filter(function (k) { return k && (k.name || k.value); });
      }
      var ins = slide.querySelector('.okr-insight');
      if (ins) {
        if (!root || !root.contains(ins)) lowerOutside = true;
        insight = { lbl: okrTxt(ins.querySelector('.ins-lbl')), txtHtml: (ins.querySelector('.ins-txt') && ins.querySelector('.ins-txt').innerHTML) || '' };
      }
      var tn = slide.querySelector('.t-note');
      if (tn && (!root || !root.contains(tn))) note = tn.innerHTML;
    }
    if (!obj || !(obj.hasTarget && obj.hasActual) || !series.length) {
      var fromTbl = extractOkrFromTable(el);
      if (fromTbl) {
        if (!obj) obj = fromTbl.obj;
        if (!series.length) series = fromTbl.series;
      }
    }
    var hasPair = (obj && obj.hasTarget && obj.hasActual) || series.some(function (s) { return s.hasTarget && s.hasActual; });
    return { ok: !!hasPair, obj: obj, series: series, krs: krs, insight: insight, krHead: krHead, note: note, lowerOutside: lowerOutside };
  }
  function canDrawOkr(el) {
    var o = extractOkr(el);
    return !!(o && o.ok);
  }
  function drawOkrBox(b) {
    if (!b) return '';
    var o = '<div class="box' + (b.mark ? ' mk' : '') + '"' + (b.lbl === '広告経由売上' ? ' style="height:19px;margin-top:1px;padding:1px 9px;"' : '') + '>';
    if (b.lbl) o += '<span class="lbl"' + (b.lbl === '広告経由売上' ? ' style="width:auto;margin-right:5px"' : '') + '>' + esc(b.lbl) + '</span>';
    if (b.val) o += '<b>' + esc(b.val) + '</b>';
    if (b.rest) o += esc(b.rest);
    if (b.s2) o += '<span class="s2">' + esc(b.s2) + '</span>';
    if (b.judge) o += ' <span style="font-weight:700;">' + esc(b.judge) + '</span>';
    return o + '</div>';
  }
  function drawOkrNode(n, kind) {
    if (!n) return '';
    var o = '<div class="nd ' + (kind || 'cat') + '"><span class="nm">';
    if (n.img && n.img.src) o += '<img src="' + esc(n.img.src) + '" alt="' + esc(n.img.alt || '') + '" style="display:block; height:34px; width:auto; margin:0 auto 3px; border-radius:3px;">';
    o += esc(n.name) + '</span>';
    (n.boxes || []).forEach(function (b) { o += drawOkrBox(b); });
    if (n.trend) {
      if (/<b>/i.test(n.trend)) o += '<div class="trend">' + n.trend + '</div>';
      else o += '<div class="trend">' + esc(n.trend) + '</div>';
    }
    return o + '</div>';
  }
  function drawOkr(data, el) {
    if (!data || !data.ok) return '';
    var o = '<div class="okr ci-okr-live">';
    o += '<ul><li>';
    if (data.obj) o += drawOkrNode(data.obj, 'big');
    if (data.series && data.series.length) {
      o += '<ul><li class="sgrp"><div class="sgrp-row">';
      data.series.forEach(function (s) { o += drawOkrNode(s, 'cat'); });
      o += '</div></li></ul>';
    }
    o += '</li></ul>';
    if (!data.lowerOutside) {
      if (data.krHead) o += '<div class="kr-band-h">' + esc(data.krHead) + '</div>';
      if (data.krs && data.krs.length) {
        o += '<div class="kr-band">';
        data.krs.forEach(function (k) {
          o += '<div class="kr"><div class="kr-n">' + esc(k.name) + '</div>';
          o += '<div class="kr-v">' + esc(k.value) + (k.meta ? '<small>' + esc(k.meta) + '</small>' : '') + '</div>';
          if (k.period) o += '<div class="kr-s">' + esc(k.period) + '</div>';
          o += '</div>';
        });
        o += '</div>';
      }
      if (data.insight && (data.insight.lbl || data.insight.txtHtml)) {
        o += '<div class="okr-insight">';
        if (data.insight.lbl) o += '<span class="ins-lbl">' + esc(data.insight.lbl) + '</span>';
        if (data.insight.txtHtml) o += '<span class="ins-txt">' + data.insight.txtHtml + '</span>';
        o += '</div>';
      }
    }
    return o + '</div>';
  }

  function canDraw(pt, data, el) {
    if (pt && (pt.id === OKR_ID || pt.family === 'okr')) return canDrawOkr(el);
    if (!data || !data.ok) return false;
    var fam = (pt && pt.family) || '';
    if (fam === 'bars') return seriesForDraw(data).length >= 1;
    if (fam === 'table' || fam === 'heatmap') return data.series.some(function (s) { return s.vals.some(function (v) { return v != null; }); });
    if (fam === 'slope') return seriesForDraw(data).some(function (s) { return s.vals.filter(function (v) { return v != null; }).length >= 2; });
    return false;
  }
  function fmtTick(v) { return Math.abs(v) >= 1000 ? Math.round(v).toLocaleString('en-US') : String(v); }
  var TK = { ink: 'var(--ink)', cry: 'var(--crystal)', c55: 'var(--crystal-55)', c25: 'var(--crystal-25)', i60: 'var(--ink-60)', i14: 'var(--ink-14)', i20: 'var(--ink-20)', i85: 'var(--ink-85)' };
  var SERC = [TK.ink, TK.cry, TK.c55, TK.i60];
  function figSize(el) {
    var w = 1000, h = 184;
    if (!el) return { w: w, h: h };
    var svg = (el.tagName && el.tagName.toLowerCase() === 'svg') ? el : el.querySelector('svg');
    if (svg && svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width) {
      return { w: svg.viewBox.baseVal.width, h: svg.viewBox.baseVal.height };
    }
    var q = el.getBoundingClientRect();
    if (q.width > 40 && q.height > 40) return { w: Math.max(640, Math.round(q.width)), h: Math.max(140, Math.round(q.height)) };
    return { w: w, h: h };
  }
  function svgOpen(w, h, label) {
    return '<svg viewBox="0 0 ' + w + ' ' + h + '" width="100%" height="100%" style="display:block" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="' + esc(label || '') + '">';
  }
  function tx(x, y, s, o) {
    o = o || {};
    var fs = Math.max(10, o.size || 11);
    return '<text x="' + (+x).toFixed(1) + '" y="' + (+y).toFixed(1) + '" font-size="' + fs + '" fill="' + (o.fill || TK.ink) + '" text-anchor="' + (o.anchor || 'start') + '"' +
      (o.weight ? ' font-weight="700"' : '') + (o.en ? ' style="font-family:var(--serif-en)"' : '') + '>' + esc(s) + '</text>';
  }
  function fmtAxis(v, pct) {
    if (pct) return (Math.abs(v) >= 10 ? String(Math.round(v)) : String(Math.round(v * 10) / 10)) + '%';
    if (Math.abs(v) >= 1e6) return '¥' + Math.round(v / 1e6) + 'M';
    if (Math.abs(v) >= 1000) return Math.round(v).toLocaleString('en-US');
    return String(Math.round(v * 10) / 10);
  }
  function lastRaw(s) {
    for (var i = s.raws.length - 1; i >= 0; i--) if (s.vals[i] != null) return { raw: s.raws[i], i: i };
    return { raw: '—', i: -1 };
  }
  function firstLast(s) {
    var a = -1, b = -1, i;
    for (i = 0; i < s.vals.length; i++) if (s.vals[i] != null) { if (a < 0) a = i; b = i; }
    return a >= 0 && b > a ? { a: a, b: b } : null;
  }

  function drawTable(data) {
    if (data.raw && data.raw.rows.length) {
      return '<div class="ci-chart-live-table"><table class="sk"><thead><tr>' + data.raw.heads.map(function (c, i) { return '<th' + (i ? '' : ' class="l"') + '>' + esc(c) + '</th>'; }).join('') + '</tr></thead><tbody>' +
        data.raw.rows.map(function (r) { return '<tr>' + r.map(function (c, i) { return '<td' + (i ? (parseCell(c).v == null ? ' class="na"' : '') : ' class="l"') + '>' + esc(c) + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>';
    }
    var th = data.cats.map(function (c) { return '<th>' + esc(c) + '</th>'; }).join('');
    var body = data.series.map(function (s) {
      return '<tr><td class="l">' + esc(s.name) + '</td>' + s.raws.map(function (r, i) {
        return '<td' + (s.vals[i] == null ? ' class="na"' : '') + '>' + esc(r) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    return '<div class="ci-chart-live-table"><table class="sk"><thead><tr><th class="l"></th>' + th + '</tr></thead><tbody>' + body + '</tbody></table></div>';
  }
  function drawHeatmap(data, w, h) {
    var o = svgOpen(w, h, 'ヒートマップ'), padL = Math.max(90, w * 0.14), padT = 28, padB = 16, padR = 10;
    var cw = (w - padL - padR) / data.cats.length, rh = (h - padT - padB) / data.series.length;
    data.cats.forEach(function (c, i) { o += tx(padL + cw * (i + 0.5), padT - 8, c, { anchor: 'middle', size: 10, fill: TK.i60 }); });
    data.series.forEach(function (s, y) {
      o += tx(padL - 6, padT + rh * (y + 0.65), s.name, { anchor: 'end', size: 10 });
      var nums = s.vals.filter(function (v) { return v != null; });
      var mn = nums.length ? Math.min.apply(null, nums) : 0, mx = nums.length ? Math.max.apply(null, nums) : 1;
      s.vals.forEach(function (v, x) {
        var xx = padL + cw * x, yy = padT + rh * y;
        if (v == null) {
          o += '<rect x="' + xx.toFixed(1) + '" y="' + yy.toFixed(1) + '" width="' + Math.max(cw - 2, 1).toFixed(1) + '" height="' + Math.max(rh - 2, 1).toFixed(1) + '" fill="none" stroke="' + TK.i20 + '" stroke-width="0.6" stroke-dasharray="2 2"/>';
          o += tx(xx + cw / 2, yy + rh * 0.65, s.raws[x] || '—', { anchor: 'middle', size: 10, fill: TK.i20 });
          return;
        }
        var k = (mx === mn) ? 0.4 : (v - mn) / (mx - mn);
        o += '<rect x="' + xx.toFixed(1) + '" y="' + yy.toFixed(1) + '" width="' + Math.max(cw - 2, 1).toFixed(1) + '" height="' + Math.max(rh - 2, 1).toFixed(1) + '" fill="' + TK.cry + '" fill-opacity="' + (0.18 + 0.82 * k).toFixed(2) + '" stroke="' + TK.i14 + '" stroke-width="0.4"/>';
        o += tx(xx + cw / 2, yy + rh * 0.65, s.raws[x], { anchor: 'middle', size: 10, en: true, weight: k > 0.7 });
      });
    });
    return o + '</svg>';
  }
  function drawSlope(data, w, h) {
    var ser = seriesForDraw(data).filter(function (s) { return firstLast(s); });
    var o = svgOpen(w, h, '前後比較'), padL = Math.max(120, w * 0.16), padR = Math.max(110, w * 0.14), padT = 20, padB = 28;
    var nums = []; ser.forEach(function (s) { var fl = firstLast(s); nums.push(s.vals[fl.a], s.vals[fl.b]); });
    var mn = nums.length ? Math.min.apply(null, nums) : 0, mx = nums.length ? Math.max.apply(null, nums) : 1;
    if (mn === mx) mn = mn > 0 ? 0 : mn - 1;
    var span = mx - mn; mn -= span * 0.08; mx += span * 0.12;
    var n = Math.max(data.cats.length, 2);
    function X(i) { return padL + (w - padL - padR) * i / (n - 1); }
    function Y(v) { return padT + (h - padT - padB) * (1 - (v - mn) / (mx - mn)); }
    var marks = {};
    ser.forEach(function (s) { var fl = firstLast(s); marks[fl.a] = 1; marks[fl.b] = 1; });
    Object.keys(marks).map(Number).sort(function (a,b){return a-b;}).forEach(function (i) {
      o += '<line x1="' + X(i).toFixed(1) + '" y1="' + padT + '" x2="' + X(i).toFixed(1) + '" y2="' + (h - padB) + '" stroke="' + TK.i20 + '" stroke-width="0.6"/>';
      o += tx(X(i), h - padB + 16, data.cats[i] || '', { anchor: 'middle', size: 10, fill: TK.i60 });
    });
    function spread(ys, gap) {
      var order = ys.map(function (y, i) { return i; }).sort(function (a, b) { return ys[a] - ys[b]; }), out = ys.slice();
      for (var k = 1; k < order.length; k++) { var a = order[k - 1], b = order[k]; if (out[b] - out[a] < gap) out[b] = out[a] + gap; }
      return out;
    }
    var ysL = spread(ser.map(function (s) { return Y(s.vals[firstLast(s).a]); }), 13);
    var ysR = spread(ser.map(function (s) { return Y(s.vals[firstLast(s).b]); }), 13);
    ser.forEach(function (s, i) {
      var fl = firstLast(s), col = i === 0 ? TK.ink : SERC[i % SERC.length], sw = i === 0 ? 2.4 : 1.6;
      var x1 = X(fl.a), x2 = X(fl.b), y1 = Y(s.vals[fl.a]), y2 = Y(s.vals[fl.b]);
      o += '<line x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="' + col + '" stroke-width="' + sw + '"/>';
      o += '<circle cx="' + x1.toFixed(1) + '" cy="' + y1.toFixed(1) + '" r="3.4" fill="' + col + '"/>';
      o += '<circle cx="' + x2.toFixed(1) + '" cy="' + y2.toFixed(1) + '" r="3.4" fill="' + col + '"/>';
      o += tx(padL - 8, ysL[i] + 4, s.name, { anchor: 'end', size: 10, weight: i === 0 });
      o += tx(x2 + 8, ysR[i] + 4, s.raws[fl.b], { size: 10, en: true, weight: i === 0 });
    });
    return o + '</svg>';
  }
  function drawBars(data, w, h, opts) {
    opts = opts || {};
    var ser = seriesForDraw(data);
    var left = opts.textLeft ? Math.round(w * 0.28) : 0;
    var o = '', plotW = w - left, plotH = h;
    if (opts.textLeft) {
      o += '<div class="ci-chart-split" style="display:flex;width:100%;height:100%;align-items:stretch">';
      o += '<div class="ci-chart-side" style="width:' + left + 'px;flex:none;padding:4px 10px 4px 0;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;gap:6px">';
      ser.forEach(function (s, i) {
        var lr = lastRaw(s);
        o += '<div style="display:flex;align-items:baseline;gap:8px;border-bottom:1px solid ' + TK.i14 + ';padding:3px 0">';
        o += '<span style="width:10px;height:10px;background:' + SERC[i % SERC.length] + ';flex:none;display:inline-block"></span>';
        o += '<span style="font-size:12px;font-weight:700;color:var(--ink)">' + esc(s.name) + '</span>';
        o += '<span style="margin-left:auto;font-size:12px;font-family:var(--serif-en);color:var(--ink)">' + esc(lr.raw) + '</span></div>';
      });
      o += '</div>';
    }
    var padL = opts.textLeft ? 36 : Math.max(48, plotW * 0.06), padR = 12, padT = 22, padB = ser.length > 1 ? 40 : 28;
    var svgW = opts.textLeft ? plotW : w, svgH = h;
    var svg = svgOpen(svgW, svgH, opts.label || '棒グラフ');
    var n = data.cats.length, g = ser.length, slot = (svgW - padL - padR) / Math.max(n, 1);
    var nums = []; ser.forEach(function (s) { s.vals.forEach(function (v) { if (v != null) nums.push(v); }); });
    var mx = nums.length ? Math.max.apply(null, nums) : 1; if (mx <= 0) mx = 1; mx *= 1.12;
    var pct = ser.every(function (s) { return s.pct; });
    function Yb(v) { return padT + (svgH - padT - padB) * (1 - v / mx); }
    [0, 0.5, 1].forEach(function (k) {
      var v = mx * k, y = Yb(v);
      svg += '<line x1="' + padL + '" y1="' + y.toFixed(1) + '" x2="' + (svgW - padR) + '" y2="' + y.toFixed(1) + '" stroke="' + TK.i14 + '" stroke-width="0.6"/>';
      svg += tx(padL - 4, y + 4, fmtAxis(v, pct), { anchor: 'end', size: 10, fill: TK.i60, en: true });
    });
    data.cats.forEach(function (c, i) {
      ser.forEach(function (s, k) {
        var v = s.vals[i]; if (v == null) return;
        var bw = Math.max(slot * 0.7 / g, 2), x = padL + slot * i + slot * 0.15 + bw * k;
        var y = Yb(v), hh = Math.max(Yb(0) - y, 0.8);
        svg += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + hh.toFixed(1) + '" fill="' + SERC[k % SERC.length] + '"/>';
      });
      if (n <= 16) svg += tx(padL + slot * (i + 0.5), svgH - padB + 14, c, { anchor: 'middle', size: 10, fill: TK.i60 });
    });
    if (ser.length && !opts.textLeft) {
      ser.forEach(function (s, k) {
        var lx = padL + k * Math.min(160, (svgW - padL) / ser.length);
        svg += '<rect x="' + lx + '" y="' + (svgH - 14) + '" width="10" height="10" fill="' + SERC[k % SERC.length] + '"/>';
        svg += tx(lx + 14, svgH - 5, s.name, { size: 10 });
      });
    }
    svg += '</svg>';
    if (opts.textLeft) return o + '<div style="flex:1;min-width:0;height:100%">' + svg + '</div></div>';
    return svg;
  }
  function dataDraw(pid, data, el) {
    var pt = BY[pid], fam = (pt && pt.family) || '', sz = figSize(el), w = sz.w, h = sz.h;
    if (fam === 'okr' || pid === OKR_ID) {
      var okr = extractOkr(el);
      return (okr && okr.ok) ? drawOkr(okr, el) : '';
    }
    if (fam === 'table') return drawTable(data);
    if (fam === 'heatmap') return drawHeatmap(data, w, h);
    if (fam === 'slope') return drawSlope(data, w, h);
    return drawBars(data, w, h, { textLeft: pid === 'chart-left-text-right', label: shortName(pt) });
  }

  function figMarkup(id, pid) {
    var el = D.querySelector('[data-fp-fig="' + id + '"]');
    var data = extractData(el);
    if (canDraw(BY[pid], data, el)) return dataDraw(pid, data, el);
    return '';   // 数字で描けない型は描かない（見本の絵で置き換えない）
  }

  function recSets(f) {
    var el = D.querySelector('[data-fp-fig="' + (typeof f === 'string' ? f : curId) + '"]');
    var data = extractData(el);
    var figF = (typeof f === 'string') ? fig(f) : f;
    var rec = (CAT.recommend[figF.kind] || []).map(function (i) { return BY[i]; }).filter(Boolean);
    var out = [], seen = {};
    function add(pt) { if (pt && pt.figure && !seen[pt.id]) { seen[pt.id] = 1; out.push(pt); } }
    rec.filter(function (pt) { return canDraw(pt, data, el); }).forEach(add);
    CAT.patterns.filter(function (pt) { return pt.figure && canDraw(pt, data, el); }).forEach(add);
    if (canDrawOkr(el)) {
      out = [OKR_PT].concat(out.filter(function (p) { return p.id !== OKR_ID; }));
    }
    var top = out.slice(0, 8);
    var others = out.slice(8);   // 「ほかの型を見る」も数字で描ける型だけ（見本だけの型は出さない）
    return { top: top, others: others, data: data };
  }

  /* ---------- 層・ボタン ---------- */
  var layer = D.createElement('div'); layer.id = 'ci-fp-layer'; D.body.appendChild(layer);
  var figs = [].slice.call(D.querySelectorAll('[data-fp-fig]'));
  var chips = {}, frames = {}, previews = {};
  figs.forEach(function (el) {
    var id = el.getAttribute('data-fp-fig');
    var b = D.createElement('button'); b.type = 'button'; b.className = 'ci-fp-chip'; b.setAttribute('aria-expanded', 'false');
    var multi = D.querySelectorAll('[data-fp-page="' + el.getAttribute('data-fp-page') + '"]').length > 1;
    b.innerHTML = 'Framework' + (multi ? ' ' + id.replace(/^.*-/, '') : '') + '<span class="who"></span>▾<span class="n"></span>'; b.title = '図 ' + id + ' の Framework を選ぶ（枠が出ている図）';
    b.setAttribute('aria-label', b.title);
    b.addEventListener('click', function (e) { e.stopPropagation(); open(id); });
    b.addEventListener('mouseenter', function () { frames[id].classList.add('on'); });
    b.addEventListener('mouseleave', function () { if (curId !== id) frames[id].classList.remove('on'); });
    var fr = D.createElement('div'); fr.className = 'ci-fp-frame';
    layer.appendChild(fr); layer.appendChild(b); chips[id] = b; frames[id] = fr;
  });
  var ORIG = {};
  figs.forEach(function (el) { ORIG[el.getAttribute('data-fp-fig')] = el.innerHTML; });
  if (!S.inserts) S.inserts = [];
  if (!S.insUndo) S.insUndo = [];
  /* 座標は viewport（getBoundingClientRect のまま）。#ci-fp-layer は position:fixed。
     発表モード（html.ci-present・スライドに transform:scale）でも、scrollY を足すと画面外へ飛ぶため足さない。 */
  function rectOf(el) { var q = el.getBoundingClientRect(); return { x: q.left, y: q.top, w: q.width, h: q.height }; }
  function slideVisible(sl) {
    if (!sl) return false;
    if (H.classList.contains('ci-overview')) return false;
    if (H.classList.contains('ci-present') && !sl.classList.contains('ci-cur')) return false;
    var cs = getComputedStyle(sl);
    if (cs.display === 'none' || cs.visibility === 'hidden') return false;
    var r = sl.getBoundingClientRect();
    return r.width > 1 && r.height > 1 && r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth;
  }
  var placeTeBtns = function () {};
  var RAIL = 160, railPadApplied = -1, placing = false;
  function ensureRail() {
    if (H.classList.contains('ci-fp-hidden') || H.classList.contains('ci-fp-static') || H.classList.contains('ci-overview')) {
      H.classList.remove('ci-fp-rail'); H.style.removeProperty('--ci-fp-rail');
      if (D.body && railPadApplied) { D.body.style.paddingRight = ''; railPadApplied = 0; }
      return false;
    }
    if (H.classList.contains('ci-present')) {
      if (D.body && railPadApplied) { D.body.style.paddingRight = ''; railPadApplied = 0; }
      var s0 = D.querySelector('section.slide');
      var sw = (s0 && s0.offsetWidth) || 1122.5, sh = (s0 && s0.offsetHeight) || 793.7;
      var k = Math.min((innerWidth - RAIL) / sw, innerHeight / sh) * 0.98;
      if (!(k > 0) || !isFinite(k)) k = 1;
      k = Math.round(k * 10000) / 10000;
      var changed = false, ks = String(k), rs = RAIL + 'px';
      if (H.style.getPropertyValue('--ci-fit') !== ks) { H.style.setProperty('--ci-fit', ks); changed = true; }
      if (H.style.getPropertyValue('--ci-fp-rail') !== rs) { H.style.setProperty('--ci-fp-rail', rs); changed = true; }
      if (!H.classList.contains('ci-fp-rail')) { H.classList.add('ci-fp-rail'); changed = true; }
      return changed;
    }
    H.classList.remove('ci-fp-rail'); H.style.removeProperty('--ci-fp-rail');
    var s = D.querySelector('section.slide'); if (!s || !D.body) return false;
    /* 左右余白は現在の padding に依存させない（padding の付け外しでスライドが左右に跳ね、撮影もずれる） */
    var sw = s.offsetWidth, side = (innerWidth - sw) / 2;
    var want = (side >= RAIL + 8) ? 0 : RAIL;
    if (want === railPadApplied) return false;
    D.body.style.paddingRight = want ? (want + 'px') : '';
    railPadApplied = want;
    return true;
  }
  function railX(sq, bw) {
    var gap = 8, x = sq.x + sq.w + gap;
    x = Math.min(x, innerWidth - bw - 6);
    if (x + 1 < sq.x + sq.w) x = innerWidth - bw - 6;  // 重なるなら画面右端へ
    if (x < sq.x + sq.w + 4) x = sq.x + sq.w + 4;
    return x;
  }
  function place() {
    if (placing) return;
    if (ensureRail()) { requestAnimationFrame(function () { place(); }); return; }
    placing = true;
    try { placeNow(); } finally { placing = false; }
  }
  function placeNow() {
    // Framework チップはスライドの右外・図の下端の高さ。余白が無いときは画面右端の列（スライドには重ねない）
    var used = [];
    figs.forEach(function (el) {
      var id = el.getAttribute('data-fp-fig'), q = rectOf(el), b = chips[id], fr = frames[id];
      var sl = el.closest('section.slide') || el.closest('section') || el, sq = rectOf(sl);
      var vis = slideVisible(sl) && q.w > 1 && q.h > 1;
      b.style.display = vis ? '' : 'none';
      fr.style.display = vis ? '' : 'none';
      if (!vis) return;
      fr.style.cssText = 'left:' + (q.x - 3) + 'px;top:' + (q.y - 3) + 'px;width:' + (q.w + 6) + 'px;height:' + (q.h + 6) + 'px';
      var bw = b.offsetWidth || 110, bh = b.offsetHeight || 20;
      var x = railX(sq, bw), y = q.y + q.h - bh;
      y = Math.max(6, Math.min(y, innerHeight - bh - 6));
      used.forEach(function (u) { if (Math.abs(u.x - x) < 4 && Math.abs(u.y - y) < 24) y = Math.min(u.y + 24, innerHeight - bh - 6); });
      used.push({ x: x, y: y });
      b.style.left = x + 'px'; b.style.top = y + 'px';
      var ff = S.figures[id] || {}, has = !!((ff.selected && ff.selected.length) || ff.confirmed); b.querySelector('.n').textContent = '';
      b.classList.toggle('has', has);
      updateChip(id);
    });
    placeTeBtns();
    if (curId) placePop();
  }

  /* ---------- 一覧（ポップアップ） ---------- */
  var pop = D.createElement('div'); pop.className = 'ci-fp-pop'; pop.hidden = true; pop.setAttribute('role', 'dialog'); layer.appendChild(pop);
  pop.addEventListener('click', function (e) { e.stopPropagation(); });
  var curId = null, showAll = false, query = '';
  function esc(s) { return String(s).replace(/[&<>"]/g, function (m) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[m]; }); }
  function open(id) {
    if (curId === id && !pop.hidden) return close();
    curId = id; Object.keys(chips).forEach(function (k) { chips[k].setAttribute('aria-expanded', k === id ? 'true' : 'false'); frames[k].classList.toggle('on', k === id); });
    render(); pop.hidden = false; placePop(); var s = pop.querySelector('input[type=search]'); if (s) s.focus({ preventScroll: true });
  }
  function close() { pop.hidden = true; if (curId) { chips[curId].setAttribute('aria-expanded', 'false'); frames[curId].classList.remove('on'); } curId = null; }
  function placePop() {
    var b = chips[curId]; if (!b) return;
    var br = b.getBoundingClientRect();
    var x = br.left - 496;  // 右外の列の左へ開く
    if (x < 8) x = Math.max(8, Math.min(br.right - 488, innerWidth - 500));
    pop.style.left = x + 'px';
    pop.style.top = Math.max(8, Math.min(br.bottom + 6, innerHeight - 80)) + 'px';
  }
  function thumb(pt, f, data) {
    var on = f.selected.some(function (s) { return s.id === pt.id; });
    var ic = schematic(pt.id);   // 一覧の小さな絵は型の目印。押すとこのページの数字で描く
    return '<button type="button" class="ci-fp-thumb' + (on ? ' on' : '') + '" data-pid="' + pt.id + '" aria-pressed="' + (on ? 'true' : 'false') + '" title="' + esc(shortName(pt)) + (on ? '（もう一度押すと元の図）' : '') + '">' +
      '<span class="ck" aria-hidden="true">✓</span>' + ic + '<span class="nm">' + esc(shortName(pt)) + '</span></button>';
  }
  var showOthers = false;
  function render() {
    var f = fig(curId), sets = recSets(f), data = sets.data;
    var h = '<header><b>この図の Framework を選ぶ</b><p class="ci-fp-lead">押すとこのページの数字で描きます。もう一度押すと元の図</p></header>';
    h += photoOptsHtml(curId);
    if (sets.top.length) h += '<div class="ci-fp-thumbs">' + sets.top.map(function (pt) { return thumb(pt, f, data); }).join('') + '</div>';
    else h += '<p class="ci-fp-none">このページの数字で描ける型がありません</p>';
    if (sets.others.length) h += '<details class="ci-fp-more"' + (showOthers ? ' open' : '') + '><summary>ほかの型を見る</summary><div class="ci-fp-thumbs more">' +
      sets.others.map(function (pt) { return thumb(pt, f, data); }).join('') + '</div></details>';
    h += '<footer><button type="button" class="ci-fp-btn" data-act="clearpv" title="重ねた見本や実データのプレビューを消して、元の図に戻す。選んだ型も外す">元に戻す</button></footer>';
    pop.innerHTML = h;
    var d = pop.querySelector('details');
    if (d) d.addEventListener('toggle', function () { showOthers = d.open; });
  }
  function toggleSel(pid) {
    /* 単一選択：押すと切り替え／別の型で置き換え／同じ型をもう一度押すと元の図 */
    var f = fig(curId), cur = (f.selected[0] && f.selected[0].id) || (f.confirmed && !f.confirmed.photo && f.confirmed.id);
    if (cur === pid) { revertFig(curId); return; }
    var el = D.querySelector('[data-fp-fig="' + curId + '"]');
    if (!canDraw(BY[pid], extractData(el), el)) return;   // 数字で描けない型は押せない
    if (f.confirmed) undoConfirm(curId);
    f.selected = [{ id: pid, label: BY[pid].label, note: '' }];
    showPreview(curId, pid);
    save(); render(); place();
  }
  pop.addEventListener('click', function (e) {
    var pb = e.target.closest && e.target.closest('[data-photo]');
    if (pb) { photoAct(curId, pb.getAttribute('data-photo')); return; }
    var th = e.target.closest && e.target.closest('.ci-fp-thumb');
    if (th) { toggleSel(th.getAttribute('data-pid')); return; }
    var a = e.target.getAttribute && e.target.getAttribute('data-act'); if (!a) return;
    if (a === 'clearpv') revertFig(curId);
    else if (a === 'close') close();
  });
  D.addEventListener('click', function () { if (!pop.hidden) close(); });

  /* ---------- 選んだ型をその場に重ねる（実データで描けるときはこのページの数字だけ） ---------- */
  function legendFor(el) {
    if (!el) return null;
    var n = el.nextElementSibling;
    if (n && (n.classList.contains('legend') || (n.tagName === 'P' && /\blegend\b/.test(n.className)))) return n;
    return null;
  }
  function setLegendHidden(el, hide) {
    var lg = legendFor(el);
    if (!lg) return;
    lg.classList.toggle('ci-legacy-legend-off', !!hide);
    if (hide) lg.setAttribute('hidden', ''); else lg.removeAttribute('hidden');
  }
  function previewHost(el) {
    if (!el) return null;
    if (el.tagName === 'TABLE' || el.tagName === 'SVG') {
      var p = el.parentElement;
      if (p && getComputedStyle(p).position === 'static') p.style.position = 'relative';
      return p || el;
    }
    if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
    return el;
  }
  function updateChip(id) {
    var b = chips[id]; if (!b) return;
    var who = b.querySelector('.who');
    var f = S.figures[id] || {};
    var pid = f.preview || (f.confirmed && f.confirmed.id) || (f.selected && f.selected.length && f.selected[f.selected.length - 1].id);
    var name = (f.confirmed && f.confirmed.photo) ? '写真' : ((pid && BY[pid]) ? (shortName(BY[pid]) || '') : '');
    if (who) { who.textContent = name ? (' ' + name) : ''; who.hidden = !name; }
  }
  function showPreview(id, pid) {
    var f = fig(id); f.preview = pid; save();
    if (previews[id]) { previews[id].remove(); delete previews[id]; } // 旧レイヤー重ねは使わない
    var el = D.querySelector('[data-fp-fig="' + id + '"]');
    if (!el) return;
    var data = extractData(el);
    if (!canDraw(BY[pid], data, el)) { f.preview = null; save(); return; }   // 見本の絵では描かない
    var body = dataDraw(pid, data, el);
    var host = previewHost(el);
    [].slice.call(el.children).forEach(function (c) {
      if (!c.classList.contains('ci-fp-preview-in')) c.style.visibility = 'hidden';
    });
    if (el !== host) el.style.visibility = 'hidden';
    var pv = host.querySelector(':scope > .ci-fp-preview-in[data-for="' + id + '"]') || host.querySelector('.ci-fp-preview-in');
    if (!pv) {
      pv = D.createElement('div');
      pv.className = 'ci-fp-preview-in';
      pv.setAttribute('data-for', id);
      host.appendChild(pv);
    }
    if (el !== host) {
      pv.style.position = 'absolute';
      pv.style.left = el.offsetLeft + 'px';
      pv.style.top = el.offsetTop + 'px';
      pv.style.width = el.offsetWidth + 'px';
      pv.style.height = el.offsetHeight + 'px';
    } else {
      pv.style.position = 'absolute';
      pv.style.left = '0'; pv.style.top = '0';
      pv.style.width = '100%'; pv.style.height = '100%';
    }
    pv.style.boxSizing = 'border-box';
    pv.style.background = 'var(--white,#fff)';
    pv.style.overflow = 'hidden';
    pv.style.zIndex = '1';
    pv.innerHTML = body;
    setLegendHidden(el, true);
    updateChip(id);
    place();
  }
  function hidePreview(id) {
    var f = fig(id); f.preview = null; save();
    if (previews[id]) { previews[id].remove(); delete previews[id]; }
    var el = D.querySelector('[data-fp-fig="' + id + '"]');
    if (el) {
      var host = previewHost(el);
      var pv = host && host.querySelector('.ci-fp-preview-in[data-for="' + id + '"]') || (host && host.querySelector('.ci-fp-preview-in'));
      if (pv) pv.remove();
      [].slice.call(el.children).forEach(function (c) { c.style.visibility = ''; });
      el.style.visibility = '';
      if (!f.confirmed) setLegendHidden(el, false);
    }
    updateChip(id);
  }

  /* ---------- JSON ---------- */
  function importJSON() {
    var i = D.createElement('input'); i.type = 'file'; i.accept = 'application/json,.json';
    i.onchange = function () { var fr = new FileReader(); fr.onload = function () { try { var s = JSON.parse(fr.result); if (!s.figures) throw 0; S = s; S.deck = DECK; if (!S.edits) S.edits = []; save(); restore(); teRestore(); if (curId) render(); } catch (e) { alert('JSON を読めませんでした'); } }; fr.readAsText(i.files[0]); };
    i.click();
  }
  function restore() { Object.keys(previews).forEach(function (k) { previews[k].remove(); delete previews[k]; }); Object.keys(S.figures).forEach(function (k) { var f = S.figures[k]; if (f.preview && chips[k] && BY[f.preview]) showPreview(k, f.preview); }); place(); }

  /* ---------- 表示の切り替え ---------- */
  var bar = D.createElement('div'); bar.id = 'ci-fp-bar';
  bar.innerHTML = '<span class="lbl">Framework ピッカー／テキスト修正</span><button type="button" aria-pressed="true" data-act="tog" title="提出プレビュー" aria-label="提出プレビュー">提出プレビュー</button><span class="te-n"></span><button type="button" data-act="apply" title="選んだ Framework を静的な図に置き換え、テキスト修正と挿入を当てた HTML を書き出す（ピッカー痕跡なし）">修正を反映した版を書き出す</button>';
  D.body.appendChild(bar);
  bar.addEventListener('click', function (e) { var a = e.target.getAttribute('data-act'); if (a === 'tog') toggle(); else if (a === 'apply') exportApplied(); });
  function toggle(force) {
    var hide = typeof force === 'boolean' ? !force : !H.classList.contains('ci-fp-hidden');
    H.classList.toggle('ci-fp-hidden', hide); close(); teBtn.hidden = true; tePop.hidden = true; if (hide && typeof exitTeMode === 'function') exitTeMode();
    var b = bar.querySelector('[data-act=tog]'); var lab = hide ? '編集モード' : '提出プレビュー';
    b.setAttribute('aria-pressed', hide ? 'false' : 'true'); b.textContent = lab; b.title = lab; b.setAttribute('aria-label', lab);
    /* プレビューは図の枠内にあるので、ピッカーを隠しても図はそのまま。旧「表示中」→「提出プレビュー」、旧「非表示」→「編集モード」（v3.21.1） */
  }
  D.addEventListener('keydown', function (e) {
    if (e.shiftKey && (e.key === 'P' || e.key === 'p') && !/INPUT|TEXTAREA/.test(e.target.tagName)) { e.preventDefault(); toggle(); }
    if (e.key === 'Escape') {
      if (!pop.hidden) { close(); e.preventDefault(); return; }
      if (tePop && !tePop.hidden) { tePop.hidden = true; e.preventDefault(); return; }
      if (typeof teMode !== 'undefined' && teMode) { exitTeMode(); e.preventDefault(); }
    }
  });
  addEventListener('hashchange', function () { H.classList.toggle('ci-fp-static', /(^|[#&])static\b/.test(location.hash)); });
  var placeQ = false;
  function placeSoon() {
    if (placeQ) return;
    placeQ = true;
    requestAnimationFrame(function () { placeQ = false; place(); });
  }
  addEventListener('resize', placeSoon);
  addEventListener('scroll', place, { passive: true, capture: true });
  if (window.visualViewport) {
    visualViewport.addEventListener('resize', placeSoon);
    visualViewport.addEventListener('scroll', place);
  }
  if (window.ResizeObserver) new ResizeObserver(place).observe(D.body);
  if (window.MutationObserver) new MutationObserver(function (ms) {
    for (var i = 0; i < ms.length; i++) {
      var c = H.className;
      if (/\bci-present\b/.test(c) || /\bci-overview\b/.test(c) || /\bci-mfit\b/.test(c) || /\bci-fp-hidden\b/.test(c)) { placeSoon(); return; }
      if (ms[i].oldValue && ms[i].oldValue !== c) { placeSoon(); return; }
    }
  }).observe(H, { attributes: true, attributeFilter: ['class'], attributeOldValue: true });
  D.addEventListener('transitionend', place);
  if (D.fonts && D.fonts.ready) D.fonts.ready.then(placeSoon);
  addEventListener('load', placeSoon);
  /* ---------- 文言の修正（テキストを選ぶ → 修正 → 画面上で差分表示） ----------
   * 修正は {slide, sel(要素の目安), tag, node_text(元の文の段), node_k(同じ段の何番目), offset, old, new, time, numbers}
   * として S.edits に保存（型の選択と同じ JSON）。正本への反映は fp_apply_edits.py（元の文と一致を確かめて置換）。
   * 「テキスト修正」を押したページだけ修正モードになる。モード外では選択しても UI を出さない。 */
  if (!S.edits) S.edits = [];
  var NUM = /[0-9０-９]/;
  var teMode = null, tePageBtns = {};
  function exitTeMode() {
    teMode = null; H.classList.remove('ci-te-mode'); H.removeAttribute('data-ci-te-slide');
    Object.keys(tePageBtns).forEach(function (k) { tePageBtns[k].setAttribute('aria-pressed', 'false'); });
    teBtn.hidden = true; tePop.hidden = true;
  }
  function enterTeMode(id) {
    if (teMode === id) { exitTeMode(); return; }
    teMode = id; H.classList.add('ci-te-mode'); H.setAttribute('data-ci-te-slide', id);
    Object.keys(tePageBtns).forEach(function (k) { tePageBtns[k].setAttribute('aria-pressed', k === id ? 'true' : 'false'); });
  }
  var teBtn = D.createElement('button'); teBtn.type = 'button'; teBtn.className = 'ci-te-btn'; teBtn.textContent = '修正'; teBtn.hidden = true; layer.appendChild(teBtn);
  var tePop = D.createElement('div'); tePop.className = 'ci-te-pop'; tePop.hidden = true; layer.appendChild(tePop);
  tePop.addEventListener('click', function (e) { e.stopPropagation(); }); tePop.addEventListener('mousedown', function (e) { e.stopPropagation(); });
  (function makeTePageBtns() {
    var seen = {};
    [].slice.call(D.querySelectorAll('section.slide')).forEach(function (sec) {
      var id = slideId(sec); if (seen[id]) return; seen[id] = true;
      if (sec.classList.contains('pd-divider') || sec.classList.contains('divider') || sec.getAttribute('data-fp-skip') != null) return;
      var b = D.createElement('button'); b.type = 'button'; b.className = 'ci-te-page';
      b.textContent = 'テキスト修正'; b.setAttribute('aria-pressed', 'false'); b.setAttribute('data-te-slide', id);
      b.title = 'このページの文言を修正する（もう一度押すか Esc で終了）';
      b.addEventListener('click', function (e) { e.stopPropagation(); enterTeMode(id); });
      layer.appendChild(b); tePageBtns[id] = b;
    });
  })();
  placeTeBtns = function () {
    Object.keys(tePageBtns).forEach(function (id) {
      var b = tePageBtns[id];
      var sec = [].slice.call(D.querySelectorAll('section.slide')).filter(function (s) { return slideId(s) === id; })[0];
      if (!sec || !slideVisible(sec)) { b.style.display = 'none'; return; }
      b.style.display = '';
      var sq = rectOf(sec), tw = b.offsetWidth || 88, th = b.offsetHeight || 24;
      var x = railX(sq, tw);
      var y = sq.y + Math.min(120, Math.max(48, sq.h * 0.16));
      var chipsY = [];
      figs.forEach(function (el) {
        var sl = el.closest('section.slide'); if (!sl || slideId(sl) !== id) return;
        var cb = chips[el.getAttribute('data-fp-fig')];
        if (cb && cb.style.display !== 'none') chipsY.push(parseFloat(cb.style.top));
      });
      if (chipsY.length && y + th + 6 > Math.min.apply(null, chipsY)) y = Math.min.apply(null, chipsY) - th - 8;
      y = Math.max(6, Math.min(y, innerHeight - th - 6));
      b.style.left = x + 'px'; b.style.top = y + 'px';
    });
  };
  teBtn.addEventListener('mousedown', function (e) { e.preventDefault(); e.stopPropagation(); });
  var pending = null;
  function slideOf(n) { var s = n.nodeType === 1 ? n : n.parentElement; return s && s.closest('section.slide'); }
  function slideId(sec) { var all = [].slice.call(D.querySelectorAll('section.slide')); return sec.id || ('p' + String(all.indexOf(sec) + 1).padStart(2, '0')); }
  function skipNode(t) { var p = t.parentElement; return !p || p.closest('script,style,.ci-te-mark,#ci-fp-layer,.ci-hb,.cm,.ci-digest-btn,button') ; }
  // 段（run）＝隣り合うテキストと修正マークのまとまり。マークは元の文（data-old）で数える＝元の DOM の1つのテキストに当たる
  function runs(sec) {
    var out = [], w = D.createTreeWalker(sec, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null), n, cur = null, last = null;
    while ((n = w.nextNode())) {
      var isMark = n.nodeType === 1 && n.classList.contains('ci-te-mark');
      if (n.nodeType === 1 && !isMark) { continue; }
      if (n.nodeType === 3 && skipNode(n)) continue;
      var prev = isMark ? n.previousSibling : n.previousSibling;
      var contiguous = cur && last && prev === last;
      if (!contiguous) { cur = { parts: [], text: '' }; out.push(cur); }
      var t = isMark ? n.getAttribute('data-old') : n.data;
      cur.parts.push({ node: n, start: cur.text.length, mark: isMark }); cur.text += t; last = n;
    }
    return out;
  }
  function pathOf(el, sec) { var p = []; while (el && el !== sec) { var i = 1, s = el; while ((s = s.previousElementSibling)) if (s.tagName === el.tagName) i++; p.unshift(el.tagName.toLowerCase() + ':nth-of-type(' + i + ')'); el = el.parentElement; } return p.join(' > '); }
  D.addEventListener('mouseup', function (e) {
    if (H.classList.contains('ci-fp-hidden') || e.target.closest && e.target.closest('#ci-fp-layer,#ci-fp-bar')) return;
    setTimeout(function () {
      var sel = getSelection(); teBtn.hidden = true; pending = null;
      if (!teMode) return;  // 修正モードのときだけ「修正」を出す
      if (!sel.rangeCount || sel.isCollapsed) return;
      var r = sel.getRangeAt(0), a = r.startContainer;
      if (a !== r.endContainer || a.nodeType !== 3 || skipNode(a)) return;  // 1つのテキストの中だけ（太字などをまたぐ選択は不可）
      var sec = slideOf(a); if (!sec || !sel.toString().trim()) return;
      if (slideId(sec) !== teMode) return;
      var rs = runs(sec), run = null, part = null;
      rs.forEach(function (x) { x.parts.forEach(function (p) { if (p.node === a) { run = x; part = p; } }); });
      if (!run) return;
      var k = rs.filter(function (x, i) { return x.text === run.text && i < rs.indexOf(run); }).length;
      pending = { sec: sec, node: a, s: r.startOffset, e: r.endOffset, run: run.text, k: k, offset: part.start + r.startOffset };
      var q = r.getBoundingClientRect(); teBtn.style.left = Math.min(q.right + 4, innerWidth - 48) + 'px'; teBtn.style.top = Math.max(8, q.top - 26) + 'px'; teBtn.hidden = false;
    }, 0);
  });
  teBtn.addEventListener('click', function (e) {
    e.stopPropagation(); if (!pending) return; var P = pending, old = P.node.data.slice(P.s, P.e);
    tePop.innerHTML = '<b>文言を修正</b><small>元の文：<span class="o"></span></small><textarea rows="3"></textarea><div class="w" hidden>数字を含む修正です。内容担当の確認待ち（要確認）として記録します。</div>' +
      '<div class="ft"><button type="button" class="ci-fp-btn" data-a="x">やめる</button><button type="button" class="ci-fp-btn pri" data-a="ok">修正する</button></div>';
    tePop.querySelector('.o').textContent = old; var ta = tePop.querySelector('textarea'); ta.value = old;
    var warn = function () { tePop.querySelector('.w').hidden = !(NUM.test(old) || NUM.test(ta.value)); }; ta.oninput = warn; warn();
    tePop.style.left = teBtn.style.left; tePop.style.top = (parseFloat(teBtn.style.top) + 26) + 'px'; tePop.hidden = false; teBtn.hidden = true; ta.focus(); ta.select();
    tePop.onclick = function (ev) { ev.stopPropagation(); var a = ev.target.getAttribute('data-a'); if (a === 'x') tePop.hidden = true;
      if (a === 'ok') { var nv = ta.value; tePop.hidden = true; if (nv === old) return;
        var ed = { id: 'e' + Date.now().toString(36), slide: slideId(P.sec), sel: pathOf(P.node.parentElement, P.sec), tag: P.node.parentElement.tagName.toLowerCase(),
          node_text: P.run, node_k: P.k, offset: P.offset, old: old, new: nv, time: new Date().toISOString(), numbers: NUM.test(old) || NUM.test(nv) };
        if (ed.numbers) ed.status = '要確認（内容担当の確認待ち）';
        mark(P.node, P.s, P.e, ed); S.edits.push(ed); save(); getSelection().removeAllRanges(); updBar(); } };
  });
  function mark(node, s, e, ed) {
    var mid = node.splitText(s); mid.splitText(e - s);
    var m = D.createElement('span'); m.className = 'ci-te-mark' + (ed.numbers ? ' num' : ''); m.setAttribute('data-te', ed.id); m.setAttribute('data-old', ed.old);
    m.innerHTML = '<del></del><ins></ins>' + (ed.numbers ? '<i>要確認</i>' : ''); m.querySelector('del').textContent = ed.old; m.querySelector('ins').textContent = ed.new;
    m.title = (ed.numbers ? '【要確認・数字を含む】' : '') + '修正：「' + ed.old + '」→「' + ed.new + '」（押すと取り消し）';
    mid.parentNode.replaceChild(m, mid);
    m.addEventListener('click', function (ev) { ev.stopPropagation(); if (confirm('この修正を取り消しますか？\n「' + ed.old + '」→「' + ed.new + '」')) undo(ed.id); });
  }
  function undo(id) { var m = D.querySelector('.ci-te-mark[data-te="' + id + '"]'); if (m) { var p = m.parentNode; p.replaceChild(D.createTextNode(m.getAttribute('data-old')), m); p.normalize(); }
    S.edits = S.edits.filter(function (x) { return x.id !== id; }); save(); updBar(); }
  function teRestore() {
    [].slice.call(D.querySelectorAll('.ci-te-mark')).forEach(function (m) { var p = m.parentNode; p.replaceChild(D.createTextNode(m.getAttribute('data-old')), m); p.normalize(); });
    var bad = 0;
    (S.edits || []).forEach(function (ed) {
      var sec = [].slice.call(D.querySelectorAll('section.slide')).filter(function (s) { return slideId(s) === ed.slide; })[0]; if (!sec) { ed.conflict = true; bad++; return; }
      var run = runs(sec).filter(function (x) { return x.text === ed.node_text; })[ed.node_k];
      var part = run && run.parts.filter(function (p) { return !p.mark && p.start <= ed.offset && ed.offset + ed.old.length <= p.start + p.node.data.length; })[0];
      if (!part || part.node.data.substr(ed.offset - part.start, ed.old.length) !== ed.old) { ed.conflict = true; bad++; return; }
      delete ed.conflict; mark(part.node, ed.offset - part.start, ed.offset - part.start + ed.old.length, ed);
    });
    if (bad) console.warn('ci-te: 元の文と合わない修正', bad); updBar();
  }
  var updBar = function () {};
  updBar = function () { var n = S.edits.length, q = S.edits.filter(function (x) { return x.numbers; }).length; var el = bar.querySelector('.te-n'); el.textContent = n ? ('修正 ' + n + ' 件' + (q ? '（要確認 ' + q + '）' : '')) : ''; el.className = 'te-n' + (q ? ' num' : ''); };
  /* ---------- 確定・書き出し・画像/表の挿入 ---------- */
  function deckBase() { return (DECK || 'deck').replace(/\.html?$/i, ''); }
  function downloadBlob(name, text, mime) {
    var a = D.createElement('a'); a.href = URL.createObjectURL(new Blob([text], { type: mime || 'text/html;charset=utf-8' }));
    a.download = name; D.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 800);
  }
  function applyConfirm(id, pid, silent) {
    var el = D.querySelector('[data-fp-fig="' + id + '"]'); if (!el || !BY[pid]) return false;
    var data = extractData(el), real = canDraw(BY[pid], data, el);
    if (!real) return false;   // 数字で描けない型は確定しない（見本の絵は入れない）
    if (ORIG[id] == null) ORIG[id] = el.innerHTML;
    var html = figMarkup(id, pid);
    hidePreview(id);
    el.innerHTML = html;
    el.setAttribute('data-fp-confirmed', pid);
    var f = fig(id); f.confirmed = { id: pid, html: html, time: new Date().toISOString(), real: !!real }; f.preview = null; save();
    setLegendHidden(el, true);
    updateChip(id);
    return true;
  }
  function undoConfirm(id) {
    var el = D.querySelector('[data-fp-fig="' + id + '"]'); if (!el) return;
    if (ORIG[id] != null) el.innerHTML = ORIG[id];
    el.removeAttribute('data-fp-confirmed');
    var f = fig(id);
    if (f.confirmed && f.confirmed.photo) { if (f.confirmed.style0) el.setAttribute('style', f.confirmed.style0); else el.removeAttribute('style'); }
    delete f.confirmed; save();
    setLegendHidden(el, !!(f && f.preview));
    updateChip(id);
  }
  function revertFig(id) {
    if (!id) return;
    hidePreview(id);
    var f = fig(id);
    if (f.confirmed) undoConfirm(id);
    f.selected = [];
    save();
    if (curId === id) render();
    updateChip(id);
    place();
  }
  /* ---------- 写真に置き換える（ダイジェスト表示の図・社内版だけ・v3.20.2 試作） ----------
     人物写真＝審査済みの既存素材だけ（fp_build.py internal --photos で同梱。生成しない）。任意の写真＝ファイルから選ぶ（WebP・長辺1600px以下に縮める）。
     写真は図の枠いっぱい。高さはグリッドの行（列幅と同じ正方モジュール）に揃え、本文エリアからはみ出すなら元の高さに戻す。 */
  var PHOTOS = (function () { var e = D.getElementById('ci-fp-photos'); try { return e ? JSON.parse(e.textContent) : {}; } catch (x) { return {}; } })();
  var PERSONA_ORDER = ['consumer', 'influencer', 'consultant'];
  var showPersons = false;
  function inDigest(id) { var el = D.querySelector('[data-fp-fig="' + id + '"]'); var sl = el && el.closest('section.slide'); return !!(sl && sl.getAttribute('data-page-mode') === 'digest'); }
  function photoOptsHtml(id) {
    if (!inDigest(id)) return '';
    var f = fig(id), cur = f.confirmed && f.confirmed.photo;
    var ps = PERSONA_ORDER.filter(function (k) { return PHOTOS[k]; });
    var h = '<div class="ci-fp-photo-opts"><p class="ci-fp-photo-h">写真に置き換える（ダイジェスト）</p>' +
      '<button type="button" class="ci-fp-btn' + (cur && cur !== 'file' ? ' on' : '') + '" data-photo="persons"' + (ps.length ? '' : ' disabled') + '>人物写真（消費者・インフルエンサー・コンサルタント）</button>' +
      '<button type="button" class="ci-fp-btn' + (cur === 'file' ? ' on' : '') + '" data-photo="file">任意の写真（ファイルから選ぶ）</button>';
    var miss = PHOTOS._missing ? Object.keys(PHOTOS._missing) : [];
    if (showPersons && miss.length) h += '<p class="ci-fp-photo-h">' + miss.map(function (k) { return ({ consumer: '消費者', influencer: 'インフルエンサー', consultant: 'コンサルタント' })[k] + '：' + esc(PHOTOS._missing[k]); }).join('／') + '（商品カテゴリー×購入層に合う審査済み素材だけを出します）</p>';
    if (showPersons && ps.length) {
      h += '<div class="ci-fp-photo-persons">' + ps.map(function (k) {
        var a = PHOTOS[k];
        return '<button type="button" class="ci-fp-thumb' + (cur === k ? ' on' : '') + '" data-photo="p:' + k + '" title="' + esc(a.caption) + '"><span class="ck" aria-hidden="true">✓</span><img src="' + a.src + '" alt=""><span class="nm">' + esc(a.caption) + '</span></button>';
      }).join('') + '</div>';
    }
    return h + '</div>';
  }
  function photoAct(id, a) {
    if (a === 'persons') { showPersons = !showPersons; render(); return; }
    if (a === 'file') {
      var i = D.createElement('input'); i.type = 'file'; i.accept = 'image/*';
      i.onchange = function () { if (i.files && i.files[0]) shrinkToWebP(i.files[0], function (url) { applyPhoto(id, { photo: 'file', src: url, alt: '', caption: '', fit: 'cover' }); }); };
      i.click(); return;
    }
    if (a.indexOf('p:') === 0) {
      var k = a.slice(2), p = PHOTOS[k]; if (!p) return;
      applyPhoto(id, { photo: k, src: p.src, alt: p.alt, caption: p.caption, fit: 'cutout' });
    }
  }
  function photoMarkup(rec) {
    var cap = rec.caption ? '<figcaption style="position:absolute;left:0;right:0;bottom:0;height:16px;line-height:16px;font-size:10px;color:var(--ink-60,#5a6470);text-align:right;letter-spacing:.04em;white-space:nowrap;overflow:hidden">' + esc(rec.caption) + '</figcaption>' : '';
    var capH = rec.caption ? 18 : 0;
    var img = '<img src="' + rec.src + '" alt="' + esc(rec.alt || '') + '" style="position:absolute;left:0;top:0;width:100%;height:calc(100% - ' + capH + 'px);object-fit:' + (rec.fit === 'cutout' ? 'contain;object-position:center bottom' : 'cover;object-position:center') + ';border-radius:12px;display:block' + (rec.fit === 'cutout' ? ';background:var(--crystal,#C3D7EE)' : '') + '">';
    return '<figure class="ci-swap-photo" data-photo-kind="' + esc(rec.photo) + '" style="position:relative;margin:0;width:100%;height:100%">' + img + cap + '</figure>';
  }
  function fitPhotoFrame(el, h0) {
    /* 高さをグリッドの行に揃える：列幅と同じ正方モジュール。最低2行、元の高さ以上。はみ出すなら1段ずつ下げる */
    var sl = el.closest('section.slide'), g = gridOf(sl), k = sl.offsetWidth / (rectOf(sl).w || 1);
    var row = g.colW + g.gap, cb = contentBox(sl);
    function bottomOf() { var b = 0; [].forEach.call(sl.querySelectorAll('*'), function (n) { if (n.closest('.ci-fp-ins-btn,.ci-te-page,.ci-digest-btn,.period,.ci-hb,.cm')) return; var r = n.getBoundingClientRect(); if (r.width > 0 && r.height > 0 && getComputedStyle(n).position !== 'fixed') b = Math.max(b, r.bottom); }); return b; }
    var limit = cb.y + cb.h;
    for (var n = Math.max(2, Math.ceil((h0 / k + g.gap) / row) + 1); n >= 1; n--) {
      var hpx = (n * g.colW + (n - 1) * g.gap) * k;
      if (n === 1 || hpx < h0) hpx = h0;
      el.style.height = hpx + 'px'; el.style.minHeight = hpx + 'px';
      if (bottomOf() <= limit + 0.5 || hpx === h0) return { rows: n, h: hpx };
    }
    return { rows: 0, h: h0 };
  }
  function applyPhoto(id, rec, silent) {
    var el = D.querySelector('[data-fp-fig="' + id + '"]'); if (!el) return false;
    var f = fig(id);
    if (ORIG[id] == null) ORIG[id] = el.innerHTML;
    var style0 = (f.confirmed && f.confirmed.photo) ? f.confirmed.style0 : (el.getAttribute('style') || '');
    if (f.confirmed && f.confirmed.photo) { if (style0) el.setAttribute('style', style0); else el.removeAttribute('style'); }
    hidePreview(id);
    var h0 = el.getBoundingClientRect().height * (el.closest('section.slide').offsetWidth / (rectOf(el.closest('section.slide')).w || 1));
    el.innerHTML = photoMarkup(rec);
    var fit = fitPhotoFrame(el, h0);
    el.setAttribute('data-fp-confirmed', 'photo:' + rec.photo);
    f.selected = [];
    f.confirmed = { id: 'photo:' + rec.photo, photo: rec.photo, html: el.innerHTML, style0: style0, style: el.getAttribute('style') || '', rows: fit.rows, time: new Date().toISOString(), real: true };
    f.preview = null; save();
    setLegendHidden(el, true); updateChip(id);
    if (!silent && curId === id) render();
    place();
    return fit;
  }
  function restorePhotos() {
    Object.keys(S.figures || {}).forEach(function (id) {
      var f = S.figures[id], el = D.querySelector('[data-fp-fig="' + id + '"]');
      if (!f || !f.confirmed || !f.confirmed.photo || !el) return;
      if (ORIG[id] == null) ORIG[id] = el.innerHTML;
      el.innerHTML = f.confirmed.html; if (f.confirmed.style) el.setAttribute('style', f.confirmed.style);
      el.setAttribute('data-fp-confirmed', f.confirmed.id); updateChip(id);
    });
  }
  function pickPid(f) {
    if (!f) return null;
    if (f.preview && f.selected && f.selected.some(function (s) { return s.id === f.preview; })) return f.preview;
    if (f.selected && f.selected.length) return f.selected[f.selected.length - 1].id;
    if (f.confirmed && f.confirmed.id) return f.confirmed.id;
    return null;
  }
  function confirmSelectionsForExport() {
    var msgs = [];
    Object.keys(S.figures || {}).forEach(function (id) {
      var f = S.figures[id];
      var pid = pickPid(f);
      if (!pid || !BY[pid]) return;
      if (false) {
        var last = shortName(BY[pid]) || pid;
        var others = f.selected.map(function (s) { return shortName((BY[s.id] || {})) || s.id; }).filter(function (n) { return n !== last; });
        msgs.push(id + ' は ' + f.selected.length + ' 件選ばれています。最後に選んだ「' + last + '」だけを反映しました' + (others.length ? '（他: ' + others.join('、') + '）' : '') + '。');
      }
      var el = D.querySelector('[data-fp-fig="' + id + '"]');
      var real = canDraw(BY[pid], extractData(el), el);
      if (!real) { msgs.push(id + ' の「' + (shortName(BY[pid]) || pid) + '」はこのページの数字では描けないため、元の図のままにしました。'); return; }
      applyConfirm(id, pid, true);
    });
    return msgs;
  }

  function tableSigOf(root) {
    return [].slice.call(root.querySelectorAll('table')).filter(function (t) { return !t.closest('#ci-fp-layer,#ci-fp-bar,.ci-fp-pop,.ci-te-pop,.ci-fp-ins-pop,.ci-fp-preview'); }).map(function (t) {
      var rows = [].slice.call(t.querySelectorAll('tr'));
      var cells = rows.map(function (r) { return [].slice.call(r.querySelectorAll('th,td')).map(function (c) { return c.textContent.replace(/\s+/g, ' ').trim(); }); });
      var hdr = cells[0] || [];
      return { rows: rows.length, ncells: cells.map(function (c) { return c.length; }), hdr_last: hdr[hdr.length - 1] || '', col1: cells.map(function (c) { return c[0] || ''; }) };
    });
  }
  var TABLE0 = tableSigOf(D);

  var GRID_COLS = 12, GRID_GAP = 8, MIN_FS = 10;
  function slideInner(slide) {
    var sq = rectOf(slide), cs = getComputedStyle(slide);
    var pl = parseFloat(cs.paddingLeft) || 0, pr = parseFloat(cs.paddingRight) || 0;
    var pt = parseFloat(cs.paddingTop) || 0, pb = parseFloat(cs.paddingBottom) || 0;
    return { x: sq.x + pl, y: sq.y + pt, w: Math.max(40, sq.w - pl - pr), h: Math.max(40, sq.h - pt - pb), pl: pl, pr: pr, pt: pt, pb: pb, sq: sq };
  }
  function gridOf(slide) {
    var inn = slideInner(slide), gap = GRID_GAP, cols = GRID_COLS;
    var colW = (inn.w - gap * (cols - 1)) / cols;
    function span(start, n) { return { x: inn.x + start * (colW + gap), w: n * colW + (n - 1) * gap }; }
    return { inn: inn, gap: gap, colW: colW, cols: cols, span: span };
  }
  function contentBox(slide) {
    var g = gridOf(slide), inn = g.inn, sq = inn.sq;
    var bottoms = [];
    ['.hdr', 'h2', 'h1', '.title', '.accent-bar', '.gist', '.ci-gist', '.period'].forEach(function (sel) {
      var e = slide.querySelector(sel);
      if (!e) return;
      var r = rectOf(e);
      /* フッター側の period は上端に使わない */
      if (r.h > 0 && r.y + r.h < sq.y + sq.h * 0.55) bottoms.push(r.y + r.h);
    });
    var top = bottoms.length ? Math.max.apply(null, bottoms) + g.gap : inn.y;
    var bot = sq.y + sq.h - Math.min(inn.pb || 18, 24);
    ['.period', '.ci-digest-btn'].forEach(function (sel) {
      var e = slide.querySelector(sel);
      if (!e) return;
      var r = rectOf(e);
      if (r.h > 0 && r.y > sq.y + sq.h * 0.7) bot = Math.min(bot, r.y - 4);
    });
    var full = g.span(0, GRID_COLS);
    return { x: full.x, y: top, w: full.w, h: Math.max(40, bot - top), sx: sq.x, sy: sq.y, sw: sq.w, sh: sq.h };
  }
  function regionBox(slide, region) {
    var c = contentBox(slide), g = gridOf(slide), b = { x: c.x, y: c.y, w: c.w, h: c.h };
    if (region === 'left') { var s = g.span(0, 6); b.x = s.x; b.w = s.w; }
    else if (region === 'right') { var s = g.span(6, 6); b.x = s.x; b.w = s.w; }
    else if (region === 'top') { b.h = Math.max(40, (c.h - g.gap) / 2); }
    else if (region === 'bottom') { b.h = Math.max(40, (c.h - g.gap) / 2); b.y = c.y + (c.h - b.h); }
    return b;
  }
  function remainBox(slide, region) {
    if (region === 'right') return regionBox(slide, 'left');
    if (region === 'left') return regionBox(slide, 'right');
    if (region === 'top') return regionBox(slide, 'bottom');
    if (region === 'bottom') return regionBox(slide, 'top');
    return null;
  }
  function isChromeEl(el) {
    if (!el || !el.classList) return true;
    if (el.matches && el.matches('.ci-hb,.corner,.hdr,.title,.accent-bar,.gist,.ci-gist,.period,.ci-digest-btn,.ci-fp-ins,.ci-fp-chip,.ci-fp-frame,.ci-fp-ins-btn,.ci-te-page,.ci-te-btn,.ci-fp-preview-in,h1,h2,svg.corner')) return true;
    return false;
  }
  function movableEls(slide) {
    return [].slice.call(slide.children).filter(function (el) {
      if (isChromeEl(el)) return false;
      if (el.hasAttribute('aria-hidden') && (el.classList.contains('dg-photo') || el.getAttribute('data-dg-photo'))) return false;
      var r = el.getBoundingClientRect();
      if (!el.classList.contains('ci-fp-reflowed') && (r.width < 2 || r.height < 2)) return false;
      return true;
    });
  }
  function slideKey(slide) { return slideId(slide) || slide.id || ''; }
  function rememberReflow(slide) {
    S.reflows = S.reflows || {};
    var key = slideKey(slide);
    if (S.reflows[key] && S.reflows[key].orig) return S.reflows[key];
    var orig = movableEls(slide).map(function (el) {
      return { style: el.getAttribute('style') || '', cls: el.getAttribute('class') || '' };
    });
    S.reflows[key] = { orig: orig };
    return S.reflows[key];
  }
  function clearReflow(slide, forget) {
    if (!slide) return;
    var key = slideKey(slide);
    var rec = (S.reflows || {})[key];
    var els = [].slice.call(slide.querySelectorAll('.ci-fp-reflowed'));
    if (!els.length) els = movableEls(slide);
    els.forEach(function (el, i) {
      var o = rec && rec.orig && rec.orig[i];
      if (o) {
        if (o.style) el.setAttribute('style', o.style); else el.removeAttribute('style');
      } else {
        ['position','left','top','width','maxWidth','margin','boxSizing','height','maxHeight','overflow'].forEach(function (k) { el.style[k] = ''; });
      }
      el.classList.remove('ci-fp-reflowed', 'ci-fp-kr-stack');
      [].slice.call(el.querySelectorAll('[data-fp-reflow-tmp]')).forEach(function (n) {
        var st = n.getAttribute('data-fp-reflow-tmp');
        if (st != null) { if (st) n.setAttribute('style', st); else n.removeAttribute('style'); }
        n.removeAttribute('data-fp-reflow-tmp');
      });
    });
    slide.classList.remove('ci-fp-reflowing', 'ci-fp-reflow-tight');
    slide.removeAttribute('data-fp-reflow-region');
    if (forget && S.reflows) delete S.reflows[key];
  }
  function tmpStyle(el, css) {
    if (!el.hasAttribute('data-fp-reflow-tmp')) el.setAttribute('data-fp-reflow-tmp', el.getAttribute('style') || '');
    el.style.cssText += ';' + css;
  }
  function applyReflow(slide, region, silent) {
    if (!slide) return [];
    var inserts = (S.inserts || []).filter(function (x) { return x.slide === slideKey(slide); });
    if (!inserts.length) { clearReflow(slide, true); save(); return []; }
    region = region || inserts[inserts.length - 1].region || 'full';
    rememberReflow(slide);
    clearReflow(slide, false);
    var remain = remainBox(slide, region);
    var msgs = [];
    var els = movableEls(slide);
    if (!remain || remain.w < 24 || remain.h < 24) {
      msgs.push((slide.id || slideKey(slide)) + '：全面挿入のため、残りの要素を置く区画がありません。');
      if (!silent && msgs.length) alert(msgs.join('\n'));
      S.reflows[slideKey(slide)].warn = msgs;
      save();
      return msgs;
    }
    slide.classList.add('ci-fp-reflowing');
    var tight = remain.w < contentBox(slide).w * 0.7 || remain.h < contentBox(slide).h * 0.7;
    if (tight) slide.classList.add('ci-fp-reflow-tight');
    slide.setAttribute('data-fp-reflow-region', region);
    var sq = rectOf(slide), gap = tight ? 4 : GRID_GAP, y = remain.y;
    els.forEach(function (el) {
      el.classList.add('ci-fp-reflowed');
      el.style.position = 'absolute';
      el.style.left = (remain.x - sq.x) + 'px';
      el.style.top = (y - sq.y) + 'px';
      el.style.width = remain.w + 'px';
      el.style.maxWidth = remain.w + 'px';
      el.style.boxSizing = 'border-box';
      el.style.margin = '0';
      var row = el.querySelector('.sgrp-row');
      if (row) {
        /* 残りが狭いときはカードを縦積みせず、1シリーズ＝1行の指標列にする（文字サイズは維持） */
        var gRow = tight ? 1 : 2;
        tmpStyle(row, 'display:flex;flex-direction:column;flex-wrap:nowrap;align-items:stretch;gap:' + gRow + 'px;padding-top:0;line-height:1.2');
        [].slice.call(row.children).forEach(function (c) {
          tmpStyle(c, 'display:flex;flex-direction:row;flex-wrap:wrap;align-items:center;gap:' + gRow + 'px;flex:0 0 auto;width:100%;max-width:100%;min-width:0;box-sizing:border-box;line-height:1.2;margin:0');
        });
      }
      if (el.classList.contains('dgx-split')) tmpStyle(el, 'flex-direction:column;flex-wrap:wrap');
      if (el.classList.contains('kr-band')) {
        tmpStyle(el, 'display:flex;flex-direction:row;flex-wrap:nowrap;gap:4px;align-items:flex-start');
        var cards = [].slice.call(el.children).filter(function (c) { return c.classList.contains('kr'); });
        var gapK = 4, needStack = cards.length > 1;
        if (cards.length) {
          var each = (remain.w - gapK * Math.max(0, cards.length - 1)) / cards.length;
          needStack = false;
          cards.forEach(function (c) {
            var v = c.querySelector('.kr-v') || c;
            var prevWS = v.style.whiteSpace;
            v.style.whiteSpace = 'nowrap';
            var need = v.scrollWidth + 16;
            v.style.whiteSpace = prevWS;
            if (need > each + 0.5) needStack = true;
          });
        }
        if (needStack) {
          el.classList.add('ci-fp-kr-stack');
          tmpStyle(el, 'display:flex;flex-direction:column;flex-wrap:nowrap;gap:' + (tight ? 2 : 4) + 'px;align-items:stretch');
          cards.forEach(function (c) {
            tmpStyle(c, 'flex:0 0 auto;width:100%;max-width:100%;min-width:0;box-sizing:border-box');
          });
        } else {
          el.classList.remove('ci-fp-kr-stack');
        }
      }
      if (el.classList.contains('okr-insight')) tmpStyle(el, 'display:flex;flex-direction:column;flex-wrap:nowrap;gap:2px;align-items:flex-start');
      var h = el.getBoundingClientRect().height;
      el.style.top = (y - sq.y) + 'px';
      y += h + gap;
    });
    var overflow = y - gap - (remain.y + remain.h);
    if (overflow > 1) {
      slide.classList.add('ci-fp-reflow-tight');
      /* 余白だけ詰めて再計測（文字サイズは触らない） */
      var g2 = 2;
      els.forEach(function (el) {
        var row = el.querySelector('.sgrp-row');
        if (row) {
          tmpStyle(row, 'gap:1px;padding-top:0;line-height:1.2');
          [].slice.call(row.children).forEach(function (c) {
            tmpStyle(c, 'gap:1px;line-height:1.2;margin:0');
            [].slice.call(c.querySelectorAll('.box,.trend,.nm')).forEach(function (b) { tmpStyle(b, 'margin:0;'); });
          });
        }
        if (el.classList.contains('ci-fp-kr-stack') || (el.classList.contains('kr-band') && el.classList.contains('ci-fp-kr-stack'))) {
          tmpStyle(el, 'gap:2px');
        }
        if (el.classList.contains('okr-insight')) tmpStyle(el, 'gap:1px;padding:1px 6px;line-height:1.25');
        if (el.classList.contains('t-note')) tmpStyle(el, 'line-height:1.25');
      });
      y = remain.y;
      els.forEach(function (el) {
        var h = el.getBoundingClientRect().height;
        el.style.top = (y - sq.y) + 'px';
        y += h + g2;
      });
      overflow = y - g2 - (remain.y + remain.h);
    }
    if (overflow > 1) {
      msgs.push((slide.id || slideKey(slide)) + '：残りの区画に入りきりません（文字サイズは変えていません）。不足 ' + Math.ceil(overflow) + 'px。');
    }
    var tooSmall = [];
    els.forEach(function (el) {
      [].slice.call(el.querySelectorAll('*')).concat([el]).forEach(function (n) {
        if (n.nodeType !== 1) return;
        var fs = parseFloat(getComputedStyle(n).fontSize);
        if (fs && fs + 0.05 < MIN_FS && !tooSmall.some(function (t) { return t === n; })) {
          /* 元から最小未満のページ用トークンはそのまま。挿入で新たに下げていないかだけ見る */
        }
      });
    });
    /* 文字の重なり・切れを検査（文字サイズは変えない。欠けていれば警告） */
    var cuts = [];
    els.forEach(function (el) {
      var tw = D.createTreeWalker(el, NodeFilter.SHOW_TEXT, null);
      var n;
      while ((n = tw.nextNode())) {
        var tx = String(n.nodeValue || '').replace(/\s+/g, ' ').trim();
        if (!tx) continue;
        var rg = D.createRange();
        try { rg.selectNodeContents(n); } catch (e) { continue; }
        var r = rg.getBoundingClientRect();
        if (r.width < 0.4 || r.height < 0.4) continue;
        if (r.left < remain.x - 1.5 || r.right > remain.x + remain.w + 1.5 || r.bottom > remain.y + remain.h + 1.5) {
          cuts.push(tx.slice(0, 24));
          continue;
        }
        var p = n.parentElement;
        while (p && p !== slide) {
          var cs = getComputedStyle(p);
          if (cs.overflowX === 'hidden' || cs.overflow === 'hidden' || cs.overflowY === 'hidden') {
            var pr = p.getBoundingClientRect();
            if (r.left < pr.left - 1.5 || r.right > pr.right + 1.5 || r.top < pr.top - 1.5 || r.bottom > pr.bottom + 1.5) {
              cuts.push(tx.slice(0, 24));
              break;
            }
          }
          p = p.parentElement;
        }
      }
    });
    if (cuts.length) {
      var uniq = [];
      cuts.forEach(function (t) { if (uniq.indexOf(t) < 0) uniq.push(t); });
      msgs.push((slide.id || slideKey(slide)) + '：文字が欠けています（' + uniq.slice(0, 4).join(' / ') + (uniq.length > 4 ? ' ほか' : '') + '）。文字サイズは変えていません。');
    }
    S.reflows[slideKey(slide)].warn = msgs;
    S.reflows[slideKey(slide)].region = region;
    save();
    if (!silent && msgs.length) alert(msgs.join('\n'));
    return msgs;
  }
  function reflowSlideOf(rec, silent) {
    var slide = D.getElementById(rec && rec.slide);
    if (slide) return applyReflow(slide, rec.region, silent);
    return [];
  }
  function regionPct(slide, region) {
    var c = contentBox(slide), b = regionBox(slide, region), sq = rectOf(slide);
    return { l: ((b.x - sq.x) / sq.w * 100), t: ((b.y - sq.y) / sq.h * 100), w: (b.w / sq.w * 100), h: (b.h / sq.h * 100) };
  }
  function figsOverlap(slide, region) {
    var b = regionBox(slide, region), hit = [];
    figs.forEach(function (el) {
      if ((el.closest('section.slide') || el) !== slide) return;
      if (el.getAttribute('data-fp-replaced')) return;
      var q = rectOf(el);
      var ox = Math.max(0, Math.min(q.x + q.w, b.x + b.w) - Math.max(q.x, b.x));
      var oy = Math.max(0, Math.min(q.y + q.h, b.y + b.h) - Math.max(q.y, b.y));
      if (ox > 24 && oy > 24) hit.push(el);
    });
    return hit;
  }

  function insEl(rec) { return D.querySelector('.ci-fp-ins[data-ins="' + rec.id + '"]'); }
  function renderInsert(rec) {
    var slide = D.getElementById(rec.slide) || [].slice.call(D.querySelectorAll('section.slide')).filter(function (s) { return slideId(s) === rec.slide; })[0];
    if (!slide) return;
    var el = insEl(rec);
    if (!el) { el = D.createElement('div'); el.className = 'ci-fp-ins'; el.setAttribute('data-ins', rec.id); slide.appendChild(el); }
    el.setAttribute('data-region', rec.region);
    el.setAttribute('data-ins-type', rec.type);
    var pct = rec.pct || regionPct(slide, rec.region);
    rec.pct = pct;
    el.style.cssText = 'position:absolute;left:' + pct.l.toFixed(2) + '%;top:' + pct.t.toFixed(2) + '%;width:' + pct.w.toFixed(2) + '%;height:' + pct.h.toFixed(2) + '%;z-index:6;box-sizing:border-box;background:var(--white);';
    var tools = '<div class="ci-fp-ins-tools"><button type="button" data-ins-a="move" title="区画を変える">移動</button><button type="button" data-ins-a="del" title="この挿入を削除">削除</button></div>';
    if (rec.type === 'image') {
      el.innerHTML = tools + '<figure class="ci-ins-fig"><img alt="' + esc(rec.caption || '') + '" style="object-fit:cover;object-position:center top;width:100%;height:100%;display:block;background:var(--white)"><figcaption class="ci-ins-cap"><input type="text" value="' + esc(rec.caption || '') + '" placeholder="キャプション"></figcaption></figure>';
      el.querySelector('img').src = rec.dataUrl;
      var inp = el.querySelector('input');
      inp.addEventListener('change', function () { rec.caption = inp.value; save(); el.querySelector('img').alt = rec.caption; });
      inp.addEventListener('click', function (e) { e.stopPropagation(); });
    } else {
      el.innerHTML = tools + '<div class="ci-ins-table">' + rec.tableHtml + '</div>';
    }
    el.onclick = function (e) { e.stopPropagation(); };
    el.querySelector('.ci-fp-ins-tools').addEventListener('click', function (e) {
      e.stopPropagation();
      var a = e.target.getAttribute('data-ins-a');
      if (a === 'del') removeInsert(rec.id);
      else if (a === 'move') moveInsert(rec.id);
    });
  }
  function renderAllInserts() {
    (S.inserts || []).forEach(renderInsert);
    var seen = {};
    (S.inserts || []).forEach(function (rec) {
      if (seen[rec.slide]) return;
      seen[rec.slide] = 1;
      reflowSlideOf(rec, true);
    });
  }
  function removeInsert(id) {
    var rec = (S.inserts || []).filter(function (x) { return x.id === id; })[0];
    if (!rec) return;
    S.insUndo.push({ type: 'del', rec: JSON.parse(JSON.stringify(rec)) });
    S.inserts = S.inserts.filter(function (x) { return x.id !== id; });
    var el = insEl(rec); if (el) el.remove();
    (rec.replaces || []).forEach(function (fid) {
      var f = D.querySelector('[data-fp-fig="' + fid + '"]');
      if (f) { f.removeAttribute('data-fp-replaced'); f.style.visibility = ''; }
    });
    var slide = D.getElementById(rec.slide);
    if (slide) {
      var left = (S.inserts || []).filter(function (x) { return x.slide === rec.slide; });
      if (left.length) applyReflow(slide, left[left.length - 1].region);
      else clearReflow(slide, true);
    }
    save(); place();
  }
  function moveInsert(id) {
    var rec = (S.inserts || []).filter(function (x) { return x.id === id; })[0]; if (!rec) return;
    openInsPop(rec.slide, rec);
  }
  function undoInsert() {
    var u = (S.insUndo || []).pop(); if (!u) { alert('戻す挿入操作がありません'); return; }
    if (u.type === 'add') removeInsert(u.id);
    else if (u.type === 'del' && u.rec) { S.inserts.push(u.rec); renderInsert(u.rec); reflowSlideOf(u.rec); save(); }
    else if (u.type === 'move' && u.rec) {
      var rec = (S.inserts || []).filter(function (x) { return x.id === u.rec.id; })[0];
      if (rec) { rec.region = u.prev; rec.pct = u.prevPct; renderInsert(rec); reflowSlideOf(rec); save(); place(); }
    }
  }
  function commitInsert(rec, replaces) {
    rec.id = rec.id || ('ins' + Date.now().toString(36));
    rec.time = new Date().toISOString();
    rec.replaces = (replaces || []).map(function (el) { return el.getAttribute('data-fp-fig'); }).filter(Boolean);
    rec.replaces.forEach(function (fid) {
      var f = D.querySelector('[data-fp-fig="' + fid + '"]');
      if (f) { f.setAttribute('data-fp-replaced', rec.id); f.style.visibility = 'hidden'; }
    });
    S.inserts = (S.inserts || []).filter(function (x) { return x.id !== rec.id; });
    S.inserts.push(rec);
    S.insUndo.push({ type: 'add', id: rec.id });
    save(); renderInsert(rec); reflowSlideOf(rec); place();
  }

  var insPop = D.createElement('div'); insPop.className = 'ci-fp-ins-pop'; insPop.hidden = true; layer.appendChild(insPop);
  insPop.addEventListener('click', function (e) { e.stopPropagation(); });
  var insTarget = null;
  function openInsPop(slideId0, rec) {
    insTarget = { slide: slideId0, rec: rec || null };
    insPop.innerHTML = '<b>画像・表を挿入</b><p>グリッドの区画を選び、画像を貼るか、Excelからコピーした表を貼ります。</p>' +
      '<div class="regs">' +
      [['left', '左半分'], ['right', '右半分'], ['top', '上半分'], ['bottom', '下半分'], ['full', '全面']].map(function (r) {
        var on = rec && rec.region === r[0];
        return '<button type="button" class="ci-fp-btn' + (on ? ' pri' : '') + '" data-reg="' + r[0] + '">' + r[1] + '</button>';
      }).join('') + '</div>' +
      (rec ? '' : '<div class="drop" tabindex="0" data-a="drop">画像をドロップ／クリックして選ぶ／ここに貼り付け</div><input type="file" accept="image/*" hidden>' +
        '<div class="paste-tbl" tabindex="0" data-a="tbl">Excelの表をコピーして、ここをクリックして貼り付け</div>') +
      '<div class="ft"><button type="button" class="ci-fp-btn" data-a="undo">元に戻す</button><span class="sp"></span><button type="button" class="ci-fp-btn" data-a="x">閉じる</button></div>';
    var slide = D.getElementById(slideId0);
    var sq = slide ? rectOf(slide) : { x: 80, y: 80 };
    insPop.style.left = Math.min(sq.x + 40, innerWidth - 420) + 'px';
    insPop.style.top = Math.min(sq.y + 80, innerHeight - 280) + 'px';
    insPop.hidden = false;
    var file = insPop.querySelector('input[type=file]');
    if (file) file.addEventListener('change', function () { if (file.files[0]) ingestImage(file.files[0]); });
    insPop.onkeydown = function (e) {
      if (e.key === 'v' && (e.metaKey || e.ctrlKey)) return;
    };
  }
  function chosenReg() { var b = insPop.querySelector('[data-reg].pri'); return b ? b.getAttribute('data-reg') : 'full'; }
  function askOverlap(slide, region) {
    var hit = figsOverlap(slide, region);
    if (!hit.length) return hit;
    if (confirm('既存の図と重なります。置き換えますか？')) return hit;
    return null;
  }
  function ingestImage(src) {
    var slide = D.getElementById(insTarget.slide); if (!slide) return;
    var region = chosenReg();
    var hit = askOverlap(slide, region); if (hit === null) return;
    function done(dataUrl) {
      var rec = (insTarget.rec && insTarget.rec.type === 'image') ? insTarget.rec : { type: 'image', slide: insTarget.slide, caption: '' };
      rec.region = region; rec.dataUrl = dataUrl; rec.pct = regionPct(slide, region);
      commitInsert(rec, hit); insPop.hidden = true;
    }
    shrinkToWebP(src, done);
  }
  function ingestTable(html, text) {
    var slide = D.getElementById(insTarget.slide); if (!slide) return;
    var region = chosenReg();
    var hit = askOverlap(slide, region); if (hit === null) return;
    var tableHtml = tableFromClipboard(html, text);
    if (!tableHtml) { alert('表として読めませんでした（Excelからコピーして貼り付けてください）'); return; }
    var rec = (insTarget.rec && insTarget.rec.type === 'table') ? insTarget.rec : { type: 'table', slide: insTarget.slide };
    rec.region = region; rec.tableHtml = tableHtml; rec.pct = regionPct(slide, region);
    commitInsert(rec, hit); insPop.hidden = true;
  }
  function shrinkToWebP(src, cb) {
    var img = new Image();
    img.onload = function () {
      var maxW = 1600, maxH = 1200, w = img.naturalWidth || img.width, h = img.naturalHeight || img.height;
      var s = Math.min(1, maxW / w, maxH / h); w = Math.max(1, Math.round(w * s)); h = Math.max(1, Math.round(h * s));
      var c = D.createElement('canvas'); c.width = w; c.height = h;
      c.getContext('2d').drawImage(img, 0, 0, w, h);
      var url = '';
      try { url = c.toDataURL('image/webp', 0.82); } catch (e) { url = ''; }
      if (!url || url.indexOf('image/webp') < 0) { try { url = c.toDataURL('image/jpeg', 0.85); } catch (e2) { url = c.toDataURL('image/png'); } }
      cb(url);
    };
    img.onerror = function () { alert('画像を読めませんでした'); };
    if (typeof src === 'string') img.src = src;
    else if (src && src.type && src.type.indexOf('image/') === 0) {
      var fr = new FileReader(); fr.onload = function () { img.src = fr.result; }; fr.readAsDataURL(src);
    } else if (src && src.type && src instanceof Blob) {
      var fr2 = new FileReader(); fr2.onload = function () { img.src = fr2.result; }; fr2.readAsDataURL(src);
    } else alert('画像を読めませんでした');
  }
  function tableFromClipboard(html, text) {
    var rows = [];
    if (html) {
      try {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var t = doc.querySelector('table');
        if (t) {
          [].slice.call(t.querySelectorAll('tr')).forEach(function (r) {
            var cells = [].slice.call(r.querySelectorAll('th,td')).map(function (c) { return (c.innerText || c.textContent || '').replace(/\r/g, '').replace(/^\s+|\s+$/g, ''); });
            if (cells.length) rows.push(cells);
          });
        }
      } catch (e) { rows = []; }
    }
    if (!rows.length && text) {
      text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n').forEach(function (line) {
        if (line === '') return;
        rows.push(line.split('\t'));
      });
    }
    if (rows.length < 1) return '';
    var w = rows.reduce(function (m, r) { return Math.max(m, r.length); }, 0);
    function cell(s, i, head, first) {
      var cls = first ? 'l' : '';
      var tag = head ? 'th' : 'td';
      return '<' + tag + (cls ? ' class="' + cls + '"' : '') + '>' + esc(s == null ? '' : s) + '</' + tag + '>';
    }
    var thead = '<thead><tr>' + (rows[0].concat(Array(Math.max(0, w - rows[0].length)).fill(''))).slice(0, w).map(function (s, i) { return cell(s, i, true, i === 0); }).join('') + '</tr></thead>';
    var body = rows.slice(1).map(function (r) {
      var cells = r.concat(Array(Math.max(0, w - r.length)).fill(''));
      return '<tr>' + cells.slice(0, w).map(function (s, i) { return cell(s, i, false, i === 0); }).join('') + '</tr>';
    }).join('');
    return '<table class="sk">' + thead + '<tbody>' + body + '</tbody></table>';
  }
  insPop.addEventListener('click', function (e) {
    var reg = e.target.getAttribute('data-reg');
    if (reg) {
      [].slice.call(insPop.querySelectorAll('[data-reg]')).forEach(function (b) { b.classList.toggle('pri', b.getAttribute('data-reg') === reg); });
      if (insTarget && insTarget.rec) {
        var slide = D.getElementById(insTarget.slide);
        var prev = insTarget.rec.region, prevPct = insTarget.rec.pct;
        var hit = askOverlap(slide, reg); if (hit === null) return;
        insTarget.rec.region = reg; insTarget.rec.pct = regionPct(slide, reg);
        S.insUndo.push({ type: 'move', rec: insTarget.rec, prev: prev, prevPct: prevPct });
        (insTarget.rec.replaces || []).forEach(function (fid) {
          var f = D.querySelector('[data-fp-fig="' + fid + '"]');
          if (f) { f.removeAttribute('data-fp-replaced'); f.style.visibility = ''; }
        });
        commitInsert(insTarget.rec, hit || []);
        insPop.hidden = true;
      }
      return;
    }
    var a = e.target.getAttribute('data-a') || (e.target.closest && e.target.closest('[data-a]') && e.target.closest('[data-a]').getAttribute('data-a'));
    if (a === 'x') insPop.hidden = true;
    else if (a === 'undo') undoInsert();
    else if (a === 'drop') { var f = insPop.querySelector('input[type=file]'); if (f) f.click(); }
  });
  insPop.addEventListener('dragover', function (e) { e.preventDefault(); });
  insPop.addEventListener('drop', function (e) {
    e.preventDefault();
    var f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f && f.type.indexOf('image/') === 0) ingestImage(f);
  });
  insPop.addEventListener('paste', function (e) {
    var cd = e.clipboardData; if (!cd) return;
    var img = [].slice.call(cd.items || []).filter(function (i) { return i.type.indexOf('image/') === 0; })[0];
    if (img) { e.preventDefault(); ingestImage(img.getAsFile()); return; }
    var html = cd.getData('text/html') || '', text = cd.getData('text/plain') || '';
    if (html.indexOf('<table') >= 0 || /\t/.test(text) || (text && text.indexOf('\n') >= 0 && text.indexOf('\t') >= 0)) {
      e.preventDefault(); ingestTable(html, text);
    }
  });

  var insBtns = {};
  (function makeInsBtns() {
    [].slice.call(D.querySelectorAll('section.slide')).forEach(function (sec) {
      var id = slideId(sec);
      if (sec.classList.contains('pd-divider') || sec.classList.contains('divider') || sec.getAttribute('data-fp-skip') != null) return;
      if (insBtns[id]) return;
      var b = D.createElement('button'); b.type = 'button'; b.className = 'ci-fp-ins-btn';
      b.textContent = '画像・表を挿入';
      b.title = 'このページのグリッド区画に、画像またはExcelの表を貼る';
      b.addEventListener('click', function (e) { e.stopPropagation(); openInsPop(id, null); });
      layer.appendChild(b); insBtns[id] = b;
    });
  })();
  var _placeTe = placeTeBtns;
  placeTeBtns = function () {
    if (typeof _placeTe === 'function') _placeTe();
    Object.keys(insBtns).forEach(function (id) {
      var b = insBtns[id];
      var sec = D.getElementById(id) || [].slice.call(D.querySelectorAll('section.slide')).filter(function (s) { return slideId(s) === id; })[0];
      if (!sec || !slideVisible(sec)) { b.style.display = 'none'; return; }
      b.style.display = '';
      var sq = rectOf(sec), tw = b.offsetWidth || 110, th = b.offsetHeight || 24;
      var x = railX(sq, tw);
      var te = tePageBtns[id];
      var y = te && te.style.display !== 'none' ? (parseFloat(te.style.top) + (te.offsetHeight || 24) + 8) : (sq.y + 48);
      y = Math.max(6, Math.min(y, innerHeight - th - 6));
      b.style.left = x + 'px'; b.style.top = y + 'px';
    });
  };

  function bakedInsertHtml(rec) {
    var st = rec.pct ? ('left:' + rec.pct.l.toFixed(2) + '%;top:' + rec.pct.t.toFixed(2) + '%;width:' + rec.pct.w.toFixed(2) + '%;height:' + rec.pct.h.toFixed(2) + '%') : '';
    var inner = rec.type === 'image'
      ? ('<figure class="ci-ins-fig"><img src="' + rec.dataUrl + '" alt="' + esc(rec.caption || '') + '" style="object-fit:cover;object-position:center top;width:100%;height:100%;display:block"><figcaption>' + esc(rec.caption || '') + '</figcaption></figure>')
      : ('<div class="ci-ins-table">' + rec.tableHtml + '</div>');
    return '<div class="ci-ins" data-region="' + esc(rec.region) + '" style="position:absolute;box-sizing:border-box;background:var(--white);' + st + '">' + inner + '</div>';
  }

  function stripPickerFrom(root) {
    [].slice.call(root.querySelectorAll('#ci-fp-layer,#ci-fp-bar,#ci-fp-css,#ci-fp-js,#ci-fp-catalog,#ci-fp-photos,.ci-fp-ins-btn,.ci-te-page,.ci-te-btn,.ci-te-pop,.ci-fp-ins-pop,.ci-fp-ins-tools,.ci-fp-preview,.ci-fp-chip,.ci-fp-frame,.ci-fp-pop')).forEach(function (n) { n.remove(); });
    [].slice.call(root.querySelectorAll('.ci-fp-ins')).forEach(function (n) {
      n.className = 'ci-ins';
      var tools = n.querySelector('.ci-fp-ins-tools'); if (tools) tools.remove();
      var cap = n.querySelector('.ci-ins-cap input');
      if (cap) { var fc = D.createElement('figcaption'); fc.textContent = cap.value; cap.parentNode.replaceChild(fc, cap); }
    });
    root.querySelectorAll('[data-fp-fig],[data-fp-page],[data-fp-kind],[data-fp-confirmed],[data-fp-replaced],[data-fp-deck],[data-fp-skip],[data-ci-fp],[data-te],[data-ci-te-slide]').forEach(function (n) {
      ['data-fp-fig', 'data-fp-page', 'data-fp-kind', 'data-fp-confirmed', 'data-fp-replaced', 'data-fp-deck', 'data-fp-skip', 'data-ci-fp', 'data-te', 'data-ci-te-slide'].forEach(function (a) { n.removeAttribute(a); });
    });
    if (root.documentElement) {
      root.documentElement.removeAttribute('data-ci-fp');
      root.documentElement.removeAttribute('data-fp-deck');
      root.documentElement.classList.remove('ci-fp-rail', 'ci-fp-hidden', 'ci-te-mode', 'ci-fp-static');
      root.documentElement.style.removeProperty('--ci-fp-rail');
    }
    if (root.body) { root.body.style.paddingRight = ''; }
    root.querySelectorAll('.ci-fp-reflowing').forEach(function (n) { n.classList.remove('ci-fp-reflowing'); n.classList.add('ci-reflowing'); n.removeAttribute('data-fp-reflow-region'); });
    root.querySelectorAll('.ci-fp-reflow-tight').forEach(function (n) { n.classList.remove('ci-fp-reflow-tight'); n.classList.add('ci-reflow-tight'); });
    root.querySelectorAll('.ci-fp-reflowed').forEach(function (n) { n.classList.remove('ci-fp-reflowed'); n.classList.add('ci-reflowed'); n.removeAttribute('data-fp-reflow-tmp'); });
    root.querySelectorAll('.ci-fp-kr-stack').forEach(function (n) { n.classList.remove('ci-fp-kr-stack'); n.classList.add('ci-kr-stack'); });
    root.querySelectorAll('[data-fp-reflow-tmp]').forEach(function (n) { n.removeAttribute('data-fp-reflow-tmp'); });
  }

  function applyMarksOn(root, applyNumbers) {
    var held = [];
    [].slice.call(root.querySelectorAll('.ci-te-mark')).forEach(function (m) {
      var ed = (S.edits || []).filter(function (x) { return x.id === m.getAttribute('data-te'); })[0];
      var nums = (ed && ed.numbers) || m.classList.contains('num');
      var text;
      if (nums && !applyNumbers) { text = m.getAttribute('data-old') || (m.querySelector('del') && m.querySelector('del').textContent) || ''; held.push(ed || { old: text }); }
      else { text = (m.querySelector('ins') && m.querySelector('ins').textContent) || ''; }
      m.parentNode.replaceChild(root.createTextNode ? root.createTextNode(text) : D.createTextNode(text), m);
    });
    return held;
  }

  function serializeDoc(doc) {
    var html = '<!DOCTYPE html>\n' + doc.documentElement.outerHTML;
    html = html.replace(new RegExp('<!--ci-fp:'+'begin-->[\\s\\S]*?<!--ci-fp:'+'end-->','g'), '');
    html = html.replace(/\s+data-fp-[\w-]+(="[^"]*")?/g, '');
    html = html.replace(/\s+data-ci-fp(="[^"]*")?/g, '');
    html = html.replace(/\s*\bci-fp-(hidden|static|rail)\b/g, '');
    html = html.replace(/\s+data-te(="[^"]*")?/g, '');
    html = html.replace(/\s+data-old(="[^"]*")?/g, '');
    return html;
  }

  function warnedNumbers() {
    return (S.edits || []).filter(function (e) { return e.numbers; });
  }

  function buildAppliedHtml(opts) {
    opts = opts || {};
    var held = warnedNumbers();
    var html0 = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    var doc = new DOMParser().parseFromString(html0, 'text/html');
    Object.keys(S.figures || {}).forEach(function (id) {
      var f = S.figures[id];
      if (f && f.confirmed && f.confirmed.html) {
        var el = doc.querySelector('[data-fp-fig="' + id + '"]');
        if (el) {
          el.innerHTML = f.confirmed.html;
          if (f.confirmed.photo && f.confirmed.style) el.setAttribute('style', f.confirmed.style);
          var lg = el.nextElementSibling;
          if (lg && (lg.classList.contains('legend') || (lg.tagName === 'P' && /\blegend\b/.test(lg.className)))) {
            lg.classList.add('ci-legacy-legend-off'); lg.setAttribute('hidden', '');
          }
        }
      }
    });
    doc.querySelectorAll('.ci-fp-preview-in').forEach(function (n) { n.remove(); });
    applyMarksOn(doc, !!opts.allowNumbers);
    (S.inserts || []).forEach(function (rec) {
      var slide = doc.getElementById(rec.slide);
      if (!slide) return;
      if (!doc.querySelector('.ci-fp-ins[data-ins="' + rec.id + '"]') && !doc.querySelector('.ci-ins[data-region][data-ins="' + rec.id + '"]')) {
        slide.insertAdjacentHTML('beforeend', bakedInsertHtml(rec));
      }
      (rec.replaces || []).forEach(function (fid) {
        var f = doc.querySelector('[data-fp-fig="' + fid + '"]');
        if (f) f.remove();
      });
    });
    stripPickerFrom(doc);
    if (doc.head && !doc.getElementById('ci-ins-css')) {
      var st = doc.createElement('style'); st.id = 'ci-ins-css';
      st.textContent = '.ci-ins{position:absolute;box-sizing:border-box;overflow:hidden}.ci-ins-fig{margin:0;width:100%;height:100%;display:flex;flex-direction:column}.ci-ins-fig img{flex:1;min-height:0;object-fit:cover;object-position:center top;width:100%;height:100%;display:block}.ci-ins-fig figcaption{font-size:11px;color:var(--ink-60);padding:2px 4px;flex:none}.ci-ins-table{width:100%;height:100%;overflow:auto;padding:4px;box-sizing:border-box}.ci-legacy-legend-off,[hidden].legend,p.legend[hidden]{display:none !important}.slide.ci-reflowing .sgrp-row{display:flex;flex-direction:column;align-items:stretch;gap:2px;padding-top:2px}.slide.ci-reflowing .sgrp-row::before,.slide.ci-reflowing .okr li::before,.slide.ci-reflowing .okr li::after,.slide.ci-reflowing .okr ul ul::before{display:none}.slide.ci-reflowing .okr ul{padding-top:2px}.slide.ci-reflowing .okr li{padding:2px 0 0}.slide.ci-reflowing .okr .nd.cat{display:flex;flex-direction:row;flex-wrap:wrap;align-items:center;gap:3px;min-width:0}.slide.ci-reflowing .okr .nd.cat .nm{min-height:0;flex:0 0 7em;flex-direction:row;align-items:center;justify-content:flex-start;gap:3px;margin:0}.slide.ci-reflowing .okr .nd.cat .nm img{height:16px !important;width:auto;margin:0 !important}.slide.ci-reflowing .okr .box{height:auto !important;min-height:0;padding:0 5px;margin:0;white-space:nowrap}.slide.ci-reflowing .okr .box .lbl{width:auto;margin-right:3px}.slide.ci-reflowing .okr .trend{margin:0;flex:1 1 auto}.slide.ci-reflowing .okr .nd.big{min-width:0}.slide.ci-reflowing .okr .nd.big .nm{min-height:0;margin-bottom:1px}.slide.ci-reflowing .okr .nd.big .box{padding:2px 8px;margin-top:1px;white-space:normal}.slide.ci-reflowing .kr-band{display:flex;flex-direction:row;flex-wrap:nowrap;gap:4px;align-items:flex-start}.slide.ci-reflowing .kr-band.ci-kr-stack{flex-direction:column;align-items:stretch}.slide.ci-reflowing .kr{flex:1 1 0;min-width:0;padding:2px 6px;box-sizing:border-box}.slide.ci-reflowing .kr-band.ci-kr-stack .kr{flex:0 0 auto;width:100%;max-width:100%}.slide.ci-reflowing .okr-insight{display:flex;flex-direction:column;flex-wrap:nowrap;gap:2px;padding:2px 8px;align-items:flex-start}.slide.ci-reflowing .okr-insight .ins-txt{min-width:0;width:100%}.slide.ci-reflowing .t-note{margin:0 !important;line-height:1.3}.ci-reflowed{box-sizing:border-box}.slide.ci-reflow-tight .kr{padding:0 4px}.slide.ci-reflow-tight .kr .kr-n,.slide.ci-reflow-tight .kr .kr-v,.slide.ci-reflow-tight .kr .kr-s{line-height:1.2;margin:0}.slide.ci-reflow-tight .okr-insight{padding:1px 6px}.slide.ci-reflow-tight .okr-insight .ins-txt{line-height:1.3}.slide.ci-reflow-tight .sgrp-row{gap:1px;padding-top:0}.slide.ci-reflow-tight .sgrp-row > *{gap:1px;line-height:1.2;margin:0}.slide.ci-reflow-tight .okr li{padding:0}.slide.ci-reflow-tight .okr ul{padding-top:0}';
      doc.head.appendChild(st);
    }
    var after = tableSigOf(doc);
    var broken = [];
    if (TABLE0.length !== after.length) broken.push('表の数 ' + TABLE0.length + '→' + after.length);
    // inserted tables are extra — allow more tables if inserts added some
    var added = (S.inserts || []).filter(function (x) { return x.type === 'table'; }).length;
    if (after.length !== TABLE0.length && after.length !== TABLE0.length + added) broken.push('表の数が照合できません');
    else {
      TABLE0.forEach(function (b, i) {
        var c = after[i]; if (!c) return;
        if (b.rows !== c.rows || b.ncells.join() !== c.ncells.join()) broken.push('表' + (i + 1) + ' 行・セル数');
        if (b.hdr_last !== c.hdr_last) broken.push('表' + (i + 1) + ' ヘッダー最終列');
        if (b.col1.join('\n') !== c.col1.join('\n')) broken.push('表' + (i + 1) + ' 1列目の並び');
      });
    }
    return { html: serializeDoc(doc), held: held, broken: broken, warnings: held.map(function (e) { return '要確認（数字を含むので当てていない）: 「' + (e.old || '') + '」→「' + (e.new || '') + '」'; }) };
  }
  function buildConfirmedHtml() { return buildAppliedHtml().html; }
  function exportApplied(opts) {
    opts = opts || {};
    var selWarn = confirmSelectionsForExport();
    var r = buildAppliedHtml(opts);
    r.selectionWarnings = selWarn;
    if (r.broken.length) {
      if (!opts.silent) alert('表の照合に合わないため書き出しません:\n' + r.broken.join('\n'));
      return r;
    }
    var notes = selWarn.concat(r.warnings || []);
    if (notes.length && !opts.silent) alert(notes.join('\n'));
    if (!opts.silent) downloadBlob(deckBase() + '_修正反映.html', r.html);
    return r;
  }
  function checkFigNumbers(id) {
    var el = D.querySelector('[data-fp-fig="' + id + '"]');
    var data = extractData(el);
    var f = fig(id); if (!f.confirmed) return { ok: false, reason: '未確定' };
    var raws = [];
    (data.series || []).forEach(function (s) { s.raws.forEach(function (r) { if (r && r !== '—') raws.push(r); }); });
    var text = (f.confirmed.html || '') + (el ? el.textContent : '');
    var cells = raws.concat((data.series || []).map(function (s) { return s.name; }), data.cats || []);
    var placed = [];
    (f.confirmed.html || '').replace(/>([^<]+)</g, function (_, s) { placed.push(s); });
    var extra = placed.filter(function (s) {
      var t = String(s).replace(/\s+/g, ' ').trim();
      if (!/[0-9０-９]/.test(t)) return false;
      if (/^¥?\d+M$/.test(t) || /^0$/.test(t)) return false; // 軸目盛り
      if (/^\d+(\.\d+)?%$/.test(t) && cells.indexOf(t) < 0) return false; // 軸の%
      if (cells.indexOf(t) >= 0) return false;
      if (cells.some(function (c) { return c && (c === t || c.indexOf(t) >= 0 || t.indexOf(c) >= 0); })) return false;
      return t.length > 1;
    });
    var shown = placed.filter(function (s) { return /[¥￥]|\d[,，]\d/.test(s); });
    var shownOk = shown.filter(function (s) { return cells.indexOf(s) >= 0; });
    return { ok: extra.length === 0 && shown.length === shownOk.length && shown.length > 0, missing: [], extra: extra, shown: shown, shownOk: shownOk, placed: placed, raws: raws };
  }

  renderAllInserts();

  window.CIFP = { state: function () { return S; }, open: open, preview: showPreview, hidePreview: hidePreview, toggle: toggle, place: place, undoEdit: undo, importJSON: importJSON, confirm: applyConfirm, undoConfirm: undoConfirm, exportConfirmed: buildConfirmedHtml, exportApplied: exportApplied, confirmSelections: confirmSelectionsForExport, applied: buildAppliedHtml, addInsert: commitInsert, applyReflow: applyReflow, clearReflow: clearReflow, remainBox: remainBox, contentBox: contentBox, markup: figMarkup, checkFigNumbers: checkFigNumbers, figSize: figSize, photo: applyPhoto, photoAct: photoAct, photos: function () { return Object.keys(PHOTOS); }, extractOkr: extractOkr, canDrawOkr: canDrawOkr, recSets: recSets, shortName: shortName, OKR_ID: OKR_ID };
  restore(); teRestore(); restorePhotos();
})();
