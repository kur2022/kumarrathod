import streamlit as st
import pandas as pd
import requests
from io import StringIO
from gtts import gTTS
import yfinance as yf
import ta
from telegram import Bot

def main():
    # ✅ Streamlit UI setup
    st.set_page_config(page_title="📈 Signal Alerts", layout="wide")
    st.title("🧠 Multi-Stock Signal Engine with Alerts")

    # ✅ Telegram setup
    bot_token = "7970626014:AAG6QFs0ZWohqkkGaNhJ7P4qkhaJN-UMe74"
    chat_id = "-1002785266393"
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
            data = ticker.history(period="7d", interval="1d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2), data
            else:
                return None, None
        except Exception as e:
            st.error(f"Live data error for {symbol}: {e}")
            return None, None

    # ✅ Load CSV from GitHub
    csv_url = "https://raw.githubusercontent.com/kur2022/kumarrathod/main/Data.csv"
    response = requests.get(csv_url)
    if response.status_code == 200:
        df_csv = pd.read_csv(StringIO(response.text))
        df_csv.columns = df_csv.columns.str.strip()
    else:
        st.error("❌ Unable to load CSV data.")
        st.stop()

    # ✅ Sidebar inputs
    tickers = st.sidebar.text_area("Enter Stock Tickers (comma-separated)", value="RELIANCE,TCS,INFY").split(",")
    selected_indicators = st.sidebar.multiselect(
        "Choose Indicators", ["RSI", "MACD", "EMA", "VWAP", "Bollinger Bands", "Supertrend", "Breakouts"],
        default=["RSI", "MACD", "EMA", "Breakouts"]
    )

    # ✅ CSV-based signals
    if 'Volume' in df_csv.columns and 'Avg_Week_Volume' in df_csv.columns:
        volume_boost = df_csv['Volume'] > df_csv['Avg_Week_Volume']
        volume_drop = df_csv['Volume'] < df_csv['Avg_Week_Volume']
    else:
        volume_boost = volume_drop = pd.Series([False]*len(df_csv))

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

    # ✅ Display CSV signals
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

    # ✅ Live signals
    st.subheader("📊 Live Market Signals")
    results = []

    for ticker in tickers:
        symbol = ticker.strip()
        ltp, data = get_live_ltp(symbol)
        if not ltp or data is None:
            continue

        signal = []
        stop_loss = round(ltp * 0.90, 2)
        target_price = round(ltp * 1.20, 2)

        # Indicators
        if "RSI" in selected_indicators:
            rsi = ta.momentum.RSIIndicator(data['Close']).rsi().iloc[-1]
            signal.append("Buy" if rsi < 30 else "Short" if rsi > 70 else "Neutral")

        if "MACD" in selected_indicators:
            macd = ta.trend.MACD(data['Close'])
            macd_val = macd.macd().iloc[-1]
            macd_sig = macd.macd_signal().iloc[-1]
            signal.append("Buy" if macd_val > macd_sig else "Short" if macd_val < macd_sig else "Neutral")

        if "EMA" in selected_indicators:
            ema = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator().iloc[-1]
            signal.append("Buy" if ltp > ema else "Short" if ltp < ema else "Neutral")

        if "VWAP" in selected_indicators:
            vwap = (data['Volume'] * data['Close']).cumsum() / data['Volume'].cumsum()
            signal.append("Buy" if ltp > vwap.iloc[-1] else "Short")

        if "Bollinger Bands" in selected_indicators:
            bb = ta.volatility.BollingerBands(data['Close'])
            upper = bb.bollinger_hband().iloc[-1]
            lower = bb.bollinger_lband().iloc[-1]
            signal.append("Buy" if ltp < lower else "Short" if ltp > upper else "Neutral")

        if "Supertrend" in selected_indicators:
            hl2 = (data['High'] + data['Low']) / 2
            atr = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range()
            upperband = hl2 + (3 * atr)
            lowerband = hl2 - (3 * atr)
            direction = "Bullish" if ltp > upperband.iloc[-2] else "Bearish" if ltp < lowerband.iloc[-2] else "Neutral"
            signal.append("Buy" if direction == "Bullish" else "Short" if direction == "Bearish" else "Neutral")

        if "Breakouts" in selected_indicators:
            week_high = data['High'].rolling(window=7).max().iloc[-2]
            month_high = data['High'].rolling(window=30).max().iloc[-2]
            signal.append("Buy" if ltp > week_high else "Neutral")
            signal.append("Buy" if ltp > month_high else "Neutral")

        label = ", ".join(signal)
        results.append({
            "Ticker": symbol,
            "Price": ltp,
            "Signal Labels": label,
            "Stop-Loss": stop_loss,
            "Target": target_price
        })

        # Send alerts for strong Buy or Short signals
        if "Buy" in label or "Short" in label:
            alert_msg = f"{symbol}: {label} at ₹{ltp} | SL ₹{stop_loss} | Target ₹{target_price}"
            send_telegram_alert(alert_msg)
            send_voice_alert(alert_msg)

    # ✅ Display live signal table
    if results:
        st.dataframe(pd.DataFrame(results))
    else:
        st.info("📭 No live signals generated. Try different tickers or indicators.")

# ✅ Required to run the app
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ App crashed: {e}")
