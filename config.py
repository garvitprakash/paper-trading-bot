"""Config — GitHub Actions me ye values 'Secrets' se aayengi (environment variables ke through).

Data ab Yahoo Finance se aata hai — koi login/API-key/TOTP ki zaroorat nahi hai
(pehle Angel One use hota tha, ab hata diya gaya hai). Sirf Telegram credentials
chahiye notifications ke liye.
"""

import os

# ---- Telegram notifications (GitHub Secrets se aayengi) ----
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")

# ---- Trading settings (ye sab yahin badal sakte hain, secret nahi hain) ----
# Swing aur Intraday ab do ALAG cash pools use karte hain — ek doosre ka paisa
# nahi chhuenge. Website par bhi dono alag-alag dikhte hain.
SWING_CAPITAL = 50000
INTRADAY_CAPITAL = 50000
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
# Watchlist ab fixed nahi hai — universe.py NSE se Nifty50+Midcap50+Smallcap50
# (~150 stocks) fetch karta hai. Yahoo Finance Angel One jaisa strict rate-limit
# nahi lagata, isliye delay chhota rakh sakte hain.
SCAN_DELAY_SECONDS = 0.4

# Har trade me max itna hi paisa lagega (ek company me), chahe risk-calculation
# zyada bataye — ye ek hard safety cap hai.
MAX_TRADE_AMOUNT = 5000

# Website par 'Live Scan Activity' dikhane ke liye — scan-status (jisme koi
# trade nahi hua) ko GitHub par itni der me ek baar hi push karte hain (taaki
# git par bahut zyada pushes na ho jaayein). Trade hone par ye rule lagu nahi
# hota — wo hamesha turant push hota hai.
STATUS_PUSH_INTERVAL_SECONDS = 300  # 5 minute

DATA_DIR = "data"
