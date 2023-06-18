from datetime import datetime, date, timedelta
from math import sqrt
import numpy as np
import pandas as pd
import copy
import pickle
import math
from scipy.stats import norm
from PricingHelperFns import binary_option_price, one_touch_option_price
from datetime import datetime, date, timedelta
class Tradable:
    def __init__(self, underlier, expiry=None):
        self.underlier = underlier
        self.expiry = expiry

    def days_to_expiry(self):
        return (self.expiry - datetime.now()) / timedelta(days=1)

    def get_spot(self):
        return self.underlier.get_spot()

    def underlying_price(self):
        if self.time_to_expiry() <= 3:
            return self.underlier.get_spot()
        else:
            return self.underlier.delivery_curve[self.time_to_expiry()]
    def get_vol(self):
        return self.underlier.get_vol()

    def delta(self):
        """calculate delta"""
        up = copy.deepcopy(self)
        up.underlier.spot += .01
        down = copy.deepcopy(self)
        down.underlier.spot -= .01
        return (up.price() - down.price()) / .02

    def vega(self):
        """calculate vega"""
        up = copy.deepcopy(self)
        up.underlier.vol += .01
        down = copy.deepcopy(self)
        down.underlier.vol -= .01
        return (up.price() - down.price()) / .02
class BinaryOption(Tradable):
    def __init__(self, underlier, min_strike=None, max_strike=None, expiry=None):
        self.max_strike = max_strike
        self.min_strike = min_strike
        super().__init__(underlier, expiry)


    def price(self):
        under_min  = binary_option_price(self.underlying_price(), self.min_strike, .05, 0, self.days_to_expiry() / 365, .2, 'put') if not np.isnan(self.min_strike) else 0
        over_max   = binary_option_price(self.underlying_price(), self.max_strike, .05, 0, self.days_to_expiry() / 365, .2, 'call') if not np.isnan(self.max_strike) else 0
        return 1 - under_min - over_max

class OneTouch(Tradable):
    def __init__(self, underlier, strike, expiry=None):
        self.strike = strike
        super().__init__(underlier, expiry)

    def price(self):
        return one_touch_option_price(self.underlying_price(), self.strike, .05, self.days_to_expiry() / 365, .2)

class Underlier:
    def __init__(self, name):
        self.name = name
        self.delivery_curve = {}

    def mark_spot(self, spot):
        self.spot = spot

    def mark_vol(self, vol):
        self.vol = vol
    def get_spot(self):
        return self.spot

    def mark_curve(self, date, value):
        self.delivery_curve[date] = value



    def get_vol(self):
        return self.vol