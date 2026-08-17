"""GitHub Actions ke liye — ye script ek baar chalti hai (login -> scan -> exit).
Continuous loop nahi hai, kyunki GitHub Actions har baar workflow ko fresh
naya run karta hai (jitni der ka schedule set kiya hoga).
"""

from datetime import datetime

import pytz

import config
import portfolio as pf
from angel_api import AngelClient, safe_call
from notifier import buy_message, send_telegram, sell_message
from scrip_master import get_token_map
from strategy import intraday_score, swing_score

IST = pytz.timezone("Asia/Kolkata")


def now_ist():
    return datetime.now(IST)


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


def scan_swing(client, token_map, state):
    results = []
    for sym in config.WATCHLIST:
        info = token_map.get(sym)
        if not info:
            continue
        candles = safe_call(client.historical_daily, info["exch_seg"], info["token"])
        if not candles:
            continue
        s = swing_score(candles)
        if s:
            results.append({"symbol": sym, "name": sym, **s, **info})

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


def scan_intraday(client, token_map, state):
    results = []
    for sym in config.WATCHLIST:
        info = token_map.get(sym)
        if not info:
            continue
        candles = safe_call(client.historical_intraday, info["exch_seg"], info["token"])
        if not candles:
            continue
        s = intraday_score(candles)
        if s:
            results.append({"symbol": sym, "name": sym, **s, **info})

    force_exit = square_off_time()

    for pos in list(state["positions"]):
        if pos["type"] != "intraday":
            continue
        match = next((r for r in results if r["symbol"] == pos["symbol"]), None)
        price = match["price"] if match else pos["entry"]
        reason = None
        if force_exit:
            reason = "Auto Square-Off (EOD)"
        elif price >= pos["target"]:
            reason = "Target Hit"
        elif price <= pos["stop"]:
            reason = "Stop Loss"
        elif match and not match["above_vwap"]:
            reason = "VWAP se neeche"
        if reason:
            trade = pf.sell(state, pos, price, reason)
            send_telegram(sell_message(trade))
            print("SELL (Intraday):", trade)

    if force_exit:
        return

    open_count = len(pf.open_positions(state, "intraday"))
    slots = config.MAX_INTRADAY_POSITIONS - open_count
    if slots > 0:
        candidates = sorted(
            [r for r in results if r["score"] >= config.INTRADAY_SCORE_THRESHOLD and r["above_vwap"] and r["orb_breakout"] and not pf.has_position(state, r["symbol"])],
            key=lambda x: -x["score"],
        )
        for cand in candidates:
            if slots <= 0:
                break
            stop_price = cand["or_low"]
            risk_amount = config.CAPITAL * (config.RISK_PER_TRADE_PCT / 100)
            risk_per_share = max(0.5, cand["price"] - stop_price)
            per_trade_cap = config.CAPITAL / config.MAX_INTRADAY_POSITIONS
            qty = int(risk_amount / risk_per_share)
            qty = min(qty, int(state["cash"] / cand["price"]), int(per_trade_cap / cand["price"]))
            if qty < 1:
                continue
            target_price = cand["price"] * (1 + config.INTRADAY_TARGET_PCT)
            pos = pf.buy(state, "intraday", cand["symbol"], cand["name"], qty, cand["price"], stop_price, target_price)
            if pos:
                send_telegram(buy_message(pos))
                print("BUY (Intraday):", pos)
                slots -= 1


def main():
    if not market_open():
        print(f"[{now_ist().strftime('%H:%M:%S')}] Market band hai, is run me kuch nahi karna.")
        return

    client = AngelClient()
    client.login()
    token_map = get_token_map()
    state = pf.load_state()

    print(f"[{now_ist().strftime('%H:%M:%S')}] Scanning...")
    scan_swing(client, token_map, state)
    scan_intraday(client, token_map, state)
    print("Scan complete. Cash:", round(state["cash"]), "Open positions:", len(state["positions"]))


if __name__ == "__main__":
    main()
