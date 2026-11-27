# Shelpha ASIN単位データのマルチLLM利用の例外

- 状態：2026-11-23 19:03 JST 若松さん承認「このまま配布してよい」（須藤経由）。全Bot共通ルール（AGENTS.md・grok-minimal-multillm）と監視の基準に反映済み。
- 根拠：2026-11-23 19:02 JST 若松さん発言「データはマルチLLMに出して良いです」。19:0x JST 若松さん回答「はい、例外として書き込んでよい」（共通ルールと監視の基準へ）。いずれも須藤 航（Shelpha）のチャットで、須藤経由で汐見が受領。
- 置き換える運用：2026-11-23 18時の「ShelphaのデータはRutzbo外にもどのLLMにも出さない」。下の範囲に限って上書きする。

## 例外の範囲
- 対象：ShelphaのASIN単位データ。
- 追加の対象（2026-11-23 19:21 JST 若松さん回答「A：sudo.mdとdecisions.mdも渡してよい。今回の例外に足し、期限は私の終了宣言まで」、須藤経由）：/workspace/shelpha-memory の memory/active-context/sudo.md と memory/decisions.md。Rutzbo上の作業フォルダにある写しを含む。sessions/ と他のファイルは対象外のまま。
- 渡してよい先：Rutzbo上の `claude -p`（モデル fable を含む）、`codex exec`、`agy --model gemini-4-carbon-low` / `-medium` / `-high`（Gemini 4 Carbon、モデル名の完全一致だけ）。
- Carbonの追加（2026-11-24 07:48 JST 若松さん回答「Carbon（Gemini 4 Carbon）もASIN単位の例外に足してください。期限は私の終了宣言まで」、須藤 航（Shelpha）のチャットで受け、須藤経由で汐見が受領。前提として11/23の若松さん発言「carbonは書面で許可を得てます」）。Rutzbo側はフックで上の3つのモデル名だけを許可（AI-shelpha 12ff63c・50154d7、shelpha-memory AGENTS.md 5f70403）。
- T3経由の追加（2026-11-26 15:32 JST 若松さん決定）：
  - 対象は補正作業に限る。
  - 追加する経路：須藤@tw1 → Rutzbo上のT3 → LLM。
  - T3 の範囲：Nightly .5209以降、127.0.0.1／LAN だけ。T3 Connect と Publish は使わない。
  - T3 で使ってよいプロバイダは Claude（claudeAgent）と Codex だけ。Ollama と、それ以外のプロバイダは不可。
  - 置き場所はこれまでどおり Rutzbo の中だけ。
  - 起動先は `~/work/AI-shelpha`（AGENTS.md あり）。
  - 同時に大量起動しない。
  - 決定日時：2026-11-26 15:32 JST。決定者：若松さん。
- 補正作業の追加（2026-11-26 15:33–15:34 JST 若松さん決定。根拠の発言「gemini cliも例外に足します」「他には、local llmもです」「T3からGeminiを呼べるようにしてください」）：
  - 対象は補正作業に限る。上の 15:32 の T3 経由（Claude〈claudeAgent〉と Codex）はそのまま残し、次の3つを足す。
  - (a) T3 の Antigravity プロバイダ経由の Gemini。T3 の範囲・起動先・T3 Connect と Publish を使わないことは上と同じ。
  - (b) Rutzbo 内で直接動かす Gemini CLI（`/opt/homebrew/bin/gemini`）。
  - (c) ローカルLLM：Ollama を `127.0.0.1` で、Rutzbo 内から直接使う。T3 に Ollama プロバイダは足さない。導入済みモデルは `gemma4:26b` と `qwen-slide:latest` の2つだけ（2026-11-26 15:42 JST に `ollama list` で読み取り確認）。新しいモデルの pull はしない。
  - 上の 15:32 の行の「Ollama と、それ以外のプロバイダは不可」は T3 のプロバイダとしての扱いを指す。今回の決定で T3 で使ってよいプロバイダは Claude（claudeAgent）・Codex・Antigravity（Gemini）になる。Ollama は T3 に乗せず、(c) の直接利用に限る。
  - 置き場所はこれまでどおり Rutzbo の中だけ。チャット・box・そのほかのサービスには出さない。同時に大量起動しない。期限は若松さんの終了宣言まで。
  - 決定日時：2026-11-26 15:33–15:34 JST。決定者：若松さん。
- 置き場所：Rutzboの中だけ。チャット、box、そのほかのサービスには出さない。
- 期限：補正が完了するまで。補正完了は、若松さんが終了を宣言した時点とする（2026-11-23 19:0x JST 若松さん回答）。

## 変わらないこと
- 秘密の値はどのLLMにも渡さない。
- 本番DBには触らない。
- 取り次ぎで他のBotやGrokに返すのは、結論とファイルの場所だけ。
