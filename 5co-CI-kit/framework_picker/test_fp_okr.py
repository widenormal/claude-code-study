"""Framework ピッカー v3.21.1：OKR 型（若松さん指示 2026-11-11）。
python3 5co-CI-kit/framework_picker/test_fp_okr.py
"""
import json, pathlib, re, sys, tempfile, unittest

HERE = pathlib.Path(__file__).resolve().parent
JS = (HERE / 'ci-framework-picker.js').read_text(encoding='utf-8')
CSS = (HERE / 'ci-framework-picker.css').read_text(encoding='utf-8')
CAT = json.loads((HERE / 'frameworks_catalog.json').read_text(encoding='utf-8'))

OKR_ID = 'okr-objective-kr'

class Source(unittest.TestCase):
    def test_okr_is_registered_and_named_okr(self):
        self.assertIn("var OKR_ID = 'okr-objective-kr'", JS)
        self.assertIn("label: 'OKR'", JS)
        self.assertIn("SHORT[OKR_ID] = 'OKR'", JS)
        self.assertIn("FAM_JP.okr = 'OKR'", JS)
        self.assertRegex(JS, r'\bokr:\s*function')
        self.assertIn('function extractOkr', JS)
        self.assertIn('function canDrawOkr', JS)
        self.assertIn('function drawOkr', JS)
        self.assertIn('canDrawOkr(el)', JS)

    def test_recommend_puts_okr_first(self):
        self.assertIn('if (canDrawOkr(el))', JS)
        self.assertIn('out = [OKR_PT].concat', JS)
        self.assertEqual(CAT['recommend']['kpi'][0], OKR_ID)

    def test_requires_target_and_actual(self):
        self.assertIn('hasTarget', JS)
        self.assertIn('hasActual', JS)
        self.assertIn('obj.hasTarget && obj.hasActual', JS)
        self.assertIn('s.hasTarget && s.hasActual', JS)

    def test_existing_picker_rules(self):
        # 単一選択・保存ボタン無し・英語IDはサムネに出さない
        self.assertIn('単一選択', JS)
        self.assertNotIn('data-act="save"', JS)
        self.assertNotIn('exportJSON', JS)
        self.assertNotRegex(JS, r'data-act=["\']save["\']')
        self.assertIn("esc(shortName(pt))", JS)
        self.assertNotIn("<span class=\"nm\">' + pt.id", JS)
        self.assertNotIn("class=\"code\">' + pt.id", JS)

    def test_schematic_has_no_numbers_or_letters(self):
        # FAM.okr 本体にテキスト要素や数字ラベルを入れない
        m = re.search(r'okr:\s*function\s*\(\)\s*\{(.*?)\n    \}', JS, re.S)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertNotIn('<text', body)
        self.assertNotRegex(body, r'Objective|目標|KR')

    def test_preview_css_present(self):
        self.assertIn('ci-okr-live', CSS)


# Playwright が使えるときだけ、実データでのおすすめ順と描画を検証する
try:
    from playwright.sync_api import sync_playwright
    HAS_PW = True
except Exception:
    HAS_PW = False


FIXTURE = '''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<style>
.okr{text-align:center}
.slide{width:1120px;padding:20px}
</style>
</head>
<body>
<section class="slide" id="p01">
  <div class="okr" data-fp-fig="p01-1" data-fp-page="p01" data-fp-kind="kpi">
    <ul><li>
      <div class="nd big"><span class="nm">9月 Objective</span>
        <div class="box"><span class="lbl">目標</span><b>適正2,664万 ／ 必達2,373万</b></div>
        <div class="box mk"><span class="lbl">実績</span><b>2,402万</b>（対必達101.2%） <span style="font-weight:700;">○</span></div>
      </div>
      <ul><li class="sgrp"><div class="sgrp-row">
        <div class="nd cat"><span class="nm">NailEnvy</span>
          <div class="box"><span class="lbl">目標</span><b>544万</b></div>
          <div class="box mk"><span class="lbl">実績</span><b>552万</b>（101%） <span style="font-weight:700;">○</span></div>
        </div>
      </div></li></ul>
    </li></ul>
  </div>
</section>
<section class="slide" id="p02">
  <table class="sk" data-fp-fig="p02-1" data-fp-page="p02" data-fp-kind="table">
    <tr><th></th><th>目標</th><th>実績</th></tr>
    <tr><td>シリーズA</td><td>100万</td><td>90万</td></tr>
  </table>
</section>
<section class="slide" id="p03">
  <table class="sk" data-fp-fig="p03-1" data-fp-page="p03" data-fp-kind="chart">
    <tr><th></th><th>7月</th><th>8月</th></tr>
    <tr><td>売上</td><td>100万</td><td>110万</td></tr>
  </table>
</section>
<section class="slide" id="p04">
  <div data-fp-fig="p04-1" data-fp-page="p04" data-fp-kind="kpi">目標だけあります<div>目標 100万</div></div>
</section>
<script id="ci-fp-catalog" type="application/json">__CAT__</script>
<script>__JS__</script>
</body></html>
'''


