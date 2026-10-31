# 人物素材（正面向き facing_*・alpha PNG）— v3.12.5（2026-10-30）

## ✅ 承認済み（本番で使う）— marketer 3枚・v3.12.5（2026-10-30）

衣装ディレクター・フォトディレクターの2段審査を通過し、若松さんが本番採用（2026-10-30）。

| ファイル | 大きさ | 内容・配置条件 |
|---|---|---|
| facing_marketer_01_v5_fix.png | 770×766 | 紺のダブルのジャケット・ノートPC。**下端がカウンターの高さで水平に切れているので、スライドの下端か机・カウンター要素に接して置く（ページの途中に浮かせない）** |
| facing_marketer_02_v4.png | 520×1033 | — |
| facing_marketer_03_v5.png | 666×1029 | キャメルのジャケット・フォリオに記入 |

- 検品: `cutout_halo_check.py --resize 1152,813,725,406,362,284,142 --bg-residue` が 3/3 OK（元写真に位置合わせした bgres 込み・2026-10-30）
- 審査記録: `/workspace/knowledge/design/photo_director/2026-10-30_photo-review-v1.md`（01_v5 は配置条件付き合格・02_v4・03_v5 合格）・`/workspace/knowledge/design/costume_director/2026-10-30_marketer-final-pass.md`（服・ヘアメイク 3枚とも合格）。QA 画像＝`/workspace/strategy/_ci_ops/qa_tools/qa_out/marketer_v5/`・`marketer_v4/`
- marketer の v1〜v3（下の表の facing_marketer_0*_v3 を含む）は**未承認のまま**。consumer_01/03 の v3 も未承認

## 審査待ち（未承認）の素材

> **⚠ 審査待ち（未承認）・2026-10-30**: この5枚は人物素材の2段審査（衣装ディレクター＋フォトディレクター）で**フォトディレクター不合格**（5枚とも・正面中央のストック写真型の構図／平らな光）。marketer_01/02/03 は衣装面も要再審査。**推奨セットとして使わない・派生リポやサイトへ展開しない**。差し替え版が両方の審査を通ったら別PRで置き換える。ファイルの削除・差し戻しは若松さんの判断待ち。審査記録＝`/workspace/knowledge/design/photo_director/2026-10-30_photo-review-v1.md`・`/workspace/knowledge/design/costume_director/2026-10-30_v6-review.md`


PR #1220 の `facing_*_v2.png`（再検査で bgres NG）の置き換え。v2 の6枚と旧透過化スクリプト `make_alpha_facing_v2.py` は入れない。

| ファイル | 大きさ | 置き換える v2 |
|---|---|---|
| facing_consumer_01_v3.png | 661×931 | facing_consumer_01_v2 |
| facing_consumer_03_v3.png | 725×1057 | facing_consumer_03_v2 |
| facing_marketer_01_v3.png | 651×1059 | facing_marketer_01_v2 |
| facing_marketer_02_v3.png | 576×949 | facing_marketer_02_v2 |
| facing_marketer_03_v3.png | 617×1023 | facing_marketer_03_v2 |

- **consumer_02 の v3 はまだ無い**（未作成。v2 は bgres NG のため入れない）
- 作り方: 元写真（無地グレー/青の背景）→ 専用の切り抜きモデルのマスク → 髪の帯だけ matting・前景色の推定・alpha bleed（`FIGURES_GUIDE.md` §2-2「切り抜きの作り方」）。**下端はフェードさせず切りっぱなし**（最下行は不透明）。手前に水色を重ねない
- 検品（納品前・必須）: `python3 5co-CI-kit/cutout_halo_check.py <alpha.png> --resize 1152,813,725,406,362,284,142 --bg-residue` が 5/5 OK（元写真に位置合わせした bgres 込み・元写真は案件側にあり kit には入れない＝kit 内で再実行すると bgres は SKIP）。スマホを持つ consumer_01 は `phone_speck_check.py --ref-w 661 --box 330,470,530,680` も OK。#101820・#C3D7EE に合成して目視
- 人物は架空。ページでは `alt` に「架空の人物・イメージ」と書く（`DIGEST_GUIDE.md`）
