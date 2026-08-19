"""Yahoo Finance se real NSE market data — koi login, TOTP, ya API key ki
zaroorat nahi. Bas symbol (jaise RELIANCE) diya, wo khud '.NS' laga kar
Yahoo se daily/intraday candles le aata hai.
"""

import time

import requests

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


def _fetch_chart(symbol, range_, interval):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}.NS?range={range_}&interval={interval}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    result = data.get("chart", {}).get("result")
    if not result:
        return None
    return result[0]


def _parse_candles(result):
    ts = result.get("timestamp") or []
    quote = result.get("indicators", {}).get("quote", [{}])[0]
    closes = quote.get("close", [])
    opens = quote.get("open", [])
    highs = quote.get("high", [])
    lows = quote.get("low", [])
    vols = quote.get("volume", [])

    candles = []
    for i, t in enumerate(ts):
        if i >= len(closes) or closes[i] is None:
            continue
        candles.append({
            "time": t * 1000,
            "open": opens[i], "high": highs[i], "low": lows[i],
            "close": closes[i], "volume": vols[i] or 0,
        })
    return candles


def historical_daily(symbol, days=None):
    """~2 saal ka daily data — Swing strategy ke liye (50/200 EMA chahiye)."""
    result = _fetch_chart(symbol, "2y", "1d")
    if not result:
        return None
    candles = _parse_candles(result)
    ltp = result.get("meta", {}).get("regularMarketPrice")
    if ltp and candles:
        candles[-1]["close"] = ltp  # sabse latest price se update kar do
    return candles


def historical_intraday(symbol):
    """Aaj ka 15-min candles — Intraday PRO strategy ke liye."""
    result = _fetch_chart(symbol, "1d", "15m")
    if not result:
        return None
    candles = _parse_candles(result)
    ltp = result.get("meta", {}).get("regularMarketPrice")
    if ltp and candles:
        candles[-1]["close"] = ltp
    return candles


def safe_call(fn, *args, retries=2, delay=1.5, **kwargs):
    """Chhota retry helper — Yahoo kabhi-kabhi timeout/glitch de sakta hai."""
    last_err = None
    for _ in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            time.sleep(delay)
    print(f"Yahoo Finance se data nahi mila: {last_err}")
    return None
