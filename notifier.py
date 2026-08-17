"""Telegram par Buy/Sell notification bhejta hai — Stop-Loss aur Target ke saath."""

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


def sell_message(trade):
    emoji = "✅" if trade["profit"] >= 0 else "❌"
    sale_price = trade["sale_amount"] / trade["sale_qty"]
    return (
        f"🔴 <b>SELL SIGNAL (Paper) — {trade['type'].upper()}</b>\n"
        f"Stock: <b>{trade['name']}</b>\n"
        f"Qty: {trade['sale_qty']}\n"
        f"Sale Price: ₹{sale_price:.2f}\n"
        f"Reason: {trade['reason']}\n"
        f"{emoji} P&L: ₹{trade['profit']:.0f}"
    )
