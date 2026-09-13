#!/usr/bin/env python3
"""
ci_head.py — 正典CSS連結の唯一の標準方式（共通HEAD）

案件ビルダー（NatureLab build_html_monthly.py / WELLA 等）が、正典フォーマットCSSを
**コピー・inline再実装せずに**デッキHTMLへ注入するための共有ヘルパ。

なぜ存在するか（2026-07-07 WELLA 世代遅れ事故・共通HEAD化依頼）:
  各案件が正典CSSを手元へコピー／自前再実装すると、正典の改定（#642 Hoefler化・
  #709 縦罫撤去 等）が自動では届かず、案件ごとに「連結方式の即興実装」が新たな
  ドリフト源になる。連結方式を正典側で1つに固定し、全案件が同一方式で消費する。

設計原則:
  - **VERSION が唯一の宣言源**。連結対象CSSは本スクリプトにハードコードせず、
    VERSION の `format:` 行から読む（版上げ時は VERSION 更新だけで全案件に追従）。
  - 本スクリプトは kit 内に置かれ、自分の場所（__file__）から kit を特定する
    （git派生リポでも Drive 案件コピーでも、kit ごと配布されるためパス設定不要）。
  - 出力の先頭に版スタンプコメントを焼き込む（「ci_head 経由で組まれたか」を
    parity 検査・監査で機械判定できるマーカー）。

使い方（案件ビルダー側・これ以外の連結方式は禁止）:
  # Python から（推奨）
  import sys; sys.path.insert(0, "<kitへのパス>")   # 例: "5co-CI-kit"
  import ci_head
  html = template.replace("<!--CI_HEAD-->", ci_head.style_block())

  # subprocess / シェルから
  python3 5co-CI-kit/ci_head.py            # <style>…</style> ブロックを stdout へ
  python3 5co-CI-kit/ci_head.py --css      # 生CSSのみ（<style>タグなし）
  python3 5co-CI-kit/ci_head.py --files    # 連結対象ファイル一覧
  python3 5co-CI-kit/ci_head.py --version  # 現行版タグ（例: v3.3）
  python3 5co-CI-kit/ci_head.py --cover-ci # 表紙CIコンセプトブロック（.cover-ci・全表紙必須）
  python3 5co-CI-kit/ci_head.py --lang en  # 英語版（多言語版）の級数スケールを連結（既定0.85倍）
  python3 5co-CI-kit/ci_head.py --lang en --lang-scale 0.8   # 実測で足りなければ段階的に下げる

多言語版（v3.8・B-8）:
  英語は同じ内容でも和文より2〜3割長く、v3.7 の級数のままでは英語版が 23枚中20枚はみ出した。
  縮め方を正典に置き（ci-lang-v3.8.css・VERSION の lang: 行）、--lang を指定したときだけ連結する。
  **--lang を付けない出力は v3.7 以前と1バイトも変わらない**（日本語版の見た目は不変）。
  インラインの font-size は CSS では縮められないので scale_inline_font_sizes() を通すこと。

終了コード: 0=成功 / 1=VERSION不在・宣言CSS欠落（fail-closed: 欠けたまま黙って
組ませない）
"""
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent


def _version_text() -> str:
    vf = KIT / "VERSION"
    if not vf.exists():
        raise FileNotFoundError(
            f"VERSION が見つかりません: {vf}（kit コピーが不完全。正典から再取得してください）"
        )
    return vf.read_text(encoding="utf-8")


def version_tag() -> str:
    """VERSION 先頭行の版タグ（例: 'v3.3'）。"""
    return _version_text().splitlines()[0].strip()


