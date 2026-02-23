"""
MarketIntel — Stock Technical & Fundamental Analysis
Supports: Nifty 50 (India) + S&P Top 50 (US)
Timeframes: 15m, 1H, 1D, 1W
Output: Interactive HTML dashboard
"""

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ─────────────────────────────────────────────
# STOCK UNIVERSE
# ─────────────────────────────────────────────

STOCKS = {
    "IN": {
        "Technology": [
            ("TCS.NS",       "Tata Consultancy Services"),
            ("INFY.NS",      "Infosys"),
            ("WIPRO.NS",     "Wipro"),
            ("HCLTECH.NS",   "HCL Technologies"),
            ("TECHM.NS",     "Tech Mahindra"),
            ("LTIM.NS",      "LTIMindtree"),
            ("MPHASIS.NS",   "Mphasis"),
        ],
        "Financials": [
            ("HDFCBANK.NS",  "HDFC Bank"),
            ("ICICIBANK.NS", "ICICI Bank"),
            ("KOTAKBANK.NS", "Kotak Mahindra Bank"),
            ("AXISBANK.NS",  "Axis Bank"),
            ("SBIN.NS",      "State Bank of India"),
            ("BAJFINANCE.NS","Bajaj Finance"),
            ("BAJAJFINSV.NS","Bajaj Finserv"),
        ],
        "Energy": [
            ("RELIANCE.NS",  "Reliance Industries"),
            ("ONGC.NS",      "ONGC"),
            ("BPCL.NS",      "BPCL"),
            ("IOC.NS",       "Indian Oil Corporation"),
            ("ADANIGREEN.NS","Adani Green Energy"),
        ],
        "Healthcare": [
            ("SUNPHARMA.NS", "Sun Pharmaceutical"),
            ("DRREDDY.NS",   "Dr. Reddy's Laboratories"),
            ("CIPLA.NS",     "Cipla"),
            ("DIVISLAB.NS",  "Divi's Laboratories"),
            ("APOLLOHOSP.NS","Apollo Hospitals"),
        ],
        "Consumer": [
            ("HINDUNILVR.NS","Hindustan Unilever"),
            ("ITC.NS",       "ITC Limited"),
            ("NESTLEIND.NS", "Nestle India"),
            ("TITAN.NS",     "Titan Company"),
            ("ASIANPAINT.NS","Asian Paints"),
            ("MARUTI.NS",    "Maruti Suzuki"),
            ("TATAMOTORS.NS","Tata Motors"),
        ],
        "Telecom": [
            ("BHARTIARTL.NS","Bharti Airtel"),
        ],
        "Industrials": [
            ("ADANIENT.NS",  "Adani Enterprises"),
            ("LTTS.NS",      "L&T Technology Services"),
            ("POWERGRID.NS", "Power Grid Corporation"),
            ("NTPC.NS",      "NTPC"),
        ],
        "Metals & Mining": [
            ("TATASTEEL.NS", "Tata Steel"),
            ("JSWSTEEL.NS",  "JSW Steel"),
            ("HINDALCO.NS",  "Hindalco Industries"),
            ("COALINDIA.NS", "Coal India"),
        ],
    },
    "US": {
        "Technology": [
            ("AAPL",  "Apple Inc."),
            ("MSFT",  "Microsoft"),
            ("GOOGL", "Alphabet (Google)"),
            ("NVDA",  "NVIDIA"),
            ("META",  "Meta Platforms"),
            ("AMZN",  "Amazon"),
            ("TSLA",  "Tesla"),
            ("ORCL",  "Oracle"),
            ("CRM",   "Salesforce"),
            ("ADBE",  "Adobe"),
        ],
        "Financials": [
            ("JPM",   "JPMorgan Chase"),
            ("BAC",   "Bank of America"),
            ("WFC",   "Wells Fargo"),
            ("GS",    "Goldman Sachs"),
            ("MS",    "Morgan Stanley"),
            ("BRK-B", "Berkshire Hathaway"),
            ("V",     "Visa"),
            ("MA",    "Mastercard"),
        ],
        "Energy": [
            ("XOM",   "Exxon Mobil"),
            ("CVX",   "Chevron"),
            ("COP",   "ConocoPhillips"),
            ("SLB",   "SLB (Schlumberger)"),
        ],
        "Healthcare": [
            ("JNJ",   "Johnson & Johnson"),
            ("UNH",   "UnitedHealth Group"),
            ("PFE",   "Pfizer"),
            ("ABBV",  "AbbVie"),
            ("MRK",   "Merck"),
            ("LLY",   "Eli Lilly"),
        ],
        "Consumer": [
            ("HD",    "Home Depot"),
            ("MCD",   "McDonald's"),
            ("NKE",   "Nike"),
            ("COST",  "Costco"),
            ("PG",    "Procter & Gamble"),
            ("KO",    "Coca-Cola"),
        ],
        "Telecom": [
            ("VZ",    "Verizon"),
            ("T",     "AT&T"),
            ("TMUS",  "T-Mobile US"),
        ],
        "Industrials": [
            ("CAT",   "Caterpillar"),
            ("BA",    "Boeing"),
            ("HON",   "Honeywell"),
            ("GE",    "GE Aerospace"),
        ],
    }
}

# ─────────────────────────────────────────────
# TIMEFRAME CONFIG
# ─────────────────────────────────────────────

TF_CONFIG = {
    "15m": {"interval": "15m",  "period": "5d",  "label": "15 Minute"},
    "1H":  {"interval": "1h",   "period": "30d", "label": "1 Hour"},
    "1D":  {"interval": "1d",   "period": "1y",  "label": "1 Day"},
    "1W":  {"interval": "1wk",  "period": "5y",  "label": "1 Week"},
}

# ─────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────

def fetch_ohlcv(ticker: str, tf: str) -> pd.DataFrame | None:
    cfg = TF_CONFIG[tf]
    try:
        df = yf.download(
            ticker,
            interval=cfg["interval"],
            period=cfg["period"],
            progress=False,
            auto_adjust=True,
        )
        if df is None or df.empty or len(df) < 30:
            return None
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.rename(columns=str.lower)
        df = df.dropna()
        return df
    except Exception as e:
        print(f"  [WARN] {ticker} fetch failed: {e}")
        return None


