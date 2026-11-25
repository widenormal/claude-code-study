# 取り次ぎは Rutzbo の T3 Code を第一候補にする（全Bot共通ルールの正本・承認済み／未配布）

> **この文書は全Bot共通ルールの正本である。** 2026-11-24 22:30 JST 若松さん承認（14件すべて草案どおり、@tw1展開含む）。配布は11/27 15:19 JSTのリセット後に榊、周知は藤村。
> **まだ配布していない。** 配布は 2026-11-27 15:19 JST の Grok 週次リセット後に榊 亮介（Template）が行う。配布までの間、この正本を他Botへ送ったり、スキルへ反映したりしない。
> **配布後も、§3 の「効き始める条件」を満たすまで T3 第一候補の運用は開始しない。** それまでの取り次ぎは、今までどおり box の CLI（`claude -p` / `codex exec` / `muse-run` / `agy`）で行う。

- 起案：汐見 遼（KR-1B AI組織図）
- 正本の担当：汐見 遼
- 配布：榊 亮介（Template）— 2026-11-27 15:19 JST の Grok 週次リセット後
- 周知：藤村 秀明（メインGrokBot）— @tw1 への展開を含めて承認済み（§10-3）
- 作成日時：2026-11-24 JST
- 更新：2026-11-24 19時台 JST（Codex が T3 経由で動くことを確認したため §3・§4.1・§4.2・§6.2・§10-8 を更新。§4.4 の作業×二段の表、§4.5 のローカルLLM、§10 の判断事項 15〜20、§11 の用語を追加）
- 更新：2026-11-24 21:31 JST（若松さん承認「ollamaを手段に加えて」。§4.4 表の「機密の大量分類・整形」通常使用に Ollama `gemma4:26b` を記入。§4.5・§10-18・§10-19 と注記を追随。`routing_rules.yaml` は未変更。配布なし）
- 更新：2026-11-24 22:30 JST（若松さん承認。§10 の判断事項 1〜14 をすべて草案どおり承認。@tw1 への展開も承認。`_draft` を外して正本化。判断事項 15〜20 は今回の承認に含まれない＝未決のまま）
- 状態：**承認済み。未配布。**（配布は 2026-11-27 15:19 JST のリセット後に榊 亮介、周知は藤村 秀明）

## 1. 文書の位置づけ

1. この文書は承認済みの正本である（2026-11-24 22:30 JST）。ただし**まだ配布していない**。配布が済むまで、各Botはこの文書を根拠に動作を変えない。
2. 既存ルールを打ち消さない。上乗せの正本である。特に、回し先（どのLLMに頼むか）の正本は `/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md` のままである。この正本が足すのは「**取り次ぎの起動経路**」だけで、回し先の選び方は置き換えない。
3. 配布されるまでは、取り次ぎは今までどおり box の CLI（`claude -p` / `codex exec` / `muse-run` / `agy`）で行う。配布後も §3 の「効き始める条件」を満たすまでは同じ。
4. この文書の作成・正本化にあたり、Rutzbo への接続試行、T3 の起動・ログイン、設定変更、他Botへの連絡は一切行っていない。
5. §10 の判断事項 15〜20 は今回の承認に含まれない。未決のまま扱い、承認済みとして引用しない。

## 2. 目的

- Rutzbo 上の T3 Code を、他LLMへ作業を取り次ぐときの第一候補に置く（2026-11-24 22:30 JST 承認。運用の開始は §3 の「効き始める条件」を満たしてから）。
- 狙いは、取り次ぎ先の実行環境（GUI・プロバイダの認証状態・CLI）をそのまま使い、取り次ぎごとに環境を組み直さずに済ませること。
- 既存の box CLI 取り次ぎは廃止しない。フォールバック（代わりの経路）として必ず残す。
- 単一マシン（Rutzbo 1台）に依存する弱点を、稼働確認とフォールバックの手順で埋める。

## 3. 適用範囲

- **対象**：box 上で動く全Bot（メインGrokBot、グループ、定時ルーチンを含む）のうち、他LLMへ作業を取り次ぐもの。
- **対象外**：
  - 若松さん・社員との会話、コネクタ操作、最終判断、承認の取り次ぎ（Grok に残すもの。正本 `2026-11-15_grok-minimal-multillm.md` §1）。
  - 承認・送信・投稿・購入・削除・本番反映。これらは取り次がない。
  - Muse（`muse-run`）への取り次ぎ（T3 経由の可否が未確認。§4.2）。
- **Codex への取り次ぎは対象外ではない**（2026-11-24 の確認で変更）。T3 経由で `--provider codex --model gpt-6-astra --option effort=low` が動くことを確認したため、Codex も §4.1 の第一候補に含める。直接 `codex exec` はフォールバックとして残す（§4.2）。
- **効き始める条件（3つすべてを満たしたときだけ）**：
  1. box 上の Bot から Rutzbo の T3 に届く経路が確立し、実際に1回以上成功したことが確認できている（§5。**現時点では未確立**）。
  2. 若松さんがこの正本の配布を確認した（**2026-11-24 22:30 JST の承認で充足**）。
  3. 榊 亮介が配布を完了し、2026-11-27 15:19 JST の Grok 週次リセットを過ぎている（**未了**）。
- 上の3条件が揃うまでは、この正本の §4・§6 の運用は開始しない。

## 4. いつ T3 を第一候補にするか／いつ既存の直接 CLI を使うか

### 4.1 T3 を第一候補にする作業（効き始める条件を満たしたあと）

- Claude プロバイダに頼む作業（長文、設計、レビュー）。Claude プロバイダは利用可を確認済み。
- Antigravity プロバイダ（モデル `gemini-4-carbon`、effort low）に頼む作業（公開情報の難しい調査、長文の照合、難しい設計の下書き）。GUI でのサインイン後に利用可を確認済み。
- **Codex プロバイダに頼む作業（コード修正、テスト、差分）。第一候補は `--provider codex --model gpt-6-astra --option effort=low`。**T3 CLI で動くことを 2026-11-24 に確認済み。ただし T3 CLI が拒否するモデルがあるため、下の例外を守る（§4.2）。
- 起動の形（確認済み。AGENTS.md のあるフォルダで実行し、`--provider` と `--model` は必ず一緒に指定する）：

