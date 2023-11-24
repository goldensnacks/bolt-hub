import pudb
import logging
from datetime import datetime
import numpy as np
import pandas as pd

from cycles import Cycle
from kalshi.KalshiInterface import ExchangeClient
from securities.graph import get_security
from tradables.pricing_helper_fns import convert_kalshi_date_to_datetime
from tradables.products import OneTouch, BinaryOption, MarketTable


class ProductMarkingCycle(Cycle):
    def __init__(self):
        self.underliers = ["EURUSD", "USDJPY"]
        self.columns = [ 'title',  'open_interest', "close_time",   "yes_bid",
                          'last_price',   "expiration_time",   "floor_strike",
                                 "cap_strike" ]
        self.display_columns = ['title',        'open_interest',
                                'last_price',   "hours_to_expiry", "floor_strike",
                                "cap_strike",   'mrp',             'pricing_vol',
                                'delta',

                                'alpha_long',  "yes_ask", 'price',   "yes_bid", 'alpha_short',
                                ]



        # from TDAPI.tradables import VanillaOption, Portfolio, Range
        self.prod_email = "jacobreedijk@gmail.com"  # change these to be your personal credentials
        self.prod_password = "DJDSOLwr11??"
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

    def assign_underlier(self, market, enabled = [ "EURUSD", "USDJPY"]):
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
        try:
            tradable_sec = Sc.get_security("tradables")
        except Exception as e:
            tradable_sec = Sc.Security("tradables", MarketTable())
        tradable_sec.obj.update_table(markets)
        tradable_sec.save()

    def markets_as_table(self):
        markets = pd.DataFrame(self.snap_markets())
        markets['underlier'] = markets.apply(self.assign_underlier, axis = 1)
        markets = markets[~markets['underlier'].isna()]
        markets['expiration_time'] = markets.apply(lambda x: x.close_time, axis = 1)
        markets['hours_to_expiry'] = markets.apply(lambda x: (convert_kalshi_date_to_datetime(x.expiration_time) -
                                                              datetime.utcnow()).total_seconds( ) /3600, axis = 1)
        markets['one_touch'] = markets.apply(self.is_one_touch, axis = 1)
        markets['strike'] = markets.apply (lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)
        if True: # exclude one touch
            markets = markets[~markets['one_touch']]

        products = markets.apply(self.assign_tradable, axis = 1)
        pudb.set_trace()
        markets['price'] = 100 *products.apply(lambda x: x.price())
        markets['delta'] = products.apply(lambda x: x.delta())

        markets['mrp'] = products.apply(lambda x: x.underlying_price())
        markets['pricing_vol'] = products.apply(lambda x: x.pricing_vol())
        markets['is_liquid'] = products.apply(lambda x: x.is_liquid())
        markets = markets[markets['is_liquid'] == True]

        markets['alpha_long'] =  markets['price'] - markets['yes_ask'] if markets['yes_ask'] != 0 else 0
        markets['alpha_short'] = markets['yes_bid'] -  markets['price'] if markets['yes_bid'] != 0 else 0
        markets = markets[self.display_columns]

        return markets

    def cycle(self):
        while True:
            try:
                self.save_markets(self.markets_as_table())
                logging.info("Saved markets")
            except Exception as e:
                print(e)
                pass    # if the cycle fails, just try again


