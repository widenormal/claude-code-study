#!/usr/bin/env python3
"""ci_gates_json.py — ci-gates.sh --json の部品（v3.12.6・2026-10-30）。stdlib のみ。

  rec   <file> <label> <checker> <hard> <rc> <status> <has_json>   … 検査1件を JSON Lines 1行で stdout へ
                                                                   （検査の出力は stdin から読む）
  merge <jsonl> <fail(0/1)> <strict(0/1)> <kit_dir>                … 溜めた行を1つの JSON 文書にまとめる
  ok                                                               … stdin の JSON Lines がすべて ok なら終了コード0（レコード無し＝表示文で判定）

JSON 文書のスキーマ:
  {"tool":"ci-gates.sh","kit_version":"v3.12.6","ok":true,"strict":false,
   "files":[{"file":"deck.html","ok":true,"warnings":2,
             "gates":[{"label":"あふれ","checker":"slide_overflow_check.py","hard":true,"rc":0,
                       "status":"ok|warn|fail|skip|info","json":[…各検査の --json 出力…],"text":"…"}]}],
   "extra":[{"target":"figs:<dir>"|"cutouts:<dir>", …同じ形…}]}
  --json を持つ検査はその出力（JSON Lines）を "json" に配列で入れる。持たない検査は表示文を "text" に入れる。
"""
import json
import sys
from pathlib import Path


def _records(text):
    out, rest = [], []
    for line in text.splitlines():
        t = line.strip()
        if t.startswith("{"):
            try:
                out.append(json.loads(t))
                continue
            except ValueError:
                pass
        if t:
            rest.append(line)
    return out, rest


def rec(argv):
    f, label, checker, hard, rc, status, hj = argv
    out = sys.stdin.read()
    r = {"file": f or None, "label": label, "checker": checker, "hard": hard == "1",
         "rc": int(rc), "status": status}
    if hj == "1":
        js, rest = _records(out)
        r["json"] = js
        if rest:
            r["text"] = "\n".join(rest)
    else:
        r["text"] = out.rstrip("\n")
    print(json.dumps(r, ensure_ascii=False))
    return 0


def ok(_argv):
    """--json で走らせた検査の出力が所見なしか。レコードが無いとき（対象の画像が無い等）は
    表示文が空か「: OK」で終わっていれば所見なしとみなす。"""
    js, rest = _records(sys.stdin.read())
    if not js:
        return 0 if not rest or rest[-1].rstrip().endswith("OK") else 1
    return 0 if all(x.get("ok", True) is not False for x in js) else 1


def merge(argv):
    jrec, fail, strict, kit = argv
    try:
        ver = (Path(kit) / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        ver = None
    files, order, extra = {}, [], []
    p = Path(jrec)
    for line in (p.read_text(encoding="utf-8").splitlines() if p.is_file() else []):
        r = json.loads(line)
        f = r.pop("file")
        if f and not f.startswith(("figs:", "cutouts:")):
            if f not in files:
                files[f] = []
                order.append(f)
            files[f].append(r)
        else:
            r["target"] = f
            extra.append(r)
    doc = {"tool": "ci-gates.sh", "kit_version": ver, "ok": fail == "0", "strict": strict == "1",
           "files": [{"file": f, "ok": all(g["status"] != "fail" for g in files[f]),
                      "warnings": sum(g["status"] == "warn" for g in files[f]), "gates": files[f]}
                     for f in order],
           "extra": extra}
    print(json.dumps(doc, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    cmds = {"rec": rec, "merge": merge, "ok": ok}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    sys.exit(cmds[sys.argv[1]](sys.argv[2:]))
