"""Har scan (Swing/Intraday) apna 'status' yahan save karta hai — kitne stocks
scan kiye, top candidates kya mile, unka score kya tha. Ye data website par
'Live Scan Activity' section me dikhta hai.

Ye file dono engines (swing_engine.py, intraday_engine.py) use karte hain,
dono hi caller (tab_loop.py) ke STATE_LOCK ke andar chalte hain, isliye alag
se lock lagane ki zaroorat nahi hai.
"""

import json
import os
from datetime import datetime

import config

STATUS_FILE = os.path.join(config.DATA_DIR, "scan_status.json")


def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def update_section(section, data):
    """section: 'swing' ya 'intraday'. data: dict jo us section me save hoga."""
    status = load_status()
    status[section] = data
    status["last_updated"] = datetime.now().isoformat()
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2, default=str)
