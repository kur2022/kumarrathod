import streamlit as st
import pandas as pd
import requests
from io import StringIO
from gtts import gTTS
import yfinance as yf
import ta
from telegram import Bot

def main():
    # Telegram setup
    bot_token = "7970626014:AAG6QFs0ZWohqkkGaNhJ7P4qkhaJN-UMe74"
    chat_id = "7970626014"
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

    def get_live_ltp(symbol):
        try:
            ticker = yf.Ticker(symbol + ".NS")
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
            else:
                return None
        except Exception as e:
            st.error(f"Live data error for {symbol}: {e}")
            return None

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

    tickers = st.sidebar.text_area("Enter Stock Tickers (comma-separated)", value="RELIANCE,TCS,INFY").split(",")
    selected_indicators = st.sidebar.multiselect(
        "Choose Indicators", ["RSI", "MACD", "EMA", "Bollinger Bands", "VWAP"],
        default=["RSI", "MACD", "EMA"]
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

    st.subheader("📊 Live Market Signals")
    results = []

    for ticker in tickers:
        symbol = ticker.strip()
        ltp = get_live_ltp(symbol)
        if not ltp:
            continue

        stop_loss = round(ltp * 0.90, 2)
        target_price = round(ltp * 1.20, 2)
        signal = []

        dummy_data = pd.DataFrame({'Close': [ltp]*30})
        dummy_data['Volume'] = [100000]*30
        dummy_data['High'] = [ltp*1.01]*30
        dummy_data['Low'] = [ltp*0.99]*30

        if "RSI" in selected_indicators:
            dummy_data['RSI'] = ta.momentum.RSIIndicator(dummy_data['Close']).rsi()
            if dummy_data['RSI'].iloc[-1] < 30:
                signal.append("📈 RSI Buy")
            elif dummy_data['RSI'].iloc[-1] > 70:
                signal.append("📉 RSI Sell")

        if "MACD" in selected_indicators:
            macd = ta.trend.MACD(dummy_data['Close'])
            dummy_data['MACD'] = macd.macd()
            dummy_data['MACD_Signal'] = macd.macd_signal()
            if dummy_data['MACD'].iloc[-1] > dummy_data['MACD_Signal'].iloc[-1]:
                signal.append("📈 MACD Bullish")
            elif dummy_data['MACD'].iloc[-1] < dummy_data['MACD_Signal'].iloc[-1]:
                signal.append("📉 MACD Bearish")

        if "EMA" in selected_indicators:
            ema = ta.trend.EMAIndicator(close=dummy_data['Close'], window=20)
            dummy_data['EMA'] = ema.ema_indicator()
            if ltp > dummy_data['EMA'].iloc[-1]:
                signal.append("📈 EMA Bullish")
            elif ltp < dummy_data['EMA'].iloc[-1]:
                signal.append("📉 EMA Bearish")

        if "Bollinger Bands" in selected_indicators:
            bb = ta.volatility.BollingerBands(close=dummy_data['Close'], window=20, window_dev=2)
            dummy_data['bb_upper'] = bb.bollinger_hband()
            dummy_data['bb_lower'] = bb.bollinger_lband()
            if ltp > dummy_data['bb_upper'].iloc[-1]:
                signal.append("📉 Overbought (BB)")
            elif ltp < dummy_data['bb_lower'].iloc[-1]:
                signal.append("📈 Oversold (BB)")

        if "VWAP" in selected_indicators:
            dummy_data['VWAP'] = (dummy_data['Volume'] * dummy_data['Close']).cumsum() / dummy_data['Volume'].cumsum()
            if ltp > dummy_data['VWAP'].iloc[-1]:
                signal.append("📈 Above VWAP")
            elif ltp < dummy_data['VWAP'].iloc[-1]:
                signal.append("📉 Below VWAP")

        if signal:
            alert_msg = f"{symbol} Signal: {', '.join(signal)} at ₹{ltp}. SL ₹{stop_loss}, Target ₹{target_price}"
            send_voice_alert(alert_msg)
            send_telegram_alert(alert_msg)

        results.append({
            "Ticker": symbol,
            "Price": ltp,
            "Signal": ", ".join(signal),
            "Stop-Loss": stop_loss,
            "Target": target_price
        })

    st.dataframe(pd.DataFrame(results))

# Entry point
if __name__ == "__main__":
    main()
