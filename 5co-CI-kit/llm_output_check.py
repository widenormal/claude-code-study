#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_output_check.py — LLM が書いた文章の検品ゲート（2026-09-08 v3.8 新設）

なぜ要るか（実インシデント・WELLA ProHair 統合デッキ 2026-09-07）:
  全社の作り方は「**文章（見出し・洞察）は Kimi k3 かローカルLLM が起案し、
  Claude は分解・検査・統合に徹する**」。つまり本文そのものが LLM の出力である。
  ところが kit のゲートは「はみ出し」「重なり」だけで、**文言の破損を見るゲートが無い**。
  実際、やさしい版（リライト）と英語版（翻訳）で数値マスク＋復元を通したのに、
  次の崩れが本番直前まで残った。**数字自体は合っているため数値チェックは全部通る。**

    「定常月¥9.5M・FY27 ¥0.73億」→「¥9.5M27¥0.73億」（FY が落ちて数字が連結）
    「WELLA様」→「ウエラ」「WELLA社」   「観測が無い SKU」→「翻訳が無い SKU」
    「月¥3.7M」→「¥3.7M個」   「最高430位」→「430位円」   「個個」
    鉤括弧「」が " " に化ける

何をするか
  A. 突合モード（リライト・翻訳）: 原文と生成物を**同じ位置の段落どうし**で突き合わせ、
     ①英数トークンが保存されているか ②タグの種類が同じか ③単位の崩れ・引用符の混入が無いか
     を判定する。満たさない段落だけ原文へ戻し、**戻した件数と理由を標準出力に出す**。
  B. 起案モード（原文が無い場合）: 突合できないので別条件で見る。
     禁止語（用語集の「使ってはいけない言い換え」）・データ由来でない数値・タグの破損。

使い方
  python3 llm_output_check.py <生成物.html> --source <原文.html>              # 判定のみ
  python3 llm_output_check.py <生成物.html> --source <原文.html> --restore    # NG段落を原文へ戻す
  python3 llm_output_check.py <生成物.html> --source <原文.html> --restore --out fixed.html
  python3 llm_output_check.py <起案.html> --terms TERMS_AMAZON.md [--values data.json]
        （既定の禁止語＝用語集が「全文検索せよ」と名指しした語。--strict-terms で表の3列目も全部）
  python3 llm_output_check.py --selftest        # 検査そのものの動作確認（しきい値を触ったら必ず）
  共通: --json（機械可読・JSON Lines）

**差し替えはタグを作り直さない**（V3.2_FORMAT.md「このページの要点(gist)」の規定・B-7）:
  本スクリプトは NG 段落の**内側の文字列だけ**を原文の同じ範囲で置き換える。開始・終了タグは
  生成物のものをそのまま残す。正規表現でタグを組み直すと `<p class="gist"><span
  class="gist-k">…</span>本文</p>` のような**開始タグが2つある要素**でラベルが消える
  （実際に十数ページで要点ラベルが消えた事故がある）。

