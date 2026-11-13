"""Framework ピッカー v3.21.0 の回帰テスト（stdlib＋node・ブラウザ不要）。
python3 5co-CI-kit/framework_picker/test_fp_v3210.py
- 「保存」ボタン・JSON のダウンロードが無い（若松さん指摘 2026-11-11）
- 単一選択（「複数選べます」「選択中 n 件」・見本のみの型を出さない）
- 表の値「630万」「¥114」「▲542万」「101.2%」を数字として読む
ブラウザでの確認（ダウンロード 0 件・単一選択・再押下で元の図・実データ・書き出し）は CIスライドの tools/test_no_save.py・test_single.py。"""
import pathlib, re, shutil, subprocess, json, unittest
JS = (pathlib.Path(__file__).resolve().parent / 'ci-framework-picker.js').read_text(encoding='utf-8')
class T(unittest.TestCase):
    def test_no_save_button(self):
        self.assertNotIn('>保存<', JS)
        self.assertNotIn('data-act="exp"', JS)
        self.assertNotIn('exportJSON', JS)
        self.assertNotIn('fp-selections.json', JS)
        self.assertNotIn('application/json', JS.replace("accept = 'application/json", ''))
        self.assertEqual(len(re.findall(r'\.download\s*=', JS)), 1)            # downloadBlob だけ
        self.assertEqual(len(re.findall(r'downloadBlob\(deckBase\(\)', JS)), 1)  # 呼ぶのは「修正を反映した版を書き出す」だけ
        self.assertIn("_修正反映.html'", JS)
    def test_single_select(self):
        for w in ('複数選べ', '選択中 ', '見本のみ'):
            self.assertNotIn(w, JS)
        self.assertIn('f.selected = [{ id: pid', JS)
        self.assertIn('if (cur === pid) { revertFig(curId); return; }', JS)
        self.assertNotIn('rec.forEach(add)', JS)                     # 描けない型をおすすめに足さない
        self.assertIn("return '';   // 数字で描けない型は描かない", JS)
    @unittest.skipUnless(shutil.which('node'), 'node が無い')
    def test_parse_cell(self):
        fn = re.search(r'function parseCell\(raw\) \{[\s\S]*?\n  \}', JS).group(0)
        code = fn + ';console.log(JSON.stringify(["630万","1,989万","¥114","▲542万","101.2%","—","先行","2億"].map(function(x){return parseCell(x).v})))'
        out = json.loads(subprocess.check_output(['node', '-e', code], text=True))
        self.assertEqual(out, [630, 1989, 114, -542, 101.2, None, None, 20000])
if __name__ == '__main__':
    unittest.main(verbosity=1)
