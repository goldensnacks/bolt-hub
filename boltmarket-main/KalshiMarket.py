from KalshiAPIStarterCode.KalshiClientsBaseV2 import ExchangeClient
import pandas as pd
import datetime
import xlwings as xw
from datetime import datetime, date, timedelta
import time
"""import needed tradables"""
from Tradables import BinaryOption, OneTouch, Underlier
from PricingHelperFns import convert_kalshi_date_to_datetime

import numpy as np

#from TDAPI.tradables import VanillaOption, Portfolio, Range
prod_email = "jacobreedijk@gmail.com" # change these to be your personal credentials
prod_password = "DJDSOLwr13?"
prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"
exchange_client = ExchangeClient(exchange_api_base=prod_api_base, email = prod_email, password = prod_password)

def get_markets(client = exchange_client):
    config = { 'limit':1000,
               'cursor':None, # passing in the cursor from the previous get_markets call
               'event_ticker': None,
               'series_ticker': None,
               'max_close_ts': None, # pass in unix_ts
               'min_close_ts': None, # pass in unix_ts
               'status': 'open', # open, closed, settled
                'tickers':None
            }
    markets = client.get_markets(**config)
    return markets

def is_one_touch(market):
    return market['title'].lower().find('minimum') != -1 or market['title'].lower().find('maximum') != -1
def display_markets(has_cap_strike = False):
    markets = pd.DataFrame(get_markets()['markets'])

    """just markets with eurusd in ticker"""
    markets = markets[markets['ticker'].str.contains('EURUSD')]
    columns = [ "ticker",    "event_ticker", "title", 'open_interest',
                "open_time", "close_time", "expiration_time",	"yes_bid",
                "yes_ask",	 "last_price",   "strike_type"	 ,   "floor_strike",	"cap_strike",	"custom_strike"]
    """just columns we want"""
    markets = markets[columns]

    """add one touch column"""
    markets['one_touch'] = markets.apply(is_one_touch, axis = 1)

    """make underlier - same for all markets"""
    underlier = Underlier('EURUSD', 1.0694, .06)

    """populate strike for markets without both cap and floor"""
    markets['strike'] = markets.apply(lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)

    """make product for each market"""
    products = markets.apply(lambda x: OneTouch(underlier, x.strike, convert_kalshi_date_to_datetime(x.expiration_time))
                                    if x.one_touch else
                                       BinaryOption(underlier, x.floor_strike, x.cap_strike,
                                                    convert_kalshi_date_to_datetime(x.expiration_time)),
                             axis = 1)

    """add prices for each market"""
    markets['price'] = products.apply(lambda x: x.price())

    """add alphas for each market"""
    markets['alpha_long'] =  markets['price'] - markets['bid']
    markets['alpha_short'] = markets['bid'] -  markets['price']

    """add delta for each market"""
    markets['delta'] = products.apply(lambda x: x.delta())

    """add vegas for each market"""
    markets['vega'] = products.apply(lambda x: x.vega())

    wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
    sht = wb.sheets[0]
    sht.range('A1').value = markets

mkts = display_markets()
print(mkts)


