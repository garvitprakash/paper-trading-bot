"""Technical indicator calculations: EMA, RSI, VWAP."""


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
