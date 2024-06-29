import numpy as np
import copy
import pandas as pd
from .pricing_helper_fns import binary_option_price, one_touch_option_price
from datetime import datetime, timedelta
from scipy.interpolate import interp1d, interp2d
from securities.graph import get_security
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
    @staticmethod
    def days_to_expiry(expiry, underlier):
        raw_days = (expiry - datetime.now()) / timedelta(days=1)
        if raw_days < 1:
            weight =  underlier.obj.get_intraday_weight(datetime.now().hour, expiry.hour)
            return raw_days*weight
        else:
            return raw_days
    @staticmethod
    def underlying_price(underlier):
        return underlier.spot

    @staticmethod
    def delta(underlier):
        """calculate delta"""
        up = copy.deepcopy(underlier)
        up.underlier.obj.spot += .01
        down = copy.deepcopy(underlier)
        down.underlier.obj.spot -= .01
        return (up.price() - down.price()) / .02

    @staticmethod
    def vega(underlier):
        """calculate vega"""
        up = copy.deepcopy(underlier)
        up.underlier.vol += .01
        down = copy.deepcopy(underlier)
        down.underlier.vol -= .01
        return (up.price() - down.price()) / .02

class SimpleEventBinary(Tradable):
    """Bet on an event occuring before some date"""
    @staticmethod
    def expiry(expiry):
        return expiry

    @staticmethod
    def tenor_in_days(expiry):
        return (expiry - datetime.utcnow()).days

    @staticmethod
    def price(underlier, tenor_in_days):
        return underlier.daily_probability ** tenor_in_days

    @staticmethod
    def underlier(underlier):
        return underlier

class OneDelta(Tradable):
    @staticmethod
    def price(underlier):
        logger.info("attempting to price one delta")
        return underlier.obj.underlying_price()


class BinaryOption(Tradable):
    @staticmethod
    def min_vol(tenor, floor_strike, underlier):
        if np.isnan(floor_strike):
            return np.nan
        else:
            vol = underlier.vol_surface_as_fn(tenor, floor_strike)
            return vol[0]

    @staticmethod
    def max_vol(tenor, cap_strike, underlier):
        if np.isnan(cap_strike):
            return np.nan
        else:
            vol = underlier.vol_surface_as_fn(tenor, cap_strike)
            return vol[0]

    @staticmethod
    def tenor(expiry, underlier):
        time_delta = (expiry - datetime.now())
        if time_delta.days:
            return time_delta.total_seconds()/86400/365
        else:
            # adjust for hourly weighting
            weights =  underlier.intraday_weights
            if datetime.utcnow().hour > expiry.hour:
                weight_today = weights[datetime.now().hour:24].mean()
                weight_tomorrow = weights[0:expiry.hour].mean()
                weight = (weight_today + weight_tomorrow) / 2
            else:
                weight = weights[datetime.utcnow().hour:expiry.hour].mean()
            weight = weight / (1/24)
            total_hours = time_delta.total_seconds()/3600
            return (total_hours*weight) / 24 / 365

    @staticmethod
    def floor_strike(floor_strike):
        return floor_strike

    @staticmethod
    def cap_strike(cap_strike):
        return cap_strike

    @staticmethod
    def expiry(expiry):
        return expiry

    @staticmethod
    def underlier(underlier):
        return underlier

    @staticmethod
    def funding(funding):
        return funding

    @staticmethod
    def price(underlier, floor_strike, cap_strike, expiry, funding):
        logger.info("attempting to price binary option")
        spot = underlier.spot
        tenor_in_years = (expiry - datetime.now()).seconds/86400/365

        floor_vol = underlier.vol_surface_as_fn(tenor_in_years, floor_strike) / 100
        cap_vol = underlier.vol_surface_as_fn(tenor_in_years, cap_strike) / 100

        under_min  = binary_option_price(spot, floor_strike, funding, 0, tenor_in_years, floor_vol, 'put') if not np.isnan(floor_strike) else 0
        over_max   = binary_option_price(spot, cap_strike,   funding, 0, tenor_in_years, cap_vol, 'call') if not np.isnan(cap_strike) else 0
        price =  1 - under_min - over_max
        return price[0]

class OneTouch(Tradable):

    @staticmethod
    def price(underlier, strike, funding, tenor_in_years):
        logger.info("attempting to price one touch")
        spot = underlier.spot
        vol = underlier.vol_surface_as_fn()(tenor_in_years, strike)
        return one_touch_option_price(spot,strike, funding, tenor_in_years, vol)


    @staticmethod
    def pricing_vol(self):
        tenor = self.days_to_expiry()
        strike = self.strike
        vol = self.underlier.obj.vol_surface_as_fn()(tenor, strike)
        return vol[0]/100

    # def is_liquid(self):
    #     return False





