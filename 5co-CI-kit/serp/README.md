# serp/ — Amazon検索順位の根拠ページ（SERP）

規定の正＝`5co-CI-kit/FIGURES_GUIDE.md` §2-4。ここは道具置き場。
**顧客名・ASIN・検索語は kit に置かない**（案件フォルダの `_context/serp_targets.yaml` に置く）。
見本だけは `sample/` に入れてある。

| ファイル | 役割 |
|---|---|
| `serp_shot.py` | 取得（ログアウト・PC・届け先固定・5ページまで・12秒以上あけ・CAPTCHA で停止）。毎回 `results.json` と日付入りの写しを書く |
| `SERP_TARGETS_TEMPLATE.yaml` | 案件側に置く取得指定の雛形（検索語・ASIN・ブランド・閾値・届け先） |
| `serp_diff.py` | 前回比（キーワード×商品の 前回順位／今回順位／↑↓→／圏外の出入り・両方の取得日時） |
| `serp_redact.py` | 配布用の `results.json`（郵便番号・番地を落として区までにする。順位・日時は不変） |
| `serp_strips.py` | 検索結果の段（帯）の切り出し・実線枠＋順位バッジ・点線枠＋「スポンサー n」 |
| `serp_page.py` | ページの組み立て（見出し・要点・帯・ギャップ枠・根拠パネル・注記・出所） |
| `SERP_PAGE_TEMPLATE.yaml` | ページ組み立ての雛形 |
| `serp_check.py` | 検品（`ci-gates.sh --serp` から呼ぶ。`SERP_SHOT?` の警告＋出所ルールの違反は落とす） |
| `test_serp_mock.py` | 127.0.0.1 の模擬ページで取得手順を通し確認（Amazon に通信しない） |
| `sample/` | 見本（day-2 のデータ＋前回比）。作り直し方は `sample/README.md` |

## 手順（1回ぶん）

```bash
# 0) 案件フォルダに取得指定を置く（雛形をコピーして埋める）
cp 5co-CI-kit/serp/SERP_TARGETS_TEMPLATE.yaml <案件>/_context/serp_targets.yaml

# 1) 取得（ログアウト・PC・届け先固定。1回で最大5ページ）
python3 5co-CI-kit/serp/serp_shot.py <案件>/_context/serp_targets.yaml -o <案件>/serp/$(date +%F)/

# 2) 前回比（同じ条件で撮った前回と突き合わせる）
python3 5co-CI-kit/serp/serp_diff.py <案件>/serp/<前回>/results.json <案件>/serp/<今回>/results.json --md \
  -o <案件>/qa/serp_diff_<前回>_to_<今回>.md

# 3) 配布用の写し（郵便番号を落とす）
python3 5co-CI-kit/serp/serp_redact.py <案件>/serp/<今回>/results.json -o <案件>/src/results.json

# 4) ページを組む
python3 5co-CI-kit/serp/serp_page.py <案件>/_context/serp_page.yaml

# 5) 検品
bash 5co-CI-kit/ci-gates.sh --serp <案件>/<デッキ>.html
```

## 繰り返して撮る（同じ条件で）

順位は日内でも動く。**条件をそろえた回を重ねる**ことではじめて前回比が読める。

- そろえるもの＝ログアウト・PC・画面幅・届け先・言語/タイムゾーン・検索語（`serp_targets.yaml` を変えない）。
  `serp_diff.py` はこの条件が違う2回を既定で**比べずに落とす**。
- 時刻もそろえる（順位は日内で動く）。1日1回・毎朝の同じ時刻に回す。
  箱の cron なら例：`43 4 * * * cd <案件> && python3 5co-CI-kit/serp/serp_shot.py _context/serp_targets.yaml -o serp/$(date +\%F)/ >> serp/run.log 2>&1`
- 出力は日付フォルダに分けて残す（`serp/2026-11-01/`・`serp/2026-11-02/` …）。
  `results.json` と日付入りの写しは**圏外の回も含めて消さない**（前回比の出所）。
- CAPTCHA・ブロックが出た回は `stopped` が入って途中で止まる。**解かない・回避しない・すぐ撮り直さない**。
  その日は「取得不可」として記録し、翌日の同じ時刻に回す。
- 主張に使うときは1回の観測ではなく**同じ条件の複数回**で見る（最良値ではなく範囲か中央値）。
  ページには常に「n 時点の観測」と書き、「常に n 位」とは書かない。

## 自己確認（Amazon に通信しない）

```bash
python3 5co-CI-kit/serp/serp_shot.py --selftest    # 届け先の判定・一般語・共有ブラウザの禁止・上限
python3 5co-CI-kit/serp/serp_strips.py --selftest  # 段分け・実線/点線・縮小・検索窓の帯
python3 5co-CI-kit/serp/serp_diff.py --selftest    # 前回比・圏外の出入り・条件の一致
python3 5co-CI-kit/serp/serp_redact.py --selftest  # 郵便番号の落とし
python3 5co-CI-kit/serp/serp_page.py --selftest    # 組み立て→検品まで
python3 5co-CI-kit/serp/serp_check.py --selftest   # 出所ルール・SERP_SHOT?
python3 5co-CI-kit/serp/test_serp_mock.py          # 模擬ページで取得手順を通し確認（数分）
```
