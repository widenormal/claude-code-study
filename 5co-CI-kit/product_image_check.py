#!/usr/bin/env python3
"""
product_image_check.py — 商品名・ASIN が出るスライドに商品画像があるか（警告）

規定（FIGURES_GUIDE §2-1「商品名・ASIN が出るときの商品画像」）:
  特定の商品名・ASIN／商品コードを示すページでは、代表商品の商品写真を
  data:image 埋め込みで置く。無いときは data-product-img-exempt="理由"。
  ロゴ（.cl-logo 等）やダイジェスト写真（dg-photo / figs/digest）だけでは足りない。
  外部 URL の画像は不可（ci_figs lint と同趣旨）。

検出:
  - ASIN: B0… および「ASIN:」ラベル付きコード（従来どおり）
  - 商品名: Latin の CamelCase／PascalCase（大文字まとまり≥2・長さ≥6）。
    例: NailEnvy, InfiniteShine, NatureStrong, NailLacquer, RapiDry。
    非商品の頻出語は denylist で除外。

使い方:
  python3 product_image_check.py <deck.html> [<deck.html> …]
  python3 product_image_check.py --warn-only <deck.html>   # 所見あっても exit 0
  python3 product_image_check.py --selftest

終了: 0=OK（または warn-only） / 1=所見あり / 2=引数誤り
出力の所見行は PRODUCT_IMG? で始まる（ci-gates の警告表示用）。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Amazon ASIN: prefer B0… (common retail) to limit false positives;
# also codes next to the literal "ASIN".
RE_ASIN_B0 = re.compile(r"\b(B0[A-Z0-9]{8})\b")
RE_ASIN_LABELED = re.compile(
    r"ASIN\s*[:：]?\s*([A-Z0-9]{10})\b", re.IGNORECASE
)
# CamelCase / PascalCase product-style: ≥2 capital groups (each with
# lowercase letters), length ≥6. Latin-only edges so CJK adjacency
# (例: NailEnvy閲覧) still matches; avoids YoY106-style digit tails.
RE_CAMEL_PRODUCT = re.compile(
    r"(?<![A-Za-z0-9])([A-Z][a-z]+(?:[A-Z][a-z]+)+)(?![A-Za-z0-9])"
)
RE_SECTION = re.compile(
    r"(<section\b[^>]*>)(.*?)(</section>)",
    re.IGNORECASE | re.DOTALL,
)
RE_IMG_TAG = re.compile(r"<img\b([^>]*)/?>", re.IGNORECASE)
RE_EXEMPT = re.compile(r"\bdata-product-img-exempt\s*=", re.IGNORECASE)
RE_SLIDE_ID = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
RE_ATTR = re.compile(
    r"""(?:^|\s)(src|alt|class)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""",
    re.IGNORECASE,
)
RE_LOGO_HINT = re.compile(r"(?i)logo|cl-logo|corner")
RE_DIG_HINT = re.compile(r"(?i)dg-photo|figs/digest")
RE_PRODUCT_PATH = re.compile(r"(?i)product|sku|asin|/figs/[^\"']*prod")

# Common non-product CamelCase / Title tokens (and kit noise)
PRODUCT_NAME_DENY: frozenset[str] = frozenset(
    {
        "Amazon",
        "Summary",
        "Agenda",
        "Follow",
        "Review",
        "Flash",
        "Progress",
        "Advertising",
        "Sponsored",
        "Google",
        "Chrome",
        "Strategy",
        "Objective",
        "Retail",
        "Meeting",
        "Results",
        "Infinite",
        "Nature",
        "Strong",
        "Overview",
        "Analysis",
        "Performance",
        "Campaign",
        "Content",
        "Report",
        "Target",
        "Market",
        "Share",
        "Brand",
        "Category",
        "Product",
        "Series",
        "Update",
        "Status",
        "Action",
        "Plan",
        "Focus",
        "Issue",
        "Solution",
        "Background",
        "Appendix",
        "Reference",
        "Total",
        "Average",
        "Growth",
        "Revenue",
        "Sales",
        "Traffic",
        "Conversion",
        "Impression",
        "Click",
        "Budget",
        "Spend",
        "Margin",
        "Profit",
        "Volume",
        "Price",
        "Rank",
        "Search",
        "Keyword",
        "Listing",
        "Inventory",
        "Shipment",
        "Order",
        "Customer",
        "Seller",
        "Vendor",
        "Partner",
        "Agency",
        "Client",
        "Weekly",
        "Monthly",
        "Quarterly",
        "Annual",
        "Fiscal",
        "PowerPoint",
        "JavaScript",
        "TypeScript",
        "GitHub",
        "YouTube",
        "LinkedIn",
        "FaceBook",
        "Instagram",
        "WhatsApp",
        "DataSource",
        "PageView",
        "HomePage",
        "SlideShow",
        "NextSteps",
        "KeyResults",
        "KeyResult",
        "Shelpha",
        "Ignite",
        "Oracle",
        "Crystal",
        "Footer",
        "Header",
        "Title",
        "Section",
        "Document",
        "Template",
        "Version",
        "ChangeLog",
        "SelfTest",
        "FalsePositive",
        "TruePositive",
        "WhiteSpace",
        "CamelCase",
        "PascalCase",
        "UpperCase",
        "LowerCase",
        "Base64",
        "JavaScript",
        "TypeScript",
        "NodeJs",
        "OpenAI",
        "ChatGPT",
        "DeepDive",
        "FollowUp",
        "CheckIn",
        "RollOut",
        "KickOff",
        "SignOff",
        "HandOff",
        "WorkFlow",
        "TimeLine",
        "RoadMap",
        "BenchMark",
        "DashBoard",
        "ScoreCard",
        "HeatMap",
        "Funnel",
        "WaterFall",
        "SlideDeck",
        "PageCount",
        "WordCount",
        "FileName",
        "FilePath",
        "FullWidth",
        "HalfWidth",
        "LeftAlign",
        "RightAlign",
        "TextAlign",
        "FontSize",
        "LineHeight",
        "BorderRadius",
        "BoxShadow",
        "BackGround",
        "ForeGround",
        "StyleSheet",
        "ClassName",
        "DataAttr",
        "AriaLabel",
        "AltText",
        "SrcSet",
        "LazyLoad",
        "AutoPlay",
        "PlayBack",
        "TimeStamp",
        "DateTime",
        "TimeZone",
        "UtcOffset",
        "AsiaTokyo",
        "UnitedStates",
        "NewYork",
        "SanFrancisco",
        "LosAngeles",
        "HongKong",
        "SouthKorea",
        "NorthAmerica",
        "LatinAmerica",
        "MiddleEast",
        "SouthEast",
        "WestCoast",
        "EastCoast",
        "PrimeDay",
        "BlackFriday",
        "CyberMonday",
        "NewYear",
        "YearOverYear",
        "MonthOverMonth",
        "WeekOverWeek",
        "DayOverDay",
        "YearToDate",
        "MonthToDate",
        "ClickThrough",
        "AddToCart",
        "BuyBox",
        "BestSeller",
        "TopSeller",
        "NewRelease",
        "AlsoBought",
        "SponsoredProducts",
        "SponsoredBrands",
        "SponsoredDisplay",
        "ProductAds",
        "BrandAds",
        "DisplayAds",
        "SearchAds",
        "RetailMedia",
        "MediaMix",
        "ShareOfVoice",
        "ShareOfSearch",
        "ShareOfShelf",
        "OutOfStock",
        "InStock",
        "OnHand",
        "LeadTime",
        "ShipDate",
        "OrderId",
        "SkuId",
        "AsinCode",
        "ProductCode",
        "ProductName",
        "ProductImage",
        "ProductPhoto",
        "ProductShot",
        "HeroImage",
        "ThumbNail",
        "ScreenShot",
        "CutOut",
        "DigPhoto",
        "CornerLogo",
        "ClientLogo",
        "BrandLogo",
        "CompanyLogo",
        "CustomerAcquisition",
        "NewCustomer",
        "NewCustomers",
        "CrossSell",
        "UpSell",
        "Retargeting",
        "Remarketing",
        "BrandAwareness",
        "MarketShare",
        "DetailPage",
        "SearchTerm",
        "SearchQuery",
        "AutoTarget",
        "ManualTarget",
        "ExactMatch",
        "BroadMatch",
        "PhraseMatch",
        "NegativeKeyword",
        "BidStrategy",
        "BudgetPacing",
        "AdGroup",
        "AdCreative",
        "LandingPage",
        "ProductPage",
        "StoreFront",
        "BrandStore",
        "TopOfSearch",
        "MustWin",
        "MustHave",
        "TopLine",
        "BottomLine",
        "TopFunnel",
        "MidFunnel",
        "LowFunnel",
        "FullFunnel",
        "AlwaysOn",
        "OneTime",
        "InHouse",
        "ThirdParty",
        "FirstParty",
        "LookAlike",
        "HighIntent",
        "LowIntent",
        "NewToBrand",
        "NewToCategory",
    }
)


def _attr_map(attrs: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in RE_ATTR.finditer(attrs):
        key = m.group(1).lower()
        val = m.group(2) if m.group(2) is not None else (
            m.group(3) if m.group(3) is not None else (m.group(4) or "")
        )
        out[key] = val
    return out


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _asins_in(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for m in RE_ASIN_B0.finditer(text):
        code = m.group(1)
        if code not in seen:
            seen.add(code)
            found.append(code)
    for m in RE_ASIN_LABELED.finditer(text):
        code = m.group(1).upper()
        if code not in seen:
            seen.add(code)
            found.append(code)
    return found


def _product_names_in(text: str) -> list[str]:
    """Latin CamelCase／PascalCase product-style tokens (tags already stripped)."""
    found: list[str] = []
    seen: set[str] = set()
    for m in RE_CAMEL_PRODUCT.finditer(text):
        tok = m.group(1)
        if len(tok) < 6:
            continue
        if tok in PRODUCT_NAME_DENY:
            continue
        if tok not in seen:
            seen.add(tok)
            found.append(tok)
    return found


def _is_logo_or_dig(attrs: str, src: str, alt: str, cls: str) -> bool:
    if RE_LOGO_HINT.search(cls) or RE_LOGO_HINT.search(alt):
        return True
    blob = f"{attrs} {src} {alt} {cls}"
    if RE_DIG_HINT.search(blob):
        return True
    return False


def _has_product_image(
    section_html: str, product_names: list[str] | None = None
) -> bool:
    """True only for a non-logo, non-dig product image evidence."""
    names = set(product_names or [])
    for m in RE_IMG_TAG.finditer(section_html):
        attrs = m.group(1) or ""
        am = _attr_map(attrs)
        src = am.get("src", "")
        alt = am.get("alt", "")
        cls = am.get("class", "")
        if _is_logo_or_dig(attrs, src, alt, cls):
            continue
        src_l = src.lower()
        if src_l.startswith("data:image"):
            return True
        if alt and alt in names:
            return True
        if src and not src_l.startswith(("http://", "https://", "//")):
            if RE_PRODUCT_PATH.search(src) or (
                Path(src).stem in names if src else False
            ):
                return True
    return False


def _section_label(open_tag: str, index: int) -> str:
    m = RE_SLIDE_ID.search(open_tag)
    if m:
        return m.group(1)
    return f"section#{index}"


def _warn_line(path: str, label: str, asins: list[str], names: list[str]) -> str:
    if asins:
        return (
            f"{path}: PRODUCT_IMG? ({label}) ASIN {', '.join(asins)} に商品画像"
            "（img / data:image）が無い"
            " — 埋め込むか data-product-img-exempt=\"理由\""
        )
    return (
        f"{path}: PRODUCT_IMG? ({label}) 商品名 {', '.join(names)} に商品画像が無い"
        " — 埋め込むか data-product-img-exempt=\"理由\""
    )


def check_html(text: str, path: str) -> list[str]:
    """Return PRODUCT_IMG? warning lines (empty = OK)."""
    issues: list[str] = []
    # Strip script/style so ASIN-looking tokens in CSS/JS don't fire
    scrubbed = re.sub(
        r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.DOTALL
    )
    scrubbed = re.sub(
        r"<style\b[^>]*>.*?</style>", " ", scrubbed, flags=re.I | re.DOTALL
    )

    sections = list(RE_SECTION.finditer(scrubbed))
    if not sections:
        # Flat HTML without section tags: treat whole body as one unit
        if RE_EXEMPT.search(scrubbed):
            return issues
        visible = _strip_tags(scrubbed)
        asins = _asins_in(visible)
        names = _product_names_in(visible)
        if (asins or names) and not _has_product_image(scrubbed, names):
            issues.append(_warn_line(path, "document", asins, names))
        return issues

    for i, m in enumerate(sections, start=1):
        open_tag, body = m.group(1), m.group(2)
        whole = open_tag + body
        if RE_EXEMPT.search(whole):
            continue
        visible = _strip_tags(whole)
        asins = _asins_in(visible)
        names = _product_names_in(visible)
        if not asins and not names:
            continue
        if _has_product_image(whole, names):
            continue
        label = _section_label(open_tag, i)
        issues.append(_warn_line(path, label, asins, names))
    return issues


def selftest() -> int:
    ok = True

    good = """
    <section class="slide" id="p3">
      <p>ASIN: B0TEST1234 の商品</p>
      <img src="data:image/jpeg;base64,/9j/4AAQ" alt="product">
    </section>
    """
    if check_html(good, "good.html"):
        print("SELFTEST FAIL: good (with data:image) should pass")
        ok = False

    exempt = """
    <section class="slide" id="p4" data-product-img-exempt="付録の一覧のみ">
      <p>B0ABCDEF12</p>
    </section>
    """
    if check_html(exempt, "exempt.html"):
        print("SELFTEST FAIL: exempt should pass")
        ok = False

    bad = """
    <section class="slide" id="p5">
      <p>対象 ASIN B0XYZABCDE の売上</p>
    </section>
    """
    bad_issues = check_html(bad, "bad.html")
    if not bad_issues or "PRODUCT_IMG?" not in bad_issues[0]:
        print("SELFTEST FAIL: bad should warn PRODUCT_IMG?", bad_issues)
        ok = False
    if bad_issues and "B0XYZABCDE" not in bad_issues[0]:
        print("SELFTEST FAIL: ASIN code missing in warning", bad_issues)
        ok = False

    labeled = """
    <section class="slide" id="p6">
      <p>ASIN: A1B2C3D4E5</p>
    </section>
    """
    lab_issues = check_html(labeled, "lab.html")
    if not lab_issues or "A1B2C3D4E5" not in lab_issues[0]:
        print("SELFTEST FAIL: labeled ASIN should warn", lab_issues)
        ok = False

    # False-positive guard: random 10-char without B0 / ASIN label should not fire
    noise = """
    <section class="slide" id="p7"><p>CODE12345X だけの表</p></section>
    """
    if check_html(noise, "noise.html"):
        print("SELFTEST FAIL: unlabeled non-B0 token should not warn")
        ok = False

    # Product name without image → warn
    name_bad = """
    <section class="slide" id="p05">
      <p>宿題: NailEnvy / InfiniteShine / NatureStrong</p>
    </section>
    """
    name_bad_issues = check_html(name_bad, "name_bad.html")
    if (
        not name_bad_issues
        or "PRODUCT_IMG?" not in name_bad_issues[0]
        or "商品名" not in name_bad_issues[0]
        or "NailEnvy" not in name_bad_issues[0]
    ):
        print("SELFTEST FAIL: product name without image should warn", name_bad_issues)
        ok = False

    # Name + non-logo data:image with matching alt → pass
    name_good = """
    <section class="slide" id="p04">
      <p>NailEnvy の動向</p>
      <img src="data:image/jpeg;base64,/9j/4AAQ" alt="NailEnvy">
    </section>
    """
    if check_html(name_good, "name_good.html"):
        print("SELFTEST FAIL: name + matching data:image should pass")
        ok = False

    # Name + only cl-logo → warn
    name_logo = """
    <section class="slide" id="p08">
      <p>InfiniteShine シリーズ</p>
      <img class="cl-logo" src="data:image/png;base64,iVBORw0" alt="OPI">
    </section>
    """
    name_logo_issues = check_html(name_logo, "name_logo.html")
    if not name_logo_issues or "InfiniteShine" not in name_logo_issues[0]:
        print("SELFTEST FAIL: name + only cl-logo should warn", name_logo_issues)
        ok = False

    # CamelCase denylist word alone → no warn
    deny = """
    <section class="slide" id="p9"><p>NextSteps と KeyResults</p></section>
    """
    if check_html(deny, "deny.html"):
        print("SELFTEST FAIL: denylist CamelCase should not warn")
        ok = False

    # Dig photo must not count as product image
    dig = """
    <section class="slide" id="p10">
      <p>NatureStrong の説明</p>
      <img class="dg-photo" src="figs/digest/scenes/cutouts/slide/x.png" alt="scene">
    </section>
    """
    dig_issues = check_html(dig, "dig.html")
    if not dig_issues or "NatureStrong" not in dig_issues[0]:
        print("SELFTEST FAIL: dig photo should not satisfy product image", dig_issues)
        ok = False


    # CJK-adjacent Latin product names must still detect
    cjk = """
    <section class="slide" id="p05b">
      <p>NailEnvy閲覧者への配信、NailLacquerでの代替</p>
    </section>
    """
    cjk_issues = check_html(cjk, "cjk.html")
    if (
        not cjk_issues
        or "NailEnvy" not in cjk_issues[0]
        or "NailLacquer" not in cjk_issues[0]
    ):
        print("SELFTEST FAIL: CJK-adjacent product names should warn", cjk_issues)
        ok = False

    # YoY106-style digit CamelCase must not warn
    yoy = """
    <section class="slide" id="pY"><p>必達比 YoY106 のみ</p></section>
    """
    if check_html(yoy, "yoy.html"):
        print("SELFTEST FAIL: YoY106 should not warn")
        ok = False

    print("product_image_check.py --selftest:", "OK" if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--selftest" in argv:
        return selftest()
    warn_only = "--warn-only" in argv
    files = [a for a in argv if not a.startswith("-")]
    if not files:
        print(
            "使い方: product_image_check.py <deck.html>…  [--warn-only]",
            file=sys.stderr,
        )
        return 2
    issues: list[str] = []
    for f in files:
        path = Path(f)
        if not path.is_file():
            issues.append(f"{f}: ファイルが無い")
            continue
        issues.extend(
            check_html(path.read_text(encoding="utf-8", errors="replace"), f)
        )
    if not issues:
        print(f"{files[0]}: OK" if len(files) == 1 else f"{len(files)} files: OK")
        return 0
    for i in issues:
        print(i)
    print(f"{files[0]}: NG" if len(files) == 1 else "NG")
    return 0 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
