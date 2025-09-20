import requests
import pandas as pd

# 📊 Chartink Screener: Buy Signals
def fetch_chartink_support():
    url = "https://chartink.com/screener/process"
    payload = {
        "scan_clause": "your_chartink_buy_scan_clause_here"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        data = response.json()
        rows = data.get("data", [])
        return [(row["nsecode"], float(row["close"])) for row in rows]
    except Exception as e:
        print(f"Error fetching Chartink buy signals: {e}")
        return []

# 📉 Topstock Screener: Short Signals
def fetch_topstock_resistance():
    url = "https://topstockresearch.com/api/screener"
    params = {
        "type": "resistance_breakdown",
        "exchange": "NSE"
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        rows = data.get("stocks", [])
        return [(row["symbol"], float(row["price"])) for row in rows]
    except Exception as e:
        print(f"Error fetching Topstock short signals: {e}")
        return []
