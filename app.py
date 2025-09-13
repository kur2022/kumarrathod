import streamlit as st
import pandas as pd
import yfinance as yf
from smartapi import SmartConnect
import plotly.graph_objects as go
import ta
from gtts import gTTS
from io import StringIO
import requests
from telegram import Bot

# Telegram setup
bot_token = "7970626014:AAG6QFs0ZWohqkkGaNhJ7P4qkhaJN-UMe74"
chat_id = "YOUR_CHAT_ID"
bot = Bot(token=bot_token)

def send_telegram_alert(message):
    bot.send_message(chat_id=chat_id, text=message)

def send_voice_alert(text):
    tts = gTTS(text=text, lang='en')
    tts.save("alert.mp3")
    st.audio("alert.mp3")
    url = f"https://api.telegram.org/bot{bot_token}/sendAudio"
    files = {'audio': open("alert.mp3", 'rb')}
    data = {'chat_id': chat_id, 'caption': text}
    requests.post(url, files=files, data=data)

# Load CSV from GitHub
csv_url = "https://raw.githubusercontent.com/kur2022/kumarrathod/main/Data.csv"
response = requests.get(csv_url)
if response.status_code == 200:
    df_csv = pd.read_csv(StringIO(response.text))
else:
    st.error("❌ Unable to load CSV data.")
    st.stop()

# Streamlit UI
st.set_page_config(page_title="📈 Signal Engine", layout="wide")
st.title("🧠 Multi-Stock Signal Engine with Alerts")

# Sidebar inputs
tickers = st.sidebar.text_area("Enter Stock Tickers (comma-separated)", value="RELIANCE.NS,TCS.NS,INFY.NS").split(",")
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m"], index=1)
days = st.sidebar.slider("Days of Data", 1, 5, 2)
selected_indicators = st.sidebar.multiselect(
    "Choose Indicators", ["RSI", "MACD", "EMA", "Bollinger Bands", "VWAP"], default=["RSI", "MACD"]
)

# CSV-based signals
volume_boost = df_csv['Volume'] > df_csv['Avg_Week_Volume']
volume_drop = df_csv['Volume'] < df_csv['Avg_Week_Volume']
near_lows = (
    (df_csv['Price'] - df_csv['Day_Low']) / df_csv['Day_Low'] <= 0.03 |
    (df_csv['Price'] - df_csv['Week_Low']) / df_csv['Week_Low'] <= 0.03 |
    (df_csv['Price'] - df_csv['Month_Low']) / df_csv['Month_Low'] <= 0.03
)
near_highs = (
    (df_csv['Day_High'] - df_csv['Price']) / df_csv['Day_High'] <= 0.03 |
    (df_csv['Week_High'] - df_csv['Price']) / df_csv['Week_High'] <= 0.03 |
    (df_csv['Month_High'] - df_csv['Price']) / df_csv['Month_High'] <= 0.03
)

strong_price_action = (
    (df_csv['Signal Type'].str.lower().isin(['breakout', 'high', 'reversal'])) &
    volume_boost & near_lows
)
weak_price_action = (
    (df_csv['Signal Type'].str.lower().isin(['low', 'sell', 'breakdown'])) &
    volume_drop & near_highs
)

upside_csv = df_csv[strong_price_action].copy()
downside_csv = df_csv[weak_price_action].copy()

for frame in [upside_csv, downside_csv]:
    frame['Stop-Loss'] = (frame['Price'] * 0.90).round(2)
    frame['Target'] = (frame['Price'] * 1.20).round(2)

# Display CSV signals
st.subheader("📁 Signals from GitHub CSV")
col1, col2 = st.columns(2)

with col1:
    st.markdown("🚀 Upside Signals")
    st.dataframe(upside_csv[['Stock Name', 'Price', 'Volume', 'Stop-Loss', 'Target']])
    if not upside_csv.empty:
        top = upside_csv.iloc[0]
        msg = f"{top['Stock Name']} shows strong upside at ₹{top['Price']}. SL ₹{top['Stop-Loss']}, Target ₹{top['Target']}"
        send_voice_alert(msg)
        send_telegram_alert(f"🚀 {msg}")

