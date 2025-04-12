import logging
import math
import numpy as np
import pytz
import scipy.stats as st
from datetime import datetime, date, timedelta

from financepy.utils import TouchOptionTypes
from scipy.stats import norm
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat

from financepy.market.curves import discount_curve_flat
from financepy.models.black_scholes import BlackScholes
from financepy.utils.date import Date
from constants.constants import DATE_OFFSETS
import logging
from datetime import timedelta
from dateutil.rrule import rrule, DAILY
from dateutil.parser import parse
import re

# Configure logging

logging.basicConfig(level=logging.WARNING)

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

def vanilla_bs_delta(S, K, r, T, sigma):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    delta = norm.cdf(d1)
    return delta

def interpet_delta(delta):
    if isinstance(delta, str):
        delta = delta.lower()
        last_char = delta[-1]
        if last_char == 'c':
            return float(delta[0:-1])/100
        elif last_char == 'p':
            return 1-float(delta[0:-1])/100
        else:
            raise ValueError("Invalid delta string")
    else:
        return delta
def interpret_sigma(sigma):
    if sigma > 1_000:
        logging.warning(f'Sigma is fucking stupid {sigma}, returning nan')
        return np.nan
    if sigma > 2:
        return sigma/100
    else:
        return sigma

def string_to_rdate(s, start_date, occurrences=10):
    # Extract the number from the string
    days = s.split(' ')[0]
    # Convert the number to an integer
    days = float(days)
    return timedelta(days=days)
def interpret_tenor(tenor):
    if isinstance(tenor, str):
        if tenor in DATE_OFFSETS.keys():
            tenor = DATE_OFFSETS[tenor].total_seconds()
        else:
            tenor = string_to_rdate(tenor, datetime.today(), 1)

    if isinstance(tenor, timedelta):
        return tenor.total_seconds()/82400/365
    return tenor
def solve_vanilla_bs_for_strike(delta, S, r, tenor, sigma):
    delta = interpet_delta(delta)
    sigma = interpret_sigma(sigma)
    tenor = interpret_tenor(tenor)
    d1 = norm.ppf(delta) + (r + 0.5 * sigma ** 2) * tenor / (sigma * np.sqrt(tenor))
    K = S * np.exp(-d1 * sigma * np.sqrt(tenor) + (r - 0.5 * sigma ** 2) * tenor)
    return K

def convert_kalshi_date_to_datetime(date):
    """first convert expiry to datetime"""
    time = datetime.strptime(date, '%Y-%m-%dT%H:%M:%SZ')
    return time

