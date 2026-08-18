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


def buy(state, ptype, symbol, name, qty, price, stop, target, extra=None):
    """extra: optional dict — intraday-pro ke liye initial_sl/risk_per_share/stage/atr_mult wagera."""
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
    if extra:
        pos.update(extra)
    state["positions"].append(pos)
    save_state(state)
    return pos


def sell(state, position, price, reason):
    """Poori position close karo."""
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


def partial_sell(state, position, sell_qty, price, reason):
    """Position ka ek hissa bech do, baaki qty ke saath position open rahegi.

    Position dict me hi update kar deta hai (caller ko state["positions"] me
    us position ko refresh karna nahi padta — same list object modify hota hai).
    """
    sell_qty = min(sell_qty, position["qty"])
    if sell_qty < 1:
        return None
    sale_amount = sell_qty * price
    profit = sale_amount - position["entry"] * sell_qty
    state["cash"] += sale_amount

    trade = {
        "type": position["type"], "symbol": position["symbol"], "name": position["name"],
        "purchase_date": position["entry_date"], "qty": sell_qty,
        "purchase_amount": position["entry"] * sell_qty,
        "sale_date": datetime.now().isoformat(), "sale_qty": sell_qty,
        "sale_amount": sale_amount, "profit": profit, "reason": reason,
    }
    state["history"].append(trade)

    # position ki remaining qty update karo (in-place, list me object same rehta hai)
    position["qty"] -= sell_qty

    save_state(state)
    return trade