def fetch_fundamentals(ticker: str, is_india: bool) -> dict:
    currency = "₹" if is_india else "$"
    defaults = {
        "pe": "N/A", "eps": "N/A", "eps_trend": "neutral",
        "market_cap": "N/A", "week52_high": "N/A", "week52_low": "N/A",
        "dividend_yield": "N/A", "currency": currency,
        "beta": "N/A", "sector": "N/A",
    }
    try:
        info = yf.Ticker(ticker).info
        pe  = info.get("trailingPE") or info.get("forwardPE")
        eps = info.get("trailingEps")
        mkt = info.get("marketCap")
        w52h = info.get("fiftyTwoWeekHigh")
        w52l = info.get("fiftyTwoWeekLow")
        dy   = info.get("dividendYield")
        beta = info.get("beta")
        sector = info.get("sector", "N/A")

        # EPS trend heuristic: compare trailing vs forward EPS
        fwd_eps = info.get("forwardEps")
        if eps and fwd_eps:
            if fwd_eps > eps:
                eps_trend = "up"
            elif fwd_eps < eps:
                eps_trend = "down"
            else:
                eps_trend = "flat"
        else:
            eps_trend = "flat"

        def fmt_large(n):
            if n is None: return "N/A"
            if n >= 1e12: return f"{currency}{n/1e12:.2f}T"
            if n >= 1e9:  return f"{currency}{n/1e9:.2f}B"
            if n >= 1e6:  return f"{currency}{n/1e6:.2f}M"
            return f"{currency}{n:,.0f}"

        return {
            "pe":            f"{pe:.1f}x" if pe else "N/A",
            "eps":           f"{currency}{eps:.2f}" if eps else "N/A",
            "eps_trend":     eps_trend,
            "market_cap":    fmt_large(mkt),
            "week52_high":   f"{currency}{w52h:,.2f}" if w52h else "N/A",
            "week52_low":    f"{currency}{w52l:,.2f}" if w52l else "N/A",
            "dividend_yield":f"{dy*100:.2f}%" if dy else "N/A",
            "currency":      currency,
            "beta":          f"{beta:.2f}" if beta else "N/A",
            "sector":        sector,
        }
    except Exception as e:
        print(f"  [WARN] {ticker} fundamentals failed: {e}")
        return defaults

# ─────────────────────────────────────────────
# SUPPORT & RESISTANCE
# ─────────────────────────────────────────────

def calculate_sr(df: pd.DataFrame, n_levels: int = 3) -> dict:
    """
    Calculate Support & Resistance using pivot points + local swing highs/lows.
    More candles = more reliable levels (adapts per timeframe automatically).
    """
    close = df["close"].values
    high  = df["high"].values
    low   = df["low"].values
    current_price = float(close[-1])

    # --- Pivot-point based S&R (last 20 candles rolling window) ---
    window = min(20, len(df) - 1)
    recent_high = float(np.max(high[-window:]))
    recent_low  = float(np.min(low[-window:]))
    pivot       = (recent_high + recent_low + float(close[-window])) / 3

    r_pivot = [
        round(2 * pivot - recent_low, 2),
        round(pivot + (recent_high - recent_low), 2),
        round(recent_high + 2 * (pivot - recent_low), 2),
    ]
    s_pivot = [
        round(2 * pivot - recent_high, 2),
        round(pivot - (recent_high - recent_low), 2),
        round(recent_low - 2 * (recent_high - pivot), 2),
    ]

    # --- Swing high/low detection ---
    swing_highs, swing_lows = [], []
    for i in range(2, len(high) - 2):
        if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
            swing_highs.append(float(high[i]))
        if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
            swing_lows.append(float(low[i]))

    # Cluster nearby swing levels (within 0.5% of each other)
    def cluster(levels, tol=0.005):
        if not levels: return []
        levels = sorted(set(levels))
        clusters, grp = [], [levels[0]]
        for l in levels[1:]:
            if (l - grp[-1]) / grp[-1] < tol:
                grp.append(l)
            else:
                clusters.append(round(np.mean(grp), 2))
                grp = [l]
        clusters.append(round(np.mean(grp), 2))
        return clusters

    swing_h_clusters = cluster(swing_highs)
    swing_l_clusters = cluster(swing_lows)

    # Resistance = above current price
    resistance = sorted([x for x in swing_h_clusters + r_pivot if x > current_price])[:n_levels]
    support    = sorted([x for x in swing_l_clusters + s_pivot if x < current_price], reverse=True)[:n_levels]

    # Pad if not enough levels
    while len(resistance) < n_levels:
        last = resistance[-1] if resistance else current_price
        resistance.append(round(last * 1.02, 2))
    while len(support) < n_levels:
        last = support[-1] if support else current_price
        support.append(round(last * 0.98, 2))

    return {
        "resistance": resistance[:n_levels],
        "support":    support[:n_levels],
        "pivot":      round(pivot, 2),
    }

# ─────────────────────────────────────────────
# TECHNICAL INDICATORS
# ─────────────────────────────────────────────

