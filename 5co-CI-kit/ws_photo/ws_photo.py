#!/usr/bin/env python3
"""ws_photo.py — 余白に人物写真（消費者・インフルエンサー・コンサルタント）を入れる仕組みを、デッキに付ける（オプトイン）。
規定: WS_PHOTO_RULE.md（試作 2026-11-11）。ci_head.py --fill-whitespace-photo deck.html [-o out] からも呼ぶ。

  python3 ws_photo.py deck.html -o out.html [--assets assets.json] [--pages p02,p06] [--external]
                     [--category nail] [--audience "female 20-49"] [--handoff handoff.json|.md]
  python3 ws_photo.py --profile deck.html [--handoff X]   … カテゴリー・購入層の判定と、選ばれる素材だけを表示

- 消費者・インフルエンサーは「デッキの商品カテゴリー × 購入層（性別・年代）」に合う素材だけ（WS_PHOTO_RULE.md §2）。
  宣言（<html data-ws-category="nail" data-ws-audience="female 20-49">）→ --category/--audience → handoff → 本文の語の順で決める。
  決められないとき、合う素材が無いときは入れない。コンサルタントはカテゴリーに関係なく従来どおり。

- 各ページの主題からペルソナを決めて data-ws-photo を付ける（手で付けた data-ws-photo / data-ws-photo-skip は尊重）。
- ws-photo.css / ws-photo.js / 素材（data: の WebP・長辺 800px）を入れる。余白の判定と配置は描画後にブラウザで行う
  （通常表示・ダイジェスト・発表・印刷のたびに測り直す）。
- 社外版（--external）は台帳で external_ok=true（顧客向けの権利・公開を確認済み）の素材だけを使う。
  合う素材が無いページには入れない。（試作初版の --rights-confirmed＝デッキ単位の確認は廃止し、素材単位に変えた）
- 冪等（前に入れたものを外してから入れ直す）。出力は別名のみ（入力の上書きは不可）。
"""
import base64, json, re, sys, pathlib
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent
BEGIN, END = '<!--ws-photo:begin-->', '<!--ws-photo:end-->'
RULE = dict(cols=12, gap=8, pad=8, min_pct=15, min_cols=3, min_rows=2, min_h_px=150, max_tables=1, person_aspect=0.7)
# 主題 → ペルソナ（見出し・要点・ページ名で当たった数が最多のもの。同数は上が優先）。WS_PHOTO_RULE.md §2
THEMES = [
    ('influencer', r'SNS|インフルエンサー|Instagram|TikTok|YouTube|広告|DSP|Sponsored|スポンサー|認知|インプレッション|表示回数|CPM|リーチ|動画'),
    ('consumer',   r'売上|購買|購入|注文|検索|レビュー|カート|顧客|消費者|Amazonユーザー|必達|実績|販売'),
    ('consultant', r'施策|計画|提案|戦略|進捗|振り返り|打ち手|要因|OKR|予算|目標|会議|定例'),
]
SKIP_CLS = re.compile(r'\b(cover-full|pd-divider|divider|cover-card)\b')

def tag_pages(src, only=None):
    out, n = [], 0
    def rep(m):
        nonlocal n
        tag = m.group(0); cls = re.search(r'class="([^"]*)"', tag); cls = cls.group(1) if cls else ''
        n += 1; pid = (re.search(r'\bid="([^"]+)"', tag) or [None, 'p%02d' % n])[1]
        if 'slide' not in cls.split() or SKIP_CLS.search(cls) or 'data-serp-page' in tag: return tag
        if only and pid not in only: return tag
        if 'data-ws-photo=' in tag or 'data-ws-photo-skip' in tag: return tag
        i = m.end(); j = src.find('<section', i); body = src[i: j if j > 0 else len(src)]
        head = re.sub(r'<[^>]+>', ' ', re.sub(r'data:[^"\')]+', '', ' '.join(re.findall(r'<(?:h2|p class="gist|span class="kicker)[^>]*>.*?</(?:h2|p|span)>', body, re.S)[:4])))
        head += ' ' + (re.search(r'data-talk-h="([^"]*)"', tag) or [None, ''])[1]
        hits = [(len(re.findall(pat, head)), -i, persona) for i, (persona, pat) in enumerate(THEMES)]
        c, _, persona = max(hits)
        if not c: return tag
        out.append((pid, persona)); return tag[:-1] + ' data-ws-photo="%s">' % persona
    src = re.sub(r'<section\b[^>]*>', rep, src)
    return src, out

def load_ledger(path):
    """台帳を読む。file が相対パスなら台帳のフォルダ基準。ファイルが無い素材は使わない（_absent に理由）。"""
    p = pathlib.Path(path); L = json.loads(p.read_text(encoding='utf-8')); L['_absent'] = []
    for a in L.get('assets', []):
        f = a.get('file')
        if not f: continue
        fp = pathlib.Path(f) if pathlib.Path(f).is_absolute() else (p.parent / f)
        a['file'] = str(fp)
        if a.get('status') == 'approved' and not fp.exists():
            a['status'] = 'absent'; L['_absent'].append(a['id'])
    return L

