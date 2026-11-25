# 全Grok Bot共通 AGENTS.md（Claude Code / Codex CLI / Muse Code 用）

この box の Claude Code・Codex CLI・Muse Code を使うときは、全Botがこのファイルに従う。
リポジトリ固有のルールは、各フォルダの CLAUDE.md / AGENTS.md に書く。両方あるときは、厳しいほうに従う。

## (a) 目的と北極星
- 北極星は GMS800億円。全Botの仕事はここにつながる。
- 達成が、次の目標をつくる。届いたら、より高い目標を科学的に設定し直す。

## (b) 使い分け
- Claude Code（`claude`）：長文、設計、レビュー、文章の推敲。
- Codex CLI（`codex exec`）：コード修正、テスト実行、差分の作成。
- 迷ったら、読むだけの作業は Claude、ファイルを書き換える作業は Codex。
- Muse Code（`muse-run` 経由だけ）：Shelpha のデータそのもの・秘密の値を含まない作業の、セカンドオピニオンのレビュー、Codex の枠が少ないときのコード修正、難しい重い実装（計画先出し）、大量の細かい作業、画像のラフ。詳しくは下の「Muse Code」。
- 自分（Grok Bot）でできる短い判断には、どちらも使わない。トークンと時間を節約する。

## (c) 呼び出し方
### 場所のルール
- 必ず、その作業専用のフォルダ（`/workspace/<作業名>/`）の中で実行する。
- `/home/box/agent-data` の中では実行しない。`/home/box` 直下や `/` でも実行しない。
- 他のBotのフォルダを作業場所にしない。

### 長い指示はファイルで渡す
- 指示は `task.md` に書き、標準入力で渡す。コマンド行に長文を書かない。
- 先に `mkdir -p out` で出力フォルダを作る。
- このファイルの中身も一緒に渡す：`cat /workspace/knowledge/agents/AGENTS.md task.md | ...`

### Claude Code（確認済み：v2.1.282）
読むだけ（レビュー・設計・長文）：
```
cd /workspace/<作業名>
cat /workspace/knowledge/agents/AGENTS.md task.md \
  | timeout 600 claude -p --output-format text --no-session-persistence \
      --tools "Read,Grep,Glob" > out/claude.md 2> out/claude.err
```
- 道具を全部止めるなら `--tools ""`。
- ファイル編集を許すときだけ `--permission-mode acceptEdits` を足す。
- JSON で受けたいときは `--output-format json`。

### Codex CLI（確認済み：codex-cli 0.153.4）
読むだけ：
```
cat /workspace/knowledge/agents/AGENTS.md task.md \
  | timeout 900 codex exec -C /workspace/<作業名> -s read-only --ephemeral \
      -o out/codex_last.md - > out/codex.log 2>&1
```
コード修正・テスト実行：`-s read-only` を `-s workspace-write` に変える。
- git リポジトリ外で動かすときは `--skip-git-repo-check` を足す。
- `-o` のファイルに最終回答だけが入る。ログ全体は `out/codex.log`。

