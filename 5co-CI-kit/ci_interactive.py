#!/usr/bin/env python3
"""
ci_interactive.py — 動く資料（v3.9・任意）の部品を HTML 文字列で返すヘルパ＋型見本

何のためか:
  会議で「その内訳は？」と聞かれたとき、押せば根拠が開く資料で答える。
  本文スライドは今の CI v3.2 系のまま。この部品は「押す・切り替える・組み上がる」だけを足す。
  部品を関数に固定するのは、案件ごとに data 属性や JS を手書きするとドリフト源になるため
  （ci_frameworks.py と同じ考え方）。CSS/JS 本体は ci_head.py --interactive が連結する。

いちばん大事な規則（V3.2_FORMAT.md「動く資料」が正）:
  1. 1ページに操作は1つだけ。見出しの判断を、読み手が自分の手で確かめられる操作にする。
  2. 操作は見出しが言いたいことの「構造」で決まる（センスで選ばない）:
       結論と根拠   → ev_button + ev_panel（押すと右から根拠パネル。ほぼ全ページに付ける）
       切り口       → op(seg(...)) + bar_rows(sort="desc")（切り替えると並び替わる）
       差分         → op(seg(["前","後"])) + bar_rows(ghost="前")（形が変わり、差が点線で残る）
       原因と結果   → op(slider(...)) + out(...) + formula(...)（動かすと再計算・式を画面に出す）
       不足と打ち手 → op(chip(...)) + data-ci-when="+打ち手"（オン/オフで不足が埋まる・残る）
       流れと時間   → data-ci-step と goto_card（順に組み上がる・押すとそのページへ）
  3. 量を表す動きは値から計算する（bar_rows は値の比で描く）。素材に無い数字は置かない。
  4. 静止状態（#static・印刷・PDF）は「見出しの判断が見える状態」。op(static=…/static_on=…) で決める。

使い方:
  import ci_head, ci_interactive as ci
  head = ci_head.style_block(interactive=True)          # 正典CSS＋動く資料の CSS/JS
  html = ci.ev_button("ev-p2") + ci.ev_panel("ev-p2", crumb="現状 › 荷待ち", judge="…",
                                             tabs=[("内訳", "<table>…</table>")], src="…")

  python3 ci_interactive.py --demo [out.html]   # 6構造の型見本（見本値は架空）を書き出す
"""
import html as _h
import json

__all__ = ["ev_button", "ev_panel", "panel", "goto_card", "op", "seg", "chip", "slider",
           "bar_rows", "out", "formula", "step", "define"]


def _a(v) -> str:
    return _h.escape(str(v), quote=True)


# ---------------------------------------------------------------- 結論と根拠
def ev_button(target: str, label: str = "内訳を見る") -> str:
    """根拠パネルを開くボタン（印刷では場所を保ったまま消える）。"""
    return f'<button class="ci-ev-btn" data-ci-ev="{_a(target)}">{_h.escape(label)}</button>'


def ev_panel(pid: str, crumb: str, judge: str, tabs, src: str) -> str:
    """押すと右から出る根拠パネルの中身（<template>＝本体の検査・PDF には出ない）。

    crumb: どこの話か（例「現状 › 荷待ち」）／judge: 判断1〜2行／tabs: [(タブ名, 中身HTML)]（2つまで）
    src: 出所（必須。出所の無い根拠は置かない）
    """
    if not src:
        raise ValueError("ev_panel: 出所（src）は必須です")
    tabs = list(tabs)
    if not 1 <= len(tabs) <= 2:
        raise ValueError("ev_panel: タブは1〜2個にしてください")
    secs = "".join(f'<section data-ci-tab="{_a(n)}">{body}</section>' for n, body in tabs)
    return (f'<template id="{_a(pid)}" data-crumb="{_a(crumb)}" data-judge="{_a(judge)}" '
            f'data-src="{_a(src)}">{secs}</template>')


def panel(big: str, unit: str, what: str, sub: str, diff: str, ev: str = "", step_no: int = 3) -> str:
    """ページ右の根拠の枠：大きな数字1つ → 何か → 補足 → 比べる相手と差（式つき）→ 内訳を見る。"""
    btn = ev_button(ev) if ev else ""
    return (f'<div class="ci-panel" data-ci-step="{step_no}">'
            f'<div class="ci-big">{_h.escape(big)}<small>{_h.escape(unit)}</small></div>'
            f'<div class="ci-what">{what}</div><div class="ci-sub">{sub}</div>'
            f'<div class="ci-diff">{diff}</div>{btn}</div>')


