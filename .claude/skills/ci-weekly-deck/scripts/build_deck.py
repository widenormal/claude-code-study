#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_deck.py — 週次定例デッキ(5co. CI v2)の worked sample【フル忠実版・14枚】。

元の制作デッキと **同じ14枚構成**(表紙/OKR/S級ドリル/エマージング/PD章扉/PD目標/DSP/SA/
まとめ/補助章扉/SAファネル/香調別月別/競合ベンチ/全ブランド一覧)を、
架空ブランド(ブランドA/B/C・EM-n)とダミー数値で生成する。単体で実行でき完成HTMLが出る。

  python3 build_deck.py [config.json]        # HTML生成
  python3 build_deck.py --pdf                # PDFも出力

★実運用では:
  - 表データ … extract_deck_data.py が出す deck_data.json 等(同じ列構造)に差し替える
  - 文言(キッカー/タイトル/所見/打ち手)とOKRツリーの数値 … 下記「顧客ごとに書き換える領域」を実値へ
  - 顧客固有定数(市場辞書/ハイライト/PD行/lavonレシピ) … config か差し替え領域で与える

CI制約(厳守): 3色のみ・緑赤グレー禁止・丸数字禁止(「打ち手:1」)・A4横・考察はSMART(実数+期限)。
"""
import os
import sys
import json
import ci_v2_lib as ci
import deck_builders as B
import sample_data as SD


def load_tables(cfg):
    """config に実データJSONパスがあれば読む。無ければ sample_data を使う。"""
    data = cfg.get("data") or {}
    if data.get("skyu_full") and data.get("deck_data"):
        base = os.path.dirname(os.path.abspath(cfg["__path__"]))

        def _load(p):
            p = os.path.expanduser(p)
            p = p if os.path.isabs(p) else os.path.join(base, p)
            return json.load(open(p, encoding="utf-8"))
        d = SD.all_data()  # 定数(市場辞書/HL等)は config 側で上書きする想定
        d["skyu_full"] = _load(data["skyu_full"])
        d["deck_data"] = _load(data["deck_data"])
        if data.get("lavon"):
            d["lavon"] = _load(data["lavon"])
        print("● 実データで生成（config.data.* を使用）")
        return d
    # --- ダミー/実データの取り違え防止（必ず明示）---
    sid = str(cfg.get("spreadsheet_id", "") or "")
    if sid and not sid.startswith("REPLACE_"):
        print("⚠️  spreadsheet_id は設定済みですが config.data.skyu_full / deck_data が空です。")
        print("    → extract_deck_data.py で抽出 → config.data.* にそのJSONパスを指定してください。")
        print("    ★今は【ダミーデータ】で雛形を生成します（WELLA実データではありません）。")
    else:
        print("● ダミーデータで雛形生成（実データ化には spreadsheet_id と data.* を設定）")
    return SD.all_data()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    cfg_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "config.json")
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(here, "..", "config.example.json")
    cfg = ci.load_config(cfg_path)
    cfg["__path__"] = cfg_path

    title = f"{cfg['client_name']} 週次 定例報告書｜5co. CI"
    head = ci.load_ci_head(cfg["ci_base_html"], title, cfg.get("lockup_symbol_id", "lockup"))
    logo = ci.img_data_uri(cfg["client_logo"])
    lk = cfg.get("lockup_symbol_id", "lockup")
    period_html = ci.period(cfg.get("period_text", "日進捗 <b>70%</b> ・ 集計期間 YYYY-MM-DD〜MM-DD"))
    T = load_tables(cfg)
    dd = T["deck_data"]

    def H(kicker, t, sub=""):
        return ci.header(kicker, t, sub, client_logo_uri=logo, lockup_id=lk, period_html=period_html)

    S = []
    # ===================== ここから顧客ごとに書き換える領域 =====================

    # 1) 表紙
    S.append(ci.cover(
        cfg["client_kicker"], "週次<br>定例報告書",
        "Amazonリテール 週次レビュー ・ 開催日 YYYY年MM月DD日<br>集計期間 MM/DD–DD（基準進捗 NN%）",
        client_logo_uri=logo, lockup_id=lk))

    # 2) OKR進捗ツリー(数値はダミー)
    def ok(name, m, a, k, mark, cls="", shr=""):
        return ci.oknode(name, m, a, k, mark, cls, shr)
    S.append(f"""<section class="slide">{H("OKR Progress", "Amazon 202X年 OKR 進捗（基準進捗NN%）")}
