"""Intraday PRO Engine — R-multiple based dynamic trailing (10-rule system).

Ye apne alag loop (intraday_loop) se chalta hai — Swing se independent, aur
zyada frequent (har 1 min) chalta hai taaki fast intraday moves miss na ho.
"""

import time

import config
import portfolio as pf
import yahoo_api
from market_hours import square_off_time, today_str
from notifier import (
    daily_loss_limit_message, intraday_pro_buy_message, partial_exit_message,
    sell_message, send_telegram, smart_exit_message, trail_update_message,
)
from strategy import evaluate_intraday_entry, update_trailing
from universe import build_universe


def todays_intraday_realized_loss(state):
    today = today_str()
    total = 0.0
    for t in state["history"]:
        if t["type"] == "intraday" and str(t.get("sale_date", "")).startswith(today):
            total += t["profit"]
    return -total if total < 0 else 0.0


def scan_intraday(state):
    universe = build_universe()
    symbols = list(universe.items())
    print(f"[Intraday] Universe: {len(symbols)} stocks")

    force_exit = square_off_time()

    candle_cache = {}
    for sym, cap_class in symbols:
        candles = yahoo_api.safe_call(yahoo_api.historical_intraday, sym)
        if candles and len(candles) >= 3:
            candle_cache[sym] = {"candles": candles, "cap_class": cap_class}
        time.sleep(config.SCAN_DELAY_SECONDS)

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
            print("[Intraday] SELL (EOD):", trade)
            continue

        result = update_trailing(pos, candles, config)

        if result["full_exit_reason"]:
            trade = pf.sell(state, pos, result["price"], result["full_exit_reason"])
            send_telegram(sell_message(trade, r_multiple=result["r_multiple"]))
            print("[Intraday] SELL:", trade)
            continue

        if result["smart_exit_now"]:
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            book_qty = max(1, round(pos["qty"] * config.SMART_EXIT_BOOK_PCT))
            trade = pf.partial_sell(state, pos, book_qty, result["price"], "Smart Early Exit")
            if trade:
                pos["smart_partial_booked"] = True
                send_telegram(smart_exit_message(trade, pos, pos["qty"]))
                print("[Intraday] SMART PARTIAL SELL:", trade)
            continue

        if result["partial_exit_now"]:
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            book_qty = max(1, round(pos["qty"] * config.INTRADAY_PARTIAL_BOOK_PCT))
            trade = pf.partial_sell(state, pos, book_qty, result["price"], "Partial Book +3R")
            if trade:
                pos["partial_booked"] = True
                send_telegram(partial_exit_message(trade, pos, pos["qty"]))
                print("[Intraday] PARTIAL SELL:", trade)
            continue

        if result["new_stop"] != pos["stop"] or result["stage"] != pos.get("stage", 0):
            pos["stop"] = result["new_stop"]
            pos["stage"] = result["stage"]
            pf.save_state(state)
            if result["stage"] > 0:
                send_telegram(trail_update_message(pos, result))
                print("[Intraday] TRAIL UPDATE:", pos["symbol"], result)

    if force_exit:
        print("[Intraday] Square-off time — naya trade nahi.")
        return

    loss_so_far = todays_intraday_realized_loss(state)
    loss_limit = config.INTRADAY_CAPITAL * (config.INTRADAY_DAILY_LOSS_LIMIT_PCT / 100)
    if loss_so_far >= loss_limit:
        loss_pct = (loss_so_far / config.INTRADAY_CAPITAL) * 100
        print(f"[Intraday] Daily loss limit hit: -₹{loss_so_far:.0f} ({loss_pct:.1f}%).")
        send_telegram(daily_loss_limit_message(loss_pct))
        return

    open_count = len(pf.open_positions(state, "intraday"))
    slots = config.MAX_INTRADAY_POSITIONS - open_count
    if slots <= 0:
        print("[Intraday] Scan complete (max positions already open).")
        return

    candidates = []
    for sym, entry in candle_cache.items():
        if pf.has_position(state, sym):
            continue
        ev = evaluate_intraday_entry(entry["candles"], config.INTRADAY_MIN_RR)
        if ev and ev.get("setup_ok"):
            candidates.append({"symbol": sym, "name": sym, "cap_class": entry["cap_class"], **ev})

    candidates.sort(key=lambda x: -x["rr_available"])

    for cand in candidates:
        if slots <= 0:
            break
        risk_amount = config.INTRADAY_CAPITAL * (config.INTRADAY_RISK_PCT / 100)
        risk_per_share = cand["risk_per_share"]
        qty = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
        qty = min(
            qty,
            int(state["intraday_cash"] / cand["price"]),
            int(config.MAX_TRADE_AMOUNT / cand["price"]),
        )
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
            print("[Intraday] BUY:", pos)
            slots -= 1

    print("[Intraday] Scan complete.")
