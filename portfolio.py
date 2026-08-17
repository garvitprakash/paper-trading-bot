"""Virtual (paper) portfolio ka state — positions, cash, trade history.

State disk par data/state.json me save hota hai, isliye script restart hone par
bhi purani open positions/history yaad rehti hai.
"""

import json
import os
from datetime import datetime

import config

STATE_FILE = os.path.join(config.DATA_DIR, "state.json")


def _default_state():
    return {"cash": config.CAPITAL, "positions": [], "history": []}


def load_state():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return _default_state()


def save_state(state):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def open_positions(state, ptype=None):
    if ptype:
        return [p for p in state["positions"] if p["type"] == ptype]
    return state["positions"]


def has_position(state, symbol):
    return any(p["symbol"] == symbol for p in state["positions"])


def buy(state, ptype, symbol, name, qty, price, stop, target):
    cost = qty * price
    if cost > state["cash"] or qty < 1:
        return None
    state["cash"] -= cost
    pos = {
        "id": f"{symbol}-{datetime.now().timestamp()}",
        "type": ptype, "symbol": symbol, "name": name, "qty": qty,
        "entry": price, "entry_date": datetime.now().isoformat(),
        "stop": stop, "target": target, "peak": price,
    }
    state["positions"].append(pos)
    save_state(state)
    return pos


def sell(state, position, price, reason):
    state["positions"] = [p for p in state["positions"] if p["id"] != position["id"]]
    sale_amount = position["qty"] * price
    profit = sale_amount - position["entry"] * position["qty"]
    state["cash"] += sale_amount
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
