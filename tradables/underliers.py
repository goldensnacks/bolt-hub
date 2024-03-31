import datetime
from typing import Optional, Union, List
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d, interp2d
from financepy.market.curves import DiscountCurve
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.utils.date import Date
from .pricing_helper_fns import solve_vanilla_bs_for_strike, interpret_tenor
import datetime as dt
from financepy.utils.date import Date


class Underlier:
    def __init__(self):
        pass


class Event(Underlier):
    """Event is a specicial case of underlier representing some occurence"""
    @staticmethod
    def daily_probability(daily_probability: float) -> float:
        return daily_probability

    @staticmethod
    def decay_curve(decay_curve: str):
        return decay_curve

    @staticmethod
    def marking_start_date(marking_start_date: datetime.date) -> datetime.date:
        return marking_start_date

class Cross(Underlier):

    @staticmethod
    def asset_one(asset_one):
        return asset_one

    @staticmethod
    def asset_two(asset_two):
        return asset_two

    @staticmethod
    def spot(asset_one, asset_two):
        return asset_one.value_in_usd/asset_two.value_in_usd

    @staticmethod
    def forward_curve(asset_one, asset_two):
        interpolate_funding = asset_one.discount_curve._interpolator.interpolate
        interpolate_asset = asset_two.discount_curve._interpolator.interpolate
        forward_curve = lambda t: interpolate_funding(t) / interpolate_asset(t)
        return forward_curve

    @staticmethod
    def vol_surface_by_delta(vol_surface_by_delta: pd.DataFrame):
        return vol_surface_by_delta

    @staticmethod
    def vol_surface_by_strike(vol_surface_by_delta: pd.DataFrame, spot):
        vol_surface_by_strike = pd.DataFrame()
        for tenor in vol_surface_by_delta.index:
            for delta in vol_surface_by_delta.columns:
                vol = vol_surface_by_delta[delta][tenor]
                strike = solve_vanilla_bs_for_strike(delta, spot, .04, tenor, vol)
                vol_surface_by_strike._set_value(tenor, strike, vol)
        vol_surface_by_strike = vol_surface_by_strike.sort_index(axis=0).sort_index(axis=1)

        for index in range(0, len(vol_surface_by_strike.index)):
            vol_surface_by_strike.iloc[index] = vol_surface_by_strike.iloc[index].interpolate().fillna(method='bfill').fillna(method='ffill')

        return vol_surface_by_strike

    @staticmethod
    def vol_surface_as_fn(vol_surface_by_strike: pd.DataFrame):
        return interp2d(vol_surface_by_strike.columns, vol_surface_by_strike.index, vol_surface_by_strike.values)

    @staticmethod
    def intraday_weights(intraday_weights: pd.DataFrame):
        return intraday_weights


class Asset:
    def __init__(self):
        pass

def rates_curve_to_discount_curve(rates_curve):
    time_deltas =  [date - datetime.datetime.today() for date in rates_curve.index]
    years = [td.days/365 for td in time_deltas]
    df = [1/((1+(r/100))**year) for r, year in zip(years, rates_curve.values)]
    return list(rates_curve.index), df

class Currency(Asset):
    @staticmethod
    def discount_curve(curve_pairs: Optional[Union[List, pd.Series]]) -> DiscountCurve:
        valuation_date = Date.from_date(dt.date.today())
        if curve_pairs is None:
            return DiscountCurveFlat(0.0)
        elif isinstance(curve_pairs, float):
            return DiscountCurveFlat(curve_pairs)
        elif type(curve_pairs) in [list]:
            return DiscountCurve(valuation_date, curve_pairs[0], curve_pairs[1])
        elif isinstance(curve_pairs, pd.Series):
            dates, curve = rates_curve_to_discount_curve(curve_pairs)
            curve = [1] + curve
            curve = np.array(curve)
            dates = [Date.from_date(index_date) for index_date in dates]
            dates = [valuation_date] + dates
            return DiscountCurve(valuation_date, dates, curve)

    @staticmethod
    def value_in_usd(value_in_usd: float) -> float:
        return value_in_usd
    @staticmethod
    def country(country: str) -> str:
        return country
