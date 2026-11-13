#!/usr/bin/env python3
"""fp_build.py — 図の型ピッカー（社内版）の付け外し（CI kit 試作 2026-11-11）

  社内版: python3 fp_build.py internal deck.html -o deck_社内.html [--base-dir DIR]
      各図に data-fp-fig を振り、ピッカー（CSS・JS・型の一覧）を HTML に入れる。
      型の一覧は kit の frameworks_catalog.json を書き出しの時点で読み込む＝共有フォルダの kit を
      見る社員は全員同じ一覧になる。出来た HTML は1ファイルで開ける（ドライブを参照しない）。
  社外版: python3 fp_build.py external deck_社内.html -o deck_社外.html [--figs DIR] [--selections X.json] [--base-dir DIR]
      ピッカーの DOM・CSS・JS・型の一覧・data-fp-* を全部外し、相対パスの画像を data: で埋め込む。
      --figs DIR に <図ID>.html（実データで描き直した図の断片）があれば、その図と差し替えて埋め込む。
      埋め込み画像を軽量化する（写真は WebP 品質85・長辺1600px、透過が必要なロゴ／切り抜きは透過 WebP、使っていない kit 背景は除外。社内版はしない）。最後に fp_external_check.py と同じ検査を走らせ、痕跡が1つでも残れば書き出さない（終了コード1）。

数値は作らない：差し替えは --figs の断片（ci_frameworks.py 等で元データから描いたもの）だけ。
型の選択（JSON）は社内の依頼メモであり、社外版には一切入れない。
"""
import argparse, base64, urllib.parse, html.parser, json, mimetypes, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
BEGIN, END = '<!--ci-fp:begin-->', '<!--ci-fp:end-->'
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
        'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse', 'stop', 'use'}
SKIP_SLIDE = re.compile(r'\b(cover-full|pd-divider|divider|dark)\b')


def line_offsets(s):
    offs = [0]
    for m in re.finditer('\n', s):
        offs.append(m.end())
    return offs


class Scan(html.parser.HTMLParser):
    """図の候補（いちばん外側だけ）と、その開始タグ・終了位置を拾う。HTML は作り直さない。"""
    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src, self.lo = src, line_offsets(src)
        self.stack, self.targets, self.slide, self.page, self.nslide = [], [], None, '', 0

    def off(self):
        ln, col = self.getpos()
        return self.lo[ln - 1] + col

    def kind(self, tag, cls, attrs):
        t = set(cls.split())
        if tag == 'figure' and 'dg-photo' not in t: return 'diagram'
        if tag == 'table' and 'sk' in t: return 'table'
        if tag in ('div', 'figure') and ('ci-fig' in t or 'ne-graph' in t): return 'chart'
        if tag == 'div' and 'okr' in t: return 'kpi'
        if tag == 'div' and 'dgx-cmp' in t: return 'digest'   # ダイジェストの図（写真に置き換えられる・v3.20.2 試作）
        if tag == 'svg' and not (t & {'corner', 'cm-svg'}) and 'aria-hidden' not in attrs: return 'chart'
        return None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs); cls = a.get('class') or ''; o = self.off()
        if tag == 'section' and re.search(r'\bslide\b', cls):
            self.nslide += 1
            self.slide = None if (SKIP_SLIDE.search(cls) or 'data-fp-skip' in a) else self.nslide
            self.page = a.get('id') or 'p%02d' % self.nslide
        k = None
        in_target = any(e[2] for e in self.stack)
        if self.slide and not in_target and 'data-fp-skip' not in a:
            k = self.kind(tag, cls, a)
        ent = [tag, o, None]
        if k:
            dg = (k == 'digest')  # 既存の図の番号（保存済みの選択のキー）を変えないよう別の連番
            n = sum(1 for t in self.targets if t['page'] == self.page and (t['kind'] == 'digest') == dg) + 1
            ent[2] = {'id': ('%s-dg%d' if dg else '%s-%d') % (self.page, n), 'page': self.page, 'kind': k, 'tag': tag, 'start': o,
                      'tag_end': o + len(self.get_starttag_text()), 'end': None}
            self.targets.append(ent[2])
        if tag not in VOID:
            self.stack.append(ent)
        elif ent[2]:
            ent[2]['end'] = ent[2]['tag_end']

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID and self.stack and self.stack[-1][0] == tag:
            e = self.stack.pop()
            if e[2]: e[2]['end'] = e[2]['tag_end']

    def handle_endtag(self, tag):
        o = self.off(); close = o + len('</%s>' % tag)
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for e in self.stack[i:]:
                    if e[2] and e[2]['end'] is None: e[2]['end'] = close
                del self.stack[i:]
                break


