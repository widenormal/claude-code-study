#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_wella_deck.py — WELLA(OPI/RH) Amazon 月次定例デッキ（5co. CI v2）。

WELLAの実定例MTG(月次運用報告)の構成を、CI表現層(ci_v2_lib)の上に再現する。
NatureLabの週次デッキ(build_deck.py)とは構造が別物のため、WELLA専用に分けている。
共通のCI部品(表紙/numfield/ヘッダ/章扉/横罫線テーブル/数値整形/フォント)は ci_v2_lib を再利用。

  python3 build_wella_deck.py <config.json>

実データ源(将来 extract で接続): 定例用 / Wella_Monthly_POS(FYサマリ) / 提出用_カテゴリ別 /
04_定例会用_スポンサー広告 / 05_定例会用_DSP。今はダミー値で構造プレビュー。

WELLA構成(実定例準拠＋OKR追加):
  表紙 / OKR進捗(FY年商目標→カテゴリ) / 月実績サマリ(YoY・○△×) / 年間目標進捗(FY) /
  カテゴリ・ブランド実績 / DSP / SA / まとめ・打ち手

CI制約(SLIDE.md準拠): --ink #101820 / --crystal #C3D7EE / 白 の3色。テーブルは横罫線のみ。
丸数字禁止(打ち手:1)。考察はSMART。評価基準は実定例の ○(目標以上)/△(-5%未満)/×(-5%以下)。
"""
import os
import sys
import ci_v2_lib as ci


def htable(headers, rows, unit, cls="sk"):
    """横罫線テーブル。rows: [{"cells":[...], "tot":bool, "hl":bool}]。先頭列は左寄せ。"""
    h = "<tr>" + "".join(f'<th class="l">{c}</th>' if i == 0 else f"<th>{c}</th>"
                         for i, c in enumerate(headers)) + "</tr>"
    body = ""
    for r in rows:
        tr = ' class="grand"' if r.get("tot") else (' class="hl"' if r.get("hl") else "")
        body += f"<tr{tr}>" + "".join(
            f'<td class="l bd">{v}</td>' if i == 0 else f"<td>{v}</td>"
            for i, v in enumerate(r["cells"])) + "</tr>"
    return f'<div class="skyu"><p class="sk-unit">{unit}</p><table class="{cls}">{h}{body}</table></div>'


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "config.json")
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(here, "..", "config.example.json")
    cfg = ci.load_config(cfg_path)

    title = f"{cfg['client_name']} Amazon 月次定例｜5co. CI"
    head = ci.load_ci_head(cfg["ci_base_html"], title, cfg.get("lockup_symbol_id", "lk"))
    logo = ci.img_data_uri(cfg["client_logo"])
    lk = cfg.get("lockup_symbol_id", "lk")
    period_html = ci.period(cfg.get("period_text", "対象月 YYYY年MM月 ・ 評価基準 ○△×"))

    def H(kicker, t, sub=""):
        return ci.header(kicker, t, sub, client_logo_uri=logo, lockup_id=lk, period_html=period_html)

    def ok(name, tgt, act, fc, mark, cls="", shr=""):
        return ci.oknode(name, tgt, act, fc, mark, cls, shr)

    S = []
    # ===================== ここから顧客ごとに書き換える領域（WELLA実値に差し替え）=====================

    # 1) 表紙
    S.append(ci.cover(
        cfg.get("client_kicker", "WELLA. ｜ Amazon Retail"),
        "Amazon広告<br>月次運用報告",
        "Amazon 月次定例MTG ・ 開催日 YYYY年MM月DD日<br>対象 YYYY年MM月実績（評価基準 ○＝目標以上／△＝-5%未満／×＝-5%以下）",
        client_logo_uri=logo, lockup_id=lk))

    # 2) 月次OKR進捗（Objective=当月目標 / KR=カテゴリ・ブランド進捗。年商目標は上部に参照）
    S.append(f"""<section class="slide">{H("OKR Progress", "Amazon ◯月 OKR進捗（YYYY年MM月）")}
