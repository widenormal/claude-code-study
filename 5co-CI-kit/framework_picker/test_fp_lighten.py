"""社外版の埋め込み画像の軽量化（v3.21.1）の回帰テスト（stdlib＋Pillow・ブラウザ不要）。
python3 5co-CI-kit/framework_picker/test_fp_lighten.py
"""
import base64, io, pathlib, sys, unittest
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fp_lighten
import fp_build

def png_bytes(w, h, color, alpha=None):
    mode, px = ('RGBA', color + (alpha,)) if alpha is not None else ('RGB', color)
    im = Image.new(mode, (w, h), px)
    if alpha is not None:
        # 端だけ透明、中央は不透明＝切り抜き風
        pxls = im.load()
        for y in range(h):
            for x in range(w):
                if x < 4 or y < 4 or x >= w-4 or y >= h-4:
                    pxls[x, y] = (0, 0, 0, 0)
                else:
                    pxls[x, y] = color + (255,)
    buf = io.BytesIO(); im.save(buf, format='PNG'); return buf.getvalue()

def jpeg_bytes(w, h, color):
    im = Image.new('RGB', (w, h), color)
    buf = io.BytesIO(); im.save(buf, format='JPEG', quality=95); return buf.getvalue()

def data_uri(mime, raw):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(raw).decode())