<div class="okr-annual-wrap"><div class="okr-annual">Amazon 年商目標 <b>XXX億円</b>（YoY XXX%）</div></div>
<div class="okr okr-sbs">
  <div class="okr-total-side">{ok("当月 全体（発送）", "<b>X.XX億</b>（YoY XXX%）", "<b>X.XX億</b>", "<b>X.XX億</b>（XX%）", "ok", "lead")}</div>
  <ul><li>{ok("主要担当ブランド", "<b>X.XX億</b>", "<b>X.XX億</b>（進捗XX%）", "<b>X.XX億</b>（XXX%）", "ok", "big")}
      <ul>
        <li class="sgrp"><div class="sgrp-row">
          {ok("カテゴリA(S級)", "<b>X.XX億</b>", "<b>X.XX億</b>（XX%）", "<b>X.XX億</b>（XX%）", "ok", "s mid", shr="&nbsp;")}
          {ok("サブA1", "<b>X.XX億</b>", "<b>X.XX億</b>", "<b>X.XX億</b>", "ok", "cat", shr="推計シェア X.X%")}
          {ok("サブA2", "<b>X.XX億</b>", "<b>X.XX億</b>", "<b>X.XX億</b>", "bh", "cat", shr="推計シェア X.X%")}
        </div></li>
        <li class="emg">{ok("カテゴリB(EM)", "<b>X.XX億</b>（XXX%）", "<b>X.XX億</b>（XX%）", "<b>X.XX億</b>（XXX%）", "ok", "s mid", shr="&nbsp;")}</li>
      </ul></li>
  </ul>
</div>
<p class="t-note note-c okr-legend">○＝着地達成／△＝ビハインド　｜　※大型カテゴリは別出し</p>
<div class="okr-insight"><span class="ins-lbl">洞察</span><span class="ins-txt">（SMARTで結論を1〜2文：目標対比/前年対比の実数と期限を明記。例『XをYで補い着地99.1%』）</span></div>
</section>""")

    # 3) S級フル表 + 所見カード
    S.append(f"""<section class="slide">{H("Drill Down ｜ S-Rank", "S級ブランド ドリルダウン")}
{B.skyu(T["skyu_full"], market=T["market"], highlight=T["skyu_hl"], grand_label="S級合算（計）")}
<div class="sho-card"><span class="sho-h">洞察・KEY INSIGHTS</span>
<p class="sho-lead">（結論リード：当月の着地と最大の論点を実数1文で）</p>
<ul class="clean sho-l">
  <li><b>サマリ／リスク</b>　（実績・達成率・着地・目標比＋日販ペース超の確度を実数で）</li>
  <li><b>遅れ要因／回復</b>　（最大の遅れと上振れの内訳・打ち手）</li>
