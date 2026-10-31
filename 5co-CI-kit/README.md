# 5 co. CI キット（持ち出し用）

5 co. のCI（トンマナ）を別セッション／別環境へ展開するための一式です。**まず `CI_KICKOFF.md` を読んでください。**

## 使い方（最短）
新しいセッションを開き、最初にこの1行を貼る：

```
このフォルダの CI_KICKOFF.md を読んで、以後すべて 5 co. のCIトンマナに沿って制作して。
```

同一マシンなら、絶対パスでこのキット／元リポ（`~/dev/5co-ci-icon/`）を直接読めます。

## 中身
| ファイル | 役割 |
|---|---|
| `CI_KICKOFF.md` | **入口**。要点＋必読ファイル一覧 |
| `LOGO_HANDOFF.md` | ロゴSVG・カラー・フォント・ルール |
| `名刺デザイン_社内共有.md` | コンセプト・トンマナの背景 |
| `ci-theme.css` | 3色CSSテーマ（:root変数＋クラス） |
| `NUMFIELD_HANDOFF.md` | 数字背景SVGの使い方 |
| `assets/5co_logo_lockup_currentColor.svg` | ロゴ本体（fill=currentColor） |
| `assets/numfield_slide_16x9.svg` ほか | 数字背景（表紙/本文/ヘッダー） |
| `assets/sample_card_front.png` | 完成名刺の実例 |

### 切り抜き人物の検品ツール（2026-10-30 追補）
| ファイル | 役割 |
|---|---|
| `cutout_halo_check.py` | 切り抜き PNG の白フチ（edge／blob／ink・`--resize` で縮小時も）。`--bg-residue` で背景色の取り残し [D] bgres も |
| `cutout_bg_residue.py` | [D] bgres の本体（元写真に自動で位置合わせして中間調の背景色の塊を検出。`cutout_halo_check.py` から呼ぶ） |
| `phone_speck_check.py` | スマホ周りの浮いた低 alpha の点・細線（スマホを持つ人物素材の納品前） |

使い方と運用（人物素材は必須・シーン素材は警告＋目視）は `FIGURES_GUIDE.md` §2-2。

## CI 要点
> 呼称は crystal blue（水色）／ink（濃紺）／Oracle（数字背景）で統一（`CI_KICKOFF.md`「CI用語」）。

- 配色は**3色のみ**：白 #FFFFFF／crystal blue #C3D7EE（PANTONE 2707 C）／ink #101820（PANTONE Black 6 C）。
- 文字・ロゴ＝ink、地・面・アクセント＝crystal blue／白。
- 和文ヒラギノ明朝＋欧文 Hoefler Text（macOS標準・スライド実装。ブランド原典 Garamond は名刺等のみ）。ロゴ＝水晶玉（crystal ball）＋「Strategy, refined.」固定ロックアップ。
- Oracle（数字背景）はうっすら・文字に掛けない。コンセプト＝Strategy, Refined.（水晶玉で市場を透視し戦略を磨き続ける）＝**表紙に `.cover-ci` で必ず明記**。

---
更新: 2026-06-03
