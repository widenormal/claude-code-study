# CI 正本一元化 ＋ セッション・ブートストラップ

> 目的: ドリフト防止。全社員がどの作業環境からでも**完全に同一の CI テンプレ**で
> スライド制作・データ分析を行える。正本は1箇所。各セッション起動時にラッパーが
> 「正本取得」＋「SA トークン読込」を自動実行する。

## 核心原則（反ドリフト）

**コピーを各フォルダに置かない。各セッションが起動時に「一箇所の正本」を pull/参照する。**
（実例: NatureLab デッキが正本 `--powder/--navy` から `--crystal/--ink`+φ へ分岐し、
正本未反映のまま「最新」と誤認された。コピーは必ずドリフトする。）

## 確定した設計

| 項目 | 決定 |
|---|---|
| 正本ストア | git リポ **`5co-hub/template` の `5co-CI-kit/`**（既存 sync 経路を流用） |
| 認証 | **fine-grained read-only PAT**（Contents: Read・対象 template）／op に1つ保管 |
| 社員 GitHub アカウント | **不要**（PAT を op から取得して pull） |
| ドリフト照合 | **警告のみ**（block しない・作業を止めない） |
| 秘密の置き場 | PAT・SA トークンは**端末ローカル**（共有フォルダに置かない） |

## 部品

| 部品 | 役割 |
|---|---|
| `CI_SOURCE.md` | 正本ポインタ（最初に読む MD）。正本の場所・フォーク禁止・CI ルール参照 |
| `scripts/ci-canonical-sync.sh` | SessionStart で実行。op→PAT→正本 pull→固定パス配置→ドリフト照合→CI ルール注入 |
| SessionStart 登録 | `.claude/settings.json` の SessionStart に追加（`setup-op.sh` の後＝op 準備済み） |
| SA トークン | 端末ローカルの `OP_SERVICE_ACCOUNT_TOKEN`（sa-common）。op を有効化 |

## SessionStart ラッパーの動作（`ci-canonical-sync.sh`）

1. op CLI / `OP_SERVICE_ACCOUNT_TOKEN` を確認（無ければ警告して skip・セッションは止めない）。
2. op から fine-grained read-only PAT を取得（item `GitHub PAT (CI canonical read)`）。
   欠落時は「PAT を発行して op に投入」する手順を出して skip。
3. 正本 `5co-hub/template:5co-CI-kit` を shallow + sparse で固定パス（`~/.cache/5co-CI-canonical`）へ取得。
   認証情報は remote URL に残さない（取得後に素の URL へ戻す）。
4. 正本と作業環境ローカル `5co-CI-kit/` のハッシュを照合し、不一致なら**ドリフト警告**（block しない）。
5. `CI_KICKOFF.md` 必読のルールを additionalContext に注入（テンプレ複製・3色・検査必須）。

### env で上書き可能な設定
`CI_CANON_PAT_ITEM` / `CI_CANON_REPO` / `CI_CANON_SUBDIR` / `CI_CANON_BRANCH` /
`CI_CANON_CACHE` / `CI_CANON_LOCAL_KIT` / `CI_CANON_VAULT`。

## セキュリティ整合（SA 設計と一致）

- PAT は広い `GitHub PAT (Template)`（scope=repo・書込可）を**使わない**。CI 正本 read 専用の
  **fine-grained read-only PAT** を別 op アイテムにし、最小権限にする。
- PAT・SA トークンは共有 Drive フォルダに置かない（端末ローカル）。
  ＝「機密の置き場＝誰が触れるか」（web env / 共有フォルダ＝編集できる人＝全員）。

## 導入の前提（運用側で実施）

1. GitHub で **fine-grained・read-only（Contents: Read / 対象 `5co-hub/template`）の PAT** を発行。
2. 1Password vault `claude-code-secrets` の item **`GitHub PAT (CI canonical read)`**（field `credential`）へ投入。
3. 各社員端末のローカル設定に `OP_SERVICE_ACCOUNT_TOKEN`（sa-common）を設定。
4. template をマージ後 `sync-derived-repos.sh` で派生リポへ伝播。

## 未検証（PAT 投入後に要・実機確認）

- 正本 pull（PAT 認証）と sparse-checkout の成否。
- ドリフト照合の実挙動（正本 vs ローカルの不一致警告）。
- ※ 現状は「op/PAT 欠落時の graceful skip」「ハッシュ計算」「additionalContext 出力」のみ検証済み。

## 共用作業箱のローカル正本キャッシュ（`scripts/ci-canonical-cache/`・2026-10-30）

op／PAT を使わない共用作業箱（エージェントの作業用 Linux 箱・`gh` 認証済み）では、`/workspace/.5co-CI-canonical/` に
`ensure.sh`・`sync.sh` を置き、作業前に `bash /workspace/.5co-CI-canonical/ensure.sh` を実行して kit を使う
（`/workspace/5co-CI-kit` はそこへのリンク）。本リポの `scripts/ci-canonical-cache/` がその2本の正本。

- **事故（2026-10-30）**: キャッシュが v3.11 のまま、main は v3.12.4 まで進んでいた。旧 `ensure.sh` は
  `VERSION` が**無いとき**しか同期せず、crontab も無かったため、一度入ったキャッシュは二度と更新されなかった。
- **修正**: `ensure.sh` が毎回 `git ls-remote`（短いタイムアウト・既定 8 秒・`CI_CANON_CHECK_TIMEOUT`）で main の commit を見て、
  `5co-CI-kit/.synced_from` の記録と違えば `sync.sh` を呼ぶ。旧形式の記録（短縮 commit）も前方一致で比べる。
- **軽さ**: `sync.sh` は blob を取らずに clone し、`5co-CI-kit` のツリーが前回と同じなら中身は取り直さず記録だけ更新する
  （main の別ディレクトリだけが進んだとき）。記録＝`<commit 40桁> <時刻> tree=<5co-CI-kit の tree>`。
- **fail-open**: オフライン・認証切れ・タイムアウトで main を確認できない／同期や検証に失敗したときは、キャッシュがあれば
  警告（stderr）して既存の版で続ける（終了コード 0）。キャッシュが無く同期もできないときだけ 1。新しい版は検証が済むまで今のコピーを消さない。
- **入れ替え方**: `cp scripts/ci-canonical-cache/{ensure,sync}.sh /workspace/.5co-CI-canonical/`（どちらも単体で動く）。
- **テスト**: `bash tests/ci-canonical-cache.test.sh`（file:// のローカル bare リポを main に見立てる・ネットワーク不要）。
