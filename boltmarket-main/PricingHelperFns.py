import math
import scipy.stats as st
from datetime import datetime, date, timedelta
from scipy.stats import norm
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.utils.global_types import TouchOptionTypes
from financepy.market.curves import discount_curve_flat
from financepy.models.black_scholes import BlackScholes
from financepy.utils.date import Date
def binary_option_price(S, K, r, q, T, sigma, option_type):
    """
    S: current stock price
    K: strike price
    r: risk-free interest rate
    q: dividend yield
    T: time to maturity (in years)
    sigma: volatility of the underlying asset
    option_type: 'call' or 'put'
    """
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if option_type == 'call':
        price = math.exp(-q * T) * norm.cdf(d2)
    elif option_type == 'put':
        price = math.exp(-q * T) * (1 - norm.cdf(d2))
    else:
        raise ValueError("Invalid option type. Must be 'call' or 'put'.")
    return price

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

def convert_kalshi_date_to_datetime(date):
    """first convert expiry to datetime"""
    return datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')