"""Technical indicator calculations: EMA, RSI, VWAP, ATR, swing structure."""


def ema(values, period):
    if len(values) < period:
        return [None] * len(values)
    k = 2 / (period + 1)
    out = [None] * len(values)
    seed = sum(values[:period]) / period
    out[period - 1] = seed
    prev = seed
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def rsi(values, period=14):
    n = len(values)
    out = [None] * n
    if n <= period:
        return out
    gain = loss = 0.0
    for i in range(1, period + 1):
        d = values[i] - values[i - 1]
        if d >= 0:
            gain += d
        else:
            loss -= d
    avg_gain = gain / period
    avg_loss = loss / period
    out[period] = 100 - 100 / (1 + (100 if avg_loss == 0 else avg_gain / avg_loss))
    for i in range(period + 1, n):
        d = values[i] - values[i - 1]
        g = d if d > 0 else 0
        l = -d if d < 0 else 0
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
        rs = 100 if avg_loss == 0 else avg_gain / avg_loss
        out[i] = 100 - 100 / (1 + rs)
    return out


def last_valid(arr):
    for v in reversed(arr):
        if v is not None:
            return v
    return None


def vwap(candles):
    cum_pv = cum_v = 0.0
    for c in candles:
        typical = (c["high"] + c["low"] + c["close"]) / 3
        cum_pv += typical * c["volume"]
        cum_v += c["volume"]
    return cum_pv / cum_v if cum_v > 0 else candles[-1]["close"]


def atr(candles, period=14):
    """Average True Range — volatility measure, candles ki list (dict: high/low/close)."""
    if len(candles) < 2:
        return None
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["high"], candles[i]["low"], candles[i - 1]["close"]
        tr = max(h - l, abs(h - pc), abs(l - pc))
        trs.append(tr)
    if len(trs) < period:
        # kam data ho to jitna hai usi ka average de do
        return sum(trs) / len(trs) if trs else None
    atr_val = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr_val = (atr_val * (period - 1) + trs[i]) / period
    return atr_val


def recent_swing_low(candles, lookback=6):
    """Pichle N candles (current candle chhodkar) ka sabse neecha low — 'structure' stop ke liye."""
    window = candles[-lookback - 1:-1] if len(candles) > lookback else candles[:-1]
    if not window:
        return candles[-1]["low"]
    return min(c["low"] for c in window)


def recent_swing_high(candles, lookback=6):
    window = candles[-lookback - 1:-1] if len(candles) > lookback else candles[:-1]
    if not window:
        return candles[-1]["high"]
    return max(c["high"] for c in window)


def recent_resistance(candles, lookback=20):
    """Pichle N candles ka sabse upar high — 'kitna upside available hai' check karne ke liye."""
    window = candles[-lookback - 1:-1] if len(candles) > lookback else candles[:-1]
    if not window:
        return candles[-1]["high"]
    return max(c["high"] for c in window)
