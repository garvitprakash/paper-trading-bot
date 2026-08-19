"""Swing Trading Engine — 50/200 EMA trend + breakout + volume + RSI.

Ye apne alag loop (swing_loop) se chalta hai, Intraday se bilkul independent —
apna interval (kam frequent, kyunki daily-based strategy hai) apne aap follow
karta hai.
"""

import time

import config
import portfolio as pf
import yahoo_api
from notifier import buy_message, sell_message, send_telegram
from strategy import swing_score
from universe import build_universe


def scan_swing(state):
    universe = build_universe()
    symbols = list(universe.items())
    print(f"[Swing] Universe: {len(symbols)} stocks")

    results = []
    for sym, cap_class in symbols:
        candles = yahoo_api.safe_call(yahoo_api.historical_daily, sym)
        if not candles or len(candles) < 210:
            continue
        s = swing_score(candles)
        if s:
            results.append({"symbol": sym, "name": sym, "cap_class": cap_class, **s})
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
            print("[Swing] SELL:", trade)

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
            risk_amount = config.SWING_CAPITAL * (config.RISK_PER_TRADE_PCT / 100)
            risk_per_share = cand["price"] - stop_price
            per_trade_cap = config.SWING_CAPITAL / config.MAX_SWING_POSITIONS
            qty = int(risk_amount / risk_per_share) if risk_per_share > 0 else 0
            qty = min(
                qty,
                int(state["swing_cash"] / cand["price"]),
                int(per_trade_cap / cand["price"]),
                int(config.MAX_TRADE_AMOUNT / cand["price"]),
            )
            if qty < 1:
                continue
            target_price = cand["price"] * (1 + config.SWING_TARGET_PCT)
            pos = pf.buy(state, "swing", cand["symbol"], cand["name"], qty, cand["price"], stop_price, target_price)
            if pos:
                send_telegram(buy_message(pos))
                print("[Swing] BUY:", pos)
                slots -= 1

    print("[Swing] Scan complete.")
