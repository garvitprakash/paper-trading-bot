"""Tablet (Termux) ke liye continuous runner — AB DO ALAG THREADS chalte hain:

  - Swing thread: har SWING_INTERVAL_MINUTES (default 15) me ek scan
  - Intraday thread: har INTRADAY_INTERVAL_MINUTES (default 1) me ek scan

Dono independent hain — Swing ka scan lamba chale to bhi Intraday apne time
pe chalta rahega. Dono ek hi state.json (portfolio) use karte hain, isliye
portfolio.STATE_LOCK se protect kiya hai taaki data corrupt na ho.

Har scan ke baad GitHub par push hota hai (dashboard live rahe):
  - Trade (state.json) badla ho to HAMESHA turant push hota hai
  - Sirf scan-status (scan_status.json, koi trade nahi hua) badla ho to
    STATUS_PUSH_INTERVAL_SECONDS (config.py, default 5 min) me ek baar hi
    push hota hai — taaki GitHub par bahut zyada pushes na ho jaayein
    (Intraday har 1 min scan karta hai, har baar push karna zyada hoga)

Chalane ka tarika: python3 tab_loop.py
Rokne ka tarika: Ctrl + C
"""

import subprocess
import threading
import time

import config
import portfolio as pf
from intraday_engine import scan_intraday
from market_hours import market_open, now_ist
from swing_engine import scan_swing

SWING_INTERVAL_MINUTES = 15
INTRADAY_INTERVAL_MINUTES = 1

GIT_LOCK = threading.Lock()  # git push bhi serialize karna hai
_last_status_push = 0.0  # timestamp — status-only push ka throttle track karne ke liye


def _has_diff(path):
    """True agar is file me uncommitted changes hain (modified YA bilkul nayi/untracked)."""
    result = subprocess.run(["git", "status", "--porcelain", "--", path], capture_output=True, text=True)
    return bool(result.stdout.strip())


def git_push():
    global _last_status_push
    with GIT_LOCK:
        try:
            state_changed = _has_diff("data/state.json")
            status_changed = _has_diff("data/scan_status.json")

            if not state_changed and not status_changed:
                return  # kuch bhi naya nahi hai

            now = time.time()
            status_due = (now - _last_status_push) >= config.STATUS_PUSH_INTERVAL_SECONDS

            # Agar sirf status badla hai (koi trade nahi) aur abhi throttle
            # window poori nahi hui, to is baar push skip karo
            if not state_changed and status_changed and not status_due:
                return

            subprocess.run(["git", "add", "data/"], check=True)
            result = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if result.returncode != 0:
                msg = f"Portfolio update {now_ist().strftime('%Y-%m-%d %H:%M IST')}"
                subprocess.run(["git", "commit", "-m", msg], check=True)
                subprocess.run(["git", "pull", "--rebase"], check=False)
                subprocess.run(["git", "push"], check=True)
                print("GitHub par push ho gaya.")
                if status_changed:
                    _last_status_push = now
        except Exception as e:
            print("Git push me error:", e)


def swing_worker():
    print("[Swing Thread] shuru ho gaya.")
    while True:
        try:
            if market_open():
                with pf.STATE_LOCK:
                    state = pf.load_state()
                    scan_swing(state)
                git_push()
            else:
                print(f"[Swing] [{now_ist().strftime('%H:%M:%S')}] Market band hai.")
        except Exception as e:
            print("[Swing] Error:", e)
        time.sleep(SWING_INTERVAL_MINUTES * 60)


def intraday_worker():
    print("[Intraday Thread] shuru ho gaya.")
    while True:
        try:
            if market_open():
                with pf.STATE_LOCK:
                    state = pf.load_state()
                    scan_intraday(state)
                git_push()
            else:
                print(f"[Intraday] [{now_ist().strftime('%H:%M:%S')}] Market band hai.")
        except Exception as e:
            print("[Intraday] Error:", e)
        time.sleep(INTRADAY_INTERVAL_MINUTES * 60)


def main():
    print("Tablet runner shuru ho gaya (Swing + Intraday alag-alag threads me). Ctrl+C se rokein.")
    t1 = threading.Thread(target=swing_worker, daemon=True)
    t2 = threading.Thread(target=intraday_worker, daemon=True)
    t1.start()
    time.sleep(5)  # dono ek saath shuru na ho, thoda gap
    t2.start()

    # Main thread ko zinda rakhna hai taaki daemon threads chalte rahein
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
