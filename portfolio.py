"""Virtual (paper) portfolio ka state — positions, cash, trade history.

State disk par data/state.json me save hota hai, isliye script restart hone par
bhi purani open positions/history yaad rehti hai.

Swing aur Intraday ke ALAG cash pools hain (swing_cash, intraday_cash) — ek
doosre ka paisa nahi chhuenge. Website par bhi dono alag-alag dikhte hain.

Ab Swing aur Intraday do ALAG loops (threads) me chalte hain, isliye ek shared
STATE_LOCK diya hai — jo bhi engine state padhe/likhe, usse pehle lock lena
chahiye, taaki dono ek saath state.json ko corrupt na kar dein.
"""

import json
import os
import threading
from datetime import datetime

import config

STATE_FILE = os.path.join(config.DATA_DIR, "state.json")

# Swing aur Intraday engine dono isi lock ko use karte hain apne poore
# scan+save operation ke around — taaki ek waqt me sirf ek hi engine
# state.json padhe/likhe.
STATE_LOCK = threading.Lock()


def _cash_key(ptype):
    return f"{ptype}_cash"


def _default_state():
    return {
        "swing_cash": config.SWING_CAPITAL,
        "intraday_cash": config.INTRADAY_CAPITAL,
        "positions": [],
        "history": [],
    }


def load_state():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
        # Purane format (single "cash") se migrate karna ho to safe fallback
        if "swing_cash" not in state:
            state["swing_cash"] = state.get("cash", config.SWING_CAPITAL)
        if "intraday_cash" not in state:
            state["intraday_cash"] = config.INTRADAY_CAPITAL
        return state
    return _default_state()


def save_state(state):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def cash_for(state, ptype):
    return state[_cash_key(ptype)]


def open_positions(state, ptype=None):
    if ptype:
        return [p for p in state["positions"] if p["type"] == ptype]
    return state["positions"]


def has_position(state, symbol):
    return any(p["symbol"] == symbol for p in state["positions"])


def buy(state, ptype, symbol, name, qty, price, stop, target, extra=None):
    """extra: optional dict — intraday-pro ke liye initial_sl/risk_per_share/stage/atr_mult wagera."""
    key = _cash_key(ptype)
    cost = qty * price
    if cost > state[key] or qty < 1:
        return None
    state[key] -= cost
    pos = {
        "id": f"{symbol}-{datetime.now().timestamp()}",
        "type": ptype, "symbol": symbol, "name": name, "qty": qty,
        "entry": price, "entry_date": datetime.now().isoformat(),
        "stop": stop, "target": target, "peak": price,
    }
    if extra:
        pos.update(extra)
    state["positions"].append(pos)
    save_state(state)
    return pos


def sell(state, position, price, reason):
    """Poori position close karo."""
    key = _cash_key(position["type"])
    state["positions"] = [p for p in state["positions"] if p["id"] != position["id"]]
    sale_amount = position["qty"] * price
    profit = sale_amount - position["entry"] * position["qty"]
    state[key] += sale_amount
    trade = {
        "type": position["type"], "symbol": position["symbol"], "name": position["name"],
        "purchase_date": position["entry_date"], "qty": position["qty"],
        "purchase_amount": position["entry"] * position["qty"],
        "sale_date": datetime.now().isoformat(), "sale_qty": position["qty"],
        "sale_amount": sale_amount, "profit": profit, "reason": reason,
    }
    state["history"].append(trade)
    save_state(state)
    return trade


def partial_sell(state, position, sell_qty, price, reason):
    """Position ka ek hissa bech do, baaki qty ke saath position open rahegi."""
    key = _cash_key(position["type"])
    sell_qty = min(sell_qty, position["qty"])
    if sell_qty < 1:
        return None
    sale_amount = sell_qty * price
    profit = sale_amount - position["entry"] * sell_qty
    state[key] += sale_amount

    trade = {
        "type": position["type"], "symbol": position["symbol"], "name": position["name"],
        "purchase_date": position["entry_date"], "qty": sell_qty,
        "purchase_amount": position["entry"] * sell_qty,
        "sale_date": datetime.now().isoformat(), "sale_qty": sell_qty,
        "sale_amount": sale_amount, "profit": profit, "reason": reason,
    }
    state["history"].append(trade)

    position["qty"] -= sell_qty

    save_state(state)
    return trade
