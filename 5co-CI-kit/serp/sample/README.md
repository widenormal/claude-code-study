# 見本：Amazon検索順位の根拠ページ（WELLA OPI・2026-11-02 取得）

規定＝`5co-CI-kit/FIGURES_GUIDE.md` §2-4。道具＝`5co-CI-kit/serp/`。
**この見本にだけ顧客名・ASIN・検索語が入る**（規定・道具の側には入れない）。

| ファイル | 中身 |
|---|---|
| `OPI_Amazon検索順位_根拠_2026-11-02.html` | 組み上がり（1枚・帯の画像は data: で埋め込み） |
| `page.yaml` | 組み立ての指定（見出し・要点・判定・施策） |
| `src/results_2026-11-02.json` | 今回の取得の写し（`serp_redact.py` 済み＝郵便番号なし） |
| `src/results_2026-11-01.json` | 前回（前回比の相手。同じ条件で取得） |
| `figs/serp/*.jpg` | 切り出した帯・検索窓・ギャップ枠のサムネイル |
| `figs/brand_logo.png`／`figs/amazon_logo.svg` | ヘッダーのロゴ（ブランド｜Amazon） |
| `qa/serp_diff_2026-11-01_to_2026-11-02.md`／`.txt` | 前回比（上がった8／下がった8／変わらず1） |
| `qa/ci-gates.log` | `ci-gates.sh --serp` の結果（0件） |
| `qa/p01_static_1280x720.jpg`／`p01_slide.jpg` | 目視確認用のレンダリング |

取得の原本（`t0*_fullpage.png`・`t0*_raw.html`）は**社内の取得フォルダに置いたままにする**。
郵便番号が写る・容量が大きいため、ここには入れない。帯の画像は書き出し済みなので、
見るだけなら取得し直す必要はない。

## 作り直し方（原本があるとき）

```bash
cd 5co-CI-kit/serp/sample
python3 ../serp_redact.py <取得フォルダ>/results.json -o src/results_2026-11-02.json
python3 ../serp_page.py page.yaml          # page.yaml の shots_dir を取得フォルダに合わせる
python3 ../serp_diff.py src/results_2026-11-01.json src/results_2026-11-02.json --md \
  -o qa/serp_diff_2026-11-01_to_2026-11-02.md
bash ../../ci-gates.sh --serp OPI_Amazon検索順位_根拠_2026-11-02.html
```

## この見本で確かめられること

- キーワードごとに**実物の検索結果の帯**が1本（顧客商品＝実線の枠＋順位バッジ・半透明の色は重ねない）
- 上位10位の外のキーワード（「ネイル 強化剤」20位）は**ギャップ枠**に施策と対で置く
  （施策が決まっていないので既定の「施策（案）要確認」）
- 行ラベル＝キーワード／順位／判定。ヘッダーはロゴだけ（OPI｜Amazon）
- 順位の右の小さい記号＝**前回比**（↑＝上がった／↓＝下がった／→＝変わらず）
- 注記＝取得日時・Amazon.co.jp・ログアウトのPC・届け先は**区まで**・スポンサー広告枠を除いた順位・
  順位の要因は特定できない。見出しは「入った」ではなく「**入っている**」
- 出所＝「出所：Amazon.co.jp検索結果（取得日時・条件）」**だけ**

この日はスポンサー枠が0件だったため、点線の「スポンサー n」は出ていない
（前日 2026-11-01 の「マニキュア」では出ていた）。点線の描き方は
`serp_strips.py --selftest`／`serp_page.py --selftest` が合成データで毎回確かめている。
