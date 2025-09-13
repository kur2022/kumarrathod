import yfinance as yf
import pandas as pd

tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS"]
final_df = []

for ticker in tickers:
    df = yf.download(ticker, period="2mo", interval="1d")
    df['Stock Name'] = ticker
    df['Avg_Week_Volume'] = df['Volume'].rolling(7).mean()
    df['Avg_Month_Volume'] = df['Volume'].rolling(30).mean()
    df['Week_Low'] = df['Low'].rolling(7).min()
    df['Week_High'] = df['High'].rolling(7).max()
    df['Month_Low'] = df['Low'].rolling(30).min()
    df['Month_High'] = df['High'].rolling(30).max()
    df['Signal Type'] = "Breakout"  # You can add logic here
    final_df.append(df)

result = pd.concat(final_df)
result.to_csv("Data.csv")