def _attr(src, name):
    m = re.search(r'<(?:html|body)\b[^>]*\b' + name + r'="([^"]*)"', src, re.I)
    return m.group(1).strip() if m else ''

def _handoff(path):
    if not path: return {}
    t = pathlib.Path(path).read_text(encoding='utf-8')
    try:
        j = json.loads(t); return {'category': j.get('category', ''), 'audience': j.get('audience', '')}
    except ValueError:
        c = re.search(r'(?:商品カテゴリー|カテゴリー)\s*[:：]\s*(\S+)', t); a = re.search(r'(?:購入層|ターゲット)\s*[:：]\s*([^\n]+)', t)
        return {'category': c.group(1) if c else '', 'audience': a.group(1).strip() if a else ''}

def _norm_aud(a):
    """'女性 20〜49歳' / 'female 20-49' → {'gender': 'female', 'age': (20, 49)}"""
    if not a: return None
    g = 'female' if re.search(r'female|女性|レディース|women', a, re.I) else 'male' if re.search(r'\bmale\b|男性|メンズ|men\b', a, re.I) else 'any' if re.search(r'any|男女', a, re.I) else ''
    m = re.search(r'(\d{2})\s*[-〜~～]\s*(\d{2})', a)
    return {'gender': g, 'age': (int(m.group(1)), int(m.group(2))) if m else None}

def deck_profile(src, ledger, category=None, audience=None, handoff=None):
    """デッキの商品カテゴリーと購入層。how に根拠（宣言／指定／handoff／本文の語／カテゴリーの既定）を残す。"""
    cats, how = ledger['categories'], {}
    ho = _handoff(handoff)
    cat = category or _attr(src, 'data-ws-category'); how['category'] = '指定' if category else '宣言' if cat else ''
    if not cat and ho.get('category'): cat, how['category'] = ho['category'], 'handoff'
    if not cat:
        body = re.sub(r'data:[^"\')]+', '', src); body = re.sub(r'<(script|style)\b.*?</\1>', ' ', body, flags=re.S | re.I)
        hits = sorted(((len(re.findall(v['kw'], body)), k) for k, v in cats.items()), reverse=True)
        if hits and hits[0][0] >= 2: cat, how['category'] = hits[0][1], '本文の語（%d件）' % hits[0][0]
    aud = audience or _attr(src, 'data-ws-audience'); how['audience'] = '指定' if audience else '宣言' if aud else ''
    if not aud and ho.get('audience'): aud, how['audience'] = ho['audience'], 'handoff'
    if not aud and cat in cats and cats[cat].get('audience'): aud, how['audience'] = cats[cat]['audience'], 'カテゴリーの既定'
    a = _norm_aud(aud)
    return {'category': cat if cat in cats else '', 'audience': a if a and a['gender'] else None, 'how': how}

def _age_ok(a, b):
    if not a or not b: return True
    lo, hi = (int(x) for x in b.split('-')) if isinstance(b, str) else b
    return not (a[1] < lo or a[0] > hi)

def select_assets(ledger, prof, internal=True):
    """ペルソナごとに1つ選ぶ。消費者＝性別が合う（年代は重なれば可）・カテゴリーが合うものを優先（* は汎用）。
    インフルエンサー＝カテゴリーが一致（* は不可）・性別が合う。コンサルタント＝カテゴリー不問。理由も返す。"""
    out, why = {}, {}
    for persona in ('consumer', 'influencer', 'consultant'):
        best = None
        for e in ledger['assets']:
            if e.get('persona') != persona or e.get('status') != 'approved' or not e.get('file'): continue
            if not internal and not e.get('external_ok'): continue   # 社外版は顧客向けの権利を確認した素材だけ
            if persona != 'consultant':
                if not prof['category'] or not prof['audience']: continue
                aud = prof['audience']
                if aud['gender'] in ('female', 'male') and e.get('gender') != aud['gender']: continue
                if not _age_ok(aud['age'], e.get('age')): continue
                exact = prof['category'] in e.get('categories', [])
                if persona == 'influencer' and not exact: continue
                if not exact and '*' not in e.get('categories', []): continue
                score = 2 if exact else 1
            else:
                score = 1
            if not best or score > best[0]: best = (score, e)
        if best: out[persona] = best[1]
        else:
            why[persona] = ('カテゴリーか購入層が決まらない' if persona != 'consultant' and (not prof['category'] or not prof['audience'])
                            else '台帳に合う審査済み素材が無い')
    return out, why

def data_uri(path):
    im = Image.open(path); w, h = im.size
    if max(w, h) > 1600: raise ValueError('長辺1600px超: %s' % path)
    im.close(); b = pathlib.Path(path).read_bytes()
    return 'data:image/webp;base64,' + base64.b64encode(b).decode(), w, h

