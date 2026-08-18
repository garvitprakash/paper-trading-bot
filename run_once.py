"""GitHub Actions ke liye — ye script ek baar chalti hai (login -> scan -> exit).

Universe: ab fixed watchlist nahi — Nifty 50 + Nifty Next 50 + Midcap 100 + Smallcap 100
(NSE se dynamically fetch, ~300-500 stocks). Itne stocks scan karne me time zyada
lagta hai (10-15+ minute ek run me), isliye workflow me concurrency-guard bhi lagaya
hai taaki agla scheduled run overlap na kare.

Swing: pehle jaisa hi (50/200 EMA trend + breakout + volume + RSI, fixed target/stop/trailing).
Intraday: "PRO" system — R-multiple based dynamic trailing (10-rule discipline system +
cap-wise ATR + VWAP/9-EMA confirmation + smart early-exit).
"""

import time
from datetime import datetime

import pytz

import config
import portfolio as pf
from angel_api import AngelClient, safe_call
from notifier import (
    buy_message, daily_loss_limit_message, intraday_pro_buy_message,
    partial_exit_message, sell_message, send_telegram, smart_exit_message,
    trail_update_message,
)
from scrip_master import get_token_map
from strategy import evaluate_intraday_entry, swing_score, update_trailing
from universe import build_universe

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
    n = now_ist()
    return n.hour > 15 or (n.hour == 15 and n.minute >= 20)


def _resolvable_symbols(universe, token_map):
    """Universe ke symbols jinke liye Angel One ka token mil gaya, sirf wahi scan honge."""
    resolved = []
    for sym, cap_class in universe.items():
        info = token_map.get(sym)
        if info:
            resolved.append((sym, cap_class, info))
    return resolved


# ---------------- SWING (logic unchanged, ab bade universe pe chalti hai) ----------------
def scan_swing(client, symbols, state):
    results = []
    for sym, cap_class, info in symbols:
        candles = safe_call(client.historical_daily, info["exch_seg"], info["token"])
        if not candles:
            continue
        s = swing_score(candles)
        if s:
            results.append({"symbol": sym, "name": sym, "cap_class": cap_class, **s, **info})
        time.sleep(config.SCAN_DELAY_SECONDS)

    for pos in list(state["positions"]):
        if pos["type"] != "swing":
            continue
        match = next((r for r in results if r["symbol"] == pos["symbol"]), None)
        if not match:
            continue
        price = match["price"]
        pos["peak"] = max(pos["peak"], price)
        reason = None
        if price >= pos["target"]:
            reason = "Target Hit"
        elif price <= pos["stop"]:
            reason = "Stop Loss"
        elif pos["peak"] > pos["entry"] * (1 + config.SWING_TRAIL_TRIGGER_PCT) and price <= pos["peak"] * (1 - config.SWING_TRAIL_PCT):
            reason = "Trailing Stop"
        elif match["ema20"] and price < match["ema20"]:
            reason = "Trend Weak (20 EMA se neeche)"
        if reason:
            trade = pf.sell(state, pos, price, reason)
            send_telegram(sell_message(trade))
            print("SELL:", trade)

    open_count = len(pf.open_positions(state, "swing"))
    slots = config.MAX_SWING_POSITIONS - open_count
    if slots > 0:
        candidates = sorted(
            [r for r in results if r["score"] >= config.SWING_SCORE_THRESHOLD and not pf.has_position(state, r["symbol"])],
            key=lambda x: -x["score"],
        )
        for cand in candidates:
            if slots <= 0:
                break
            stop_price = cand["price"] * (1 - config.SWING_STOP_PCT)
            risk_amount = config.CAPITAL * (config.RISK_PER_TRADE_PCT / 100)
            risk_per_share = cand["price"] - stop_price
            per_trade_cap = config.CAPITAL / config.MAX_SWING_POSITIONS
            qty = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            qty = min(qty, int(state["cash"] / cand["price"]), int(per_trade_cap / cand["price"]))
            if qty < 1:
                continue
            target_price = cand["price"] * (1 + config.SWING_TARGET_PCT)
            pos = pf.buy(state, "swing", cand["symbol"], cand["name"], qty, cand["price"], stop_price, target_price)
            if pos:
                send_telegram(buy_message(pos))
                print("BUY:", pos)
                slots -= 1


# ---------------- INTRADAY PRO ----------------
def todays_intraday_realized_loss(state):
    today = today_str()
    total = 0.0
    for t in state["history"]:
        if t["type"] == "intraday" and str(t.get("sale_date", "")).startswith(today):
            total += t["profit"]
    return -total if total < 0 else 0.0