```
~/.local/bin/t3 thread start . --provider <プロバイダ> --model <モデル> --option effort=low --wait "..."
```

- 起動場所の決まりは既存どおり（`2026-11-17_launch-in-agents-md-dir.md`）。T3 CLI も AGENTS.md のあるリポジトリかフォルダに cd してから起動する。使い捨てフォルダでは起動しない。起動前に `test -f AGENTS.md`。

### 4.2 既存の直接 CLI を使う作業（T3 を使わない）

- **Codex は T3（`gpt-6-astra`）が第一候補、直接 `codex exec` がフォールバック。**（2026-11-24 更新。Codex を直接起動だけに限る旧い扱いは取り消した。）
  - 第一候補：`--provider codex --model gpt-6-astra --option effort=low`（T3 CLI で動くことを確認済み）。
  - 直接 `codex exec` に落とすのは次の2つのとき：(a) T3 が使えないとき（稼働確認の失敗、起動の失敗、Rutzbo の停止やログイン切れ）、(b) **T3 が拒否するモデルが必要なとき**。
  - (b) の具体：`gpt-6.2-astra` と `gpt-6.1-sol` は T3 CLI だと 400（ChatGPT アカウントでは未対応）。原因と回避策は未解決。事実の縛りが強い記事の下書きで承認されているモデルは `gpt-6.2-astra`（`approved_offload_patterns.md` の P6）なので、**その作業は直接 `codex exec` のまま**。
- Muse（`muse-run`）への取り次ぎは、T3 経由の可否が未確認のため、当面 `muse-run` のまま。
- `agy` で行っている Google 接地の調べもの・Drive 周りの読み役は、当面 `agy` のまま（正本 `2026-11-15_grok-minimal-multillm.md` の回し先表）。
- 短い判断（1往復で終わるもの）は、どちらにも取り次がない。
- Rutzbo の稼働確認に失敗したとき、または T3 の起動が失敗したときは、必ず既存 box CLI に切り替える（§6）。

### 4.3 渡してよいデータ（既存ルールのまま。変更しない）

- 秘密の値（パスワード・APIキー・トークン・Cookie）は、どの経路にも書かない。1Password の参照だけを書く。
- 顧客名・人事データ（評価・給与・面談）は LLM に渡さない。
- Shelpha のデータそのもの（推計値・推計データ）は原則どのLLMにも出さない。ASIN 単位データについては、**Rutzbo の中だけ**で定められた相手に渡してよいという例外が出ている（正本 `rules/2026-11-23_shelpha-asin-multillm-exception.md`）。チャット・box・ほかのサービスには出さない。例外の終わりは若松さんが宣言する。
- T3 経由で扱えるデータの範囲が、この例外のどこに当たるかは**未決**。§10 の判断事項に回す。確認が取れるまで、T3 には Shelpha のデータそのものを渡さない。

### 4.4 作業×二段（通常使用／高度な検証）のモデル割当（案）

若松さんの指示（2026-11-24）「通常使用と高度な検証でモデルを使い分けるので表にまとめる」に対する案である。**この表の割当そのものは、2026-11-24 22:30 JST の承認（判断事項 1〜14）には含まれない。§10-15 は未決のままである。**

二段の意味：

- **通常使用**＝安く速い側。effort low を既定にする。日常の取り次ぎはこちら。
- **高度な検証**＝最終確認・事実の縛りが強い記事・設計レビュー向け。強いモデル、または high 相当の effort を使う。

書き方の決まり：

- セルに書くのは「**実際に使え、かつ承認済みまたは実機で確認済み**のモデル」だけ。カタログに名前があるだけのモデルは推奨にしない。
- 割当の根拠が弱いところは「（案）」と書き、§10 の判断事項に回す。
- 不明なところは「未割り当て（理由）」と書く。空欄を埋めない。