def scan(src):
    # data: の画像本体はパーサに読ませない（長さを保ったまま置き換え＝位置はそのまま使える）
    masked = re.sub(r'data:[^"\')\s]{64,}', lambda m: 'x' * len(m.group(0)), src)
    masked = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', lambda m: ' ' * len(m.group(0)), masked, flags=re.S | re.I)
    sc = Scan(masked); sc.feed(masked); sc.close()
    return [t for t in sc.targets if t['end']]


def strip_fp(src):
    src = re.sub(re.escape(BEGIN) + '.*?' + re.escape(END), '', src, flags=re.S)
    src = re.sub(r'\s+data-fp-[\w-]+(="[^"]*")?', '', src)
    src = re.sub(r'\s+data-ci-fp(="[^"]*")?', '', src)
    src = re.sub(r'\s*\bci-fp-(hidden|static)\b', '', src)
    return src


def inline_local(src, base_dir):
    """相対パスの画像（src= / url()）を data: に埋め込む。見つからなければ止める。"""
    missing = []
    def to_data(ref):
        p = (base_dir / ref).resolve()
        if not p.is_file():
            missing.append(ref); return None
        mt = mimetypes.guess_type(str(p))[0] or 'application/octet-stream'
        return 'data:%s;base64,%s' % (mt, base64.b64encode(p.read_bytes()).decode())
    def rep_attr(m):
        ref = m.group(2)
        if re.match(r'(data:|https?:|#|mailto:|javascript:|blob:)', ref, re.I) or not ref.strip(): return m.group(0)
        d = to_data(ref)
        return m.group(1) + (d or ref) + m.group(3)
    src = re.sub(r'(<(?:img|source|image)\b[^>]*?\s(?:src|href|xlink:href)=")([^"]+)(")', rep_attr, src, flags=re.I)
    def rep_url(m):
        ref = m.group(2).strip('\'"')
        if re.match(r'(data:|https?:|#)', ref, re.I): return m.group(0)
        if not re.fullmatch(r'[\w./%~-]+\.(png|jpe?g|gif|svg|webp|avif|woff2?|ttf|otf)', ref, re.I): return m.group(0)
        d = to_data(urllib.parse.unquote(ref))
        return 'url(' + m.group(1) + (d or ref) + m.group(3) + ')'
    src = re.sub(r'url\((["\']?)((?!data:)[^)"\']+)(["\']?)\)', rep_url, src)
    has_pdf = 'application/pdf' in src
    def rep_a(m):
        tag = m.group(0); h = re.search(r'\shref="([^"]+)"', tag)
        if not h: return tag
        ref = h.group(1)
        if re.match(r'(data:|https?:|#|mailto:|javascript:|blob:)', ref, re.I) or not ref.strip(): return tag
        if 'data-ci-pdf-save' in tag and has_pdf:  # 手元確認用 PDF は HTML 内の base64 から JS が出す＝相対の予備リンクは不要
            new = '#'
        else:
            new = to_data(urllib.parse.unquote(ref)) or ref
        return tag[:h.start(1)] + new + tag[h.end(1):]
    src = re.sub(r'<a\b[^>]*>', rep_a, src, flags=re.I)
    if missing:
        sys.exit('❌ 埋め込めない相対パス: ' + ', '.join(sorted(set(missing))) + '（--base-dir を元デッキのフォルダに）')
    return src


def photos_json(path, src='', category=None, audience=None, handoff=None):
    """審査済みの人物写真（ws_photo/assets.json の台帳）から、このデッキの商品カテゴリー×購入層に合う1枚ずつを
    data: の WebP にして返す（ws_photo.select_assets と同じ選び方・社内版なので external_ok=false の素材も可）。長辺1600px超は止める。"""
    if not path: return '{}'
    from PIL import Image
    sys.path.insert(0, str(HERE.parent / 'ws_photo')); import ws_photo
    L = ws_photo.load_ledger(path); prof = ws_photo.deck_profile(src, L, category, audience, handoff)
    chosen, why = ws_photo.select_assets(L, prof, internal=True); out = {}
    for k, e in chosen.items():
        f = pathlib.Path(e['file']); w, h = Image.open(f).size
        if max(w, h) > 1600 or f.suffix.lower() != '.webp': sys.exit('❌ 写真は WebP・長辺1600px以下: %s' % f)
        out[k] = dict(src='data:image/webp;base64,' + base64.b64encode(f.read_bytes()).decode(), w=w, h=h,
                      caption=e['caption'], alt=e['alt'], id=e['id'])
    if why: out['_missing'] = {k: v for k, v in why.items()}
    print('  写真ピッカー: カテゴリー=%s 購入層=%s 素材=%s 無し=%s' % (prof['category'] or '未定', (prof['audience'] or {}).get('gender', '未定'),
          {k: v['id'] for k, v in chosen.items()}, why))
    return json.dumps(out, ensure_ascii=False).replace('</', '<\\/')


