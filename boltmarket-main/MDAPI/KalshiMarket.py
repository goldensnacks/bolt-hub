from KalshiAPIStarterCode.KalshiClientsBaseV2 import ExchangeClient
import pandas as pd
import datetime
import xlwings as xw

prod_email = "jacobreedijk@gmail.com" # change these to be your personal credentials
prod_password = "DJDSOLwr69?"
prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"
exchange_client = ExchangeClient(exchange_api_base=prod_api_base, email = prod_email, password = prod_password)

def get_markets(client = exchange_client):
    config = { 'limit':100,
               'cursor':None, # passing in the cursor from the previous get_markets call
               'event_ticker': None,
               'series_ticker': 'INXY-23DEC29',
               'max_close_ts': None, # pass in unix_ts
               'min_close_ts': None, # pass in unix_ts
               'status': None,
                'tickers':None
            }
    markets = client.get_markets(**config)

    return markets

def display_markets():
    markets = pd.DataFrame(get_markets()['markets'])
    wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
    sht = wb.sheets[0]
    sht.range('A1').value = markets

mkts = display_markets()
print(mkts)