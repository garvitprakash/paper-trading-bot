"""Trade report CSV banata hai. Chalane ka tarika: python report.py"""

import csv
from datetime import datetime

import portfolio as pf


def export_csv(filename=None):
    state = pf.load_state()
    filename = filename or f"trade_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Type", "Stock", "Purchase Date", "Qty", "Purchase Amount",
            "Sale Date", "Sale Qty", "Sale Amount", "Profit", "Reason",
        ])
        for t in state["history"]:
            writer.writerow([
                t["type"], t["name"], t["purchase_date"], t["qty"], round(t["purchase_amount"]),
                t["sale_date"], t["sale_qty"], round(t["sale_amount"]), round(t["profit"]), t["reason"],
            ])
    print(f"Report saved: {filename}")
    print(f"Total closed trades: {len(state['history'])}")
    print(f"Open positions: {len(state['positions'])}")
    print(f"Available cash: ₹{round(state['cash'])}")


if __name__ == "__main__":
    export_csv()