</ul></div>
</section>""")

    # 4) エマージング ドリルダウン(ブランド単位＋PV列)
    S.append(f"""<section class="slide">{H("Drill Down ｜ Emerging", "エマージングブランド ドリルダウン")}
{B.emrg_tbl(dd.get("エマージング_drill") or dd["エマージング_シリーズ"], highlight=T["emrg_hl"])}
<ul class="clean"><li>（牽引ブランドと下振れブランドを実数で。集客◎・転換×／在庫制約 等の構造を1〜2行）</li>
<li><b>KR:1（PV/集客）</b>は合計達成XX%。（広告増でなくLP/レビュー/価格の転換改善が打ち手のブランドを名指し）</li></ul>
</section>""")

    # 5) PD目標(pd_tbl)
    S.append(f"""<section class="slide">{H("Forward ｜ Prime Day 202X", "次セール 目標（M/D–D）", "主要担当のみで X.XX億円（YoY XXX%）を狙う。本セールに売上集中度 XX%。")}
{B.pd_tbl(T["pd_rows"])}
<p class="t-note">※出典・前提を明記（例：年間計画書「PD目標」タブ・ベンダー実績ベース）。別定例ブランドは除外。</p>
</section>""")

    # 6) DSP。実ソースが単一DSPなら合算1表、P+/Bonusタブがあれば3表に拡張（実extract契約に寛容）。
    dsp_html = ('<p class="sho-h" style="margin-top:2px">■DSP 通常・P+合算（Bonus抜き）</p>'
                + B.dsp_tbl(dd["DSP"], em_rows=(), tcls="dsp3",
                            note="金額＝万円・単価/CPP/eCPDPV＝円・DPV/購入/NtB/SnSS＝件・他＝％ ／ 各表 S級3＋EM計＋総合計"))
    if dd.get("DSP_P"):
        dsp_html += ('<p class="sho-h" style="margin-top:7px">■DSP Performance+のみ</p>'
                     + B.dsp_tbl(dd["DSP_P"], em_rows=(), tcls="dsp3", note="&nbsp;"))
    if dd.get("DSP_B"):
        dsp_html += ('<p class="sho-h" style="margin-top:7px">■DSP Bonusのみ（オンサイト内・ノンセグメント配信）</p>'
                     + B.dsp_tbl(dd["DSP_B"], em_rows=(), tcls="dsp3", note="&nbsp;"))
    S.append(f"""<section class="slide">{H("Advertising ｜ DSP", "Amazon DSP（通常＋Performance+）", "（要点：新規CPP/配信比率/合算ROAS を実数で）")}
{dsp_html}
</section>""")

    # 7) SA
    S.append(f"""<section class="slide">{H("Advertising ｜ Sponsored Ads", "スポンサー広告（SA）", "全体ROAS 約XXX%、一般Kw比率 XX%。指名ファネルが高効率。")}
{B.sa_tbl(dd["SA"], em_rows=(10, 11, 12, 13, 14), em_tot=15, grand=17)}
<ul class="clean"><li>（一般＝新規獲得／指名＝刈り取りの役割分担を実数で）</li></ul>
</section>""")

    # 8) まとめ(dark)
    S.append(f"""<section class="slide dark">
  <svg class="corner" viewBox="0 0 50.857 36.507"><use href="#{lk}"/></svg>
  <span class="kicker">Summary &amp; Next</span><h2 class="title">今週の要点と打ち手</h2><div class="accent-bar"></div>
  <ul class="clean">
    <li><b>着地</b>｜（全体・主要担当の着地を実数で・下振れ余地も併記）</li>
    <li><b>打ち手:1</b>｜（最大の上振れ余地と即アクション）</li>
    <li><b>打ち手:2</b>｜（広告効率/在庫等の是正）</li>
    <li><b>打ち手:3</b>｜（原資の再配分・次セール逆算）</li>
  </ul>
