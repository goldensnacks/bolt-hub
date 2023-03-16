import functools
import pickle
from dataclasses import dataclass
import numpy
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from scipy import interpolate
import scipy
import numpy as np
import time
from io import StringIO
from scipy.optimize import curve_fit
import math
"import tws api"
import ib_insync
from ib_insync import *
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


class YFinanceSource:
    def __init__(self, symbol):
        self.ticker = yf.Ticker(symbol)
        self.create_time = time.time()

    def vol_surface(self):
        ticker = self.ticker
        supported_dates = ticker.options

        surface_calls = pd.concat(list(
            map(lambda date: (ticker.option_chain(date).calls[["strike", "impliedVolatility"]]).set_index('strike'),
                supported_dates)), axis=1).T
        surface_puts = pd.concat(list(
            map(lambda date: (ticker.option_chain(date).puts[["strike", "impliedVolatility"]]).set_index('strike'),
                supported_dates)), axis=1).T

        def combine(A, B):
            if A is numpy.NaN:
                if B is numpy.NaN:
                    return None
                else:
                    return B
            if B is numpy.NaN:
                return A
            return (A + B) / 2

        surface = surface_calls.combine(surface_puts, combine)
        surface['dates'] = list(map(lambda date: ((datetime.strptime(date,
                                                                     "%Y-%m-%d").timestamp() - datetime.today().timestamp()) / 86400) + 16 / 24,
                                    supported_dates))
        surface = (surface.reset_index(drop=True)).set_index('dates').sort_index(axis=1)
        surface = surface.loc[[y for y in surface.index.values.tolist()],
                              [x for x in surface.columns.values.tolist()]]

        tenors = surface.index.values
        x, y = np.mgrid[0:len(surface), 0:len(surface.columns)]
        ix_notna = surface.notna().values
        z_interpolated = interpolate.griddata(
            (x[ix_notna], y[ix_notna]),
            surface.values[ix_notna],
            (x, y),
            method='linear')
        strikes = surface.columns.values
        surface = (pd.DataFrame(z_interpolated).reset_index(drop=True)).set_index(tenors)
        surface.columns = strikes
        return surface

class ibkrSource(EWrapper, EClient):
    def __init__(self, symbol):
        self.ticker = symbol
        self.create_time = time.time()
        self.ib = IB()
        self.client = EClient.__init__(self, self)
        self.connect(host="127.0.0.1", port=7496, clientId=0)

    def spot(self):
        return self.client.reqMktData(1, Contract(), "", False, False, [])


@dataclass
class MarketData:
    spot: float
    smile: np.polyfit

@dataclass
class positions:
    delta: float
    vega: float
    gamma: float
    theta:float
    position: pd.DataFrame


@dataclass
class Diddle:
    spot: float = 0
    vol: float = 0
    rate: float = 0

class Pair:
    def __init__(self, over, under, delivery, handle="marketdata.pickle"):
        self.over = over
        self.under = under
        self.delivery = delivery
        self.diddle = Diddle()
        self.handle = handle
        try:
            with open(self.handle, 'rb') as handle:
                self.market_data = pickle.loads(pickle.load(handle))
        except(Exception):
            self.save_market_data()
            self.market_data = pickle.loads(pickle.load(handle))

    def pairToSource(self):
        pairs = { ("USD", "NDX") : ("^NDX","NQ=F"),
                  ("USD", "SPX"): ("^SPX", "ES=F")
                 }
        return pairs[(self.over,self.under)]


    def vol(self, strike="atm"):
        if strike == "atm":
            strike = self.spot()
        if strike == 'NA':
            return numpy.nan
        strike = float(strike)
        return np.polyval(self.smile(), strike) + self.diddle.vol

    def save_market_data(self):
        market_data = MarketData(self.save_spot(), self.save_smile())
        print("spot: ", market_data.spot)
        print("smile: ", market_data.smile)
        market_data = pickle.dumps(market_data)
        with open(self.handle, 'wb') as handle:
            pickle.dump(market_data, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def save_smile(self):
        surface = YFinanceSource(self.pairToSource()[0]).vol_surface()
        smile = (surface.iloc[surface.index.get_loc(self.delivery, method='nearest')]).transpose()
        smile = smile.squeeze()
        smile = smile[smile.notnull()]
        smile = np.polyfit(smile.index, [value for value in smile.values], 2)
        return smile

    def save_spot(self):
        spot_ticker = yf.Ticker(self.pairToSource()[0])
        return spot_ticker.info['regularMarketPrice'] + self.diddle.spot
    def smile(self):
        return self.market_data.smile

    def spot(self):
        return self.market_data.spot

    def two_four_decay(self):
        return pd.read_csv('../24hr_decay.csv')