class T(unittest.TestCase):
    def test_photo_jpeg_to_webp_and_resize(self):
        raw = jpeg_bytes(2000, 1000, (20, 80, 180))
        out, kind = fp_lighten.lighten_raster(raw, 'image/jpeg')
        self.assertEqual(kind, 'photo-webp')
        self.assertIsNotNone(out)
        self.assertLess(len(out), len(raw))
        im = Image.open(io.BytesIO(out))
        self.assertEqual(im.format, 'WEBP')
        self.assertLessEqual(max(im.size), 1600)
        self.assertEqual(im.size, (1600, 800))

    def test_opaque_png_to_webp(self):
        raw = png_bytes(80, 60, (10, 20, 30))
        out, kind = fp_lighten.lighten_raster(raw, 'image/png')
        # 小さい単色 PNG は WebP より小さいことがあり、そのときは残す
        if out is None:
            self.assertEqual(kind, 'not-smaller')
        else:
            self.assertEqual(kind, 'photo-webp')
            self.assertEqual(Image.open(io.BytesIO(out)).format, 'WEBP')

    def test_cutout_keeps_alpha(self):
        raw = png_bytes(600, 800, (200, 40, 40), alpha=255)
        out, kind = fp_lighten.lighten_raster(raw, 'image/png', logo_hint=False)
        self.assertIsNotNone(out)
        self.assertIn(kind, ('cutout-webp', 'logo-webp'))
        im = Image.open(io.BytesIO(out)).convert('RGBA')
        self.assertEqual(im.getpixel((0, 0))[3], 0)
        self.assertEqual(im.getpixel((im.size[0]//2, im.size[1]//2))[3], 255)
        # 中央の色が残る
        rgb = im.getpixel((im.size[0]//2, im.size[1]//2))[:3]
        self.assertTrue(all(abs(a-b) < 20 for a, b in zip(rgb, (200, 40, 40))), rgb)

    def test_small_logo_alpha(self):
        raw = png_bytes(64, 32, (16, 24, 32), alpha=255)
        out, kind = fp_lighten.lighten_raster(raw, 'image/png', logo_hint=True)
        if out is None:
            self.assertEqual(kind, 'not-smaller')
            return
        self.assertIn(kind, ('logo-webp', 'cutout-webp'))
        im = Image.open(io.BytesIO(out)).convert('RGBA')
        self.assertEqual(im.getpixel((0, 0))[3], 0)
        self.assertGreater(im.getpixel((32, 16))[3], 200)

    def test_svg_left_alone_in_html(self):
        svg = data_uri('image/svg+xml', b'<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"/>')
        html = '<html><body><img class="mall-logo" src="%s"></body></html>' % svg
        out, st = fp_lighten.recompress_rasters(html)
        self.assertIn(svg, out)
        self.assertEqual(st['photo-webp'] + st['cutout-webp'] + st['logo-webp'], 0)

    def test_unused_kit_bg_stripped_used_kept(self):
        tiny = base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>').decode()
        used = base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg" id="used"/>').decode()
        css = (
            '.slide.light{background:#fff url("data:image/svg+xml;base64,%s");}'
            '.cover-full .numfield-full{background-image:url("data:image/svg+xml;base64,%s");}'
        ) % (tiny, used)
        html = (
            '<html><head><style>%s</style></head>'
            '<body><section class="slide cover-full"><div class="numfield-full"></div></section>'
            '</body></html>'
        ) % css
        out, n = fp_lighten.strip_unused_kit_bg(html)
        self.assertEqual(n, 1)
        self.assertNotIn(tiny, out)
        self.assertIn(used, out)
        self.assertRegex(out, r'\.slide\.light\{background:#fff none;\}')

    def test_internal_build_does_not_call_lighten(self):
        # 社内版の経路は inline_local のみ。lighten_html は external の main だけ。
        src = pathlib.Path(fp_build.__file__).read_text(encoding='utf-8')
        # internal 分岐に lighten が無いこと、external 分岐にあること
        self.assertIn('fp_lighten.lighten_html', src)
        int_part = src.split("if a.mode == 'internal':", 1)[1].split('sel = json.loads', 1)[0]
        self.assertNotIn('lighten_html', int_part)

    def test_fp_build_external_lightens(self):
        import tempfile, os
        raw = jpeg_bytes(1200, 800, (40, 120, 200))
        uri = data_uri('image/jpeg', raw)
        html = (
            '<html><head><style>'
            '.slide.light{background:#fff url("data:image/svg+xml;base64,%s");}'
            '</style></head><body>'
            '<section class="slide"><img src="%s" alt="x"></section>'
            '</body></html>'
        ) % (base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>').decode(), uri)
        with tempfile.TemporaryDirectory() as td:
            inp = pathlib.Path(td) / 'in.html'
            outp = pathlib.Path(td) / 'out.html'
            inp.write_text(html, encoding='utf-8')
            # 直接 lighten_html（fp_build external と同じ関数）
            res, st = fp_lighten.lighten_html(html)
            self.assertGreaterEqual(st['unused_bg'], 1)
            self.assertIn('data:image/webp;base64,', res)
            self.assertNotIn('data:image/jpeg', res)
            self.assertIn('none', res)


    def test_skip_webp_without_pillow(self):
        """Pillow が import できないときは WebP 化を飛ばし、書き出しは成功する。"""
        import builtins, sys
        saved = {k: sys.modules[k] for k in list(sys.modules) if k == 'PIL' or k.startswith('PIL.')}
        real_import = builtins.__import__
        def fake_import(name, *a, **kw):
            if name == 'PIL' or name.startswith('PIL.'):
                raise ImportError('no pillow (test)')
            return real_import(name, *a, **kw)
        for k in list(sys.modules):
            if k == 'PIL' or k.startswith('PIL.'):
                del sys.modules[k]
        builtins.__import__ = fake_import
        try:
            raw = jpeg_bytes(800, 400, (20, 80, 180))
            uri = data_uri('image/jpeg', raw)
            tiny = __import__('base64').b64encode(b'<svg xmlns="http://www.w3.org/2000/svg"/>').decode()
            html = (
                '<html><head><style>'
                '.slide.light{background:#fff url("data:image/svg+xml;base64,%s");}'
                '</style></head><body>'
                '<section class="slide"><img src="%s" alt="x"></section>'
                '</body></html>'
            ) % (tiny, uri)
            # lighten_html must not raise
            res, st = fp_lighten.lighten_html(html)
            self.assertTrue(st.get('skipped_pillow'))
            self.assertEqual(st.get('photo-webp', 0), 0)
            # JPEG はそのまま残る
            self.assertIn('data:image/jpeg', res)
            self.assertIn(uri.split(',')[1][:40], res)
            # 未使用背景の除外は Pillow なしでも行う
            self.assertGreaterEqual(st.get('unused_bg', 0), 1)
            self.assertNotIn(tiny, res)
            msg = fp_lighten.format_stats(st, len(html), len(res))
            self.assertIn('Pillow', msg)
        finally:
            builtins.__import__ = real_import
            sys.modules.update(saved)

if __name__ == '__main__':
    unittest.main(verbosity=1)
