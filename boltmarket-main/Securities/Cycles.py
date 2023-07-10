import pickle
import sys
from datetime import datetime, date, timedelta
import sys
import os
from random import random
import pandas as pd
import openpyxl
import xlwings as xw

from KalshiAPIStarterCode.KalshiClientsBaseV2 import ExchangeClient

# Add the parent directory (my_project) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '..')))
from Shrugs import Shrugs
from Securities import get_security, Security, save_security

class Cycle:
    def __init__(self):
        pass

class UnderlierMarkingCycle(Cycle):
    def __init__(self, underlier, shrug):
        self.underlier = underlier
        self.shrug = shrug

    def mark_spot(self, randsim=False):
        spot = self.shrug.get_val(self.underlier, "spot") + randsim*random()
        sec = get_security(self.underlier)
        sec.obj.mark_spot(spot)
        sec.save()

    def cycle(self):
        while True:
            self.mark_spot()

class ProductMarkingCycle(Cycle):
    def __init__(self, filter):
        self.filter = filter
        # from TDAPI.tradables import VanillaOption, Portfolio, Range
        self.prod_email = "jacobreedijk@gmail.com"  # change these to be your personal credentials
        self.prod_password = "DJDSOLwr13?"
        self.prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"
        self.exchange_client = ExchangeClient(exchange_api_base=self.prod_api_base, email=self.prod_email, password=self.prod_password)
        self.config = {'limit': 1000,
                  'cursor': None,  # passing in the cursor from the previous get_markets call
                  'event_ticker': None,
                  'series_ticker': None,
                  'max_close_ts': None,  # pass in unix_ts
                  'min_close_ts': None,  # pass in unix_ts
                  'status': 'open',  # open, closed, settled
                  'tickers': None
                  }
        self.markets = self.exchange_client.get_markets(**self.config)


    def is_one_touch(self, market):
        return market['title'].lower().find('minimum') != -1 or market['title'].lower().find('maximum') != -1

    def display_markets(self):
        markets = pd.DataFrame(get_markets()['markets'])

        """just markets with eurusd in ticker"""
        markets = markets[markets['ticker'].str.contains('EURUSD')]
        columns = ["ticker", "event_ticker", "title", 'open_interest',
                   "open_time", "close_time", "yes_bid",
                   "yes_ask", "last_price", "strike_type"	,   "floor_strike",	"cap_strike",	"custom_strike"]
        """just columns we want"""
        markets = markets[columns]

        """add expiration time column"""
        markets['expiration_time'] = markets.apply(lambda x: x.close_time, axis = 1)

        """add hours to expiry"""
        markets['hours_to_expiry'] = markets.apply(lambda x: (convert_kalshi_date_to_datetime(x.expiration_time) -
                                                              datetime.utcnow()).total_seconds( ) /3600, axis = 1)
        """add one touch column"""
        markets['one_touch'] = markets.apply(is_one_touch, axis = 1)

        """filter out any one touch markets"""
        markets = markets[~markets['one_touch']]

        """make underlier - same for all markets"""
        with open('Securities/EURUSD.pkl', 'rb') as f:
            underlier = pickle.load(f)

        """populate strike for markets without both cap and floor"""
        markets['strike'] = markets.apply \
            (lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)

        """make product for each market"""
        products = markets.apply \
            (lambda x: OneTouch(underlier, x.strike, convert_kalshi_date_to_datetime(x.expiration_time))
        if x.one_touch else
        BinaryOption(underlier, x.floor_strike, x.cap_strike,
                     convert_kalshi_date_to_datetime(x.expiration_time)),
                                 axis = 1)

        """add prices for each market"""
        markets['price'] = 10 0 *products.apply(lambda x: x.price())

        """add alphas for each market"""
        markets['alpha_long'] =  markets['price'] - markets['yes_ask']
        markets['alpha_short'] = markets['yes_bid'] -  markets['price']

        """display underlier pricer for each market"""
        markets['underlying_px'] = products.apply(lambda x: x.underlying_price())

        """add risks for each market"""
        # markets['delta'] = products.apply(lambda x: x.delta())

        # markets['vega'] = products.apply(lambda x: x.vega())



class GUICycle(Cycle):
    def __init__(self, excel, tab, mappings):
        self.excel = excel
        self.tab = tab
        self.mappings = mappings


        super().__init__()

    def cycle(self):
        while True:
            wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
            sht = wb.sheets[0]
            for item in self.mappings.items():
                sht.range(item[0]).value = item[1]()


