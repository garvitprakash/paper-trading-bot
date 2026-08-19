"""GitHub Actions (ya kisi single-run use) ke liye — ek scan karke exit ho
jaata hai. Ab ye sirf ek thin wrapper hai — asli logic swing_engine.py aur
intraday_engine.py me hai (jo tablet ka tab_loop.py bhi use karta hai), taaki
dono jagah same code chale, alag-alag maintain na karna pade.
"""

import portfolio as pf
from intraday_engine import scan_intraday
from market_hours import market_open, now_ist
from swing_engine import scan_swing


def main():
    if not market_open():
        print(f"[{now_ist().strftime('%H:%M:%S')}] Market band hai, is run me kuch nahi karna.")
        return

    state = pf.load_state()

    print(f"[{now_ist().strftime('%H:%M:%S')}] Swing scan shuru...")
    scan_swing(state)

    print(f"[{now_ist().strftime('%H:%M:%S')}] Intraday scan shuru...")
    scan_intraday(state)

    print("Scan complete. Cash:", round(state["cash"]), "Open positions:", len(state["positions"]))


if __name__ == "__main__":
    main()
