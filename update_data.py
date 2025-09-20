from smartapi import SmartConnect
import pandas as pd
import datetime

# Replace with your credentials
client_id = "your_client_id"
api_key = "your_api_key"
access_token = "your_access_token"

# Initialize SmartAPI
obj = SmartConnect(api_key=api_key)
obj.set_access_token(access_token)

# Define stocks and parameters
stocks = ["RELIANCE", "TCS", "INFY"]
exchange = "NSE"
interval = "ONE_DAY"
duration = "2M"

final_df = []

for stock in stocks:
    try:
        historic_data = obj.get_historical_data(
            exchange=exchange,
            symboltoken="",  # You need to fetch this using obj.searchScrip()
            symbol=stock,
            interval=interval,
            fromdate=(datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d %H:%M'),
            todate=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
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

result = pd.concat(final_df)
result.to_csv("Data.csv", index=False)
