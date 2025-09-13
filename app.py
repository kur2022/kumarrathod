import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import ta
from gtts import gTTS
from io import StringIO
import requests
from telegram import Bot

# Telegram credentials (store securely in st.secrets for production)
bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
chat_id = "YOUR_CHAT_ID"
bot = Bot(token=bot_token)

def send_telegram_alert(message):
    bot.send_message(chat_id=chat_id, text=message)

# Load CSV from GitHub
csv_url = "https://raw.githubusercontent.com/kur2022/kumarrathod/main/Data.csv"
response = requests.get(csv_url)
if response.status_code == 200:
    df = pd.read_csv(StringIO(response.text))
else:
    st.error("❌ Unable to load data. Check your CSV link or network.")
    st.stop()

st.set_page_config(page_title="📈 Market Signal Engine", layout="wide")
st.title("🧠 Serious Signal Engine for Upside & Downside Detection")

# Signal thresholds
volume_boost = df['Volume'] > df['Avg_Week_Volume']
volume_drop = df['Volume'] < df['Avg_Week_Volume']
near_lows = (
    (df['Price'] - df['Day_Low']) / df['Day_Low'] <= 0.03 |
    (df['Price'] - df['Week_Low']) / df['Week_Low'] <= 0.03 |
    (df['Price'] - df['Month_Low']) / df['Month_Low'] <= 0.03
)
near_highs = (
    (df['Day_High'] - df['Price']) / df['Day_High'] <= 0.03 |
    (df['Week_High'] - df['Price']) / df['Week_High'] <= 0.03 |
    (df['Month_High'] - df['Price']) / df['Month_High'] <= 0.03
)

# Signal logic
strong_price_action = (
    (df['Signal Type'].str.lower().isin(['breakout', 'high', 'reversal'])) &
    volume_boost & near_lows
)
weak_price_action = (
    (df['Signal Type'].str.lower().isin(['low', 'sell', 'breakdown'])) &
    volume_drop & near_highs
)

upside = df[strong_price_action]
downside = df[weak_price_action]

# Display signals
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Strong Upside Signals")
    st.dataframe(upside[['Stock Name', 'Price', 'Volume', 'Day_Low', 'Week_Low', 'Month_Low']])
    if not upside.empty:
        top = upside.iloc[0]
        msg = f"{top['Stock Name']} shows strong upside at ₹{top['Price']}. Volume: {top['Volume']}"
        tts = gTTS(text=msg, lang='en')
        tts.save("upside.mp3")
        st.audio("upside.mp3")
        send_telegram_alert(f"🚀 {msg}")

with col2:
    st.subheader("📉 Downside Weakness Signals")
    st.dataframe(downside[['Stock Name', 'Price', 'Volume', 'Day_High', 'Week_High', 'Month_High']])
    if not downside.empty:
        top = downside.iloc[0]
        msg = f"{top['Stock Name']} shows weakness at ₹{top['Price']}. Volume: {top['Volume']}"
        tts = gTTS(text=msg, lang='en')
        tts.save("downside.mp3")
        st.audio("downside.mp3")
        send_telegram_alert(f"📉 {msg}")

# Candlestick + RSI/MACD
st.subheader("📊 Candlestick Chart with RSI & MACD")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., RELIANCE.NS)", value="RELIANCE.NS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2025-08-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2025-09-13"))

data = yf.download(ticker, start=start_date, end=end_date)
data.dropna(inplace=True)
data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
macd = ta.trend.MACD(data['Close'])
data['MACD'] = macd.macd()
data['MACD_Signal'] = macd.macd_signal()

fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close']
)])
fig.update_layout(title=f"{ticker} Candlestick Chart", xaxis_title="Date", yaxis_title="Price")
st.plotly_chart(fig)

st.line_chart(data[['RSI', 'MACD', 'MACD_Signal']])
