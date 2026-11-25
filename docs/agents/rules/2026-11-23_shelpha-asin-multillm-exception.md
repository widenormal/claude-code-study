# Shelpha ASIN単位データのマルチLLM利用の例外

- 状態：2026-11-23 19:03 JST 若松さん承認「このまま配布してよい」（須藤経由）。全Bot共通ルール（AGENTS.md・grok-minimal-multillm）と監視の基準に反映済み。
- 根拠：2026-11-23 19:02 JST 若松さん発言「データはマルチLLMに出して良いです」。19:0x JST 若松さん回答「はい、例外として書き込んでよい」（共通ルールと監視の基準へ）。いずれも須藤 航（Shelpha）のチャットで、須藤経由で汐見が受領。
- 置き換える運用：2026-11-23 18時の「ShelphaのデータはRutzbo外にもどのLLMにも出さない」。下の範囲に限って上書きする。

## 例外の範囲
- 対象：ShelphaのASIN単位データ。
- 追加の対象（2026-11-23 19:21 JST 若松さん回答「A：sudo.mdとdecisions.mdも渡してよい。今回の例外に足し、期限は私の終了宣言まで」、須藤経由）：/workspace/shelpha-memory の memory/active-context/sudo.md と memory/decisions.md。Rutzbo上の作業フォルダにある写しを含む。sessions/ と他のファイルは対象外のまま。
- 渡してよい先：Rutzbo上の `claude -p`（モデル fable を含む）、`codex exec`、`agy --model gemini-4-carbon-low` / `-medium` / `-high`（Gemini 4 Carbon、モデル名の完全一致だけ）。
- Carbonの追加（2026-11-24 07:48 JST 若松さん回答「Carbon（Gemini 4 Carbon）もASIN単位の例外に足してください。期限は私の終了宣言まで」、須藤 航（Shelpha）のチャットで受け、須藤経由で汐見が受領。前提として11/23の若松さん発言「carbonは書面で許可を得てます」）。Rutzbo側はフックで上の3つのモデル名だけを許可（AI-shelpha 12ff63c・50154d7、shelpha-memory AGENTS.md 5f70403）。
- 置き場所：Rutzboの中だけ。チャット、box、そのほかのサービスには出さない。
- 期限：補正が完了するまで。補正完了は、若松さんが終了を宣言した時点とする（2026-11-23 19:0x JST 若松さん回答）。

## 変わらないこと
- 秘密の値はどのLLMにも渡さない。
- 本番DBには触らない。
- 取り次ぎで他のBotやGrokに返すのは、結論とファイルの場所だけ。