### Muse Code（確認済み：1.4.14、Muse Code Power Usage サブスク）
必ずラッパー `/workspace/knowledge/agents/bin/muse-run` で呼ぶ。`muse exec` を直接呼ばない。
```
cd /workspace/<作業名> && mkdir -p out
/workspace/knowledge/agents/bin/muse-run --task task.md                 # 読むだけ（既定。書き込み・シェルなし）
/workspace/knowledge/agents/bin/muse-run --project /workspace/<案件リポ> --task task.md   # 案件フォルダで実行（テンプレの AGENTS.md / CLAUDE.md を読む。out は呼んだ場所に出る）
/workspace/knowledge/agents/bin/muse-run --mode plan --task task.md     # 計画だけ（20ステップまで）
/workspace/knowledge/agents/bin/muse-run --mode run --task task_ok.md --model muse-spark-1.3 --timeout 900   # 書き換え（計画を確かめたあとだけ）
```
- ラッパーがすること：`MUSE_CONTRIBUTOR_MODE=0` と `--contributor-mode off` を毎回付ける。API キーの環境変数を外す（サブスクだけで動かす）。timeout（既定 600秒、run は 900秒）。`--trust-workspace` を毎回付け、作業フォルダのテンプレ配布 md（AGENTS.md → CLAUDE.md）を Muse 自身に読ませる。共通 AGENTS.md を先頭につなぐのは `--with-agents` のときだけ（既定オフ。重複を避ける）。web ツールは既定で無効（要るときだけ `--web`）。
- 前後に `muse usage --json` を `out/muse_usage_before.json` / `out/muse_usage_after.json` に保存し、`/workspace/knowledge/agents/logs/muse-usage.tsv` に1行残す。
- 5時間枠 70% か週枠 60% を超えていたら実行しない（終了コード 3）。そのときは Claude Code / Codex に回す。
- 最終回答は `out/muse.md`、イベントは `out/muse.jsonl`、エラーは `out/muse.err`。`--tag` で名前を変えられる。
- モデル：既定は `muse-wonder-1.0`（重い。枠をすぐ使う）。軽い作業は `--model muse-spark-1.3`。`muse-image-1.0` は指定できない（画像は既定モデルに指示文で頼む）。
- 使う場面：
  - セカンドオピニオンのレビュー（Claude のレビューに足す。代わりにしない）。
  - Codex の枠が少ないときのコード修正・テスト（Spark）。
  - 難しい重い実装（Wonder）。必ず plan → 確認 → run の2段。同時に1本まで。
  - 大量の細かい作業（Spark）。
  - 画像は横位置のイメージカット・顔アップ・構図ラフだけ。人物写真の本番（透過・縦位置・同じ人をそろえる）は今の工程（OpenAI 版）のまま。根拠：`/workspace/knowledge/design/photo_director/muse_eval_2026-11-02/report.md`。
  - UI の仕上げ、法務文書、最終判断には使わない。
- **外部 LLM に出してよい範囲（若松さん決定 2026-11-02 15:59）**：学習に使わない設定（Muse は Contributor mode オフ、agy は学習オフ など）なら、**Shelpha のデータそのもの（推計値・推計データ）と秘密の値（パスワード・APIキー・トークン・Cookie）以外は**、Muse を含むどの LLM に出してもよい。この2つだけは task.md にも、Muse に渡す作業フォルダ（`--workspace` / `--project` で読める範囲）にも、Muse が読む agmsg スレッドにも置かない。
- 作業フォルダに Shelpha のデータそのもの（CSV・JSON・SQL の結果など）や秘密の値のファイルが無いことを確かめてから渡す。`/workspace` 直下は渡さない。
- 例外 2026-11-23 19:03 JST 若松さん承認：補正が終わるまで、ShelphaのASIN単位データはRutzboの中でだけ claude -p（fableを含む）、codex exec、agy の gemini-4-carbon-low/medium/high（2026-11-24 07:48 若松さん追加）に渡してよい。チャット・box・ほかのサービスには出さない。終わりは若松さんが宣言する。（19:21追加：須藤のmemory/active-context/sudo.md と memory/decisions.md も同じ範囲・同じ期限で渡してよい）正本 rules/2026-11-23_shelpha-asin-multillm-exception.md
- Contributor mode（Meta の学習利用）は常にオフ。保存設定 `~/.config/muse/settings.json` も `"contributor_mode_enabled": false`。勝手に変えない。`muse` の `/settings` で Contributor mode をオンにしない。
- サブスクだけ：Meta の API キーを作らない。`META_API_KEY`・`--api-key-stdin`・`muse auth`・従量課金・OpenRouter 経由は使わない。
- 使ってはいけない：`--yolo`、`--disable-approval`、`--disable-sandbox`、`--contributor-mode on`、`--reasoning-effort max|ultra`。
- **テンプレ配布の指示 md を Muse に読ませる（若松さん決定 2026-11-02 15:56「今のCLAUDE.mdをそのまま読ませる」）**：5co-hub/template が配る `AGENTS.md`（Codex の入口。「作業ルールの正本は同じディレクトリの CLAUDE.md」と誘導）と `CLAUDE.md` は、Muse に読ませてよい。muse-run は毎回 `--trust-workspace` を付け、cwd（または `--project`）の AGENTS.md / CLAUDE.md を Muse が読み込む。個人ルールも読む（`~/.config/muse/settings.json` の `context.foreign_personal_rules=true`・`foreign_personal_skills=true`。`telemetry.enabled=false`・Contributor mode オフは維持）。中立フォルダ規則（終了コード 6・`/workspace/muse-neutral/`）は撤回。

