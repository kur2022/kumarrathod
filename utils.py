import pandas as pd
import os
import pyotp
from smartapi import SmartConnect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
LOG_FILE = "signals_log.csv"

# 🔐 SmartAPI connection
def connect_smartapi():
    client_id = os.getenv("K98607")
    api_key = os.getenv("lBFbAJX1")
    mpin = os.getenv("2014")
    secret_key = os.getenv("b85f1564-b805-4aa6-86ff-f8d0103d9f18")

    totp = pyotp.TOTP(secret_key).now()
    obj = SmartConnect(api_key=api_key)
    obj.generateSession(client_id=client_id, pin=mpin, totp=totp)

    return obj, obj.getfeedToken()

# 🔍 Token lookup utility
def lookup_token(api, symbol, exchange="NSE"):
    try:
        result = api.searchScrip(exchange=exchange, symbol=symbol)
        return result['data'][0]['token']
    except Exception as e:
        print(f"Token lookup failed for {symbol}: {e}")
        return None

# 📈 Calculate stop-loss and target levels
def calculate_levels(price):
    stop_loss = round(price * 0.95, 2)
    target = round(price * 1.10, 2)
    return stop_loss, target

# 💾 Save signals to CSV
def save_signals(date, buy_signals, short_signals):
    api, _ = connect_smartapi()
    all_signals = []

    for stock, price in buy_signals:
        sl, tgt = calculate_levels(price)
        token = lookup_token(api, f"{stock}-EQ")
        all_signals.append({
            "Date": date,
            "Stock": stock,
            "Signal": "Buy",
            "Entry": price,
            "Stop-Loss": sl,
            "Target": tgt,
            "Token": token
        })

    for stock, price in short_signals:
        sl, tgt = calculate_levels(price)
        token = lookup_token(api, f"{stock}-EQ")
        all_signals.append({
            "Date": date,
            "Stock": stock,
            "Signal": "Short",
            "Entry": price,
            "Stop-Loss": sl,
            "Target": tgt,
            "Token": token
        })

    df_new = pd.DataFrame(all_signals)

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        df_existing = pd.read_csv(LOG_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_csv(LOG_FILE, index=False)
