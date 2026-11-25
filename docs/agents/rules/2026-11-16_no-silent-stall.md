# 依頼したまま止まらないためのルール（全Bot共通）

- 作成者：汐見 遼（KR-1B AI組織図）
- 作成日時：2026-11-16 JST
- 根拠：若松さん 2026-11-16 20:41 JST

## 0. この文書の状態

- 状態：承認済み。若松さん 2026-11-16 20:59 JST「この案で配布と見張りの開始を進めてください」（このチャットで本人回答）。配布はTemplate（榊さん）、周知は藤村さん、見張りは汐見のルーチン。
- 細部の決定（汐見、若松さんの委任による）：策1は全Botで必須。促し先は元のBotだけ（汐見への集約はしない）。元Botの特定は progress.md の先頭行にBot名を書く。策2の完了webhookは、秘密の選定（伏見さん）と登録・着信確認（久我さん）が済むまで使わず、それまでは策1か、そのターンで待つ。PR #245 は当面そのまま。下の「決めること」一覧はこの決定で閉じた。
- 配布：榊さんに依頼（2026-11-16 21:0x）。付録の差分をスキルへ反映するのは榊さん。
- 見張りは汐見のルーチン「止まった作業の見張り（KR-1B）」で開始（2026-11-16）。webhook の鍵は未登録（下の修正策2参照）。
- 追記（2026-11-19 14:27 JST 若松さん決定、須藤さんのチャットで本人がカード回答）：第6.5節「『進める／送る／登録する』などの約束」。文案は浅野さん。周知は藤村さん、スキル反映は榊さん。
- 追記（2026-11-19 17:24 JST 若松さん決定、浅野さんのチャットで本人がカード回答「進めてよい」）：第6.6節「順番作業（AのあとB）を止めない」。文案は汐見。周知は藤村さん、スキル反映は榊さん。見張り拡張は汐見のルーチン kr-1b-2。課題 Plane KR1B-1。

## 1. 目的

依頼したあと確認せず、作業が止まることを防ぐ。

マルチLLM化のあと、Bot が `claude -p` / `codex exec` / `muse-run` に渡し、そのまま会話を終える事故が出ている。CLI が終わっても Bot が起きないので、誰も続きを見ない。例：嵯峨 尚人（Tesla）が「終わったらお送りします」と述べ、未送付のまま止まった（若松さん 2026-11-16 20:41 JST）。

## 2. 修正策1（原則）：追跡付きバックグラウンドで起こす

- CLI は Shell ツールのバックグラウンド起動（`block_until_ms 0`）で動かす。完了通知で Bot が起きる。
- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。切り離すと完了で起きない。
- 対象は `claude -p`、`codex exec`、`muse-run` の3つ全部。
- ポーリングしない。`sleep` で様子を見に行かない。完了通知を待つ。
- `timeout` は従来どおり付ける（短い問い 120秒、レビュー 600秒、コード修正 900秒）。
- 完了後は既存どおり `progress.md` を `tail -3` だけ読む。全文を読まない。
- 短い仕事は前面で待ち切ってよい。その場合はこの節は要らない。

## 3. 現行指示の整理

公式スキル・正本は切り離しを命じていない。禁止もしていない。正しい起こし方は Codex についてだけ書かれている。

| 文書 | いま書いてあること | 足りないこと |
| --- | --- | --- |
| 正本 `/workspace/knowledge/agents/rules/2026-11-16_codex-progress-file.md` 第2項 | 「codex exec はバックグラウンド（block_until_ms 0）で起動する。終了時の完了通知でGrokが起きるので、ポーリングしない。」 | 対象が `codex exec` だけ |
| スキル `/home/box/agent-data/workflows/grok-minimal-multillm/SKILL.md` と正本 `/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md` | 同趣旨（`codex exec` のみ） | `claude -p` / `muse-run` の起こし方が無い |
| `/workspace/knowledge/agents/AGENTS.md` (c) 呼び出し方 | `timeout 600 claude -p ...` / `timeout 900 codex exec ...` の前面待ち例 | 起こし方と切り離し禁止が無い |
| スキル `/home/box/agent-data/workflows/claude-codex-cli/SKILL.md`、`/home/box/agent-data/workflows/claude-code-codex-cli/SKILL.md` | 同型の前面待ち例 | 同じ |

