#!/usr/bin/env python3
"""
ci_paths.py — kit（5co-CI-kit）の場所解決の唯一の標準方式

案件スクリプト（はみ出し検査・parity 検査・ビルダー等）が、kit（5co-CI-kit）への
パスを **`parents[N]` のような階層決め打ちにせず** 解決するための共有ヘルパ。

なぜ存在するか（2026-09-09 B-12・parents[5] 誤り事故）:
  ある案件スクリプトが `ROOT = HERE.parents[5]` で kit の位置を決め打ちしていたが、
  実際の階層と1つずれていた。その結果 kit 内のファイルが見つからず、はみ出し検査
  （slide_overflow_check.py）が **例外も出さずに「実行されず成功扱い」** になり、
  検査をすり抜けた不備が本番に残った。「kit が見つからない」は握りつぶしてよい状態
  ではなく、その場で構築を止めるべき事故である。

設計原則:
  - **fail-closed**。kit（`5co-CI-kit/VERSION`）が見つからなければ検査・生成を
    黙ってスキップさせず、`SystemExit` で明示的に落とす。
  - 階層数を決め打ちしない。呼び出し元の位置から親ディレクトリを1段ずつ遡り、
    `5co-CI-kit/VERSION` を持つ最初のディレクトリを kit と認定する（案件の
    フォルダ構成が変わっても追従する）。
  - 依存は標準ライブラリのみ（案件側の環境を問わず使える）。

使い方（案件ビルダー側）:
  # ci_paths.py 自体は kit の中にあるので、案件スクリプトは最初の1回だけ自力で kit を探す。
  # 「スクリプト自身の場所」を起点に遡る（cwd 起点にしない＝どこから実行しても同じ結果）。
  import sys, pathlib
  _here = pathlib.Path(__file__).resolve()
  _kit = next(d / "5co-CI-kit" for d in (_here, *_here.parents) if (d / "5co-CI-kit" / "VERSION").is_file())
  sys.path.insert(0, str(_kit))
  from ci_paths import add_to_sys_path
  kit = add_to_sys_path(__file__)   # 以後の解決はこれ1本（見つからなければ SystemExit・黙ってスキップしない）
  import ci_head                    # これで import 可能になる

  # kit のパスだけ欲しい場合
  from ci_paths import find_kit
  kit_dir = find_kit(__file__)      # 起点はスクリプト自身。省略時は cwd（対話用・ビルダーでは省略しない）

  # subprocess / シェルから
  python3 5co-CI-kit/ci_paths.py            # 見つかった kit の絶対パスを1行出力（exit 0）
  python3 5co-CI-kit/ci_paths.py --selftest # 自己診断（見つかる/見つからない の両ケース）

終了コード: 0=成功 / 1=kit（5co-CI-kit/VERSION）不在（fail-closed: 見つからないまま
黙って検査をスキップさせない）
"""
import sys
import tempfile
from pathlib import Path

KIT_DIRNAME = "5co-CI-kit"
VERSION_FILENAME = "VERSION"


def find_kit(start=None):
    """start（既定＝呼び出し元の cwd）から親ディレクトリを順に遡り、
    <dir>/5co-CI-kit/VERSION が存在する最初の <dir>/5co-CI-kit を返す。

    start 自身が 5co-CI-kit ディレクトリ（VERSION を持つ）ならそれをそのまま返す。
    見つからなければ SystemExit で落とす（黙ってスキップしない・fail-closed）。
    """
    start_path = Path(start).resolve() if start is not None else Path.cwd().resolve()

    # start 自身が 5co-CI-kit ディレクトリの場合
    if start_path.name == KIT_DIRNAME and (start_path / VERSION_FILENAME).is_file():
        return start_path

    # start 自身 → 親へ順に遡って探索
    for directory in [start_path, *start_path.parents]:
        candidate = directory / KIT_DIRNAME
        if (candidate / VERSION_FILENAME).is_file():
            return candidate

    raise SystemExit(
        "NG: 5co-CI-kit/VERSION が見つかりません（探索開始: {}）。"
        "案件スクリプトは kit を見つけられないときに検査を黙ってスキップしてはいけない".format(
            start_path
        )
    )


def add_to_sys_path(start=None):
    """find_kit() の結果を sys.path の先頭に入れて返す（import ci_head 等が使えるように）。"""
    kit = find_kit(start)
    kit_str = str(kit)
    if kit_str in sys.path:
        sys.path.remove(kit_str)
    sys.path.insert(0, kit_str)
    return kit


def _selftest():
    # ケース1: 深い階層から見つかる
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        kit_dir = root / KIT_DIRNAME
        kit_dir.mkdir()
        (kit_dir / VERSION_FILENAME).write_text("v0.0-selftest\n", encoding="utf-8")

        deep = root / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)

        found = find_kit(deep)
        assert found == kit_dir, "深い階層からの探索に失敗: {} != {}".format(found, kit_dir)

        # start 自身が kit ディレクトリの場合
        found_self = find_kit(kit_dir)
        assert found_self == kit_dir, "kit 自身を start にした場合の解決に失敗"

    # ケース2: 見つからなければ SystemExit
    with tempfile.TemporaryDirectory() as tmp2:
        root2 = Path(tmp2)
        deep2 = root2 / "x" / "y"
        deep2.mkdir(parents=True)
        try:
            find_kit(deep2)
        except SystemExit:
            pass
        else:
            raise AssertionError("kit が無いのに SystemExit しなかった")

    print("OK: ci_paths.py selftest 2/2 passed")


def _main():
    if "--selftest" in sys.argv:
        _selftest()
        sys.exit(0)
    try:
        kit = find_kit()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    print(str(kit))


if __name__ == "__main__":
    _main()
