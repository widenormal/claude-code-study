#!/usr/bin/env python3
"""社外版の埋め込み画像を軽量化する（v3.21.1・若松さん指示 2026-11-11 19:24）。

社内版（fp_build.py internal）では呼ばない。社外版の書き出しでだけ、
inline_local のあとに lighten_html() を通す。

- 写真（PNG / JPEG、透過の無いラスタ）：WebP 品質 85、長辺 1600px 以下
- ロゴ・切り抜きなど透過が必要なラスタ：透過 WebP（小さなロゴは可逆、大きい切り抜きは品質 85）
- SVG はそのまま（ロゴや使っている kit 背景の見た目を崩さない）
- このデッキの要素に当てはまらない CSS の kit 背景（url(data:image…)）は除外する
- 変換後が大きくなるときは元のバイトを残す
"""
from __future__ import annotations

import base64
import html.parser
import io
import re
from typing import Optional

MAX_EDGE = 1600
WEBP_Q = 85
LOGO_EDGE = 400  # これ以下で透過があるものはロゴ扱い（可逆 WebP）

_DATA_RASTER = re.compile(
    r'data:image/(png|jpe?g|gif|webp|bmp)(;charset=[^;,]+)?;base64,([A-Za-z0-9+/=\s]+)',
    re.I,
)
_STYLE = re.compile(r'(<style\b[^>]*>)(.*?)(</style>)', re.S | re.I)
_URL_DATA = re.compile(r'url\(\s*([\'"]?)(data:image/[^)\'"]+)\1\s*\)', re.I)
_LOGO_HINT = re.compile(r'logo|lockup|glyph|favicon|icon|wordmark', re.I)


# ---------- DOM（未使用 CSS 判定用） ----------
class _El:
    __slots__ = ('tag', 'eid', 'classes', 'parent', 'children')

    def __init__(self, tag, eid, classes, parent):
        self.tag = tag
        self.eid = eid
        self.classes = classes
        self.parent = parent
        self.children = []


class _Dom(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = _El('[root]', '', set(), None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        el = _El(tag.lower(), a.get('id') or '', set((a.get('class') or '').split()), self.cur)
        self.cur.children.append(el)
        if tag.lower() not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                               'link', 'meta', 'source', 'track', 'wbr'}:
            self.cur = el

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        # void は cur を動かしていない。非 void の自己閉じは戻す
        if self.cur is not self.root and self.cur.tag == tag.lower() and not self.cur.children:
            # startend で非 void が来た場合だけ戻る（通常は void）
            pass
        if tag.lower() not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                               'link', 'meta', 'source', 'track', 'wbr'}:
            if self.cur.tag == tag.lower():
                self.cur = self.cur.parent or self.root

    def handle_endtag(self, tag):
        tag = tag.lower()
        cur = self.cur
        while cur is not None:
            if cur.tag == tag:
                self.cur = cur.parent or self.root
                return
            cur = cur.parent


def parse_dom(src: str) -> _El:
    masked = re.sub(r'data:[^"\')\s]{32,}', lambda m: 'x' * len(m.group(0)), src)
    masked = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', lambda m: ' ' * len(m.group(0)),
                    masked, flags=re.S | re.I)
    d = _Dom()
    try:
        d.feed(masked)
        d.close()
    except html.parser.HTMLParseError:
        pass
    return d.root


def _iter_el(el: _El):
    yield el
    for c in el.children:
        yield from _iter_el(c)


def _match_simple(el: _El, simple: str) -> bool:
    simple = simple.strip()
    if not simple or simple in ('*', ':root'):
        return True
    simple = re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?', '', simple).strip() or '*'
    if simple == '*':
        return True
    m = re.fullmatch(r'([a-zA-Z][\w-]*)?(#[\w-]+)?((?:\.[\w-]+)*)', simple)
    if not m:
        return False
    tag, eid, classes = m.group(1), m.group(2), m.group(3)
    if tag and el.tag != tag.lower():
        return False
    if eid and el.eid != eid[1:]:
        return False
    if classes:
        need = set(classes.split('.'))
        need.discard('')
        if not need.issubset(el.classes):
            return False
    return True


