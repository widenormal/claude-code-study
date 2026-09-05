# シークレット集中管理（1Password Service Account）— CI / ローカル共通

複数リポジトリ + ローカル（Mac / Google Drive 同期フォルダを含む）を横断して、
シークレットを **1Password を単一の真実源**に集中管理し、CI とローカルで**同一の参照定義**を使い回す仕組み。

設計は Codex（GPT-5）の 3 回のセキュリティレビューを通し、最終 **Go（条件付き）** を満たす形にしている。

## 全体像

```
ci/secrets/secrets.map        論理ENV名 → 1Password item title / field（非 secret・単一ソース）
        │
        ▼  scripts/gen-env-ref.sh（op item get で title→item ID を解決）
op:// ID 参照テンプレ（非 secret。解決済みの secret 値は含まない）
        │
        ▼  scripts/op-run.sh → op run --env-file
子プロセスの env に **メモリ注入のみ**（平文 .env をディスクに残さない）
```

- **真実源**: 1Password vault `claude-code-secrets`。値はここだけに存在する。
- **認証**: `OP_SERVICE_ACCOUNT_TOKEN`。CI は GitHub Actions Secrets、ローカルは env / launchd 経由。
  個人アカウント（デスクトップアプリ＋生体認証）経路は ssh / cron / バックグラウンドでは使えない
  → 「[対話環境と非対話環境の違い](#対話環境と非対話環境の違い重要)」節。
- **参照は item ID**: R7 のとおり item title に括弧 `(` があると `op read`/`op run` が
  `invalid character` で失敗する。そこで人間は title で書き、生成器が **一意な item ID** に解決する。

## ファイル

| パス | 役割 | 追跡 |
|---|---|---|
| `ci/secrets/secrets.map` | 論理名 \| item title（括弧可）\| field の単一ソース | ✅ git 追跡 |
| `scripts/gen-env-ref.sh` | map → op:// ID 参照テンプレ生成（secret 値なし） | ✅ |
| `scripts/op-run.sh` | 参照を `op run` でメモリ注入してコマンド実行 | ✅ |
| `.github/workflows/op-secrets.yml` | reusable CI ワークフロー（git リポのみ） | ✅ |
| 生成物（`op-ref.*` / `.env`） | 一時。`.gitignore` 済 | ❌ 絶対コミット禁止 |

## 使い方

### ローカル

```bash
# OP_SERVICE_ACCOUNT_TOKEN が env にある前提（無ければ .claude/scripts/setup-op.sh が bootstrap）
bash scripts/op-run.sh -- python app.py
bash scripts/op-run.sh -- bash -c './task.sh'
```

`op-run.sh` は ID 参照テンプレを `$TMPDIR` に `chmod 600` で一時生成し、`trap` で必ず削除する。
**解決済み secret はディスクに書かない**（`op inject -o .env` は使わない）。

### CI（GitHub Actions, 案2）

1. 対象リポの Actions secret に `OP_SERVICE_ACCOUNT_TOKEN` を登録。
2. 呼び出し:

```yaml
jobs:
  task:
    uses: ./.github/workflows/op-secrets.yml
    with:
      run: python app.py     # env から各キー参照。値は絶対 stdout に出さない
    secrets:
      OP_SERVICE_ACCOUNT_TOKEN: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
```

ワークフローは GitHub の自動マスクに加え、各 secret 値を `::add-mask::` で**二重マスク**する。

## secrets.map の追加・変更

```
# 論理名            | item title              | field
GEMINI_API_KEY      | Gemini API Key (Template) | credential
```

- field は通常 `credential`（CONCEALED）。**op は field を id でも label でも解決する**ため、
  生成器も id/label 両方で照合する（例: Grok item はキーが `label=credential` のフィールドにある）。
- **item title を変更/再作成したら `gen-env-ref.sh` を再実行**すれば新しい ID に自動追従する
  （ID を手書きしないので、再作成で ID が変わっても map は壊れない）。
- field 未投入の item は既定で **warn + skip**。CI で厳格にしたい場合は `--strict` で fail。

## 運用ルール（必読）

### Drive 同期フォルダ

- **Drive 同期フォルダ配下で op-run / 生成を実行しない**。秘匿構成情報・op キャッシュ・一時ファイルが
  Drive のバックアップ/索引に拡散する。
- secret 本体・op キャッシュ・生成物は **`$HOME` 配下（同期対象外）に固定**する
  （既存 `setup-op.sh` が `~/.search-api-env` 等 `$HOME` に書くのと同方針）。
- 非 git 作業環境（Drive フォルダ等）では `.github/workflows/op-secrets.yml` は機能しない。
  R8 のとおり `scripts/strip-non-git.sh` で除去される。

### 対話環境と非対話環境の違い（重要）

op CLI には認証経路が2つある。**どちらを使っているかで、非対話環境での挙動が変わる。**

| 経路 | 認証 | 対話ターミナル | ssh / cron / launchd / バックグラウンド |
|---|---|---|---|
| 個人アカウント（デスクトップアプリ連携） | 生体認証・マスターパスワード | ✅ 動く | ❌ **承認ダイアログを押せずハング／authorization timeout** |
| **サービスアカウント（`OP_SERVICE_ACCOUNT_TOKEN`）** | トークン | ✅ 動く | ✅ **動く** |

**非対話で op を叩く環境には、必ずサービスアカウントトークンを配ること。**
共有 Mac・CI・夜間バッチ・エージェントのバックグラウンドジョブがこれに該当する。

トークンがあれば `.claude/scripts/setup-op.sh` が op CLI の導入からキーの永続化まで自動で行う
（トークンが無ければ黙って `exit 0` する設計なので、未配布の環境では何も起きない）。
サービスアカウント使用時は `OP_ACCOUNT` の指定は不要。

#### 症状と切り分け

| 症状 | 原因 |
|---|---|
| `op whoami` → `account is not signed in` かつ `${#OP_SERVICE_ACCOUNT_TOKEN}` が 0 | トークン未配布。個人アカウント経路にフォールバックしている |
| `op read` が無反応のまま数十秒経過 | 承認ダイアログが出ているが、押せる人がいない |
| `authorization timeout` | 同上（タイムアウトした） |
| キーは設定されているのに API が 401 | 下記の「失敗の握りつぶし」 |

実測（2026-09-04〜05・共有 Mac）＝ssh 越しの `op whoami` は `account is not signed in`、
`echo ${#OP_SERVICE_ACCOUNT_TOKEN}` は `0`、`op read` は16秒待って応答なし（強制終了するまでハング）。
人が Touch ID を押すと成功する＝**手順の誤りではなく認証経路の選択**が原因。

#### 失敗の握りつぶしを避ける

次の書き方はエラーを捨てるため、認証が通らないと**空文字が入るだけで気づけない**。

```bash
# 悪い例：401 の原因が分からなくなる
export SOME_API_KEY="$(op read 'op://vault/item/credential' 2>/dev/null)"
```

シェルの起動ファイルで `op read` を直接呼ぶのも避ける。承認待ちでシェル自体が固まる。
キーが要るコマンドだけ `scripts/op-run.sh` 経由で実行するか、`setup-op.sh` に任せる。

```bash
bash scripts/op-run.sh -- python3 my_task.py
```

### ローテーション / 失効

1. 1Password 側でキーを更新（item は再作成せず**同じ item の field を更新**するのが楽）。
2. item を作り直した場合のみ `gen-env-ref.sh` を再実行（ID 追従）。
3. CI が認証エラーで落ちたら: `op whoami` → vault 列挙 → 該当 item の field 確認（R7 の 3 段階）。

### 監査

- 「誰がいつどの item を読んだか」は 1Password の Service Account アクティビティログで追跡。
- `secrets.map` の変更は PR レビュー必須（どのキーが参照されるかの構成情報のため）。

## 既知の外部要因（実装不具合ではない）

- **Grok / xAI が 403**: vault の鍵自体は有効（`api_key_blocked=false`）。原因は
  **xAI チームのクレジット枯渇 / 月次上限到達**（`team_blocked=true`）。
  診断: `curl https://api.x.ai/v1/api-key -H "Authorization: Bearer <key>"` の本文を見る。
  対処は console.x.ai での課金であり、キーのローテーションでは直らない。
- **MiniMax**: vault item に `credential` 未投入（`api_base`/`model_name` のみ）。
  キーを登録するまで生成器は skip する。

## 残課題（次フェーズ）

- **CI / ローカルで Service Account を分離**（現状は単一 SA。リスク受容済み: 漏洩時の爆発半径は
  vault 全体。最小権限 vault への分割と SA 分離を次フェーズで実施）。
- **OIDC / 短命認証**: 1Password Service Account での可否は未確認。可能なら固定トークンより優先。
