from datetime import datetime, date
from datetime import timedelta

import numpy as np
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date
from scipy.optimize import brentq

def one_touch_option_price(S, K, r, T, vol):
    expiry = date.today() + timedelta(days=T * 252)
    today = Date(datetime.today().day, datetime.today().month, datetime.today().year)
    expiry = Date(expiry.day, expiry.month, expiry.year)
    option_type = TouchOptionTypes.UP_AND_IN_CASH_AT_EXPIRY if S < K else TouchOptionTypes.DOWN_AND_IN_CASH_AT_EXPIRY
    barier  = K
    payment = 1.0
    opt = EquityOneTouchOption(expiry, option_type, barier, payment)
    dis_curve = DiscountCurveFlat(today, r)
    div_curve = DiscountCurveFlat(today, 0)
    model = BlackScholes(vol)
    return opt.value(today, S, dis_curve, div_curve, model)


def one_touch_option_delta(S, K, r, T, vol):

    try:
        expiry = date.today() + timedelta(days=T * 252)
        today = Date(datetime.today().day, datetime.today().month, datetime.today().year)
        expiry = Date(expiry.day, expiry.month, expiry.year)
        option_type = TouchOptionTypes.UP_AND_IN_CASH_AT_EXPIRY if S < K else TouchOptionTypes.DOWN_AND_IN_CASH_AT_EXPIRY
        barier  = K
        payment = 1.0
        opt = EquityOneTouchOption(expiry, option_type, barier, payment)
        dis_curve = DiscountCurveFlat(today, r)
        div_curve = DiscountCurveFlat(today, 0)
        model = BlackScholes(vol)
        return opt.delta(today, S, dis_curve, div_curve, model)
    except Exception as e:
        return np.nan


def implied_volatility_one_touch(market_price, S, K, r, T,
                                 vol_lower=0.25, vol_upper=2,
                                 tol=1e-6, max_iter=100):
    """
    Compute implied volatility for a one-touch option.

    Parameters
    ----------
    market_price : float
        The observed market price of the one-touch option.
    S : float
        Spot price.
    K : float
        Barrier level.
    r : float
        Risk-free rate.
    T : float
        Time to expiry in years.
    vol_lower : float
        Lower bound for volatility search.
    vol_upper : float
        Upper bound for volatility search.
    tol : float
        Tolerance for convergence.
    max_iter : int
        Maximum iterations for solver.

    Returns
    -------
    float
        Implied volatility.
    """
    def objective(vol):
        return one_touch_option_price(S, K, r, T, vol) - market_price / 100

    try:
        implied_vol = brentq(objective, vol_lower, vol_upper, xtol=tol, maxiter=max_iter)
        return implied_vol
    except ValueError:
        return None  # No solution found within bounds


def set_deltas(enriched_df: pd.DataFrame, spot: float) -> pd.DataFrame:
    enriched_df['delta_by_mid'] = enriched_df.apply(
        lambda row: one_touch_option_delta(
            spot,  # using spot instead of self.spot
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
            row.implied_vol_mid
        ),
        axis=1
    )
    enriched_df['delta_by_marked'] = enriched_df.apply(
        lambda row: one_touch_option_delta(
            spot,  # using spot instead of self.spot
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
            row.vol_mark
        ),  
        axis=1
    )
    enriched_df['position_delta'] = enriched_df['position'] * enriched_df['delta_by_mid'] * spot * .01
    enriched_df['position_delta_marked'] = enriched_df['position'] * enriched_df['delta_by_marked'] * spot * .01
    enriched_df['collateral_value'] = np.where(
        enriched_df['position'] > 0,
        (enriched_df['mid']) * enriched_df['position'].abs() / 100,
        (100 - enriched_df['mid']) * enriched_df['position'].abs() / 100
    )
    return enriched_df


def set_implied_vol(enriched_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates and sets the implied volatility columns ('implied_vol_bid', 'implied_vol_ask', 'implied_vol_mid')
    and the mid price ('mid') for each row in the DataFrame using the one-touch option model.

    The function expects the following columns to be present in enriched_df:
        - 'yes_bid': Bid price for the "yes" side of the option
        - 'yes_ask': Ask price for the "yes" side of the option
        - 'spot': Current spot price of the underlier
        - 'strike': Option strike price

    Returns
    -------
    pd.DataFrame
        The input DataFrame with new columns:
            - 'implied_vol_bid': Implied volatility calculated from 'yes_bid'
            - 'implied_vol_ask': Implied volatility calculated from 'yes_ask'
            - 'implied_vol_mid': Average of 'implied_vol_bid' and 'implied_vol_ask'
            - 'mid': Average of 'yes_bid' and 'yes_ask'
    """
    enriched_df['implied_vol_bid'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_bid'],
            row['spot'],
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )
    enriched_df['implied_vol_ask'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_ask'],
            row['spot'],
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )
    enriched_df['implied_vol_mid'] = (enriched_df['implied_vol_bid'] + enriched_df['implied_vol_ask']) / 2
    enriched_df['mid'] = (enriched_df['yes_bid'] + enriched_df['yes_ask']) / 2
    return enriched_df

