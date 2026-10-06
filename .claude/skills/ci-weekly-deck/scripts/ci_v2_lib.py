#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ci_v2_lib.py — 週次定例デッキ(5co. CI v2)を組み立てる再利用ライブラリ。

このファイルは **顧客非依存** の共通部品のみを持つ:
  - 正典CSS連結: <!--CI_HEAD--> マーカーを 5co-CI-kit/ci_head.style_block() で置換する
    inject_ci_head()（V3.2_FORMAT 1.6 の唯一の標準方式・fail-closed）
  - CI基盤HTMLからロックアップsymbol(ブランド資産)だけを流用するHEADビルダ load_ci_head()
  - IR作法の数値整形ヘルパ(百万円/万円/円/件/%・四捨五入・マイナス△)
  - CI v2レイアウトヘルパ(表紙/ヘッダ/章扉/OKRノード)
  - 本デッキ固有の上書きCSS(EXTRA_CSS・正典と重複するルールは持たない)

顧客固有(ブランド名・実数値・所見文・スプレッドシートID・ロゴ)は **一切持たない**。
それらは build_deck.py 側の「顧客ごとに書き換える領域」と config.json に置く。

CI制約(厳守・SLIDE.md準拠): 配色は 白#FFFFFF / 水色 --crystal #C3D7EE / 紺 --ink #101820 の3色のみ
(旧世代のトークン名・旧hexは廃止済み。混入は scripts/check-slide-ci-parity.py が検出)。
増減セマンティクス(達成/未達)以外で緑・赤・グレー・他色相を使わない。
CSSは0から書かず正典を ci_head 連結で参照する(EXTRA_CSSは正典を壊さない最小の上書きのみ)。
"""
import re
import json
import base64
import os
import sys
import subprocess


# ---------------------------------------------------------------- config / IO
def load_config(path):
    """config.json を読む。相対パスは config の置き場基準で解決する。"""
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(path))

    def _resolve(p):
        p = os.path.expanduser(p)
        return p if os.path.isabs(p) else os.path.normpath(os.path.join(base, p))

    for k in ("ci_base_html", "client_logo", "output_html", "oauth_token", "numfield_svg"):
        if cfg.get(k):
            cfg[k] = _resolve(cfg[k])
    return cfg


def img_data_uri(path):
    """画像をdata URI化(HTMLを単一ファイルで完結させ、Drive取込・PDF印刷を安定させる)。"""
    ext = os.path.splitext(path)[1].lstrip(".").lower() or "png"
    mime = {"svg": "svg+xml", "jpg": "jpeg"}.get(ext, ext)
    with open(path, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


def load_ci_head(ci_base_html, title, lockup_id="lockup"):
    """
    CI基盤HTMLから **ロックアップsymbol(ブランド資産)だけ** を流用し、CSSは
    <!--CI_HEAD--> マーカーとして残すHEADを組む。マーカーは inject_ci_head()
    (＝正典 ci_head.style_block()・V3.2_FORMAT 1.6)で置換してから出力すること。
    旧方式「基盤HEADのCSSごと複製」は正典改定(Hoefler化・縦罫撤去 等)が自動で
    届かずWELLA世代遅れ事故の温床だったため廃止(2026-07-07)。
    lockup_id: 基盤の <symbol id="..."> のID(標準テンプレ・同梱sampleとも "lk")。
    """
    s = open(ci_base_html, encoding="utf-8").read()
    end = s.find("</symbol>")
    if end < 0:
        raise ValueError(f"CI基盤に <symbol> が見つかりません: {ci_base_html}")
    seg = s[: end + len("</symbol>")]
    start = seg.rfind("<svg")
    if start < 0:
        raise ValueError(f"CI基盤の <symbol> を包む <svg> が見つかりません: {ci_base_html}")
    if f'id="{lockup_id}"' not in seg[start:]:
        raise ValueError(f"CI基盤の <symbol> に id=\"{lockup_id}\" がありません: {ci_base_html}")
    symbol_svg = seg[start:] + "</svg>\n"
    m = re.search(r'<link rel="icon"[^>]*>', s)
    favicon = (m.group(0) + "\n") if m else ""
    return (
        '<!DOCTYPE html>\n<html lang="ja"><head><meta charset="UTF-8">\n'
        f"{favicon}<title>{title}</title>\n<!--CI_HEAD-->\n</head>\n<body>\n{symbol_svg}"
    )


def find_ci_kit():
    """正典 5co-CI-kit の場所を解決する(環境変数 CI_KIT_DIR → 本ファイルから親方向へ探索)。
    見つからなければ例外(fail-closed: 正典CSSなしで黙って組ませない)。"""
    candidates = []
    env = os.environ.get("CI_KIT_DIR")
    if env:
        candidates.append(os.path.abspath(os.path.expanduser(env)))
    p = os.path.dirname(os.path.abspath(__file__))
    while True:
        candidates.append(os.path.join(p, "5co-CI-kit"))
        parent = os.path.dirname(p)
        if parent == p:
            break
        p = parent
    for d in candidates:
        if os.path.isfile(os.path.join(d, "ci_head.py")):
            return d
    raise FileNotFoundError(
        "5co-CI-kit が見つかりません(正典CSS連結に必須)。リポ直下の 5co-CI-kit を確認するか、"
        "環境変数 CI_KIT_DIR でkitのパスを指定してください。")


def inject_ci_head(html):
    """<!--CI_HEAD--> を正典CSS連結 ci_head.style_block() で置換する(V3.2_FORMAT 1.6・
    これ以外の連結方式は禁止)。出力冒頭の版スタンプが「ci_head 経由で組まれた」証跡になる。
    マーカー不在・kitコピー不完全は fail-closed で例外。"""
    if "<!--CI_HEAD-->" not in html:
        raise ValueError("<!--CI_HEAD--> マーカーがありません(load_ci_head を経由してください)")
    kit = find_ci_kit()
    if kit not in sys.path:
        sys.path.insert(0, kit)
    import ci_head
    return html.replace("<!--CI_HEAD-->", ci_head.style_block())


def add_autofigs(html):
    """図の無い本文ページに、表（数値の列→横棒）か箇条書き（対応図・流れ・一覧）から図を自動で添える
    （5co-CI-kit ci_figs.autofig・FIGURES_GUIDE.md 0章「図は既定で使う」）。表も箇条書きも無いページは
    そのまま残る＝仕上げ（ci-finalize.sh）の FIG? で気づける。何度呼んでも二重に入らない。"""
    kit = find_ci_kit()
    if kit not in sys.path:
        sys.path.insert(0, kit)
    import ci_figs
    html, added = ci_figs.autofig(html)
    if added:
        print("自動の図:", ", ".join(f"{n}枚目={k}" for n, k in added))
    return html


# ---------------------------------------------------------------- formatters (IR作法)
def num(s):
    """セル文字列を数値へ。非数値/空はNone。"""
    s = str(s)
    if not s or s in ("–", "-", "-%", "#DIV/0!"):
        return None
    try:
        return float(re.sub(r"[¥,]", "", s))
    except ValueError:
        return None


def rhu(x):
    """四捨五入(round half up・符号対応)。"""
    import math
    return -math.floor(-x + 0.5) if x < 0 else math.floor(x + 0.5)


def mm(s):
    """百万円・小数1桁・カンマ・マイナス△(単位は表頭に書く)。CI: 百万円は0.1まで記載。"""
    n = num(s)
    if n is None:
        return "–" if str(s).strip() in ("", "–", "-", "-%", "#DIV/0!") else str(s)
    v = n / 1e6
    return f"△{abs(v):,.1f}" if v < 0 else f"{v:,.1f}"


def man(s):
    """万円・整数・カンマ(日販など小桁列、単位は表頭)。"""
    n = num(s)
    if n is None:
        return "–" if str(s).strip() in ("", "–", "-", "-%", "#DIV/0!") else str(s)
    v = rhu(n / 1e4)
    return f"△{abs(v):,.0f}" if v < 0 else f"{v:,.0f}"


def f_man(s):
    n = num(s)
    return "–" if n is None else f"{round(n / 1e4):,}"


def f_yen(s):
    n = num(s)
    return "–" if n is None else f"¥{round(n):,}"


def f_cnt(s):
    n = num(s)
    return "–" if n is None else f"{round(n):,}"


def f_pc(s, dec=0):
    """%整形。元が非数値ならそのまま(または–)。"""
    m = re.sub(r"[¥,%]", "", str(s))
    try:
        return f"{float(m):.{dec}f}%"
    except ValueError:
        return str(s) or "–"


# ---------------------------------------------------------------- layout helpers
def _corner(lockup_id):
    return f'<svg class="corner" viewBox="0 0 50.857 36.507"><use href="#{lockup_id}"/></svg>'


def period(text):
    """フッター左の『日進捗・集計期間』1行。text例: '日進捗 <b>70%</b> ・ 集計期間 YYYY-MM-DD〜MM-DD'"""
    return f'<div class="period">{text}</div>'


def header(kicker, title, sub="", *, client_logo_uri, lockup_id="lockup", period_html=""):
    """本文スライドのヘッダ(顧客ロゴ＋キッカー＋タイトル＋アクセントバー＋サブ)。"""
    h = _corner(lockup_id) + period_html
    h += (
        f'<div class="hdr"><img class="client-logo" src="{client_logo_uri}" alt="client logo">'
        f'<span class="kicker">{kicker}</span></div>'
    )
    h += f'<h2 class="title">{title}</h2><div class="accent-bar"></div>'
    if sub:
        h += f'<p class="sub">{sub}</p>'
    return h


def _canonical_cover_ci():
    """正典 ci_head.cover_ci_block() を解決して返す（表紙CIコンセプトの単一情報源）。
    kit 未検出は fail-closed（find_ci_kit が例外＝コンセプトなしで黙って組ませない）。"""
    kit = find_ci_kit()
    if kit not in sys.path:
        sys.path.insert(0, kit)
    import ci_head
    return ci_head.cover_ci_block()


def cover(kicker, title_html, lead_html, *, client_logo_uri, lockup_id="lockup",
          ci_concept_html=None):
    """表紙(数字フィールド背景＋顧客ロゴ＋5coロックアップ＋タイトル＋CIコンセプト)。

    ci_concept_html を省略すると正典のCIコンセプト(ci_head.cover_ci_block)を必ず載せる
    ＝**表紙CIコンセプト必須ルール**（V3.2_FORMAT・全CIスライド規則）。ブランド概念以外の
    理由で上書きしない（属人的な手書き文言はドリフト源）。"""
    ci_block = _canonical_cover_ci() if ci_concept_html is None else ci_concept_html
    return f"""<section class="slide cover-full">
  <div class="numfield-full"></div>
  <div class="cf-corner"><svg viewBox="0 0 50.857 36.507"><use href="#{lockup_id}"/></svg></div>
  <div class="cf-logo"><img src="{client_logo_uri}" alt="client logo" style="width:100%"></div>
  <div class="cf-block">
    <span class="kicker">{kicker}</span>
    <h1>{title_html}</h1>
    <p class="lead">{lead_html}</p>
  </div>
{ci_block}
</section>"""


def divider(secno, title, sub, *, lockup_id="lockup"):
    """章扉(dark・左に縦バー)。"""
    return (
        f'<section class="slide dark divider">{_corner(lockup_id)}'
        f'<div class="dv-bar"></div><div><span class="secno">{secno}</span>'
        f'<h2 class="dv-title">{title}</h2><p class="dv-sub">{sub}</p></div></section>'
    )


def pd_divider(secno, title, sub_html, *, lockup_id="lockup"):
    """章扉(表紙の数字フィールド背景に扉レイアウトの文字をノセ・明色背景=ink文字)。"""
    return f"""<section class="slide cover-full pd-divider">
  <div class="numfield-full"></div>
  <div class="cf-corner"><svg viewBox="0 0 50.857 36.507"><use href="#{lockup_id}"/></svg></div>
  <div class="pd-text"><div class="dv-bar"></div><div><span class="secno">{secno}</span>
    <h2 class="dv-title">{title}</h2>
    <p class="dv-sub">{sub_html}</p></div>
  </div>