</section>""")

    # 9) 補助資料 章扉
    S.append(ci.divider(
        "Appendix ｜ 補助資料", "補助資料",
        "スポンサー広告のファネル別・香調別月別・競合ベンチ等の明細。", lockup_id=lk))

    # 10) SA ファネル別
    S.append(f"""<section class="slide">{H("Appendix ｜ SA Funnel", "スポンサー広告 ファネル別（一般／指名）", "指名ファネルは高ROAS・高CVR。一般は新規獲得、指名は刈り取りで役割分担。")}
{B.sa_funnel_tbl(dd["SA"], T["funnel_groups"], T["funnel_total"])}
<ul class="clean"><li>（指名の投下比率と効率、一般のCVR/CPP改善余地を実数で）</li></ul>
</section>""")

    # 11) 香調別 月別
    S.append(f"""<section class="slide">{H("Appendix ｜ Monthly by Scent", "香調別 月別売上", "本体＋詰め替え合算で香調別に月次把握。")}
{B.lavon_tbls(T["lavon"], T["lavon_sections"])}
<ul class="clean"><li>（主力香調・伸長/在庫切れを月次で監視し、伸びる香調へ在庫・配信を寄せる）</li></ul>
</section>""")

    # 12) 競合ベンチマーク(静的・プレースホルダー)
    S.append(f"""<section class="slide">{H("Appendix ｜ Emerging Benchmark", "エマージング 競合ベンチマーク＆シェア奪取", "老舗大手に対し『定着＋空きセグメント』でシェアを獲る。出典: 市場推計（参考）。")}
<div class="skyu"><table class="sk">
<tr><th class="l">ブランド／カテゴリ</th><th class="l">上位競合（直近シェア）</th><th class="l">現在地</th><th class="l">シェア奪取の打ち手</th></tr>
<tr><td class="l bd">ブランドX／カテゴリα</td><td class="l">競合A XX%</td><td class="l">実質#N・約XX%</td><td class="l">（旗艦防衛の打ち手）</td></tr>
<tr><td class="l bd">ブランドY／カテゴリβ</td><td class="l">競合B XX%・競合C XX%</td><td class="l">定着X%・#NN</td><td class="l">（空きセグメントでN%へ）</td></tr>
<tr><td class="l bd">ブランドZ／カテゴリγ</td><td class="l">競合D XX%（新興急伸）</td><td class="l">X%・未定着</td><td class="l">（流動市場の空きを定着で獲る）</td></tr>
</table>
<p class="sk-unit">直近シェア＝3ヶ月平均（市場推計・参考値）。月商/シェアはブランド名寄せ後。</p></div>
<ul class="clean"><li>（共通の即効打ち手＝表記揺れ統合等／第一KR＝連続出現＝定着 を1〜2行）</li></ul>
</section>""")

    # 13) エマージング 全ブランド一覧
    S.append(f"""<section class="slide">{H("Appendix ｜ Emerging 全ブランド", "エマージング 全ブランド一覧（ブランドレベル）", "主要ブランドはシリーズ別ドリルダウン（本編）、本表は全ブランドの網羅一覧。")}
{B.emrg_tbl_all(dd["エマージング"], grand_label="EM合計", annotate=T["emrg_annotate"])}
<ul class="clean"><li>（EM全体の目標/実績/着地と、後半挽回型ブランドを実数で。小規模も全数掲載）</li></ul>
</section>""")

    # PD章扉を PD目標(現 index4) の前に挿入(表紙の数字フィールド背景＋扉文字)
    S.insert(4, ci.pd_divider(
        "Forward ｜ Prime Day 202X", "次セール 目標",
        "M/D–D ・ 主要担当のみで X.XX億円（YoY XXX%）を狙う。<br>アーリーで初動、本セールで最大化。",
        lockup_id=lk))
    # ===================== 顧客ごとに書き換える領域 ここまで =====================

    nf = ci.numfield_style(cfg.get("numfield_svg"))  # 表紙の数字フィールド背景(data URI埋込)
    # 正典CSS連結＝ci_head 経由のみ(V3.2_FORMAT 1.6・fail-closed)。版スタンプが冒頭に焼き込まれる
    html = ci.add_autofigs(ci.inject_ci_head(ci.render(head, S, extra_head=nf)))
    out = cfg["output_html"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    open(out, "w", encoding="utf-8").write(html)
    print("生成:", out, "slides:", len(S), "bytes:", len(html))

    if "--pdf" in sys.argv:
        pdf = ci.to_pdf(out, cfg.get("output_pdf", os.path.splitext(out)[0] + ".pdf"))
        print("PDF:", pdf)


if __name__ == "__main__":
    main()