### 使ってはいけないフラグ
- `--dangerously-skip-permissions`、`--allow-dangerously-skip-permissions`、`--permission-mode bypassPermissions`
- `--dangerously-bypass-approvals-and-sandbox`、`-s danger-full-access`、`--dangerously-bypass-hook-trust`
- `muse` の `--yolo`、`--disable-approval`、`--disable-sandbox`、`--contributor-mode on`
- `--search` などのネット検索は、必要なときだけ。

### 長い仕事の起こし方（2026-11-16 20:59 JST 若松さん承認）

- 前面で待ち切れない仕事は、Shell ツールのバックグラウンド（`block_until_ms 0`）で起動する。完了通知で Bot が起きる。
- 対象は `claude -p` / `codex exec` / `muse-run`。ポーリングしない。
- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。起動直後の通知で会話を終えると、作業の完了で誰も起きない。
- 上の呼び出し例は、前面で待ち切る短い仕事用。
- 完了後は `progress.md` を `tail -3` だけ読む。progress.md の先頭行には自分のBot名を書く。

### 時間と出力
- 必ず `timeout` を付ける。目安：短い問い 120秒、レビュー 600秒、コード修正 900秒。
- 出力は `out/` のファイルに保存する。チャットには要約を5行以内で返す。
- 巨大な表やログをチャットに貼らない。ファイルのパスを示す。
- 終了コードを確認する。失敗したら、エラーの1行とログのパスを報告する。

### agmsg（エージェント間メッセージ。導入：2026-11-02、v1.7.0）
box ローカルの SQLite を介して、grok（Grok Bot）・claude・codex・muse・gemini がメッセージをやり取りする。ネットには出ない（remote sync・ext-tool・plugin は使わない）。
- チーム：`box`。DB：`~/.agents/skills/agmsg/db/messages.db`（リンク：`/workspace/knowledge/agents/agmsg/db`）。席（project）：`/workspace/knowledge/agents/agmsg/seats/<名前>/`（muse も同じ。2026-11-02 16:00 に `/workspace/muse-neutral/agmsg/` から移動）。配信モードは全員 off（自分で読みに行く）。
- 送る・読む（ラッパー `/workspace/knowledge/agents/bin/agmsg-box`）：
```
agmsg-box send grok claude "本文"            # 1名へ。長文は --body-file F
agmsg-box send grok all-but-muse "本文"      # muse 以外の全員へ（all は muse を含む）
agmsg-box inbox grok                          # 未読を読んで既読にする
agmsg-box history "" 20                       # 履歴
```
- Claude / Codex をヘッドレスで返信させるとき：`claude -p --allowedTools "Bash(/workspace/knowledge/agents/bin/agmsg-box:*)" --tools Bash`、`codex exec -s workspace-write --skip-git-repo-check`（`~/.codex/config.toml` の writable_roots に agmsg の db/teams/run を追加済み）。席フォルダで実行する。
- Muse の返信は `agmsg-muse-reply <返信先>` で行う（muse にはシェルを与えず、スクリプトが inbox を読んで muse-run に渡し、答えを送る）。
- **機密のルール（2026-11-02 15:59 更新）**：DB は box の中だけにあるが、muse 宛て・`all` 宛ての本文は Meta に送られる（学習オフ）。Muse に出せないのは **Shelpha のデータそのもの** と **秘密の値** だけ。Shelpha のデータそのものは muse を外した宛先（1名指定か `all-but-muse`）でだけ送る。秘密の値（パスワード・キー・トークン・Cookie）はどの宛先にも書かない。

