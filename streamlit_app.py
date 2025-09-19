import streamlit as st
import pandas as pd
from datetime import datetime
import os
from smartapi import SmartConnect
from smartapi import SmartWebSocket
from utils import connect_smartapi, get_live_price
from fetchers import fetch_chartink_support, fetch_topstock_resistance
from utils import save_signals, calculate_levels, LOG_FILE

# Store ticks in session state
if "tick_data" not in st.session_state:
    st.session_state.tick_data = []

def on_tick(tick_data):
    tick = tick_data.get("data", [])[0]
    tick_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.tick_data.append({
        "Time": tick_time,
        "Token": tick["token"],
        "Price": tick["ltp"],
        "Volume": tick["volume"]
    })

def on_connect(ws):
    tokens = [str(row["Token"]) for _, row in st.session_state.df_selected.iterrows() if "Token" in row]
    subscriptions = [{"exchange": "NSE", "token": token} for token in tokens]
    ws.subscribe(subscriptions)

def on_close(ws):
    print("WebSocket closed")

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
        st.session_state.df_selected = df_selected

        st.subheader(f"🟢 Buy Signals for {selected_date}")
        df_buy = df_selected[df_selected['Signal'] == "Buy"]
        st.dataframe(df_buy if not df_buy.empty else pd.DataFrame(columns=df_selected.columns))

        st.subheader(f"🔴 Short Signals for {selected_date}")
        df_short = df_selected[df_selected['Signal'] == "Short"]
        st.dataframe(df_short if not df_short.empty else pd.DataFrame(columns=df_selected.columns))

        st.subheader("⚡ Real-Time Price Alerts (Angel Broking)")
        api, feed_token = connect_smartapi()
        if api:
            for _, row in df_selected.iterrows():
                symbol = f"{row['Stock']}-EQ"
                token = row.get("Token", "2885")  # Replace with actual token lookup
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

        st.subheader("📡 Tick-by-Tick Live Feed")
        if st.button("Start Tick Streaming"):
            sws = SmartWebSocket(feed_token, api.client_code, api.api_key)
            sws.on_ticks = on_tick
            sws.on_connect = on_connect
            sws.on_close = on_close
            sws.connect()

        if st.session_state.tick_data:
            df_ticks = pd.DataFrame(st.session_state.tick_data)
            st.dataframe(df_ticks.tail(10), use_container_width=True)
    else:
        st.warning("📭 No signal history found yet. Please run the app again after today's signals are fetched.")

if __name__ == "__main__":
    main()