def scan_intraday_pro(client, symbols, state):
    force_exit = square_off_time()

    candle_cache = {}
    for sym, cap_class, info in symbols:
        candles = safe_call(client.historical_intraday, info["exch_seg"], info["token"])
        if candles and len(candles) >= 3:
            candle_cache[sym] = {"candles": candles, "info": info, "cap_class": cap_class}
        time.sleep(config.SCAN_DELAY_SECONDS)

    # ---- Manage open intraday-pro positions ----
    for pos in list(state["positions"]):
        if pos["type"] != "intraday":
            continue
        entry = candle_cache.get(pos["symbol"])
        if not entry:
            continue
        candles = entry["candles"]

        if force_exit:
            price = candles[-1]["close"]
            trade = pf.sell(state, pos, price, "Auto Square-Off (EOD)")
            r_mult = round((price - pos["entry"]) / pos["risk_per_share"], 2) if pos.get("risk_per_share") else None
            send_telegram(sell_message(trade, r_multiple=r_mult))
            print("SELL (Intraday EOD):", trade)
            continue

        result = update_trailing(pos, candles, config)

        if result["full_exit_reason"]:
            trade = pf.sell(state, pos, result["price"], result["full_exit_reason"])
            send_telegram(sell_message(trade, r_multiple=result["r_multiple"]))
            print("SELL (Intraday):", trade)
            continue

        if result["smart_exit_now"]:
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            book_qty = max(1, round(pos["qty"] * config.SMART_EXIT_BOOK_PCT))
            trade = pf.partial_sell(state, pos, book_qty, result["price"], "Smart Early Exit")
            if trade:
                pos["smart_partial_booked"] = True
                send_telegram(smart_exit_message(trade, pos, pos["qty"]))
                print("SMART PARTIAL SELL:", trade)
            continue

        if result["partial_exit_now"]:
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            book_qty = max(1, round(pos["qty"] * config.INTRADAY_PARTIAL_BOOK_PCT))
            trade = pf.partial_sell(state, pos, book_qty, result["price"], "Partial Book +3R")
            if trade:
                pos["partial_booked"] = True
                send_telegram(partial_exit_message(trade, pos, pos["qty"]))
                print("PARTIAL SELL (Intraday):", trade)
            continue

        if result["new_stop"] != pos["stop"] or result["stage"] != pos.get("stage", 0):
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            pf.save_state(state)
            if result["stage"] > 0:
                send_telegram(trail_update_message(pos, result))
                print("TRAIL UPDATE:", pos["symbol"], result)

    if force_exit:
        return

    # ---- Daily loss limit check ----
    loss_so_far = todays_intraday_realized_loss(state)
    loss_limit = config.CAPITAL * (config.INTRADAY_DAILY_LOSS_LIMIT_PCT / 100)
    if loss_so_far >= loss_limit:
        loss_pct = (loss_so_far / config.CAPITAL) * 100
        print(f"Daily loss limit hit: -₹{loss_so_far:.0f} ({loss_pct:.1f}%). Naya intraday trade nahi lenge.")
        send_telegram(daily_loss_limit_message(loss_pct))
        return

    # ---- New entries ----
    open_count = len(pf.open_positions(state, "intraday"))
    slots = config.MAX_INTRADAY_POSITIONS - open_count
    if slots <= 0:
        return

    candidates = []
    for sym, entry in candle_cache.items():
        if pf.has_position(state, sym):
            continue
        ev = evaluate_intraday_entry(entry["candles"], config.INTRADAY_MIN_RR)
        if ev and ev.get("setup_ok"):
            candidates.append({"symbol": sym, "name": sym, "cap_class": entry["cap_class"], **entry["info"], **ev})

    candidates.sort(key=lambda x: -x["rr_available"])

    for cand in candidates:
        if slots <= 0:
            break
        risk_amount = config.CAPITAL * (config.INTRADAY_RISK_PCT / 100)
        risk_per_share = cand["risk_per_share"]
        qty = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        qty = min(qty, int(state["cash"] / cand["price"]))
        if qty < 1:
            continue
        far_target = cand["price"] + risk_per_share * 10
        atr_mult = config.ATR_MULT.get(cand["cap_class"], config.ATR_MULTIPLIER_DEFAULT)
        extra = {
            "initial_sl": cand["initial_sl"],
            "risk_per_share": risk_per_share,
            "stage": 0,
            "partial_booked": False,
            "smart_partial_booked": False,
            "atr_mult": atr_mult,
            "cap_class": cand["cap_class"],
        }
        pos = pf.buy(state, "intraday", cand["symbol"], cand["name"], qty, cand["price"],
                     cand["initial_sl"], far_target, extra=extra)
        if pos:
            send_telegram(intraday_pro_buy_message(pos, cand))
            print("BUY (Intraday PRO):", pos)
            slots -= 1


def main():
    if not market_open():
        print(f"[{now_ist().strftime('%H:%M:%S')}] Market band hai, is run me kuch nahi karna.")
        return

    client = AngelClient()
    client.login()
    token_map = get_token_map()
    universe = build_universe()
    symbols = _resolvable_symbols(universe, token_map)
    print(f"Universe: {len(universe)} stocks total, {len(symbols)} Angel One token ke saath resolve hue.")

    state = pf.load_state()

    print(f"[{now_ist().strftime('%H:%M:%S')}] Swing scan shuru ({len(symbols)} stocks)...")
    scan_swing(client, symbols, state)

    print(f"[{now_ist().strftime('%H:%M:%S')}] Intraday scan shuru ({len(symbols)} stocks)...")
    scan_intraday_pro(client, symbols, state)

    print("Scan complete. Cash:", round(state["cash"]), "Open positions:", len(state["positions"]))


if __name__ == "__main__":
    main()