この隙間で、実務が長い仕事を `nohup codex exec ... &` で切り離し、起動直後の通知で会話を終えている。Shell の通知は起動コマンドの終了で出るだけで、本作業の終了では Bot が起きない。

## 4. 修正策2（追跡付き起動が使えない長い仕事に限る）：完了webhook

追跡付きバックグラウンドで足りる仕事には使わない。枠を超える長時間ジョブだけ。

- ジョブの最後の1行で、全Bot共用の完了 webhook へ送る。
- ジョブに `GROKBOT_JOB_ID` を付ける。無ければ送らない。
- 送り先は環境変数 `GROKBOT_WEBHOOK_URL`。鍵はファイルに置かず、実行時に `GROKBOT_WEBHOOK_KEY_REF`（1Password 参照）から読む。
- 送る JSON は jobId / event / tool / hookEvent / timestamp だけ。本文・データは送らない。
- 秘密は名前だけ。値と実URLはこの文書にも task.md にも書かない。
- routine id は今回の依頼で `box-webhook-bot`（汐見のBot）と指定された。設計文書上は未作成で、box の設計文書・main・記憶に「作成済み」の記録は見当たらない。**存在するかは未確認。**
- つながっていないまま本番利用しない。

設計の正（下書き）：

- `/workspace/aac/docs/webhook-wake-on-completion.md`（作成 2026-11-05）。冒頭に「routine・webhook・鍵はまだ作っていない。サンプルはどこにもインストールしていない」と書かれている。
- 例示 `/workspace/aac/docs/examples/webhook-wake/`（未インストール）。テスト `/workspace/aac/tests/test_webhook_hook.sh`。
- PR #245（DRAFT・OPEN・**未マージ**、枝 `docs/webhook-wake`）：https://github.com/5co-hub/ai-agent-architecture-comparison/pull/245

担当（`/workspace/knowledge/agents/rules/2026-11-16_builder-owns-secrets-and-delivery.md` v2）：

| 作業 | 担当 | 条件 |
| --- | --- | --- |
| 鍵・URL の項目を決める | 伏見 静（1Password） | 新規保存は若松さんの承認後 |
| サービスへ登録（1Password 参照）と届くかの確認 | 久我 慎（情報システム） | 本番チャンネルへ試し投稿しない |

未決・未確認：

| 項目 | 状態 |
| --- | --- |
| routine `box-webhook-bot` が既にあるか | 未確認。設計は未作成のまま |
| 全Botで1つか Bot ごとか | 未決。設計は1つを推奨。起きる側が jobId 先頭のBot名で振り分ける経路は未実装 |
| 1Password の vault / item / field 名 | 未決（設計 4-2） |
| hook 方式（Stop 等）と「ジョブ最後の1行」方式の関係 | 未決。設計は hook ＋任意のラッパー。修正策2は最終行方式。両方残してよいが混同しない |
| Template 配布と試験開始Bot | 未決（設計 4-3 / 4-4） |

## 5. 修正策3（承認後に新設）：止まっている仕事の見張り

承認後にだけ、汐見の定時ルーチンとして置く。この作業では作らない。

- 時間：7:00–21:59 JST に1時間ごと。22:00–6:59 JST は動かさない。Botにも人にも連絡しない。
- 実装は安価な shell。必要なときだけ Claude Code。スキャン自体に Grok を使わない。
- 見る対象：`/workspace` 配下の `progress.md`（`node_modules` / `.git` / vendor は除外）。
- 判定：最終行が `DONE` でない、かつ（最終行の時刻が30分超前、または `BLOCKED`）。
- 判定の追加（2026-11-19 第6.6節）：`NEXT | … | status:pending` があり、同じ系列の最終進捗行が `DONE` で、その時刻から30分超なら促す（前がDONEなのに次が未起動）。
- 該当したら、そのBotへ続きまたは報告を1行で促す。
- 止まっているものがゼロなら、何も送らない（沈黙）。
- 作業フォルダから元Botを特定する方法は未決。案は `progress.md` の先頭行にBot名を書く。決めるのは若松さん（下の8項）。

## 6. 追加ルール：「終わったらお送りします」の条件

- 「終わったらお送りします」（同趣旨を含む）と言うなら、その仕事に修正策1か修正策2のどちらかが付いていること。
- 付いていなければ、そのターンの中で終わるまで待つ。
- 待ち切れないなら、途中までを報告し、次の起こし方を先に付ける。約束だけ残して終わらない。

