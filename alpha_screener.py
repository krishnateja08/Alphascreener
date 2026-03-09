#!/usr/bin/env python3
"""
Global Market News & Indicators Dashboard
Fetches REAL latest news using RSS feeds every run.
Generates HTML with Bloomberg Terminal UI (Template 1).
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import html as html_module
import re

# ─────────────────────────────────────────────
#  NEWS SOURCES  (RSS feeds – no API key needed)
# ─────────────────────────────────────────────
RSS_SOURCES = {
    # 1 ── Markets + Earnings + IPO & Deals
    "markets": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,^IXIC&region=US&lang=en-US",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://news.google.com/rss/search?q=earnings+results+IPO+stock+market+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 2 ── Macro & Policy + Trade & Tariffs
    "macro_policy": [
        "https://www.cnbc.com/id/20910258/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/economy-politics/",
        "https://www.federalreserve.gov/feeds/press_all.xml",
        "https://news.google.com/rss/search?q=trade+tariffs+WTO+supply+chain+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 3 ── Banking & FX + Forex
    "banking_fx": [
        "https://news.google.com/rss/search?q=central+bank+interest+rates+Fed+ECB+RBI+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://www.cnbc.com/id/10000108/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/financialservices/",
        "https://news.google.com/rss/search?q=forex+USD+EUR+JPY+GBP+currency+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 4 ── Commodities & Energy + OPEC
    "commodities_energy": [
        "https://news.google.com/rss/search?q=commodities+copper+wheat+natural+gas+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.marketwatch.com/marketwatch/commodities/",
        "https://www.cnbc.com/id/10000113/device/rss/rss.html",
        "https://news.google.com/rss/search?q=OPEC+oil+energy+renewables+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 5 ── India Markets
    "india": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://www.moneycontrol.com/rss/marketreports.xml",
        "https://economictimes.indiatimes.com/rssfeeds/1373380680.cms",
    ],
    # 6 ── Trending (India Google)
    "trending": [
        "https://news.google.com/rss/search?q=NSE+BSE+stock+market+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=Nifty+Sensex+today+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=india+stocks+trending+today+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    # 7 ── Corporate News
    "corporate": [
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/marketpulse/",
        "https://finance.yahoo.com/rss/topfinstories",
    ],
    # 8 ── Geopolitical
    "geopolitical": [
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/realtimeheadlines/",
    ],
    # 9 ── Crypto & Web3
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "https://news.google.com/rss/search?q=bitcoin+ethereum+crypto+DeFi+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 10 ── Tech & AI
    "tech_ai": [
        "https://news.google.com/rss/search?q=artificial+intelligence+AI+tech+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=OpenAI+Google+AI+Microsoft+AI+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=AI+chips+semiconductor+LLM+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 11 ── Asia & China (China + Japan/Nikkei/BOJ)
    "asia_china": [
        "https://news.google.com/rss/search?q=china+stock+market+Hang+Seng+Shanghai+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=PBOC+yuan+China+economy+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.reuters.com/reuters/CNtopNews",
        "https://news.google.com/rss/search?q=Nikkei+Japan+BOJ+yen+Asia+markets+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 12 ── Europe & UK (NEW)
    "europe_uk": [
        "https://news.google.com/rss/search?q=DAX+FTSE+Euro+Stoxx+European+markets+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=ECB+Bank+of+England+interest+rates+Europe+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://feeds.reuters.com/reuters/UKTopNews",
        "https://news.google.com/rss/search?q=FTSE+100+UK+economy+pound+sterling+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
    # 13 ── ESG & Climate (NEW)
    "esg_climate": [
        "https://news.google.com/rss/search?q=ESG+green+bonds+sustainable+investing+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=carbon+market+climate+change+COP+when:1d&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=renewable+energy+solar+wind+EV+when:1d&hl=en-US&gl=US&ceid=US:en",
    ],
}

MAX_NEWS_PER_CATEGORY = 10
REQUEST_TIMEOUT = 8


# ─────────────────────────────────────────────
#  RSS FETCHER
# ─────────────────────────────────────────────
def fetch_rss(url: str) -> list[dict]:
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; MarketDashboard/1.0)",
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")

        raw = re.sub(r'\s+xmlns[^"]*"[^"]*"', "", raw)
        raw = re.sub(r"<(/?)[\w]+:", r"<\1", raw)

        root = ET.fromstring(raw)
        channel = root.find("channel") or root

        domain = urllib.parse.urlparse(url).netloc.replace("www.", "").replace("feeds.", "")
        source_map = {
            "cnbc.com": "CNBC",
            "marketwatch.com": "MarketWatch",
            "reuters.com": "Reuters",
            "finance.yahoo.com": "Yahoo Finance",
            "economictimes.indiatimes.com": "Economic Times",
            "moneycontrol.com": "MoneyControl",
            "federalreserve.gov": "Federal Reserve",
            "cointelegraph.com": "CoinTelegraph",
            "coindesk.com": "CoinDesk",
            "feedburner.com": "TechCrunch",
            "techcrunch.com": "TechCrunch",
            "news.google.com": "Google News",
            "ft.com": "Financial Times",
            "bbc.co.uk": "BBC",
            "theguardian.com": "The Guardian",
        }
        source = next((v for k, v in source_map.items() if k in domain), domain)

        for item in channel.findall("item")[:MAX_NEWS_PER_CATEGORY]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            summary = (item.findtext("description") or item.findtext("summary") or "").strip()
            pub_date = (item.findtext("pubDate") or item.findtext("date") or "").strip()

            summary = re.sub(r"<[^>]+>", "", summary).strip()
            summary = html_module.unescape(summary)
            title = html_module.unescape(title)

            if title and len(title) > 10:
                items.append({
                    "title": title,
                    "link": link,
                    "summary": summary[:500] if summary else "Click to read the full article.",
                    "pubDate": pub_date,
                    "source": source,
                })
    except Exception as e:
        print(f"    ⚠  Could not fetch {url}: {e}")
    return items


def fetch_category_news(category: str, urls: list[str]) -> list[dict]:
    seen_titles = set()
    results = []

    DATE_FMTS = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
    ]

    def is_within_window(pub_date_str: str, cutoff: datetime) -> bool:
        if not pub_date_str:
            return False
        for fmt in DATE_FMTS:
            try:
                pub = datetime.strptime(pub_date_str.strip(), fmt)
                if pub.tzinfo is not None:
                    pub = pub.utctimetuple()
                    pub = datetime(*pub[:6])
                return pub >= cutoff
            except ValueError:
                continue
        return False

    def _collect(cutoff: datetime) -> None:
        for url in urls:
            print(f"  Fetching {url[:60]}...")
            for item in fetch_rss(url):
                key = item["title"].lower()[:60]
                if key in seen_titles:
                    continue
                if not is_within_window(item.get("pubDate", ""), cutoff):
                    continue
                seen_titles.add(key)
                results.append(item)
                if len(results) >= MAX_NEWS_PER_CATEGORY:
                    return
            if len(results) >= MAX_NEWS_PER_CATEGORY:
                return

    # Pass 1: last 24 hours
    _collect(datetime.utcnow() - timedelta(hours=24))

    # Pass 2 fallback: extend to 7 days if fewer than 5 articles
    if len(results) < 5:
        print(f"  ⚠  Only {len(results)} articles in 24h for [{category}] — extending to 7-day window…")
        _collect(datetime.utcnow() - timedelta(days=7))

    return results[:MAX_NEWS_PER_CATEGORY]


def format_pub_date(raw: str) -> str:
    if not raw:
        return "Just now"
    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.utcnow()
            diff = now - dt
            if diff.days == 0:
                hours = diff.seconds // 3600
                mins = (diff.seconds % 3600) // 60
                if hours == 0:
                    return f"{mins} min ago" if mins > 1 else "Just now"
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return dt.strftime("%b %d, %Y")
        except ValueError:
            continue
    return raw[:20]


# ─────────────────────────────────────────────
#  HTML GENERATION
# ─────────────────────────────────────────────
def get_ist_time() -> str:
    utc_time = datetime.utcnow()
    ist_time = utc_time + timedelta(hours=5, minutes=30)
    return ist_time.strftime("%B %d, %Y at %I:%M %p IST")


def escape(text: str) -> str:
    return html_module.escape(str(text), quote=True)


def build_news_json(all_news: dict) -> str:
    """Serialize all_news into a JS-safe JSON object for client-side tab rendering."""
    categories_meta = {
        "markets":            "📊 MARKETS & EARNINGS",
        "macro_policy":       "💰 MACRO & POLICY",
        "banking_fx":         "🏦 BANKING & FX",
        "commodities_energy": "📦 COMMODITIES & ENERGY",
        "india":              "🇮🇳 INDIA MARKETS",
        "trending":           "🔥 TRENDING",
        "corporate":          "🏢 CORPORATE NEWS",
        "geopolitical":       "🌍 GEOPOLITICAL",
        "crypto":             "📉 CRYPTO & WEB3",
        "tech_ai":            "🤖 TECH & AI",
        "asia_china":         "🌏 ASIA & CHINA",
        "europe_uk":          "🇪🇺 EUROPE & UK",
        "esg_climate":        "🌱 ESG & CLIMATE",
    }

    out = {}
    for cat, label in categories_meta.items():
        items = all_news.get(cat, [])
        out[cat] = {
            "label": label,
            "items": [
                {
                    "title":   escape(item.get("title", "Untitled")),
                    "source":  escape(item.get("source", "Unknown")),
                    "time":    format_pub_date(item.get("pubDate", "")),
                    "summary": escape(item.get("summary", "Click to read the full article.")),
                    "link":    escape(item.get("link", "#")),
                }
                for item in items
            ],
        }
    return json.dumps(out, ensure_ascii=False)


def generate_complete_html(all_news: dict) -> str:
    current_time = get_ist_time()
    total_articles = sum(len(v) for v in all_news.values())
    news_json = build_news_json(all_news)

    # Count per category for sidebar
    cat_counts = {
        "markets":            len(all_news.get("markets", [])),
        "macro_policy":       len(all_news.get("macro_policy", [])),
        "banking_fx":         len(all_news.get("banking_fx", [])),
        "commodities_energy": len(all_news.get("commodities_energy", [])),
        "india":              len(all_news.get("india", [])),
        "trending":           len(all_news.get("trending", [])),
        "corporate":          len(all_news.get("corporate", [])),
        "geopolitical":       len(all_news.get("geopolitical", [])),
        "crypto":             len(all_news.get("crypto", [])),
        "tech_ai":            len(all_news.get("tech_ai", [])),
        "asia_china":         len(all_news.get("asia_china", [])),
        "europe_uk":          len(all_news.get("europe_uk", [])),
        "esg_climate":        len(all_news.get("esg_climate", [])),
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NexusFeed – Global Market Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600;700&family=IBM+Plex+Sans:wght@300;400;600&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
/* ══════════════════════════════════════════
   BLOOMBERG TERMINAL THEME
   ══════════════════════════════════════════ */
:root {{
  --bg: #0d0d0d;
  --panel: #131313;
  --panel2: #181818;
  --border: #333333;
  --border2: #252525;
  --orange: #ff6a00;
  --orange-dim: rgba(255,106,0,0.10);
  --orange-mid: rgba(255,106,0,0.22);
  --green: #00ff55;
  --green-dim: rgba(0,255,85,0.08);
  --red: #ff3355;
  --red-dim: rgba(255,51,85,0.08);
  --yellow: #ffd700;
  --blue: #29b6ff;
  --muted: #999999;
  --muted2: #666666;
  --text: #d8d8d8;
  --white: #f5f5f5;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: 'IBM Plex Mono', monospace;
  font-size: 14px;
  min-height: 100vh;
  overflow-x: hidden;
}}

/* ── TOP BAR ── */
.topbar {{
  background: var(--orange);
  color: #000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 18px;
  font-weight: 700;
  font-size: 12px;
  letter-spacing: 2px;
  position: sticky;
  top: 0;
  z-index: 100;
}}
.topbar-left {{ display:flex; align-items:center; gap:16px; }}
.topbar-right {{ display:flex; gap: 22px; font-weight: 600; font-size: 11px; }}
.topbar-dot {{ width:8px; height:8px; border-radius:50%; background:#000; animation: blink 1.5s step-end infinite; }}
@keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}

/* ── TICKER STRIP ── */
.ticker {{
  background: #1c1c1c;
  border-bottom: 1px solid var(--border);
  padding: 6px 0;
  overflow: hidden;
  white-space: nowrap;
}}
.ticker-track {{
  display: inline-flex;
  gap: 0;
  animation: scroll-ticker 60s linear infinite;
}}
.ticker-track:hover {{ animation-play-state: paused; }}
.ticker-item {{
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 26px;
  border-right: 1px solid var(--border);
  font-size: 12px;
  letter-spacing: 0.3px;
}}
.t-sym {{ color: var(--orange); font-weight: 700; }}
.t-val {{ color: var(--white); font-weight: 500; }}
.t-pos {{ color: var(--green); font-weight: 600; }}
.t-neg {{ color: var(--red); font-weight: 600; }}
.t-neu {{ color: #aaaaaa; }}
@keyframes scroll-ticker {{
  0%   {{ transform: translateX(0); }}
  100% {{ transform: translateX(-50%); }}
}}

/* ── MAIN SHELL ── */
.shell {{
  display: grid;
  grid-template-columns: 240px 1fr;
  height: calc(100vh - 56px);
}}

/* ── SIDEBAR ── */
.sidebar {{
  background: var(--panel);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  padding: 16px 0 40px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}}
.sidebar::-webkit-scrollbar {{ width:4px; }}
.sidebar::-webkit-scrollbar-track {{ background:transparent; }}
.sidebar::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}

.sb-section {{ margin-bottom: 24px; }}
.sb-label {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  padding: 5px 14px 8px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.sb-item {{
  padding: 8px 14px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 3px solid transparent;
  transition: all 0.12s;
  font-size: 13px;
}}
.sb-item:hover {{ background: var(--orange-dim); border-left-color: rgba(255,106,0,0.4); }}
.sb-item.active {{ background: var(--orange-dim); border-left-color: var(--orange); }}
.sb-item .sb-name {{ color: var(--white); font-weight: 500; }}
.sb-item .sb-count {{
  color: #cccccc;
  font-size: 11px;
  background: var(--border2);
  padding: 1px 7px;
  border-radius: 2px;
  font-weight: 600;
}}
.sb-item.active .sb-count {{ background: var(--orange-mid); color: var(--orange); }}

.sb-ind-row {{
  padding: 7px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  border-bottom: 1px solid var(--border2);
}}
.sb-ind-row:last-child {{ border-bottom: none; }}
.sb-ind-name {{ color: #cccccc; font-weight: 400; }}
.sb-ind-val {{ font-weight: 700; font-size: 12px; }}
.sb-ind-val.pos {{ color: var(--green); }}
.sb-ind-val.neg {{ color: var(--red); }}
.sb-ind-val.neu {{ color: #aaaaaa; }}

/* ── COLLAPSIBLE ECON SECTIONS IN SIDEBAR ── */
.sb-econ-hdr {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 14px 8px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
  transition: background 0.12s;
}}
.sb-econ-hdr:hover {{ background: rgba(255,106,0,0.06); }}
.sb-econ-title {{
  font-size: 11px; font-weight: 700; letter-spacing: 2px;
  text-transform: uppercase; display: flex; align-items: center; gap: 6px;
}}
.sb-econ-title.usa  {{ color: #e05060; }}
.sb-econ-title.india {{ color: #ffaa44; }}
.sb-econ-arrow {{
  color: var(--orange); font-size: 9px;
  transition: transform 0.2s; flex-shrink: 0;
}}
.sb-econ-arrow.collapsed {{ transform: rotate(-90deg); }}

.sb-econ-body {{ overflow: hidden; transition: max-height 0.25s ease; }}
.sb-econ-body.collapsed {{ max-height: 0 !important; }}

.sb-econ-row {{
  padding: 5px 14px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 11px; border-bottom: 1px solid var(--border2);
}}
.sb-econ-row:last-child {{ border-bottom: none; padding-bottom: 8px; }}
.sb-econ-key {{ color: #bbbbbb; font-size: 10px; letter-spacing: 0.3px; flex: 1; }}
.sb-econ-val {{ font-weight: 700; font-size: 11px; white-space: nowrap; margin-left: 6px; }}
.sb-econ-val.pos {{ color: var(--green); }}
.sb-econ-val.neg {{ color: var(--red); }}
.sb-econ-val.neu {{ color: #aaaaaa; }}
.sb-econ-note {{ color: #666; font-size: 9px; margin-left: 4px; white-space: nowrap; }}

/* ── MAIN CONTENT ── */
.main {{ overflow-y: auto; display: flex; flex-direction: column; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }}
.main::-webkit-scrollbar {{ width:4px; }}
.main::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:2px; }}

/* ── INDICATORS / ECON PANELS ── */
.ind-panel-hdr {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.ind-panel-hdr::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(255,106,0,0.5), transparent); }}

.ind-row {{ display: flex; gap: 3px; flex-wrap: wrap; }}

.ind-cell {{
  background: var(--panel);
  border: 1px solid var(--border);
  padding: 10px 14px;
  min-width: 130px;
  flex: 1;
  position: relative;
  transition: border-color 0.2s;
}}
.ind-cell::after {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
}}
.ind-cell.pos::after {{ background: var(--green); }}
.ind-cell.neg::after {{ background: var(--red); }}
.ind-cell.neu::after {{ background: #666; }}
.ind-cell:hover {{ border-color: var(--orange); }}

.ind-name {{
  color: #aaaaaa;
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 5px;
  font-weight: 500;
}}
.ind-val {{
  color: var(--white);
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 4px;
  white-space: nowrap;
  letter-spacing: -0.5px;
}}
.ind-chg {{
  font-size: 11px;
  letter-spacing: 0.3px;
  white-space: nowrap;
  font-weight: 600;
}}
.ind-chg.pos {{ color: var(--green); }}
.ind-chg.neg {{ color: var(--red); }}
.ind-chg.neu {{ color: #aaaaaa; }}

/* ── USA / INDIA ECON PANELS ── */
.econ-section {{
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  background: #101010;
  flex-shrink: 0;
}}
.econ-hdr {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.econ-hdr.usa {{ color: #e05060; }}
.econ-hdr.usa::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(224,80,96,0.5), transparent); }}
.econ-hdr.india {{ color: #ffaa44; }}
.econ-hdr.india::after {{ content:''; flex:1; height:1px; background: linear-gradient(90deg, rgba(255,170,68,0.5), transparent); }}

/* ── CATEGORY TABS ── */
.cat-tabs {{
  display: flex;
  gap: 0;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  background: #101010;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}}
.cat-tabs::-webkit-scrollbar {{ display:none; }}
.cat-tab {{
  padding: 9px 18px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: #999999;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: all 0.15s;
  flex-shrink: 0;
}}
.cat-tab:hover {{ color: var(--white); }}
.cat-tab.active {{
  color: var(--orange);
  border-bottom-color: var(--orange);
}}

/* ── NEWS AREA ── */
.news-area {{ flex: 1; padding: 16px 18px; overflow-y: auto; }}
.news-hdr {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
}}
.news-hdr-title {{
  color: var(--orange);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
}}
.news-hdr-meta {{ color: #aaaaaa; font-size: 11px; }}

/* ── NEWSPAPER COLUMN — COMPACT STYLE ── */
.news-col {{ border: 1px solid var(--border); border-radius: 3px; overflow: hidden; }}

.nc-item {{
  border-bottom: 1px solid #1e1e1e;
  cursor: pointer;
  transition: background 0.12s;
  user-select: none;
}}
.nc-item:last-of-type {{ border-bottom: none; }}
.nc-item:hover {{ background: rgba(255,106,0,0.04); }}
.nc-item.open {{ background: rgba(255,106,0,0.06); border-left: 2px solid var(--orange); }}

.nc-row {{
  display: grid;
  grid-template-columns: 36px 1fr 24px;
  align-items: center;
  padding: 13px 12px 13px 0;
  gap: 4px;
}}
.nc-num {{
  font-size: 12px; font-weight: 700;
  color: var(--orange); opacity: 0.55;
  font-family: 'IBM Plex Mono', monospace;
  text-align: right; padding-right: 4px;
}}
.nc-headline {{
  font-family: 'DM Sans', sans-serif;
  font-size: 17px; font-weight: 500;
  color: #e8e8e8; line-height: 1.55;
  letter-spacing: 0.1px;
}}
.nc-arrow {{
  color: #555; font-size: 9px;
  text-align: center; transition: transform 0.2s, color 0.15s;
}}
.nc-item:hover .nc-arrow {{ color: var(--orange); }}
.nc-item.open .nc-arrow {{ transform: rotate(180deg); color: var(--orange); }}

.nc-expand-body {{
  display: none;
  padding: 0 14px 12px 36px;
  border-top: 1px dashed #2a2a2a;
}}
.nc-expand-body.open {{ display: block; animation: fadeIn 0.18s ease; }}
@keyframes fadeIn {{ from {{ opacity:0; transform:translateY(-3px); }} to {{ opacity:1; transform:translateY(0); }} }}

.nc-meta {{
  display: flex; align-items: center; gap: 6px;
  padding: 8px 0 6px;
}}
.nc-src {{
  font-family: 'DM Sans', sans-serif;
  font-size: 12px; font-weight: 600; letter-spacing: 0.5px;
  padding: 2px 7px; border-radius: 3px;
  background: rgba(255,106,0,0.14); color: var(--orange);
  text-transform: uppercase;
}}
.nc-sep {{ color: #444; font-size: 12px; }}
.nc-time {{ font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #666; }}
.nc-summary {{
  font-family: 'DM Sans', sans-serif;
  font-size: 15px; color: #aaaaaa;
  line-height: 1.7; margin-bottom: 8px;
}}
.nc-link {{
  display: inline-block;
  font-family: 'DM Sans', sans-serif;
  color: var(--orange); font-size: 13px; font-weight: 600;
  text-decoration: none; letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(255,106,0,0.3);
  padding-bottom: 1px; transition: opacity 0.15s;
}}
.nc-link:hover {{ opacity: 0.7; }}

.no-news {{
  color: #777; font-size: 12px;
  padding: 20px 14px; font-family: 'DM Sans', sans-serif;
}}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 4px; height: 4px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 2px; }}

/* ── HAMBURGER BUTTON ── */
.hamburger {{
  display: none;
  flex-direction: column; justify-content: center; gap: 4px;
  width: 32px; height: 32px; cursor: pointer;
  padding: 4px; border-radius: 3px;
  transition: background 0.15s; flex-shrink: 0;
}}
.hamburger:hover {{ background: rgba(0,0,0,0.2); }}
.hamburger span {{ display: block; width: 20px; height: 2px; background: #000; border-radius: 2px; }}

/* ── SIDEBAR OVERLAY (mobile) ── */
.sidebar-overlay {{
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7); z-index: 200;
}}
.sidebar-overlay.open {{ display: block; }}

/* ── RESPONSIVE — Tablet ── */
@media (max-width: 900px) {{
  .shell {{ grid-template-columns: 1fr; height: auto; }}
  .sidebar {{
    position: fixed; top: 0; left: -265px; bottom: 0;
    width: 265px; z-index: 300;
    transition: left 0.25s ease; padding-top: 50px;
  }}
  .sidebar.open {{ left: 0; }}
  .hamburger {{ display: flex; }}
  .topbar-right span:nth-child(3) {{ display: none; }}
  .ind-row {{ flex-wrap: wrap; }}
  .ind-cell {{ min-width: 110px; }}
  .news-area {{ padding: 12px 10px; }}
  .statusbar span:first-child {{ font-size: 9px; letter-spacing: 0; }}
}}

/* ── RESPONSIVE — Mobile ── */
@media (max-width: 600px) {{
  body {{ font-size: 13px; }}
  .topbar {{ padding: 5px 10px; }}
  .topbar-right {{ gap: 10px; font-size: 10px; }}
  .topbar-right span:nth-child(3), .topbar-right span:nth-child(4) {{ display: none; }}
  .ticker-item {{ padding: 0 14px; font-size: 11px; }}
  .cat-tabs {{ padding: 0 6px; }}
  .cat-tab {{ padding: 8px 10px; font-size: 10px; letter-spacing: 0.5px; }}
  .news-area {{ padding: 10px 8px; }}
  .news-hdr {{ margin-bottom: 10px; padding-bottom: 8px; }}
  .news-hdr-title {{ font-size: 10px; }}
  .news-hdr-meta {{ display: none; }}
  .nc-row {{ padding: 8px 8px 8px 0; }}
  .nc-headline {{ font-size: 12.5px; }}
  .nc-expand-body {{ padding: 0 8px 10px 30px; }}
  .statusbar {{ padding: 3px 8px; font-size: 9px; }}
  .statusbar span:first-child {{ display: none; }}
  .ind-cell {{ min-width: 90px; padding: 8px 10px; }}
  .ind-val {{ font-size: 14px; }}
}}
</style>
</head>
<body>

<!-- LOADING OVERLAY -->
<div class="loading-overlay" id="loadingOverlay">
  <div class="spinner"></div>
  <div class="loading-text">Loading Market Data…</div>
</div>

<!-- TOP BAR -->
<div class="topbar">
  <div class="topbar-left">
    <div class="hamburger" onclick="toggleSidebar()" aria-label="Menu">
      <span></span><span></span><span></span>
    </div>
    <div class="topbar-dot"></div>
    <span>🌐 NEXUSFEED</span>
  </div>
  <div class="topbar-right">
    <span>🔴 LIVE FEED</span>
    <span id="topClock">--:--:-- IST</span>
    <span>📅 {current_time}</span>
    <span>✅ {total_articles} ARTICLES</span>
  </div>
</div>

<!-- TICKER STRIP -->
<div class="ticker">
  <div class="ticker-track" id="tickerTrack">
    <!-- populated by JS -->
  </div>
</div>

<!-- SIDEBAR OVERLAY (mobile) -->
<div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>

<!-- MAIN SHELL -->
<div class="shell">

  <!-- ═══ SIDEBAR ═══ -->
  <div class="sidebar">

    <!-- 1. USA ECONOMIC (collapsible) ── -->
    <div class="sb-section">
      <div class="sb-econ-hdr" onclick="toggleEcon('usa')">
        <span class="sb-econ-title usa">🇺🇸 USA ECONOMIC</span>
        <span class="sb-econ-arrow" id="arrow-usa">▼</span>
      </div>
      <div class="sb-econ-body" id="body-usa">
        <div class="sb-econ-row"><span class="sb-econ-key">Fed Funds Rate</span><span class="sb-econ-val neu">4.25–4.50%</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">FOMC Next</span><span class="sb-econ-val neu">Hold</span><span class="sb-econ-note">Mar 18–19</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">CPI YoY</span><span class="sb-econ-val neu" id="sbv-cpi">--</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">Core CPI</span><span class="sb-econ-val neu">3.3%</span><span class="sb-econ-note">Dec 2025</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">GDP Growth</span><span class="sb-econ-val pos">2.8%</span><span class="sb-econ-note">Q4 2025</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">Unemployment</span><span class="sb-econ-val pos">4.1%</span><span class="sb-econ-note">Jan 2026</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">NFP</span><span class="sb-econ-val pos">+256K</span><span class="sb-econ-note">Jan 2026</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">PPI YoY</span><span class="sb-econ-val neu">3.3%</span><span class="sb-econ-note">Dec 2025</span></div>
      </div>
    </div>

    <!-- 2. INDIA ECONOMIC (collapsible) ── -->
    <div class="sb-section">
      <div class="sb-econ-hdr" onclick="toggleEcon('india')">
        <span class="sb-econ-title india">🇮🇳 INDIA ECONOMIC</span>
        <span class="sb-econ-arrow" id="arrow-india">▼</span>
      </div>
      <div class="sb-econ-body" id="body-india">
        <div class="sb-econ-row"><span class="sb-econ-key">Repo Rate</span><span class="sb-econ-val neu">6.25%</span><span class="sb-econ-note">RBI Feb 2026</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">CPI</span><span class="sb-econ-val neu">5.22%</span><span class="sb-econ-note">Dec 2025</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">WPI</span><span class="sb-econ-val neu">2.4%</span><span class="sb-econ-note">Nov 2025</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">IIP</span><span class="sb-econ-val pos">5.2%</span><span class="sb-econ-note">Nov 2025</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">Mfg PMI</span><span class="sb-econ-val pos">57.7</span><span class="sb-econ-note">Jan 2026</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">GDP Growth</span><span class="sb-econ-val pos">6.4%</span><span class="sb-econ-note">FY25</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">Fiscal Deficit</span><span class="sb-econ-val neu">4.9%</span><span class="sb-econ-note">FY25 Target</span></div>
        <div class="sb-econ-row"><span class="sb-econ-key">USD/INR</span><span class="sb-econ-val neu" id="sbv-usdinr2">₹--</span></div>
      </div>
    </div>

    <!-- 3. LIVE PRICES ── -->
    <div class="sb-section">
      <div class="sb-label">▶ LIVE PRICES</div>
      <div class="sb-ind-row"><span class="sb-ind-name">S&amp;P 500</span>    <span class="sb-ind-val neu" id="sbv-sp500">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Dow Jones</span>   <span class="sb-ind-val neu" id="sbv-dow">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nasdaq</span>      <span class="sb-ind-val neu" id="sbv-nasdaq">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Nifty 50</span>    <span class="sb-ind-val neu" id="sbv-nifty">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Sensex</span>      <span class="sb-ind-val neu" id="sbv-sensex">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD/INR</span>     <span class="sb-ind-val neu" id="sbv-usdinr">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Crude Oil</span>   <span class="sb-ind-val neu" id="sbv-oil">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Gold</span>        <span class="sb-ind-val neu" id="sbv-gold">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Silver</span>      <span class="sb-ind-val neu" id="sbv-silver">--</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">USD Index</span>   <span class="sb-ind-val neu" id="sbv-dollar">--</span></div>
    </div>

    <!-- 4. CATEGORIES ── -->
    <div class="sb-section">
      <div class="sb-label">▶ CATEGORIES</div>
      <div class="sb-item active" id="sb-markets"            onclick="switchCat('markets',this)">
        <span class="sb-name">📊 Markets</span>
        <span class="sb-count">{cat_counts["markets"]}</span>
      </div>
      <div class="sb-item" id="sb-macro_policy"      onclick="switchCat('macro_policy',this)">
        <span class="sb-name">💰 Macro & Policy</span>
        <span class="sb-count">{cat_counts["macro_policy"]}</span>
      </div>
      <div class="sb-item" id="sb-banking_fx"        onclick="switchCat('banking_fx',this)">
        <span class="sb-name">🏦 Banking & FX</span>
        <span class="sb-count">{cat_counts["banking_fx"]}</span>
      </div>
      <div class="sb-item" id="sb-commodities_energy" onclick="switchCat('commodities_energy',this)">
        <span class="sb-name">📦 Commodities & Energy</span>
        <span class="sb-count">{cat_counts["commodities_energy"]}</span>
      </div>
      <div class="sb-item" id="sb-india"             onclick="switchCat('india',this)">
        <span class="sb-name">🇮🇳 India</span>
        <span class="sb-count">{cat_counts["india"]}</span>
      </div>
      <div class="sb-item" id="sb-trending"          onclick="switchCat('trending',this)">
        <span class="sb-name">🔥 Trending</span>
        <span class="sb-count">{cat_counts["trending"]}</span>
      </div>
      <div class="sb-item" id="sb-corporate"         onclick="switchCat('corporate',this)">
        <span class="sb-name">🏢 Corporate</span>
        <span class="sb-count">{cat_counts["corporate"]}</span>
      </div>
      <div class="sb-item" id="sb-geopolitical"      onclick="switchCat('geopolitical',this)">
        <span class="sb-name">🌍 Geopolitical</span>
        <span class="sb-count">{cat_counts["geopolitical"]}</span>
      </div>
      <div class="sb-item" id="sb-crypto"            onclick="switchCat('crypto',this)">
        <span class="sb-name">📉 Crypto & Web3</span>
        <span class="sb-count">{cat_counts["crypto"]}</span>
      </div>
      <div class="sb-item" id="sb-tech_ai"           onclick="switchCat('tech_ai',this)">
        <span class="sb-name">🤖 Tech & AI</span>
        <span class="sb-count">{cat_counts["tech_ai"]}</span>
      </div>
      <div class="sb-item" id="sb-asia_china"        onclick="switchCat('asia_china',this)">
        <span class="sb-name">🌏 Asia & China</span>
        <span class="sb-count">{cat_counts["asia_china"]}</span>
      </div>
      <div class="sb-item" id="sb-europe_uk"         onclick="switchCat('europe_uk',this)">
        <span class="sb-name">🇪🇺 Europe & UK</span>
        <span class="sb-count">{cat_counts["europe_uk"]}</span>
      </div>
      <div class="sb-item" id="sb-esg_climate"       onclick="switchCat('esg_climate',this)">
        <span class="sb-name">🌱 ESG & Climate</span>
        <span class="sb-count">{cat_counts["esg_climate"]}</span>
      </div>
    </div>

    <!-- Sources ── -->
    <div class="sb-section">
      <div class="sb-label">▶ SOURCES</div>
      <div class="sb-ind-row"><span class="sb-ind-name">CNBC</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">MarketWatch</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Economic Times</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">MoneyControl</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Yahoo Finance</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Google News</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Federal Reserve</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">CoinTelegraph</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">CoinDesk</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters UK</span></div>
      <div class="sb-ind-row"><span class="sb-ind-name">Reuters China</span></div>
    </div>

  </div><!-- /sidebar -->

  <!-- ═══ MAIN ═══ -->
  <div class="main">

    <!-- Hidden elements kept for JS ticker/sidebar updates (panel removed – prices shown in sidebar + ticker) -->
    <div style="display:none">
      <span id="card-gift-nifty"></span><span id="val-gift-nifty"></span><span id="chg-gift-nifty"></span>
      <span id="card-dow"></span><span id="val-dow"></span><span id="chg-dow"></span>
      <span id="card-sp500"></span><span id="val-sp500"></span><span id="chg-sp500"></span>
      <span id="card-nasdaq"></span><span id="val-nasdaq"></span><span id="chg-nasdaq"></span>
      <span id="card-oil"></span><span id="val-oil"></span><span id="chg-oil"></span>
      <span id="card-dollar"></span><span id="val-dollar"></span><span id="chg-dollar"></span>
      <span id="card-gold"></span><span id="val-gold"></span><span id="chg-gold"></span>
      <span id="card-silver"></span><span id="val-silver"></span><span id="chg-silver"></span>
    </div>

    <!-- ── CATEGORY TABS ── -->
    <div class="cat-tabs" id="catTabs">
      <div class="cat-tab active" id="tab-markets"           onclick="switchCat('markets',null)">📊 MARKETS</div>
      <div class="cat-tab"        id="tab-macro_policy"      onclick="switchCat('macro_policy',null)">💰 MACRO</div>
      <div class="cat-tab"        id="tab-banking_fx"        onclick="switchCat('banking_fx',null)">🏦 BANKING & FX</div>
      <div class="cat-tab"        id="tab-commodities_energy" onclick="switchCat('commodities_energy',null)">📦 COMMODITIES</div>
      <div class="cat-tab"        id="tab-india"             onclick="switchCat('india',null)">🇮🇳 INDIA</div>
      <div class="cat-tab"        id="tab-trending"          onclick="switchCat('trending',null)">🔥 TRENDING</div>
      <div class="cat-tab"        id="tab-corporate"         onclick="switchCat('corporate',null)">🏢 CORPORATE</div>
      <div class="cat-tab"        id="tab-geopolitical"      onclick="switchCat('geopolitical',null)">🌍 GEOPOLITICAL</div>
      <div class="cat-tab"        id="tab-crypto"            onclick="switchCat('crypto',null)">📉 CRYPTO</div>
      <div class="cat-tab"        id="tab-tech_ai"           onclick="switchCat('tech_ai',null)">🤖 TECH & AI</div>
      <div class="cat-tab"        id="tab-asia_china"        onclick="switchCat('asia_china',null)">🌏 ASIA & CHINA</div>
      <div class="cat-tab"        id="tab-europe_uk"         onclick="switchCat('europe_uk',null)">🇪🇺 EUROPE & UK</div>
      <div class="cat-tab"        id="tab-esg_climate"       onclick="switchCat('esg_climate',null)">🌱 ESG & CLIMATE</div>
    </div>

    <!-- ── NEWS AREA ── -->
    <div class="news-area">
      <div class="news-hdr">
        <span class="news-hdr-title" id="newsTitle">▶ MARKET UPDATES</span>
        <span class="news-hdr-meta" id="newsSubtitle">Click headline to expand · {current_time}</span>
      </div>
      <div class="news-col" id="newsCol"></div>
    </div>

  </div><!-- /main -->
</div><!-- /shell -->

<!-- STATUS BAR -->
<div class="statusbar">
  <span>NEXUSFEED · RSS FEEDS: 43 SOURCES · 13 CATEGORIES · AUTO-REFRESH: 5 MIN · NOT FINANCIAL ADVICE</span>
  <span id="statusClock">--:-- IST</span>
</div>

<!-- ══════════════════════════════════════════
     SCRIPTS
══════════════════════════════════════════ -->
<script>
// ── All news injected by Python ──
const NEWS_DATA = {news_json};

// ── Current active category ──
let currentCat = 'markets';

// ════════════════════════════
// RENDER NEWS — NEWSPAPER COLUMN (Option B)
// ════════════════════════════
function renderNews(cat) {{
  const d = NEWS_DATA[cat];
  if (!d) return;
  const col = document.getElementById('newsCol');
  const items = d.items;

  if (!items || items.length === 0) {{
    col.innerHTML = '<div class="no-news">No articles available for this category.</div>';
    document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — 0 ARTICLES';
    return;
  }}

  col.innerHTML = items.map((item, i) => {{
    const num = String(i + 1).padStart(2, '0');
    const link = item.link && item.link !== '#'
      ? `<a class="nc-link" href="${{item.link}}" target="_blank" rel="noopener">Read Full Article ↗</a>`
      : '';
    return `<div class="nc-item" onclick="toggleNC(this)" id="nc-${{cat}}-${{i}}">
  <div class="nc-row">
    <span class="nc-num">${{num}}</span>
    <span class="nc-headline">${{item.title}}</span>
    <span class="nc-arrow">▼</span>
  </div>
  <div class="nc-expand-body" id="nc-exp-${{cat}}-${{i}}">
    <div class="nc-meta">
      <span class="nc-src">${{item.source}}</span>
      <span class="nc-sep">·</span>
      <span class="nc-time">${{item.time}}</span>
    </div>
    <div class="nc-summary">${{item.summary}}</div>
    ${{link}}
  </div>
</div>`;
  }}).join('');

  document.getElementById('newsTitle').textContent = '▶ ' + d.label + ' — ' + items.length + ' ARTICLES';
}}
function toggleNC(row) {{
  row.classList.toggle('open');
  const exp = row.querySelector('.nc-expand-body');
  if (exp) exp.classList.toggle('open');
}}

// ════════════════════════════
// HAMBURGER / SIDEBAR DRAWER
// ════════════════════════════
function toggleSidebar() {{
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const isOpen  = sidebar.classList.contains('open');
  sidebar.classList.toggle('open', !isOpen);
  overlay.classList.toggle('open', !isOpen);
}}

// ════════════════════════════
// SWITCH CATEGORY
// ════════════════════════════
function switchCat(cat, sidebarEl) {{
  currentCat = cat;

  // Update sidebar items
  document.querySelectorAll('.sb-item').forEach(el => el.classList.remove('active'));
  const sbEl = document.getElementById('sb-' + cat);
  if (sbEl) sbEl.classList.add('active');

  // Update tabs
  document.querySelectorAll('.cat-tab').forEach(el => el.classList.remove('active'));
  const tabEl = document.getElementById('tab-' + cat);
  if (tabEl) tabEl.classList.add('active');

  renderNews(cat);
}}

// ════════════════════════════
// TOGGLE ECON SECTIONS IN SIDEBAR
// ════════════════════════════
function toggleEcon(id) {{
  const body  = document.getElementById('body-'  + id);
  const arrow = document.getElementById('arrow-' + id);
  if (!body) return;
  body.classList.toggle('collapsed');
  arrow.classList.toggle('collapsed');
  // Set explicit max-height for smooth animation
  if (!body.classList.contains('collapsed')) {{
    body.style.maxHeight = body.scrollHeight + 'px';
  }} else {{
    body.style.maxHeight = '0';
  }}
}}

// ════════════════════════════
// TICKER STRIP
// ════════════════════════════
const TICKER_SYMBOLS = [
  ['GIFT NIFTY', 'gift-nifty'],
  ['DOW',    'dow'],
  ['S&P 500','sp500'],
  ['NASDAQ', 'nasdaq'],
  ['CRUDE',  'oil'],
  ['GOLD',   'gold'],
  ['SILVER', 'silver'],
  ['USD IDX','dollar'],
  ['USD/INR','usdinr'],
];

function buildTicker() {{
  const track = document.getElementById('tickerTrack');
  // Double for seamless loop
  const items = [...TICKER_SYMBOLS, ...TICKER_SYMBOLS];
  track.innerHTML = items.map(([name, key]) => `
    <span class="ticker-item" id="tick-${{key}}">
      <span class="t-sym">${{name}}</span>
      <span class="t-val t-neu" id="tv-${{key}}">--</span>
    </span>
  `).join('');
}}

function updateTicker(key, val, pct) {{
  const el = document.getElementById('tv-' + key);
  if (!el) return;
  const p = parseFloat(pct);
  el.textContent = val + (pct ? ' (' + (p >= 0 ? '+' : '') + pct + '%)' : '');
  el.className = 't-val ' + (p > 0 ? 't-pos' : p < 0 ? 't-neg' : 't-neu');

  // Update duplicate ticker item too
  const els = document.querySelectorAll('[id="tv-' + key + '"]');
  els.forEach(e => {{
    e.textContent = el.textContent;
    e.className = el.className;
  }});
}}

// ════════════════════════════
// INDICATOR CARD UPDATE
// ════════════════════════════
function updateCard(id, value, change, pchange) {{
  const vEl = document.getElementById('val-' + id);
  const cEl = document.getElementById('chg-' + id);
  const card = document.getElementById('card-' + id);
  if (vEl) vEl.textContent = value;
  if (cEl) {{
    const p = parseFloat(pchange);
    const sign = p >= 0 ? '+' : '';
    cEl.textContent = sign + change + ' (' + sign + pchange + '%)';
    const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
    cEl.className = 'ind-chg ' + cls;
    if (card) card.className = 'ind-cell ' + cls;
  }}
  // Update sidebar
  const sbEl = document.getElementById('sbv-' + id);
  if (sbEl) {{
    sbEl.textContent = value;
    const p = parseFloat(pchange);
    sbEl.className = 'sb-ind-val ' + (p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu');
  }}
  updateTicker(id, value, pchange);
}}

// ════════════════════════════
// YAHOO FINANCE FETCH
// ════════════════════════════
const SYMBOLS = {{
  'dow':    '^DJI',
  'sp500':  '^GSPC',
  'nasdaq': '^IXIC',
  'oil':    'CL=F',
  'dollar': 'DX-Y.NYB',
  'gold':   'GC=F',
  'silver': 'SI=F',
  'usdinr': 'INR=X'
}};

async function fetchYahoo(key, sym) {{
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${{sym}}?interval=1d&range=1d`;
  const proxies = [
    'https://corsproxy.io/?' + encodeURIComponent(url),
    'https://api.allorigins.win/get?url=' + encodeURIComponent(url),
    url
  ];
  for (const u of proxies) {{
    try {{
      const r = await fetch(u, {{mode: 'cors'}});
      if (!r.ok) continue;
      let d = await r.json();
      if (d.contents) d = JSON.parse(d.contents);
      const meta = d?.chart?.result?.[0]?.meta;
      if (!meta) continue;
      const cur = meta.regularMarketPrice;
      const prev = meta.chartPreviousClose || meta.previousClose;
      if (!cur || !prev) continue;
      const chg = (cur - prev).toFixed(2);
      const pct = (((cur - prev) / prev) * 100).toFixed(2);
      let val = ['dow', 'sp500', 'nasdaq'].includes(key)
        ? cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}})
        : key === 'dollar' ? cur.toFixed(2)
        : key === 'usdinr' ? '₹' + cur.toFixed(2)
        : '$' + cur.toFixed(2);
      updateCard(key, val, chg, pct);
      // Extra sidebar updates for nifty/sensex placeholder
      if (key === 'usdinr') {{
        const sbEl = document.getElementById('sbv-usdinr');
        if (sbEl) {{ sbEl.textContent = '₹' + cur.toFixed(2); }}
        const sbEl2 = document.getElementById('sbv-usdinr2');
        if (sbEl2) {{ sbEl2.textContent = '₹' + cur.toFixed(2); }}
      }}
      return true;
    }} catch (e) {{ /* try next */ }}
  }}
  return false;
}}

// ════════════════════════════
// GIFT NIFTY FETCH
// ════════════════════════════
async function fetchGiftNifty() {{
  // Attempt 1: NSE IFSC via CORS proxy
  const nseUrl = 'https://www.nseifsc.com/market/GetIndexChartDetails?indices=NIFTY50&type=I';
  try {{
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(nseUrl), {{mode: 'cors', signal: AbortSignal.timeout(6000)}});
    if (r.ok) {{
      const d = await r.json();
      if (d && d.length > 0) {{
        const last = d[d.length - 1];
        const first = d[0];
        const cur = parseFloat(last[1]);
        const prev = parseFloat(first[1]);
        if (cur && prev) {{
          const chg = (cur - prev).toFixed(2);
          const pct = (((cur - prev) / prev) * 100).toFixed(2);
          const val = cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · NSE IX';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          // sidebar nifty
          const sbN = document.getElementById('sbv-nifty');
          if (sbN) {{ sbN.textContent = val; sbN.className = 'sb-ind-val ' + (parseFloat(pct) > 0 ? 'pos' : parseFloat(pct) < 0 ? 'neg' : 'neu'); }}
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Attempt 2: Stooq
  try {{
    const stooqUrl = 'https://stooq.com/q/l/?s=nifty.ix&f=sd2t2ohlcv&e=csv';
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(stooqUrl), {{signal: AbortSignal.timeout(5000)}});
    if (r.ok) {{
      const text = await r.text();
      const lines = text.trim().split('\\n');
      if (lines.length >= 2) {{
        const cols = lines[1].split(',');
        const close = parseFloat(cols[6]);
        const open = parseFloat(cols[3]);
        if (close && open) {{
          const chg = (close - open).toFixed(2);
          const pct = (((close - open) / open) * 100).toFixed(2);
          const val = close.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · NSE IX ~';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Attempt 3: Fallback – Nifty 50 spot as proxy
  try {{
    const url = 'https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=1d';
    const r = await fetch('https://corsproxy.io/?' + encodeURIComponent(url), {{mode: 'cors', signal: AbortSignal.timeout(5000)}});
    if (r.ok) {{
      const d = await r.json();
      const meta = d?.chart?.result?.[0]?.meta;
      if (meta) {{
        const cur = meta.regularMarketPrice;
        const prev = meta.chartPreviousClose || meta.previousClose;
        if (cur && prev) {{
          const chg = (cur - prev).toFixed(2);
          const pct = (((cur - prev) / prev) * 100).toFixed(2);
          const val = cur.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          const titleEl = document.querySelector('#card-gift-nifty .ind-name');
          if (titleEl) titleEl.textContent = '⚠ NIFTY 50 (GIFT proxy)';
          const vEl = document.getElementById('val-gift-nifty');
          const cEl = document.getElementById('chg-gift-nifty');
          const card = document.getElementById('card-gift-nifty');
          if (vEl) vEl.textContent = val;
          if (cEl) {{
            const p = parseFloat(pct);
            const sign = p >= 0 ? '+' : '';
            cEl.textContent = sign + chg + ' (' + sign + pct + '%) · INR spot';
            const cls = p > 0 ? 'pos' : p < 0 ? 'neg' : 'neu';
            cEl.className = 'ind-chg ' + cls;
            if (card) card.className = 'ind-cell ' + cls;
          }}
          updateTicker('gift-nifty', val, pct);
          // sidebar sensex/nifty
          const sbN = document.getElementById('sbv-nifty');
          if (sbN) {{ sbN.textContent = val; sbN.className = 'sb-ind-val ' + (parseFloat(pct) > 0 ? 'pos' : parseFloat(pct) < 0 ? 'neg' : 'neu'); }}
          return;
        }}
      }}
    }}
  }} catch (e) {{ /* fall through */ }}

  // Hard fallback
  const vEl = document.getElementById('val-gift-nifty');
  const cEl = document.getElementById('chg-gift-nifty');
  if (vEl) vEl.textContent = 'N/A';
  if (cEl) cEl.textContent = 'Data unavailable';
}}

// ════════════════════════════
// CPI via FRED CSV (CORS proxy)
// ════════════════════════════
async function fetchCPI() {{
  const csvUrl = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL';
  const proxied = 'https://corsproxy.io/?' + encodeURIComponent(csvUrl);
  try {{
    const r = await fetch(proxied, {{signal: AbortSignal.timeout(8000)}});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const text = await r.text();
    const lines = text.trim().split('\\n').filter(l => l && !l.startsWith('DATE'));
    if (lines.length < 13) throw new Error('Not enough data');
    const lastLine = lines[lines.length - 1].split(',');
    const prevLine = lines[lines.length - 13].split(',');
    const lastVal = parseFloat(lastLine[1]);
    const prevVal = parseFloat(prevLine[1]);
    if (isNaN(lastVal) || isNaN(prevVal) || prevVal === 0) throw new Error('Bad values');
    const yoy = (((lastVal - prevVal) / prevVal) * 100).toFixed(1);
    const date = lastLine[0];
    const d = new Date(date + 'T12:00:00Z');
    const label = d.toLocaleString('en-US', {{month: 'short', year: 'numeric', timeZone: 'UTC'}});
    const vEl = document.getElementById('val-cpi');
    const cEl = document.getElementById('chg-cpi');
    const card = vEl ? vEl.closest('.ind-cell') : null;
    if (vEl) vEl.textContent = yoy + '%';
    if (cEl) cEl.textContent = 'YoY · ' + label;
    if (card) {{
      const p = parseFloat(yoy);
      card.className = 'ind-cell ' + (p > 3 ? 'neg' : p <= 2 ? 'pos' : 'neu');
    }}
    // Update sidebar CPI
    const sbCpi = document.getElementById('sbv-cpi');
    if (sbCpi) {{ sbCpi.textContent = yoy + '%'; sbCpi.className = 'sb-econ-val ' + (parseFloat(yoy) > 3 ? 'neg' : parseFloat(yoy) <= 2 ? 'pos' : 'neu'); }}
  }} catch (e) {{
    const vEl = document.getElementById('val-cpi');
    const cEl = document.getElementById('chg-cpi');
    if (vEl) vEl.textContent = '2.9%';
    if (cEl) cEl.textContent = 'YoY · Dec 2025 (cached)';
    const sbCpi = document.getElementById('sbv-cpi');
    if (sbCpi) {{ sbCpi.textContent = '2.9%'; }}
  }}
}}

// ════════════════════════════
// CLOCK & REFRESH
// ════════════════════════════
function updateClock() {{
  const now = new Date();
  const opts = {{hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Kolkata'}};
  const ist = now.toLocaleString('en-US', opts);
  const el = document.getElementById('topClock');
  if (el) el.textContent = ist + ' IST';
  const st = document.getElementById('statusClock');
  if (st) st.textContent = ist + ' IST';
  const ref = document.getElementById('newsSubtitle');
  if (ref) {{
    const opts2 = {{hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata'}};
    ref.textContent = 'Click any headline to expand · Last refresh: ' + now.toLocaleString('en-US', opts2) + ' IST';
  }}
}}

let isFirstLoad = true;

async function loadAll() {{
  fetchGiftNifty();
  await Promise.all(
    Object.entries(SYMBOLS).map(async ([k, s]) => {{
      const ok = await fetchYahoo(k, s);
      if (!ok) {{
        const vEl = document.getElementById('val-' + k);
        const cEl = document.getElementById('chg-' + k);
        if (vEl) vEl.textContent = 'N/A';
        if (cEl) cEl.textContent = 'Unavailable';
      }}
    }})
  );
  updateClock();
  if (isFirstLoad) {{
    setTimeout(() => document.getElementById('loadingOverlay').classList.remove('visible'), 500);
    isFirstLoad = false;
  }}
}}

// ════════════════════════════
// INIT
// ════════════════════════════
window.addEventListener('DOMContentLoaded', () => {{
  buildTicker();
  renderNews('markets');

  // Set initial max-height for smooth collapse animation
  ['usa', 'india'].forEach(id => {{
    const body = document.getElementById('body-' + id);
    if (body) body.style.maxHeight = body.scrollHeight + 'px';
  }});

  if (!sessionStorage.getItem('visited')) {{
    document.getElementById('loadingOverlay').classList.add('visible');
    sessionStorage.setItem('visited', '1');
  }}

  loadAll();
  fetchCPI();
  setInterval(loadAll, 5 * 60 * 1000);
  setInterval(updateClock, 1000);
}});
</script>
</body>
</html>"""


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    print("\n" + "=" * 70)
    print("🚀  GLOBAL MARKET DASHBOARD  –  BLOOMBERG TERMINAL THEME")
    print("    11 CATEGORIES · 33 RSS SOURCES")
    print("=" * 70)

    all_news = {}
    for category, urls in RSS_SOURCES.items():
        print(f"\n📂 Fetching [{category.upper()}] news …")
        items = fetch_category_news(category, urls)
        all_news[category] = items
        print(f"   ✓ {len(items)} articles collected")

    total = sum(len(v) for v in all_news.values())
    print(f"\n📊 Total articles fetched: {total}")

    print("\n🖊  Generating index.html …")
    html = generate_complete_html(all_news)

    output = "index.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)

    print("\n" + "=" * 70)
    print(f"✅  SUCCESS!  Dashboard written to: {output}")
    print("=" * 70)
    print("\n💡 Every time you run this script the news refreshes automatically.")
    print("   Click any headline in the browser to expand and read the summary.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
