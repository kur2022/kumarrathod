import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

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

def main():
    st.set_page_config(page_title="📊 Auto Buy/Short Screener", layout="wide")
    st.title("🧠 Free Technical Screener: Buy & Short Signals")

    with st.spinner("🔍 Fetching signals from Chartink and TopStockResearch..."):
        buy_signals = fetch_chartink_support()
        short_signals = fetch_topstock_resistance()

    st.subheader("📈 Strong Buy Candidates (Near Support)")
    if buy_signals:
        buy_df = pd.DataFrame([
            {"Stock": stock, "Entry": price, "Stop-Loss": calculate_levels(price)[0], "Target": calculate_levels(price)[1]}
            for stock, price in buy_signals
        ])
        st.dataframe(buy_df)
    else:
        st.info("No Buy signals found.")

    st.subheader("📉 Strong Short Candidates (Near Resistance)")
    if short_signals:
        short_df = pd.DataFrame([
            {"Stock": stock, "Entry": price, "Stop-Loss": calculate_levels(price)[0], "Target": calculate_levels(price)[1]}
            for stock, price in short_signals
        ])
        st.dataframe(short_df)
    else:
        st.info("No Short signals found.")

if __name__ == "__main__":
    main()