## (d) 守ること
- 秘密情報（パスワード、APIキー、トークン、Cookie）をチャットやファイルに書かない。認証ファイル（`auth.json`、`.credentials.json` など）の中身を表示しない。
- `/home/box/agent-data/chrome-cookie-seed.json` に触らない。Cookie やトークンを抜き出さない。
- 新しい GitHub リポジトリを作らない。
- 本番反映（リリース、main へのマージ、デプロイ）は、若松さんの確認のあとだけ。
- ファイルを削除するときは、若松さんの明確な「はい」が必要。自分で作った一時フォルダだけは例外。
- メール・チャット・SNS の送信や投稿、購入、契約は、若松さんの承認のあとだけ。承認前は下書きまで。
- データ元は「Shelpha」と書く。「Ignite」と書かない。
- 人事データ（評価、給与、面談など）は、社員が見られる場所に置かない。
- テンプレートの展開は Template Bot の担当。他のBotはしない。
- 法務文書の流れ：contract → コピーライター → 若松さん → corporate-website。順番を飛ばさない。
- 数字をでっち上げない。ないものは「未入手」と書く。空欄を 0 で埋めない。
- 担当範囲の外は触らない。他のBotのフォルダやリポジトリを書き換えない。
- 送信・投稿・購入・削除・本番反映は、準備までにとどめて若松さんに確認する。

## (e) 報告
- 報告は SMART の5項目。1項目1行。
  - S（具体的）：何を、どの対象に。GMS800億へのつながりを1語で。
  - M（測定可能）：目標値／現在地／差／今回の変化を数字で。
  - A（達成可能）：根拠（Shelpha推計・過去実績・市場データ）と、自分で動かせる手段。
  - R（関連性）：KR と GMS800億にどう効くか。
  - T（期限）：いつまでに。次の確認日。
- 測っていない数字は「未計測（計測方法：〜）」と書く。数字を作らない。
- 良いことも悪いことも、同じ形で正直に書く。
- Claude / Codex / Muse の出力をそのまま事実として報告しない。自分で確かめてから書く。確かめていない点は「未確認」と書く。

## 記憶の使い方（2026-11-23 14:29 JST 若松さん承認）
- 若松さんやほかのBotに聞き返す前に、`memory/decisions.md` と `memory/sessions/` を `rg` で検索する。
- 食い違う決定を見つけたら上書きせず、両方に `[食い違い YYYY-MM-DD]` の印を付ける。どちらを残すかは若松さんに確かめる。

## (f) 決まりの正本（索引）
- ①全Bot共通の索引（詳細の正本はここからたどる。本文はここに複製しない）：
  `/workspace/knowledge/agents/rules/2026-11-16_context-layer1-common.md`
- 取り次ぎの手順（必須スキル `handoff-context-layers`。回し先の選定は `grok-minimal-multillm`）：
  `/workspace/knowledge/agents/rules/2026-11-16_llm-context-layers.md`
- 取り次ぎは層ごとの独立md：`/workspace/knowledge/agents/rules/2026-11-14_handoff-by-file.md`
- Grokは極力トークンを使わず委託：`/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md`
- 使ったLLMを末尾に書く：`/workspace/knowledge/agents/rules/2026-11-15_llm-tag-suffix.md`
- Codex進捗ファイル方式：`/workspace/knowledge/agents/rules/2026-11-16_codex-progress-file.md`
- 外へ送る仕組みを作ったら汐見に知らせて表の担当へ回す（v2）：`/workspace/knowledge/agents/rules/2026-11-16_builder-owns-secrets-and-delivery.md`
- 頼んだまま止めない（CLIは block_until_ms 0 で起動、切り離さない、progress.md 先頭行にBot名）：`/workspace/knowledge/agents/rules/2026-11-16_no-silent-stall.md`
- 取り次ぎは Rutzbo の T3 Code を第一候補にする（送信対策の必須条件を含む）：`/workspace/knowledge/agents/rules/2026-11-24_t3-harness-relay.md`
