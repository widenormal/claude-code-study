# 全Bot共通ルール：取り次ぎは層ごとの独立mdで渡す（2026-11-14 01:50 JST 若松さん決定）

要約：Bot同士・グループで長い中身を渡すときは、本文をメッセージに書かず、`/workspace/handoff/` の下に取り次ぎ1件につき1フォルダを作り、層ごとに独立したmdを置く。メッセージは「場所＋結論＋依頼」だけ。受け手は必要な層までしか読まない。詳細層は全文を読まず、必要な節だけを、原則Claude Codeで読む。目的はGrok使用量の削減（今週はBot同士のやり取りが約24%）。01:47の「ファイルで渡す」決定を、Templateの3層コンテクストに合わせて層別ファイルにしたものである。

## Templateの3層コンテクスト（型）

出典は `5co-hub/template`（box上の写し `/workspace/tpl-main`、`origin/main` と当該箇所は一致）。正本は次のファイル。

- `/workspace/tpl-main/CLAUDE.md`（「コンテキスト管理（3層構造）」）
- `/workspace/tpl-main/README.md`（同節）
- `/workspace/tpl-main/docs/active-context-template.md`（SessionStart注入の3層とサイズ目安）
- `/workspace/tpl-main/.claude/scripts/session-context.sh`（実装）
- `/workspace/tpl-main/memory/active-context/_template.md`（状態層の雛形）

Template本体の3層は、層ごとにファイル（群）が独立し、読む深さが違う。

| Layer | 場所 | 役割 | 読み方 |
|---|---|---|---|
| 1 | `CLAUDE.md` | コアルール | 毎ターン |
| 2 | `memory/` ＋ `profile/` ＋ `learnings/` ＋ `<domain>/visited/` | セッション状態・辞書・学習・除外 | セッション開始時。中はさらに独立ファイル（①状態 `memory/active-context.md` は全文、②辞書は該当節、③学習 `learnings/insights.md` は見出しのみ、④除外はリスト、⑤未来は任意） |
| 3 | `.claude/skills/` | 手順スキル | 必要なときだけ |

取り次ぎでもこの仕組みを使う。ファイル名は取り次ぎ用に合わせ、役割と読み方を対応させる。

## 置き方

取り次ぎ1件につき1フォルダ。雛形は `/workspace/handoff/_template/`（中の `_README.md` は運用説明なのでコピーしない）。

```
/workspace/handoff/<YYYY-MM-DD>_<送信元>_<件名>/
  01_message.md    … Layer 1（依頼の核。メッセージと同じ内容）
  02_summary.md    … Layer 2（状態。決定事項・未決・次の一手）
  03_details.md    … Layer 3（詳細。調査・表・ログ・下書き）
```

- フォルダ名の日付は `TZ=Asia/Tokyo date "+%Y-%m-%d"` で取る。
- 既存の `/workspace/handoff/` 配下の案件フォルダ（このルール以前のもの）は、この場で移さない。
- `_` で始まる名前（`_template/` など）は運用用で、取り次ぎの本文ではない（Templateの `_template.md` / `_README.md` と同じ約束）。

## 各層（独立して読めること）

各ファイルは、他の層を開かなくても意味が通じるように書く。長い本文を上の層へコピーしない。下の層への参照は「パス」と「見出し」だけにする。

| 取り次ぎの層 | ファイル | Templateでの対応 | 中身 | 目安 |
|---|---|---|---|---|
| Layer 1 | `01_message.md` | Layer 1（毎回読む短い核） | フォルダの場所、結論1〜2行、してほしいこと（読む層と、詳細なら節名） | 数行（8行以内） |
| Layer 2 | `02_summary.md` | Layer 2の①状態層（`active-context.md`） | 決定事項、未決、次の一手（動詞で書く）。`03_details.md` の見出し一覧だけ添えてよい | 20〜30行（上限の目安100行。Templateのセッションサマリーと同じ） |
| Layer 3 | `03_details.md` | Layer 3および学習層の本文（オンデマンド） | 調査結果、表、ログ、下書き。見出しで節を分ける | 行数上限なし。全文読み禁止。必要な節だけ |

チャットやSendToAgentのメッセージは、`01_message.md` と同じ数行にする（場所＋結論＋依頼）。Layer 2・3の本文は貼らない。

## 送る側

- 目安として5行を超える中身（調査結果、下書き、表、ログ、経緯）は、上記3ファイルに分けて置く。
- 長文（とくに `03_details.md`）の作成は、できるだけboxのClaude Codeに回す（claude-codex-cliスキル）。
- GitHubには、残す価値のある決定事項・設計だけを置く。取り次ぎのために毎回push・PRはしない。

## 受け取る側（読む深さ）

1. まずメッセージ（または `01_message.md`）だけ読む。それで足りれば、そこで止める。
2. 判断に状態が必要なら `02_summary.md` を全文読む（短く保つ前提）。
3. `03_details.md` は指定された節、または `02_summary.md` の見出しから必要な節だけ読む。全文を読み込まない。読み込みは原則Claude Codeに回す。
4. 返信も同じ形（場所＋結論＋依頼。必要なら同じフォルダを更新するか、新しいフォルダを作る）。

## 守ること

- 秘密の値はファイルにも書かない（1Passwordの参照だけ）。
- 人事の給与、Shelphaの推計データ・手法・データ元はhandoffに置かない（rutzboや既定の場所のまま）。
- 送信・投稿・削除・契約などの承認ルールは従来どおり。配置の変更、各Botの設定の変更、mainへの反映は、若松さんの承認を得るまでしない。
