"""ws_photo の単体テスト（stdlib unittest・ブラウザ不要）。
python3 5co-CI-kit/ws_photo/test_ws_photo.py
素材ファイルは一時フォルダに小さな WebP を作って使う（実素材は不要）。"""
import json, pathlib, sys, tempfile, unittest
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ws_photo
from PIL import Image

DECK = ('<html lang="ja"><head></head><body>'
        '<section class="slide" id="p01" data-cover="1"><h1>表紙</h1></section>'
        '<section class="slide" id="p02"><h2 class="title">売上｜9月は必達</h2><p>購買 注文 検索 売上</p></section>'
        '<section class="slide" id="p06"><h2 class="title">広告｜DSP</h2><p>広告 DSP スポンサー広告 SNS</p></section>'
        '<section class="slide" id="p09"><h2 class="title">施策｜計画</h2><p>施策 計画 進捗</p></section>'
        '</body></html>')

class T(unittest.TestCase):
    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp())
        for n in ('c_f', 'c_m', 'inf_nail', 'inf_skin', 'cons'):
            Image.new('RGBA', (70, 100), (200, 100, 100, 255)).save(self.d / (n + '.webp'))
        A = lambda **k: dict(dict(status='approved', external_ok=False, caption=k.get('persona'), alt=k.get('persona') + '（架空の人物）'), **k)
        self.L = dict(categories={'nail': {'kw': 'ネイル|マニキュア', 'audience': 'female'},
                                  'detergent': {'kw': '洗剤', 'audience': None}},
                      assets=[A(id='c_f', persona='consumer', gender='female', age='30-39', categories=['*'], file='c_f.webp'),
                              A(id='c_m', persona='consumer', gender='male', age='30-39', categories=['*'], file='c_m.webp'),
                              A(id='inf_nail', persona='influencer', gender='female', age='20-39', categories=['nail'], file='inf_nail.webp', external_ok=True, caption='ネイルのインフルエンサー'),
                              A(id='inf_skin', persona='influencer', gender='female', age='20-39', categories=['skincare'], file='inf_skin.webp', external_ok=True),
                              A(id='cand', persona='influencer', gender='female', age='20-39', categories=['nail'], file='inf_nail.webp', status='candidate'),
                              A(id='cons', persona='consultant', gender='female', age='30-39', categories=['*'], file='cons.webp')])
        self.lp = self.d / 'assets.json'; self.lp.write_text(json.dumps(self.L, ensure_ascii=False), encoding='utf-8')

    def chosen(self, deck=DECK, external=False, **kw):
        L = ws_photo.load_ledger(self.lp); prof = ws_photo.deck_profile(deck, L, **kw)
        ch, why = ws_photo.select_assets(L, prof, internal=not external)
        return {k: v['id'] for k, v in ch.items()}, why, prof

    def test_declared_nail_female(self):
        d = DECK.replace('<html lang="ja"', '<html lang="ja" data-ws-category="nail" data-ws-audience="female 20-59"')
        ch, _, prof = self.chosen(d)
        self.assertEqual(prof['category'], 'nail')
        self.assertEqual(ch, {'consumer': 'c_f', 'influencer': 'inf_nail', 'consultant': 'cons'})

    def test_category_default_audience(self):
        ch, _, _ = self.chosen(category='nail')       # nail の既定＝女性
        self.assertEqual(ch.get('consumer'), 'c_f')

    def test_male_audience(self):
        ch, _, _ = self.chosen(category='nail', audience='male')
        self.assertEqual(ch.get('consumer'), 'c_m')
        self.assertNotIn('influencer', ch)            # 男性のネイルのインフルエンサー素材は無い

    def test_undetermined_only_consultant(self):
        ch, why, _ = self.chosen()
        self.assertEqual(ch, {'consultant': 'cons'})
        self.assertIn('consumer', why)

    def test_influencer_needs_exact_category(self):
        ch, _, _ = self.chosen(category='detergent', audience='female')
        self.assertNotIn('influencer', ch)            # 汎用・別カテゴリーは使わない
        self.assertEqual(ch.get('consumer'), 'c_f')

    def test_external_only_external_ok(self):
        ch, why, _ = self.chosen(category='nail', external=True)
        self.assertEqual(ch, {'influencer': 'inf_nail'})
        self.assertNotIn('cand', ch.values())

    def test_absent_file_not_used(self):
        (self.d / 'cons.webp').unlink()
        ch, _, _ = self.chosen(category='nail')
        self.assertNotIn('consultant', ch)

    def test_apply_tags_and_declares(self):
        html, pages = ws_photo.apply(DECK, self.lp, category='nail', audience='female 20-59')
        self.assertIn('data-ws-category="nail"', html)
        self.assertIn('data-ws-audience="female 20-59"', html)
        kinds = dict(pages)
        self.assertNotIn('p01', kinds)                # 表紙は入れない
        self.assertEqual(kinds.get('p02'), 'consumer')
        self.assertEqual(kinds.get('p06'), 'influencer')
        self.assertEqual(kinds.get('p09'), 'consultant')
        self.assertEqual(html.count('id="ws-photo-js"'), 1)
        html2, _ = ws_photo.apply(html, self.lp, category='nail', audience='female 20-59')
        self.assertEqual(html2.count('id="ws-photo-js"'), 1)   # 冪等
        self.assertEqual(html2.count('data-ws-category='), 1)

    def test_external_apply_has_no_internal_assets(self):
        html, _ = ws_photo.apply(DECK, self.lp, external=True, category='nail')
        cfg = json.loads(html.split('id="ws-photo-cfg">')[1].split('</script>')[0].replace('<\\/', '</'))
        self.assertEqual(sorted(cfg['assets']), ['influencer'] if 'influencer' in cfg['assets'] else [])

if __name__ == '__main__':
    unittest.main(verbosity=1)
