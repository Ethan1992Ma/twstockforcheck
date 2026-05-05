#!/usr/bin/env python3
"""build_site.py — Static site generator for TW Coverage.

Usage:
  python scripts/build_site.py              # Build to docs/
  SITE_BASE=/My-TW-Coverage python ...      # For GitHub Pages subpath
"""

import glob
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

import markdown
from markdown.extensions.tables import TableExtension

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR  = PROJECT_ROOT / "Pilot_Reports"
THEMES_DIR   = PROJECT_ROOT / "themes"
ASSETS_SRC   = Path(__file__).parent / "site_assets"
DOCS_DIR     = PROJECT_ROOT / "docs"
SITE_BASE    = os.environ.get("SITE_BASE", "")   # e.g. "/My-TW-Coverage"

MD = markdown.Markdown(extensions=[TableExtension()], output_format="html")

SECTOR_ZH = {
    "Advertising Agencies":                  "廣告代理",
    "Aerospace & Defense":                   "航太與國防",
    "Agricultural Inputs":                   "農業原料",
    "Airlines":                              "航空",
    "Aluminum":                              "鋁業",
    "Apparel Manufacturing":                 "服裝製造",
    "Apparel Retail":                        "服裝零售",
    "Asset Management":                      "資產管理",
    "Auto & Truck Dealerships":              "汽車與卡車經銷",
    "Auto Manufacturers":                    "汽車製造",
    "Auto Parts":                            "汽車零件",
    "Banks":                                 "銀行",
    "Banks - Regional":                      "區域銀行",
    "Beverages - Non-Alcoholic":             "非酒精飲料",
    "Biotech - Therapeutics":                "生技治療",
    "Biotechnology":                         "生物技術",
    "Broadcasting":                          "廣播媒體",
    "Building Materials":                    "建材",
    "Building Products & Equipment":         "建築產品與設備",
    "Business Equipment & Supplies":         "商業設備與耗材",
    "Capital Markets":                       "資本市場",
    "Chemicals":                             "化學品",
    "Communication Equipment":               "通訊設備",
    "Computer Hardware":                     "電腦硬體",
    "Conglomerates":                         "多角化集團",
    "Consulting Services":                   "顧問服務",
    "Consumer Electronics":                  "消費電子",
    "Copper":                                "銅業",
    "Credit Services":                       "信貸服務",
    "Department Stores":                     "百貨公司",
    "Drug Manufacturers - Specialty & Generic": "學名藥與特殊藥品",
    "Education & Training Services":         "教育與培訓服務",
    "Electrical Equipment & Parts":          "電氣設備與零件",
    "Electronic Components":                 "電子元件",
    "Electronic Gaming & Multimedia":        "電子遊戲與多媒體",
    "Electronics & Computer Distribution":   "電子與電腦通路",
    "Engineering & Construction":            "工程與建設",
    "Entertainment":                         "娛樂",
    "Farm Products":                         "農產品",
    "Financial Conglomerates":               "金融集團",
    "Food Distribution":                     "食品流通",
    "Footwear & Accessories":                "鞋類與配件",
    "Furnishings, Fixtures & Appliances":    "家具燈具家電",
    "Gambling":                              "博弈",
    "Home Improvement Retail":               "居家改善零售",
    "Household & Personal Products":         "家用與個人護理",
    "Industrial Distribution":               "工業通路",
    "Information Technology Services":       "資訊科技服務",
    "Insurance - Diversified":               "多元化保險",
    "Insurance - Life":                      "壽險",
    "Insurance - Property & Casualty":       "產險",
    "Insurance - Reinsurance":               "再保險",
    "Insurance Brokers":                     "保險經紀",
    "Integrated Freight & Logistics":        "整合貨運與物流",
    "Internet Content & Information":        "網路內容與資訊",
    "Internet Retail":                       "網路零售",
    "Leisure":                               "休閒",
    "Lodging":                               "住宿",
    "Lumber & Wood Production":              "木材生產",
    "Marine Shipping":                       "海運",
    "Medical Devices":                       "醫療器材",
    "Metal Fabrication":                     "金屬加工",
    "Oil & Gas Equipment & Services":        "油氣設備與服務",
    "Oil & Gas Refining & Marketing":        "油氣煉製與行銷",
    "Other Industrial Metals & Mining":      "工業金屬與礦業",
    "Packaged Foods":                        "包裝食品",
    "Packaging & Containers":               "包裝與容器",
    "Personal Services":                     "個人服務",
    "Pollution & Treatment Controls":        "污染防治",
    "Publishing":                            "出版",
    "Railroads":                             "鐵路",
    "Real Estate - Development":             "不動產開發",
    "Real Estate - Diversified":             "多元化不動產",
    "Real Estate Services":                  "不動產服務",
    "Recreational Vehicles":                 "休閒車輛",
    "Scientific & Technical Instruments":    "科學與技術儀器",
    "Security & Protection Services":        "保全與防護服務",
    "Semiconductor Equipment & Materials":   "半導體設備與材料",
    "Semiconductors":                        "半導體",
    "Software - Application":               "應用軟體",
    "Software - Infrastructure":             "基礎設施軟體",
    "Solar":                                 "太陽能",
    "Specialty Business Services":           "特殊商業服務",
    "Specialty Chemicals":                   "特殊化學品",
    "Specialty Industrial Machinery":        "特殊工業機械",
    "Specialty Retail":                      "特殊零售",
    "Staffing & Employment Services":        "人力資源服務",
    "Steel":                                 "鋼鐵",
    "Telecom Services":                      "電信服務",
    "Textile Manufacturing":                 "紡織製造",
    "Thermal Coal":                          "煤炭",
    "Tools & Accessories":                   "工具與配件",
    "Trucking":                              "貨運",
    "Utilities - Regulated Electric":        "電力公用事業",
    "Utilities - Regulated Gas":             "天然氣公用事業",
    "Utilities - Regulated Water":           "水務公用事業",
    "Utilities - Renewable":                 "再生能源",
    "Waste Management":                      "廢棄物管理",
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def href(path: str) -> str:
    return f"{SITE_BASE}/{path.lstrip('/')}"

def ticker_url(t_id: str) -> str:  return href("ticker/" + t_id + ".html")
def hub_url(wl: str) -> str:       return href("hub/" + slugify(wl) + ".html")
def theme_url(slug: str) -> str:   return href("theme/" + slug + ".html")
def sector_url(s: str) -> str:     return href("sector/" + slugify(s) + ".html")

def sector_zh(s: str) -> str:
    return SECTOR_ZH.get(s, s)

def slugify(text: str) -> str:
    return re.sub(r'[^\w一-鿿㐀-䷿＀-￯]+', '-', text).strip('-')

def md_to_html(text: str) -> str:
    MD.reset()
    return MD.convert(text)

def strip_wikilinks(text: str) -> str:
    return re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)

