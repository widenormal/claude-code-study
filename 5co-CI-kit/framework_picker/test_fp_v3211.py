"""Framework ピッカー v3.21.1 の回帰テスト（stdlib・ブラウザ不要）。
python3 5co-CI-kit/framework_picker/test_fp_v3211.py
- バーの状態表記：旧「表示中」→「提出プレビュー」、旧「非表示」→「編集モード」（若松さん指示 2026-11-11 19:20）
- ボタンの text・title・aria-label が同じ文言
ブラウザでの目視は CIスライドの renders/bar_preview.png・bar_edit.png。
"""
import pathlib, unittest
JS = (pathlib.Path(__file__).resolve().parent / 'ci-framework-picker.js').read_text(encoding='utf-8')

class T(unittest.TestCase):
    def test_no_old_button_labels(self):
        self.assertNotIn('>表示中<', JS)
        self.assertNotIn("hide ? '非表示' : '表示中'", JS)
        self.assertNotIn('data-act="tog">表示中<', JS)

    def test_initial_button(self):
        self.assertIn(
            'data-act="tog" title="提出プレビュー" aria-label="提出プレビュー">提出プレビュー<',
            JS,
        )
        self.assertIn('aria-pressed="true"', JS)

    def test_toggle_mapping(self):
        self.assertIn("var lab = hide ? '編集モード' : '提出プレビュー'", JS)
        self.assertIn('b.textContent = lab', JS)
        self.assertIn('b.title = lab', JS)
        self.assertIn("b.setAttribute('aria-label', lab)", JS)
        self.assertIn("b.setAttribute('aria-pressed', hide ? 'false' : 'true')", JS)

if __name__ == '__main__':
    unittest.main(verbosity=1)
