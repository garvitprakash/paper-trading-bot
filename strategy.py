"""Swing aur Intraday ke liye stock scoring/signal logic.

Swing: 50 EMA > 200 EMA (trend) + 20-din breakout + volume >=1.5x avg + RSI 55-70
Intraday: VWAP ke upar + opening-range breakout + volume spike
"""

from indicators import ema, rsi, last_valid, vwap


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


def intraday_score(candles):
    if len(candles) < 3:
        return None
    vw = vwap(candles)
    or_high = max(candles[0]["high"], candles[1]["high"])
    or_low = min(candles[0]["low"], candles[1]["low"])
    ltp = candles[-1]["close"]
    avg_vol = sum(c["volume"] for c in candles[:-1]) / max(1, len(candles) - 1)
    last_vol = candles[-1]["volume"]

    above_vwap = ltp > vw
    orb_breakout = ltp > or_high
    vol_spike = avg_vol > 0 and last_vol > avg_vol * 1.3

    pts = (34 if above_vwap else 0) + (33 if orb_breakout else 0) + (33 if vol_spike else 0)
    return {
        "score": pts, "price": ltp, "vwap": round(vw, 2),
        "or_high": or_high, "or_low": or_low,
        "above_vwap": above_vwap, "orb_breakout": orb_breakout, "vol_spike": vol_spike,
    }