| 作業 | 通常使用 | 高度な検証 | 起動経路（T3 provider・model） | 出典 |
| --- | --- | --- | --- | --- |
| 調べもの（research。公開情報の調査・照合） | `gemini-4-carbon` effort low | `gemini-4-carbon` の high（**案**。T3 CLI での high 成功は未確認。agy 側の `gemini-4-carbon-high` という名前と、T3 の `--model gemini-4-carbon`＋`effort=high` が同じものを指すかも未確認） | `--provider antigravity --model gemini-4-carbon --option effort=low`（low のみ T3 CLI で確認済み）。T3 が使えないときは `agy` | T3 実機確認（Rutzbo、2026-11-24 19時台 JST、読み取りのみ）／`/workspace/mllm/llm-hub/configs/routing_rules.yaml`（web_research → antigravity_cli、fallback grok）。**`gemini-3.8-flash` と `gemini-4-argon` は使わない**（`/workspace/orgchart/grok_usage_relief/approved_offload_patterns.md` の P6）。routing_rules の `antigravity_cli.default_model`（"Gemini 3.8 Flash"、2026-11-05 時点）は古く、正本が追いついていない |
| 長文・設計・レビュー | `claude-opus-5-5`（effort low は方針。T3 でこの effort を実際に呼んだ記録は「Claude プロバイダ利用可」までで限定的） | 点検も `claude-opus-5-5`。事実の縛りが強い記事の下書きだけ `gpt-6.2-astra`（**T3 不可のため直接 `codex exec`**）→ `claude-opus-5-5` で点検。**`claude-fable-5-2` は高度の既定にしない（承認なし）** | `--provider claudeAgent --model claude-opus-5-5 --option effort=low`。T3 が使えないときは `claude -p`。`gpt-6.2-astra` は T3 を通さず直接 `codex exec` | `approved_offload_patterns.md` の P6（2026-11-18 13:02 承認。事実縛りモデルの `gpt-6.2-astra` への変更は `top2.md` 記載、2026-11-23 05:27）／T3 実機確認（caches/claudeAgent.json に opus-5-5・sonnet-5-5・fable-5-2、effort は low〜ultrathink） |
| コード（修正・テスト・差分） | `gpt-6-astra` effort low | `gpt-6.2-astra`（**直接 `codex exec`**。T3 CLI では 400） | 第一候補 `--provider codex --model gpt-6-astra --option effort=low`（確認済み）。フォールバックは直接 `codex exec` | T3 実機確認（2026-11-24。T3 CLI で成功を確認したのは `gpt-6-astra` のみ。`gpt-6.2-astra` / `gpt-6.1-sol` は 400）／`routing_rules.yaml`（code_generation → codex_cli）／本正本 §4.1・§4.2 |
| 短い判断（1往復で終わるもの） | Jev | 未割り当て（より強いモデルを充てる承認がない。無理に割り当てない） | T3 経路なし（T3 には回さない） | `routing_rules.yaml`（short_judgment → jev）／`/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md`／`approved_offload_patterns.md` の P7・P8（短い判断は Jev） |
| 機密の大量分類・整形（分類・名前の正規化・形式変換） | Ollama `gemma4:26b`（Rutzbo、`127.0.0.1` のみ。temperature 0、JSON、1件ずつ呼ぶ。まとめ呼びするときは出力上限を上げる）。2026-11-24 21:31 JST 若松さん承認（「ollamaを手段に加えて」） | 未決 | **未接続**（T3 には乗せず、Rutzbo の localhost API を直接呼ぶ。T3 に Ollama／カスタム〈OpenAI互換〉プロバイダは未追加） | 試験 39/40・中央値 0.54秒（2026-11-24、`/workspace/orgchart/grok_usage_relief/2026-11-24_ollama-trial.md`）。本番の機密データで使う前に再試験が必要。Shelpha データを渡す承認はない。LM Studio は採用しない（試すときだけ起動。比較：`/workspace/orgchart/grok_usage_relief/2026-11-24_ollama-vs-lmstudio.md`）。`routing_rules.yaml` の `qwen_local` は `enabled: false` のまま（この正本では触らない）／§4.5 |

表に関する注意：

- 上の表は**モデル台帳の代わりではない**。aac（`/workspace/mllm/ai-agent-architecture-comparison`）を `rg 'gemini-4-carbon|claude-opus|gpt-6'` で探しても現行のモデル台帳は見つからなかった。そのため割当の根拠は、上の出典列にある正本・承認ファイルと、2026-11-24 の T3／Ollama 実機確認（読み取りのみ）に限る。
- T3 の Antigravity のモデル一覧には `gemini-4-neon` / `gemini-4-argon` / `gemini-4-hydrogen` / `gemini-3.8-flash` / orchestrator 系 / `gpt-oss-120b-medium` もあるが、**一覧にあること＝承認ではない**ため推奨に置いていない。
- 機密の大量分類・整形の通常使用は、2026-11-24 21:31 JST に若松さんが Ollama を手段として加えることを承認した。以前の「ローカルLLMは今は使わない／未割り当て」という記述は、この行については撤回する。
- 表の割当でよいかは §10 の判断事項。

### 4.5 ローカルLLM（Rutzbo の Ollama）

確認した事実だけを書く。**設定変更の手順は書かない。有効化やプロバイダ追加は、承認後に人が行う。**

- Rutzbo に `ollama` が入っており（`/opt/homebrew/bin/ollama`）、`ollama serve` が動いている。導入済みのモデルは**2つだけ**：`gemma4:26b`（18 GB）と `qwen-slide:latest`（21 GB）。**新しいモデルの pull は不要**（容量は既にある）。
- 待ち受けは **`127.0.0.1:11434` のみ（localhost だけ。外部には公開されていない）**。
- `routing_rules.yaml` では **`qwen_local` は `enabled: false`**（コメント：box 導入は案の確認後）。endpoint は `http://127.0.0.1:11434/v1`。
- **T3 には Ollama プロバイダを追加していない。** T3 のアプリ内文字列には OpenAI / OpenRouter / Anthropic / Ollama / LM Studio / カスタム（OpenAI互換）という種類があり、ポート 11434 や名前に ollama を含む場合を `ollama` 種別として扱う分岐もある。これは「追加できる種類がある」という事実にとどまり、**今は追加されていない。この正本でも追加しない**（若松さんの承認が必要。§10-17 は未決）。
- box からこの Ollama を呼ぶ経路は**未確立**（従来どおり）。使えるのは Rutzbo 上の localhost からだけ。
- `qwen-slide:latest` が公式のどのモデルに当たるかは、`/workspace/orgchart/llm_compare/model_catalog.md`（確認日 2026-11-22）でも未確認。
- 2026-11-24 21:31 JST、若松さんが「ollamaを手段に加えて」と承認した。§4.4 表のとおり、機密の大量分類・整形の**通常使用**は Ollama `gemma4:26b`（Rutzbo、`127.0.0.1` のみ。temperature 0、JSON、1件ずつ。まとめ呼びするときは出力上限を上げる）。**高度な検証は未決。** 起動は T3 **未接続**で、Rutzbo の localhost API を直接呼ぶ（T3 プロバイダは追加しない）。
- 予備試験は 40件中39件正解、1件あたり中央値 0.54秒（2026-11-24、`/workspace/orgchart/grok_usage_relief/2026-11-24_ollama-trial.md`）。使ったのは人名や顧客名を抜いた言い換え依頼文で、Shelpha データは含めていない。**本番の機密データで使う前に再試験が必要。**
- **LM Studio は採用しない。** 普段は Ollama を使い、LM Studio は試すときだけ起動する（比較：`/workspace/orgchart/grok_usage_relief/2026-11-24_ollama-vs-lmstudio.md`）。
- **Shelpha のデータそのものを Ollama に渡してよい、という承認はない。** 2026-11-23 の ASIN 例外が名指ししている相手は `claude -p`（fable を含む）・`codex exec`・`agy` の `gemini-4-carbon-low/medium/high` だけで、**T3 経由と ollama は含まれない**。可否は §10 の判断事項（未決）。