# ---------------------------------------------------------------- 流れと時間
def goto_card(target: str, body: str, step_no: int = 2) -> str:
    """押すとそのページへ入るカード（target＝飛び先 .slide の id）。

    右上のページ番号「p.N ›」は JS が飛び先から数えて入れる（直書きしない＝並べ替えてもずれない）。
    """
    return (f'<div class="ci-card" data-ci-goto="{_a(target)}" data-ci-step="{step_no}">'
            f'<span class="ci-card-go"></span>{body}</div>')


def step(n: int) -> str:
    """組み上がりの順番の属性（1=見出し 2=主役の図 3=数字 4=根拠）。"""
    return f'data-ci-step="{int(n)}"'


# ---------------------------------------------------------------- 1枚1操作
def op(inner: str, static: str = None, static_on=None, initial: str = None, initial_on=None,
       sort: str = None, max_value: float = None, cls: str = "") -> str:
    """操作の入れ物（1ページに1つ）。static/static_on＝静止状態（PDF・検査）で見せる状態。"""
    attrs = ["data-ci-op"]
    if static is not None:
        attrs.append(f'data-ci-static="{_a(static)}"')
    if static_on is not None:
        attrs.append(f'data-ci-static-on="{_a(" ".join(static_on))}"')
    if initial is not None:
        attrs.append(f'data-ci-initial="{_a(initial)}"')
    if initial_on is not None:
        attrs.append(f'data-ci-initial-on="{_a(" ".join(initial_on))}"')
    if sort:
        if sort not in ("desc", "asc"):
            raise ValueError("op: sort は desc か asc")
        attrs.append(f'data-ci-sort="{sort}"')
    if max_value:
        attrs.append(f'data-ci-max="{max_value:g}"')
    c = f' class="{_a(cls)}"' if cls else ""
    return f'<div {" ".join(attrs)}{c}>{inner}</div>'


def seg(options, label: str = "") -> str:
    """切り口・前後の切り替え（どれか1つ）。"""
    btns = "".join(f'<button data-ci-set="{_a(o)}">{_h.escape(o)}</button>' for o in options)
    lab = f"<span>{_h.escape(label)}</span>" if label else ""
    return f'<div class="ci-controls">{lab}<div class="ci-seg">{btns}</div></div>'


def chip(key: str, label: str = None) -> str:
    """打ち手のオン/オフ。"""
    return f'<button class="ci-chip" data-ci-toggle="{_a(key)}">{_h.escape(label or key)}</button>'


def slider(var: str, lo: float, hi: float, value: float, step_: float = 1, label: str = "") -> str:
    """条件を動かすスライダー（値は CIInteractive.define の関数に s.vars[var] で渡る）。"""
    lab = f"<span>{_h.escape(label)}</span>" if label else ""
    return (f'<label class="ci-controls">{lab}<input class="ci-range" type="range" data-ci-var="{_a(var)}" '
            f'min="{lo:g}" max="{hi:g}" step="{step_:g}" value="{value:g}"></label>')


def out(name: str, cls: str = "") -> str:
    """計算結果を出す場所（中身は CIInteractive.define(name, fn) の戻り値）。"""
    c = f' class="{_a(cls)}"' if cls else ""
    return f'<span data-ci-out="{_a(name)}"{c}></span>'


def formula(text_html: str) -> str:
    """計算式を画面に出す枠（試算は必ず式と前提を見せる）。"""
    return f'<div class="ci-formula">{text_html}</div>'


def define(name: str, js_arrow: str) -> str:
    """計算式の登録（デッキ側の JS はこれだけ）。js_arrow 例: 's => (s.vars.x * 22 / 60).toFixed(1)'"""
    return f'<script>CIInteractive.define({json.dumps(name, ensure_ascii=False)}, {js_arrow});</script>'


