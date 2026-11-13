#!/usr/bin/env python3
"""fp_apply_edits.py — 社内版で記録した文言の修正（*.fp-selections.json の edits）を正本デッキに反映する（CI kit 試作 2026-11-11）

  python3 fp_apply_edits.py deck.html edits.json -o deck_修正後.html [--allow-numbers] [--only e1,e2] [--dry-run]

- JSON に書かれた箇所だけを置き換える（一括リライト・正規表現での書き換えはしない）。
- 1件ごとに、スライド（slide）→ 元の文の段（node_text・node_k 番目）→ 位置（offset）で場所を決め、
  そこにある文字が「元の文（old）」と一致することを確かめてから「新しい文（new）」にする。合わなければその件は適用しない。
- 数字を含む修正（old か new に数字・JSON の numbers に関係なくここで判定し直す）は --allow-numbers が無ければ適用しない。
- 置換の前後で、全部の表について 行数・行ごとのセル数・ヘッダーの最終列・1列目の並び（行順）を照合し、
  修正した文以外で変わっていたら全体を中止する（ファイルを書かない）。
- 出力は必ず別名。入力と同じ名前・既にあるファイルには書かない。
"""
import argparse, html, json, pathlib, re, sys

NUM = re.compile(r'[0-9０-９]')


def mask(src):
    """script・style・コメント・data: を長さを保ったまま潰す（位置はそのまま使える）"""
    m = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', lambda x: ' ' * len(x.group(0)), src, flags=re.S | re.I)
    m = re.sub(r'<!--.*?-->', lambda x: ' ' * len(x.group(0)), m, flags=re.S)
    return m


def sections(src):
    ms = mask(src)
    starts = [m.start() for m in re.finditer(r'<section\b[^>]*\bclass="[^"]*\bslide\b', ms)]
    out = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(src)
        tag = re.match(r'<section\b[^>]*>', ms[s:]).group(0)
        sid = re.search(r'\bid="([^"]+)"', tag)
        out.append((sid.group(1) if sid else 'p%02d' % (i + 1), s, e))
    return out


SKIP_TAGS = ('script', 'style', 'button')
SKIP_CLASS = re.compile(r'class="(?:[^"]*\s)?(ci-hb|cm|ci-digest-btn)(?=[\s"])')  # クラス名の完全一致（ci-hb-on は対象外）


def text_runs(src, s, e):
    """section 内のテキストノード（生の位置つき）。ランタイムの段と同じく、ロゴの帯・表紙の数字・ボタンの中は数えない。"""
    ms = mask(src)
    runs, stack = [], []
    for m in re.finditer(r'<[^>]+>|[^<]+', ms[s:e]):
        tok = m.group(0); a = s + m.start()
        if tok.startswith('<'):
            t = re.match(r'</?([a-zA-Z0-9]+)', tok)
            if not t: continue
            name = t.group(1).lower()
            if tok.startswith('</'):
                while stack:
                    if stack.pop()[0] == name: break
            elif not tok.endswith('/>') and name not in ('img', 'br', 'hr', 'input', 'meta', 'link', 'source', 'path', 'use', 'circle', 'rect', 'line', 'polyline', 'polygon', 'stop', 'col', 'wbr'):
                stack.append((name, bool(SKIP_CLASS.search(tok)) or name in SKIP_TAGS))
            continue
        if any(x[1] for x in stack) or not tok.strip() and False:
            continue
        raw = src[a:a + len(tok)]
        runs.append({'raw': raw, 'text': html.unescape(raw), 'start': a, 'tag': stack[-1][0] if stack else ''})
    return runs