def calculate_indicators(df: pd.DataFrame) -> dict:
    close = df["close"]
    high  = df["high"]
    low   = df["low"]
    vol   = df["volume"]

    result = {}

    # RSI
    try:
        rsi_s = ta.rsi(close, length=14)
        result["rsi"] = round(float(rsi_s.iloc[-1]), 2) if rsi_s is not None else None
    except:
        result["rsi"] = None

    # MACD
    try:
        macd_df = ta.macd(close, fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            result["macd"]        = round(float(macd_df["MACD_12_26_9"].iloc[-1]), 3)
            result["macd_signal"] = round(float(macd_df["MACDs_12_26_9"].iloc[-1]), 3)
            result["macd_hist"]   = round(float(macd_df["MACDh_12_26_9"].iloc[-1]), 3)
            result["macd_bull"]   = result["macd"] > result["macd_signal"]
        else:
            result.update({"macd": None, "macd_signal": None, "macd_hist": None, "macd_bull": False})
    except:
        result.update({"macd": None, "macd_signal": None, "macd_hist": None, "macd_bull": False})

    # ATR
    try:
        atr_s = ta.atr(high, low, close, length=14)
        result["atr"] = round(float(atr_s.iloc[-1]), 2) if atr_s is not None else None
    except:
        result["atr"] = None

    # EMA 20, 50, 200
    try:
        ema20  = ta.ema(close, length=20)
        ema50  = ta.ema(close, length=50)
        ema200 = ta.ema(close, length=200)
        curr   = float(close.iloc[-1])
        e20    = float(ema20.iloc[-1])  if ema20  is not None else None
        e50    = float(ema50.iloc[-1])  if ema50  is not None else None
        e200   = float(ema200.iloc[-1]) if ema200 is not None else None
        result["ema20"]  = round(e20,  2) if e20  else None
        result["ema50"]  = round(e50,  2) if e50  else None
        result["ema200"] = round(e200, 2) if e200 else None

        if e50 and e200:
            if e50 > e200 and curr > e50:
                result["ema_signal"] = "Golden Cross"
                result["ema_bull"]   = True
            elif e50 < e200:
                result["ema_signal"] = "Death Cross"
                result["ema_bull"]   = False
            elif curr > e50:
                result["ema_signal"] = "Above 50 EMA"
                result["ema_bull"]   = True
            else:
                result["ema_signal"] = "Below 50 EMA"
                result["ema_bull"]   = False
        else:
            result["ema_signal"] = "N/A"
            result["ema_bull"]   = False
    except:
        result.update({"ema20": None, "ema50": None, "ema200": None, "ema_signal": "N/A", "ema_bull": False})

    # Volume ratio vs 20-period average
    try:
        avg_vol = float(vol.rolling(20).mean().iloc[-1])
        cur_vol = float(vol.iloc[-1])
        ratio   = cur_vol / avg_vol if avg_vol > 0 else 1.0
        result["volume_ratio"] = round(ratio, 2)
        result["volume_bull"]  = ratio > 1.2
    except:
        result["volume_ratio"] = 1.0
        result["volume_bull"]  = False

    # Stochastic
    try:
        stoch_df = ta.stoch(high, low, close, k=14, d=3)
        if stoch_df is not None and not stoch_df.empty:
            k_col = [c for c in stoch_df.columns if c.startswith("STOCHk")][0]
            result["stoch_k"] = round(float(stoch_df[k_col].iloc[-1]), 2)
            result["stoch_bull"] = 20 < result["stoch_k"] < 80
        else:
            result["stoch_k"] = None
            result["stoch_bull"] = False
    except:
        result["stoch_k"] = None
        result["stoch_bull"] = False

    # Bollinger Bands
    try:
        bb = ta.bbands(close, length=20, std=2)
        if bb is not None and not bb.empty:
            cols = bb.columns.tolist()
            lower_col = [c for c in cols if "BBL" in c][0]
            upper_col = [c for c in cols if "BBU" in c][0]
            mid_col   = [c for c in cols if "BBM" in c][0]
            curr = float(close.iloc[-1])
            bbl  = float(bb[lower_col].iloc[-1])
            bbu  = float(bb[upper_col].iloc[-1])
            bbm  = float(bb[mid_col].iloc[-1])
            result["bb_lower"] = round(bbl, 2)
            result["bb_upper"] = round(bbu, 2)
            result["bb_mid"]   = round(bbm, 2)
            if curr <= bbl:
                result["bb_signal"] = "At Lower Band"
                result["bb_bull"]   = True
            elif curr >= bbu:
                result["bb_signal"] = "At Upper Band"
                result["bb_bull"]   = False
            else:
                result["bb_signal"] = "Mid Band"
                result["bb_bull"]   = True
        else:
            result.update({"bb_lower": None, "bb_upper": None, "bb_mid": None, "bb_signal": "N/A", "bb_bull": False})
    except:
        result.update({"bb_lower": None, "bb_upper": None, "bb_mid": None, "bb_signal": "N/A", "bb_bull": False})

    return result

# ─────────────────────────────────────────────
# SIGNAL SCORING
# ─────────────────────────────────────────────

def compute_signal(ind: dict, fund: dict) -> dict:
    """
    Score 0–100. Each indicator contributes weight.
    Technical: 75 pts | Fundamental: 25 pts
    """
    score = 0
    details = []

    # RSI (15 pts)
    rsi = ind.get("rsi")
    if rsi is not None:
        if 40 <= rsi <= 60:
            score += 10; details.append(("RSI", "neutral", rsi))
        elif 30 <= rsi < 40:
            score += 13; details.append(("RSI", "bull", rsi))
        elif rsi < 30:
            score += 15; details.append(("RSI", "bull", rsi))   # oversold = opportunity
        elif 60 < rsi <= 70:
            score += 7;  details.append(("RSI", "neut", rsi))
        else:  # >70 overbought
            score += 2;  details.append(("RSI", "bear", rsi))

    # MACD (15 pts)
    if ind.get("macd_bull"):
        score += 15; details.append(("MACD", "bull", ind.get("macd")))
    elif ind.get("macd") is not None:
        score += 3;  details.append(("MACD", "bear", ind.get("macd")))

    # EMA (15 pts)
    if ind.get("ema_bull"):
        ema_sig = ind.get("ema_signal","")
        pts = 15 if "Golden" in ema_sig else 10
        score += pts; details.append(("EMA", "bull", ema_sig))
    elif ind.get("ema_signal") not in (None, "N/A"):
        score += 2;  details.append(("EMA", "bear", ind.get("ema_signal")))

    # Volume (10 pts)
    if ind.get("volume_bull"):
        score += 10; details.append(("Volume", "bull", ind.get("volume_ratio")))
    else:
        score += 4;  details.append(("Volume", "neut", ind.get("volume_ratio")))

    # Stochastic (10 pts)
    stoch = ind.get("stoch_k")
    if stoch is not None:
        if stoch < 20:
            score += 10; details.append(("Stochastic", "bull", stoch))
        elif stoch > 80:
            score += 2;  details.append(("Stochastic", "bear", stoch))
        else:
            score += 7;  details.append(("Stochastic", "neut", stoch))

    # Bollinger (10 pts)
    if ind.get("bb_bull"):
        score += 8; details.append(("Bollinger", "bull", ind.get("bb_signal")))
    else:
        score += 3; details.append(("Bollinger", "bear", ind.get("bb_signal")))

    # ── Fundamentals (25 pts) ──
    pe_str = fund.get("pe", "N/A")
    try:
        pe_val = float(pe_str.replace("x",""))
        if pe_val < 20:    score += 10
        elif pe_val < 35:  score += 7
        else:              score += 3
    except:
        score += 5  # neutral if N/A

    eps_trend = fund.get("eps_trend", "flat")
    if eps_trend == "up":   score += 10
    elif eps_trend == "flat": score += 5
    else:                     score += 0

    beta_str = fund.get("beta", "N/A")
    try:
        beta_val = float(beta_str)
        if 0.5 <= beta_val <= 1.5: score += 5
        elif beta_val < 0.5:       score += 3
        else:                      score += 1
    except:
        score += 3

    score = min(score, 100)

    # Final signal
    if score >= 65:   signal = "BUY"
    elif score >= 50: signal = "WATCH"
    elif score >= 38: signal = "HOLD"
    else:             signal = "SELL"

    bull_count = sum(1 for _, cls, _ in details if cls == "bull")
    total_ind  = len(details)

    return {
        "score":      score,
        "signal":     signal,
        "bull_pct":   score,
        "bear_pct":   100 - score,
        "bull_count": bull_count,
        "total_ind":  total_ind,
        "details":    details,
    }

# ─────────────────────────────────────────────
# ANALYSE ONE STOCK
# ─────────────────────────────────────────────

def analyse_stock(ticker: str, name: str, country: str, sector: str, tf: str) -> dict | None:
    is_india = (country == "IN")
    currency = "₹" if is_india else "$"
    print(f"  Analysing {ticker} ({name}) [{tf}] ...", end=" ", flush=True)

    df = fetch_ohlcv(ticker, tf)
    if df is None:
        print("SKIP (no data)")
        return None

    ind  = calculate_indicators(df)
    sr   = calculate_sr(df)
    fund = fetch_fundamentals(ticker, is_india)

    # Price info
    curr_price = float(df["close"].iloc[-1])
    prev_price = float(df["close"].iloc[-2]) if len(df) > 1 else curr_price
    change_pct = ((curr_price - prev_price) / prev_price * 100) if prev_price else 0

    # ATR-based stop/target (only displayed for BUY)
    atr_val = ind.get("atr")
    stop_loss = round(curr_price - 1.5 * atr_val, 2) if atr_val else None
    target    = round(curr_price + 2.0 * atr_val, 2)  if atr_val else None

    sig = compute_signal(ind, fund)

    def fmt_price(p):
        return f"{currency}{p:,.2f}" if p else "N/A"

    def fmt_sr_list(lst):
        return [fmt_price(x) for x in lst]

    result = {
        "ticker":      ticker,
        "name":        name,
        "country":     country,
        "country_flag":"🇮🇳" if is_india else "🇺🇸",
        "sector":      sector,
        "timeframe":   tf,
        "price":       fmt_price(curr_price),
        "price_raw":   curr_price,
        "change":      f"{change_pct:+.2f}%",
        "change_pos":  change_pct >= 0,
        "currency":    currency,

        # Signal
        "signal":      sig["signal"],
        "score":       sig["score"],
        "bull_pct":    sig["bull_pct"],
        "bear_pct":    sig["bear_pct"],
        "bull_count":  sig["bull_count"],
        "total_ind":   sig["total_ind"],

        # Indicators
        "rsi":          ind.get("rsi"),
        "macd":         ind.get("macd"),
        "macd_signal":  ind.get("macd_signal"),
        "macd_hist":    ind.get("macd_hist"),
        "macd_bull":    ind.get("macd_bull", False),
        "ema_signal":   ind.get("ema_signal", "N/A"),
        "ema_bull":     ind.get("ema_bull", False),
        "ema50":        ind.get("ema50"),
        "ema200":       ind.get("ema200"),
        "volume_ratio": ind.get("volume_ratio"),
        "volume_bull":  ind.get("volume_bull", False),
        "stoch_k":      ind.get("stoch_k"),
        "stoch_bull":   ind.get("stoch_bull", False),
        "bb_signal":    ind.get("bb_signal", "N/A"),
        "bb_bull":      ind.get("bb_bull", False),
        "bb_upper":     ind.get("bb_upper"),
        "bb_lower":     ind.get("bb_lower"),

        # ATR
        "atr":        fmt_price(atr_val) if atr_val else "N/A",
        "stop_loss":  fmt_price(stop_loss),
        "target":     fmt_price(target),

        # S&R
        "resistance": fmt_sr_list(sr["resistance"]),
        "support":    fmt_sr_list(sr["support"]),
        "pivot":      fmt_price(sr["pivot"]),

        # Fundamentals
        "pe":             fund.get("pe", "N/A"),
        "eps":            fund.get("eps", "N/A"),
        "eps_trend":      fund.get("eps_trend", "flat"),
        "market_cap":     fund.get("market_cap", "N/A"),
        "week52_high":    fund.get("week52_high", "N/A"),
        "week52_low":     fund.get("week52_low", "N/A"),
        "dividend_yield": fund.get("dividend_yield", "N/A"),
        "beta":           fund.get("beta", "N/A"),
    }
    print(f"DONE — {sig['signal']} ({sig['score']}/100)")
    return result

# ─────────────────────────────────────────────
# HTML GENERATION
# ─────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MarketIntel Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#080c14;--surface:#0d1420;--surface2:#111928;--border:#1e2d45;--ab:#00d4ff;--ag:#00ff88;--ar:#ff3d6b;--ay:#ffd600;--ap:#a855f7;--text:#e2eaf5;--muted:#5a7196;--dim:#1a2840;}
*{margin:0;padding:0;box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Syne',sans-serif;min-height:100vh;overflow-x:hidden;}
body::before{content:'';position:fixed;inset:0;background-image:linear-gradient(var(--dim) 1px,transparent 1px),linear-gradient(90deg,var(--dim) 1px,transparent 1px);background-size:40px 40px;opacity:.4;pointer-events:none;z-index:0;}
.wrap{position:relative;z-index:1;max-width:1300px;margin:0 auto;padding:24px;}

/* HEADER */
.hdr{display:flex;align-items:center;justify-content:space-between;padding:18px 0 28px;border-bottom:1px solid var(--border);margin-bottom:32px;}
.logo{display:flex;align-items:center;gap:14px;}
.logo-icon{width:46px;height:46px;background:linear-gradient(135deg,var(--ab),var(--ap));border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:22px;}
.logo-title{font-size:24px;font-weight:800;letter-spacing:-.5px;}
.logo-title span{color:var(--ab);}
.logo-sub{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:3px;}
.hdr-right{text-align:right;font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);line-height:1.9;}
.live{display:inline-block;width:7px;height:7px;background:var(--ag);border-radius:50%;margin-right:5px;animation:blink 1.4s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.2}}