def _match_branch(el: _El, branch: str) -> bool:
    """スペース（子孫）と >（子）だけのシンプルな枝。解けなければ False。"""
    branch = branch.strip()
    if not branch or re.search(r'[+~\[\]=]|:not\(|:is\(|:where\(|:has\(', branch):
        return False
    parts = re.split(r'\s*(>)\s*|\s+', branch.strip())
    parts = [p for p in parts if p]
    # parts は [sel, '>', sel, sel, ...] または [sel, sel]
    # 右端が対象要素。左へ祖先を辿る
    def walk(el, parts):
        if not parts:
            return True
        if parts[-1] == '>':
            return False
        sel = parts[-1]
        if not _match_simple(el, sel):
            return False
        rest = parts[:-1]
        if not rest:
            return True
        if rest[-1] == '>':
            return el.parent is not None and walk(el.parent, rest[:-1])
        # 子孫：いずれかの祖先
        p = el.parent
        while p is not None:
            if walk(p, rest):
                return True
            p = p.parent
        return False
    return walk(el, parts)


def selector_used(root: _El, selector: str) -> Optional[bool]:
    """要素に当てはまるか。解けないセレクタは None（残す）。"""
    selector = selector.strip()
    if not selector or selector.startswith('@'):
        return None
    branches = [b.strip() for b in selector.split(',') if b.strip()]
    if not branches:
        return None
    known = True
    for br in branches:
        if re.search(r'[+~\[\]=]|:not\(|:is\(|:where\(|:has\(', br):
            known = False
            continue
        for el in _iter_el(root):
            if el.tag == '[root]':
                continue
            if _match_branch(el, br):
                return True
        # html / body / :root はパーサが拾えないことがある
        if re.fullmatch(r'(html|body|:root)(\[.*\])?', br.strip(), re.I):
            return True
    if not known:
        return None
    return False


def _mask_css_comments(css: str) -> str:
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def _iter_css_rules(css: str):
    """(selector, body_start, body_end) をネスト（@media 内も）出す。"""
    masked = _mask_css_comments(css)
    n = len(masked)

    def walk(lo, hi):
        i = lo
        while i < hi:
            while i < hi and masked[i].isspace():
                i += 1
            if i >= hi:
                return
            if masked[i] == '}':
                return
            # セレクタまたは at-rule
            j = i
            depth = 0
            while j < hi:
                if masked[j] == '{':
                    break
                if masked[j] == ';' and depth == 0 and masked[i] == '@':
                    j += 1
                    i = j
                    break
                j += 1
            else:
                return
            if masked[i] == '@' and (j >= hi or masked[j] != '{'):
                continue
            if j >= hi or masked[j] != '{':
                return
            # body
            sel = css[i:j].strip()
            b0 = j + 1
            d = 1
            k = b0
            while k < hi and d:
                if masked[k] == '{':
                    d += 1
                elif masked[k] == '}':
                    d -= 1
                k += 1
            b1 = k - 1
            if sel.startswith('@'):
                yield from walk(b0, b1)
            else:
                yield sel, b0, b1
            i = k

    yield from walk(0, n)


def strip_unused_kit_bg(src: str, root: Optional[_El] = None) -> tuple[str, int]:
    """要素に当てはまらない CSS の url(data:image…) を none にする。"""
    if root is None:
        root = parse_dom(src)
    removed = 0

    def fix_style(m):
        nonlocal removed
        css = m.group(2)
        # ルール単位で、使われていないセレクタの data URI だけを外す
        # 後ろから置換して位置を保つ
        cuts = []
        for sel, b0, b1 in _iter_css_rules(css):
            used = selector_used(root, sel)
            if used is not False:
                continue
            for u in _URL_DATA.finditer(css, b0, b1):
                cuts.append(u)
        if not cuts:
            return m.group(0)
        out = css
        for u in sorted(cuts, key=lambda x: -x.start()):
            out = out[:u.start()] + 'none' + out[u.end():]
            removed += 1
        return m.group(1) + out + m.group(3)

    return _STYLE.sub(fix_style, src), removed


# ---------- ラスタの WebP 化 ----------
def pillow_available() -> bool:
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


def _useful_alpha(im) -> bool:
    from PIL import Image
    if im.mode == 'P':
        if 'transparency' in im.info:
            im = im.convert('RGBA')
        else:
            return False
    if im.mode in ('LA', 'PA'):
        im = im.convert('RGBA')
    if im.mode != 'RGBA':
        return False
    band = im.getchannel('A')
    amin, amax = band.getextrema()
    return amin < 250


def _resize_max_edge(im, edge=MAX_EDGE):
    from PIL import Image
    w, h = im.size
    m = max(w, h)
    if m <= edge:
        return im
    scale = edge / m
    return im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.Resampling.LANCZOS)


def _webp_bytes(im, *, lossless: bool, quality: int = WEBP_Q) -> bytes:
    buf = io.BytesIO()
    kw = dict(format='WEBP', method=6)
    if lossless:
        kw['lossless'] = True
    else:
        kw['quality'] = quality
    im.save(buf, **kw)
    return buf.getvalue()