def bar_rows(rows, modes=None, fmt="{:,.0f}", unit="", ghost: str = None, src: str = "") -> str:
    """値で伸びる横棒の一覧。

    rows: [(名前, 値 or {状態: 値}, 主役か)]
    modes: 切り替えがあるときの状態名（値の表示を状態ごとに重ねて置く）
    ghost: 差分で「前」の値を点線で残すときの状態名（op(max_value=…) で目盛りをそろえること）
    src: 吹き出し（ホバー）に出す出所
    """
    out_rows = []
    for name, vals, main in rows:
        if isinstance(vals, dict):
            data = f"data-ci-values='{_a(json.dumps(vals, ensure_ascii=False))}'"
            texts = "".join(
                f'<span data-ci-when="{_a(m)}">{fmt.format(vals.get(m, 0))}{_h.escape(unit)}</span>'
                for m in (modes or vals.keys()))
            val = f'<span class="ci-val ci-stack">{texts}</span>'
            tip = " / ".join(f"{m}: {fmt.format(v)}{unit}" for m, v in vals.items())
        else:
            data = f'data-ci-value="{vals:g}"'
            val = f'<span class="ci-val">{fmt.format(vals)}{_h.escape(unit)}</span>'
            tip = f"{fmt.format(vals)}{unit}"
        title = _a(f"{name}｜{tip}" + (f"｜出所: {src}" if src else ""))
        g = ""
        if ghost and isinstance(vals, dict) and ghost in vals:
            g = f'<div class="ci-ghost" data-ci-ghost="{_a(ghost)}"></div>'
        out_rows.append(
            f'<div class="ci-row{" ci-main" if main else ""}" data-ci-row>'
            f'<span>{_h.escape(name)}</span>'
            f'<div class="ci-track" title="{title}">{g}'
            f'<div class="ci-fill ci-h ci-grow-x" data-ci-step="2" data-ci-bar {data}></div></div>{val}</div>')
    return f'<div class="ci-rows">{"".join(out_rows)}</div>'


# ---------------------------------------------------------------- 型見本（--demo）
def _slide(sid, kicker, title, body, gist=""):
    g = f'<p class="gist" data-ci-step="1"><span class="gist-k">このページの要点</span>{gist}</p>' if gist else ""
    return (f'<section class="slide" id="{sid}"><div class="hdr"><p class="kicker">{kicker}</p></div>'
            f'<h2 class="title" data-ci-step="1">{title}</h2><div class="accent-bar"></div>{g}{body}'
            f'<p class="note-line">見本値（架空）。型見本のため数字はデータ由来ではない</p></section>')


