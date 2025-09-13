import streamlit as st
import pandas as pd
from gtts import gTTS

# Load CSV from GitHub
csv_url = "https://raw.githubusercontent.com/kur2022/kumarrathod/main/data.csv"
df = pd.read_csv(csv_url)

st.set_page_config(page_title="Intraday Stock Signals", layout="wide")
st.title("📊 Intraday Stock Dashboard")

# Layout: 3 columns
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📉 Day's Low")
    st.dataframe(df[df['Signal Type'].str.lower() == 'low'])

with col2:
    st.subheader("📈 Day's High")
    st.dataframe(df[df['Signal Type'].str.lower() == 'high'])

with col3:
    st.subheader("🚀 Breakout + High Volume")
    breakout = df[(df['Signal Type'].str.lower() == 'breakout') & (df['Volume'] > 100000)]
    st.dataframe(breakout)

    # Voice alert for first breakout stock
    if not breakout.empty:
        message = f"Strong Buy Signal for {breakout.iloc[0]['Stock Name']} at ₹{breakout.iloc[0]['Price']}"
        tts = gTTS(text=message, lang='en')
        tts.save("alert.mp3")
        audio_file = open("alert.mp3", "rb")
        st.audio(audio_file.read(), format="audio/mp3")
