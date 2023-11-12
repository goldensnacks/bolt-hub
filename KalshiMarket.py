from kalshi.KalshiInterface import ExchangeClient
import pandas as pd
import datetime
import xlwings as xw
from datetime import datetime

"""import needed tradables"""
from tradables import BinaryOption, OneTouch
from PricingHelperFns import convert_kalshi_date_to_datetime
import pickle
import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '')))

from securities import get_security

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
def display_markets(underliers=[]):


    """snap underlier securities"""

    markets = pd.DataFrame(get_markets()['markets'])

    """just markets with eurusd in ticker"""
    markets = markets[markets['ticker'].str.contains('EURUSD')]
    columns = [ "ticker",    "event_ticker", "title", 'open_interest',
                "open_time", "close_time","yes_bid",
                "yes_ask",	 "last_price",   "strike_type"	 ,   "floor_strike",	"cap_strike",	"custom_strike"]
    """just columns we want"""
    markets = markets[columns]

    """add expiration time column"""
    markets['expiration_time'] = markets.apply(lambda x: x.close_time, axis = 1)

    markets['underlier'] = [get_security(underlier) for underlier in underliers]

    """add hours to expiry"""
    markets['hours_to_expiry'] = markets.apply(lambda x: (convert_kalshi_date_to_datetime(x.expiration_time) -
                                                          datetime.utcnow()).total_seconds()/3600, axis = 1)
    """add one touch column"""
    markets['one_touch'] = markets.apply(is_one_touch, axis = 1)

    """make underlier - same for all markets"""
    with open('securities/EURUSD.pkl', 'rb') as f:
        underlier = pickle.load(f)

    """populate strike for markets without both cap and floor"""
    markets['strike'] = markets.apply(lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)

    """make product for each market"""
    products = markets.apply(lambda x: OneTouch(x.underlier, x.strike, convert_kalshi_date_to_datetime(x.expiration_time))
                                    if x.one_touch else
                                       BinaryOption(x.underlier, x.floor_strike, x.cap_strike,
                                                    convert_kalshi_date_to_datetime(x.expiration_time)),
                             axis = 1)

    """add prices for each market"""
    markets['price'] = 100*products.apply(lambda x: x.price())

    """add alphas for each market"""
    markets['alpha_long'] =  markets['price'] - markets['yes_ask']
    markets['alpha_short'] = markets['yes_bid'] -  markets['price']

    """display underlier pricer for each market"""
    markets['underlying_px'] = products.apply(lambda x: x.underlying_price())

    """add risks for each market"""
    #markets['delta'] = products.apply(lambda x: x.delta())

    #markets['vega'] = products.apply(lambda x: x.vega())


    wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
    sht = wb.sheets[0]
    sht.range('A1').value = markets

mkts = display_markets()
print(mkts)