def build_internal(src, deck_name, catalog_path, photos=None):
    src = strip_fp(src)
    ts = scan(src)
    out, pos = [], 0
    for t in ts:
        te = t['tag_end']; tag = src[t['start']:te]
        close = '/>' if tag.endswith('/>') else '>'
        new = tag[:-len(close)] + ' data-fp-fig="%s" data-fp-page="%s" data-fp-kind="%s"' % (t['id'], t['page'], t['kind']) + close
        out.append(src[pos:t['start']]); out.append(new); pos = te
    out.append(src[pos:]); src = ''.join(out)
    cat = json.loads(pathlib.Path(catalog_path).read_text(encoding='utf-8'))
    css = (HERE / 'ci-framework-picker.css').read_text(encoding='utf-8')
    js = (HERE / 'ci-framework-picker.js').read_text(encoding='utf-8')
    head = BEGIN + '<style id="ci-fp-css">' + css + '</style>' + END
    body = (BEGIN + '<script type="application/json" id="ci-fp-catalog">' +
            json.dumps(cat, ensure_ascii=False).replace('</', '<\\/') + '</script><script type="application/json" id="ci-fp-photos">' +
            photos_json(photos, src) + '</script><script id="ci-fp-js">' + js + '</script>' + END)
    src = re.sub(r'</head>', lambda m: head + '</head>', src, count=1, flags=re.I)
    src = re.sub(r'</body>(?![\s\S]*</body>)', lambda m: body + '</body>', src, count=1, flags=re.I)
    src = re.sub(r'<html\b', lambda m: '<html data-ci-fp="internal" data-fp-deck="%s"' % deck_name.replace('"', ''), src, count=1, flags=re.I)
    return src, ts


def build_external(src, figs_dir, selections):
    ts = {t['id']: t for t in scan(src)}  # 社内版の data-fp-fig を使う前に位置を取る
    ids = {}
    for m in re.finditer(r'data-fp-fig="([^"]+)"', src):
        ids[m.group(1)] = m.start()
    swaps = []
    if figs_dir:
        for fid in sorted(ids):
            frag = pathlib.Path(figs_dir) / (fid + '.html')
            if frag.is_file():
                t = next((t for t in ts.values() if t['start'] <= ids[fid] < t['tag_end']), None)
                if not t: sys.exit('❌ 図 %s の位置が取れません' % fid)
                swaps.append((t, frag.read_text(encoding='utf-8'), fid))
    for t, frag, fid in sorted(swaps, key=lambda x: -x[0]['start']):
        frag = re.sub(r'<script\b.*?</script>', '', frag, flags=re.S | re.I)
        frag = re.sub(r'<!--.*?-->', '', frag, flags=re.S)  # 断片のメモ（社内の注記）は社外に持ち出さない
        src = src[:t['start']] + '<div class="fig ci-fig" data-fig="%s">%s</div>' % (fid, frag) + src[t['end']:]
    src = strip_fp(src)
    return src, [s[2] for s in swaps]