## 6.5. 「進める／送る／登録する」などの約束（2026-11-19 追記）

- 根拠：若松さん 2026-11-19 14:27 JST 決定（須藤 航のチャットで本人がカード回答）。文案は浅野 結衣。
- きっかけ：2026-11-19 11:53ごろ、須藤が若松さんへ「Prism・SellerApp・AMZScoutの登録を進めておきます」と書いたが、作業の開始呼び出しをしないまま返事を終え、約2時間手つかずだった。progress.md がない仕事だったため、見張りにも引っかからなかった。
- ルール：若松さんや依頼元へ「進める／送る／登録する」など完了や着手を約束する文は、同じターンでその作業の開始呼び出しを出したあとにだけ書いてよい。出せないときは約束せず、未着手と理由を書く。
- 第6節（「終わったらお送りします」）と併用する。約束のあとに追跡が付かないまま会話を終えない。


## 6.6. 順番作業（AのあとB）を止めない（2026-11-19 追記）

- 根拠：若松さん 2026-11-19 17:24 JST 決定（浅野 結衣のチャットで本人がカード回答「進めてよい」）。文案は汐見 遼。課題 Plane KR1B-1。
- きっかけ：2026-11-19 真鍋 透の映り込み修正で「1本目が終わったら2本目を起動する」と伝えたが、1本目 DONE（10:50）の完了通知で起きず、2本目が約4時間40分未起動（15:33起動）。
- 対象：同じBotが「Aが終わったらBを始める」順番で動かす作業（CLI同士、またはCLIのあとに報告・送信の段取りを含む）。

### 6.6.1 原則：1本の起動でつなぐ（A && B）

- 可能な限り、1回の追跡付きバックグラウンド起動の中で `A && B`（または同等の連続実行）につなぐ。Aの完了通知だけに頼って、人が起きてからBを手で起動しない。
- 例：`timeout 900 claude -p "…A…" && timeout 900 claude -p "…B…"` を Shell の `block_until_ms 0` で1本起動する（修正策1と同じ起こし方）。
- AとBの間に若松さんの判断が必要なときはつなげない（6.6.2へ）。

### 6.6.2 つなげないとき：台帳に「次の作業」を1行書く

- A && B でつなげないときは、作業フォルダの `progress.md`（または続きの progress-N.md）に、次の未起動作業を次の形式で1行書く（Bot名の行の直後がよい）。

```
NEXT | <次の作業の一言> | wait_for:DONE | status:pending
```

- 意味：
  - `NEXT`：見張りが拾う印。
  - 次の作業の一言：フォルダ名や工程名（秘密・顧客数字は書かない）。
  - `wait_for:DONE`：いまの progress の最終段階が DONE になったら次を起動する、の印。
  - `status:pending`：まだ起動していない。Bを起動したターンで `status:started` に直すか、行を消す。
- 前の作業が DONE なのに `status:pending` のまま30分超えたら、汐見の見張りが元Botへ1通促す（修正策3の拡張。設計は `/workspace/knowledge/agents/rules/designs/2026-11-19_stall-watch-next-job.md`）。

### 6.6.3 「終わったら始めます」は禁止（§6.5と併用）

- まだ起動していない次の作業について、「終わったら始めます」「終わったら起動します」など着手の約束をしない。
- 言うなら、同じターンで (a) A && B の1本起動を出すか、(b) `NEXT | … | status:pending` を書いてから、追跡付きでAだけを起動する。どちらもできないときは約束せず、未着手と理由を書く（§6.5と同じ型）。

### 6.6.4 変わらないこと

- 外への送信・投稿、削除、本番公開は若松さんの承認後だけ。
- 完了webhook（修正策2）は鍵準備が済むまで使わない。

## 7. 変わらないこと

次は若松さんの承認後だけ。

- 外への送信・投稿。
- ルーチンの作成。
- 秘密の新規保存。
- 本番利用。
- スキルの配布。

## 8. 若松さんに決めてもらう項目