<div class="okr-annual-wrap"><div class="okr-annual">（参考）FY26 年商必達目標 <b>X.X億円</b>（YoY 126%）　／　年間ペース着地 <b>X.X億</b>（YoY XXX%）</div></div>
<div class="okr okr-sbs">
  <div class="okr-total-side">{ok("当月 全体", "<b>X.XX億</b>（当月目標）", "<b>X.XX億</b>", "<b>X.XX億</b>（着地・YoY XXX%）", "ok", "lead")}</div>
  <ul><li>{ok("WELLA Amazon", "<b>X.X億</b>", "<b>X.X億</b>（進捗XX%）", "<b>X.X億</b>（着地）", "ok", "big")}
      <ul>
        <li class="sgrp"><div class="sgrp-row">
          {ok("OPI", "<b>X.X億</b>", "<b>X.X億</b>（YoY XXX%）", "<b>X.X億</b>", "ok", "s mid", shr="&nbsp;")}
          {ok("ネイルカラー", "<b>X.X億</b>", "<b>X.X億</b>", "<b>X.X億</b>", "ok", "cat", shr="推計シェア X.X%")}
          {ok("トリートメント", "<b>X.X億</b>", "<b>X.X億</b>", "<b>X.X億</b>", "bh", "cat", shr="推計シェア X.X%")}
        </div></li>
        <li class="emg">{ok("RH", "<b>X.X億</b>（YoY XXX%）", "<b>X.X億</b>", "<b>X.X億</b>", "ok", "s mid", shr="&nbsp;")}</li>
      </ul></li>
  </ul>
</div>
<p class="t-note note-c okr-legend">○＝目標以上／△＝目標から-5%未満／×＝-5%以下　｜　Objective＝当月GMS目標、KR＝カテゴリ別GMS進捗（年商目標は参考）</p>
<div class="okr-insight"><span class="ins-lbl">洞察</span><span class="ins-txt">（SMARTで1〜2文：当月目標X.X億に対し実績X.X億・着地X.X億（YoYXXX%）。下振れカテゴリと打ち手を実数で）</span></div>
</section>""")

    # 3) 月実績サマリ（YoY・○△×）
    S.append(f"""<section class="slide">{H("Monthly Result", "当月実績サマリ（前年同月比）", "総売上・注文数・GV・CVR を前年同月と対比。評価は ○△×。")}
{htable(
    ["指標", "前年同月", "当月", "YoY", "評価"],
    [{"cells": ["総売上（GMS）", "¥XX.XM", "¥XX.XM", "XXX%", "○"], "tot": True},
     {"cells": ["注文数", "XX,XXX", "XX,XXX", "XXX%", "○"]},
     {"cells": ["GV（トラフィック）", "XXX,XXX", "XXX,XXX", "XXX%", "△"], "hl": True},
     {"cells": ["CVR", "X.X%", "X.X%", "—", "—"]}],
    "出典：定例用タブ（ベンダーセントラル/AMZ-POS）。GMSはベンダーセントラル実数値が正。")}
<ul class="clean"><li>（当月の着地と前月差・要因を実数で1〜2行。例：トラフィック低下が主因 等）</li></ul>
</section>""")

    # 4) 年間目標進捗（FY）
    S.append(f"""<section class="slide">{H("FY Progress", "年間目標進捗（FY26）", "FY必達YoY126%に対する実績ペースと着地見込。")}
{htable(
    ["区分", "FY必達目標", "実績（〆まで）", "進捗YoY", "着地ペース", "評価"],
    [{"cells": ["WELLA Amazon 計", "¥X.X億", "¥X.X億", "133%", "¥X.X億 / 131%", "○"], "tot": True},
     {"cells": ["OPI", "¥X.X億", "¥X.X億", "XXX%", "¥X.X億 / XXX%", "○"]},
     {"cells": ["RH", "¥X.X億", "¥X.X億", "XXX%", "¥X.X億 / XXX%", "△"], "hl": True}],
    "出典：Wella_Monthly_POS FYサマリ（OPI/RH）。FY必達 YoY126%／百万円・整数四捨五入。")}
<ul class="clean"><li>（年間ペースの所見：着地約X.X億・YoYXXX%。必達との差と挽回打ち手を実数で）</li></ul>
</section>""")

    # 5) カテゴリ・ブランド実績
    S.append(f"""<section class="slide">{H("Category", "カテゴリ・ブランド実績", "主要カテゴリ/ブランドの当月着地・前月差・要因。")}
{htable(
    ["カテゴリ／ブランド", "目標", "当月着地", "前月差", "YoY", "推計シェア", "評価"],
    [{"cells": ["OPI 計", "¥XX.XM", "¥XX.XM", "+X.XM", "XXX%", "—", "○"], "tot": True},
     {"cells": ["ネイルカラー", "¥X.XM", "¥X.XM", "+X.XM", "XXX%", "X.X%", "○"]},
     {"cells": ["トリートメント（ヘアオイル等）", "¥X.XM", "¥X.XM", "▲X.XM", "XXX%", "X.X%", "△"], "hl": True},
     {"cells": ["EssenceIN", "¥X.XM", "¥X.XM", "▲X.XM", "XXX%", "X.X%", "×"]}],
    "出典：提出用_カテゴリ別 ＋ Monthly POS シリーズ別。金額＝百万円・△＝マイナス。")}
