# ①全Bot共通層（Template 管理の写し）

若松さん決定（2026-11-16 17:22 JST）：全Bot共通の層は Template のリポジトリで管理する。

- このフォルダは box 上の `/workspace/knowledge/agents/` にある承認済みファイルの**写し**である。原本は削除も移動もしていない。
- 派生リポへは Sync Template（`docs/agents/` を `TEMPLATE_DIRS` として配布）で届く。この変更の投入だけでは Sync は走らない。
- 派生リポでの経路：`docs/agents/AGENTS.md` と `docs/agents/rules/`。
- box 上の Template クローンで読む経路：`/workspace/template/docs/agents/`（クローンの場所が違うときは `<clone>/docs/agents/`）。
- バックアップ（`*.bak*` / `*.orig*`）、未承認の案、秘密・推計実データ・人事の中身・顧客名／仕入れ先名／幹部のみの情報を含むファイルは入れていない。