## 5. box 上の Bot が Rutzbo の T3 に届く経路（未確立）

**現時点で、box 上の Bot が Rutzbo のポート 3773 や `~/.local/bin/t3` を直接呼べる経路は確立していない。** 確立しているかのように書かない。読んだBotも、あるものとして扱わない。

事実として分かっていること：

| 項目 | 状態 |
| --- | --- |
| Rutzbo 上の T3 Code（Beta）GUI | 動作する。GUI 自身のサーバはポート 3773（Rutzbo のローカル） |
| T3 CLI（`~/.local/bin/t3`） | Rutzbo 上では上記の形で使える |
| box → Rutzbo の経路 | **未確立・未検証** |
| box → Rutzbo の Ollama | 経路確認（設定変更なし）は実施済み。ただし Ollama は localhost のみ・ポート非公開・`qwen_local` 未有効 |
| Tailscale 経由の案 | 中止済み。box 側プラグイン導入と会社ネット参加、Rutzbo 側 Tailscale 起動、SSH ローカルフォワードは、会社端の Grok Bot が未参加（Cursor Free では会社参加不可）のため実施していない |

### 5.1 経路の試験の進め方（承認済み。開始は配布後、かつ §3 の条件を満たしてから。今は始めない）

1. 経路は新たに作らず、**Rutzbo 上で動くBotだけが T3 を使う**範囲に限って試験する（§10-5、2026-11-24 22:30 JST 承認）。
2. 経路が確認できたら、まず**須藤 航と汐見 遼の2体だけ**で試験する。ほかのBotには広げない。
3. 試験では、取り次ぎ1件ごとに次を記録する：成功／失敗、失敗の理由の1行、使った経路（T3 か既存 CLI か）、所要時間。
4. 1週間の試験のあと、**不合格率**（取り次ぎのやり直しが発生した割合）と**使用量の変化**を、試験前の実測と並べて比べる。数字がないものは「未計測」と書き、作らない。
5. 悪化していなければ、若松さんの確認を取ってから対象Botを広げる。悪化していれば、この正本を取り下げるか書き直す。
6. 試験の開始は、榊 亮介の配布後（2026-11-27 15:19 JST のリセット後）で、§3 の「効き始める条件」を満たしてから。

## 6. 使う前の稼働確認と、失敗時の必須フォールバック

### 6.1 使う前の稼働確認（T3 に取り次ぐ前に毎回）

1. 経路が生きているか（§5 の経路が確立したあと、その経路での到達確認を1回）。
2. T3 の GUI が「This T3 home is unavailable」になっていないか。なっている場合、原因は CLI で別に起動した `t3 serve`（または同等のサーバ）が居ることである。対処は、その余分なサーバの PID を終了すること。**この対処は Rutzbo を操作できる人（または若松さんの承認を得た担当）が行う。Bot が勝手に他のプロセスを落とさない。**
3. 使うプロバイダのサインインが切れていないか（Claude／Antigravity）。切れていたら GUI でのサインインが必要で、これは人の作業になる。
4. 稼働確認が1回で通らなければ、待たずに §6.2 へ移る。ポーリングして待ち続けない。

### 6.2 フォールバック（必須）

- T3 が使えないときは、**必ず**既存の box CLI に切り替えて作業を続ける。作業を止めない。
  - 長文・設計・レビュー → `claude -p`
  - コード・テスト・差分 → `codex exec`（§4.2 のとおり、第一候補は T3 の `gpt-6-astra`。直接 `codex exec` はフォールバック。`gpt-6.2-astra` が必要なときは最初から直接）
  - セカンドオピニオン、Codex 枠が少ないときのコード → `muse-run`
  - Google 接地の調べもの、Drive 周り → `agy`
- 切り替えたら、`progress.md` に1行だけ理由を残す（例：`HH:MM JST | 切替 | T3不通のためclaude -pへ`）。
- 単一マシンのリスクを前提にする：夜間・週末に Rutzbo のログイン切れやサーバ詰まりが起きても、若松さんがすぐ直せないことがある。**T3 が復旧するのを待つのではなく、フォールバックで終わらせる。**
- 若松さんへ T3 の復旧作業を頼むのは、その作業がフォールバックでは終わらないときだけ。夜0〜7時の一斉の問いかけはしない（`rules/2026-11-17_bulk-bot-query.md`）。

## 7. 進捗・停滞の報告（既存ルールに合わせる）

既存の決まりをそのまま使う。ここに手順を書き直さない。正本は `2026-11-16_codex-progress-file.md` と `2026-11-16_no-silent-stall.md`。

- 取り次ぎ先には、区切りごとに `progress.md` へ1行追記させる（形式 `HH:MM JST | 段階 | 一言`、詰まったら `BLOCKED | 理由`、最後に `DONE | 結果の場所`）。T3 経由でもこの一文を指示文に入れる。
- `progress.md` の先頭行に自分のBot名を書く。
- 前面で待ち切れない仕事は Shell ツールのバックグラウンド（`block_until_ms 0`）で起動し、完了通知で起きる。ポーリングしない。`nohup` / `setsid` / `disown` / 末尾 `&` だけで切り離さない。T3 CLI を使う場合も同じ扱いとする（**T3 CLI でこの起こし方が成立するかは未検証。§10 の判断事項**）。
- 完了後は `progress.md` を `tail -3` だけ読む。
- 「進める／送る／登録する」など着手・完了を約束する文は、同じターンで開始呼び出しを出したあとにだけ書く。出せないときは約束せず、未着手と理由を書く。
- 順番作業は1本の起動で `A && B` につなぐ。つなげないときは `NEXT | … | wait_for:DONE | status:pending` を1行書く。
- 報告は SMART の5項目。T3 の出力をそのまま事実として報告しない。確かめていない点は「未確認」と書く。

