#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CIスライドのはみ出し検査
各 .slide の scrollHeight が clientHeight(=720px固定) を超えていないかを
headless Chrome で実測する。編集後は必ず実行すること（ガイドライン§5.6）。

使い方: python3 slide_overflow_check.py <file.html> [<file2.html> ...]
        --json   … 1ファイル1行の JSON（JSON Lines）で出す。**下流ツールはこれを使う**
        --lines  … 所見を1件1行で出す（各行に OVERFLOW/LOGO/COVER_CI/TITLE を前置）
出力:   OK or OVERFLOW slide番号:+超過px

**下流ツールは既定の1行書式を正規表現で拾わないこと**（v3.8 追加・B-5）:
  既定書式は1行に全件をまとめるため、`OVERFLOW (\\d+):` のような正規表現では
  先頭1件しか取れない。実際に英語版ビルダーがこれで 20頁中19頁のはみ出しを
  取りこぼし、「はみ出しゼロ」と誤って扱った事故が起きている。
  機械で読むときは必ず `--json`（下記スキーマ）を使う。

--json のスキーマ（1ファイル1行）:
  {"file":"deck.html", "ok":false,
   "slides":[{"n":2,"over_px":106,"kind":"v"},          # kind: v=縦 / h=横
             {"n":3,"kind":"clip","tag":"TABLE"}],       # clip=overflow:hidden で切れ
   "logo":[{"n":5,"width_px":130}],                      # 隅ロゴ過大（正準102px）
   "cover_ci":[1],                                       # 表紙にCIコンセプト(.cover-ci)なし
   "title_lines":[{"n":7,"lines":3}],                    # 見出しが3行に折り返した（v3.8・B-2）
   "pagerefs":[{"n":14,"text":"14ページ"}],               # ページ番号の直書き（v3.8・B-1）
   "notes":["TITLE? …"]}                                 # 非ゲートのヒューリスティック

非ゲートの警告（表示のみ・終了コードに影響しない）:
  TITLE_LINES?  h2.title が3行以上に折り返している。**見出しは全角45字程度まで（2行以内）**が目安
                （実測で全角46字前後が3行の境目）。あふれの原因が見出しであることを名指しする
  PAGEREF?      「14ページ」「P14」「次ページ」等の直書き。ページを並べ替えると参照が全部ずれるため、
                ci_pagerefs.py の {{PG:タイトル}} で解決する（解決済みの参照には鳴らない）
