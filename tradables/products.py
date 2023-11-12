import pudb
import numpy as np
import copy
import pandas as pd
from .pricing_helper_fns import binary_option_price, one_touch_option_price
from datetime import datetime, timedelta
from scipy.interpolate import interp1d, interp2d
from securities import get_security
from logging import getLogger
logger = getLogger(__name__)

class MarketTable:
    def __init__(self, table=pd.DataFrame()):
        self.table = table
    def update_table(self, new_table):
        self.table = new_table

    def get_table(self):
        return self.table

class Tradable:
    def __init__(self, underlier, expiry=None):
        self.underlier = get_security(underlier)
        self.expiry = expiry
        self.funding = .08

    def days_to_expiry(self):
        raw_days = (self.expiry - datetime.now()) / timedelta(days=1)
        if raw_days < 1:
            weight =  self.underlier.obj.get_intraday_weight(datetime.now().hour, self.expiry.hour)
            return raw_days*weight
        else:
            return raw_days
    def underlying_price(self):
        try:
            return self.underlier.obj.forward_curve_as_fn()(self.days_to_expiry()*86400).max() if self.days_to_expiry() > 10 else self.underlier.spot
        except Exception:
            return self.underlier.obj.spot
    def delta(self):
        """calculate delta"""
        up = copy.deepcopy(self)
        up.underlier.obj.spot += .01
        down = copy.deepcopy(self)
        down.underlier.obj.spot -= .01
        return (up.price() - down.price()) / .02

    def vega(self):
        """calculate vega"""
        up = copy.deepcopy(self)
        up.underlier.vol += .01
        down = copy.deepcopy(self)
        down.underlier.vol -= .01
        return (up.price() - down.price()) / .02

class OneDelta(Tradable):
    def __init__(self, underlier, expiry=None):
        super().__init__(underlier, expiry)
    def price(self):
        logger.info("attempting to price one delta")
        return self.underlier.obj.underlying_price()


class BinaryOption(Tradable):
    def __init__(self, underlier, min_strike=None, max_strike=None, expiry=None):
        self.max_strike = max_strike
        self.min_strike = min_strike
        super().__init__(underlier, expiry)

    def get_min_vol(self):
        tenor = self.days_to_expiry()
        strike = self.min_strike
        vol = self.underlier.obj.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100
    def get_max_vol(self):
        tenor = self.days_to_expiry()
        strike = self.max_strike
        vol = self.underlier.obj.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100

    def price(self):
        logger.info("attempting to price binary option")
        under_min  = binary_option_price(self.underlying_price(), self.min_strike, self.funding, 0, self.days_to_expiry() / 365, self.get_min_vol(), 'put') if not np.isnan(self.min_strike) else 0
        over_max   = binary_option_price(self.underlying_price(), self.max_strike, self.funding, 0, self.days_to_expiry() / 365, self.get_max_vol(), 'call') if not np.isnan(self.max_strike) else 0
        return 1 - under_min - over_max

    def pricing_vol(self):
        return f"Min: {self.get_min_vol()} Max:  {self.get_max_vol()}"

    def is_liquid(self):
        return True

class OneTouch(Tradable):
    def __init__(self, underlier, strike, expiry=None):
        self.strike = strike
        super().__init__(underlier, expiry)

    def price(self):
        logger.info("attempting to price one touch")
        return one_touch_option_price(self.underlying_price(), self.strike, .05, self.days_to_expiry() / 365, self.pricing_vol())

    def pricing_vol(self):
        tenor = self.days_to_expiry()
        strike = self.strike
        vol = self.underlier.obj.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100

    def is_liquid(self):
        return False





