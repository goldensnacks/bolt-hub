from datetime import datetime, date, time
from datetime import timedelta
from logging import getLogger

import numpy as np
import pandas as pd
from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date

from logging import getLogger

from datetime import datetime, date
from datetime import timedelta
from logging import getLogger

from financepy.market.curves.discount_curve_flat import DiscountCurveFlat
from financepy.models.black_scholes import BlackScholes
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.utils import TouchOptionTypes
from financepy.utils.date import Date
import yfinance as yf
from logging import getLogger
from pyxll import xl_func
from scipy.interpolate import interp1d
from scipy.stats import norm

from marking_cycles.kalshi_api import KalshiSession, snap_markets

# set cwd to be where this file is located
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from scipy.optimize import minimize, curve_fit

logger = getLogger('backtester_fns.pyxll_functions')



@xl_func(': string')
def get_cwd():
    import os
    return os.getcwd()

def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")["Close"].iloc[-1]

@xl_func('string ticker: rtd')
def get_stock_price_ticking(ticker):
    while True:
        price = get_stock_price(ticker)
        yield price
        import time
        time.sleep(60)


@xl_func(': float')
def get_balance():
    from main import get_balance
    logger.info("getting balance")
    return get_balance()

@xl_func(': dataframe')
def get_positions():
    from main import get_positions
    logger.info("getting positions")
    return get_positions()

@xl_func('str catagory: dataframe')
def get_events(catagory='all'):
    from main import get_events
    logger.info(f"getting events with category {catagory}")
    events = get_events()
    if catagory == 'all':
        return events
    else:
        return events[events['category'] == catagory]


@xl_func('str ticker: dataframe')
def get_event_markets(ticker):
    from main import get_event_markets
    logger.info("getting events")
    return get_event_markets(ticker)



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


@xl_func("float spot, float barrier, float vol, float rate, float expiry: float")
def price_one_touch(S, B, sigma, r, T):
    return one_touch_option_price(S, B, r, T, sigma)


@xl_func("float spot, float strike, float vol, float rate, float expiry: float")
def one_touch_delta(S, K, sigma, r, T):
    # get spot increased 1%
    S_up = S * 1.01
    # get spot decreased 1%
    S_down = S * 0.99
    # calculate the delta
    return (one_touch_option_price(S_up, K, r, T, sigma) - one_touch_option_price(S_down, K, r, T, sigma)) / 2


@xl_func("float spot, float strike, float vol, float rate, float expiry: float")
def one_touch_vega(S, K, sigma, r, T):
    # get vol increased 1%
    vol_up = sigma * 1.01
    # get vol decreased 1%
    vol_down = sigma * 0.99
    # calculate the vega
    return (one_touch_option_price(S, K, r, T, vol_up) - one_touch_option_price(S, K, r, T, vol_down)) / 2


@xl_func("float spot, float strike, float vol, float rate, float expiry: float")
def one_touch_theta(S, K, sigma, r, T):
    # get expiry increased 1 day
    T_up = T + 1/252
    # calculate the theta
    return one_touch_option_price(S, K, r, T_up, sigma) - one_touch_option_price(S, K, r, T, sigma)

@xl_func('str ticker, dataframe<index=1, columns=1> positons: float')
def get_position(ticker, positions):
    logger.info(f"getting position for {ticker}")
    try:
        position = positions.loc[ticker]
    except KeyError:
        logger.info(f"no position for {ticker}")
        return 0
    return position['position']



@xl_func('float delta, float vol, float T, float S, float r, float q, str option_type: float')
def find_strike(delta: float, vol: float, T: float, S: float, r: float = 0, q: float = 0, option_type: str = "call") -> float:
    """
    Computes the strike price corresponding to a given delta and implied volatility using an iterative method.

    Parameters:
    - delta: The option delta (e.g., 0.05 for a 5-delta call, -0.25 for a 25-delta put)
    - vol: Implied volatility (in decimal, e.g., 0.20 for 20%)
    - T: Time to expiry in years
    - S: Spot price of the underlying
    - r: Domestic risk-free rate (default 0)
    - q: Foreign risk-free rate or dividend yield (default 0)
    - option_type: "call" or "put"

    Returns:
    - K: The corresponding strike price
    """

    def calculate_delta(S, K, vol, T, r_dom, r_for, call_or_put):
        """
        Garman–Kohlhagen spot delta for an FX option, from the domestic perspective.

        Parameters
        ----------
        S : float
            Spot FX rate (domestic per foreign).
        K : float
            Strike (same units as S).
        vol : float
            Volatility (annualized).
        T : float
            Time to maturity (in years).
        r_dom : float
            Domestic interest rate (continuously compounded).
        r_for : float
            Foreign interest rate (continuously compounded).
        call_or_put : str
            'call' or 'put'.

        Returns
        -------
        delta : float
            The Garman–Kohlhagen spot delta.
        """
        d1 = (np.log(S / K) + (r_dom - r_for + 0.5 * vol ** 2) * T) / (vol * np.sqrt(T))
        if call_or_put.lower() == 'call':
            return np.exp(-r_for * T) * norm.cdf(d1)
        elif call_or_put.lower() == 'put':
            return np.exp(-r_for * T) * (norm.cdf(d1) - 1)
        else:
            raise ValueError("call_or_put must be 'call' or 'put'")
    # Objective function to minimize
    def objective(K_guess):
        delta_calculated = calculate_delta(S, K_guess, vol, T, r, q, option_type)
        return (delta_calculated - delta) ** 2

    # Initial guess for strike price
    initial_guess = S

    # Minimize the difference between target delta and calculated delta
    result = minimize(objective, initial_guess, method='Nelder-Mead')

    if not result.success:
        raise ValueError("Optimization failed to converge")

    # Return the optimized strike price
    result = result.x[0]

    delta = calculate_delta(S, result, vol, T, r, q, option_type)  # This is to ensure the final result is correct

    return result  # Return the strike price that corresponds to the given delta


@xl_func('float strike, numpy_array strikes, numpy_array vols: float')
def generate_interpolation_function(strike, strikes, vols):
    """
    Generates a parabolic interpolation function that returns volatility given a strike price.

    Parameters:
    - strikes: List or array of strike prices
    - vols: List or array of corresponding volatilities (in decimal)

    Returns:
    - A function that takes a strike price and returns the interpolated volatility
    """

    # Convert inputs to numpy arrays if they are not already
    strikes = np.asarray(strikes).flatten()
    vols = np.asarray(vols).flatten()

    if len(strikes) != len(vols):
        raise ValueError("Length of strikes and vols must be equal")

    # Sort strikes and vols for curve fitting
    sorted_indices = np.argsort(strikes)
    sorted_strikes = strikes[sorted_indices]
    sorted_vols = vols[sorted_indices]

    # Define a parabolic function
    def parabolic_func(x, a, b, c):
        return a * x**2 + b * x + c

    # Fit the data to the parabolic function
    params, _ = curve_fit(parabolic_func, sorted_strikes, sorted_vols)

    # Generate the interpolation function using the fitted parameters
    def interpolation_function(x):
        return parabolic_func(x, *params)

    return interpolation_function(strike)