with col2:
    st.markdown("📉 Downside Signals")
    st.dataframe(downside_csv[['Stock Name', 'Price', 'Volume', 'Stop-Loss', 'Target']])
    if not downside_csv.empty:
        top = downside_csv.iloc[0]
        msg = f"{top['Stock Name']} shows weakness at ₹{top['Price']}. SL ₹{top['Stop-Loss']}, Target ₹{top['Target']}"
        send_voice_alert(msg)
        send_telegram_alert(f"📉 {msg}")

# Live indicator-based scanning
results = []
for ticker in tickers:
    data = yf.download(ticker.strip(), period=f"{days}d", interval=interval)
    if data.empty:
        continue
    data.dropna(inplace=True)
    latest = data.iloc[-1]
    entry_price = latest['Close']
    stop_loss = round(entry_price * 0.90, 2)
    target_price = round(entry_price * 1.20, 2)
    signal = []

    if "RSI" in selected_indicators:
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        if data['RSI'].iloc[-1] < 30:
            signal.append("📈 RSI Buy")
        elif data['RSI'].iloc[-1] > 70:
            signal.append("📉 RSI Sell")

    if "MACD" in selected_indicators:
        macd = ta.trend.MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_Signal'] = macd.macd_signal()
        if data['MACD'].iloc[-1] > data['MACD_Signal'].iloc[-1]:
            signal.append("📈 MACD Bullish")
        elif data['MACD'].iloc[-1] < data['MACD_Signal'].iloc[-1]:
            signal.append("📉 MACD Bearish")

    if "EMA" in selected_indicators:
        data['EMA_12'] = ta.trend.EMAIndicator(data['Close'], window=12).ema_indicator()
        data['EMA_26'] = ta.trend.EMAIndicator(data['Close'], window=26).ema_indicator()
        if data['EMA_12'].iloc[-1] > data['EMA_26'].iloc[-1]:
            signal.append("📈 EMA Bullish")
        elif data['EMA_12'].iloc[-1] < data['EMA_26'].iloc[-1]:
            signal.append("📉 EMA Bearish")

    if "Bollinger Bands" in selected_indicators:
        bb = ta.volatility.BollingerBands(data['Close'])
        data['BB_High'] = bb.bollinger_hband()
        data['BB_Low'] = bb.bollinger_lband()
        if data['Close'].iloc[-1] > data['BB_High'].iloc[-1]:
            signal.append("📈 BB Breakout")
        elif data['Close'].iloc[-1] < data['BB_Low'].iloc[-1]:
            signal.append("📉 BB Breakdown")

    if "VWAP" in selected_indicators:
        data['VWAP'] = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
        if data['Close'].iloc[-1] > data['VWAP'].iloc[-1]:
            signal.append("📈 Above VWAP")
        else:
            signal.append("📉 Below VWAP")

    if signal:
        alert_msg = f"{ticker.strip()} Signal: {', '.join(signal)} at ₹{entry_price}. SL ₹{stop_loss}, Target ₹{target_price}"
        send_voice_alert(alert_msg)
        send_telegram_alert(alert_msg)

    results.append({
        "Ticker": ticker.strip(),
        "Price": entry_price,
        "Signal": ", ".join(signal),
        "Stop-Loss": stop_loss,
        "Target": target_price
    })

# Display live signals
st.subheader("📊 Live Market Signals")
st.dataframe(pd.DataFrame(results))

# Chart for selected ticker
st.subheader("📈 Chart for Selected Ticker")
selected_ticker = st.selectbox("Choose ticker to view chart", tickers)
chart_data = yf.download(selected_ticker.strip(), period=f"{days}d", interval=interval)
chart_data.drop