def unwrap_te_marks(src):
    """社外版・修正反映版に、テキスト修正の印（.ci-te-mark・枠・取り消し線・下線・data-old 等）を残さない。
    新しい文（<ins>）だけを本文として残す。v3.21.1・若松さん指示 2026-11-11 19:37。"""
    def repl(m):
        inner = m.group(1)
        ins = re.search(r'<ins\b[^>]*>(.*?)</ins>', inner, flags=re.S | re.I)
        if ins:
            return ins.group(1)
        return re.sub(r'<[^>]+>', '', inner)
    if 'ci-te-mark' not in src and 'ci-te-mark' not in src.lower():
        return src, 0
    src, n = re.subn(r'<span\b[^>]*\bci-te-mark\b[^>]*>(.*?)</span>', repl, src, flags=re.S | re.I)
    # 印のスタイル（.ci-te-mark ルール）も残さない。巨大な data URI を含む style では
    # 正規表現の戻追跡を避け、文字列検索でルール単位に落とす。
    def strip_mark_rules(css):
        if '.ci-te-mark' not in css:
            return css
        out, i = [], 0
        while True:
            j = css.find('.ci-te-mark', i)
            if j < 0:
                out.append(css[i:])
                break
            start = css.rfind('}', 0, j) + 1
            if start < i:
                start = i
            brace = css.find('{', j)
            if brace < 0:
                out.append(css[i:])
                break
            end = css.find('}', brace)
            if end < 0:
                out.append(css[i:])
                break
            out.append(css[i:start])
            i = end + 1
        return ''.join(out)
    def drop_css(m):
        return m.group(1) + strip_mark_rules(m.group(2)) + m.group(3)
    src = re.sub(r'(<style\b[^>]*>)(.*?)(</style>)', drop_css, src, flags=re.S | re.I)
    return src, n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['internal', 'external', 'list'])
    ap.add_argument('deck'); ap.add_argument('-o', '--out')
    ap.add_argument('--base-dir', help='相対パスの画像を解決するフォルダ（既定＝入力のフォルダ）')
    ap.add_argument('--deck-id', help='選択を保存するキー（既定＝出力ファイル名）')
    ap.add_argument('--catalog', default=str(HERE / 'frameworks_catalog.json'))
    ap.add_argument('--figs', help='実データで描き直した図の断片 <図ID>.html のフォルダ（external）')
    ap.add_argument('--photos', help='internal：ダイジェストの図を置き換える人物写真（審査済み素材の assets.json）。社外版には入らない')
    ap.add_argument('--ws-photo', action='store_true', help='external：余白の人物写真を external_ok の素材だけで付け直す（WS_PHOTO_RULE.md §4）')
    ap.add_argument('--selections', help='ピッカーから書き出した JSON（external：差し替え候補の表示だけに使う）')
    a = ap.parse_args()
    inp = pathlib.Path(a.deck); src = inp.read_text(encoding='utf-8')
    base = pathlib.Path(a.base_dir) if a.base_dir else inp.parent
    if a.mode == 'list':
        for t in scan(strip_fp(src)): print(t['id'], t['kind'], t['tag'])
        return 0
    if not a.out: sys.exit('-o が要ります')
    out = pathlib.Path(a.out)
    if out.resolve() == inp.resolve() or out.exists():
        sys.exit('❌ 上書きしません（別名で出してください）: %s' % out)
    if a.mode == 'internal':
        res, ts = build_internal(inline_local(src, base), a.deck_id or out.stem, a.catalog, a.photos)
        out.write_text(res, encoding='utf-8')
        print('社内版: %s（図 %d 個にピッカー）' % (out, len(ts)))
        for t in ts: print('  ', t['id'], t['kind'])
        return 0
    sel = json.loads(pathlib.Path(a.selections).read_text(encoding='utf-8')) if a.selections else {'figures': {}}
    # 社内版の余白写真（社内だけの素材を含みうる）はいったん全部外す。--ws-photo なら external_ok の素材だけで付け直す
    n_ws = len(re.findall(r'<!--ws-photo:begin-->', src))
    src = re.sub(r'<!--ws-photo:begin-->[\s\S]*?<!--ws-photo:end-->', '', src)
    src = re.sub(r'\s+data-ws-photo(?:-[\w-]+)?="[^"]*"', '', src)
    res, swapped = build_external(src, a.figs, sel)
    if a.ws_photo:   # 社外版にも余白写真を付ける：台帳で external_ok（顧客向けの権利を確認済み）の素材だけ
        sys.path.insert(0, str(HERE.parent / 'ws_photo')); import ws_photo
        res, pages = ws_photo.apply(res, a.photos or (HERE.parent / 'ws_photo' / 'assets.json'), external=True)
        print('  余白の人物写真（社外）: %s 素材=%s 無し=%s' % (', '.join('%s=%s' % p for p in pages), ws_photo.apply.last['chosen'], ws_photo.apply.last['missing']))
    elif n_ws: print('  余白の人物写真（ws_photo）を外しました（付けるなら --ws-photo：external_ok の素材だけ）')
    res, nmarks = unwrap_te_marks(res)
    if nmarks:
        print('  テキスト修正の印 %d 件を外し、新しい文だけを本文にしました' % nmarks)
    res = inline_local(res, base)
    before_len = len(res.encode('utf-8'))
    sys.path.insert(0, str(HERE))
    import fp_lighten
    try:
        res, st = fp_lighten.lighten_html(res)
        print('  ' + fp_lighten.format_stats(st, before_len, len(res.encode('utf-8'))))
        if st.get('skipped_pillow'):
            print('  ⚠ Pillow が無いため、埋め込み写真の WebP 化はしませんでした（書き出しは完了します）。', file=sys.stderr)
    except ImportError as e:
        print('  ⚠ Pillow が無いため、埋め込み画像の軽量化を飛ばします（%s）。書き出しは続けます。' % e, file=sys.stderr)
    import fp_external_check as chk
    found = chk.check_text(res)
    if found:
        for f in found: print(f, file=sys.stderr)
        sys.exit('❌ 社外版にピッカー／ローカル参照の痕跡が残るため書き出しません')
    out.write_text(res, encoding='utf-8')
    print('社外版: %s（差し替え %d 図: %s）' % (out, len(swapped), ', '.join(swapped) or 'なし'))
    pend = [k for k, v in sel.get('figures', {}).items() if v.get('selected') and k not in swapped]
    if pend: print('  型を選んだが描き直しの断片が無い図（元の図のまま）:', ', '.join(sorted(pend)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