<ul class="clean"><li>（牽引/下振れカテゴリを名指しで。例：ヘアオイルはトラフィック低下で前月比▲、EssenceInはROAS低迷）</li></ul>
</section>""")

    # 6) Amazon DSP【ALLカテゴリ】
    S.append(f"""<section class="slide">{H("Advertising ｜ DSP", "Amazon DSP（ALLカテゴリ）", "拡張セグメント含む。新規獲得効率と合算ROAS。")}
{htable(
    ["区分", "予算(万)", "投下(万)", "進捗", "IMP", "DPV", "購入", "売上(万)", "ROAS", "新規CPP"],
    [{"cells": ["DSP 合計", "XXX", "XXX", "XX%", "X,XXX,XXX", "XX,XXX", "XXX", "X,XXX", "XXX%", "¥XXX"], "tot": True},
     {"cells": ["ヘアケア（拡張）", "XXX", "XXX", "XX%", "X,XXX,XXX", "XX,XXX", "XXX", "X,XXX", "XXX%", "¥XXX"]},
     {"cells": ["Bonus（ノンセグ）", "XXX", "XXX", "XX%", "X,XXX,XXX", "XX,XXX", "XXX", "X,XXX", "XXX%", "¥XXX"]}],
    "出典：05_定例会用_DSP（25/9〜）＋Bonus用。金額＝万円・CPP＝円・IMP/DPV/購入＝件・他＝％。")}
<ul class="clean"><li>（配信方針・牽引セグメント・新規獲得効率を実数で）</li></ul>
</section>""")

    # 7) スポンサー広告 SA【ALLカテゴリ】
    S.append(f"""<section class="slide">{H("Advertising ｜ Sponsored Ads", "スポンサー広告 SA（ALLカテゴリ）", "一般/指名のファネル別。新規はAMCから取得。")}
{htable(
    ["ブランド", "投下(万)", "Imp", "Click", "CTR", "CPC", "CVR", "売上(万)", "ROAS", "新規率"],
    [{"cells": ["SA 合計", "XXX", "XX,XXX,XXX", "XXX,XXX", "X.X%", "¥XX", "X.X%", "X,XXX", "XXX%", "XX%"], "tot": True},
     {"cells": ["2plus1", "XX", "X,XXX,XXX", "XX,XXX", "X.X%", "¥XX", "X.X%", "XXX", "XXX%", "XX%"]},
     {"cells": ["EssenceIn", "XX", "X,XXX,XXX", "XX,XXX", "X.X%", "¥XX", "X.X%", "XXX", "XX%", "XX%"], "hl": True}],
    "出典：04_定例会用_スポンサー広告。新規はAMC。金額＝万円・CPC＝円・他＝％。")}
<ul class="clean"><li>（高効率/低効率ブランドを実数で。例：2plus1はCVR/ROAS安定、EssenceInはROAS100%割れ）</li></ul>
</section>""")

    # 8) まとめ・打ち手（dark）
    S.append(f"""<section class="slide dark">
  <svg class="corner" viewBox="0 0 50.857 36.507"><use href="#{lk}"/></svg>
  <span class="kicker">Summary &amp; Next</span><h2 class="title">今月の要点と打ち手</h2><div class="accent-bar"></div>
  <ul class="clean">
    <li><b>着地</b>｜（全体の当月着地・YoY、FY着地ペースを実数で）</li>
    <li><b>打ち手:1</b>｜（最大の下振れカテゴリの是正＝トラフィック/ROAS/在庫）</li>
    <li><b>打ち手:2</b>｜（未達カテゴリのMIDファネル新規CPP改善）</li>
    <li><b>打ち手:3</b>｜（予算の再配分・次月の重点）</li>
  </ul>
</section>""")
    # ===================== 顧客ごとに書き換える領域 ここまで =====================

    nf = ci.numfield_style(cfg.get("numfield_svg"))
    # 正典CSS連結＝ci_head 経由のみ(V3.2_FORMAT 1.6・fail-closed)。版スタンプが冒頭に焼き込まれる
    html = ci.add_autofigs(ci.inject_ci_head(ci.render(head, S, extra_head=nf)))
    out = cfg.get("output_html", "./output/WELLA_月次定例.html")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print("生成:", out, "slides:", len(S), "bytes:", len(html))
    if "--pdf" in sys.argv:
        print("PDF:", ci.to_pdf(out, cfg.get("output_pdf", os.path.splitext(out)[0] + ".pdf")))


if __name__ == "__main__":
    main()
