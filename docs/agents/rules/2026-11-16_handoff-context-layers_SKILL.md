---
name: handoff-context-layers
description: >-
  use this when a bot hands work to another LLM or bot (claude -p, codex exec,
  muse-run, agmsg, /workspace/handoff/), to pass the 3-layer context md paths,
  the acceptance criteria, and the pre-submit checks before sending the
  instruction (required for every relaying bot; approved 2026-11-16 17:14 JST).
---
**2026-11-16 17:14 JST 若松さん承認（決定事項11件すべて案どおり・試行は省略）。** 共有スキルとして配布済み。本文の写しは `/workspace/knowledge/agents/rules/2026-11-16_handoff-context-layers_SKILL.md`。

# 取り次ぎの3層コンテクスト（取り次ぐBotの必須スキル）

対象：**自分以外のLLMまたはBotに作業を渡すBot全員**（`claude -p` / `codex exec` / `muse-run` / agmsg / `/workspace/handoff/`。メイン・グループ・定時ルーチンのどれでも同じ）。自分だけで完結する作業は対象外。

詳細の正本：`/workspace/knowledge/agents/rules/2026-11-16_llm-context-layers.md`
①層の索引：`/workspace/knowledge/agents/rules/2026-11-16_context-layer1-common.md`
（この技能に本文を複製しない。迷ったら上の2つを読む）

## 1. 取り次ぐ前に、3層のパスを指示文の冒頭に書く

- **最初に担当Botを確かめる**（2026-11-18 04:51 JST 若松さん決定。正本：`/workspace/knowledge/agents/rules/2026-11-15_save-mode-bypass.md` v4）：CLIのLLMに回す前に、その作業に担当のAI社員がいないか確かめる。担当がいれば、まずそのBotに頼む（担当Botが自分の作業をCLIのLLMに回すのはかまわない）。担当表にない作業だけ、自分でCLIのLLMに回す。
- `task.md` / `01_message.md` の**冒頭**に、①②③を絶対パスで、①→②→③の順に書く。
- 読み方も一緒に書く：「上から順。全部は読まない。今回効く③は<番号>」。
- **パスを書かずに送らない。**
- 取り次ぎ先のセッションは、必ず AGENTS.md のあるリポジトリかフォルダに cd してから起動する。使い捨てフォルダでは起動しない。起動前に `test -f AGENTS.md`（2026-11-17 00:56 JST 若松さん決定。正本：`/workspace/knowledge/agents/rules/2026-11-17_launch-in-agents-md-dir.md`）。
- 指示文には次の一文を**必ず固定で**入れる：「区切りごとに progress.md へ1行（HH:MM JST｜段階｜一言、詰まったら BLOCKED、最後は DONE）を書く」（2026-11-17 02:00 JST 若松さん承認。正本：`/workspace/knowledge/agents/rules/2026-11-17_progress-md-guard.md`）。
- 起動は `/workspace/knowledge/agents/bin/prelaunch-check task.md || exit 1` を通してから（AGENTS.md と progress.md の指示を確かめ、どちらかなければ起動しない。muse-run は自分で確かめる）。
- 続けて `/workspace/knowledge/agents/bin/launch-guard --cwd "$PWD" --prompt-file task.md` を通す（指示文が分かれていれば `--prompt-file` を本数分くり返す）。①②③のパスと合格条件の有無を見る。**当面は `WARN` でも起動は止まらない**が、送る前に足りない行を足す。足せない理由があるときは `01_message.md` か progress.md に1行で残す（2026-11-17 10:35 JST 若松さん承認。正本：`/workspace/knowledge/agents/rules/2026-11-16_llm-context-layers.md` の「起動する前に…機械で確かめる」）。
- 送る前に、②③のあるリポジトリ（と①がGitHub管理ならその写し）で `git pull` し、mainの最新の決まりを読ませる（2026-11-16 17:20 JST 若松さん承認）。
- ファイルを自分で読めない相手（agy、box外のLLM）には、③の該当行の**本文だけ**を貼る。①の全文は貼らない。

## 2. 合格条件を書く

