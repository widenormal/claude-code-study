#!/usr/bin/env python3
"""fp_external_check.py — 社外版に「図の型ピッカー」とローカル参照の痕跡が無いかを見る（CI kit 試作 2026-11-11）

  python3 fp_external_check.py deck.html            … 痕跡があれば FP_TRACE を出して終了コード1
  python3 fp_external_check.py deck.html --mode internal
                                                    … 社内版の確認用。ピッカー入りなら FP_INTERNAL? を警告（終了コード0）

見るもの（data: の画像本体は除く・<style>・<script>・コメント・属性まで全文）
  picker : ピッカーと文言修正の DOM・CSS・JS・型の一覧（ci-fp-・data-fp-・data-ci-fp・CIFP・ci-framework-…・ci-te-・data-te=・data-old=）
  path   : ローカルパス（file:・/workspace/・/home/・/Users/・/Volumes/・/mnt/・C:\\・共有ドライブ・マイドライブ・
           Shared drives・My Drive・GoogleDrive・CloudStorage・drive.google.com・.5co-CI-canonical・CLAUDE.md）
  ref    : 相対パスの参照（src= / href= / url() が data:・http(s):・# 以外）＝社外では開けない
  vendor : 仕入れ元の名前（Ignite・DMT・大文字小文字を区別しない・v3.19.0・契約上の必須）。
           英数字の途中（base64 など）は数えない。Shelpha は対象外（v3.19.2・若松さん決定 2026-11-03 v3.14.2＝
           顧客向けでもフッターに Shelpha 版を既定で出す。伏せる案件だけ ci-gates.sh --ban-shelpha）
"""
import re, sys

PICKER = (r'ci-fp[-:]|data-fp-|data-ci-fp|\bCIFP\b|ci-framework-(?:picker|catalog|selections)|frameworks_catalog|fp-selections|型ピッカー|型を選ぶ|Framework ピッカー|Framework▾|Framework を選ぶ|'
          r'ci-te-|data-te=|data-old=|文言を修正|文言修正|fp_apply_edits')
PATHS = (r'file:/|/workspace/|/home/[\w.-]+/|/Users/[\w.-]+/|/Volumes/|/mnt/[\w.-]+/|\b[A-Z]:\\\\|共有ドライブ|マイドライブ|'
         r'Shared drives|My Drive|GoogleDrive|CloudStorage|drive\.google\.com|\.5co-CI-canonical|CLAUDE\.md|claude\.md')
# 社外版に出してはいけない名前（契約上の必須・v3.19.0）。名前は社内のコード・テスト・この一覧にだけ置く
VENDOR_NAMES = ('Ignite', 'DMT')  # Shelpha は入れない（v3.14.2 の若松さん決定＝顧客向けにも版を出す・v3.19.2）
VENDOR = re.compile(r'(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])' % '|'.join(re.escape(n) for n in VENDOR_NAMES), re.I)
B64RUN = re.compile(r'[A-Za-z0-9+/=\r\n]{120,}')  # 空白の無い長い英数字の並び＝埋め込みデータ
REF = r'''(?:\s(?:src|href|xlink:href|poster)=["']|url\(["']?)(?!data:|https?:|#|mailto:|javascript:|blob:|about:|["')])([^"')\s>]+)'''


def check_text(s):
    s = re.sub(r'data:[^"\')\s]{64,}', 'data:…', s)
    lines = s.split('\n'); out = []
    for kind, pat in (('picker', PICKER), ('path', PATHS), ('ref', REF)):
        for m in re.finditer(pat, s):
            ln = s.count('\n', 0, m.start()) + 1
            snip = s[max(0, m.start() - 30):m.end() + 30].replace('\n', ' ')
            out.append('FP_TRACE %s L%d «%s»' % (kind, ln, snip))
            if len(out) > 60: out.append('…打ち切り'); return out
    v = B64RUN.sub(lambda m: '#' * len(m.group(0)), s)
    for m in VENDOR.finditer(v):
        ln = s.count('\n', 0, m.start()) + 1
        snip = s[max(0, m.start() - 30):m.end() + 30].replace('\n', ' ')
        out.append('FP_TRACE vendor L%d «%s»' % (ln, snip))
        if len(out) > 60: out.append('…打ち切り'); return out
    return out


def main(argv):
    files = [a for a in argv if not a.startswith('--') and a != 'internal']
    internal = '--mode' in argv and 'internal' in argv
    rc = 0
    for f in files:
        s = open(f, encoding='utf-8', errors='replace').read()
        if internal:
            if 'data-ci-fp="internal"' in s:
                print('%s: FP_INTERNAL? 社内版（型ピッカー入り）＝社外に出さない。社外版は fp_build.py external で作る' % f)
                print('%s: WARN' % f)
            else:
                print('%s: OK' % f)
            continue
        found = check_text(s)
        for x in found: print('%s: %s' % (f, x))
        if found: rc = 1; print('%s: NG（社外版に痕跡 %d 件）' % (f, len(found)))
        else: print('%s: OK' % f)
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