"""
import sys, os, glob, json, shutil, pathlib, subprocess, tempfile, re, urllib.parse


def find_chrome() -> str:
    """Chrome/Chromium を自動探索（Mac → Playwright 同梱 → PATH）。
    従来は Mac パス決め打ちで、ファイナライザ/CI (Linux) では必ず失敗していた。
    探索順は scripts/html_to_pptx.py / ci-finalize.sh と同一。"""
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    pw = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "/opt/pw-browsers")
    candidates += sorted(glob.glob(f"{pw}/chromium-*/chrome-linux/chrome"))
    candidates += sorted(glob.glob(f"{pw}/chromium_headless_shell-*/chrome-linux/headless_shell"))
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    sys.exit("ERROR: Chrome/Chromium が見つかりません（Mac は Google Chrome を、"
             "Linux は chromium か PLAYWRIGHT_BROWSERS_PATH を用意してください）。")


CHROME = find_chrome()
PROBE = """
<script>
window.addEventListener('load', () => {
  const out = [];
  const logo = [];
  document.querySelectorAll('.slide').forEach((s, i) => {
    const over = s.scrollHeight - s.clientHeight;
    if (over > 2) out.push((i + 1) + ':+' + over + 'px');
    // 横方向のあふれ（2026-07-07 現場報告: 縦のみ検査の死角でテーブル右列見切れがすり抜けた）
    const overX = s.scrollWidth - s.clientWidth;
    if (overX > 2) out.push((i + 1) + ':+' + overX + 'px(横)');
    // overflow:hidden で「あふれず隠れて切れる」ケース: 固有幅を持つ子孫の右端がスライド右端を越えていないか
    const sr = s.getBoundingClientRect().right;
    s.querySelectorAll('table,svg,img').forEach(el => {
      if (el.getBoundingClientRect().right - sr > 2) out.push((i + 1) + ':clip(' + el.tagName + ')');
    });
    // 隅ロゴ幅ガード: 正準=102px（CI v2・V3実デッキ準拠）。表紙(cover)の cf-logo は除外。
    const lg = s.querySelector('svg.corner, .corner-logo, .hd, svg.cc-logo, .lockup');
    if (lg && !s.matches('.cover-full, .cover-card')) {
      const w = Math.round(lg.getBoundingClientRect().width);
      if (w > 112) logo.push((i + 1) + ':' + w + 'px');
    }
  });
  // 表紙CIコンセプト必須（V3.2_FORMAT・全CIスライド規則）: 表紙(cover-full・章扉 pd-divider 除く)
  // に .cover-ci があるか。無ければ流用ミス/未対応を表示（TITLE? と同じく非ゲート・目視差し戻し用）。
  const coverci = [];
  const slides = [...document.querySelectorAll('.slide')];
  document.querySelectorAll('.cover-full:not(.pd-divider)').forEach((s) => {
    if (!s.querySelector('.cover-ci')) coverci.push(slides.indexOf(s) + 1);
  });
  // 見出しの折り返し行数（v3.8・B-2）: 用語を正式名に直すと見出しが伸び、2行想定が3行になって
  // ページが溢れる。あふれ検査は「溢れた」ことしか分からず、原因が見出しだと特定できなかった。
  const tline = [];
  slides.forEach((s, i) => {
    const t = s.querySelector('h2.title');
    if (!t) return;
    const lh = parseFloat(getComputedStyle(t).lineHeight);
    if (!lh || !isFinite(lh)) return;
    const n = Math.round(t.getBoundingClientRect().height / lh);
    if (n >= 3) tline.push((i + 1) + ':' + n);
  });
  document.title = 'OVERFLOW_REPORT[' + out.join(',') + ']!LOGO_REPORT[' + logo.join(',')
                 + ']!COVERCI_REPORT[' + coverci.join(',') + ']!TITLELINE_REPORT[' + tline.join(',') + ']';
});
</script>
"""

# ---------------------------------------------------------------- 所見の構造化（v3.8・B-5）
# 既定の1行書式は人が読むためのもの。機械可読が要る下流ツール向けに、probe の出力を
# ここで構造化してから書式化する（表示書式が変わっても --json のスキーマは変わらない）。
_RE_V = re.compile(r'^(\d+):\+(\d+)px$')
_RE_H = re.compile(r'^(\d+):\+(\d+)px\(横\)$')
_RE_CLIP = re.compile(r'^(\d+):clip\(([^)]*)\)$')
_RE_LOGO = re.compile(r'^(\d+):(\d+)px$')
_RE_TLINE = re.compile(r'^(\d+):(\d+)$')

# ---- ページ参照の直書き検出（v3.8・B-1）--------------------------------------
# VERSION は「ページ参照は ci_pagerefs.py の {{PG:タイトル}} で解決（直書き禁止）」と規定しているが、
# **守られたかを機械で確認する手段が無かった**。実際に OPI 版・ULTIME 版とも「（14ページ）」を
# 直書きしており、ページを並べ替えたときに参照が全部ずれた（気付けたのは目視のみ）。
# ci_pagerefs.py が解決した番号は <span class="pgref">N</span> で包まれるため、ここでは
# **それを除いてから**探す＝正しい参照には鳴らない（鳴り続ける警告は無視されるようになるため）。
_PGREF_SPAN = re.compile(r'<span class="pgref">.*?</span>', re.S)
_TAGS = re.compile(r'<(script|style)\b.*?</\1>|<[^>]+>', re.S | re.I)
_PGREF_PATTERNS = [
    re.compile(r'\d+\s*ページ'),
    re.compile(r'(?<![A-Za-z])[PpＰｐ]\s*\.?\s*\d+'),
    re.compile(r'次のページ|次ページ|前のページ|前ページ'),
]
# 本文で普通に出る言い回し（ページ番号の直書きではない）は除外する
_PGREF_ALLOW = ('1ページ1メッセージ', 'ページ数', 'ページ目安', '1ページに')


def _pageref_notes(html: str) -> list:
    """スライドごとに、ページ番号の直書きと思われる箇所を拾う（非ゲート・警告）。"""
    parts = re.split(r'(?=<section[^>]*class="[^"]*\bslide\b)', html)
    found = []
    n = 0
    for part in parts:
        if not re.match(r'<section[^>]*class="[^"]*\bslide\b', part):
            continue
        n += 1
        text = _TAGS.sub(' ', _PGREF_SPAN.sub(' ', part))
        for allow in _PGREF_ALLOW:
            text = text.replace(allow, ' ')
        for pat in _PGREF_PATTERNS:
            m = pat.search(text)
            if m:
                found.append({'n': n, 'text': m.group(0).strip()})
                break
    return found

# 版サフィックス（やさしい版・英語版など）は主題ではないので、<title> 照合の前に落とす
_VER_SUFFIX = re.compile(r'[_\-]?(EN|en|ja|JA|plain|PLAIN|やさしい版|英語版|日本語版|簡易版)$')
_TITLE_STOP = {'スライド', 'シート', '資料', 'さん', 'ため', 'こと', '全社', '共有', '版'}
_LATIN_STOP = {'wip', 'ci', 'html', 'ver', 'draft', 'final', 'en', 'ja', 'plain', 'copy'}


def _parse_findings(out: str, logo: str, coverci: str, tline: str = '') -> dict:
    """probe が返した文字列を構造化する。未知の書式は raw として落とさず残す。"""
    slides, logos, raw = [], [], []
    titles = []
    for tok in [t for t in tline.split(',') if t]:
        if (m := _RE_TLINE.match(tok)):
            titles.append({'n': int(m.group(1)), 'lines': int(m.group(2))})
        else:
            raw.append(tok)
    for tok in [t for t in out.split(',') if t]:
        if (m := _RE_V.match(tok)):
            slides.append({'n': int(m.group(1)), 'over_px': int(m.group(2)), 'kind': 'v'})
        elif (m := _RE_H.match(tok)):
            slides.append({'n': int(m.group(1)), 'over_px': int(m.group(2)), 'kind': 'h'})
        elif (m := _RE_CLIP.match(tok)):
            slides.append({'n': int(m.group(1)), 'kind': 'clip', 'tag': m.group(2)})
        else:
            raw.append(tok)
    for tok in [t for t in logo.split(',') if t]:
        if (m := _RE_LOGO.match(tok)):
            logos.append({'n': int(m.group(1)), 'width_px': int(m.group(2))})
        else:
            raw.append(tok)
    cover = [int(t) for t in coverci.split(',') if t.strip().isdigit()]
    return {'slides': slides, 'logo': logos, 'cover_ci': cover, 'raw': raw, 'title_lines': titles}


def _title_notes(html: str, stem: str) -> list:
    """<title> がファイル名の主題と無関係＝head 流用時の更新漏れを検出（非ゲート）。

    v3.8（B-8）: 英語版・やさしい版で**必ず鳴る**問題を修正した。
      - 版サフィックス（_EN / _やさしい版 …）はファイル名から落としてから照合する
      - 英語のタイトルは日本語トークンを持たないため、従来は必ず不一致になっていた。
        ラテン文字トークン（WELLA・ProHair 等）でも照合し、どちらかが一致すれば OK とする
    毎回鳴る警告は無視される運用になり、警告そのものが形骸化するため。
    """
    tm = re.search(r'<title>(.*?)</title>', html, re.S)
    if not tm:
        return []
    title = tm.group(1).strip()
    if '__DOC_TITLE__' in title:
        return ['TITLE? <title> がテンプレ未置換（__DOC_TITLE__ のまま）']
    if not title:
        return []
    base = _VER_SUFFIX.sub('', re.sub(r'\d{6,8}', '', stem))
    jp = lambda s: set(re.findall(r'[一-龥ぁ-んァ-ヶ]{2,}', s)) - _TITLE_STOP
    lat = lambda s: {t.lower() for t in re.findall(r'[A-Za-z][A-Za-z0-9]{2,}', s)} - _LATIN_STOP
    fj, tj, fl, tl = jp(base), jp(title), lat(base), lat(title)
    if not fj:                  # 発火条件は従来どおり（ファイル名に日本語の主題語があるときだけ）。
        return []               # ラテン一致は「鳴らさない」側にだけ効かせ、警告を増やさない
    if (fj & tj) or (fl & tl):  # 日本語・ラテンのどちらかが一致すれば流用ではない
        return []
    return [f'TITLE? <title>「{title[:24]}」がファイル名と不一致（テンプレ流用の更新漏れ?）']


def analyze(path: pathlib.Path) -> dict:
    """1ファイルを検査し、構造化した結果を返す（書式化は format_* 側）。"""
    res = check(path, structured=True)
    return res


def format_text(res: dict) -> str:
    """従来どおりの1行書式（後方互換・人が読む用）。"""
    if res.get('error'):
        return res['error']
    msgs = []
    toks = []
    for s in res['slides']:
        if s['kind'] == 'v':
            toks.append(f"{s['n']}:+{s['over_px']}px")
        elif s['kind'] == 'h':
            toks.append(f"{s['n']}:+{s['over_px']}px(横)")
        else:
            toks.append(f"{s['n']}:clip({s['tag']})")
    toks += res.get('raw', [])
    if toks:
        msgs.append('OVERFLOW ' + ','.join(toks))
    if res['logo']:
        msgs.append('LOGO>112px ' + ','.join(f"{l['n']}:{l['width_px']}px" for l in res['logo']))
    if res['cover_ci']:
        msgs.append('COVER_CI? 表紙にCIコンセプト(.cover-ci)なし slide:'
                    + ','.join(str(n) for n in res['cover_ci']))
    for t in res.get('title_lines', []):
        msgs.append(f'TITLE_LINES? 見出しが{t["lines"]}行に折り返し slide:{t["n"]}'
                    '（全角45字程度・2行以内が目安）')
    for g in res.get('pagerefs', []):
        msgs.append(f'PAGEREF? ページ番号の直書き「{g["text"]}」 slide:{g["n"]}'
                    '（ci_pagerefs.py の {{PG:タイトル}} を使う）')
    msgs += res['notes']
    return ' / '.join(msgs) if msgs else 'OK'


def format_lines(res: dict) -> list:
    """1件1行（各行に種別を前置）。正規表現で拾う下流でも取りこぼさない書式。"""
    name = res['file']
    if res.get('error'):
        return [f'{name}: {res["error"]}']
    out = []
    for s in res['slides']:
        if s['kind'] == 'clip':
            out.append(f'{name}: OVERFLOW {s["n"]}:clip({s["tag"]})')
        else:
            axis = '縦' if s['kind'] == 'v' else '横'
            out.append(f'{name}: OVERFLOW {s["n"]}:+{s["over_px"]}px({axis})')
    for t in res.get('raw', []):
        out.append(f'{name}: OVERFLOW {t}')
    for l in res['logo']:
        out.append(f'{name}: LOGO>112px {l["n"]}:{l["width_px"]}px')
    for n in res['cover_ci']:
        out.append(f'{name}: COVER_CI? 表紙にCIコンセプト(.cover-ci)なし slide:{n}')
    for t in res.get('title_lines', []):
        out.append(f'{name}: TITLE_LINES? 見出しが{t["lines"]}行に折り返し slide:{t["n"]}'
                   '（全角45字程度・2行以内が目安）')
    for g in res.get('pagerefs', []):
        out.append(f'{name}: PAGEREF? ページ番号の直書き「{g["text"]}」 slide:{g["n"]}'
                   '（ci_pagerefs.py の {{PG:タイトル}} を使う）')
    for note in res['notes']:
        out.append(f'{name}: {note}')
    return out or [f'{name}: OK']


def is_bad(res: dict) -> bool:
    """ゲート判定。幾何学的NG（あふれ・ロゴ過大）と検査不能のみ落とす（TITLE? は表示のみ）。"""
    return bool(res.get('error') or res['slides'] or res.get('raw') or res['logo'])


def check(path: pathlib.Path, structured: bool = False):
    html = path.read_text()
    probe_html = html.replace('</body>', PROBE + '</body>') if '</body>' in html else html + PROBE
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, dir=str(path.parent)) as tf:
        tf.write(probe_html)
        tmp = pathlib.Path(tf.name)
    try:
        url = 'file://' + urllib.parse.quote(str(tmp))
        # --no-sandbox: CI コンテナ等 root 実行時に必須（Mac では無害）
        r = subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-sandbox',
                            '--dump-dom', '--virtual-time-budget=4000', url],
                           capture_output=True, text=True, timeout=60)
        m = re.search(r'OVERFLOW_REPORT\[([^\]]*)\]', r.stdout)
        if not m:
            err = 'ERROR: report not found'
            return {'file': path.name, 'path': str(path), 'ok': False, 'error': err,
                    'slides': [], 'logo': [], 'cover_ci': [], 'notes': [], 'raw': [],
                    'title_lines': [], 'pagerefs': []} \
                if structured else err
        lm = re.search(r'LOGO_REPORT\[([^\]]*)\]', r.stdout)
        cm = re.search(r'COVERCI_REPORT\[([^\]]*)\]', r.stdout)
        tm = re.search(r'TITLELINE_REPORT\[([^\]]*)\]', r.stdout)
        res = _parse_findings(m.group(1),
                              lm.group(1) if lm else '',
                              cm.group(1) if cm else '',
                              tm.group(1) if tm else '')
        res['pagerefs'] = _pageref_notes(html)
        res['notes'] = _title_notes(html, path.stem)
        res['file'] = path.name
        res['path'] = str(path)
        # ok は**ゲート判定と一致**させる（終了コードと同義）。cover_ci / notes は非ゲートの
        # 所見なので ok を false にしない（下流が「落ちた」と誤読するため）。
        res['ok'] = not is_bad(res)
        return res if structured else format_text(res)
    finally:
        tmp.unlink(missing_ok=True)

if __name__ == '__main__':
    # 幾何学的 NG（はみ出し・ロゴ過大）と検査不能は exit 1（gate として機能させる）。
    # TITLE? は流用ミスのヒューリスティックなので表示のみ（exit 0）。
    args = sys.argv[1:]
    as_json = '--json' in args
    as_lines = '--lines' in args
    files = [a for a in args if not a.startswith('--')]
    if not files:
        sys.exit('使い方: python3 slide_overflow_check.py <file.html> [...] [--json|--lines]')
    bad = 0
    for p in files:
        res = analyze(pathlib.Path(p))
        if as_json:
            # JSON Lines（1ファイル1行）。1ファイルなら json.loads() でそのまま読める
            print(json.dumps(res, ensure_ascii=False))
        elif as_lines:
            print('\n'.join(format_lines(res)))
        else:
            print(f'{res["file"]}: {format_text(res)}')
        if is_bad(res):
            bad = 1
    sys.exit(bad)
