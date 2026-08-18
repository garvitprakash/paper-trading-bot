"""Telegram par Buy/Sell/Trailing notification bhejta hai — poori detail ke saath."""

import requests

import config


def send_telegram(message):
    if not config.TELEGRAM_BOT_TOKEN or "YOUR_" in config.TELEGRAM_BOT_TOKEN:
        print("[Telegram configure nahi hai, sirf console pe]\n" + message)
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
    except Exception as e:
        print("Telegram message bhejne me error:", e)


def buy_message(pos):
    """Swing ke liye simple buy message (jaisa pehle tha)."""
    return (
        f"🟢 <b>BUY SIGNAL (Paper) — {pos['type'].upper()}</b>\n"
        f"Stock: <b>{pos['name']}</b>\n"
        f"Qty: {pos['qty']}\n"
        f"Price: ₹{pos['entry']:.2f}\n"
        f"🎯 Target: ₹{pos['target']:.2f}\n"
        f"🛑 Stop-Loss: ₹{pos['stop']:.2f}\n"
        f"Amount: ₹{pos['entry'] * pos['qty']:.0f}\n\n"
        f"👉 Agar aap real me bhi lena chahein to yahi Price/SL/Target dekh kar khud order lagayein."
    )


def intraday_pro_buy_message(pos, entry_eval):
    """Intraday PRO ke liye detailed entry message — R:R, risk amount, structure stop sab kuch."""
    rr = entry_eval["rr_available"]
    risk_amount = pos["risk_per_share"] * pos["qty"]
    return (
        f"🟢 <b>BUY (Paper) — INTRADAY PRO</b>\n"
        f"Stock: <b>{pos['name']}</b>\n"
        f"Qty: {pos['qty']}\n"
        f"Entry: ₹{pos['entry']:.2f}\n"
        f"🛑 Initial SL (structure): ₹{pos['stop']:.2f}\n"
        f"📏 Risk/share: ₹{pos['risk_per_share']:.2f} | Risk amount: ₹{risk_amount:.0f}\n"
        f"📈 R:R available: 1:{rr:.1f}\n"
        f"🎯 Resistance (upside ref): ₹{entry_eval['resistance']:.2f}\n"
        f"Amount invested: ₹{pos['entry'] * pos['qty']:.0f}\n\n"
        f"Strategy: 1R tak SL fixed → 1R pe breakeven → 2R pe structure trailing → "
        f"3R pe partial book + profit-maximization mode.\n"
        f"👉 Real order khud lagana ho to yahi Entry/SL dekh kar lagayein."
    )


def trail_update_message(pos, trail_result):
    """Jab SL trail ho (stage badle ya SL upar khisake) tab bhejne wala message."""
    stage_names = {0: "Initial", 1: "Breakeven Protect", 2: "Structure Trailing", 3: "Profit-Max Mode"}
    return (
        f"🔵 <b>TRAILING UPDATE — {pos['name']}</b>\n"
        f"R-Multiple abhi: <b>+{trail_result['r_multiple']}R</b>\n"
        f"Stage: {stage_names.get(trail_result['stage'], trail_result['stage'])}\n"
        f"SL update: ₹{pos['stop']:.2f} → ₹{trail_result['new_stop']:.2f}\n"
        f"Current Price: ₹{trail_result['price']:.2f}"
    )


def partial_exit_message(trade, pos, remaining_qty):
    emoji = "✅" if trade["profit"] >= 0 else "❌"
    sale_price = trade["sale_amount"] / trade["sale_qty"]
    return (
        f"🟡 <b>PARTIAL BOOK (25%) — {pos['name']}</b>\n"
        f"+3R hit — kuch profit lock kar liya, baaki position trail karega.\n"
        f"Sold Qty: {trade['sale_qty']} @ ₹{sale_price:.2f}\n"
        f"{emoji} Locked P&L: ₹{trade['profit']:.0f}\n"
        f"Remaining Qty (still open): {remaining_qty}"
    )


def smart_exit_message(trade, pos, remaining_qty):
    emoji = "✅" if trade["profit"] >= 0 else "❌"
    sale_price = trade["sale_amount"] / trade["sale_qty"]
    return (
        f"⚠️ <b>SMART EARLY EXIT — {pos['name']}</b>\n"
        f"Reason: Volume gir raha hai + reversal candle + VWAP se dur — jaldi profit lock kar liya.\n"
        f"Sold Qty: {trade['sale_qty']} @ ₹{sale_price:.2f}\n"
        f"{emoji} Locked P&L: ₹{trade['profit']:.0f}\n"
        f"Remaining Qty (still open): {remaining_qty}"
    )


def sell_message(trade, r_multiple=None):
    emoji = "✅" if trade["profit"] >= 0 else "❌"
    sale_price = trade["sale_amount"] / trade["sale_qty"]
    r_line = f"\nFinal R-Multiple: +{r_multiple}R" if r_multiple is not None else ""
    return (
        f"🔴 <b>SELL SIGNAL (Paper) — {trade['type'].upper()}</b>\n"
        f"Stock: <b>{trade['name']}</b>\n"
        f"Qty: {trade['sale_qty']}\n"
        f"Sale Price: ₹{sale_price:.2f}\n"
        f"Reason: {trade['reason']}{r_line}\n"
        f"{emoji} P&L: ₹{trade['profit']:.0f}"
    )


def daily_loss_limit_message(loss_pct):
    return (
        f"🚫 <b>Daily Loss Limit Hit</b>\n"
        f"Aaj ka loss capital ka {loss_pct:.1f}% ho gaya hai.\n"
        f"Aaj ke liye naye Intraday trades band kar diye gaye hain. "
        f"Khuli positions normal trailing se manage hoti rahengi."
    )
