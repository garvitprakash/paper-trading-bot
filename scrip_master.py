"""Angel One ka scrip master (sabhi stocks ki token list) download aur cache karta hai.

Har stock ko trade karne ke liye uska 'symboltoken' chahiye hota hai — ye file
trading symbol (jaise RELIANCE) ko uske token se map karti hai.
"""

import json
import os

import requests

import config

SCRIP_MASTER_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
CACHE_FILE = os.path.join(config.DATA_DIR, "scrip_master.json")


def load_scrip_master(force_refresh=False):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not force_refresh and os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    resp = requests.get(SCRIP_MASTER_URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
    return data


def build_token_map(scrip_data):
    """Trading symbol (RELIANCE) -> {token, symbol, exch_seg}. Sirf NSE equity (-EQ)."""
    token_map = {}
    for row in scrip_data:
        try:
            if row.get("exch_seg") == "NSE" and row.get("symbol", "").endswith("-EQ"):
                base = row["symbol"].replace("-EQ", "")
                token_map[base] = {
                    "token": row["token"],
                    "symbol": row["symbol"],
                    "exch_seg": "NSE",
                }
        except Exception:
            continue
    return token_map


def get_token_map(force_refresh=False):
    data = load_scrip_master(force_refresh=force_refresh)
    tm = build_token_map(data)
    print(f"Scrip master load hua — {len(tm)} NSE stocks mile.")
    return tm
