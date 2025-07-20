import numpy as np
import pandas as pd
from crypto_book.pricing_and_risk import one_touch_option_price, implied_volatility_one_touch, one_touch_option_delta
import datetime as dt
import yfinance as yf
import os
import pickle
import pandas as pd
import kalshi_api.main as kpi
import logging
from typing import Optional

# Set up logging
logger = logging.getLogger("airflow.task.crypto_snapshot")
logger.setLevel(logging.INFO)

def get_stock_price(ticker: str) -> float:
    """
    Fetches the latest closing price for a given stock ticker using yfinance.

    Common error associated with this function is returning none because yfinance is not updated to latest.

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
        raise Exception(f"Failed to get stock price for {ticker}: {e}")


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

def save_stock_price(ticker: str, output_path: Optional[str] = None):
    """
    Fetches the latest closing price for a given ticker and saves it to a pickle file.

    Parameters
    ----------
    ticker : str
        The ticker symbol (e.g., 'BTC-USD').
    output_path : str
        The file path where the price will be saved.
    """
    if output_path is None:
        output_path = f"app_data/{ticker}.pkl"
    price = get_stock_price(ticker)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(price, f)
    logger.info(f"Saved {ticker} price ({price}) to {output_path}")


def save_balance(output_path: str = "app_data/balance.pkl"):
    """
    Fetches the account balance and saves it to a pickle file.

    Parameters
    ----------
    output_path : str
        The file path where the balance will be saved.
    """
    try:
        balance = kpi.get_balance()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(balance, f)
        logger.info(f"Saved account balance ({balance}) to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save account balance: {e}", exc_info=True)
        raise

def save_positions(output_path: str = "app_data/positions.pkl"):
    """
    Fetches the current positions and saves them to a pickle file.

    Parameters
    ----------
    output_path : str
        The file path where the positions will be saved.
    """
    try:
        positions = kpi.get_positions()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(positions, f)
        logger.info(f"Saved positions to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save positions: {e}", exc_info=True)
        raise


def save_markets(ticker: str, output_path: str = None):
    """
    Fetches the markets for a given event ticker and saves them to a pickle file.

    Parameters
    ----------
    ticker : str
        The event ticker for which to fetch markets.
    output_path : str, optional
        The file path where the markets will be saved. If None, defaults to "app_data/{ticker}_markets.pkl".
    """
    try:
        if output_path is None:
            output_path = f"app_data/{ticker}_markets.pkl"
        markets = kpi.get_event_markets(ticker)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(markets, f)
        logger.info(f"Saved markets for {ticker} to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save markets for {ticker}: {e}", exc_info=True)
        raise

def save_orders(output_path: str = "app_data/orders.pkl"):
    """
    Fetches the current orders and saves them to a pickle file.

    Parameters
    ----------
    output_path : str
        The file path where the orders will be saved.
    """
    try:
        orders = kpi.get_orders()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(orders, f)
        logger.info(f"Saved orders to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save orders: {e}", exc_info=True)
        raise



def fetch_and_process_data():
    try:
        # logger.info("Fetching account balance...")
        # balance = kpi.get_balance()
        # logger.info(f"Balance type: {type(balance)}, value: {balance}")
        # os.makedirs("app_data", exist_ok=True)
        # with open("app_data/balance.pkl", "wb") as f:
        #     pickle.dump(balance, f)
        # logger.info("Balance fetched and saved.")

        # positions = kpi.get_positions()
        logger.info("Fetching positions...")
        positions = pd.read_pickle("app_data/positions.pkl")
        logger.info(f"Positions shape: {positions.shape if hasattr(positions, 'shape') else 'No shape'}")
        
        logger.info("Loading BTC markets from pickle files...")
        miny_markets = pd.read_pickle("app_data/miny_markets.pkl")
        maxy_markets = pd.read_pickle("app_data/maxy_markets.pkl")
        logger.info(f"MINY markets type: {type(miny_markets)}, shape: {miny_markets.shape if hasattr(miny_markets, 'shape') else 'No shape'}")
        logger.info(f"MAXY markets type: {type(maxy_markets)}, shape: {maxy_markets.shape if hasattr(maxy_markets, 'shape') else 'No shape'}")
        
        # Use pd.concat instead of append
        btc_markets = pd.concat([miny_markets, maxy_markets], ignore_index=True)
        logger.info(f"Combined BTC markets shape: {btc_markets.shape}")
        
        logger.info("Enriching positions...")
        enriched_positions = enriched_position_df(positions, btc_markets)
        enriched_positions.to_pickle("app_data/enriched_positions.pkl")
        logger.info("Enriched positions saved.")

        logger.info("DAG execution completed successfully!")
        return "SUCCESS"
    except Exception as e:
        logger.error(f"Error in fetch_and_process_data: {e}", exc_info=True)
        raise

