#!/usr/bin/env python3
"""
ci_options.py — CIスライドの「出力オプション」を記録・読み出す（v3.9）

なぜ要るか:
  PDF を必須から任意にした（2026-09-27）。何を出すか（動く資料／PDF／PPTX）は作成依頼のたびに
  選び、その答えをデッキの隣のファイルに残す。ci-finalize.sh はこのファイルを読んで出し分ける。
  答えを会話の中だけに置くと、あとで finalize を回した人（別セッション・ファイナライザ）に届かず、
  要らない PDF が出たり、欲しい PPTX が出なかったりする。

ファイル: <デッキ名>.ci-options.json（デッキ HTML と同じフォルダ）
  {"interactive": true, "pdf": false, "pptx": true, "figs_multiagent": false, "decided_at": "2026-09-27"}
  HTML は常に作るので項目に無い。interactive は「ci_head.py --interactive で組む」かどうか。
  figs_multiagent（任意・v3.10）は「図・イラストをマルチエージェント（作成→レビュー）で仕上げる」かどうか。
  省略時は false（Claude が1人で描き、表・箇条書きのページには ci_figs.py autofig が図を添える）。

使い方:
  python3 ci_options.py write <deck.html> --interactive --no-pdf --pptx [--figs-multi|--no-figs-multi]   # 答えを記録
  python3 ci_options.py show  <deck.html>                                 # 人が読む形で表示
  python3 ci_options.py read  <deck.html|options.json>                    # ci-finalize.sh 用（"pdf pptx interactive" を 1/0 で）

終了コード: 0=成功 / 1=形式不正・引数不正（黙って既定に戻さない）
"""
import datetime
import json
import sys
from pathlib import Path

KEYS = ("interactive", "pdf", "pptx")
OPTIONAL = {"figs_multiagent": "図・イラストをマルチエージェントで仕上げる"}   # 省略時 false（v3.10）
LABEL = {"interactive": "動く資料（押すと根拠が開くHTML）", "pdf": "PDF", "pptx": "PPTX（1枚1画像）"}


def options_path(target: str) -> Path:
    p = Path(target)
    if p.suffix == ".json":
        return p
    return p.with_name(p.stem + ".ci-options.json")


def load(target: str) -> dict:
    p = options_path(target)
    try:
        o = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except Exception as e:
        raise ValueError(f"{p} が JSON として読めません: {e}")
    if not isinstance(o, dict):
        raise ValueError(f"{p} は {{...}} の形で書いてください")
    unknown = [k for k in o if k not in KEYS and k not in OPTIONAL and k != "decided_at"]
    if unknown:
        # 打ち間違い（"ppxt" 等）を黙って受けると、その項目が既定値（出す）に化ける
        raise ValueError(f"{p}: 知らない項目 {', '.join(unknown)}（使えるのは {', '.join(KEYS)}）")
    for k in KEYS + tuple(OPTIONAL):
        if k in o and not isinstance(o[k], bool):
            raise ValueError(f"{p}: {k} は true/false で書いてください（今は {o[k]!r}）")
    return o


def load_complete(target: str) -> dict:
    """3つとも決まっていることまで確かめる（finalize が読むときはこちら＝部分指定を既定値で埋めない）。"""
    o = load(target)
    missing = [k for k in KEYS if k not in o]
    if missing:
        raise ValueError(f"{options_path(target)}: 未決の項目 {', '.join(missing)}（ci_options.py write で3つとも決める）")
    return o


def write(target: str, flags: list) -> Path:
    o = {}
    p = options_path(target)
    if p.exists():
        o = load(target)
    for f in flags:
        neg = f.startswith("--no-")
        k = f[5:] if neg else f[2:]
        if k == "figs-multi":
            k = "figs_multiagent"
        if k not in KEYS and k not in OPTIONAL:
            raise ValueError(f"知らないオプション: {f}（使えるのは --interactive/--pdf/--pptx/--figs-multi と --no-…）")
        o[k] = not neg
    missing = [k for k in KEYS if k not in o]
    if missing:
        raise ValueError("3つとも決めてください（未決: " + ", ".join(missing) + "）。例: --interactive --no-pdf --pptx")
    o["decided_at"] = datetime.date.today().isoformat()
    p.write_text(json.dumps(o, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def main(argv):
    if len(argv) < 2 or argv[0] not in ("write", "read", "show"):
        print(__doc__.strip())
        return 1
    cmd, target, rest = argv[0], argv[1], argv[2:]
    try:
        if cmd == "write":
            p = write(target, rest)
            o = load(target)
            print(f"記録しました: {p}")
            print("  出す物: HTML" + "".join(f" ＋ {LABEL[k]}" for k in KEYS if o[k]))
            print("  図・イラスト: " + ("マルチエージェント（作成→レビュー）で仕上げる" if o.get("figs_multiagent") else "Claude が描く＋表・箇条書きは自動の図（autofig）"))
        elif cmd == "read":
            o = load_complete(target)
            print(" ".join("1" if o[k] else "0" for k in ("pdf", "pptx", "interactive")))
        else:
            o = load(target)
            for k in KEYS:
                print(f"  {LABEL[k]}: {'出す' if o.get(k) else ('出さない' if k in o else '未決')}")
            print(f"  {OPTIONAL['figs_multiagent']}: {'する' if o.get('figs_multiagent') else 'しない'}")
        return 0
    except FileNotFoundError:
        print(f"NG: 出力オプションが見つかりません: {options_path(target)}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"NG: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
