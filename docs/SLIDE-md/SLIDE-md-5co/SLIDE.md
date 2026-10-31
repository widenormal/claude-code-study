# SLIDE.md

このファイルは 5 co. CIスライドの**正データ仕様**です。

## 作り方（既定＝決定論的・Claude Code）

**「CIスライド作って」と言われたら、Claude Code がこの SLIDE.md と `5co-CI-kit` の
テンプレ/トークンを読み、A4-HTML を直書きする（生成AIに丸投げしない＝崩れない・再現できる）。**

1. **まず `5co-CI-kit/VERSION` を読み、現行フォーマット**（v3.2 以降＝`ci-format-v3.2.css` 系・型仕様 `V3.2_FORMAT.md`）**に文言だけ差し替える**（0からCSSを書かない）。`5co_slide_template.html` は週次v2雛形（本文明朝）＝週次専用の残置で、月次・新規デッキには使わない（2026-07-07 WELLA 世代遅れ事故の原因）。
2. 編集後は必ず `python3 5co-CI-kit/slide_overflow_check.py <file.html>` で `OK` を確認。
3. 出力は `5co-CI-kit/ci-finalize.sh`（または Chrome の「印刷→PDF（背景ON）」）。

**Claude Design / `slide-deck-builder` スキルは任意の代替**（速い初稿・Claude Code 非利用者向け）。
本仕様を `SLIDE-DECK.md` 化して claude.ai/design 等に渡せるが、生成方式のため厳密な再現は決定論パスが上。
5co 公式CIの既定は上記の決定論パス。

---

以下はそのトークン定義（AIツールに渡す場合もこのまま使える）。

**このデザインシステムは 5 co. CI v2 の「実納品デッキ」準拠版です。** 正データは
**実際に納品されている最新の CIスライド（A4横・`--crystal`・数字フィールド表紙）の CSS**。
`5co-CI-kit/styleguide_v2.html` は Web スタイルガイド用（16:9・`--ice`・numfield 無し）で
**納品フォーマットとは別物・旧世代**なので参照しない（2026-07-13 正典から退役済み＝`_RETIRED.txt`）。
齟齬時は最新の納品デッキを正とする。

> 経緯：旧版 SLIDE-md-5co は styleguide_v2.html（16:9/`--ice`）を素データにしたため
> 「A4でない・数字フィールド無し・トークン名が違う」古い見た目になっていた。本版で是正。

## Overview

