import numpy as np
import pandas as pd
from crypto_book.pricing_and_risk import one_touch_option_price, implied_volatility_one_touch, one_touch_option_delta
import datetime as dt
import yfinance as yf

def get_stock_price(ticker: str) -> float:
    """
    Fetches the latest closing price for a given stock ticker using yfinance.

    Parameters
    ----------
    ticker : str
        The ticker symbol of the stock (e.g., 'BTC-USD').

    Returns
    -------
    float
        The latest closing price of the stock. If fetching fails, returns a default value.
    """
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period="1d")["Close"].iloc[-1]
    except Exception as e:
        print(f"failed to  get stock price for {ticker}: {e}, returning 94000")
        return 120_000



def fit_vol_spline(spot: float) -> np.poly1d:
    """
    Fit a quadratic polynomial (parabola) to implied volatility as a function of strike price.

    Parameters
    ----------
    spot : float
        The current spot price of the underlying asset.

    Returns
    -------
    np.poly1d
        A quadratic polynomial function mapping strike price to implied volatility.
    """
    offset_strikes = np.array([.25, .5, .75,  1, 1.25, 1.5, 2, 5])
    strikes = offset_strikes * spot
    vols    = np.array([.63, .6, .51, .5, .52,  .56, .58, 1])
    # fit a spline to the data

    # Fit a parabola: vol ≈ a * strike^2 + b * strike + c
    coeffs = np.polyfit(strikes, vols, deg=2)
    # Create the quadratic function
    spline = np.poly1d(coeffs)
    return spline

def set_strike(enriched_df: pd.DataFrame, spot: float) -> pd.DataFrame:
    enriched_df['strike'] = enriched_df.apply(
        lambda row: row['cap_strike'] if pd.notna(row['cap_strike']) else row['floor_strike'],
        axis=1
    )
    return enriched_df

def set_vol_mark(enriched_df: pd.DataFrame, spline: np.poly1d, spot: float) -> pd.DataFrame:
    enriched_df = enriched_df.copy()
    enriched_df['vol_mark'] = enriched_df.strike.apply(lambda x: spline(x))
    enriched_df['marked_price'] = enriched_df.apply(
        lambda row: one_touch_option_price(
            spot,  # using spot instead of self.spot
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
            row['vol_mark']
        ),
        axis=1
    )
    enriched_df['marked_price'] = enriched_df.apply(
        lambda row: one_touch_option_price(
            spot,  # using spot instead of self.spot
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
            row['vol_mark']
        ),
        axis=1
    )
    return enriched_df

def filter_positions_by_market(positions_df: pd.DataFrame, markets_df: pd.DataFrame) -> pd.DataFrame:
    positions_df = positions_df[positions_df['ticker'].isin(markets_df['ticker'])]
    enriched_df = markets_df.merge(positions_df, on='ticker', how='left')
    return enriched_df


def set_implied_vol(enriched_df: pd.DataFrame, spot: float) -> pd.DataFrame:
    enriched_df['implied_vol_bid'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_bid'],
            spot,
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )
    enriched_df['implied_vol_ask'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_ask'],
            spot,
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )
    enriched_df['implied_vol_mid'] = (enriched_df['implied_vol_bid'] + enriched_df['implied_vol_ask']) / 2
    enriched_df['mid'] = (enriched_df['yes_bid'] + enriched_df['yes_ask']) / 2
    return enriched_df

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


def enriched_position_df(positions_df: pd.DataFrame, markets_df: pd.DataFrame, spot: float = None) -> pd.DataFrame:
    if spot is None:
        spot = get_stock_price('BTC-USD')
    spline = fit_vol_spline(spot)

    enriched_df = filter_positions_by_market(positions_df, markets_df)
    enriched_df = set_strike(enriched_df, spot)
    enriched_df = set_vol_mark(enriched_df, spline, spot)
    enriched_df = set_implied_vol(enriched_df, spot)
    
    
    enriched_df = set_deltas(enriched_df, spot)
    return enriched_df

def _enriched_position_df(positions_df, markets_df, spot=None):
    """
    Enrich positions_df with market data.
    """
    if spot is None:
        spot = get_stock_price('BTC-USD')
    
    # drop positions where ticker is not in markets_df
    positions_df = positions_df[positions_df['ticker'].isin(markets_df['ticker'])]
    positions_df = set_spot(positions_df, spot)
    enriched_df = markets_df.merge(positions_df, on='ticker', how='left')

    offset_strikes = np.array([.25, .5, .75,  1, 1.25, 1.5, 2, 5])
    strikes = offset_strikes * spot
    vols    = np.array([.63, .6, .51, .5, .52,  .56, .58, 1])
    # fit a spline to the data

    # Fit a parabola: vol ≈ a * strike^2 + b * strike + c
    coeffs = np.polyfit(strikes, vols, deg=2)
    # Create the quadratic function
    spline = np.poly1d(coeffs)

    # strike is whichever is not nan
    enriched_df['strike'] = enriched_df.apply(
        lambda row: row['cap_strike'] if pd.notna(row['cap_strike']) else row['floor_strike'],
        axis=1
    )

    # apply spline for each strike in enriched_positions
    enriched_df['vol_mark'] = enriched_df.strike.apply(lambda x: spline(x))

    enriched_df['mid'] = (enriched_df['yes_bid'] + enriched_df['yes_ask']) / 2
    enriched_df['marked_price'] = enriched_df.apply(
        lambda row: one_touch_option_price(
            spot,  # using spot instead of self.spot
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
            row['vol_mark']
        ),
        axis=1
    )

    enriched_df['implied_vol_bid'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_bid'],
            spot,
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )

    enriched_df['implied_vol_ask'] = enriched_df.apply(
        lambda row: implied_volatility_one_touch(
            row['yes_ask'],
            spot,
            row.strike,
            0.05,  # assuming a risk-free rate of 5%
            (dt.datetime(2025, 12, 31) - pd.Timestamp.now()).days / 365,
        ),
        axis=1
    )
    enriched_df['implied_vol_mid'] = (enriched_df['implied_vol_bid'] + enriched_df['implied_vol_ask']) / 2
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


