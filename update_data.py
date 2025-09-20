from smartapi import SmartConnect
import pyotp
import pandas as pd
import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env (for local testing)
load_dotenv()

# Credentials from environment
client_id = os.getenv("SMARTAPI_CLIENT_ID")
api_key = os.getenv("SMARTAPI_API_KEY")
mpin = os.getenv("SMARTAPI_MPIN")
secret_key = os.getenv("SMARTAPI_SECRET_KEY")

# Generate TOTP using secret key
totp = pyotp.TOTP(secret_key).now()

# Initialize SmartConnect and login
obj = SmartConnect(api_key=api_key)
login_data = obj.generateSession(client_id=client_id, pin=mpin, totp=totp)

# Get access and feed tokens
access_token = login_data['data']['access_token']
feed_token = obj.getfeedToken()

# Define stocks and parameters
stocks = ["RELIANCE", "TCS", "INFY"]
exchange = "NSE"
interval = "ONE_DAY"
from_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d %H:%M')
to_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

final_df = []

for stock in stocks:
    try:
        # Get symbol token
        search_result = obj.searchScrip(exchange=exchange, symbol=stock)
        symboltoken = search_result['data'][0]['token']

        # Fetch historical data
        historic_data = obj.get_historical_data(
            exchange=exchange,
            symboltoken=symboltoken,
            symbol=stock,
            interval=interval,
            fromdate=from_date,
            todate=to_date
        )

        df = pd.DataFrame(historic_data['data'])
        df['Stock Name'] = stock
        df['Avg_Week_Volume'] = df['volume'].rolling(7).mean()
        df['Avg_Month_Volume'] = df['volume'].rolling(30).mean()
        df['Week_Low'] = df['low'].rolling(7).min()
        df['Week_High'] = df['high'].rolling(7).max()
        df['Month_Low'] = df['low'].rolling(30).min()
        df['Month_High'] = df['high'].rolling(30).max()
        df['Signal Type'] = "Breakout"
        final_df.append(df)

    except Exception as e:
        print(f"Error fetching data for {stock}: {e}")

# Save to CSV
result = pd.concat(final_df)
result.to_csv("Data.csv", index=False)