/* FILTER PANEL */
.fp{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:28px 32px;margin-bottom:32px;}
.fp-title{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:22px;display:flex;align-items:center;gap:10px;}
.fp-title::after{content:'';flex:1;height:1px;background:var(--border);}
.frow{display:flex;gap:20px;align-items:flex-end;flex-wrap:wrap;}
.fg{display:flex;flex-direction:column;gap:8px;}
.fl{font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);}
.btn-group{display:flex;gap:6px;}
.btn{padding:9px 18px;border-radius:9px;border:1px solid var(--border);background:var(--surface2);color:var(--muted);font-family:'Space Mono',monospace;font-size:12px;cursor:pointer;transition:all .2s;}
.btn:hover{border-color:var(--ab);color:var(--ab);}
.btn.active{background:rgba(0,212,255,.12);border-color:var(--ab);color:var(--ab);font-weight:700;}
.btn.c-in{background:rgba(0,255,136,.1);border-color:var(--ag);color:var(--ag);font-weight:700;}
.btn.c-us{background:rgba(0,212,255,.1);border-color:var(--ab);color:var(--ab);font-weight:700;}
.sel-wrap{position:relative;}
.sel-wrap::after{content:'▾';position:absolute;right:14px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:12px;pointer-events:none;}
select{padding:10px 36px 10px 14px;border-radius:9px;border:1px solid var(--border);background:var(--surface2);color:var(--text);font-family:'Space Mono',monospace;font-size:12px;cursor:pointer;outline:none;appearance:none;min-width:200px;transition:border-color .2s;}
select:focus{border-color:var(--ab);}
select:disabled{opacity:.35;cursor:not-allowed;}
.run-btn{padding:11px 32px;border-radius:10px;background:linear-gradient(135deg,var(--ab),var(--ap));border:none;color:#000;font-family:'Syne',sans-serif;font-weight:800;font-size:14px;cursor:pointer;letter-spacing:.5px;transition:transform .2s,box-shadow .2s;white-space:nowrap;}
.run-btn:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(0,212,255,.3);}
.run-btn:disabled{opacity:.4;cursor:not-allowed;transform:none;box-shadow:none;}