def apply(src, assets_path=HERE / 'assets.json', only=None, external=False, rights=False,
          category=None, audience=None, handoff=None):
    """category/audience を渡すとデッキの <html> に data-ws-category / data-ws-audience として書き込む（宣言として残す）。"""
    if rights:
        print('注意: --rights-confirmed は廃止（素材ごとの external_ok で判断）。無視します', file=sys.stderr)
    for name, val in (('data-ws-category', category), ('data-ws-audience', audience)):
        if val:
            src = re.sub(r'(<html\b[^>]*?)\s+' + name + r'="[^"]*"', r'\1', src, count=1, flags=re.I)
            src = re.sub(r'<html\b', lambda m: m.group(0) + ' %s="%s"' % (name, val.replace('"', '')), src, count=1, flags=re.I)
    src = re.sub(re.escape(BEGIN) + r'[\s\S]*?' + re.escape(END), '', src)
    src = re.sub(r'\s+data-ws-photo="[^"]*"', '', src) if only is None else src
    L = load_ledger(assets_path)
    prof = deck_profile(src, L, category, audience, handoff)
    chosen, why = select_assets(L, prof, internal=not external)
    if external:
        why = {k: (v if v != '台帳に合う審査済み素材が無い' else '顧客向けに使える（external_ok）素材が無い') for k, v in why.items()}
    src, pages = tag_pages(src, only)
    used = {p for _, p in pages}; cfg = {'rule': RULE, 'assets': {}, 'profile': {'category': prof['category'], 'audience': prof['audience'] and prof['audience']['gender']}}
    for k in used:
        if k not in chosen: continue   # 合う素材が無いペルソナのページは入れない（data-ws-photo は残し、状態に理由を出す）
        e = chosen[k]; uri, w, h = data_uri(e['file'])
        cfg['assets'][k] = dict(src=uri, w=w, h=h, caption=e['caption'], alt=e['alt'], id=e['id'])
    cfg['missing'] = why
    if L.get('_absent'): print('注意: 素材ファイルが見つからないので使わない: ' + ', '.join(L['_absent']), file=sys.stderr)
    apply.last = {'profile': prof, 'chosen': {k: v['id'] for k, v in chosen.items()}, 'missing': why}
    css = (HERE / 'ws-photo.css').read_text(encoding='utf-8'); js = (HERE / 'ws-photo.js').read_text(encoding='utf-8')
    head = BEGIN + '<style id="ws-photo-css">' + css + '</style>' + END
    body = BEGIN + '<script type="application/json" id="ws-photo-cfg">' + json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/') + '</script><script id="ws-photo-js">' + js + '</script>' + END
    src = re.sub(r'</head>', lambda m: head + '</head>', src, count=1, flags=re.I)
    src = re.sub(r'</body>(?![\s\S]*</body>)', lambda m: body + '</body>', src, count=1, flags=re.I)
    return src, pages

def main(argv):
    if not argv or argv[0] in ('-h', '--help'): print(__doc__); return 2
    opt = lambda n: argv[argv.index(n) + 1] if n in argv else None
    if argv[0] == '--profile':
        L = load_ledger(opt('--assets') or HERE / 'assets.json')
        prof = deck_profile(pathlib.Path(argv[1]).read_text(encoding='utf-8'), L, opt('--category'), opt('--audience'), opt('--handoff'))
        ch, why = select_assets(L, prof, internal='--external' not in argv)
        print(json.dumps({'profile': prof, 'chosen': {k: v['id'] for k, v in ch.items()}, 'missing': why}, ensure_ascii=False, indent=1)); return 0
    src = pathlib.Path(argv[0]); dst = pathlib.Path(argv[argv.index('-o') + 1]) if '-o' in argv else None
    if not dst or dst.resolve() == src.resolve(): print('NG: -o に別名を指定（上書きしない）', file=sys.stderr); return 1
    only = set(argv[argv.index('--pages') + 1].split(',')) if '--pages' in argv else None
    ap = argv[argv.index('--assets') + 1] if '--assets' in argv else HERE / 'assets.json'
    try:
        html, pages = apply(src.read_text(encoding='utf-8'), ap, only, '--external' in argv, '--rights-confirmed' in argv,
                            opt('--category'), opt('--audience'), opt('--handoff'))
    except ValueError as e:
        print('NG:', e, file=sys.stderr); return 1
    dst.write_text(html, encoding='utf-8')
    print('ws_photo: ' + ', '.join('%s=%s' % p for p in pages) + ' -> %s' % dst, file=sys.stderr)
    print('  profile: %s / chosen: %s / missing: %s' % (json.dumps(apply.last['profile'], ensure_ascii=False), apply.last['chosen'], apply.last['missing']), file=sys.stderr); return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