def _is_animated(im) -> bool:
    try:
        return int(getattr(im, 'n_frames', 1) or 1) > 1
    except Exception:
        return False


def lighten_raster(raw: bytes, mime: str, *, logo_hint: bool = False) -> tuple[Optional[bytes], str]:
    """(新しいバイト, 説明)。変換しないときは (None, 理由)。"""
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:
        return None, 'decode-fail'
    if _is_animated(im):
        return None, 'animated'
    mime = (mime or '').lower()
    has_alpha = _useful_alpha(im)
    if has_alpha:
        im = im.convert('RGBA')
        im = _resize_max_edge(im)
        q85_b = _webp_bytes(im, lossless=False, quality=WEBP_Q)
        # ロゴは見た目優先：可逆が元より小さければ可逆。切り抜きは品質85（透過付き）
        if logo_hint or max(im.size) <= LOGO_EDGE:
            lossless_b = _webp_bytes(im, lossless=True)
            if len(lossless_b) < len(raw):
                out, kind = lossless_b, 'logo-webp'
            elif len(q85_b) < len(raw):
                out, kind = q85_b, 'logo-webp'
            else:
                return None, 'not-smaller'
        else:
            out, kind = q85_b, 'cutout-webp'
    else:
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        elif im.mode == 'L':
            pass
        im = _resize_max_edge(im)
        if im.mode == 'P':
            im = im.convert('RGB')
        out = _webp_bytes(im.convert('RGB') if im.mode != 'L' else im, lossless=False, quality=WEBP_Q)
        kind = 'photo-webp'
    if len(out) >= len(raw) and max(Image.open(io.BytesIO(raw)).size) <= MAX_EDGE:
        return None, 'not-smaller'
    return out, kind


def _logo_hint_at(src: str, pos: int, end: int | None = None) -> bool:
    pre = src[max(0, pos - 300):pos]
    post = src[end:end + 220] if end is not None else ''
    return bool(_LOGO_HINT.search(pre) or _LOGO_HINT.search(post))


def recompress_rasters(src: str) -> tuple[str, dict]:
    stats = {'photo-webp': 0, 'cutout-webp': 0, 'logo-webp': 0, 'kept': 0, 'bytes_in': 0, 'bytes_out': 0, 'skipped_pillow': False}
    if not pillow_available():
        stats['skipped_pillow'] = True
        return src, stats
    cache: dict[tuple, tuple] = {}

    def repl(m):
        mime, _cs, b64 = m.group(1), m.group(2), m.group(3)
        raw = base64.b64decode(re.sub(r'\s+', '', b64))
        key = (mime.lower(), raw, _logo_hint_at(src, m.start(), m.end()))
        stats['bytes_in'] += len(raw)
        if key not in cache:
            cache[key] = lighten_raster(raw, 'image/' + mime, logo_hint=key[2])
        out, kind = cache[key]
        if not out:
            stats['kept'] += 1
            stats['bytes_out'] += len(raw)
            return m.group(0)
        stats[kind] = stats.get(kind, 0) + 1
        stats['bytes_out'] += len(out)
        return 'data:image/webp;base64,' + base64.b64encode(out).decode('ascii')

    return _DATA_RASTER.sub(repl, src), stats


def lighten_html(src: str) -> tuple[str, dict]:
    root = parse_dom(src)
    src, n_bg = strip_unused_kit_bg(src, root)
    src, st = recompress_rasters(src)
    st['unused_bg'] = n_bg
    return src, st


def format_stats(st: dict, before_len: int, after_len: int) -> str:
    def mb(n):
        return '%.2fMB' % (n / 1048576)
    if st.get('skipped_pillow'):
        return ('埋め込み画像の軽量化: Pillow が無いため写真の WebP 化はしませんでした。'
                '未使用の kit 背景 %d 件を除外。HTML %s（WebP 化なし）' % (
                    st.get('unused_bg', 0), mb(after_len)))
    return ('埋め込み画像の軽量化: 未使用の kit 背景 %d 件を除外、'
            '写真 %d・切り抜き %d・ロゴ %d を WebP に（変換なし %d）。'
            '画像バイト %s → %s／HTML %s → %s' % (
                st.get('unused_bg', 0),
                st.get('photo-webp', 0), st.get('cutout-webp', 0), st.get('logo-webp', 0),
                st.get('kept', 0),
                mb(st.get('bytes_in', 0)), mb(st.get('bytes_out', 0)),
                mb(before_len), mb(after_len),
            ))