def demo(path="ci_interactive_demo.html"):
    """6構造の型見本を書き出す（見本値は架空）。ci_head.py が隣にあれば正典CSS＋動く資料を連結する。"""
    import pathlib
    import sys as _sys
    here = pathlib.Path(__file__).resolve().parent
    _sys.path.insert(0, str(here))
    import ci_head
    head = ci_head.style_block(interactive=True)
    SRC = "見本データ（架空）"

    p1 = _slide("p1", "Overview ｜ 流れと時間",
                "拘束時間の超過は荷待ちと荷役に集中し、運転時間はほぼ変わっていない",
                '<div class="kpis" data-ci-step="3">'
                '<div class="kpi"><div class="v">13.2<small>h</small></div><div class="l">1日の拘束時間（見本値）</div></div>'
                '<div class="kpi"><div class="v">2.4<small>h</small></div><div class="l">うち荷待ち（見本値）</div></div>'
                '<div class="kpi"><div class="v">38<small>%</small></div><div class="l">超過日の割合（見本値）</div></div></div>'
                '<div class="cols">'
                + goto_card("p2", '<div class="h3">どこで時間が漏れているか</div><div class="t-note">工程別の時間を切り口で見る</div>')
                + goto_card("p3", '<div class="h3">前年から何が縮んだか</div><div class="t-note">前後で形が変わり、差が残る</div>')
                + goto_card("p4", '<div class="h3">荷待ちを減らすと何時間減るか</div><div class="t-note">条件を動かして試算する</div>')
                + goto_card("p5", '<div class="h3">打ち手でどこまで埋まるか</div><div class="t-note">打ち手をオン/オフする</div>')
                + '</div>',
                gist="押すと各ページへ入れる。O キーで全ページを並べ、見出しだけで筋が通るかを確かめる")

    rows2 = [("運転", {"時間": 6.1, "件数比": 30}, False), ("荷待ち", {"時間": 2.4, "件数比": 45}, True),
             ("荷役", {"時間": 2.2, "件数比": 15}, False), ("休憩", {"時間": 1.5, "件数比": 6}, False),
             ("点検", {"時間": 1.0, "件数比": 4}, False)]
    p2 = _slide("p2", "Pyramid ｜ 結論と根拠 × 切り口",
                "超過日の半数近くは荷待ちが原因で、時間で見ても運転に次ぐ大きさだ",
                '<div class="cols" style="gap:28px"><div style="flex:0 0 60%">'
                + op(seg(["時間", "件数比"], "切り口:")
                     + '<div class="t-note" style="margin:6px 0">図の読み方: 1日あたりの工程別の時間（h）／超過日の原因の件数比（%）。切り替えると並び替わる</div>'
                     + bar_rows(rows2, modes=["時間", "件数比"], fmt="{:.1f}", src=SRC),
                     static="件数比", sort="desc")
                + '</div><div style="flex:1">'
                + panel("45", "%", "超過日の原因のうち荷待ち", "運転（30%）より多い。荷主側の受け入れ待ちが主因",
                        "比べる相手＝運転 30%｜差 = 45 − 30 = <b>15pt</b>", ev="ev-p2")
                + '</div></div>'
                + ev_panel("ev-p2", "現状 › 荷待ち", "荷待ちは特定の2拠点に偏っている。拠点別の受け入れ枠が打ち手の起点",
                           [("内訳", '<table><tr><th>拠点</th><th class="r">荷待ち（h/日）</th></tr>'
                                    '<tr><td>拠点A</td><td class="r">1.1</td></tr><tr><td>拠点B</td><td class="r">0.8</td></tr>'
                                    '<tr><td>その他</td><td class="r">0.5</td></tr></table>'),
                            ("出所と前提", "<p>見本データ（架空）。1日あたりの平均。超過＝拘束13時間超の日</p>")], SRC),
                gist="切り口を「時間」に替えても荷待ちは2番目。どちらで見ても主要因であることを手で確かめられる")

    rows3 = [("運転", {"前": 6.3, "後": 6.1}, False), ("荷待ち", {"前": 3.3, "後": 2.4}, True),
             ("荷役", {"前": 2.9, "後": 2.2}, False), ("休憩", {"前": 1.5, "後": 1.5}, False),
             ("点検", {"前": 1.0, "後": 1.0}, False)]
    ghost_rows = bar_rows(rows3, modes=["前", "後"], fmt="{:.1f}", unit="h", ghost="前", src=SRC)
    p3 = _slide("p3", "Diff ｜ 差分",
                "前年から縮んだ1.8時間のうち1.6時間は、荷待ちと荷役の削減によるものだ",
                '<div class="cols" style="gap:28px"><div style="flex:0 0 60%">'
                + op(seg(["前", "後"], "年度:")
                     + '<div class="t-note" style="margin:6px 0">図の読み方: 工程別の1日あたり時間（h）。「後」に替えると、前年の長さが点線で残る</div>'
                     + ghost_rows, static="後", max_value=7)
                + '</div><div style="flex:1">'
                + panel("1.8", "h", "1日の拘束時間の減少（前年→今年）", "うち荷待ち 0.9h・荷役 0.7h＝1.6h。運転は 0.2h",
                        "差 = 15.0 − 13.2 = <b>1.8h</b>（5工程の合計）", ev="ev-p3")
                + '</div></div>'
                + ev_panel("ev-p3", "変化 › 前年比", "運転時間はほぼ不変。削減は待ちと荷役の運用改善による",
                           [("内訳", '<table><tr><th>工程</th><th class="r">前</th><th class="r">後</th><th class="r">差</th></tr>'
                                    '<tr><td>荷待ち</td><td class="r">3.3</td><td class="r">2.4</td><td class="r">−0.9</td></tr>'
                                    '<tr><td>荷役</td><td class="r">2.9</td><td class="r">2.2</td><td class="r">−0.7</td></tr>'
                                    '<tr><td>運転</td><td class="r">6.3</td><td class="r">6.1</td><td class="r">−0.2</td></tr></table>')],
                           SRC),
                gist="「前」「後」を切り替えると、縮んだのが運転ではなく待ちと荷役だと形で分かる")

    p4 = _slide("p4", "Cause ｜ 原因と結果",
                "荷待ちを1回30分縮めると、1人あたり月11時間の拘束時間が減る試算になる",
                op('<div class="cols" style="gap:28px"><div style="flex:0 0 60%" data-ci-step="2">'
                   + slider("短縮", 0, 60, 30, 5, "1回あたりの荷待ち短縮（分）:")
                   + '<div class="t-note" style="margin:10px 0 4px">試算結果（1人あたり・月）</div>'
                   + '<div class="ci-big" style="font-family:var(--serif-en);font-size:var(--fs-xl);line-height:1">'
                   + out("月の削減") + '<small style="font-size:.38em">h</small></div>'
                   + formula("試算の式: 短縮（分）× 月の運行回数 22回（見本値）÷ 60<br>前提: 荷待ちが毎運行1回発生する")
                   + '</div><div style="flex:1">'
                   + panel("22", "回/月", "月の運行回数（見本値）", "式の前提。回数が増えるほど削減は比例して大きくなる",
                           "30分 × 22回 ÷ 60 = <b>11h</b>", ev="ev-p4")
                   + '</div></div>')
                + define("月の削減", "s => (s.vars['短縮'] * 22 / 60).toFixed(1)")
                + ev_panel("ev-p4", "試算 › 前提", "これは試算。実際の削減は拠点ごとの受け入れ枠の改善幅による",
                           [("出所と前提", "<p>見本データ（架空）。運行回数 22回/月・荷待ち1回/運行を前提</p>")], SRC),
                gist="スライダーを動かすと試算がその場で計算し直される。式と前提は画面に出したまま")

    p5 = _slide("p5", "Gap ｜ 不足と打ち手",
                "3つの打ち手をすべて実行すれば、月の上限まで残る超過はなくなる見込みだ",
                op('<div class="cols" style="gap:28px"><div style="flex:0 0 60%" data-ci-step="2">'
                   + '<div class="ci-controls">打ち手: ' + chip("予約受付") + chip("パレット化") + chip("中継輸送") + '</div>'
                   + '<div class="t-note" style="margin:8px 0">図の読み方: 月の超過時間（h）を、打ち手ごとの削減見込みで埋める（見本値）</div>'
                   + '<div class="ci-rows">'
                   + '<div class="ci-row ci-main"><span>超過（現状）</span><div class="ci-track"><div class="ci-fill" style="width:100%"></div></div><span class="ci-val">38h</span></div>'
                   + '<div class="ci-row" data-ci-when="+予約受付"><span>予約受付</span><div class="ci-track"><div class="ci-fill" style="width:47.4%"></div></div><span class="ci-val">−18h</span></div>'
                   + '<div class="ci-row" data-ci-when="+パレット化"><span>パレット化</span><div class="ci-track"><div class="ci-fill" style="width:31.6%"></div></div><span class="ci-val">−12h</span></div>'
                   + '<div class="ci-row" data-ci-when="+中継輸送"><span>中継輸送</span><div class="ci-track"><div class="ci-fill" style="width:21.1%"></div></div><span class="ci-val">−8h</span></div>'
                   + '</div></div><div style="flex:1" data-ci-step="3">'
                   + '<div class="ci-panel"><div class="ci-big">' + out("残り") + '<small>h</small></div>'
                   + '<div class="ci-what">打ち手の後に残る月の超過</div>'
                   + '<div class="ci-diff">残り = 38 − 選んだ打ち手の削減見込み の合計</div>'
                   + ev_button("ev-p5") + '</div></div></div>', static_on=["予約受付", "パレット化", "中継輸送"])
                + define("残り", "s => String(38 - (s.on.has('予約受付') ? 18 : 0) - (s.on.has('パレット化') ? 12 : 0) - (s.on.has('中継輸送') ? 8 : 0))")
                + ev_panel("ev-p5", "打ち手 › 見込み", "予約受付だけで超過の約半分が埋まる。残りは荷役の機械化が要る",
                           [("内訳", '<table><tr><th>打ち手</th><th class="r">削減見込み（h/月）</th></tr>'
                                    '<tr><td>予約受付</td><td class="r">18</td></tr><tr><td>パレット化</td><td class="r">12</td></tr>'
                                    '<tr><td>中継輸送</td><td class="r">8</td></tr></table>')], SRC),
                gist="打ち手を1つずつオンにすると、どれがどれだけ埋めるかが分かる（静止状態は全部オン）")

    doc = ('<!DOCTYPE html>\n<html lang="ja"><head><meta charset="UTF-8">\n'
           '<title>ci_interactive 型見本（動く資料）</title>\n' + head + '\n</head><body>\n'
           + "\n".join([p1, p2, p3, p4, p5]) + "\n</body></html>\n")
    pathlib.Path(path).write_text(doc, encoding="utf-8")
    print(f"動く資料の型見本を書き出しました: {path}（5ページ・6構造）")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        i = sys.argv.index("--demo")
        demo(sys.argv[i + 1] if len(sys.argv) > i + 1 else "ci_interactive_demo.html")
    else:
        print(__doc__.strip())