## 8. やってはいけないこと

1. T3 Connect と Publish を使わない。
2. テレメトリをオンにしない（オフのまま）。
3. Rutzbo の次のものに触らない：agy hooks、launch-guard、Tailscale、ファイアウォール、ポート、ルータ、ログイン項目、`~/work/AI-shelpha`。
4. 「Install managed runtime」を押さない。
5. Antigravity プロバイダの設定で、API キー・GCP プロジェクト・ロケーションを埋めない（空のまま）。binary path は Automatic、instance ID は `antigravity` のまま。
6. 秘密の値（パスワード・APIキー・トークン・Cookie）を、指示文・`progress.md`・この種の文書・ログに書かない。1Password の参照だけ。
7. 顧客名・人事データ（評価・給与・面談）を LLM に渡さない。人事データを社員が見られる場所に置かない。
8. Shelpha のデータそのものを、認められた例外の範囲外へ出さない。チャット・box・ほかのサービスには出さない。
9. 若松さんの承認なしに、送信・投稿・購入・削除・契約・main へのマージ・本番反映をしない。
10. 新しい GitHub リポジトリを作らない。
11. 配布が済むまで、この正本を根拠に他Botへ運用変更を連絡しない。スキルの正本を書き換えない（配布は榊 亮介の作業。§9）。
12. 使ってはいけないフラグ（`--dangerously-skip-permissions`、`--permission-mode bypassPermissions`、`-s danger-full-access`、`muse` の `--yolo` 等）は T3 を使う場合も同じく使わない。
13. Bot が自分の判断で Rutzbo のプロセスを終了させない（§6.1 の `t3 serve` 終了も人の作業）。

## 9. 配布計画

- **配布はまだ済んでいない。** 配布は榊 亮介（Template）の作業である。この正本を今この場で他Botへ送ったり、スキルへ反映したりしない。git commit / push / main マージをしない（`/workspace/knowledge` は git リポジトリではない）。
- 配布の担当：榊 亮介（Template）。
- 配布の条件：
  1. 2026-11-27 15:19 JST の Grok 週次リセットを過ぎている（**未了**）。
  2. 若松さんがこの内容を確認している（**2026-11-24 22:30 JST 承認で充足**）。
- 正本ファイルは `/workspace/knowledge/agents/rules/2026-11-24_t3-harness-relay.md`（`_draft` を外して確定。草案ファイルは残していない）。
- 周知は藤村 秀明（メインGrokBot）。@tw1 への展開を含めて 2026-11-24 22:30 JST に承認済み。
- 配布後も、§3 の「効き始める条件」を満たすまで、T3 第一候補の運用は開始しない。

## 10. 若松さんに決めてもらうこと（1項目1判断）

**1〜14 は 2026-11-24 22:30 JST に若松さんが承認した（すべて草案どおり。@tw1 への展開も承認）。15〜20 は今回の承認に含まれず、未決のままである。**

1. この文書を、全Bot共通ルールとして進めてよいか。→ **承認（2026-11-24 22:30 JST、草案どおり）。正本化した。**
2. 配布を榊 亮介（Template）が行うことでよいか。→ **承認（同日時、草案どおり）。配布は榊。**
3. 周知を藤村 秀明が行うことでよいか。→ **承認（同日時、草案どおり）。@tw1 への展開も承認。**
4. 配布の時期は「2026-11-27 15:19 JST のリセット後かつ確認後」でよいか。→ **承認（同日時、草案どおり）。リセット後に配布。**
5. box → Rutzbo の経路を、どの方法で確立しようとするか（Tailscale 案は中止済み。次の候補の選定を含む）。推奨：まず「経路を作らず、Rutzbo 上で動くBotだけが T3 を使う」範囲に限って試験する。理由：box からの経路は未確立で、確立には会社ネットや端末側の変更が絡み、若松さんの手を要するため。→ **承認（同日時、草案どおり＝推奨のとおり）。経路を作らず Rutzbo 上のBotに限って試験する。**
6. 試験を須藤 航と汐見 遼の2体で始めてよいか。→ **承認（同日時、草案どおり）。2体で開始（開始は §3 の条件を満たしたあと）。**
7. 試験の期間と、広げる判断に使う指標（不合格率・使用量）をこれでよいか。→ **承認（同日時、草案どおり）。1週間、不合格率と使用量で判断。**
8. Codex の取り次ぎを「第一候補は T3 の `--provider codex --model gpt-6-astra --option effort=low`、フォールバックは直接 `codex exec`（T3 が使えないとき、および T3 が拒否するモデルが必要なとき）」としてよいか。推奨：**よい**。理由：`gpt-6-astra` は T3 CLI で動くことを確認済みで、拒否される `gpt-6.2-astra` / `gpt-6.1-sol`（400）は直接起動で回せるため、取り次ぎを止めずに済む。→ **承認（同日時、草案どおり）。**
9. Muse（`muse-run`）を T3 経由にする検討を、今回の範囲に含めるか。推奨：含めない。理由：T3 側の可否が未確認で、論点が増えるため。→ **承認（同日時、草案どおり）。含めない。**
10. T3 に Shelpha のデータそのもの（ASIN 単位データ）を渡してよいか。T3 は Rutzbo 上で動くが、2026-11-23 の例外に挙がっている相手（`claude -p` / `codex exec` / `agy` の指定モデル）に T3 経由が含まれるかは未決。推奨：含めない（渡さない）。理由：例外は相手を名指しで限定しており、拡張は若松さんの宣言が必要なため。→ **承認（同日時、草案どおり）。T3 には Shelpha のデータそのものを渡さない。**
11. T3 の GUI が「This T3 home is unavailable」になったときの余分なサーバ終了を、誰が行うか（Bot には行わせない案でよいか）。→ **承認（同日時、草案どおり）。Bot には行わせない。人の作業。**
12. Rutzbo が夜間・週末に止まったとき、復旧を待たずにフォールバックで終わらせる扱いでよいか。→ **承認（同日時、草案どおり）。復旧を待たずフォールバックで終わらせる。**
13. T3 CLI をバックグラウンド（`block_until_ms 0`）で起こす形が成立するかの検証を、試験に含めてよいか（未検証）。→ **承認（同日時、草案どおり）。試験に含める。成否は依然未検証。**
14. 配布時の正本ファイル名を `rules/2026-11-27_t3-harness-relay.md` とするか、別の名前にするか。→ **承認（同日時）。22:30 JST の正本化指示に従い、正本ファイル名は `/workspace/knowledge/agents/rules/2026-11-24_t3-harness-relay.md` とした（案にあった `2026-11-27_t3-harness-relay.md` は採らない）。**

