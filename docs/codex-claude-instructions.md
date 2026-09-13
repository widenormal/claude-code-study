# Codex と Claude Code の共通ルール

## 正本は CLAUDE.md

このテンプレートでは `CLAUDE.md` を作業ルールの正本として維持する。Codex が最初に読む `AGENTS.md` は、同じディレクトリの `CLAUDE.md` を読み込むよう指示する短い入口とする。ルール本文の移動・複製やファイル名変更はしない。

Codex が `CLAUDE.md` を直接自動発見する設定ではなく、標準で発見する `AGENTS.md` を通じて読む方式。個々のMacのグローバル設定に依存せず、リポジトリと一緒に共有できる。`@CLAUDE.md` の自動展開を前提にしない。

## 利用方法

1. テンプレートまたは同期PRを取得する。
2. 対象フォルダで新しいCodexタスクを開始する。
3. 読み込んだ指示の出典と正本のルールを確認する。`AGENTS.md` が入口、`CLAUDE.md` が正本として参照されていることを確認する。

進行中のタスクへ起動時の指示が遡って自動注入されるとは限らない。GitHubにファイルがあるだけで、接続先の全リポジトリへ自動適用されるわけでもない。作業対象のチェックアウトに入口ファイルが必要。

## 派生先への配布

`apply-template.sh` は、各 `CLAUDE.md` ディレクトリに `AGENTS.md` がなければ配置する。既存の `AGENTS.md` は `--repair` でも上書きしない。既存の入口がある派生先は、その内容を確認して正本への参照を個別に統合する。各案件の `CLAUDE.md` は従来どおり同期で上書きしない。

## 実行機能との境界

この変更は指示文の共通利用。Claude Codeの `.claude/settings.json`、フック、MCP、コマンド、スキルの自動登録をCodexに移植するものではない。本文を読めたことと、各機能の実行確認は分けて扱う。

## 参考

[OpenAI公式：AGENTS.mdの読み込みと代替ファイル名](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

個人環境だけで直接読み込ませたい場合は、公式の `project_doc_fallback_filenames = ["CLAUDE.md"]` も使える。ただし同じディレクトリの `AGENTS.override.md` / `AGENTS.md` が優先される。本テンプレートは共有しやすい入口方式を採用する。
