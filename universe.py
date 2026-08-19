"""Stock universe — Nifty 50 + Midcap 50 + Smallcap 50 (total ~150 stocks).
NSE ki public index-constituent CSV files se fetch karta hai (roz nahi, cache
karke rakhta hai taaki har scan pe dobara download na karna pade).

Pehle 300-500 stocks wala universe tha, jisse Angel One rate-limit lagne laga
tha ("Too many requests"). Isliye ab chhota (150) universe use kar rahe hain —
kam API calls, kam risk, jaldi scan complete hota hai.

Har symbol ko uski 'cap class' (large/mid/small) bhi milti hai — isse Intraday
PRO system apna ATR trailing multiplier decide karta hai.
"""

import csv
import io
import json
import os
import time

import requests

import config

INDEX_URLS = {
    "large": [
        "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    ],
    "mid": [
        "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    ],
    "small": [
        "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    ],
}

CACHE_FILE = os.path.join(config.DATA_DIR, "universe_cache.json")
CACHE_MAX_AGE_HOURS = 24

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/csv,application/vnd.ms-excel,*/*",
}

FALLBACK_WATCHLIST = {
    "RELIANCE": "large", "TCS": "large", "HDFCBANK": "large", "INFY": "large",
    "ICICIBANK": "large", "ITC": "large", "SBIN": "large", "BHARTIARTL": "large",
    "KOTAKBANK": "large", "LT": "large", "AXISBANK": "large", "TITAN": "large",
    "SUNPHARMA": "large", "WIPRO": "large", "TATAMOTORS": "large",
    "TATASTEEL": "large", "HCLTECH": "large", "JSWSTEEL": "large",
    "COALINDIA": "large", "NTPC": "large",
}


def _fetch_csv_symbols(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        reader = csv.DictReader(io.StringIO(r.text))
        symbols = []
        for row in reader:
            sym = row.get("Symbol") or row.get("SYMBOL")
            if sym:
                symbols.append(sym.strip())
        return symbols
    except Exception as e:
        print(f"Index list fetch fail ({url}): {e}")
        return []


def build_universe(force_refresh=False):
    os.makedirs(config.DATA_DIR, exist_ok=True)

    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                cached = json.load(f)
            age_hours = (time.time() - cached.get("fetched_at", 0)) / 3600
            if age_hours < CACHE_MAX_AGE_HOURS and cached.get("universe"):
                print(f"Universe cache use kar rahe hain ({len(cached['universe'])} stocks, {age_hours:.1f}h old)")
                return cached["universe"]
        except Exception:
            pass

    universe = {}
    for cap_class, urls in INDEX_URLS.items():
        for url in urls:
            for sym in _fetch_csv_symbols(url):
                universe[sym] = cap_class

    if not universe:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE) as f:
                    old = json.load(f)
                if old.get("universe"):
                    print("NSE fetch fail hua, purani cache use kar rahe hain.")
                    return old["universe"]
            except Exception:
                pass
        print("NSE fetch fail hua aur koi cache nahi hai — chhoti fallback list use ho rahi hai.")
        return dict(FALLBACK_WATCHLIST)

    with open(CACHE_FILE, "w") as f:
        json.dump({"fetched_at": time.time(), "universe": universe}, f)

    print(f"Naya universe fetch hua: {len(universe)} stocks (Nifty50 + Midcap50 + Smallcap50)")
    return universe