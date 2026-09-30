#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIスライド 視覚回帰チェック（計算済みスタイル＋構造シグネチャ方式）

各 .slide の「寸法・地色/文字色・隅ロゴ幅・見出しサイズ・φ型スケール・KPI/表/段数」を
headless Chrome の computed style から抽出して JSON シグネチャ化し、基準(baseline)と比較する。

なぜピクセルPNG差分でないか:
  - マシンごとにフォント描画が異なり、ピクセル比較は誤検知が多く移植性が低い。
  - 本ツールは CSS の computed 値（px/色）を比較するので決定論的・マシン非依存で、
    今回の「隅ロゴ 64px↔102px」のような構造/スタイルのドリフトを確実に検出できる。

使い方:
  slide_visual_regression.py <file.html>                       # baseline と比較
  slide_visual_regression.py <file.html> --update-baseline     # baseline を更新（承認後）
  slide_visual_regression.py <file.html> --baseline <path.json>
出力:  OK / DRIFT <slide番号:項目 基準≠現在> ...
環境:  CHROME_BIN で Chrome/Chromium パス上書き可。
"""
import sys, os, json, base64, re, subprocess, tempfile, pathlib, urllib.parse, argparse

CHROME = os.environ.get("CHROME_BIN", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_BASELINE = HERE / "baseline" / "template_signature.json"

PROBE = r"""
<script>
window.addEventListener('load', function () {
  function fs(sel){ var e=document.querySelector(sel); return e?Math.round(parseFloat(getComputedStyle(e).fontSize)):null; }
  var sig = { typo:{}, sections:[] };
  ['.t-xl','.t-lg','.t-md','.t-body','.t-note','.kicker','.lead'].forEach(function(s){ sig.typo[s]=fs(s); });
  document.querySelectorAll('.slide').forEach(function (s) {
    var corner=s.querySelector('svg.corner'), title=s.querySelector('h2.title'), cs=getComputedStyle(s);
    sig.sections.push({
      cls: s.className.trim(),
      w: s.clientWidth, h: s.clientHeight,
      bg: cs.backgroundColor, color: cs.color,
      corner: corner ? Math.round(corner.getBoundingClientRect().width) : null,
      title_fs: title ? Math.round(parseFloat(getComputedStyle(title).fontSize)) : null,
      kpis: s.querySelectorAll('.kpi').length,
      rows: s.querySelectorAll('tbody tr').length,
      cols: s.querySelectorAll('.cols > div').length
    });
  });
  document.title = 'SIG:' + btoa(unescape(encodeURIComponent(JSON.stringify(sig))));
});
</script>
"""


def signature(path: pathlib.Path) -> dict:
    html = path.read_text()
    probe_html = html.replace('</body>', PROBE + '</body>') if '</body>' in html else html + PROBE
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, dir=str(path.parent)) as tf:
        tf.write(probe_html)
        tmp = pathlib.Path(tf.name)
    try:
        url = 'file://' + urllib.parse.quote(str(tmp)) + '#static'  # #static＝動く資料（v3.9）を組み上がった最終状態で開く。静的デッキでは何もしない
        r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox', '--dump-dom',
                            '--virtual-time-budget=4000', url], capture_output=True, text=True, timeout=60)
        m = re.search(r'SIG:([A-Za-z0-9+/=]+)', r.stdout)
        if not m:
            raise SystemExit('ERROR: signature を取得できません（Chrome パス/CHROME_BIN を確認）')
        return json.loads(base64.b64decode(m.group(1)).decode('utf-8'))
    finally:
        tmp.unlink(missing_ok=True)


NUM = ('w', 'h', 'corner', 'title_fs')
EXACT = ('cls', 'bg', 'color', 'kpis', 'rows', 'cols')


def diff(base: dict, cur: dict) -> list[str]:
    out = []
    for k in base.get('typo', {}):
        b, c = base['typo'].get(k), cur.get('typo', {}).get(k)
        if b != c:
            out.append(f'typo {k}: {b}≠{c}')
    bs, csz = base.get('sections', []), cur.get('sections', [])
    if len(bs) != len(csz):
        out.append(f'section数: {len(bs)}≠{len(csz)}')
    for i, (b, c) in enumerate(zip(bs, csz), 1):
        for k in NUM:
            if b.get(k) is None or c.get(k) is None:
                if b.get(k) != c.get(k):
                    out.append(f'slide{i} {k}: {b.get(k)}≠{c.get(k)}')
            elif abs(b[k] - c[k]) > 1:  # 1px のサブピクセル許容
                out.append(f'slide{i} {k}: {b[k]}≠{c[k]}')
        for k in EXACT:
            if b.get(k) != c.get(k):
                out.append(f'slide{i} {k}: {b.get(k)}≠{c.get(k)}')
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('html')
    ap.add_argument('--baseline', default=str(DEFAULT_BASELINE))
    ap.add_argument('--update-baseline', action='store_true')
    a = ap.parse_args()
    sig = signature(pathlib.Path(a.html))
    bpath = pathlib.Path(a.baseline)
    if a.update_baseline:
        bpath.parent.mkdir(parents=True, exist_ok=True)
        bpath.write_text(json.dumps(sig, ensure_ascii=False, indent=1))
        print(f'baseline 更新: {bpath}（sections={len(sig["sections"])}）')
        return 0
    if not bpath.is_file():
        print(f'WARN: baseline が無い（{bpath}）。--update-baseline で作成してください。')
        return 0
    base = json.loads(bpath.read_text())
    d = diff(base, sig)
    if d:
        print('DRIFT ' + ' / '.join(d))
        return 1
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