戻り値: 0=合格（--restore で全件戻せた場合を含む） / 1=NGが残る・構造不一致・入力不正
"""
import sys, os, re, json, html as _html, pathlib, tempfile
from collections import Counter

# ---------------------------------------------------------------- HTML 走査（タグを作り直さないための位置情報）
_TAG = re.compile(r'<(/?)([a-zA-Z][\w:-]*)((?:"[^"]*"|\'[^\']*\'|[^>])*?)(/?)>', re.S)
VOID = {'br', 'img', 'hr', 'input', 'meta', 'link', 'source', 'col', 'area', 'base', 'embed', 'param', 'track', 'wbr'}
SKIP = {'svg', 'script', 'style', 'head'}          # 中の文字は対象外（SVG図版は svg_label_check.py の担当）
BLOCKS = {'p', 'li', 'td', 'th', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
          'caption', 'figcaption', 'dt', 'dd', 'blockquote'}


def scan(src: str):
    """本文を持つ末端ブロック要素を、原文中の位置つきで拾う。

    返り値: [{'tag','inner_start','inner_end','inner','segments'}...]（文書順）と、閉じ忘れタグの一覧。

    入れ子（td の中の p、li の中の ul>li 等）の扱い:
      - 内側のブロックはそれぞれ独立した要素として拾う（壊れた1段落だけを戻せるように）
      - 外側のブロックは、**子ブロックを除いた地の文の区間（segments）だけ**を持つ要素として残す
        （`<li>FY27 本文<ul><li>…</li></ul></li>` の「FY27 本文」を見落とさないため。
        Codex astra 指摘・2026-09-09）。地の文が空（td が p を並べるだけ等）なら外側は落とす
      - 'inner' は segments を連結した文字列。差し戻しは segments 単位で行うので置換範囲は重ならない
    """
    stack, found, unclosed, skip_depth = [], [], [], 0
    for m in _TAG.finditer(src):
        closing, tag, _attrs, selfclose = m.group(1), m.group(2).lower(), m.group(3), m.group(4)
        if skip_depth:
            if tag in SKIP:
                skip_depth += 0 if closing else 1
                if closing:
                    skip_depth -= 1
            continue
        if not closing and tag in SKIP and not selfclose:
            skip_depth = 1
            continue
        if closing:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i][0] == tag:
                    t, outer_start, inner_start = stack[i]
                    for orphan in stack[i + 1:]:
                        unclosed.append(orphan[0])
                    del stack[i:]
                    if t in BLOCKS:
                        found.append({'tag': t, 'outer_start': outer_start, 'outer_end': m.end(),
                                      'inner_start': inner_start, 'inner_end': m.start()})
                    break
        elif tag not in VOID and not selfclose:
            stack.append((tag, m.start(), m.end()))
    unclosed += [t for t, _, _ in stack]
    found.sort(key=lambda e: (e['inner_start'], -e['inner_end']))
    out = []
    for e in found:
        # e の直下の子ブロック＝e に含まれ、かつ e 内の他のブロックに含まれないもの
        inside = [o for o in found if o is not e
                  and o['inner_start'] >= e['inner_start'] and o['inner_end'] <= e['inner_end']]
        kids = [o for o in inside if not any(k is not o and o['inner_start'] >= k['inner_start']
                                             and o['inner_end'] <= k['inner_end'] for k in inside)]
        if not kids:
            e['segments'] = [(e['inner_start'], e['inner_end'])]
        else:
            # 子ブロックを除いた地の文の区間だけを残す（子は独立した要素として別に拾われる）
            segs, pos = [], e['inner_start']
            for k in sorted(kids, key=lambda k: k['outer_start']):
                segs.append((pos, k['outer_start']))
                pos = k['outer_end']
            segs.append((pos, e['inner_end']))
            e['segments'] = [(a, b) for a, b in segs if a < b]
        e['inner'] = ' '.join(src[a:b] for a, b in e['segments'])
        if kids and not text_of(e['inner']):
            continue      # 純粋な入れ物（td が p を並べるだけ等）は突合対象にしない
        out.append(e)
    return out, unclosed


def text_of(inner: str) -> str:
    """内側HTMLから素の文字列（タグを除き、実体参照を戻し、空白を正規化）。"""
    return re.sub(r'\s+', ' ', _html.unescape(_TAG.sub(' ', inner))).strip()


def tag_kinds(inner: str) -> Counter:
    return Counter(m.group(2).lower() for m in _TAG.finditer(inner) if not m.group(1))


# ---------------------------------------------------------------- 判定
# 略語→日常語への置換は許す（COPY_GUIDE ルール4「専門用語に日常語を併記」の範囲）。
# これ以外の英数トークン（FY27・WELLA・ULTIME・Shelpha 等）が消えたら破損とみなす。
ALLOW_DROP = {'KR', 'SKU', 'ASIN', 'TACOS', 'ACOS', 'ROAS', 'BSR', 'NTB', 'KPI', 'OKR', 'CFR',
              'OODA', 'PDCA', 'CVR', 'CTR', 'CPC', 'CPA', 'ROI', 'EC', 'SEO', 'DWH', 'FBA',
              'SP', 'SB', 'SD', 'PL', 'QA', 'AI', 'LLM', 'PDF', 'PPTX', 'HTML', 'CSS'}
_TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9]*')
_NUM = re.compile(r'\d[\d,]*(?:\.\d+)?')

BROKEN_UNITS = [
    (re.compile(r'個個|位位|円円|件件|本本|%%|％％'), '単位の重複'),
    (re.compile(r'[¥￥][\d,.]+[MK億万]?\s*個'), '金額に個数の単位が付いた'),
    (re.compile(r'\d+\s*位\s*円'), '順位に金額の単位が付いた'),
    (re.compile(r'\d+\s*円\s*位'), '金額に順位の単位が付いた'),
    (re.compile(r'[¥￥][\d,.]+[MK]\d'), '数値の連結（単位語・年度表記の脱落）'),
]


def _nums(text: str) -> set:
    return {m.group(0).replace(',', '') for m in _NUM.finditer(text)}


def compare(src_inner: str, gen_inner: str) -> list:
    """段落1つ分の突合。返り値＝NG理由のリスト（空なら合格）。"""
    s, g = text_of(src_inner), text_of(gen_inner)
    reasons = []

    # ① 英数トークンの保存
    st = {t for t in _TOKEN.findall(s)}
    gt = {t.casefold() for t in _TOKEN.findall(g)}
    lost = sorted(t for t in st if t.casefold() not in gt and t.upper() not in ALLOW_DROP)
    if lost:
        reasons.append(f'英数トークンが消えた: {", ".join(lost[:6])}')
    lost_n = sorted(n for n in _nums(s) if n not in _nums(g))
    if lost_n:
        reasons.append(f'数値が消えた: {", ".join(lost_n[:6])}')

    # ② タグの種類
    ks, kg = tag_kinds(src_inner), tag_kinds(gen_inner)
    if ks != kg:
        diff = sorted((ks - kg).elements()) or sorted((kg - ks).elements())
        reasons.append(f'タグ構成が変わった: {"/".join(diff[:6])}')

    # ③ 単位の崩れ・引用符の混入
    for pat, why in BROKEN_UNITS:
        if (m := pat.search(g)) and not pat.search(s):
            reasons.append(f'{why}: 「{m.group(0)}」')
    if '「' in s and '「' not in g and '"' in g:
        reasons.append('鉤括弧「」が引用符 " に化けた')
    return reasons


# ---------------------------------------------------------------- 起案モード（原文が無い場合）
def forbidden_from_terms(path: pathlib.Path, strict: bool = False) -> list:
    """用語集（TERMS_AMAZON.md）から検索対象の禁止語を集める。

    既定は用語集自身が「書くときの手順」で**全文検索せよと名指しした語**（バッククォート
    表記）だけを使う。表の3列目には「色」「サイズ」「枚」のように、文脈で正しく使える語も
    含まれるため、そのまま全部を禁止語にすると誤検出だらけになり警告が形骸化する。
    `strict=True`（--strict-terms）で3列目も全部拾う。
    """
    text = path.read_text(encoding='utf-8')
    if not strict:
        for line in text.splitlines():
            if '使ってはいけない言い換え' in line and '検索' in line:
                return sorted(set(re.findall(r'`([^`]{1,8})`', line)))
    words, col = set(), None
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip().startswith('|'):
            col = None
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if any('使ってはいけない' in c for c in cells):
            col = next(i for i, c in enumerate(cells) if '使ってはいけない' in c)
            continue
        if col is None or col >= len(cells) or set(cells[0]) <= set('-: '):
            continue
        for w in re.split(r'[・、,]', cells[col]):
            w = w.strip().strip('*` ')
            # 「ASIN と混用しない」のような注記や空欄は禁止語ではない
            if 1 <= len(w) <= 8 and '—' not in w and 'ない' not in w and '（' not in w and ' ' not in w:
                words.add(w)
    return sorted(words)


def check_draft(html: str, forbid: list, values: set | None) -> list:
    """起案（原文なし）の判定。返り値＝{'kind','detail'} のリスト。"""
    out = []
    els, unclosed = scan(html)
    for t in sorted(set(unclosed)):
        out.append({'kind': 'タグの破損', 'detail': f'閉じられていない <{t}>'})
    body = ' '.join(text_of(e['inner']) for e in els)
    for w in forbid:
        if (n := body.count(w)):
            out.append({'kind': '禁止語', 'detail': f'「{w}」が {n} 箇所（用語集の使ってはいけない言い換え）'})
    if values is not None:
        seen = _nums(body)
        stray = sorted(n for n in seen if n not in values)
        if stray:
            out.append({'kind': 'データ由来でない数値',
                        'detail': '、'.join(stray[:8]) + ('…' if len(stray) > 8 else '')})
    return out


# ---------------------------------------------------------------- 突合＋差し戻し
def run_compare(gen_path: pathlib.Path, src_path: pathlib.Path, restore: bool, out_path):
    gen, src = gen_path.read_text(encoding='utf-8'), src_path.read_text(encoding='utf-8')
    gels, gunclosed = scan(gen)
    sels, _ = scan(src)
    res = {'file': gen_path.name, 'source': src_path.name, 'ok': True,
           'elements': len(gels), 'failed': [], 'restored': 0, 'unclosed': sorted(set(gunclosed))}
    if len(gels) != len(sels):
        res['ok'] = False
        res['error'] = (f'段落数が一致しない（原文 {len(sels)} / 生成物 {len(gels)}）。'
                        '構造が変わっているため位置での突合ができない。差し戻しは行わない')
        return res, None
    # 構造の破損（Codex astra 指摘・2026-09-09）: 閉じ忘れタグと、同じ位置でブロックの種類が
    # 変わったもの（h2→p 等）は、内側を戻しても直らない。差し戻しても合格にしない。
    structural = []
    if gunclosed:
        structural.append(f'閉じられていないタグ: {", ".join(f"<{t}>" for t in res["unclosed"][:6])}')
    for i, (se, ge) in enumerate(zip(sels, gels)):
        why = compare(se['inner'], ge['inner'])
        if se['tag'] != ge['tag']:
            why.insert(0, f'ブロックの種類が変わった: <{se["tag"]}> → <{ge["tag"]}>')
            structural.append(f'[{i}] <{se["tag"]}> → <{ge["tag"]}>')
        if len(se['segments']) != len(ge['segments']):
            why.insert(0, f'入れ子の構成が変わった（地の文の区間 {len(se["segments"])} → {len(ge["segments"])}）')
            structural.append(f'[{i}] <{ge["tag"]}> 入れ子の構成')
        if why:
            restorable = se['tag'] == ge['tag'] and len(se['segments']) == len(ge['segments'])
            res['failed'].append({'i': i, 'tag': ge['tag'], 'restorable': restorable,
                                  'text': text_of(ge['inner'])[:60], 'reasons': why})
    res['structural'] = structural
    if res['failed'] or structural:
        res['ok'] = False
    fixed = None
    if restore and res['failed']:
        # **後ろから**差し替える（前を書き換えると後ろの位置がずれるため）。
        # 置き換えるのは内側の文字列だけ。開始・終了タグは生成物のものをそのまま残す（B-7）。
        # 要素ではなく区間（segments）単位で置換区間を集め、文書の後ろから当てる。外側ブロックの
        # 地の文は子ブロックの前後に分かれるため、要素単位で後ろから当てると位置がずれる。
        repl = []
        for f in res['failed']:
            if not f['restorable']:
                continue
            ge, se = gels[f['i']], sels[f['i']]
            for (ga, gb), (sa, sb) in zip(ge['segments'], se['segments']):
                repl.append((ga, gb, src[sa:sb]))
        fixed = gen
        for ga, gb, text in sorted(repl, key=lambda r: -r[0]):
            fixed = fixed[:ga] + text + fixed[gb:]
        res['restored'] = sum(1 for f in res['failed'] if f['restorable'])
        # 戻した結果は原文＝合格。ただし構造の破損が残るなら不合格のまま（人が直す）
        res['ok'] = not structural
    return res, fixed


# ---------------------------------------------------------------- 自己検査
SELFTEST = [
    # (原文, 生成物, 検出されるべきか, 説明)
    ('<p>定常月¥9.5M・FY27 ¥0.73億</p>', '<p>¥9.5M27¥0.73億</p>', True, 'FY脱落＋数値連結'),
    ('<p>WELLA様の実績</p>', '<p>ウエラの実績</p>', True, 'ブランド名の消失'),
    ('<p>観測が無い SKU</p>', '<p>翻訳が無い SKU</p>', False, '略語以外は保存されていればOK'),
    ('<p>月¥3.7M</p>', '<p>¥3.7M個</p>', True, '金額に個数の単位'),
    ('<p>最高430位</p>', '<p>430位円</p>', True, '順位に金額の単位'),
    ('<p>親ASIN 30件</p>', '<p>親ASIN 30件個個</p>', True, '単位の重複'),
    ('<p>「第2候補」を選ぶ</p>', '<p>"第2候補"を選ぶ</p>', True, '鉤括弧の化け'),
    ('<p class="gist"><span class="gist-k">このページの要点</span>本文</p>',
     '<p class="gist">本文</p>', True, 'gist ラベルの消失（タグ構成の変化）'),
    ('<p>親ASIN 30件</p>', '<p>商品ページ 30件</p>', False, '略語の日常語化は許容（ASIN）'),
    ('<p>FY27 は ¥0.73億</p>', '<p>FY27 is ¥0.73億</p>', False, '翻訳でトークンが保存されていればOK'),
]


def selftest() -> int:
    bad = 0
    for s, g, want, why in SELFTEST:
        got = bool(compare(s, g))
        ok = (got == want)
        bad |= (not ok)
        print(f'{"✔" if ok else "✘"} {why}: 期待={"検出" if want else "合格"} '
              f'実際={"検出" if got else "合格"}' + (f' → {compare(s, g)}' if got else ''))
    # 差し替えがタグを壊さないこと（B-7 の回帰テスト）
    src = '<p class="gist"><span class="gist-k">このページの要点</span>FY27 は ¥0.73億</p>'
    gen = '<p class="gist"><span class="gist-k">このページの要点</span>¥0.73億</p>'
    sels, _ = scan(src); gels, _ = scan(gen)
    fixed = gen[:gels[0]['inner_start']] + sels[0]['inner'] + gen[gels[0]['inner_end']:]
    ok = 'gist-k' in fixed and 'FY27' in fixed and fixed.count('<p') == 1
    bad |= (not ok)
    print(f'{"✔" if ok else "✘"} 差し戻しで gist ラベルと開始タグが保たれる')
    # 入れ子は最内側だけを拾う（td の中の p が2つ → p が2つ・td は拾わない）
    els, _ = scan('<table><tr><td><p>A</p><p>B</p></td><td>C</td></tr></table>')
    ok = [e['tag'] for e in els] == ['p', 'p', 'td'] and [text_of(e['inner']) for e in els] == ['A', 'B', 'C']
    bad |= (not ok)
    print(f'{"✔" if ok else "✘"} 入れ子ブロックは最内側だけを突合対象にする（td>p×2・入れ物の td は落とす）')
    # 外側ブロックの地の文（子ブロックの外）も突合し、区間単位で戻す（astra 2回目の指摘）
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / 's.html').write_text('<ul><li>FY27 WELLA<ul><li>Detail</li></ul> 末尾</li></ul>', encoding='utf-8')
        (d / 'g.html').write_text('<ul><li>FY28 OTHER<ul><li>Detail</li></ul> tail</li></ul>', encoding='utf-8')
        r, fixed = run_compare(d / 'g.html', d / 's.html', True, None)
        ok = (not r['ok'] or r['restored'] == 1) and fixed == (d / 's.html').read_text(encoding='utf-8')
        ok = ok and r['failed'] and r['failed'][0]['tag'] == 'li' and 'FY27' in r['failed'][0]['reasons'][0]
        # 起案モードでも地の文の禁止語を拾う
        ok = ok and any('OTHER' in f['detail'] for f in check_draft((d / 'g.html').read_text(encoding='utf-8'), ['OTHER'], None))
    bad |= (not ok)
    print(f'{"✔" if ok else "✘"} 子ブロックの外の地の文も突合し、区間単位で原文へ戻す（li>ul>li）')
    # 構造の破損は差し戻しても合格にしない（閉じ忘れ・ブロック種別の変化）
    with tempfile.TemporaryDirectory() as d:
        d = pathlib.Path(d)
        (d / 's.html').write_text('<div><h2>FY27</h2><p>本文</p></div>', encoding='utf-8')
        (d / 'g1.html').write_text('<div><h2>FY27</h2><p>本文</p>', encoding='utf-8')
        (d / 'g2.html').write_text('<div><p>FY27</p><p>本文</p></div>', encoding='utf-8')
        r1, _ = run_compare(d / 'g1.html', d / 's.html', True, None)
        r2, _ = run_compare(d / 'g2.html', d / 's.html', True, None)
        ok = (not r1['ok'] and r1['unclosed'] == ['div']
              and not r2['ok'] and r2['failed'] and not r2['failed'][0]['restorable'])
    bad |= (not ok)
    print(f'{"✔" if ok else "✘"} 閉じ忘れ・ブロック種別の変化は --restore でも不合格のまま')
    print('OK' if not bad else 'NG')
    return bad


# ---------------------------------------------------------------- CLI
def main(argv) -> int:
    if '--selftest' in argv:
        return selftest()
    as_json = '--json' in argv
    restore = '--restore' in argv

    def opt(name):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None

    src, terms, values_f, out = opt('--source'), opt('--terms'), opt('--values'), opt('--out')
    consumed = {src, terms, values_f, out}
    files = [a for a in argv if not a.startswith('--') and a not in consumed]
    if not files:
        print(__doc__.split('使い方')[1].split('**差し替え')[0], file=sys.stderr)
        return 1
    gen_path = pathlib.Path(files[0])

    if src:
        res, fixed = run_compare(gen_path, pathlib.Path(src), restore, out)
        if fixed is not None:
            target = pathlib.Path(out) if out else gen_path
            target.write_text(fixed, encoding='utf-8')
            res['written'] = str(target)
        if as_json:
            print(json.dumps(res, ensure_ascii=False))
        else:
            name = res['file']
            if res.get('error'):
                print(f'{name}: NG {res["error"]}')
            elif not res['failed'] and not res.get('structural'):
                # 最終行は他の検査と同じ「<name>: OK」で終える
                # （ci-gates.sh は最終行の ': *OK$' で合否を判定するため）
                print(f'{name}: {res["elements"]} 段落を原文と突合')
                print(f'{name}: OK')
            else:
                head = f'{name}: {"戻した" if res["ok"] else "NG"} {len(res["failed"])} 段落'
                print(f'{head}（{res["elements"]} 段落中）')
                for st in res.get('structural', []):
                    print(f'  ✘ 構造の破損（差し戻しでは直らない・人が直す）: {st}')
                for f in res['failed']:
                    print(f'  [{f["i"]}] <{f["tag"]}> {f["text"]}')
                    for r in f['reasons']:
                        print(f'      – {r}')
                if res.get('written'):
                    print(f'  → 原文へ戻して書き出し: {res["written"]}')
        return 0 if res['ok'] else 1

    forbid = forbidden_from_terms(pathlib.Path(terms), '--strict-terms' in argv) if terms else []
    values = None
    if values_f:
        raw = json.loads(pathlib.Path(values_f).read_text(encoding='utf-8'))
        seq = raw.values() if isinstance(raw, dict) else raw
        values = {str(v).replace(',', '') for v in _flatten(seq)}
    findings = check_draft(gen_path.read_text(encoding='utf-8'), forbid, values)
    res = {'file': gen_path.name, 'ok': not findings, 'findings': findings,
           'forbidden_words': len(forbid)}
    if as_json:
        print(json.dumps(res, ensure_ascii=False))
    else:
        if not findings:
            print(f'{gen_path.name}: OK')
        else:
            print(f'{gen_path.name}: NG {len(findings)} 件')
            for f in findings:
                print(f'  – {f["kind"]}: {f["detail"]}')
    return 0 if res['ok'] else 1


def _flatten(seq):
    for v in seq:
        if isinstance(v, (list, tuple, set)):
            yield from _flatten(v)
        elif isinstance(v, dict):
            yield from _flatten(v.values())
        else:
            yield v


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