以下 15〜20 は**未決**（2026-11-24 22:30 JST の承認に含まれない）。

15. §4.4 の二段表（通常使用／高度な検証）の割当でよいか。推奨：このままで試す。理由：承認済みまたは実機確認済みのモデルだけを置き、根拠が弱いところは「案」「未割り当て」にしてあるため。
16. 調べものの「高度な検証」を `gemini-4-carbon` の high にしてよいか。推奨：先に T3 CLI で high の呼び出しが通るかを1回確かめ、通ってから決める。理由：T3 CLI での high 成功が未確認で、agy 側の `gemini-4-carbon-high` との名前の対応も未確認のため。
17. T3 に Ollama またはカスタム（OpenAI互換）プロバイダを足すか。推奨：**今は足さない**。理由：T3 側に種類はあるが未追加で、追加は設定変更に当たり若松さんの承認が必要なため。
18. `routing_rules.yaml` の `qwen_local`（`enabled: false`）を有効化するか。推奨：今は有効化しない。理由：通常使用は Rutzbo の localhost API 直接呼びで足り、`routing_rules.yaml` は触らない方針のため。box からの経路も未確立。
19. Rutzbo の Ollama にある2モデル（`gemma4:26b` / `qwen-slide:latest`）を、どの作業にどう使い分けるか。通常使用（機密の大量分類・整形）は `gemma4:26b` を割り当て済み（2026-11-24 21:31 JST 承認。「ローカルLLMは今は使わない」は撤回）。`qwen-slide:latest` と高度な検証は未決のまま。理由：`qwen-slide` の公式モデルIDとの対応が未確認で、高度な検証の割当承認もないため。新しい pull は不要。
20. Shelpha のデータそのもの（ASIN 単位データ）を Rutzbo の Ollama に渡してよいか。推奨：**渡さない**。理由：2026-11-23 の例外は相手を名指しで限定しており（`claude -p` / `codex exec` / `agy` の指定モデル）、ollama は含まれていないため。拡張は若松さんの宣言が必要。

## 11. 用語一覧（言葉／意味／出典）