</section>"""


def oknode(name, target, actual, forecast, mark, cls="", shr=""):
    """OKRツリーのノード(目標/実績/見込を別の四角に分割)。mark: 'ok'(○) or 'bh'(△)。"""
    sh = f'<span class="shr">{shr}</span>' if shr else ""
    return (
        f'<div class="nd {cls}"><span class="nm">{name}{sh}</span>'
        f'<div class="box"><span class="lbl">目標</span>{target}</div>'
        f'<div class="box"><span class="lbl">実績</span>{actual}</div>'
        f'<div class="box mk"><span class="lbl">見込</span>{forecast} <span class="{mark}"></span></div></div>'
    )


# ---------------------------------------------------------------- render / export
def numfield_style(svg_path, opacity=0.75):
    """
    表紙(cover-full)・PD章扉の全面数字フィールド背景。CI基盤は assets/ を相対参照するため
    単一HTMLでは表示されない → CI正本の numfield SVG を data URI で埋め込む(実デッキと同方式)。
    svg_path が無ければ空文字を返す(数字背景なしで動作継続)。
    """
    if not svg_path or not os.path.exists(svg_path):
        return ""
    uri = img_data_uri(svg_path)
    return ("<style>.cover-full .numfield-full,.cover-full.pd-divider .numfield-full{"
            f'position:absolute;inset:0;z-index:0;pointer-events:none;background-image:url("{uri}");'
            f"background-size:cover;background-position:center;opacity:{opacity};}}</style>")


def render(head_html, slides, *, tail="\n</body>\n</html>\n", extra_head=""):
    """HEAD ＋ EXTRA_CSS ＋ 追加head ＋ スライド列 ＋ TAIL を結合して完成HTMLを返す。"""
    return head_html + EXTRA_CSS + (extra_head or "") + "\n".join(slides) + tail


def to_pdf(html_path, pdf_path, chrome=None):
    """Chrome --headless --print-to-pdf でA4横PDFを出力(任意・印刷確認用)。"""
    candidates = [chrome] if chrome else [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome", "chromium", "chromium-browser",
    ]
    for exe in candidates:
        if not exe:
            continue
        try:
            subprocess.run(
                [exe, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                 f"--print-to-pdf={pdf_path}", f"file://{os.path.abspath(html_path)}"],
                check=True, capture_output=True,
            )
            return pdf_path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("Chromeが見つからずPDF化に失敗。chrome引数で実行パスを指定してください。")


# ---------------------------------------------------------------- EXTRA CSS (本デッキ固有のみ・正典重複は持たない)
EXTRA_CSS = r"""
<style>
/* --- 週次デッキ固有の上書き（正典 ci_head 連結の後段に適用） ---
   正典 ci-format-v3.2.css と宣言まで一致するルールは削除済み（2026-07-07 ci_head 移行）。
   ここに残すのは (a) 正典に無い案件固有ルール と (b) 週次デッキの確定した見た目を
   維持する意図的上書き（正典と値が異なる行）のみ。正典改定への追従は ci_head が担う。
   白混ぜの濃淡(#DEE9F6/#F0F5FB)は3色CIの許容範囲。 */
