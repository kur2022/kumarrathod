import streamlit as st
from smartapi import SmartConnect
import pandas as pd
import time
import threading

# ---- USER CONFIG ----
API_KEY = "lBFbAJX1"
CLIENT_ID = "K98607"
PASSWORD = "2014"
TOTP = "393487"  # If applicable

TOKEN = "26000"  # Example: Nifty index token
EXCHANGE = "NSE" # Example: NSE

# ---- AUTHENTICATION ----
smartApi = SmartConnect(api_key=API_KEY)
login_data = smartApi.generateSession(CLIENT_ID, PASSWORD, TOTP)
authToken = login_data['data']['jwtToken']
feed_token = smartApi.getfeedToken()

# ---- STREAMLIT UI ----
st.title("Angel One Real-Time Tick Updates")
st.write("Streaming live ticks for token: {}".format(TOKEN))

tick_data = st.empty()

# ---- TICK STORAGE ----
latest_tick = {}

def on_tick(tick):
    global latest_tick
    latest_tick = tick

def ws_thread():
    # Subscribe to WebSocket for live ticks
    smartApi.subscribe(
        token=TOKEN,
        exchange=EXCHANGE,
        on_tick=on_tick
    )
    while True:
        time.sleep(1)

# ---- START WEBSOCKET THREAD ----
threading.Thread(target=ws_thread, daemon=True).start()

# ---- UPDATE STREAMLIT UI ----
while True:
    if latest_tick:
        tick_data.write(pd.DataFrame([latest_tick]))
    time.sleep(1)