def tables_sig(src):
    ms = mask(src); sig = []
    for t in re.finditer(r'<table\b.*?</table>', ms, flags=re.S | re.I):
        body = src[t.start():t.end()]
        rows = re.findall(r'<tr\b.*?</tr>', body, flags=re.S | re.I)
        cells = [[re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', c))).strip()
                  for c in re.findall(r'<t[hd]\b.*?</t[hd]>', r, flags=re.S | re.I)] for r in rows]
        hdr = next((c for c, r in zip(cells, rows) if '<th' in r.lower()), cells[0] if cells else [])
        sig.append({'rows': len(rows), 'ncells': [len(c) for c in cells], 'hdr_last': hdr[-1] if hdr else '',
                    'col1': [c[0] if c else '' for c in cells]})
    return sig


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck'); ap.add_argument('edits'); ap.add_argument('-o', '--out')
    ap.add_argument('--allow-numbers', action='store_true'); ap.add_argument('--only'); ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    inp = pathlib.Path(a.deck); src = inp.read_text(encoding='utf-8')
    if 'data-ci-fp="internal"' in src:
        sys.exit('❌ 社内版（ピッカー入り）ではなく、元のデッキに当ててください')
    data = json.loads(pathlib.Path(a.edits).read_text(encoding='utf-8'))
    edits = data.get('edits', [])
    if a.only: keep = set(a.only.split(',')); edits = [e for e in edits if e.get('id') in keep]
    if not a.dry_run:
        if not a.out: sys.exit('-o が要ります')
        out = pathlib.Path(a.out)
        if out.resolve() == inp.resolve() or out.exists(): sys.exit('❌ 上書きしません（別名で出してください）: %s' % out)
    secs = {sid: (s, e) for sid, s, e in sections(src)}
    plan, report = [], []
    for ed in edits:
        eid, old, new = ed.get('id', '?'), ed.get('old', ''), ed.get('new', '')
        if not old or old == new:
            report.append((eid, 'SKIP 空・変更なし')); continue
        if NUM.search(old) or NUM.search(new):
            if not a.allow_numbers:
                report.append((eid, 'HOLD 数字を含む＝要確認（--allow-numbers が無いので適用しない）')); continue
        if ed.get('slide') not in secs:
            report.append((eid, 'NG スライド %s が無い' % ed.get('slide'))); continue
        runs = [r for r in text_runs(src, *secs[ed['slide']]) if r['text'] == ed.get('node_text')]
        k = int(ed.get('node_k', 0))
        if k >= len(runs):
            report.append((eid, 'NG 元の文の段が見つからない（デッキが変わった？）')); continue
        r = runs[k]; off = int(ed.get('offset', -1))
        if r['text'][off:off + len(old)] != old:
            report.append((eid, 'NG 位置の文字が元の文と一致しない')); continue
        if r['raw'] != r['text']:
            report.append((eid, 'NG 文字参照（&amp; など）を含む段は自動では置換しない')); continue
        if ed.get('tag') and r['tag'] and ed['tag'] != r['tag']:
            report.append((eid, 'NG 要素の種類が違う（%s≠%s）' % (ed['tag'], r['tag']))); continue
        p = r['start'] + off
        if any(not (p + len(old) <= q or q + l <= p) for q, l, *_ in plan):
            report.append((eid, 'NG 他の修正と重なる')); continue
        plan.append((p, len(old), html.escape(new, quote=False), eid, old, new))
        report.append((eid, 'OK 「%s」→「%s」（%s）' % (old, new, ed['slide'])))
    res = src
    for p, l, rep, *_ in sorted(plan, key=lambda x: -x[0]):
        res = res[:p] + rep + res[p + l:]
    # 表の照合（行数・セル数・ヘッダー最終列・1列目の並び）。修正した文の置き換えで説明できる差だけ許す
    before, after = tables_sig(src), tables_sig(res)
    def explained(b, c):
        return b == c or any(o in b and b.replace(o, n, 1) == c for *_, o, n in plan) or \
            any(o in b and re.sub(r'\s+', ' ', b.replace(o, n, 1)).strip() == c for *_, o, n in plan)
    broken = []
    if len(before) != len(after): broken.append('表の数 %d→%d' % (len(before), len(after)))
    for i, (b, c) in enumerate(zip(before, after)):
        if b['rows'] != c['rows'] or b['ncells'] != c['ncells']: broken.append('表%d 行・セル数' % (i + 1))
        if not explained(b['hdr_last'], c['hdr_last']): broken.append('表%d ヘッダー最終列「%s」→「%s」' % (i + 1, b['hdr_last'], c['hdr_last']))
        if len(b['col1']) != len(c['col1']) or not all(explained(x, y) for x, y in zip(b['col1'], c['col1'])): broken.append('表%d 行順（1列目）' % (i + 1))
    for eid, msg in report: print('  %s %s' % (eid, msg))
    if broken:
        print('❌ 表が崩れるため中止（書き出さない）: ' + ' / '.join(broken)); return 1
    print('表の照合 OK（%d 表）・適用 %d 件 / %d 件' % (len(before), len(plan), len(edits)))
    if a.dry_run or not plan:
        if not plan: print('適用できる修正がないので書き出しません')
        return 0 if plan or a.dry_run else 1
    out.write_text(res, encoding='utf-8'); print('出力: %s' % out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