/* ヘッダー＝クライアントロゴ＋キッカーを横並び(ロゴを少し下げ、キッカーは右隣)。
   margin-top 18px は本デッキ確定値（正典は 0） */
.hdr{display:flex; align-items:center; gap:20px; margin:18px 0 6px;}
.hdr .client-logo{height:34px; width:auto; display:block;}
/* ヘッダー右上の5coロゴ：本ビルダーは .corner をemitするため position:absolute を自前指定
   (これが無いと左上にインライン表示で崩れる)。top:78px＝左ブロックと天地を揃えた確定位置 */
svg.corner{position:absolute; top:78px; right:50px; width:102px; height:auto; display:block;
  color:var(--ink); fill:currentColor; z-index:3;}
/* PD章扉の地色＝crystal（週次デッキ確定の見た目。正典は白地＋数字フィールドに改定済みだが
   本デッキは表紙と同じ crystal 地に数字フィールドをノセる構成を維持する意図的上書き） */
.cover-full.pd-divider{background:var(--crystal);}
/* ダーク地スライド：地色・フッターは正典 .slide.dark。子要素の配色のみ本デッキで補完 */
.slide.dark h1,.slide.dark h2,.slide.dark h3,.slide.dark .title{color:var(--crystal);}
.slide.dark .kicker,.slide.dark .sub,.slide.dark small,.slide.dark .note{color:rgba(195,215,238,.78);}
.slide.dark .accent-bar,.slide.dark ul.clean li::before{background:var(--crystal);}
.slide.dark svg.corner{color:var(--crystal);}
/* OKRツリー：本デッキ確定の微調整（コネクタ罫1.5px・ラベル/凡例の濃度=ink-60・級数） */
.okr{--ln:var(--ink-60); text-align:center; margin-top:2px;}
.okr li::before,.okr li::after{content:""; position:absolute; top:0; right:50%; width:50%; height:9px; border-top:1.5px solid var(--ln);}
.okr li::after{right:auto; left:50%; border-left:1.5px solid var(--ln);}
.okr li:last-child::before{border-right:1.5px solid var(--ln);}
.okr ul ul::before{content:""; position:absolute; top:0; left:50%; border-left:1.5px solid var(--ln); width:0; height:9px;}
.okr .nm{font-weight:600; font-size:12.5px; display:block; margin-bottom:4px; text-align:center; color:var(--ink); line-height:1.3;}
.okr .box{border:1pt solid var(--ink-60); border-radius:6px; padding:2px 9px; margin-top:2px; font-size:10.5px; color:var(--ink); line-height:1.4; font-variant-numeric:lining-nums tabular-nums; background:var(--white); white-space:nowrap;}
.okr .box .lbl{display:inline-block; width:30px; color:var(--ink-60); font-size:9.5px;}
.okr .nd.lead{background:var(--ink); border-radius:8px; padding:9px 16px; min-width:0; font-size:inherit; line-height:1.3;}
.okr .nd.lead .nm{color:var(--crystal); text-align:left;}
.okr .nd.lead .box{display:block; margin:4px 0 0 0; background:rgba(195,215,238,.12); border-color:rgba(195,215,238,.60); color:var(--crystal);}
.okr-annual-wrap::after{content:""; display:block; width:0; height:4px; margin:0 auto; border-left:1.5px solid var(--ink-60);}
.okr-legend{color:var(--ink-60); font-size:11px; margin:2px 0 3px;}
.okr-insight .ins-lbl{flex:none; font-size:11px; font-weight:600; color:var(--ink-60); border:1px solid var(--crystal); border-radius:4px; padding:3px 10px;}
.okr-insight .ins-txt{font-size:15px; font-weight:700; color:var(--ink); line-height:1.5;}
.okr .sgrp-row{display:flex; gap:8px; justify-content:center; align-items:flex-end; position:relative; padding-top:9px;}
.okr .sgrp-row::before{content:""; position:absolute; top:0; left:81px; right:81px; border-top:1.5px solid var(--ln);}
.okr .nd .shr{display:block; font-size:8.5px; font-weight:600; color:var(--ink-60); margin-top:1px; line-height:1.2; white-space:nowrap; text-align:center;}
.okr .nd.big .box{font-size:13px; padding:6px 14px; margin-top:5px; border-color:var(--ink-60);}
.okr .nd.cat .shr{font-size:7.5px;}
/* テーブル小見出し・単位注＝ink-60（正典 ink-85 より薄い本デッキ確定濃度） */
.skyu-h{font-size:11px; color:var(--ink-60); margin:0 0 2px 2px; letter-spacing:.04em;}
.sk-unit{text-align:right; font-size:9px; color:var(--ink-60); margin:0 2px 3px 0; letter-spacing:.02em; line-height:1.4;}
table.sk.wide th,table.sk.wide td{padding:1px 2px;}
table.sk.dsp3 th,table.sk.dsp3 td{padding:1px 2px;}
/* 罫線ルール：横線のみ(下罫線)・縦線は使わない。font-family/size:inherit で基盤の
   th,td 直指定を打ち消す(これが無いと明朝・巨大化で列が切れる) */
table.sk th,table.sk td{border:none; border-bottom:1pt solid var(--ink-60); padding:1px 3px; text-align:right; white-space:nowrap; line-height:1.2; vertical-align:middle; font-size:inherit; font-family:inherit;}
table.sk td.dim{color:var(--ink-60);}
/* 所見カード見出し＝ink-60（正典 ink-85 より薄い本デッキ確定濃度） */
.sho-card .sho-h{border-left:0; padding-left:0; font-size:13px; color:var(--ink-60); font-weight:600; letter-spacing:.1em;}
/* 日進捗・集計期間(フッターCONFIDENTIALの左隣に1行)＝ink-60 */
.period{position:absolute; bottom:15px; left:36px; white-space:nowrap; font-family:var(--serif-en);
  font-size:11px; letter-spacing:.04em; color:var(--ink-60); z-index:3;}
.notemk{font-size:11.5px; color:var(--ink-60); margin-top:6px;}
</style>
"""
