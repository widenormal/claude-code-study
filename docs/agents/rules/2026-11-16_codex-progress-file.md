# Codex進捗ファイル方式（2026-11-16 16:18 JST 若松さん決定、全Botに展開）

目的：GrokがCodexの進捗を取りに行かず（トークン節約）、Codex側から区切りごとに経過が残る仕組みにする。

## やり方
1. codex exec に渡す指示の末尾に必ず次を足す：
   「作業フォルダの progress.md に、区切り（調査完了・実装完了・ビルド/テスト結果・プレビュー配置・PR作成・詰まり）ごとに1行追記する。形式：`HH:MM JST | 段階 | 一言（20字程度）`。詰まったら `BLOCKED | 理由` を書いて止まる。最後に `DONE | 結果の場所` を書く。」
2. codex exec はバックグラウンド（block_until_ms 0）で起動する。終了時の完了通知でGrokが起きるので、ポーリングしない。
3. Grokは progress.md を `tail -3` で読むだけ（ログ全体は開かない）。読むのは「若松さんに聞かれたとき」「完了通知が来たとき」だけ。
4. 作業をつなぐときは `codex exec A; codex exec B` の単純な順番にする。`pgrep -f` で自分のコマンド文字列にも当たる待ち方は使わない（自分自身を待ち続ける不具合が起きた）。
5. Slackなど外への自動通知は送信にあたるため、若松さんの承認なしに付けない。

## 対象は Codex だけでない（2026-11-16 20:59 JST 若松さん承認）

- 同じ起こし方を `claude -p` と `muse-run` にも使う。Shell ツールのバックグラウンド（`block_until_ms 0`）で起動し、完了通知で起きる。
- `nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。
- progress.md の先頭行に自分のBot名を書く。
- 完了後は `progress.md` を `tail -3` だけ読む。全文を読まない。
- 正本：`/workspace/knowledge/agents/rules/2026-11-16_no-silent-stall.md`
