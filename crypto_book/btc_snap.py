import pickle

import kalshi_api.main as kpi
import numpy as np
import pandas as pd
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.products.fx.fx_one_touch_option import FXOneTouchOption
from scipy.interpolate import UnivariateSpline

from pricing_and_risk import one_touch_option_price, implied_volatility_one_touch, one_touch_option_delta
import datetime as dt
import yfinance as yf

def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        return stock.history(period="1d")["Close"].iloc[-1]
    except Exception as e:
        print(f"failed to  get stock price for {ticker}: {e}, returning 94000")
        return 97439

class AppData:
    def to_pickle(self, path="app_data/positions.pkl"):
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self.to_dict(), f)




class Underlying(AppData):
    def __init__(self, ticker):
        self.ticker = ticker

    @property
    def spot(self):
        return get_stock_price(self.ticker)

    def to_dict(self):
        return {"ticker": self.ticker}

    @classmethod
    def from_pickle(cls, path="app_data/positions.pkl"):
        import pickle
        import pandas as pd
        with open(path, "rb") as f:
            state = pickle.load(f)
        # df = pd.DataFrame(state["positions_df"])
        # balance = state["balance"]
        ticker = state["ticker"]
        return cls(ticker)



def enriched_position_df(positions_df, markets_df):
    """
    Enrich positions_df with market data.
    """
    spot = get_stock_price('BTC-USD')
    positions_df['spot'] = spot
    # drop positions where ticker is not in markets_df
    positions_df = positions_df[positions_df['ticker'].isin(markets_df['ticker'])]
    # enriched_df = positions_df.merge(markets_df, on='ticker', how='left')
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
    enriched_df['position_delta'] = enriched_df['position'] * enriched_df['delta_by_mid'] * spot * .01
    enriched_df['collateral_value'] = np.where(
        enriched_df['position'] > 0,
        (enriched_df['mid']) * enriched_df['position'].abs() / 100,
        (100 - enriched_df['mid']) * enriched_df['position'].abs() / 100
    )
    return enriched_df


if __name__ == "__main__":
    # print balance
    balance = kpi.get_balance()
    # dump balance to pickle
    with open("app_data/balance.pkl", "wb") as f:
        pickle.dump(balance, f)

    # pull in data from kalshi
    positions = kpi.get_positions()
    # get enriched positions
    btc_markets = kpi.get_event_markets("KXBTCMINY-25").append(kpi.get_event_markets("KXBTCMAXY-25"))
    enriched_positions = enriched_position_df(positions, btc_markets)
    # enriched_positions['marked_vol'] = enriched_positions['strike'].apply(lambda x: spline(x))
    enriched_positions.to_pickle("app_data/enriched_positions.pkl")

    # pos = Positions(enriched_positions, balance)
    # btc_markets.to_pickle("app_data/btc_markets.pkl")
    # pos.to_pickle()

    # construct btc underlying object
    # btc_underlying = Underlying("BTC-USD")
    # btc_underlying.to_pickle("app_data/btc_underlying.pkl")

    # strikes = np.array([50_000, 60_000, 70_000, 125_000,
    #                     150_000, 160_000, 180_000, 200_000,
    #                     250_000, 300_000, 500_000])# enriched_positions['strike'].unique()
    # vols = np.array([0.67, 0.55, 0.52, .62,
    #                  .65, .77, .83, .94,
    #                  1.373])
    strikes = np.array([.25, .5, .75,  1, 1.25, 1.5,  2,  5])
    vols    = np.array([.63, .6, .51, .5, .52,  .56, .58, 1])
    # fit a spline to the data

    # # Fit spline (s=0 ensures it passes through all points)
    # spline = UnivariateSpline(strikes, vols, s=0)
    # spline.set_smoothing_factor(0)  # explicitly no smoothing
    # spline._ext = 3  # extrapolate beyond range
    #
    # # apply spline for each strike in enriched_positions

    # pickle spline
    # with open("app_data/spline.pkl", "wb") as f:
    #     pickle.dump(spline, f)

    orders = kpi.get_orders()
    orders.to_pickle('app_data/orders.pkl')

    pass