**参照ソース：** 5 co. の実納品 CIスライド（A4横・CI v2）
**マッチするシーン：** 5 co. の社外向け提案・営業資料、引き継ぎ資料、社内公式プレゼン、IR・戦略説明。静謐・上質・余白多めで「水晶玉で市場を透視し戦略を磨き続ける（Strategy, refined.）」を体現するフォーマル資料。
**最重要原則：** **配色は 2 色＋白のみ**（リッチブラック `--ink` ／ クリスタル（水色）`--crystal` ／ 白）。グレー・純黒(#000)・他色相は禁止。濃淡は白混ぜ（ティント）か不透明度のみ。

## Colors

青の正式トークン名は **`--crystal`**（水晶玉。実納品デッキの呼称）。旧 `--ice` / `--powder` / `#0E1A38` / `#A9CFDF` は廃止・使用禁止（hex は同じでも名前を揃える）。

| 役割 | トークン | HEX | 由来 |
|---|---|---|---|
| 文字・ロゴ・ダーク地 | `--ink` | #101820 | PANTONE Black 6 C（リッチブラック） |
| 水色地・アクセント | `--crystal` | #C3D7EE | PANTONE 2707 C / DIC 576 アミ40% |
| 地・抜き | `--white` | #FFFFFF | 紙白 |
| ティント 55% | `--crystal-55` | #DEE9F6 | 薄帯・表見出し・カード地 |
| ティント 25% | `--crystal-25` | #F0F5FB | ごく薄い面・地色 |
| 文字濃淡 | `--ink-85 / 60 / 14` | rgba(16,24,32,.85 / .60 / .14) | 本文 / 補足・軸 / 罫線 |

```yaml
colors:
  ink: "#101820"        # PANTONE Black 6 C
  crystal: "#C3D7EE"    # PANTONE 2707 C / DIC576アミ40%（青の正式名）
  white: "#FFFFFF"
  crystal_55: "#DEE9F6"
  crystal_25: "#F0F5FB"
  ink_85: "rgba(16,24,32,.85)"
  ink_60: "rgba(16,24,32,.60)"
  ink_14: "rgba(16,24,32,.14)"
  forbidden: ["grey", "#000", "他色相", "旧 --ice/--powder/#0E1A38/#A9CFDF"]
```

### チャート/データ可視化（`5co-CI-kit/ci-charts.css`）

データ系列は**紺〜水色のモノトーン階調**：`--data-1 #101820`（主系列・目標）/ `--data-2 #C3D7EE`（対比・現在）/ `--data-3 #5B7C99`（中間）/ `--data-4 #DEE9F6`（面）。**増減セマンティクス限定**で機能色 `--pos #2F7D6B`（達成・増）/ `--neg #B23A48`（未達・減）を「意味」にのみ使う。

## Typography

書体：和文 `Hiragino Mincho ProN` ／ 欧文 `Hoefler Text`（macOS標準・タグラインは italic）。**Georgia をフォールバックに置かない**。Garamond 系（Garamond Premier Pro / EB Garamond）はスライドでは廃止（#642・2026-07-06 で Hoefler へ移行。名刺等の別成果物のみ据え置き）。
v3.2 系デッキは **V3.1 タイポ**（本文＝ゴシック `--sans-ja`・表紙/章扉/見出し/欧文ラベルのみセリフ）を適用する（`ci-format-v3.2.css` の `v31-typography` ブロック・詳細＝`5co-CI-kit/SLIDE_DESIGN_GUIDELINES.md` §3）。

**φ タイプスケール（隣接比 1.618・基準 body 18px）**：`--fs-note 11px / --fs-body 18px / --fs-md 29px / --fs-lg 47px / --fs-xl 76px`。ベースライン単位 `--u 29px`。

- 字間：見出し・欧文 `letter-spacing:.04em`、kicker `.18em`。リガチャ禁止（`font-variant-ligatures:none`）。
- **数字＝ライニング+タブラー必須**：`table,th,td,.t-num,.kpi .v{font-variant-numeric:lining-nums tabular-nums;}`。
- 見出しは Grade 準拠で抑えめ（本文スライドの section 見出し `h3` ≈ 22–29px、表紙 h1 ≈ 46px）。

```yaml
typography:
  serif_ja: '"Hiragino Mincho ProN","Yu Mincho",serif'
  serif_en: '"Hoefler Text","Baskerville","Palatino","Hiragino Mincho ProN","Yu Mincho",serif'
  scale_phi: { note: "11px", body: "18px", md: "29px", lg: "47px", xl: "76px" }
  baseline_unit_u: "29px"
  numerals: "lining-nums tabular-nums（必須）"
  no_georgia: true
```

## Layout（★最重要：A4横・mm 単位）

**納品フォーマットは A4 ランドスケープ（297mm × 210mm）。** Chrome の「印刷→PDF（背景ON）」で配布 PDF を作る前提。16:9/1280×720 は使わない（旧 styleguide の名残）。

```css
.slide{ position:relative; width:297mm; height:210mm; margin:0 auto 8mm; overflow:hidden;
  background:var(--white); padding:16mm 18mm 14mm; box-shadow:0 1px 10px rgba(16,24,32,.14);
  counter-increment:page; }
@page{ size:A4 landscape; margin:0; }
@media print{ .slide{ margin:0; box-shadow:none; break-after:page; } }
```

- マージン：左右 18mm・上 16mm・下 14mm。
- 地色バリエーション（3色のみ）：`.slide`（白）／`.slide.pale`（crystal-25）／`.slide.pale-strong`（crystal）／`.slide.dark`（ink 地・**文字は crystal**）。

```yaml
layout:
  format: "A4 landscape"
  width: "297mm"
  height: "210mm"
  padding: "16mm 18mm 14mm"
  page: "@page { size: A4 landscape; margin: 0 }"
  surfaces: { white: "白/ink字", pale: "crystal-25/ink字", pale_strong: "crystal/ink字", dark: "ink/crystal字" }
```

## 表紙（cover-full）＋ 数字フィールド

表紙は **crystal 地に数字フィールド（numfield）を全面・うっすら**敷き、ロゴ左上・タイトル左下。

```css
.slide.cover-full{ background:var(--crystal); padding:0; }
.cover-full .numfield-full{ position:absolute; inset:0; z-index:0; pointer-events:none;
  background-image:url("…numfield SVG…"); background-size:cover; background-position:center; opacity:.75; }
.cover-full .cf-logo{ position:absolute; left:18mm; top:22mm; width:32mm; color:var(--ink); z-index:1; }
.cover-full .cf-block{ position:absolute; left:18mm; bottom:28mm; max-width:64%; z-index:1; }
.cover-full .cf-block h1{ font-size:46px; line-height:1.22; letter-spacing:.04em; }
```

- numfield SVG は `5co-CI-kit/assets/numfield_*.svg`（公式）を使う。手書き span で代替しない。
- **本文スライドはプレーン**（numfield を敷かない）。数字を本文・図表・表に掛けない。

## Logo / Footer

- ロックアップ v2（マーク＋「Strategy, refined.」固定・`fill=currentColor`）。色：White/Pale=ink、Dark=crystal。
- **各ページ右上に corner-logo 102px**（`top:30px; right:36px; width:102px`・v2.2 で 102px に確定）。表紙は左上 32mm。
- **フッター（全スライド共通・厳守）**：左下 `© 2026 5co. All rights reserved.`／右下 `CONFIDENTIAL ・ NN`（2桁ゼロ詰め・公開資料は CONFIDENTIAL を外す）。Hoefler Text 11px・色 `--ink-60`・Dark 面は crystal 65%・下端 15px/左右 36px。CSS カウンタ（`body{counter-reset:page}` `.slide{counter-increment:page}` ＋ `::before/::after`）。

## コンポーネント（実納品デッキ準拠の主要クラス）

| クラス | 用途 |
|---|---|
| `.cols` / `.cols > div` | 横並びカラム（`display:flex; gap:40px`） |
| `ul.clean` | 行頭 crystal ドットの箇条書き |
| `table` / `th`(`.hl`) / `td.num` | 表（見出し行 crystal-55・数字右寄せ lining+tabular） |
| `.cmp` | 比較表（行間タイト） |
| `.kpis` / `.kpi .v` `.kpi .l` | KPI カード（数値 Hoefler Text 42px lining+tabular） |
| `.note-line` | 補足注記（ink-60・12.5px） |
| `ol.steps` | 番号付きステップ（丸番号は crystal 枠） |
| `.title-row` | 見出し＋補足の baseline 揃え |

## はみ出し検証（編集のたびに必須）

A4 固定・自動縮小なし。編集後は `python3 5co-CI-kit/slide_overflow_check.py <file.html>` で `OK` を確認（headless Chrome）。直し方は「縮小」でなく「削る」。

## Do / Don't

**Do**：2色＋白だけ／A4横で組む／表紙は cover-full＋numfield／Dark 面の文字は crystal／数字 lining+tabular／ロックアップ v2 を color 着色（corner 102px）。
**Don't**：グレー・#000・他色相・旧 `--ice/--powder`／16:9 で組む／numfield を本文・図表に掛ける／Dark 面に白文字／Georgia フォールバック／ロゴの分離・歪み・比率変更。
