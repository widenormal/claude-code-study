# 表紙・中扉カバーモーション（cover_motion）｜社員向け手引き

> Drive 案件フォルダで `cd` したあと、Claude Code / Codex からこの手順で載せる。
> 正本ディレクトリ＝`5co-CI-kit/cover_motion/`（本ファイルと同階層）。

## これは何か

表紙・中扉の **CSS keyframes モーション**（数字がゆっくり漂う／個別に回転）。

- **メール軽量**：動画・GIF・大画像なし。CSS＋数字の SVG 断片のみ
- **任意層**：デッキごとに opt-in。付けない既存デッキは見た目不変
- **採用**：`layer8_spin_spread_v3`（2026-10-28・若松さん確定・kit v3.11 同梱）

## 採用内容（layer8_spin_spread_v3・2026-10-28）

| 項目 | 値 |
|---|---|
| 構造 | 8 深度帯 `cm-n1\|n2\|m1–m4\|f1\|f2` ＋桁ごとの `.cm-spin` |
| Keyframes | `cmDriftN1`/`N2`/`M1`–`M4`/`F1`/`F2` ＋ `cmSpinSway` / `cmSpinCW` / `cmSpinCCW`（周期広め） |
| 数字 | 表紙 **620** `<text>` / 中扉 **620** `<text>`（同密度・全8帯可視） |
| 表紙 | crystal 背景（`--crystal`）＋ **白** 数字 |
| 中扉 | **白背景**＋クリスタルブルー `#C3D7EE` 数字（far-layer hide なし） |
| 球（sphere） | **無し**（NO sphere） |
| 命名 | **Ignite 名禁止**（データ元は Shelpha） |

ファイル：

- `cover_motion.css` … 上記 keyframes＋レイヤ＋`html.ci-static` / print / `prefers-reduced-motion` の凍結
- `digits_cover.svgpart` … 表紙用断片（既に `<div class="cm cm-cover">…</div>`）
- `digits_div.svgpart` … 中扉用断片（既に `<div class="cm cm-div">…</div>`）
- `cover_motion.py` … `--css` / `--cover` / `--div` / `--check`

## 静的 Oracle との関係

- 静的背景の正＝`assets/numfield_*.svg` ＋ `numfield_outline.py`（`NUMFIELD_HANDOFF.md`）
- **置き換えない**。モーション表紙は `.cover-full.cm-field` が `.numfield-full` を隠し、その上に `.cm` 層を載せる
- 静的デッキ・PDF・印刷は従来どおり Oracle／凍結モーション

## `ci_head --interactive`（動く資料）との関係

- **独立**。`--interactive` を付けなくても、本モーションだけを載せられる

## 既定 ON（v3.12.6・2026-10-30）

ビルダーが表紙の `cm-field` を付け忘れるため、v3.12.6 から既定で載せる。

- `ci_head.style_block()` が `cover_motion.css` を既定で連結する（`.cm-field` にしか効かない）。外すときは `style_block(cover_motion=False)`／`ci_head.py --no-cover-motion`
- ビルダーの最後に1回 `html, n = ci_head.apply_cover_motion(html)`（シェルからは `python3 5co-CI-kit/ci_head.py --apply-cover-motion deck.html [-o out.html]`）。表紙 `.cover-full` と中扉 `.cover-full.pd-divider` に `cm-field`＋数字断片を足す。kit のファイルをビルド時に読む（コピーしない）・先に `--check` を通す・既に `cm-field` がある節は触らない（冪等）。中扉を除くときは `--no-dividers`
- 足し忘れは `ci-gates.sh` の「表紙モーション」（`cover_motion.py --lint deck.html`・COVER_MOTION?＝cover has no motion）で警告する（落とさない）

下の a〜c は手で載せる場合の手順（従来どおり使える）。

## 載せ方（opt-in）

案件フォルダで（kit が `5co-CI-kit/` にある前提）：

### a. CSS を一度入れる

```bash
python3 5co-CI-kit/cover_motion/cover_motion.py --css
```

出力をデッキの `<style>` に追記するか、`cover_motion.css` をリンク／コピーする。

### b. 表紙

1. 表紙の `section.cover-full` にクラス **`cm-field`** を足す
2. `python3 5co-CI-kit/cover_motion/cover_motion.py --cover` の断片をカバー直下へ

### c. 中扉（`pd-divider` / 章扉）

`python3 5co-CI-kit/cover_motion/cover_motion.py --div`。中扉にも `cm-field`（必要なら `pd-divider`）を付ける。

### d. 凍結（検査・印刷・動きを減らす設定）

`cover_motion.css` に含まれる：

- `html.ci-static .cm, html.ci-static .cm * { animation/transition: none }`
- `@media print` / `prefers-reduced-motion: reduce`

## やらないこと

- **Eddy 4-layer / gust / v1.1 二軸**など不採用案は kit に入れない（履歴のみ・demoted）
- GIF・動画・大きな埋め込み画像を足さない
- Ignite 社名をスライドに書かない（Shelpha）

## 検品

```bash
python3 5co-CI-kit/cover_motion/cover_motion.py --check
```

表紙・中扉とも `<text>` 620・CSS に `cmDriftN1`＋`cmSpinSway`＋`html.ci-static` があること。
