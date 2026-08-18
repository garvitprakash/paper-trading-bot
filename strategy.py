"""Swing scoring (unchanged) + Intraday PRO system: R-multiple based dynamic trailing.

Intraday PRO rules (based on user's finalized 10-rule system + ChatGPT trailing detail):
  1. Entry sirf A/A+ setup (VWAP + Opening Range Breakout + Volume Spike) par
  2. Entry ke time kam se kam 1:3 R:R available hona chahiye (warna reject)
  3. Risk per trade = capital ka 0.5%
  4. +1R tak SL fixed; +1R pe SL breakeven ke paas; +2R pe structure (swing-low) trailing
     + VWAP/9-EMA secondary confirmation; +3R pe fixed target hata kar profit-max mode + partial book
  5. Trailing SL kabhi peeche (neeche) nahi jaata — ratchet rule
  6. Cap-size ke hisaab se ATR buffer alag (large 1.5x / mid 1.8x / small 2.0x)
  7. Smart early-exit: profit + volume-decline + VWAP-se-dur + reversal-candle -> jaldi
     20-30% book kar lo, poore trend ke khatam hone ka wait mat karo
"""

from indicators import (
    ema, rsi, last_valid, vwap, atr, recent_swing_low, recent_resistance,
)


def swing_score(candles):
    closes = [c["close"] for c in candles]
    vols = [c["volume"] for c in candles]
    if len(closes) < 210:
        return None

    ema50 = last_valid(ema(closes, 50))
    ema200 = last_valid(ema(closes, 200))
    ema20 = last_valid(ema(closes, 20))
    rsi_val = last_valid(rsi(closes, 14))
    ltp = closes[-1]
    recent_high20 = max(c["high"] for c in candles[-21:-1])
    avg_vol20 = sum(vols[-21:-1]) / 20
    vol_ratio = (vols[-1] / avg_vol20) if avg_vol20 > 0 else 0

    trend_up = ema50 is not None and ema200 is not None and ema50 > ema200
    breakout = ltp > recent_high20

    trend_pts = 25 if trend_up else 0
    breakout_pts = 25 if breakout else 0
    vol_pts = max(0, min(25, (vol_ratio / 1.5) * 25))
    rsi_pts = 0
    if rsi_val is not None:
        if 55 <= rsi_val <= 70:
            rsi_pts = 25
        elif 40 < rsi_val < 80:
            dist = (55 - rsi_val) if rsi_val < 55 else (rsi_val - 70)
            rsi_pts = max(0, 25 - dist * 1.8)

    score = round(trend_pts + breakout_pts + vol_pts + rsi_pts)
    return {
        "score": score, "price": ltp, "ema20": ema20,
        "trend_up": trend_up, "breakout": breakout,
        "vol_ratio": round(vol_ratio, 2), "rsi": round(rsi_val, 1) if rsi_val else None,
    }


def evaluate_intraday_entry(candles, min_rr):
    """A/A+ setup check + 1:3 R:R validation. setup_ok=False lautata hai agar reject ho."""
    if len(candles) < 5:
        return None

    ltp = candles[-1]["close"]
    vw = vwap(candles)
    or_high = max(candles[0]["high"], candles[1]["high"])
    avg_vol = sum(c["volume"] for c in candles[:-1]) / max(1, len(candles) - 1)
    last_vol = candles[-1]["volume"]

    above_vwap = ltp > vw
    orb_breakout = ltp > or_high
    vol_spike = avg_vol > 0 and last_vol > avg_vol * 1.3

    setup_ok = above_vwap and orb_breakout and vol_spike
    if not setup_ok:
        return {"setup_ok": False, "price": ltp, "above_vwap": above_vwap,
                "orb_breakout": orb_breakout, "vol_spike": vol_spike}

    initial_sl = recent_swing_low(candles)
    risk_per_share = ltp - initial_sl
    if risk_per_share <= 0:
        return {"setup_ok": False, "price": ltp, "reason": "invalid structure stop"}

    resistance = recent_resistance(candles)
    potential_upside = resistance - ltp
    rr_available = potential_upside / risk_per_share if risk_per_share > 0 else 0

    if rr_available < min_rr:
        return {"setup_ok": False, "price": ltp, "rr_available": round(rr_available, 2),
                "reason": f"R:R sirf {rr_available:.1f}, min {min_rr} chahiye"}

    atr_val = atr(candles) or risk_per_share

    return {
        "setup_ok": True, "price": ltp, "initial_sl": initial_sl,
        "risk_per_share": risk_per_share, "resistance": resistance,
        "rr_available": round(rr_available, 2), "atr": atr_val,
        "above_vwap": above_vwap, "orb_breakout": orb_breakout, "vol_spike": vol_spike,
    }