- 満たせたかを**機械か目視で判定できる形**にする。「きれいに」「適切に」は合格条件にならない。
- 毎回効く条件は③層のmdに置き、指示文では「③の1・3が合格条件」と番号で指す。
- 提出物（PRか、ファイルのパスか）と、やらないこと（`main` へのマージ・本番反映・送信・投稿・購入・削除）も書く。
- **合格条件が書けていない取り次ぎは送らない。** 書けないときは送る前に若松さんか②の担当Botに1行で聞く。

## 3. 提出前の自己チェックと自動テストを指示する

- 機械で確かめられるものは、相手に**提出前に自分で走らせ、結果を報告させる**（コマンド／終了コード／落ちた項目）。走らせていないなら「未実行」と書かせる。通ったことにしない。
- 落ちたまま提出させない。直せないときは `BLOCKED | 理由` で止まらせる。
- 機械で難しいものは、③の「## 人が確かめること」を**提出前に記入**させる（空欄のまま出させない）。
- 自己チェックは承認ではない。レビューと承認は従来どおり（承認・マージ・公開は若松さん）。

## 4. 若松さんの決定をmdへ反映する（要約。詳細は正本）

- **誰が**：決定を直接受けたBotが、その場で下書きする。伝聞で書かない。①汐見／②リポ担当Bot／③作業担当Bot。
- **いつ**：**決定の当日中（JST 24時）に1行**。間に合わないときは `01_message.md` の「今回とくに守ること」に書いて取り次ぎ、翌営業日の午前中までにmdへ移す。
- **どこへ**：全Botに効く＝①、1リポ／1Botだけ＝②、作業の種類＝③。**迷ったら③。①には書かない。**
- **書く4つ**：決定日時（JST）・要約1〜2行（命令形。原文の全文は貼らない）・出典・適用範囲。
- 配布・他リポ展開・Templateの正本変更・①への追加は、この手順の外（若松さんの承認が必要）。
- 幹部だけに公開する決定は、①②③のどれにも書かない（置き場所の指定がないため、若松さんに毎回確認する）。

## 5. 取り次ぎ前チェック（全部「はい」になるまで送らない）

- [ ] 起動場所に AGENTS.md があるか（`test -f AGENTS.md`）
- [ ] 指示文に progress.md の一文が入っているか（`prelaunch-check task.md` が OK）
- [ ] `launch-guard --prompt-file <指示文>` に層チェックの `WARN` が出ていないか（出たまま送るなら理由を1行残す）
- [ ] 指示文の冒頭に①②③のパスを書いたか
- [ ] 読む順番（①→②→③、上から順・全部は読まない）を書いたか
- [ ] 今回の**合格条件**を書いたか
- [ ] 提出前に走らせる**テストのコマンド**と、記入させる**チェックリストのパス**を書いたか
- [ ] 書いてはいけないものを入れていないか（秘密の値／Shelphaのデータそのもの・推計／人事・給与・評価・面談／顧客名・仕入れ先名／幹部のみ公開の情報。外部LLMに渡す作業フォルダに該当ファイルが無いことも確認）
- [ ] 差し戻しが出たら回数と原因区分（A 決まりの見落とし／B 指示不足／C その他）を1行で記録する用意があるか
- [ ] 承認が必要なこと（送信・投稿・購入・削除・`main` へのマージ・本番反映）を「やらない」と書いたか

受け手側：**「読む層」や合格条件が空の取り次ぎは、作業を始めずに1行で差し戻す。**

## 6. 回し先の選定は別の技能（参照は一方向）

- どのLLMに回すかは `grok-minimal-multillm` が決める。**この技能は、回し先が決まったあとの取り次ぎ手順だけ**を決める。
- **この技能から回し先選定の技能を参照しない**（互いに指し合うと、どちらが正本か分からなくなる）。

---

## 付録（本文に数えない）：各リポジトリの `AGENTS.md` に足す文面

正は設計案 §2-1（`/workspace/knowledge/agents/rules/2026-11-16_repo-AGENTS-snippet.md` と同じ文面）。4の例は、そのリポジトリの作業の種類に差し替える。

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