@unittest.skipUnless(HAS_PW, 'playwright not available')
class Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cat = json.loads((HERE / 'frameworks_catalog.json').read_text(encoding='utf-8'))
        html = FIXTURE.replace('__CAT__', json.dumps(cat, ensure_ascii=False)).replace('__JS__', JS)
        cls.tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8')
        cls.tmp.write(html)
        cls.tmp.close()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch()
        cls.page = cls.browser.new_page()
        cls.page.goto('file://' + cls.tmp.name)
        cls.page.wait_for_function('() => window.CIFP && window.CIFP.extractOkr')

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        pathlib.Path(cls.tmp.name).unlink(missing_ok=True)

    def test_okr_first_when_data_exists(self):
        top = self.page.evaluate("() => CIFP.recSets('p01-1').top.map(p => ({id:p.id, name:CIFP.shortName(p)}))")
        self.assertTrue(top)
        self.assertEqual(top[0]['id'], OKR_ID)
        self.assertEqual(top[0]['name'], 'OKR')
        self.assertFalse(any(OKR_ID in (x.get('name') or '') for x in top))

    def test_table_with_target_actual_recommends_okr(self):
        top = self.page.evaluate("() => CIFP.recSets('p02-1').top.map(p => p.id)")
        self.assertEqual(top[0], OKR_ID)

    def test_no_recommend_without_target_and_actual(self):
        ids = self.page.evaluate("""() => {
          const a = CIFP.recSets('p03-1');
          const b = CIFP.recSets('p04-1');
          return {
            a: a.top.concat(a.others).map(p => p.id),
            b: b.top.concat(b.others).map(p => p.id),
            ok3: CIFP.canDrawOkr(document.querySelector('[data-fp-fig="p03-1"]')),
            ok4: CIFP.canDrawOkr(document.querySelector('[data-fp-fig="p04-1"]'))
          };
        }""")
        self.assertFalse(ids['ok3'])
        self.assertFalse(ids['ok4'])
        self.assertNotIn(OKR_ID, ids['a'])
        self.assertNotIn(OKR_ID, ids['b'])

    def test_draw_uses_only_page_values(self):
        html = self.page.evaluate("() => CIFP.markup('p01-1', CIFP.OKR_ID)")
        self.assertIn('2,664万', html)
        self.assertIn('2,373万', html)
        self.assertIn('2,402万', html)
        self.assertIn('NailEnvy', html)
        self.assertIn('544万', html)
        self.assertIn('552万', html)
        # ページに無い数字は作らない
        self.assertNotIn('999', html)
        self.assertIn('ci-okr-live', html)

    def test_thumb_label_is_okr_not_english_id(self):
        self.page.evaluate("() => CIFP.open('p01-1')")
        names = self.page.evaluate("""() => Array.from(document.querySelectorAll('#ci-fp-layer .ci-fp-thumb .nm')).map(n => n.textContent)""")
        self.assertIn('OKR', names)
        self.assertNotIn(OKR_ID, names)
        first = self.page.evaluate("""() => {
          const t = document.querySelector('#ci-fp-layer .ci-fp-thumbs .ci-fp-thumb');
          return t ? {name: t.querySelector('.nm').textContent, pid: t.getAttribute('data-pid')} : null;
        }""")
        self.assertEqual(first['name'], 'OKR')
        self.assertEqual(first['pid'], OKR_ID)


if __name__ == '__main__':
    unittest.main(verbosity=1)
