# 5 co. Oracle（数字背景）SVG｜スライド制作 共有

> 正式名は **Oracle（数字背景）**（`CI_KICKOFF.md`「CI用語」）。実装ファイル名の `numfield_*` は温存。
> Oracle は **SVGで共有・使用**します（PNGは使わない）。HTMLは拡大自在、PowerPoint（2016/365以降）も「挿入→画像→SVG」でベクターのまま使えます。色は crystal blue `#C3D7EE`（うっすら）。

## SVG素材（すべて 1920×… の透過SVG）
| ファイル | 用途 |
|---|---|
| `~/dev/5co-ci-icon/slide/assets/numfield_slide_16x9.svg` | 表紙・章扉（中央クリア／16:9） |
| `~/dev/5co-ci-icon/slide/assets/numfield_slide_allover.svg` | 本文ページ（全面うっすら／16:9） |
| `~/dev/5co-ci-icon/slide/assets/numfield_header.svg` | ヘッダー帯（左クリア・右へ流れる／1920×180） |
| `~/dev/5co-ci-icon/slide/assets/numfield_header_even.svg` | ヘッダー帯（全幅均一／1920×180） |

- すべて**透過**。白地でも淡い crystal blue 地（`#C3D7EE`系）でもそのまま重なる。
- 数字色は `fill="#C3D7EE"`。色を変えたい場合は SVG内の `#C3D7EE` を置換（例：ダーク地用は crystal blue のまま＝CI v2 では白抜きを使わない）。

## HTMLでの使い方（SVG）
```css
/* 背景に敷く */
.slide.cover   { background:url("assets/numfield_slide_16x9.svg")  center/cover no-repeat, var(--white); }
.slide.content { background:url("assets/numfield_slide_allover.svg") center/cover no-repeat, var(--white); }
.page-header   { background:url("assets/numfield_header.svg") right center/cover no-repeat, var(--white); }
```
- もしくは**インラインSVG**で直接埋め込み（DOMで色・不透明度を後から制御したい場合）。

## PowerPointでの使い方（SVG）
1. **挿入 → 画像 → このデバイス** で `numfield_*.svg` を選択（SVGはベクターのまま入る）。
2. スライド幅にフィット → **最背面へ移動**。透過なので地色に重なる。
3. 色変更が必要なら、SVGを選択 → 「**図形に変換**」→「図形の塗りつぶし」で再配色可能。
4. **スライドマスター**に入れておけば全ページ共通（表紙＝16:9版／本文＝allover版／ヘッダー＝header版）。

## ルール
- 数字は**うっすら**（不透明度0.05–0.16）。文字・図表には掛けない（可読性最優先）。
- 配色は3色（白／crystal blue `#C3D7EE`／ink `#101820`）のみ。数字は crystal blue、文字は ink。
- 別アスペクト（1920×120 / 1920×240 等）や**紺地用の白抜き版**が要れば追加生成可。

---
更新: 2026-06-03 / 出典 `~/dev/5co-ci-icon/slide/assets/`

## 表紙モーションとの区別（2026-10-28）
- 本ファイルの `numfield_*.svg` / `numfield_outline.py` は**静的** Oracle 背景の正。
- 動く表紙・中扉は別層 `cover_motion/`（`.cover-full.cm-field` が `.numfield-full` を隠して `.cm` を注入）。numfield 資産は置き換えない。手順＝`cover_motion/COVER_MOTION_HANDOFF.md`。
