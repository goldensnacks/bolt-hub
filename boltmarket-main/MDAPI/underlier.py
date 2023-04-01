import functools
import pickle
from dataclasses import dataclass
import numpy
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