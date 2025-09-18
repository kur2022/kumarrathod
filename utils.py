import pandas as pd
import os

LOG_FILE = "signals_log.csv"

def calculate_levels(price):
    return round(price * 0.95, 2), round(price * 1.10, 2)

def save_signals(date, buy_signals, short_signals):
    all_signals = []

    for stock, price in buy_signals:
        sl, tgt = calculate_levels(price)
        all_signals.append({
            "Date": date,
            "Stock": stock,
            "Signal": "Buy",
            "Entry": price,
            "Stop-Loss": sl,
            "Target": tgt
        })

    for stock, price in short_signals:
        sl, tgt = calculate_levels(price)
        all_signals.append({
            "Date": date,
            "Stock": stock,
            "Signal": "Short",
            "Entry": price,
            "Stop-Loss": sl,
            "Target": tgt
        })

    df_new = pd.DataFrame(all_signals)

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        df_existing = pd.read_csv(LOG_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new
    df_combined.to_csv(LOG_FILE, index=False)