1. この案を本文化してよいか。
2. 配布してよいか（Template：榊さん、周知：藤村さん）。
3. 修正策1を全Bot必須にするか、長い仕事だけにするか。
4. webhook routine `box-webhook-bot` が既にあるか。無ければ作るか。
5. webhook は全Botで1つか、Botごとに分けるか。
6. 鍵・URL の置き場所（1Password の vault / item / field）。
7. 1Password への新規保存の可否（伏見 静が項目を決め、久我 慎が登録と着信確認）。
8. PR #245 を進めるか、DRAFT のまま置くか。
9. 見張りルーチンを新設してよいか。
10. `progress.md` から元Botを特定する方法（先頭行にBot名を書く案でよいか）。
11. 見張りが促す相手は元Botだけか、汐見にも集約するか。

---

# 付録：スキル・正本への追記案

付録1は 2026-11-19 に榊が `grok-minimal-multillm` スキルと正本へ反映済み（第6.5節の約束行に加え、同日17:24の第6.6節・順番作業行も反映）。付録2・3は未反映。

行番号は未確認（この作業の実行権限では `/workspace/knowledge` と `/home/box/agent-data` を読めない）。適用時に、各ハンクの見出し位置を目で確かめてから入れる。すべて追加だけで、既存行は消さない。

## 付録1：`grok-minimal-multillm`（スキルと正本の2本に同文）

適用先：
- `/home/box/agent-data/workflows/grok-minimal-multillm/SKILL.md`
- `/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md`

```diff
--- a/workflows/grok-minimal-multillm/SKILL.md
+++ b/workflows/grok-minimal-multillm/SKILL.md
@@ codex exec の起こし方を書いた節の直後に追加 @@
+- 起こし方は `claude -p` と `muse-run` も同じ。Shell ツールのバックグラウンド（`block_until_ms 0`）で起動し、完了通知で起きる。ポーリングしない。
+- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。切り離すと作業の完了で起きない。
+- 「終わったらお送りします」と言うなら、その仕事に追跡付き起動（`block_until_ms 0`）か完了webhookが付いていること。付いていなければ、そのターンの中で待つ。
+- 若松さんや依頼元へ「進める／送る／登録する」など完了や着手を約束する文は、同じターンでその作業の開始呼び出しを出したあとにだけ書いてよい。出せないときは約束せず、未着手と理由を書く。（2026-11-19 14:27 JST 若松さん決定。正本 2026-11-16_no-silent-stall.md 第6.5節）
+- 順番作業（AのあとB）は可能な限り1本の起動で `A && B` につなぐ。つなげないときは progress.md に `NEXT | … | wait_for:DONE | status:pending` を1行書く。起動していない次について「終わったら始めます」は禁止。（2026-11-19 17:24 JST 若松さん決定。正本 2026-11-16_no-silent-stall.md 第6.6節）
```

## 付録2：`2026-11-16_codex-progress-file.md`（対象を広げる1節）

適用先：`/workspace/knowledge/agents/rules/2026-11-16_codex-progress-file.md`

```diff
--- a/agents/rules/2026-11-16_codex-progress-file.md
+++ b/agents/rules/2026-11-16_codex-progress-file.md
@@ 第2項（codex exec はバックグラウンドで起動する）の直後に追加 @@
+## 対象は Codex だけでない
+
+- 同じ起こし方を `claude -p` と `muse-run` にも使う。Shell ツールのバックグラウンド（`block_until_ms 0`）で起動し、完了通知で起きる。
+- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。
+- 完了後は `progress.md` を `tail -3` だけ読む。全文を読まない。
```

## 付録3：呼び出し例に起こし方を足す（3か所に同文）

適用先：
- `/home/box/agent-data/workflows/claude-codex-cli/SKILL.md`
- `/home/box/agent-data/workflows/claude-code-codex-cli/SKILL.md`
- `/workspace/knowledge/agents/AGENTS.md`（(c) 呼び出し方）

既存の前面待ち例は、短い仕事用として残す。

```diff
--- a/agents/AGENTS.md
+++ b/agents/AGENTS.md
@@ 「(c) 呼び出し方」の最後、「時間と出力」の前に追加 @@
+### 長い仕事の起こし方
+
+- 前面で待ち切れない仕事は、Shell ツールのバックグラウンド（`block_until_ms 0`）で起動する。完了通知で Bot が起きる。
+- 対象は `claude -p` / `codex exec` / `muse-run`。ポーリングしない。
+- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。起動直後の通知で会話を終えると、作業の完了で誰も起きない。
+- 上の呼び出し例は、前面で待ち切る短い仕事用。
+- 完了後は `progress.md` を `tail -3` だけ読む。
```

---

使用LLM：Claude Code。起案は汐見 遼。