def wikilink_html(target: str, name_to_ticker: dict) -> str:
    if target in name_to_ticker:
        return f'<a href="{href(f"ticker/{name_to_ticker[target]}.html")}" class="wl wl-ticker">{target}</a>'
    return f'<a href="{href(f"hub/{slugify(target)}.html")}" class="wl">{target}</a>'

def render_content(md_text: str, name_to_ticker: dict) -> str:
    """Markdown with [[wikilinks]] → HTML."""
    # Replace [[wikilinks]] with placeholder HTML-safe tags first
    def replace_wl(m):
        return f"§WL§{m.group(1)}§/WL§"
    text = re.sub(r'\[\[([^\]]+)\]\]', replace_wl, md_text)
    html = md_to_html(text)
    # Restore wikilinks
    def restore_wl(m):
        return wikilink_html(m.group(1), name_to_ticker)
    return re.sub(r'§WL§([^§]+)§/WL§', restore_wl, html)


# ─── Data collection ──────────────────────────────────────────────────────────

def collect_tickers() -> list:
    tickers = []
    for filepath in glob.glob(str(REPORTS_DIR / "**" / "*.md"), recursive=True):
        fn = os.path.basename(filepath)
        m  = re.match(r'^(\d{4})_(.+)\.md$', fn)
        if not m:
            continue
        ticker, name = m.group(1), m.group(2)
        sector       = os.path.basename(os.path.dirname(filepath))

        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        meta = {}
        for field in ["板塊", "產業", "市值", "企業價值"]:
            fm = re.search(rf'\*\*{field}:\*\*\s*(.+)', content)
            if fm:
                meta[field] = fm.group(1).strip()

        # First real paragraph of 業務簡介 as excerpt
        excerpt = ""
        biz_m = re.search(r'## 業務簡介\n(?:[^\n]*\n){0,6}(\[\[.{3,}|[^\[*\-\|#\n][^\n]{30,})', content)
        if biz_m:
            raw     = strip_wikilinks(biz_m.group(1))
            raw     = re.sub(r'\*+', '', raw)
            excerpt = raw[:200].strip()

        wikilinks = list(dict.fromkeys(re.findall(r'\[\[([^\]]+)\]\]', content)))

        tickers.append({
            "ticker":    ticker,
            "name":      name,
            "sector":    sector,
            "filepath":  filepath,
            "content":   content,
            "meta":      meta,
            "excerpt":   excerpt,
            "wikilinks": wikilinks[:40],
        })

    return sorted(tickers, key=lambda x: x["ticker"])


