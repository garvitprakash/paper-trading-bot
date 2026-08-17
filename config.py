"""Config — GitHub Actions me ye values 'Secrets' se aayengi (environment variables ke through).

Apne PC par local test karna ho to neeche 'YOUR_...' ki jagah apni details daal
sakte hain, PAR GitHub par push karne se PEHLE unhe wapas 'YOUR_...' kar dein —
asli values sirf GitHub Secrets me hi rakhein, is file me kabhi nahi.
"""

import os

# ---- Angel One SmartAPI credentials (GitHub Secrets se aayengi) ----
API_KEY = os.environ.get("ANGEL_API_KEY", "YOUR_API_KEY")
CLIENT_CODE = os.environ.get("ANGEL_CLIENT_CODE", "YOUR_CLIENT_ID")
PASSWORD = os.environ.get("ANGEL_PASSWORD", "YOUR_MPIN")
TOTP_SECRET = os.environ.get("ANGEL_TOTP_SECRET", "YOUR_TOTP_SECRET")

# ---- Telegram notifications (GitHub Secrets se aayengi) ----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# ---- Trading settings (ye sab yahin badal sakte hain, secret nahi hain) ----
CAPITAL = 50000
RISK_PER_TRADE_PCT = 1.0
MAX_SWING_POSITIONS = 3
MAX_INTRADAY_POSITIONS = 2
SWING_SCORE_THRESHOLD = 80
INTRADAY_SCORE_THRESHOLD = 67

SWING_TARGET_PCT = 0.09
SWING_STOP_PCT = 0.04
SWING_TRAIL_TRIGGER_PCT = 0.02
SWING_TRAIL_PCT = 0.04

INTRADAY_TARGET_PCT = 0.02

WATCHLIST = [
    # Large-cap / Swing ke liye achhe (trend-following)
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "ITC", "SBIN",
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "TITAN", "SUNPHARMA",
    "WIPRO", "TATAMOTORS", "TATASTEEL", "HCLTECH", "JSWSTEEL", "COALINDIA", "NTPC",
    "ADANIENT", "ADANIPORTS", "BAJFINANCE", "BAJAJFINSV", "MARUTI",
    "HINDALCO", "VEDANTA", "ONGC", "GAIL", "IOC", "BPCL", "INDUSINDBK",

    # High-volume / Intraday favorites (retail me bahut active, price movement zyada)
    "PNB", "CANBK", "BANKBARODA", "FEDERALBNK", "IDFCFIRSTB", "YESBANK",
    "IDEA", "SUZLON", "TATAPOWER", "SAIL", "NATIONALUM", "RVNL", "IRFC", "ZOMATO","CUPID", "NETWEB", "RRKABEL",
]

DATA_DIR = "data"
