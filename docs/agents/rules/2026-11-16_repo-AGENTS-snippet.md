# 各リポジトリの `AGENTS.md` に足す文面（承認済み・2026-11-16）

**承認済み（2026-11-16 17:14 JST 若松さん）。** 文面は承認済み。各リポジトリへの反映は Template（榊さん）が行う。

- 正は設計案 §2-1：`/workspace/knowledge/agents/rules/2026-11-16_llm-context-layers.md`
- 同じ文面の置き場所：この案と、スキル本文案 `/workspace/knowledge/agents/rules/2026-11-16_handoff-context-layers_SKILL.md` の末尾（コピー用）。**3か所の文面を同じに保つ。**
- 役割：`AGENTS.md` は**入口（読む順番の案内）だけ**。決まりの本文は書かない（書くと二重管理になる）。上限 **20行以内**。正本は `CLAUDE.md` という既存方針は変えない。
- 下は corporate-website を例にした草稿（15行）。他のリポジトリでは 4 の `docs/site-rules/` の例を、そのリポジトリの作業の種類に差し替える。

```markdown
# Codex の指示入口

このリポジトリの作業ルールの正本は、同じディレクトリの `CLAUDE.md` です。
作業の前に、この順番で読んでください（上から順。全部は読まない）。

1. 全Bot共通：`/workspace/knowledge/agents/AGENTS.md`
   （box の外で動くときは読めません。読めない場合は指示文に貼ってもらってください）
2. このリポジトリの正本：`./CLAUDE.md`
3. いまの状態：`./memory/active-context.md`（現在地・開いているPR）、`./memory/decisions.md`（過去の決定）
4. 今回の作業の種類に合うものだけ：`./docs/site-rules/README.md`（索引）→ 該当する1ファイル
   例：人物の画像を差し替える → `./docs/site-rules/person-photo.md`
5. 迷ったとき：`./docs/claude-detailed-rules.md`（詳細。必要な節だけ）

- ルールの更新は `CLAUDE.md` と `docs/site-rules/` に行い、このファイルへ本文を複製しないでください。
- Claude Code 専用のフック・MCP・コマンドは、参照しただけでは Codex に登録・実行されません。
- commit と下書きPRまでは行ってよい。`main` へのマージと本番反映は若松さんの確認のあとだけ。
```

## 注意

- `./docs/site-rules/` は **corporate-website にはまだ存在しない**（2026-11-16 時点で確認済み）。4 の案内を入れる前に、そのリポジトリの③層のファイルを作る（担当：そのリポジトリの担当Bot）。索引が空のまま案内すると、読み手が空振りする。
- `/workspace/knowledge/agents/AGENTS.md` は box の外では読めない。box外のLLMに渡すときは、①の全文ではなく③の該当行の本文を指示文に貼る（設計案 §2-2）。
- この文面をリポジトリに入れる作業は、**若松さんの承認後**。承認前は、取り次ぎの指示文に③のパスを手書きする運用でしのぐ。

## 変更記録

- 2026-11-16 初版作成（反映者：Claude Code）。リポジトリの `AGENTS.md` は1つも変更していない。