def build_wikilink_map(tickers: list) -> dict:
    wmap = defaultdict(list)
    for t in tickers:
        for wl in t["wikilinks"]:
            wmap[wl].append(t)
    return dict(wmap)


def collect_themes() -> list:
    themes = []
    for filepath in sorted(glob.glob(str(THEMES_DIR / "*.md"))):
        stem = Path(filepath).stem
        if stem in ("README",):
            continue
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        title_m = re.match(r'^# (.+)', content)
        title   = title_m.group(1) if title_m else stem
        desc_m  = re.search(r'^> (.+)', content, re.MULTILINE)
        desc    = desc_m.group(1) if desc_m else ""
        count_m = re.search(r'\*\*涵蓋公司數:\*\* (\d+)', content)
        count   = int(count_m.group(1)) if count_m else 0

        sections = {}
        for sec in ["上游", "中游", "下游", "相關公司"]:
            pat = rf'## {re.escape(sec)} \(\d+\)\n\n((?:- .+\n?)*)'
            sm  = re.search(pat, content)
            if not sm:
                continue
            companies = []
            for line in sm.group(1).strip().splitlines():
                line = line.lstrip("- ").strip()
                cm = re.match(r'\*\*(\d{4}) ([^*]+)\*\*\s*(?:\(([^)]+)\))?', line)
                if cm:
                    companies.append({
                        "ticker": cm.group(1),
                        "name":   cm.group(2).strip(),
                        "sector": cm.group(3) or "",
                    })
            sections[sec] = companies

        themes.append({
            "name":        stem,
            "title":       title,
            "description": desc,
            "count":       count,
            "sections":    sections,
            "slug":        slugify(stem),
        })

    return sorted(themes, key=lambda x: -x["count"])


# ─── Sankey ───────────────────────────────────────────────────────────────────

def build_sankey(theme: dict) -> dict:
    secs       = theme["sections"]
    upstream   = secs.get("上游",   [])
    midstream  = secs.get("中游",   [])
    downstream = secs.get("下游",   [])

    if not (upstream or midstream) or not downstream:
        return {}

    labels, colors, src, tgt = [], [], [], []
    COLORS = {"上游": "#4c9aff", "中游": "#f39c12", "theme": "#ff6b6b", "下游": "#51cf66"}

    for c in upstream:
        labels.append(c["name"]); colors.append(COLORS["上游"])
    up_end = len(labels)

    for c in midstream:
        labels.append(c["name"]); colors.append(COLORS["中游"])
    mid_end = len(labels)

    # Central theme node
    theme_idx = len(labels)
    labels.append(theme["title"].split("\n")[0])
    colors.append(COLORS["theme"])

    for c in downstream:
        labels.append(c["name"]); colors.append(COLORS["下游"])

    # Links: 上游/中游 → theme
    for i in range(mid_end):
        src.append(i); tgt.append(theme_idx)
    # Links: theme → 下游
    for j in range(len(downstream)):
        src.append(theme_idx); tgt.append(theme_idx + 1 + j)

    return {"labels": labels, "colors": colors,
            "source": src, "target": tgt, "value": [1] * len(src)}


