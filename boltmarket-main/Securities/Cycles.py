import pickle
import sys
from datetime import datetime, date, timedelta
import sys
import os
from random import random
import numpy as np
import pandas as pd
import xlwings as xw
from KalshiAPIStarterCode.KalshiClientsBaseV2 import ExchangeClient

# Add the parent directory (my_project) to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '..')))
from Shrugs import Shrugs
from Securities import get_security, Security, save_security
from PricingHelperFns import convert_kalshi_date_to_datetime
from Tradables import BinaryOption, OneTouch, Underlier

class Cycle:
    def __init__(self):
        pass

class UnderlierMarkingCycle(Cycle):
    def __init__(self, underliers, shrug):
        self.underliers = underliers
        self.shrug = shrug

    def mark_spot(self, underlier, spot):
        sec = get_security(underlier)
        sec.obj.mark_spot(spot)
        sec.save()
        print(f"Marked {underlier} spot at {spot}")

    def mark_spots(self):
        spots = self.get_spots()
        for underlier in self.underliers:
            self.mark_spot(underlier, spots[underlier])

    def get_spots(self):
        return self.shrug.datasource.get_spots(self.underliers)
    def cycle(self):
        while True:
            self.mark_spots()

class ProductMarkingCycle(Cycle):
    def __init__(self):
        self.underliers = ["EURUSD", "USDJPY"]
        self.columns = [ 'title',  'open_interest', "close_time",   "yes_bid", "yes_ask",
                          'last_price',   "expiration_time",   "floor_strike",
                                 "cap_strike" ]
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


    def snap_markets(self):
        return self.exchange_client.get_markets(**self.config)['markets']
    def is_one_touch(self, market):
        return market['title'].lower().find('minimum') != -1 or market['title'].lower().find('maximum') != -1

    def assign_underlier(self, market, enabled = [ "EURUSD"]):
        if market['title'].lower().find('eur') != -1 and  "EURUSD" in enabled:
            return 'EURUSD'
        elif market['title'].lower().find('jpy') != -1 and "USDJPY" in enabled:
            return 'USDJPY'
        else:
            return None
    def filter_by_underlier(self, markets):
        return markets[markets['underlier'].isin(self.underliers)]

    def assign_tradable(self, market):
        if market['one_touch']:
            return OneTouch(market['underlier'], market['strike'], convert_kalshi_date_to_datetime(market['expiration_time']))
        else:
            return BinaryOption(market['underlier'], market['floor_strike'],market['cap_strike'], convert_kalshi_date_to_datetime(market['expiration_time']))

    def save_markets(self, markets):
        tradable_sec = get_security("Tradables")
        tradable_sec.obj.update_table(markets)
        tradable_sec.save()

    def markets_as_table(self):
        markets = pd.DataFrame(self.snap_markets())
        markets = markets[self.columns]
        markets['underlier'] = markets.apply(self.assign_underlier, axis = 1)
        markets = markets[~markets['underlier'].isna()]
        markets['expiration_time'] = markets.apply(lambda x: x.close_time, axis = 1)
        markets['hours_to_expiry'] = markets.apply(lambda x: (convert_kalshi_date_to_datetime(x.expiration_time) -
                                                              datetime.utcnow()).total_seconds( ) /3600, axis = 1)
        markets['one_touch'] = markets.apply(self.is_one_touch, axis = 1)
        markets['strike'] = markets.apply (lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)
        products = markets.apply(self.assign_tradable, axis = 1)
        markets['price'] = 100 *products.apply(lambda x: x.price())
        markets['alpha_long'] =  markets['price'] - markets['yes_ask']
        markets['alpha_short'] = markets['yes_bid'] -  markets['price']
        return markets

    def cycle(self):
        while True:
            try:
                self.save_markets(self.markets_as_table())
            except Exception as e:
                print(e)
                pass    # if the cycle fails, just try again



class GUICycle(Cycle):
    def __init__(self, excel, tab, mappings):
        self.excel = excel
        self.tab = tab
        self.mappings = mappings


        super().__init__()

    def place(self, cell, value, sheet):
        if isinstance(value, pd.DataFrame):
            sheet.range(cell).value = value
        else:
            sheet.range(cell).value = value

    def cycle(self):
        while True:
            try:
                wb = xw.Book(r'C:\Users\jacob\bolt-hub\GUI.xlsx')
                sht = wb.sheets[0]
                for item in self.mappings.items():
                    self.place(item[0], item[1](), sht)

            except Exception as e:
                print(e)
                pass
