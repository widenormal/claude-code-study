#!/usr/bin/env python3
"""frameworks_catalog.json を作る（一度きりの生成スクリプト・kit 同梱）。
元: corporate-website staff preview の src/data/slide-patterns.ts（SLIDE-PATTERN 129種・修正依頼欄と同じID）。
family = 簡易プレビュー（数値なしの型見本 SVG）の種類。kit_fn = ci_frameworks.py で実データから描ける関数。"""
import json, re, sys, pathlib
if len(sys.argv) < 2: sys.exit('使い方: make_catalog.py <corporate-website>/src/data/slide-patterns.ts')
ts = open(sys.argv[1], encoding='utf-8').read()
arr = json.loads(re.search(r'SLIDE_PATTERNS: SlidePattern\[\] = (\[.*?\n\]);', ts, re.S).group(1))
RULES = [  # (正規表現, family) 先勝ち
 (r'waterfall', 'waterfall'), (r'stacked-bar', 'stacked'), (r'mekko', 'mekko'),
 (r'tornado', 'tornado'), (r'butterfly', 'butterfly'), (r'scatter|bubble', 'scatter'),
 (r'radar', 'radar'), (r'slope', 'slope'), (r'heatmap|harvey', 'heatmap'),
 (r'funnel', 'funnel'), (r'logic-tree|driver-tree|decision-tree|org-chart|minto', 'tree'),
 (r'positioning-matrix|risk-matrix|four-quadrant|nine-box', 'matrix'),
 (r'fishbone', 'fishbone'), (r'concentric|iceberg', 'concentric'), (r'venn', 'venn'),
 (r'pyramid|strategy-house|staircase|three-horizons', 'pyramid'),
 (r'cycle|pdca', 'cycle'), (r'hub|spoke|node-edge|bilateral', 'hub'),
 (r'donut|pie', 'donut'), (r'timeline|roadmap|milestone|swimlane|journey', 'timeline'),
 (r'flow|step|value-chain|problem-solution|before-after', 'flow'),
 (r'table|comparison|pricing|status', 'table'),
 (r'chart|kpi|metrics|dashboard|bar', 'bars'),
 (r'card|grid|canvas|segment', 'cards'),
]
KIT_FN = {  # ci_frameworks.py の関数（実データから描ける型）
 'mekko-market-map': 'mekko', 'heatmap-matrix-table': 'heatmap', 'funnel-conversion-stages': 'funnel',
 'scatter-bubble-positioning': 'bubble', 'waterfall-bridge-chart': 'waterfall',
 'slope-chart-before-after': 'slope', 'concentric-circles-market': 'concentric',
 'issue-logic-tree': 'tree', 'kpi-driver-tree': 'tree', 'two-col-list-and-chart': 'bars_line',
 'tornado-sensitivity-chart': 'ranges',
}
FIG_CATS = ['フレームワーク・分析', 'グラフ・データ', '図解・ダイアグラム', 'フロー・ステップ',
            'テーブル・比較', 'KPI・まとめ', 'カード・グリッド']
out = []
for p in arr:
    fam = next((f for r, f in RULES if re.search(r, p['id'])), 'text')
    name = re.sub(r'（[^（）]*）$', '', p['label'])
    d = {'id': p['id'], 'label': name, 'category': p['category'], 'family': fam,
         'figure': p['category'] in FIG_CATS}
    if p['id'] in KIT_FN: d['kit_fn'] = KIT_FN[p['id']]
    out.append(d)
RECOMMEND = {  # 図の種類ごとのおすすめ（先頭に出す）
 'table': ['heatmap-matrix-table', 'comparison-table-with-highlight', 'stacked-bar-100pct',
           'waterfall-bridge-chart', 'butterfly-comparison-chart', 'slope-chart-before-after'],
 'chart': ['waterfall-bridge-chart', 'stacked-bar-100pct', 'slope-chart-before-after',
           'chart-with-callout', 'kpi-bar-chart', 'tornado-sensitivity-chart'],
 'kpi': ['three-kpi-big-number', 'goal-kgi-kpi-dashboard', 'kpi-driver-tree',
         'waterfall-bridge-chart', 'donut-left-kpi-bar-right'],
 'diagram': ['issue-logic-tree', 'kpi-driver-tree', 'swimlane-process-flow',
             'positioning-matrix-2x2', 'mekko-market-map'],
}
cat = {'schema': 'ci-framework-catalog/1', 'version': '2026.11.11',
       'source': 'SLIDE-PATTERN 129種（修正依頼欄と同じID）',
       'figure_categories': FIG_CATS, 'recommend': RECOMMEND, 'patterns': out}
p = pathlib.Path(__file__).with_name('frameworks_catalog.json')
p.write_text(json.dumps(cat, ensure_ascii=False, indent=1), encoding='utf-8')
from collections import Counter
print(len(out), Counter(d['family'] for d in out))
