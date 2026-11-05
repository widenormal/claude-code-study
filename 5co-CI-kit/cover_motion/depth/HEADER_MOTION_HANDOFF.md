# 本文ヘッダーの数字の帯（v3.17.0 試作・2026-11-05）

モーションディレクター仕様 rev4・バリアントB（速さ1.0倍・数字126個）。若松さん承認 2026-11-05 12:29 JST。

## 使い方
- Python: `html, n = ci_head.apply_header_motion(html)`（apply_cover_motion の後でも前でもよい・冪等）
- CLI: `python3 ci_head.py --apply-header-motion deck.html [-o out.html]`
- 帯を付けない本文ページ: `<section class="slide" data-hb="off">`

## 形
- 帯: 上0〜118px・全幅・端はぼかさず切る（edgeFade 0・overflow:hidden）。z-index 0、ヘッダー（.hdr / h2.title / .accent-bar / .corner）は z-index 1。
- 静かな範囲: タイトルと青い線の上（calm x .05 y .50 w .76 h .50）。5co ロゴの周りは楕円（95×58px @1036,66）で 0.35 に薄める。
- 帯のあるページだけヘッダーの余白を詰める: `.hdr` margin-top −30px・下0／`h2.title` 下0／`.accent-bar` 上5px・下16px。文字の大きさは不変（ロゴ34px・キッカー13px・タイトル27px）。
- 実測（A4横 1122.5×793.7px）: ロゴ行 30.5・タイトル 64.5〜105・青い線の下端 113.0・本文の開始 129.0（v3.16.0 は 176.0・202.0）。

## 動き
- エンジンは表紙と同じ `oracle-school-depth.min.js`（変更しない）。取り付けは `header_mount.js`（オプションだけ渡す）。
- 見えているページだけ動く。reduced-motion・印刷・`#static`／`html.ci-static` は t=6 の決まった静止画。
