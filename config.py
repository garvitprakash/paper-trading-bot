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
CAPITAL = 100000
RISK_PER_TRADE_PCT = 1.0
MAX_SWING_POSITIONS = 3
MAX_INTRADAY_POSITIONS = 2
SWING_SCORE_THRESHOLD = 80
INTRADAY_SCORE_THRESHOLD = 67

SWING_TARGET_PCT = 0.09
SWING_STOP_PCT = 0.04
SWING_TRAIL_TRIGGER_PCT = 0.02
SWING_TRAIL_PCT = 0.04

# ---- Intraday PRO settings (R-multiple based dynamic trailing system) ----
INTRADAY_RISK_PCT = 0.5          # ek trade me capital ka sirf 0.5% risk
INTRADAY_MIN_RR = 3.0            # entry ke time kam se kam 1:3 R:R chahiye, warna trade reject
INTRADAY_PARTIAL_BOOK_R = 3.0    # is R-multiple pe pahunchte hi partial profit book hoga
INTRADAY_PARTIAL_BOOK_PCT = 0.25 # kitna % position partial book hoga (baaki trail hoga)
INTRADAY_BREAKEVEN_R = 1.0       # is R pe SL breakeven ke paas aayega
INTRADAY_STRUCTURE_TRAIL_R = 2.0 # is R se structure (swing-low) based trailing shuru hogi
INTRADAY_DAILY_LOSS_LIMIT_PCT = 2.0  # din ka total loss capital ka itna % hote hi naya trade band
ATR_PERIOD = 14

# Cap-size ke hisaab se ATR trailing multiplier — large-cap kam volatile (tight trail
# chalta hai), small-cap zyada volatile (loose trail chahiye warna jaldi stop-out ho jaate hain)
ATR_MULT = {"large": 1.5, "mid": 1.8, "small": 2.0}
ATR_MULTIPLIER_DEFAULT = 1.8  # agar cap class na pata chale to ye use hoga

# Smart early-exit rule: profit chal raha ho par volume gir raha ho + price VWAP se
# bahut dur ho + reversal candle bane, to poori trend khatam hone ka wait na karo
SMART_EXIT_MIN_R = 1.0            # kam se kam itna R profit hone ke baad hi ye rule check hoga
SMART_EXIT_MAX_R = 3.0            # 3R ke baad ye rule nahi (wahan alag partial-book rule chalta hai)
SMART_EXIT_VWAP_DIST_PCT = 1.5    # VWAP se itna % dur hone par "bahut dur" maana jayega
SMART_EXIT_BOOK_PCT = 0.25        # kitna % position book hoga jab ye rule trigger ho

# ---- Universe scanning ----
# Watchlist ab fixed nahi hai — universe.py NSE se Nifty50+Next50+Midcap100+Smallcap100
# (~300-500 stocks) fetch karta hai. Itne stocks scan karne me time zyada lagta hai,
# isliye har API call ke beech thoda zyada gap rakha hai (rate-limit se bachne ke liye).
SCAN_DELAY_SECONDS = 0.35

DATA_DIR = "data"
