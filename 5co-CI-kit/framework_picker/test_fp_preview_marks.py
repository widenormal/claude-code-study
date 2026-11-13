"""Framework ピッカー v3.21.1：提出プレビューではテキスト修正の印を出さない（若松さん指示 2026-11-11 19:37）。
python3 5co-CI-kit/framework_picker/test_fp_preview_marks.py
"""
import pathlib, re, sys, tempfile, unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fp_build

CSS = (HERE / 'ci-framework-picker.css').read_text(encoding='utf-8')
JS = (HERE / 'ci-framework-picker.js').read_text(encoding='utf-8')

MARK = ('<p>まえ<span class="ci-te-mark" data-te="e1" data-old="プライム感謝祭（PAS）" title="修正">'
        '<del>プライム感謝祭（PAS）</del><ins>PASプライム感謝祭</ins></span>あと</p>')

class T(unittest.TestCase):
    def test_css_hides_marks_in_preview_not_edit(self):
        # 編集モード（hidden なし）では印のスタイルが定義されている
        self.assertRegex(CSS, r'\.ci-te-mark\s*\{')
        self.assertIn('outline:1px dashed #101820', CSS)
        self.assertRegex(CSS, r'\.ci-te-mark\s+del\s*\{')
        self.assertRegex(CSS, r'\.ci-te-mark\s+ins\s*\{')
        # 提出プレビュー（ci-fp-hidden）と #static では印を消す
        self.assertIn('html.ci-fp-hidden .ci-te-mark', CSS)
        self.assertIn('html.ci-fp-static .ci-te-mark', CSS)
        hidden = CSS.split('html.ci-fp-hidden .ci-te-mark', 1)[1][:1200]
        self.assertIn('background:none', hidden)
        self.assertIn('outline:none', hidden)
        self.assertIn('html.ci-fp-hidden .ci-te-mark del', CSS)
        self.assertIn('html.ci-fp-hidden .ci-te-mark ins', CSS)
        ins = CSS.split('html.ci-fp-hidden .ci-te-mark ins', 1)[1][:400]
        self.assertIn('text-decoration:none', ins)

    def test_export_js_unwraps_marks(self):
        self.assertIn('function applyMarksOn(root, applyNumbers)', JS)
        self.assertIn(".ci-te-mark", JS)
        self.assertIn('m.parentNode.replaceChild', JS)
        self.assertIn('querySelector(\'ins\')', JS.replace(' ', '') or JS)

    def test_unwrap_te_marks_keeps_new_text_only(self):
        out, n = fp_build.unwrap_te_marks(MARK)
        self.assertEqual(n, 1)
        self.assertEqual(out, '<p>まえPASプライム感謝祭あと</p>')
        self.assertNotIn('ci-te-mark', out)
        self.assertNotIn('data-old', out)
        self.assertNotIn('<del>', out)
        self.assertNotIn('<ins>', out)

    def test_fp_build_external_strips_marks(self):
        html = (
            '<html><head><style>.ci-te-mark{outline:1px dashed #101820}</style></head>'
            '<body><section class="slide"><div class="hdr"></div>'
            + MARK +
            '</section></body></html>'
        )
        with tempfile.TemporaryDirectory() as td:
            inp = pathlib.Path(td) / 'in.html'
            outp = pathlib.Path(td) / 'out.html'
            inp.write_text(html, encoding='utf-8')
            # run external via functions (no overwrite)
            src = html
            src = fp_build.strip_fp(src)
            src, n = fp_build.unwrap_te_marks(src)
            self.assertGreaterEqual(n, 1)
            self.assertIn('PASプライム感謝祭', src)
            self.assertNotIn('ci-te-mark', src)
            self.assertNotIn('data-old', src)
            self.assertNotIn('<del>', src)

if __name__ == '__main__':
    unittest.main(verbosity=1)
