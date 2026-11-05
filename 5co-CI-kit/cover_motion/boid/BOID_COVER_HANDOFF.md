# 表紙・中扉カバーモーション｜Boid 版（boid_cover_v1・2026-11-04 試作）

> 若松さん指示（モーションディレクター経由）で、表紙・中扉の数字背景を
> **Euclidean（layer8_spin_spread_v3）→ Boid（OracleSchool）** に置き換えた試作。
> 正本ディレクトリ＝`5co-CI-kit/cover_motion/boid/`（本ファイルと同階層）。

## これは何か

数字が**群れ（boid）として泳ぐ** canvas 背景。CSS keyframes＋SVG 620桁の代わりに、
`OracleSchool.mount(canvas, {mode})` が 1 枚の canvas に描く。

| | Euclidean（従来・`../`） | Boid（本層・既定） |
|---|---|---|
| 実装 | CSS keyframes＋SVG `<text>` 620 | canvas＋OracleSchool |
| 層 | `.cm > svg.cm-svg` | `.cm > canvas.cm-canvas` |
| 表紙 | crystal 背景＋**白**数字 | 同じ（`mode:"cover"`） |
| 中扉 | **白**背景＋crystal `#C3D7EE` 数字 | 同じ（`mode:"divider"`） |
| 色 | CI 3色のみ | CI 3色のみ（ライブラリ内の定数が `#FFFFFF` / `#C3D7EE`） |
| 重なり順 | タイトル・本文より後ろ（`z-index:0`） | 同じ |

**Euclidean は撤去していない**。`cover_motion.css` も従来どおり連結される（旧デッキの `.cm` 断片が
そのまま動くため）。切り替えは engine 1つ。

## ファイル

- `oracle-school.min.js` … 本番圧縮版（https://5co.ltd/motion/oracle-school.js と同じもの）。**編集禁止**
- `boid_mount.js` … `.cm` 層の `canvas[data-boid-mode]` に取り付ける数行
- `boid_motion.css` … `.cm` / `.cm-canvas` と `.cm-field` の地・重なり順（`../cover_motion.css` と同じ値）
- `digits_cover.htmlpart` / `digits_div.htmlpart` … 表紙・中扉の断片（canvas 1枚）
- `boid_motion.py` … `--css` / `--js` / `--cover` / `--div` / `--check` / `--lint`

## 載せ方

ビルダーの最後に1回（従来と同じ呼び出し。既定が Boid）：

```python
html, n = ci_head.apply_cover_motion(html)                  # engine="boid"（既定）
html, n = ci_head.apply_cover_motion(html, engine="euclid") # 従来の SVG に戻す
```

シェルから：

```bash
python3 5co-CI-kit/ci_head.py --apply-cover-motion deck.html -o out.html
python3 5co-CI-kit/ci_head.py --cover-motion-engine euclid --apply-cover-motion deck.html
```

`style_block()` は engine="boid" のとき `boid_motion.css` を足す。`<script>`（ライブラリ＋取り付け）は
`apply_cover_motion` が `</head>` の直前に**インラインで**1回だけ足す（外部参照なし＝単一HTMLで動く）。

## 止まる条件（動かさない場面）

`OracleSchool.mount` が自分で見る：

- `prefers-reduced-motion: reduce` … `staticTime`（t=6.0s）の1枚で静止。設定を切り替えると追従する
- `beforeprint` / `afterprint` … 印刷・PDF では静止
- 画面外（IntersectionObserver）・非表示タブ（visibilitychange） … 止める

`boid_mount.js` が足す：

- `html.ci-static`（検査・凍結） … `preroll` を `staticTime` にして t=6.0s で停止

## 検品

```bash
python3 5co-CI-kit/cover_motion/boid/boid_motion.py --check
```

素材の有無・CI 色（`#FFFFFF` / `#C3D7EE`）・埋め込み JS の **gzip ≤ 6.7KB** を見る。
デッキ側の漏れは `ci-gates.sh` の「表紙モーション(Boid)」（`BOID_MOTION?`・警告のみ）。

## やらないこと

- 色・レイアウト・文言・フォント・他ページを変えない（本層は数字背景の実装だけを差し替える）
- GIF・動画・大きな埋め込み画像を足さない
- 仕入れ元名（DMT・Acorn-i・Ignite・AMZ-POS）を書かない。データ元は Shelpha と書く
