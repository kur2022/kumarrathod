import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

LOG_FILE = "signals_log.csv"

def fetch_chartink_support():
    url = "https://chartink.com/screener/stocks-near-support"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "DataTables_Table_0"})
    rows = table.find_all("tr")[1:] if table else []

    support_stocks = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            stock = cols[0].text.strip()
            price = float(cols[1].text.strip().replace(",", ""))
            support_stocks.append((stock, price))
    return support_stocks

def fetch_topstock_resistance():
    url = "https://www.topstockresearch.com/rt/Screener/Technical/PivotPoint/StandardPivotPoint/ListSupportOrResistance"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "tableizer-table"})
    rows = table.find_all("tr")[1:] if table else []

    resistance_stocks = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            stock = cols[0].text.strip()
            try:
                price = float(cols[1].text.strip().replace(",", ""))
                resistance_stocks.append((stock, price))
            except:
                continue
    return resistance_stocks

def calculate_levels(price):
    sl = round(price * 0.95, 2)
    target = round(price * 1.10, 2)
    return sl, target

def save_signals(date, buy_signals, short_signals):
    all_signals = []

    for stock, price in buy_signals:
        sl, target = calculate_levels(price)
        all_signals.append({
            "Date": date, "Stock": stock, "Signal": "Buy",
            "Entry": price, "Stop-Loss": sl, "Target": target
        })

    for stock, price in short_signals:
        sl, target = calculate_levels(price)
        all_signals.append({
            "Date": date, "Stock": stock, "Signal": "Short",
            "Entry": price, "Stop-Loss": sl, "Target": target
        })

    df_new = pd.DataFrame(all_signals)

    if os.path.exists(LOG_FILE):
        df_existing = pd.read_csv(LOG_FILE)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_csv(LOG_FILE, index=False)

def main():
    st.set_page_config(page_title="📅 Daily Screener", layout="wide")
    st.title("📊 Daily Buy & Short Screener with History")

    today = datetime.now().strftime("%d-%b-%Y")

    # Fetch and save today's signals
    with st.spinner("🔍 Fetching today's signals..."):
        buy_signals = fetch_chartink_support()
        short_signals = fetch_topstock_resistance()
        save_signals(today, buy_signals, short_signals)

    # Load all saved signals
    if os.path.exists(LOG_FILE):
        df_all = pd.read_csv(LOG_FILE)
        df_all['Date'] = pd.to_datetime(df_all['Date'], format="%d-%b-%Y")
        df_all.sort_values(by="Date", ascending=False, inplace=True)

        # Select date to view
        unique_dates = df_all['Date'].dt.strftime("%d-%b-%Y").unique()
        selected_date = st.selectbox("📅 Select Date to View Signals", options=unique_dates)

        df_selected = df_all[df_all['Date'].dt.strftime("%d-%b-%Y") == selected_date]

        st.subheader(f"🟢 Buy Signals for {selected_date}")
        st.dataframe(df_selected[df_selected['Signal'] == "Buy"])

        st.subheader(f"🔴 Short Signals for {selected_date}")
        st.dataframe(df_selected[df_selected['Signal'] == "Short"])
    else:
        st.warning("No signal history found yet.")

if __name__ == "__main__":
    main()
