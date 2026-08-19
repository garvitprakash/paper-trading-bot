"""Market hours check — dono (Swing aur Intraday) engines yahi use karte hain."""

from datetime import datetime

import pytz

IST = pytz.timezone("Asia/Kolkata")


def now_ist():
    return datetime.now(IST)


def today_str():
    return now_ist().strftime("%Y-%m-%d")


def market_open():
    n = now_ist()
    if n.weekday() >= 5:
        return False
    open_t = n.replace(hour=9, minute=15, second=0, microsecond=0)
    close_t = n.replace(hour=15, minute=30, second=0, microsecond=0)
    return open_t <= n <= close_t


def square_off_time():
    """Intraday positions ko is time ke baad zabardasti square-off karna hai."""
    n = now_ist()
    return n.hour > 15 or (n.hour == 15 and n.minute >= 5)