def css_files() -> list:
    """VERSION の format: 行に宣言された CSS ファイル群（宣言順・kit相対）。"""
    m = re.search(r"^format:\s*(.+)$", _version_text(), re.MULTILINE)
    if not m:
        raise ValueError("VERSION に format: 行がありません（正典の宣言形式が変わった場合は本ヘルパも追従させること）")
    names = re.findall(r"[\w][\w.-]*\.css", m.group(1))
    if not names:
        raise ValueError("VERSION の format: 行に .css 宣言がありません")
    missing = [n for n in names if not (KIT / n).exists()]
    if missing:
        raise FileNotFoundError(
            f"VERSION 宣言のCSSが kit に見つかりません: {', '.join(missing)}（kit コピーが不完全）"
        )
    return names


def head_css() -> str:
    """現行フォーマットCSS（VERSION宣言・宣言順）を連結して返す（生CSS）。"""
    parts = []
    for name in css_files():
        body = (KIT / name).read_text(encoding="utf-8")
        parts.append(f"/* ==== {name}（正典 5co-CI-kit・編集禁止） ==== */\n{body}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------- 多言語版の級数（v3.8・B-8）
# 英語は同じ内容でも和文より2〜3割長く、v3.7 の級数のままだと英語版は 23枚中20枚が
# はみ出した（実測 2026-09-07）。案件ごとに違う縮め方をするとドリフトになるため、
# 縮め方を正典に置き、`--lang` を指定したときだけ連結する（日本語版の出力は不変）。
DEFAULT_LANG_SCALE = {"ja": 1.0, "en": 0.85}


def lang_css_file() -> str:
    """VERSION の lang: 行が宣言する多言語CSS（無ければ空文字）。"""
    m = re.search(r"^lang:\s*(.+)$", _version_text(), re.MULTILINE)
    if not m:
        return ""
    names = re.findall(r"[\w][\w.-]*\.css", m.group(1))
    if not names:
        return ""
    if not (KIT / names[0]).exists():
        raise FileNotFoundError(f"VERSION 宣言の多言語CSSが kit に見つかりません: {names[0]}（kit コピーが不完全）")
    return names[0]


def lang_css(lang: str, scale: float = None) -> str:
    """多言語CSS＋スケール確定値。lang='ja'（既定）なら空文字＝何も足さない。"""
    if not lang or lang == "ja":
        return ""
    name = lang_css_file()
    if not name:
        raise ValueError("VERSION に lang: 行がありません（多言語版の級数を宣言してください）")
    if scale is None:
        scale = DEFAULT_LANG_SCALE.get(lang, DEFAULT_LANG_SCALE["en"])
    body = (KIT / name).read_text(encoding="utf-8")
    # スケール確定値を後段で焼き込む＝html の lang 属性に依存せず決定論的にする。
    # 詳細度に注意（Codex astra 指摘・2026-09-09）: CSS 側の保険 `:root[lang="en"]` は (0,1,1) で、
    # 素の `:root{}` (0,1,0) より強い。<html lang="en"> のデッキで --lang-scale 0.8 を指定しても
    # 0.85 に固定されてしまうため、同じ詳細度以上のセレクタで、かつ後段に出す。
    return (f"/* ==== {name}（正典 5co-CI-kit・編集禁止） ==== */\n{body}\n"
            f"/* lang={lang} のスケール確定値（ci_head.py が焼き込み・CSS側の保険より優先） */\n"
            f":root, :root[lang], .lang-en{{--lang-scale:{scale:g};}}")


_INLINE_FS = re.compile(r"(font-size\s*:\s*)([\d.]+)px")


def scale_inline_font_sizes(html: str, scale: float) -> str:
    """HTML 内のインライン `font-size:NNpx` を同率で縮める（CSSでは縮められないため）。

    英語版で実際に必要だった処理。ビルダー側で最後に1回通す。
    `<style>` ブロックは対象外（正典CSSを書き換えないため）。
    """
    def repl(m):
        return f"{m.group(1)}{round(float(m.group(2)) * scale, 2):g}px"
    out, last = [], 0
    for m in re.finditer(r"<style\b.*?</style>", html, re.S | re.I):
        out.append(_INLINE_FS.sub(repl, html[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(_INLINE_FS.sub(repl, html[last:]))
    return "".join(out)


def style_block(lang: str = "ja", scale: float = None) -> str:
    """HEADに挿入する <style> ブロック。先頭の版スタンプが ci_head 経由の証跡になる。

    lang を指定すると多言語CSS（VERSION の lang: 行）を末尾に連結する。
    既定（ja）の出力は v3.7 以前と1バイトも変わらない。
    """
    tag = version_tag()
    files = " + ".join(css_files())
    extra = lang_css(lang, scale)
    if extra:
        files += f" + {lang_css_file()}(lang={lang})"
    stamp = (
        f"/* 5co-CI ci_head {tag} — {files}\n"
        f"   正典連結（5co-CI-kit/ci_head.py 生成・手編集禁止・CSSコピー/inline再実装禁止） */"
    )
    body = head_css() + (f"\n\n{extra}" if extra else "")
    return f"<style>\n{stamp}\n{body}\n</style>"


# ---------------------------------------------------------------- 表紙CIコンセプト（正典・単一情報源）
# 全案件の表紙に載せる「CIコンセプト説明」の正典テキスト。共有ビルダー(ci_v2_lib.cover)も
# bespoke ビルダー(build_html_monthly.py / build_w1_july.py 等)も、ここを唯一の情報源として
# 参照する（属人的な手書き＝ドリフト源を禁止）。既定文言はブランド正典 LOGO_HANDOFF.md §4
# （水晶玉＝市場を透視する5・Strategy, refined.）に基づく。
# ※ 文言は 5co ブランド概念のみで顧客データを含まない（Tier0 安全・kit へ格納可）。
#    改定は本リポの PR 経由のみ（VERSION 由来のCSS `.cover-ci` と対で運用）。
COVER_CI_TAGLINE = "水晶玉で市場を透視し、戦略を磨く。"
COVER_CI_BODY = (
    "2026年7月に刷新したロゴマークは、複雑な市場を見通す「水晶玉」と社名の「5」を"
    "一体にしたシンボルです。<br>曇りのない視点でデータの奥にある本質を捉え、"
    "戦略を磨き続ける。――「Strategy, refined.」に込めた5coの姿勢を表しています。"
)


def cover_ci_block(tagline: str = COVER_CI_TAGLINE, body: str = COVER_CI_BODY) -> str:
    """表紙に載せるCIコンセプト説明ブロック（`.cover-ci`）を返す。

    全案件の表紙(cover-full・章扉 pd-divider は除く)に**必須**（V3.2_FORMAT「表紙CIコンセプト」・
    全CIスライド規則）。正典CSS `.cover-ci` / `.cover-ci-h` に対応する固定マークアップ。
    既定文言はブランド正典（LOGO_HANDOFF.md §4）。ブランド概念以外の理由で上書きしない。
    """
    return f'<div class="cover-ci"><span class="cover-ci-h">{tagline}</span>{body}</div>'


def _opt(argv, name, cast=str, default=None):
    if name in argv and argv.index(name) + 1 < len(argv):
        return cast(argv[argv.index(name) + 1])
    return default


def main(argv):
    try:
        lang = _opt(argv, "--lang", str, "ja")
        scale = _opt(argv, "--lang-scale", float, None)
        if "--version" in argv:
            print(version_tag())
        elif "--files" in argv:
            names = css_files() + ([lang_css_file()] if lang != "ja" and lang_css_file() else [])
            print("\n".join(names))
        elif "--cover-ci" in argv:
            print(cover_ci_block())
        elif "--css" in argv:
            extra = lang_css(lang, scale)
            print(head_css() + (f"\n\n{extra}" if extra else ""))
        else:
            print(style_block(lang, scale))
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"NG: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        # `ci_head.py | head` 等でパイプ先が先に閉じた場合は正常終了扱い
        sys.exit(0)