def _is_bearish_reversal(candles):
    if len(candles) < 2:
        return False
    prev, cur = candles[-2], candles[-1]
    prev_bullish = prev["close"] > prev["open"]
    cur_bearish = cur["close"] < cur["open"]
    return prev_bullish and cur_bearish


def _volume_declining(candles):
    if len(candles) < 2:
        return False
    return candles[-1]["volume"] < candles[-2]["volume"]


def update_trailing(position, candles, config):
    """Har scan par open intraday-pro position ka R-multiple + trailing SL update karta hai."""
    price = candles[-1]["close"]
    risk = position["risk_per_share"]
    r_multiple = (price - position["entry"]) / risk if risk > 0 else 0

    stage = position.get("stage", 0)
    new_sl = position["stop"]
    partial_exit_now = False
    smart_exit_now = False

    closes = [c["close"] for c in candles]
    vw = vwap(candles)
    ema9 = last_valid(ema(closes, 9))
    atr_val = atr(candles) or risk
    atr_mult = position.get("atr_mult", config.ATR_MULTIPLIER_DEFAULT)

    # ---- Smart early-exit check (1R se 3R ke beech, ek baar hi trigger hota hai) ----
    if (config.SMART_EXIT_MIN_R <= r_multiple < config.SMART_EXIT_MAX_R
            and not position.get("smart_partial_booked", False)):
        dist_from_vwap_pct = ((price - vw) / vw * 100) if vw else 0
        if (_volume_declining(candles) and _is_bearish_reversal(candles)
                and dist_from_vwap_pct > config.SMART_EXIT_VWAP_DIST_PCT):
            smart_exit_now = True

    # Stage 1: +1R -> breakeven ke paas
    if r_multiple >= config.INTRADAY_BREAKEVEN_R and stage < 1:
        candidate = position["entry"] + risk * 0.1
        new_sl = max(new_sl, candidate)
        stage = 1

    # Stage 2: +2R -> structure trailing shuru
    if r_multiple >= config.INTRADAY_STRUCTURE_TRAIL_R and stage < 2:
        stage = 2

    # Stage 2+ me har scan par structure + VWAP/9-EMA confirmation wali trailing (ratchet)
    if stage >= 2:
        swing_low = recent_swing_low(candles)
        structure_stop = swing_low - atr_val * atr_mult

        secondary_candidates = [vw - atr_val * 0.5]
        if position.get("cap_class") == "small" and ema9 is not None:
            secondary_candidates.append(ema9 - atr_val * 0.5)
        secondary_stop = min(secondary_candidates)

        candidate_sl = max(structure_stop, secondary_stop)
        new_sl = max(new_sl, candidate_sl)  # ratchet — kabhi neeche nahi

    # Stage 3: +3R -> fixed target hata do, ek baar partial book karo
    if r_multiple >= config.INTRADAY_PARTIAL_BOOK_R and stage < 3:
        stage = 3
        if not position.get("partial_booked", False):
            partial_exit_now = True

    full_exit_reason = None
    if price <= new_sl:
        full_exit_reason = "Trailing Stop Hit" if stage >= 1 else "Stop Loss"

    return {
        "r_multiple": round(r_multiple, 2),
        "new_stop": new_sl,
        "stage": stage,
        "partial_exit_now": partial_exit_now,
        "smart_exit_now": smart_exit_now,
        "full_exit_reason": full_exit_reason,
        "price": price,
    }
