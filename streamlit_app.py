import streamlit as st
import pandas as pd
from datetime import datetime
import os

from fetchers import fetch_chartink_support, fetch_topstock_resistance
from alerts import connect_smartapi, get_live_price
from utils import save_signals, calculate_levels, LOG_FILE

def main():
    st.set_page_config(page_title="📅 Daily Screener", layout="wide")
    st.title("📊 Daily Buy & Short Screener with Real-Time Alerts")

    today = datetime.now().strftime("%d-%b-%Y")

    with st.spinner("🔍 Fetching today's signals..."):
        buy_signals = fetch_chartink_support()
        short_signals = fetch_topstock_resistance()
        if buy_signals or short_signals:
            save_signals(today, buy_signals, short_signals)

    if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
        df_all = pd.read_csv(LOG_FILE)
        df_all['Date'] = pd.to_datetime(df_all['Date'], format="%d-%b-%Y")
        df_all.sort_values(by="Date", ascending=False, inplace=True)

        unique_dates = df_all['Date'].dt.strftime("%d-%b-%Y").unique()
        selected_date = st.selectbox("📅 Select Date to View Signals", options=unique_dates)

        df_selected = df_all[df_all['Date'].dt.strftime("%d-%b-%Y") == selected_date]

        st.subheader(f"🟢 Buy Signals for {selected_date}")
        df_buy = df_selected[df_selected['Signal'] == "Buy"]
        st.dataframe(df_buy if not df_buy.empty else pd.DataFrame(columns=df_selected.columns))

        st.subheader(f"🔴 Short Signals for {selected_date}")
        df_short = df_selected[df_selected['Signal'] == "Short"]
        st.dataframe(df_short if not df_short.empty else pd.DataFrame(columns=df_selected.columns))

        st.subheader("⚡ Real-Time Price Alerts (Angel Broking)")
        api = connect_smartapi()
        if api:
            for _, row in df_selected.iterrows():
                symbol = f"{row['Stock']}-EQ"
                token = "2885"  # Replace with actual token lookup
                live_price = get_live_price(api, symbol, token)
                if live_price:
                    if row['Signal'] == "Buy" and live_price > row['Target']:
                        st.success(f"📈 {row['Stock']} crossed target: ₹{live_price}")
                    elif row['Signal'] == "Short" and live_price < row['Stop-Loss']:
                        st.error(f"📉 {row['Stock']} hit stop-loss: ₹{live_price}")
                    else:
                        st.info(f"ℹ️ {row['Stock']} live: ₹{live_price}")
                else:
                    st.warning(f"⚠️ Could not fetch price for {row['Stock']}")
    else:
        st.warning("📭 No signal history found yet. Please run the app again after today's signals are fetched.")

if __name__ == "__main__":
    main()
