import requests
from bs4 import BeautifulSoup

def fetch_chartink_support():
    url = "https://chartink.com/screener/stocks-near-support"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"id": "DataTables_Table_0"})
    rows = table.find_all("tr")[1:] if table else []

    support_stocks = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            stock = cols[0].text.strip()
            try:
                price = float(cols[1].text.strip().replace(",", ""))
                support_stocks.append((stock, price))
            except:
                continue
    return support_stocks

def fetch_topstock_resistance():
    url = "https://www.topstockresearch.com/rt/Screener/Technical/PivotPoint/StandardPivotPoint/ListSupportOrResistance"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", {"class": "tableizer-table"})
    rows = table.find_all("tr")[1:] if table else []

    resistance_stocks = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            stock = cols[0].text.strip()
            try:
                price = float(cols[1].text.strip().replace(",", ""))
                resistance_stocks.append((stock, price))
            except:
                continue
    return resistance_stocks
