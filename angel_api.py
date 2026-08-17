"""Angel One SmartAPI se login aur real market data fetch karne wala wrapper.

Sirf READ-ONLY data ke liye use hota hai (LTP + historical candles).
Ye kahin bhi order place NAHI karta — bot sirf paper (virtual) trading karta hai.
"""

import time
from datetime import datetime, timedelta

import pyotp
from SmartApi import SmartConnect

import config


class AngelClient:
    def __init__(self):
        self.obj = SmartConnect(api_key=config.API_KEY)
        self.session = None

    def login(self):
        totp = pyotp.TOTP(config.TOTP_SECRET).now()
        self.session = self.obj.generateSession(config.CLIENT_CODE, config.PASSWORD, totp)
        if not self.session or not self.session.get("status"):
            raise Exception(f"Angel One login fail ho gaya: {self.session}")
        print("Angel One login safal.")
        return self.session

    def ltp(self, exch_seg, symbol, token):
        r = self.obj.ltpData(exch_seg, symbol, token)
        return r["data"]["ltp"]

    def historical_daily(self, exch_seg, token, days=420):
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        params = {
            "exchange": exch_seg,
            "symboltoken": token,
            "interval": "ONE_DAY",
            "fromdate": from_date.strftime("%Y-%m-%d %H:%M"),
            "todate": to_date.strftime("%Y-%m-%d %H:%M"),
        }
        r = self.obj.getCandleData(params)
        return self._parse(r)

    def historical_intraday(self, exch_seg, token):
        today = datetime.now().strftime("%Y-%m-%d")
        params = {
            "exchange": exch_seg,
            "symboltoken": token,
            "interval": "FIFTEEN_MINUTE",
            "fromdate": f"{today} 09:15",
            "todate": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        r = self.obj.getCandleData(params)
        return self._parse(r)

    @staticmethod
    def _parse(r):
        candles = []
        for row in r.get("data", []) or []:
            # row format: [timestamp, open, high, low, close, volume]
            candles.append({
                "time": row[0], "open": row[1], "high": row[2],
                "low": row[3], "close": row[4], "volume": row[5],
            })
        return candles


def safe_call(fn, *args, retries=2, delay=1.0, **kwargs):
    """Small retry helper — broker API kabhi-kabhi timeout/rate-limit deta hai."""
    last_err = None
    for _ in range(retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            time.sleep(delay)
    print(f"API call fail ho gayi: {last_err}")
    return None
