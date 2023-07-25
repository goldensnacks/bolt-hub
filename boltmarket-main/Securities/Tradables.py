from datetime import datetime, date, timedelta
from math import sqrt
import numpy as np
import pandas as pd
import copy
import pickle
import math
from scipy.stats import norm
from PricingHelperFns import binary_option_price, one_touch_option_price, solve_vanilla_bs_for_strike
from datetime import datetime, date, timedelta
from scipy.interpolate import interp1d, interp2d
import sys
import os
# Add the parent directory (my_project) to the Python path
sys.path.append('/boltmarket-main/Securities')
sys.path.append('/boltmarket-main')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname('boltmarket-main'), '../..')))

from Securities import get_security, Security, save_security



class Tradable:
    def __init__(self, underlier, expiry=None):
        self.underlier = get_security(underlier).obj
        self.expiry = expiry
        self.funding = .08

    def days_to_expiry(self):
        raw_days = (self.expiry - datetime.now()) / timedelta(days=1)
        if raw_days < 1:
            weight =  self.underlier.get_intraday_weight(datetime.now().hour, self.expiry.hour)
            return raw_days*weight
        else:
            return raw_days
    def underlying_price(self):
        return self.underlier.forward_curve_as_fn()(self.days_to_expiry()).max() if self.days_to_expiry() > 1 else self.underlier.spot
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

    def get_min_vol(self):
        tenor = self.days_to_expiry()
        strike = self.min_strike
        vol = self.underlier.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100
    def get_max_vol(self):
        tenor = self.days_to_expiry()
        strike = self.max_strike
        vol = self.underlier.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100

    def price(self):
        under_min  = binary_option_price(self.underlying_price(), self.min_strike, self.funding, 0, self.days_to_expiry() / 365, self.get_min_vol(), 'put') if not np.isnan(self.min_strike) else 0
        over_max   = binary_option_price(self.underlying_price(), self.max_strike, self.funding, 0, self.days_to_expiry() / 365, self.get_max_vol(), 'call') if not np.isnan(self.max_strike) else 0
        return 1 - under_min - over_max

class OneTouch(Tradable):
    def __init__(self, underlier, strike, expiry=None):
        self.strike = strike
        super().__init__(underlier, expiry)

    def price(self):
        return one_touch_option_price(self.underlying_price(), self.strike, .05, self.days_to_expiry() / 365, .2)

class Underlier:
    def __init__(self):
        pass

    """spot & forward curve"""
    def mark_spot(self, spot):
        """spot represents current price, also remarking spot will reset forward curve"""
        self.spot = spot

    def get_spot(self):
        return self.spot
    def forward_curve_as_fn(self):
        x = [x.total_seconds()/86400 for x in self.forward_curve.index]
        y = [y[0] for y in self.forward_curve.values]
        return interp1d(x, y, kind='linear')
    def load_forward_curve(self, forward_curve):
        self.forward_curve = forward_curve


    """vol surface"""
    def load_vol_surface(self, vol_surface):
        self.marked_vol_tenors = vol_surface.index
        self.marked_deltas = vol_surface.columns
        self.vol_surface = vol_surface


    def vol_surface_as_fn(self):
        vol_surface = self.vol_surface.to_dict()
        Xs = []
        Ys = []
        Zs = []
        for x in vol_surface.keys():
            for y in vol_surface[x].keys():
                Xs.append(x)
                Ys.append(y.total_seconds()/86400)
                Zs.append(vol_surface[x][y])
        return interp2d(Xs, Ys, Zs)

    def delta_to_strike(self, delta, tenor):
        tenor = tenor.total_seconds()/86400
        sigma = self.vol_surface_as_fn()(delta, tenor)
        fwd = self.forward_curve_as_fn()(tenor)
        return solve_vanilla_bs_for_strike(delta, fwd, .05, tenor, sigma)

    def get_vol(self, tenor, strike = None, delta = None):
        if strike is not None:
            return self.vol_surface_as_fn()(strike, tenor.total_seconds()/86400)
        elif delta is not None:
            return self.vol_surface_as_fn()(delta, tenor.total_seconds()/86400)
        else:
            raise Exception('Must provide either strike or delta')

    def load_intraday_weights(self, weights):
        self.intraday_weights = weights

    def get_intraday_weight(self, start, end):
        if start < end:
            return self.intraday_weights.loc[start:end].mean() / self.intraday_weights.mean()
        else:
            left_today = self.intraday_weights.loc[start:23].mean() * (24 - start)
            right_today = self.intraday_weights.loc[0:end].mean() * end
            weighted_mean = (left_today + right_today) / (24 - start + end)
            return weighted_mean / self.intraday_weights.mean()