| 言葉 | 意味 | 出典 |
| --- | --- | --- |
| T3 Code（Beta） | Rutzbo 上で動いている開発支援ツール。GUI とコマンド（`~/.local/bin/t3`）を持ち、プロバイダとモデルを指定してスレッドを開始できる。GUI 自身のサーバはポート 3773 | **公式では確認できなかった**（この文書はネット検索をしていない）。ここに書いた意味は、Rutzbo 上で確認された挙動の範囲にとどめている |
| 「ハーネス込み」 | 若松さんの発言にある言い方。公式の名称としては確認できなかったため、見出し語として使わない。この正本では「取り次ぎ先の実行環境（GUI・プロバイダの認証状態・CLI）をそのまま残したまま作業を取り次ぐこと」の意味で扱う | 若松さんの発言（2026-11-24）。製品用語としては**公式では確認できなかった** |
| Antigravity（プロバイダ名） | T3 の GUI の Providers 一覧に表示されるプロバイダの1つ。モデル `gemini-4-carbon`、effort low で利用可を確認済み。instance ID は `antigravity` | T3 の GUI 画面表示（Rutzbo）。公式ドキュメントは**未確認** |
| `--provider` / `--model` / `--option effort=low` | T3 のコマンドに渡す指定。`--provider` と `--model` は必ず一緒に指定する | Rutzbo 上で確認済みのコマンド形。公式ドキュメントは**未確認** |
| `gpt-6-astra` | T3 の Codex プロバイダのモデル名（slug）。T3 CLI 経由で動くことを確認した唯一の Codex モデル。この正本ではコードの通常使用に置く | Rutzbo 上の T3 実機確認（2026-11-24、caches/codex.json と CLI 起動）。公式ドメインでは**確認できなかった**（この文書はネット検索をしていない）。社内正本：本ファイル §4.1・§4.4 |
| `gpt-6.2-astra` | Codex のモデル名。事実の縛りが強い記事の下書きに承認されている。**T3 CLI では 400 になるため、直接 `codex exec` で使う** | `/workspace/orgchart/grok_usage_relief/approved_offload_patterns.md` の P6（2026-11-18 13:02 承認、モデル変更は `top2.md` 2026-11-23 05:27）。400 の事実は Rutzbo 上の T3 実機確認（2026-11-24）。公式ドメインでは**確認できなかった** |
| Ollama | ローカルの機械の中でモデルを動かすための実行環境。Rutzbo に入っており、`127.0.0.1:11434` でだけ待ち受ける（外部非公開）。導入済みは `gemma4:26b` と `qwen-slide:latest` の2つ | Rutzbo 上の実機確認（2026-11-24、読み取りのみ。§4.5）。公式ドメインでは**確認していない**（ネット検索をしていないため）。社内正本：`/workspace/mllm/llm-hub/configs/routing_rules.yaml`（endpoint `http://127.0.0.1:11434/v1`） |
| `qwen_local` | `routing_rules.yaml` に書かれたローカルモデルの回し先の名前。機密の大量分類・名前の正規化・形式変換の第一候補だが、**`enabled: false`（未有効）**。有効化は承認後 | `/workspace/mllm/llm-hub/configs/routing_rules.yaml`（最終コミット 2026-11-05、ブランチ feat/usage-reporting-shadow-roles）／`/workspace/orgchart/grok_usage_relief/approved_offload_patterns.md` 用語一覧「ローカルQwen」（未有効のため対象外） |
| 通常使用 / 高度な検証 | 若松さんの指示（2026-11-24）にある2段の使い分け。**通常使用**＝安く速い側、effort low を既定にする日常の取り次ぎ。**高度な検証**＝最終確認・事実の縛りが強い記事・設計レビュー向けの、強いモデルまたは high 相当の effort | 若松さんの発言（2026-11-24）。製品用語ではないため公式では**確認できない**。社内正本：本ファイル §4.4 |
| 「This T3 home is unavailable」 | T3 の GUI に出る表示。CLI で別に起動した `t3 serve`（または同等のサーバ）が居るときに出る。対処はその余分なサーバの PID を終了すること | Rutzbo 上で確認した事象。公式の説明は**未確認** |
| T3 Connect / Publish | T3 の機能名。この正本では使わないと決めている | T3 の GUI 画面表示（Rutzbo）。機能の中身は**未確認**。使わないため確認もしない |
| Rutzbo | 社内の Mac mini（machineId <machine-id>）。T3 Code の GUI が動いている機体 | 社内の呼び名。`/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md`（Shelpha 推計を rutzbo 内だけで扱う旨の記述） |
| 取り次ぎ（Handoff） | Bot が自分で作業せず、ほかのLLMに作業を渡すこと。回し先の選び方と渡してよいデータの線引きが定められている | `/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md`、`/workspace/knowledge/agents/rules/2026-11-14_handoff-by-file.md` |
| `progress.md` | 取り次ぎ先が区切りごとに1行追記する進捗ファイル。先頭行に元のBot名を書く | `/workspace/knowledge/agents/rules/2026-11-16_codex-progress-file.md`、`/workspace/knowledge/agents/rules/2026-11-16_no-silent-stall.md` |
| `block_until_ms 0` | Shell ツールのバックグラウンド起動。完了通知で Bot が起きる。切り離し（`nohup` 等）は禁止 | `/workspace/knowledge/agents/rules/2026-11-16_no-silent-stall.md` 第2節 |
| フォールバック | 第一候補が使えないときに切り替える別の経路。この正本では既存 box CLI（`claude -p` / `codex exec` / `muse-run` / `agy`）を指す | `/workspace/knowledge/agents/AGENTS.md`（c）、`/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md` 回し先表 |
| `agy` | box 上で Gemini 系モデルを呼ぶために使っているコマンド。法人アカウント用と個人アカウント用で HOME を分けている | `/workspace/knowledge/agents/rules/2026-11-15_grok-minimal-multillm.md` 回し先表 |
| Shelpha | 社内のデータ元の呼び名。データそのもの（推計値・推計データ）の取り扱いに制限がある | `/workspace/knowledge/agents/AGENTS.md`（d）、`/workspace/knowledge/agents/rules/2026-11-23_shelpha-asin-multillm-exception.md` |
| GMV | 全Botの仕事がつながる北極星の指標（目標 800億円） | `/workspace/knowledge/agents/AGENTS.md`（a） |

## 人が確かめること

