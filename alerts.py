from SmartApi import SmartConnect
import pyotp
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
CLIENT_CODE = os.getenv("CLIENT_CODE")
PIN = os.getenv("PIN")
TOTP_SECRET = os.getenv("TOTP_SECRET")

def connect_smartapi():
    totp = pyotp.TOTP(TOTP_SECRET).now()
    smartApi = SmartConnect(API_KEY)
    data = smartApi.generateSession(CLIENT_CODE, PIN, totp)
    if not data['status']:
        return None
    return smartApi

def get_live_price(api, symbol, token):
    params = {
        "exchange": "NSE",
        "tradingsymbol": symbol,
        "symboltoken": token
    }
    try:
        quote = api.getQuote(params)
        return quote['data']['ltp']
    except:
        return None