/* FLOW BAR */
.flow{display:flex;margin-top:22px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.fs{flex:1;padding:10px 16px;display:flex;align-items:center;gap:8px;font-size:11px;border-right:1px solid var(--border);transition:all .3s;}
.fs:last-child{border-right:none;}
.fs.done{background:rgba(0,255,136,.05);}
.fs.cur{background:rgba(0,212,255,.07);}
.fn{width:22px;height:22px;border-radius:50%;border:1.5px solid var(--border);display:flex;align-items:center;justify-content:center;font-family:'Space Mono',monospace;font-size:10px;font-weight:700;flex-shrink:0;}
.fs.done .fn{background:var(--ag);border-color:var(--ag);color:#000;}
.fs.cur .fn{background:rgba(0,212,255,.2);border-color:var(--ab);color:var(--ab);}
.ftext{display:flex;flex-direction:column;gap:1px;}
.fname{font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--muted);}
.fval{font-size:12px;font-weight:700;color:var(--text);font-family:'Space Mono',monospace;}
.fs.done .fval{color:var(--ag);}
.fs.cur .fval{color:var(--ab);}

/* PLACEHOLDER */
.ph{text-align:center;padding:80px 40px;background:var(--surface);border:1px dashed var(--border);border-radius:16px;color:var(--muted);animation:fu .4s ease;}
.ph-icon{font-size:56px;margin-bottom:16px;opacity:.4;}
.ph-text{font-size:18px;font-weight:700;color:var(--muted);margin-bottom:8px;}
.ph-sub{font-family:'Space Mono',monospace;font-size:12px;}
@keyframes fu{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* ANALYSIS CARD */
.ac{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden;animation:fu .5s ease;}
.ac-hdr{padding:24px 28px;border-bottom:1px solid var(--border);background:linear-gradient(135deg,rgba(0,212,255,.04),rgba(168,85,247,.04));display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;}
.ac-name{font-size:26px;font-weight:800;letter-spacing:-.5px;}
.ac-meta{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:8px;}
.mtag{padding:4px 12px;border-radius:6px;font-size:11px;font-weight:700;font-family:'Space Mono',monospace;border:1px solid;}
.mc{background:rgba(0,255,136,.08);color:var(--ag);border-color:rgba(0,255,136,.2);}
.ms{background:rgba(168,85,247,.08);color:var(--ap);border-color:rgba(168,85,247,.2);}
.mt{background:rgba(0,212,255,.08);color:var(--ab);border-color:rgba(0,212,255,.2);}
.ac-pb{text-align:right;}
.ac-price{font-family:'Space Mono',monospace;font-size:36px;font-weight:700;color:var(--ab);}
.chg-p{color:var(--ag);font-family:'Space Mono',monospace;font-size:14px;margin-top:4px;}
.chg-n{color:var(--ar);font-family:'Space Mono',monospace;font-size:14px;margin-top:4px;}
.sig{padding:8px 20px;border-radius:9px;font-weight:800;font-size:13px;letter-spacing:.5px;display:inline-block;}
.sig-buy{background:rgba(0,255,136,.15);color:var(--ag);border:1px solid rgba(0,255,136,.35);}
.sig-sell{background:rgba(255,61,107,.15);color:var(--ar);border:1px solid rgba(255,61,107,.35);}
.sig-hold{background:rgba(255,214,0,.1);color:var(--ay);border:1px solid rgba(255,214,0,.25);}
.sig-watch{background:rgba(0,212,255,.1);color:var(--ab);border:1px solid rgba(0,212,255,.25);}

.ac-body{padding:24px 28px;display:flex;flex-direction:column;gap:28px;}
.sec-lbl{font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted);margin-bottom:14px;display:flex;align-items:center;gap:10px;}
.sec-lbl::after{content:'';flex:1;height:1px;background:var(--border);}

/* TOW */
.tow-lbls{display:flex;justify-content:space-between;margin-bottom:10px;}
.tow-bear-l{font-size:12px;font-weight:700;color:var(--ar);}
.tow-bull-l{font-size:12px;font-weight:700;color:var(--ag);}
.tow-bar{height:32px;border-radius:16px;overflow:hidden;display:flex;position:relative;background:var(--border);}
.tow-bf{height:100%;background:linear-gradient(90deg,#ff1a4b,#ff7090);}
.tow-bull{height:100%;background:linear-gradient(90deg,#00cc6a,#00ff88);flex:1;}
.tow-div{position:absolute;left:50%;top:-4px;bottom:-4px;width:3px;background:rgba(255,255,255,.15);border-radius:2px;}
.tow-sr{display:flex;justify-content:space-between;align-items:center;margin-top:10px;}
.tow-st{font-family:'Space Mono',monospace;font-size:12px;color:var(--muted);}
.tow-sn{font-size:18px;font-weight:800;}
.tow-sn.buy{color:var(--ag);}
.tow-sn.sell{color:var(--ar);}
.tow-sn.hold{color:var(--ay);}
.tow-sn.watch{color:var(--ab);}

/* IND GRID */
.ig{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;}
.ic{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:8px;position:relative;overflow:hidden;}
.ic::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;}
.ic.bull::before{background:var(--ag);}
.ic.bear::before{background:var(--ar);}
.ic.neut::before{background:var(--ay);}
.in{font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);}
.iv{font-family:'Space Mono',monospace;font-size:17px;font-weight:700;}
.iv.bull{color:var(--ag);}
.iv.bear{color:var(--ar);}
.iv.neut{color:var(--ay);}
.ist{font-size:10px;font-weight:700;}
.ist.bull{color:var(--ag);}
.ist.bear{color:var(--ar);}
.ist.neut{color:var(--ay);}
.rsi-bar{height:4px;background:var(--border);border-radius:2px;margin-top:4px;}
.rsi-fill{height:100%;border-radius:2px;}

/* ATR */
.atr-block{background:rgba(255,214,0,.05);border:1px solid rgba(255,214,0,.15);border-radius:12px;padding:18px 22px;display:grid;grid-template-columns:auto 1px 1fr 1fr;gap:20px;align-items:center;}
.atr-lbl{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--ay);opacity:.6;}
.atr-v{font-family:'Space Mono',monospace;font-size:26px;font-weight:700;color:var(--ay);}
.atr-d{background:rgba(255,214,0,.15);align-self:stretch;}
.atr-det{display:flex;flex-direction:column;gap:8px;}
.atr-rl{font-size:9px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--muted);}
.atr-rv{font-family:'Space Mono',monospace;font-size:14px;font-weight:700;}
.stop{color:var(--ar);}
.tgt{color:var(--ag);}

/* SR */
.srg{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.src{background:var(--surface2);border:1px solid var(--border);border-radius:12px;padding:18px;}
.srh{font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:14px;}
.srh.r{color:var(--ar);}
.srh.s{color:var(--ag);}
.srl{display:flex;flex-direction:column;gap:8px;}
.srv{display:flex;justify-content:space-between;align-items:center;padding:9px 13px;border-radius:8px;}
.srv.r{background:rgba(255,61,107,.07);border:1px solid rgba(255,61,107,.14);}
.srv.s{background:rgba(0,255,136,.07);border:1px solid rgba(0,255,136,.14);}
.srvl{font-size:10px;color:var(--muted);font-family:'Space Mono',monospace;}
.srvp{font-family:'Space Mono',monospace;font-size:14px;font-weight:700;}
.srvp.r{color:var(--ar);}
.srvp.s{color:var(--ag);}
.sr-note{font-family:'Space Mono',monospace;font-size:10px;color:var(--muted);margin-top:10px;text-align:center;}

/* FUND */
.fundg{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.fc{background:rgba(168,85,247,.05);border:1px solid rgba(168,85,247,.13);border-radius:12px;padding:16px;}
.fl2{font-size:9px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--ap);opacity:.6;margin-bottom:8px;}
.fv{font-family:'Space Mono',monospace;font-size:15px;font-weight:700;color:var(--ap);}
.fsb{font-size:10px;color:var(--muted);margin-top:4px;}
.eps-u{color:var(--ag);}
.eps-d{color:var(--ar);}
.eps-f{color:var(--ay);}

footer{text-align:center;padding:28px 0 12px;color:var(--muted);font-size:10px;font-family:'Space Mono',monospace;border-top:1px solid var(--border);margin-top:40px;line-height:2;}
footer span{color:var(--ab);}

@media(max-width:900px){.ig{grid-template-columns:repeat(3,1fr);}.fundg{grid-template-columns:repeat(2,1fr);}.atr-block{grid-template-columns:1fr;}.srg{grid-template-columns:1fr;}.frow{flex-direction:column;}.flow{flex-direction:column;}}
</style>
</head>
<body>
<div class="wrap">

<div class="hdr">
  <div class="logo">
    <div class="logo-icon">📈</div>
    <div>
      <div class="logo-title">Market<span>Intel</span></div>
      <div class="logo-sub">NIFTY 50 · S&P TOP 50 · MULTI-TIMEFRAME ANALYSIS</div>
    </div>
  </div>
  <div class="hdr-right">
    <div><span class="live"></span>Data via Yahoo Finance (yfinance)</div>
    <div>Generated: __GENERATED__</div>
    <div>Powered by GitHub Actions ⚡</div>
  </div>
</div>

<!-- FILTER PANEL -->
<div class="fp">
  <div class="fp-title">🎛️ Stock Selection Filters</div>
  <div class="frow">

    <div class="fg">
      <div class="fl">① Country</div>
      <div class="btn-group">
        <button class="btn c-in" id="btn-IN" onclick="selCountry('IN',this)">🇮🇳 India</button>
        <button class="btn"      id="btn-US" onclick="selCountry('US',this)">🇺🇸 United States</button>
      </div>
    </div>

    <div class="fg">
      <div class="fl">② Sector</div>
      <div class="sel-wrap">
        <select id="secSel" onchange="loadStocks()">
          <option value="">— Select Sector —</option>
        </select>
      </div>
    </div>

    <div class="fg">
      <div class="fl">③ Stock / Company</div>
      <div class="sel-wrap">
        <select id="stkSel" disabled onchange="stkChosen()">
          <option value="">— Select Sector First —</option>
        </select>
      </div>
    </div>

    <div class="fg">
      <div class="fl">④ Timeframe</div>
      <div class="btn-group">
        <button class="btn" onclick="setTF('15m',this)">15m</button>
        <button class="btn" onclick="setTF('1H',this)">1H</button>
        <button class="btn active" id="btn-tf-1D" onclick="setTF('1D',this)">1D</button>
        <button class="btn" onclick="setTF('1W',this)">1W</button>
      </div>
    </div>

    <div class="fg">
      <div class="fl">&nbsp;</div>
      <button class="run-btn" id="runBtn" disabled onclick="showCard()">⚡ Analyze</button>
    </div>
  </div>

  <!-- FLOW BAR -->
  <div class="flow">
    <div class="fs done" id="s1"><div class="fn">✓</div><div class="ftext"><div class="fname">Country</div><div class="fval" id="s1v">🇮🇳 India</div></div></div>
    <div class="fs" id="s2"><div class="fn">2</div><div class="ftext"><div class="fname">Sector</div><div class="fval" id="s2v">Pending</div></div></div>
    <div class="fs" id="s3"><div class="fn">3</div><div class="ftext"><div class="fname">Stock</div><div class="fval" id="s3v">Pending</div></div></div>
    <div class="fs done" id="s4"><div class="fn">✓</div><div class="ftext"><div class="fname">Timeframe</div><div class="fval" id="s4v">1D</div></div></div>
    <div class="fs cur" id="s5"><div class="fn">5</div><div class="ftext"><div class="fname">Analysis</div><div class="fval" id="s5v">Waiting...</div></div></div>
  </div>
</div>

<!-- OUTPUT -->
<div id="out">
  <div class="ph">
    <div class="ph-icon">🔍</div>
    <div class="ph-text">Select Country → Sector → Stock → Timeframe</div>
    <div class="ph-sub">Then click ⚡ Analyze to see full technical + fundamental analysis</div>
  </div>
</div>

<footer>
  <span>MarketIntel</span> · Python + yfinance + pandas-ta · GitHub Actions Scheduled<br>
  <span>Data is for informational purposes only — Not financial advice.</span>
</footer>
</div>

<script>
const DATA = __DATA_JSON__;

let curCountry = 'IN', curTF = '1D', curTicker = '';

function selCountry(code, btn) {
  curCountry = code;
  ['IN','US'].forEach(c => {
    const b = document.getElementById('btn-'+c);
    b.className = 'btn';
  });
  btn.className = code==='IN' ? 'btn c-in' : 'btn c-us';
  document.getElementById('s1v').textContent = code==='IN' ? '🇮🇳 India' : '🇺🇸 USA';
  mark('s1','done','✓');
  // Build sector list
  const sectors = Object.keys(DATA[code] || {});
  const secSel = document.getElementById('secSel');
  secSel.innerHTML = '<option value="">— Select Sector —</option>' +
    sectors.map(s=>`<option value="${s}">${s}</option>`).join('');
  resetStock(); resetOut();
  mark('s2','','2'); document.getElementById('s2v').textContent='Pending';
  mark('s3','','3'); document.getElementById('s3v').textContent='Pending';
}

function loadStocks() {
  const sec = document.getElementById('secSel').value;
  const stkSel = document.getElementById('stkSel');
  if (!sec) { stkSel.innerHTML='<option>— Select Sector First —</option>'; stkSel.disabled=true; document.getElementById('runBtn').disabled=true; resetOut(); mark('s2','','2'); document.getElementById('s2v').textContent='Pending'; return; }
  mark('s2','done','✓'); document.getElementById('s2v').textContent=sec;
  const stocks = DATA[curCountry][sec] || [];
  stkSel.innerHTML = '<option value="">— Select Company —</option>' +
    stocks.map(s=>`<option value="${s.ticker}">${s.name} (${s.ticker})</option>`).join('');
  stkSel.disabled = false;
  mark('s3','','3'); document.getElementById('s3v').textContent='Pending';
  document.getElementById('runBtn').disabled=true; curTicker=''; resetOut();
}

function stkChosen() {
  curTicker = document.getElementById('stkSel').value;
  if (curTicker) {
    mark('s3','done','✓'); document.getElementById('s3v').textContent=curTicker;
    document.getElementById('runBtn').disabled=false;
  } else {
    mark('s3','','3'); document.getElementById('s3v').textContent='Pending';
    document.getElementById('runBtn').disabled=true;
  }
  resetOut();
}

function setTF(tf, btn) {
  curTF = tf;
  document.querySelectorAll('.btn[onclick*="setTF"]').forEach(b=>b.className='btn');
  btn.className='btn active';
  document.getElementById('s4v').textContent=tf;
  mark('s4','done','✓');
  if (document.getElementById('out').querySelector('.ac')) showCard();
}

function mark(id, cls, num) {
  const el = document.getElementById(id);
  el.className = 'fs' + (cls ? ' '+cls : '');
  el.querySelector('.fn').textContent = num;
}

function resetStock() { const s=document.getElementById('stkSel'); s.innerHTML='<option>— Select Sector First —</option>'; s.disabled=true; document.getElementById('runBtn').disabled=true; curTicker=''; }

function resetOut() {
  document.getElementById('out').innerHTML=`<div class="ph"><div class="ph-icon">🔍</div><div class="ph-text">Select Country → Sector → Stock → Timeframe</div><div class="ph-sub">Then click ⚡ Analyze to see full technical + fundamental analysis</div></div>`;
  mark('s5','cur','5'); document.getElementById('s5v').textContent='Waiting...';
}

function showCard() {
  if (!curTicker) return;
  const sec = document.getElementById('secSel').value;
  const stocks = DATA[curCountry][sec] || [];
  const tf_stocks = stocks.filter(s => s.ticker === curTicker && s.timeframe === curTF);
  const d = tf_stocks.length ? tf_stocks[0] : stocks.find(s=>s.ticker===curTicker);
  if (!d) { document.getElementById('out').innerHTML=`<div class="ph"><div class="ph-icon">⚠️</div><div class="ph-text">No data found for ${curTicker} on ${curTF}</div><div class="ph-sub">Try a different timeframe or re-run the analysis script</div></div>`; return; }

  const sigCls = {BUY:'sig-buy',SELL:'sig-sell',HOLD:'sig-hold',WATCH:'sig-watch'}[d.signal]||'sig-watch';
  const sigEmoji = {BUY:'✅',SELL:'❌',HOLD:'⏸',WATCH:'👁'}[d.signal]||'⚠️';
  const scoreCls = d.score>=65?'buy':d.score<=40?'sell':d.score>=50?'watch':'hold';

  function rsiCls(r) { return r>70?'bear':r<35?'bull':'neut'; }
  function rsiStat(r) { return r>70?'● Overbought':r<35?'● Oversold — Opportunity':'● Neutral Zone'; }
  function rsiColor(r) { return r>70?'var(--ar)':r<35?'var(--ag)':'var(--ay)'; }
  const rsiPct = Math.min(d.rsi||0,100);

  const volStr = d.volume_ratio!=null ? `${d.volume_ratio}x Avg` : 'N/A';
  const stochStr = d.stoch_k!=null ? `${d.stoch_k}` : 'N/A';
  const stochCls = d.stoch_bull ? 'bull' : 'bear';
  const stochStat = d.stoch_k>80?'● Overbought':d.stoch_k<20?'● Oversold':'● In Range';

  const atrSection = d.signal==='BUY' ? `
  <div>
    <div class="sec-lbl">⚡ ATR — Volatility &amp; Trade Sizing (${curTF})</div>
    <div class="atr-block">
      <div>
        <div class="atr-lbl">ATR (14)</div>
        <div class="atr-v">${d.atr}</div>
        <div style="font-size:10px;color:var(--muted);margin-top:4px;">Avg True Range<br>TF: ${curTF}</div>
      </div>
      <div class="atr-d"></div>
      <div class="atr-det">
        <div><div class="atr-rl">🔴 Stop Loss (1.5× ATR)</div><div class="atr-rv stop">${d.stop_loss}</div></div>
        <div><div class="atr-rl">Risk Per Share</div><div class="atr-rv" style="color:var(--muted);font-size:12px;">Entry − Stop Loss</div></div>
      </div>
      <div class="atr-det">
        <div><div class="atr-rl">🟢 Target (2× ATR)</div><div class="atr-rv tgt">${d.target}</div></div>
        <div><div class="atr-rl">Risk : Reward</div><div class="atr-rv" style="color:var(--ay);font-size:12px;">1 : 2.0</div></div>
      </div>
    </div>
  </div>` : '';

  const epsCls = d.eps_trend==='up'?'eps-u':d.eps_trend==='down'?'eps-d':'eps-f';
  const epsTxt = d.eps_trend==='up'?'▲ Rising':d.eps_trend==='down'?'▼ Falling':'— Flat';

  document.getElementById('out').innerHTML = `
  <div class="ac">
    <div class="ac-hdr">
      <div>
        <div class="ac-name">${d.name}</div>
        <div class="ac-meta">
          <span class="mtag mc">${d.country_flag} ${d.country==='IN'?'India':'USA'}</span>
          <span class="mtag ms">📂 ${d.sector}</span>
          <span class="mtag mt">⏱ ${curTF} Timeframe</span>
          <span style="font-family:'Space Mono',monospace;font-size:11px;color:var(--muted);">${d.ticker}</span>
        </div>
      </div>
      <div class="ac-pb">
        <div class="ac-price">${d.price}</div>
        <div class="${d.change_pos?'chg-p':'chg-n'}">${d.change_pos?'▲':'▼'} ${d.change}</div>
        <div style="margin-top:10px;"><span class="sig ${sigCls}">${sigEmoji} ${d.signal}</span></div>
      </div>
    </div>

    <div class="ac-body">

      <!-- TOW -->
      <div>
        <div class="sec-lbl">⚔️ Tug of War — Bull vs Bear Pressure</div>
        <div class="tow-lbls">
          <span class="tow-bear-l">🐻 Bearish ${d.bear_pct}%</span>
          <span class="tow-bull-l">Bullish ${d.bull_pct}% 🐂</span>
        </div>
        <div class="tow-bar">
          <div class="tow-bf" style="width:${d.bear_pct}%"></div>
          <div class="tow-bull"></div>
          <div class="tow-div"></div>
        </div>
        <div class="tow-sr">
          <span class="tow-st">Score:</span>
          <span class="tow-sn ${scoreCls}">${d.score} / 100</span>
          <span class="tow-st">${d.bull_count} of ${d.total_ind} indicators bullish</span>
        </div>
      </div>

      <!-- INDICATORS -->
      <div>
        <div class="sec-lbl">📊 Technical Indicators — ${curTF}</div>
        <div class="ig">
          <div class="ic ${rsiCls(d.rsi)}">
            <div class="in">RSI (14)</div>
            <div class="iv ${rsiCls(d.rsi)}">${d.rsi??'N/A'}</div>
            <div class="rsi-bar"><div class="rsi-fill" style="width:${rsiPct}%;background:${rsiColor(d.rsi)}"></div></div>
            <div class="ist ${rsiCls(d.rsi)}">${rsiStat(d.rsi)}</div>
          </div>
          <div class="ic ${d.macd_bull?'bull':'bear'}">
            <div class="in">MACD</div>
            <div class="iv ${d.macd_bull?'bull':'bear'}" style="font-size:14px;">${d.macd??'N/A'}</div>
            <div class="ist ${d.macd_bull?'bull':'bear'}">${d.macd_bull?'● Bullish Cross':'● Bearish Cross'}</div>
          </div>
          <div class="ic ${d.ema_bull?'bull':'bear'}">
            <div class="in">EMA 50/200</div>
            <div class="iv ${d.ema_bull?'bull':'bear'}" style="font-size:13px;">${d.ema_signal}</div>
            <div class="ist ${d.ema_bull?'bull':'bear'}">${d.ema_bull?'● Uptrend':'● Downtrend'}</div>
          </div>
          <div class="ic ${d.volume_bull?'bull':'neut'}">
            <div class="in">Volume</div>
            <div class="iv ${d.volume_bull?'bull':'neut'}">${volStr}</div>
            <div class="ist ${d.volume_bull?'bull':'neut'}">${d.volume_bull?'● Strong':'● Normal'}</div>
          </div>
          <div class="ic ${stochCls}">
            <div class="in">Stochastic</div>
            <div class="iv ${stochCls}">${stochStr}</div>
            <div class="ist ${stochCls}">${stochStat}</div>
          </div>
        </div>
      </div>

      <!-- ATR (BUY only) -->
      ${atrSection}

      <!-- S&R -->
      <div>
        <div class="sec-lbl">📍 Support &amp; Resistance — ${curTF} Timeframe | Pivot: ${d.pivot}</div>
        <div class="srg">
          <div class="src">
            <div class="srh r">🔴 Resistance Levels</div>
            <div class="srl">
              <div class="srv r"><span class="srvl">R1 — Nearest</span><span class="srvp r">${d.resistance[0]||'N/A'}</span></div>
              <div class="srv r"><span class="srvl">R2 — Moderate</span><span class="srvp r">${d.resistance[1]||'N/A'}</span></div>
              <div class="srv r"><span class="srvl">R3 — Strong</span><span class="srvp r">${d.resistance[2]||'N/A'}</span></div>
            </div>
          </div>
          <div class="src">
            <div class="srh s">🟢 Support Levels</div>
            <div class="srl">
              <div class="srv s"><span class="srvl">S1 — Nearest</span><span class="srvp s">${d.support[0]||'N/A'}</span></div>
              <div class="srv s"><span class="srvl">S2 — Moderate</span><span class="srvp s">${d.support[1]||'N/A'}</span></div>
              <div class="srv s"><span class="srvl">S3 — Strong</span><span class="srvp s">${d.support[2]||'N/A'}</span></div>
            </div>
          </div>
        </div>
        <div class="sr-note">⚠️ S&amp;R levels dynamically calculated per selected timeframe (${curTF})</div>
      </div>

      <!-- FUNDAMENTALS -->
      <div>
        <div class="sec-lbl">📈 Fundamental Overlay</div>
        <div class="fundg">
          <div class="fc"><div class="fl2">P/E Ratio</div><div class="fv">${d.pe}</div><div class="fsb">Price-to-Earnings</div></div>
          <div class="fc"><div class="fl2">EPS Trend</div><div class="fv ${epsCls}">${epsTxt}</div><div class="fsb">${d.eps} trailing EPS</div></div>
          <div class="fc"><div class="fl2">Market Cap</div><div class="fv">${d.market_cap}</div><div class="fsb">Total Capitalization</div></div>
          <div class="fc"><div class="fl2">52-Week Range</div><div class="fv" style="font-size:13px;">${d.week52_low} – ${d.week52_high}</div><div class="fsb">Low / High</div></div>
          <div class="fc"><div class="fl2">Beta</div><div class="fv">${d.beta}</div><div class="fsb">Volatility vs Market</div></div>
          <div class="fc"><div class="fl2">Dividend Yield</div><div class="fv">${d.dividend_yield}</div><div class="fsb">Annual Yield</div></div>
        </div>
      </div>

    </div>
  </div>`;

  mark('s5','done','✓'); document.getElementById('s5v').textContent='✅ Done';
}

// ── Bootstrap sector dropdown for default country (IN) ──
(function init() {
  const sectors = Object.keys(DATA['IN'] || {});
  const secSel = document.getElementById('secSel');
  secSel.innerHTML = '<option value="">— Select Sector —</option>' +
    sectors.map(s=>`<option value="${s}">${s}</option>`).join('');
})();
</script>
</body>
</html>
"""


def build_html(data: dict, generated_at: str) -> str:
    html = HTML_TEMPLATE.replace("__GENERATED__", generated_at)
    html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
    return html


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MarketIntel Stock Analyser")
    parser.add_argument("--country",   choices=["IN","US","ALL"], default="ALL",  help="Country to scan")
    parser.add_argument("--sector",    default=None,  help="Specific sector (optional)")
    parser.add_argument("--ticker",    default=None,  help="Single ticker (optional)")
    parser.add_argument("--timeframes",default="1D",  help="Comma-separated timeframes: 15m,1H,1D,1W")
    parser.add_argument("--output",    default="docs/index.html", help="Output HTML path")
    args = parser.parse_args()

    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip() in TF_CONFIG]
    if not tfs:
        tfs = ["1D"]

    countries = ["IN","US"] if args.country == "ALL" else [args.country]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*60}")
    print(f"  MarketIntel Analysis — {generated_at}")
    print(f"  Countries: {countries} | Timeframes: {tfs}")
    print(f"{'='*60}\n")

    # Structure: data[country][sector] = [stock_result, ...]
    output_data = {}

    for country in countries:
        output_data[country] = {}
        universe = STOCKS.get(country, {})

        for sector, stocks in universe.items():
            # Filter by sector if requested
            if args.sector and sector != args.sector:
                continue

            print(f"\n[{country}] {sector}")
            output_data[country][sector] = []

            for ticker, name in stocks:
                # Filter by ticker if requested
                if args.ticker and ticker != args.ticker:
                    continue

                for tf in tfs:
                    result = analyse_stock(ticker, name, country, sector, tf)
                    if result:
                        output_data[country][sector].append(result)

            # Remove empty sectors
            if not output_data[country][sector]:
                del output_data[country][sector]

        # If sector has no known stocks, it lands in Others via yfinance sector info
        # (for manually added tickers outside the predefined list, sector="Others")

    # Generate HTML
    html = build_html(output_data, generated_at)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    total = sum(len(v) for country in output_data.values() for v in country.values())
    print(f"\n{'='*60}")
    print(f"  ✅ Done! Analysed {total} stock-timeframe combinations.")
    print(f"  📄 HTML saved to: {out_path.resolve()}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