- **用語の出典**：製品側の用語（T3 Code、Antigravity プロバイダ、T3 Connect / Publish、GUI の表示文）に公式 URL を付けられていない。この文書ではネット検索を行わず、推測の URL を書かない方針を取り、該当箇所に「公式では確認できなかった」「未確認」と明記した。**公式ドメインでの確認は人（または検索を許された取り次ぎ）が行う必要がある。**
- **「ハーネス込み」**：公式名称として確認できなかったため、見出し語にしていない。§11 で中身（実行環境を残したまま取り次ぐこと）として説明した。この解釈が若松さんの意図と合っているかは、§10-1 の承認（2026-11-24 22:30 JST、草案どおり）に含まれる扱いとした。用語そのものの公式確認は依然として残る。
- **未確立の経路**：box → Rutzbo の T3 経路は §3・§5・§11 で一貫して「未確立・未検証」と書いた。確立済みと読める箇所は入れていない。Tailscale 案が中止済みであることも明記した。
- **配布・起動の指示をしていないか**：この文書は配布・連絡・設定変更・Rutzbo への接続・T3 の起動やログインを指示していない。§1・§3・§9 で「配布は榊 亮介の作業で、まだ済んでいない」「効き始める条件を満たすまで開始しない」と明記した。配布は 2026-11-27 15:19 JST のリセット後。実作業（経路の確立、試験の開始、配布）は、この正本を配ったあとに始まる。
- **Codex の扱いを 2026-11-24 に変更した**：Codex を直接起動だけに限る旧い扱いは取り消し、第一候補を T3 の `--provider codex --model gpt-6-astra --option effort=low`、フォールバックを直接 `codex exec` に直した（§3・§4.1・§4.2・§4.4・§6.2・§10-8・§11）。T3 CLI で成功を確認したのは `gpt-6-astra` のみで、`gpt-6.2-astra` と `gpt-6.1-sol` は 400 のままである。**他の Codex モデルが T3 CLI で通るかは未確認**。人が確かめる余地がある。
- **二段表（§4.4）の弱いところ**：①`gemini-4-carbon` の **high を T3 CLI で呼べたかは未確認**（確認済みは low のみ）。②agy 側の `gemini-4-carbon-high` という名前と、T3 の `--model gemini-4-carbon`＋`effort=high` が同じものを指すかは**未確認**。③T3 の Claude プロバイダで `claude-opus-5-5` を**どの effort で実際に呼んだかの記録は限定的**（「Claude プロバイダ利用可」まで）。④短い判断の「高度な検証」は**未割り当て**、機密の大量分類・整形の「高度な検証」は**未決**のままにした（通常使用の `gemma4:26b` は 2026-11-24 21:31 JST に承認）。
- **モデル台帳がない**：aac を `rg 'gemini-4-carbon|claude-opus|gpt-6'` で探しても現行のモデル台帳は見つからなかった。表の根拠は正本・承認ファイルと 2026-11-24 の実機確認だけで、**台帳との突き合わせは未実施**。`/workspace/orgchart/llm_compare/model_catalog.md`（確認日 2026-11-22）は一部が実機より古い。
- **正本が追いついていない箇所**：`routing_rules.yaml` の `antigravity_cli.default_model` は 2026-11-05 時点で "Gemini 3.8 Flash" のままだが、`gemini-3.8-flash` と `gemini-4-argon` を公開版に使わないことは P6 で承認済みである。表には 3.8 / argon を置いていない。**正本の更新が必要かは人の判断**。
- **ローカルLLM（§4.5）**：2026-11-24 21:31 JST に、機密の大量分類・整形の通常使用へ Ollama `gemma4:26b`（`127.0.0.1` のみ）を加えることが承認された。「ローカルLLMは今は使わない」は撤回。呼び出しは localhost API 直接で、T3 は未接続（プロバイダ未追加）。`qwen_local` は未有効のまま（`routing_rules.yaml` は触らない）。高度な検証と `qwen-slide:latest` の割当は未決。LM Studio は採用しない（試すときだけ起動）。本番の機密データで使う前に再試験が必要。Shelpha データを渡す承認はない。
- **Shelpha データの線引き**：2026-11-23 の ASIN 例外が名指ししている相手に **T3 経由と ollama は含まれない**。表・本文のどこにも「Shelpha を ollama や T3 に回してよい」とは書いていない。T3 へ渡さないことは §10-10 として 2026-11-24 22:30 JST に承認済み（§4.3）。ollama へ渡してよいか（§10-20）は未決で、未決のまま渡さない（§4.5）。例外の拡張は若松さんの宣言が必要。
- **用語の出典**：`gpt-6-astra`・`gpt-6.2-astra`・Ollama・通常使用／高度な検証は、公式ドメインでの確認ができていない（この文書はネット検索をしていない）。§11 に「公式では確認できなかった」と書き、社内正本のパスを付けた。**公式確認は人（または検索を許された取り次ぎ）が行う必要がある。**
- **残る未決**：§10 の 15〜20（二段表の割当、`gemini-4-carbon` high、Ollama プロバイダ追加、`qwen_local` 有効化、`qwen-slide` と高度な検証、ollama への Shelpha データ）。1〜14 は 2026-11-24 22:30 JST に承認済み。15〜20 は今回の承認に含まれないので、承認済みとして扱わない。13 で承認されたのは「検証を試験に含めること」で、T3 CLI のバックグラウンド起動が成立するかは依然未検証である。
- **この更新でしていないこと**：配布、他Botへの連絡、git commit / push（`/workspace/knowledge` は git リポジトリではない）、設定変更、Rutzbo への書き込み、T3 へのプロバイダ追加、`routing_rules.yaml` の変更。いずれも行っていない。正本化（`_draft` を外す改名）と本文の承認反映だけを行った。

---

使用LLM：Claude Code（Opus 5）。起案は汐見 遼。

## T3の利用状況送信への対策（必須条件）

根拠: `projects/t3-telemetry-check/findings.md`（2026-11-25 検証）。T3の商品利用イベントは既定オンで、既定の受け口は `https://ingest.t3.codes`、送信は10秒周期のバッチ。

T3を第一候補にできるのは、下の3つがすべて揃った端末に限る。1つでも欠けていれば、T3は第一候補にせず、boxのCLIを使う。

### 必須1: 環境変数2つを、シェル設定とLaunchAgentの両方に入れる

| 変数 | 値 |
|---|---|
| `T3CODE_TELEMETRY_ENABLED` | `false` |
| `T3CODE_OTEL_SDK_DISABLED` | `true` |

- 入れる場所は2経路とも必須。シェル設定（`~/.zshrc` と `~/.zprofile`）と、LaunchAgent から `launchctl setenv <変数名> <値>` を RunAtLoad で実行する。
- 片方だけでは穴が残る。シェル設定だけだと、シェルを経由せず起動したアプリに効かない。LaunchAgentだけだと、plistが読まれる前の起動に効かない。
- 確認: `launchctl getenv T3CODE_TELEMETRY_ENABLED` と `launchctl getenv T3CODE_OTEL_SDK_DISABLED` が期待値を返し、稼働中のT3プロセス全部の環境に両方が入っていること。
- 効く範囲: 商品利用イベントの送信、relay tracing、OTLP export が止まる。Identifyのローカル読み取りは止まらない（必須3で対処する）。

### 必須2: /etc/hosts で受け口を 0.0.0.0 に向ける

`/etc/hosts` に次の1行を入れる。

```
0.0.0.0 ingest.t3.codes
```

環境変数が落ちた・読まれなかったときの網。これもIdentifyのローカル読み取りは止めない。

### 必須3: PR #42299 以降を含む版だけを使う

- T3のバージョンは、ホームの認証ファイル（`~/.codex/auth.json`、`~/.claude.json`）を読む処理を廃止した PR #42299（2026-11-25 マージ）以降を含む版に限る。https://github.com/pingdotgg/t3code/pull/42299
- それ以前の版（たとえば 0.1.11）は、送信をオフにしていても起動のたびにこれらのファイルを読む処理が残っている。
- 確認: 入れた版が #42299 を含むこと。含まない版は必須3を満たさない。

### 3つが揃うまでの運用

- T3は第一候補にしない。boxのCLIを使う。
- hosted web は使わない。server側の環境変数では止まらない。
