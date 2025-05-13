from datetime import datetime, date
from datetime import timedelta

from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date

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


from scipy.optimize import brentq

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

