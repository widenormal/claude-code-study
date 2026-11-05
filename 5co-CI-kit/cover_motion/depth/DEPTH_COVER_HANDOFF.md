# 表紙・中扉カバーモーション｜奥行きの層 depth 版（depth_cover_v1・2026-11-05 試作）

> 若松さん指示（2026-11-05 10:51・モーションディレクター経由）で、表紙・中扉の数字背景を
> **Boid（v3.15.0・boid_cover_v1）→ Oracle 実験#4「奥行きの層」の本番版** に置き換えた試作。
> 正本ディレクトリ＝`5co-CI-kit/cover_motion/depth/`（本ファイルと同階層）。

## これは何か

Boid の群れに「奥行き」の3要素（大きさ・濃さ・速さ）を足した canvas 背景。遠い数字は小さく・淡く・遅く、
近い数字は大きく・濃く・速い。API・取り付け・CSS・重なり順は Boid と同じ（`OracleSchool.mount(canvas,{mode})`）。

| | Boid（v3.15.0・`../boid/`） | depth（本層・既定） |
|---|---|---|
| 実装 | canvas＋OracleSchool | 同じ（エンジンだけ差し替え） |
| 表紙 | crystal 背景＋白数字・静止画 t=6 | 同じ |
| 中扉 | 白背景＋crystal 数字・seed 20261104・静止画 t=9 | 同じ |
| 色 | CI 3色のみ | 同じ（ライブラリ内の定数 `#FFFFFF` / `#C3D7EE`） |
| 重なり順 | タイトルより後ろ（`.cm` z-index:0・タイトル z-index:2） | 同じ |

Boid・Euclidean は撤去していない。切り替えは engine 1つ。

## ファイル

- `oracle-school-depth.min.js` … 実験#4 本番圧縮版（`motion/oracle/experiments/2026-11-05_depth-layers/oracle-school-exp.prod.min.js` の写し）。**編集禁止**
- `depth_mount.js` … `../boid/boid_mount.js` と同一（`canvas[data-boid-mode]` に取り付け・`window.ciBoid` に登録）
- `depth_motion.css` … `../boid/boid_motion.css` と同じ規則（コメントだけ違う）
- `digits_cover.htmlpart` / `digits_div.htmlpart` … canvas 1枚（`data-cm-engine="depth"` 付き）
- `depth_motion.py` … `--css` / `--js` / `--cover` / `--div` / `--check` / `--lint`（DEPTH_MOTION?・警告のみ）

## 載せ方

```python
html, n = ci_head.apply_cover_motion(html)                  # engine="depth"（既定）
html, n = ci_head.apply_cover_motion(html, engine="boid")   # v3.15.0 の Boid に戻す
html, n = ci_head.apply_cover_motion(html, engine="euclid") # 従来の SVG に戻す
```

```bash
python3 5co-CI-kit/ci_head.py --apply-cover-motion deck.html -o out.html
python3 5co-CI-kit/ci_head.py --cover-motion-engine boid   --apply-cover-motion deck.html
python3 5co-CI-kit/ci_head.py --cover-motion-engine euclid --apply-cover-motion deck.html
```

1つのデッキに canvas 版のエンジンを2つ混ぜない（どちらも `window.OracleSchool` を定義する）。

## 止まる条件

Boid と同じ：`prefers-reduced-motion: reduce`・印刷・画面外・非表示タブで止まる。reduced-motion の止め絵は表紙 t=6・中扉 t=9（`depth_mount.js` が中扉だけ `cfg.staticTime=9`・2026-11-05 審査の指摘で修正）。`html.ci-static`（#static）は
表紙 t=6・中扉 t=9 で停止。gzip 上限 6.7KB（`--check`）。