# ─── HTML templates ───────────────────────────────────────────────────────────

def _head(title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — TW Coverage</title>
<link rel="stylesheet" href="{href('assets/style.css')}">
<script>window.SITE_BASE="{SITE_BASE}"</script>
</head>
<body>"""


def _nav() -> str:
    return f"""<header class="site-header">
  <nav class="nav-inner">
    <a class="nav-logo" href="{href('')}">📊 TW Coverage</a>
    <div class="nav-search-wrap">
      <input id="nav-search" type="text" placeholder="搜尋股票、公司、主題..." autocomplete="off">
      <div id="nav-results" class="search-dropdown"></div>
    </div>
    <div class="nav-links">
      <a href="{href('sectors.html')}">產業</a>
      <a href="{href('themes.html')}">主題</a>
    </div>
  </nav>
</header>"""


def _foot(extra_js: str = "") -> str:
    return f"""{extra_js}
<script src="{href('assets/app.js')}"></script>
</body></html>"""


def _badge(text: str, cls: str = "badge") -> str:
    return f'<span class="{cls}">{text}</span>' if text else ""


# ─── Page generators ──────────────────────────────────────────────────────────

def gen_homepage(tickers: list, themes: list, by_sector: dict) -> str:
    n_tickers = len(tickers)
    n_sectors = len(set(t["sector"] for t in tickers))

    theme_cards = "\n".join(
        '<a class="theme-card" href="' + theme_url(t["slug"]) + '">'
        + '<strong>' + t["title"] + '</strong><span>' + str(t["count"]) + ' 家公司</span>'
        + ('<small>' + t["description"] + '</small>' if t["description"] else '')
        + '</a>'
        for t in themes[:12]
    )

    # Sector heatmap — top 24 by company count
    sorted_sectors = sorted(by_sector.items(), key=lambda x: -len(x[1]))[:24]
    max_count = max(len(ts) for _, ts in sorted_sectors) if sorted_sectors else 1
    heat_cells = "".join(
        '<a class="heat-cell" href="' + sector_url(s) + '"'
        ' style="--heat:' + f"{len(ts)/max_count:.2f}" + '">'
        '<strong>' + sector_zh(s) + '</strong>'
        '<em>' + str(len(ts)) + ' 家</em>'
        '</a>'
        for s, ts in sorted_sectors
    )

    return f"""{_head("Taiwan Stock Coverage")}
{_nav()}
<main>
  <section class="hero">
    <div class="hero-inner">
      <h1>Taiwan Stock<br>Coverage</h1>
      <p class="hero-sub">{n_tickers:,} 家台股 &nbsp;·&nbsp; {n_sectors} 個產業 &nbsp;·&nbsp; 4,900+ Wikilinks</p>
      <div class="hero-search-wrap">
        <input id="hero-search" type="text" placeholder="搜尋股票代碼、公司名稱、供應鏈主題..." autocomplete="off" spellcheck="false">
        <div id="hero-results" class="search-dropdown search-dropdown--hero"></div>
      </div>
      <div class="search-pills">
        試試：
        <a href="{href('ticker/2330.html')}">台積電</a>
        <a href="{href('hub/Apple.html')}">Apple</a>
        <a href="{href('theme/CoWoS.html')}">CoWoS</a>
        <a href="{href('hub/矽光子.html')}">矽光子</a>
        <a href="{href('hub/NVIDIA.html')}">NVIDIA</a>
      </div>
    </div>
  </section>

  <section class="container home-section">
    <h2>板塊熱度</h2>
    <p class="heat-legend">顏色越深代表覆蓋公司數越多，點擊進入各產業列表。</p>
    <div class="sector-heat-grid sector-heat-grid--home">{heat_cells}</div>
    <a class="see-all" href="{href('sectors.html')}">查看全部 {n_sectors} 個產業 →</a>
  </section>

  <section class="container home-section">
    <h2>熱門主題供應鏈</h2>
    <div class="theme-grid">{theme_cards}</div>
    <a class="see-all" href="{href('themes.html')}">查看全部主題 →</a>
  </section>
</main>
{_foot()}"""


def gen_ticker_page(t: dict, name_to_ticker: dict) -> str:
    content_html = render_content(t["content"], name_to_ticker)
    market_cap   = t["meta"].get("市值", "")
    sector_badge = _badge(t["meta"].get("板塊", ""),    "badge badge-sector")
    ind_badge    = _badge(t["meta"].get("產業", ""),    "badge badge-industry")
    cap_badge    = _badge(market_cap,                    "badge badge-cap") if market_cap else ""

    return f"""{_head(f"{t['ticker']} {t['name']}")}
{_nav()}
<main class="container">
  <div class="ticker-header">
    <div class="ticker-title">
      <span class="ticker-code">{t['ticker']}</span>
      <h1>{t['name']}</h1>
    </div>
    <div class="ticker-badges">{sector_badge}{ind_badge}{cap_badge}</div>
  </div>
  <div class="ticker-content">
    {content_html}
  </div>
</main>
{_foot()}"""


def gen_hub_page(wl: str, wl_tickers: list, related: list) -> str:
    count     = len(wl_tickers)
    by_sector = defaultdict(list)
    for t in wl_tickers:
        by_sector[t["sector"]].append(t)

    sectors_html = ""
    for sector, st in sorted(by_sector.items(), key=lambda x: -len(x[1])):
        zh = sector_zh(sector)
        chips = "".join(
            '<a class="ticker-chip" href="' + ticker_url(t["ticker"]) + '">'
            '<span class="chip-code">' + t["ticker"] + '</span>' + t["name"] + '</a>'
            for t in sorted(st, key=lambda x: x["ticker"])
        )
        sectors_html += (
            f'<div class="hub-sector">'
            f'<h3>{zh} <span class="sector-en">{sector}</span>'
            f' <span class="count-badge">{len(st)}</span></h3>'
            f'<div class="chip-grid">{chips}</div></div>'
        )

    related_html = ""
    if related:
        chips = "".join(
            '<a class="wl-chip" href="' + hub_url(rwl) + '">'
            + rwl + ' <span class="chip-count">' + str(cnt) + '</span></a>'
            for rwl, cnt in related[:20]
        )
        related_html = f'<div class="hub-related"><h3>常一起出現的主題</h3><div class="chip-grid">{chips}</div></div>'

    return f"""{_head(wl)}
{_nav()}
<main class="container">
  <div class="hub-header">
    <h1 class="wl">{wl}</h1>
    <p class="hub-count">{count} 家台股相關公司</p>
  </div>
  {sectors_html}
  {related_html}
</main>
{_foot()}"""


def gen_theme_page(theme: dict, name_to_ticker: dict) -> str:
    sankey = build_sankey(theme)
    sankey_block = ""
    if sankey:
        sankey_js = f"""
<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
<script>
(function(){{
  var d={json.dumps(sankey, ensure_ascii=False)};
  Plotly.newPlot("sankey-chart",[{{
    type:"sankey",orientation:"h",
    node:{{pad:15,thickness:18,line:{{color:"#ddd",width:0.5}},
          label:d.labels,color:d.colors}},
    link:{{source:d.source,target:d.target,value:d.value,
           color:"rgba(150,150,150,0.15)"}}
  }}],{{
    font:{{size:11,family:"-apple-system,'Noto Sans TC',sans-serif"}},
    margin:{{l:0,r:0,t:10,b:10}},paper_bgcolor:"transparent"
  }},{{responsive:true,displayModeBar:false}});
}})();
</script>"""
        sankey_block = f'<div id="sankey-chart" style="height:380px;margin:1.5rem 0"></div>'
    else:
        sankey_js = ""

    sections_html = ""
    sec_colors = {"上游": "upstream", "中游": "midstream", "下游": "downstream", "相關公司": "related"}
    for sec_name, companies in theme["sections"].items():
        if not companies:
            continue
        cls   = sec_colors.get(sec_name, "")
        chips = "".join(
            '<a class="ticker-chip ticker-chip--' + cls + '" href="' + ticker_url(c["ticker"]) + '">'
            '<span class="chip-code">' + c["ticker"] + '</span>' + c["name"]
            + ('<small>' + c["sector"] + '</small>' if c["sector"] else '')
            + '</a>'
            for c in companies
        )
        sections_html += (
            f'<div class="theme-section theme-section--{cls}">'
            f'<h2>{sec_name} <span class="count-badge">{len(companies)}</span></h2>'
            f'<div class="chip-grid">{chips}</div></div>'
        )

    return f"""{_head(theme["title"])}
{_nav()}
<main class="container">
  <div class="theme-header">
    <h1>{theme["title"]}</h1>
    {"<p class='theme-desc'>" + theme["description"] + "</p>" if theme["description"] else ""}
    <p class="theme-count">{theme["count"]} 家相關公司</p>
  </div>
  {sankey_block}
  {sections_html}
</main>
{_foot(sankey_js)}"""


def gen_sector_page(sector: str, tickers: list) -> str:
    zh = sector_zh(sector)
    rows = "".join(
        '<a class="sector-row" href="' + ticker_url(t["ticker"]) + '">'
        '<span class="sr-code">' + t["ticker"] + '</span>'
        '<span class="sr-name">' + t["name"] + '</span>'
        '<span class="sr-excerpt">' + t["excerpt"][:80] + '</span>'
        '<span class="sr-cap">' + t["meta"].get("市值", "") + '</span>'
        '</a>'
        for t in sorted(tickers, key=lambda x: x["ticker"])
    )
    title_html = (
        f'<h1>{zh} <span class="sector-en">{sector}</span>'
        f' <span class="count-badge">{len(tickers)}</span></h1>'
    )
    return f"""{_head(zh + " — " + sector)}
{_nav()}
<main class="container">
  {title_html}
  <div class="sector-list">{rows}</div>
</main>
{_foot()}"""


def gen_sectors_index(by_sector: dict) -> str:
    sorted_sectors = sorted(by_sector.items(), key=lambda x: -len(x[1]))
    max_count = max(len(ts) for ts in by_sector.values()) if by_sector else 1
    cells = "".join(
        '<a class="heat-cell" href="' + sector_url(s) + '"'
        ' style="--heat:' + f"{len(ts)/max_count:.2f}" + '">'
        '<strong>' + sector_zh(s) + '</strong>'
        '<span>' + s + '</span>'
        '<em>' + str(len(ts)) + ' 家</em>'
        '</a>'
        for s, ts in sorted_sectors
    )
    return f"""{_head("產業熱度")}
{_nav()}
<main class="container">
  <h1>產業熱度 <span class="count-badge">{len(by_sector)}</span></h1>
  <p class="heat-legend">顏色深淺代表覆蓋公司數量，顏色越深代表公司數越多。</p>
  <div class="sector-heat-grid">{cells}</div>
</main>
{_foot()}"""


def gen_themes_index(themes: list) -> str:
    cards = "".join(
        '<a class="theme-card" href="' + theme_url(t["slug"]) + '">'
        + '<strong>' + t["title"] + '</strong><span>' + str(t["count"]) + ' 家公司</span>'
        + ('<small>' + t["description"] + '</small>' if t["description"] else '')
        + '</a>'
        for t in themes
    )
    return f"""{_head("主題供應鏈")}
{_nav()}
<main class="container">
  <h1>主題供應鏈 <span class="count-badge">{len(themes)}</span></h1>
  <div class="theme-grid">{cards}</div>
</main>
{_foot()}"""


def build_search_index(tickers: list) -> list:
    return [
        {
            "t": t["ticker"],
            "n": t["name"],
            "s": t["sector"],
            "e": t["excerpt"][:150],
            "w": t["wikilinks"][:10],
        }
        for t in tickers
    ]


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("🔨 Building TW Coverage static site...")

    for subdir in ["ticker", "sector", "hub", "theme", "assets"]:
        (DOCS_DIR / subdir).mkdir(parents=True, exist_ok=True)

    # Collect
    print("📁 Scanning tickers...", end=" ", flush=True)
    tickers = collect_tickers()
    print(f"{len(tickers)} found")

    name_to_ticker = {t["name"]: t["ticker"] for t in tickers}
    wikilink_map   = build_wikilink_map(tickers)
    by_sector      = defaultdict(list)
    for t in tickers:
        by_sector[t["sector"]].append(t)

    print("🗂️  Scanning themes...", end=" ", flush=True)
    themes = collect_themes()
    print(f"{len(themes)} found")

    # Ticker pages
    print("📄 Ticker pages...", end=" ", flush=True)
    for t in tickers:
        html = gen_ticker_page(t, name_to_ticker)
        (DOCS_DIR / "ticker" / f'{t["ticker"]}.html').write_text(html, encoding="utf-8")
    print(f"{len(tickers)} pages")

    # Sector pages
    print("🏭 Sector pages...", end=" ", flush=True)
    for sector, st in by_sector.items():
        html = gen_sector_page(sector, st)
        (DOCS_DIR / "sector" / f"{slugify(sector)}.html").write_text(html, encoding="utf-8")
    (DOCS_DIR / "sectors.html").write_text(gen_sectors_index(by_sector), encoding="utf-8")
    print(f"{len(by_sector)} sectors")

    # Hub pages (wikilinks with ≥5 mentions)
    print("🔗 Hub pages...", end=" ", flush=True)
    hub_count = 0
    for wl, wl_tickers in wikilink_map.items():
        if len(wl_tickers) < 5:
            continue
        co = defaultdict(int)
        for t in wl_tickers:
            for owt in t["wikilinks"]:
                if owt != wl:
                    co[owt] += 1
        related = sorted(co.items(), key=lambda x: -x[1])[:20]
        html = gen_hub_page(wl, wl_tickers, related)
        (DOCS_DIR / "hub" / f"{slugify(wl)}.html").write_text(html, encoding="utf-8")
        hub_count += 1
    print(f"{hub_count} hubs")

    # Theme pages
    print("🗺️  Theme pages...", end=" ", flush=True)
    for theme in themes:
        html = gen_theme_page(theme, name_to_ticker)
        (DOCS_DIR / "theme" / f'{theme["slug"]}.html').write_text(html, encoding="utf-8")
    (DOCS_DIR / "themes.html").write_text(gen_themes_index(themes), encoding="utf-8")
    print(f"{len(themes)} themes")

    # Homepage
    print("🏠 Homepage...", end=" ", flush=True)
    (DOCS_DIR / "index.html").write_text(gen_homepage(tickers, themes, by_sector), encoding="utf-8")
    print("done")

    # Search index
    print("🔍 Search index...", end=" ", flush=True)
    idx = build_search_index(tickers)
    (DOCS_DIR / "search-index.json").write_text(
        json.dumps(idx, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"{len(idx)} entries")

    # Assets
    print("🎨 Assets...", end=" ", flush=True)
    for asset in ASSETS_SRC.glob("*"):
        shutil.copy(asset, DOCS_DIR / "assets" / asset.name)
    print("done")

    total_pages = len(tickers) + hub_count + len(by_sector) + len(themes) + 3
    print(f"\n✅ Done — {total_pages} pages → {DOCS_DIR}")


if __name__ == "__main__":
    main()
