import kalshi_api.main as kpi
import numpy as np
import pandas as pd
from financepy.products.equity.equity_one_touch_option import EquityOneTouchOption
from financepy.products.fx.fx_one_touch_option import FXOneTouchOption
from pricing_and_risk import one_touch_option_price, implied_volatility_one_touch, one_touch_option_delta
import datetime as dt
import yfinance as yf

def get_stock_price(ticker):
    stock = yf.Ticker(ticker)
    return stock.history(period="1d")["Close"].iloc[-1]

class Market:
    def __init__(self, ticker):
        self.ticker = ticker

    @property
    def spot(self):
        return get_stock_price(self.ticker)


class Positions:
    def __init__(self, positions_df, balance):
        self.positions_df = positions_df
        self.balance = balance

    def get_positions(self):
        return self.positions_df

    def get_balance(self):
        return self.balance

    def to_dict(self):
        return {
            "positions_df": self.positions_df.to_dict(orient="records"),
            "balance": self.balance
        }

    @property
    def spot(self):
        return get_stock_price('BTC-USD')
    


    def to_pickle(self, path="app_data/positions.pkl"):
        import pickle
        with open(path, "wb") as f:
            pickle.dump(self.to_dict(), f)

    @classmethod
    def from_pickle(cls, path="app_data/positions.pkl"):
        import pickle
        import pandas as pd
        with open(path, "rb") as f:
            state = pickle.load(f)
        df = pd.DataFrame(state["positions_df"])
        balance = state["balance"]
        return cls(df, balance)

    @staticmethod
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
        enriched_df['vol_mark'] = .5
        # strike is whichever is not nan
        enriched_df['strike'] = enriched_df.apply(
            lambda row: row['cap_strike'] if pd.notna(row['cap_strike']) else row['floor_strike'],
            axis=1
        )
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
                row['vol_mark']
            ),
            axis=1
        )
        enriched_df['position_delta'] = enriched_df['position'] * enriched_df['delta_by_mid'] * spot * .01

        return enriched_df

    @property
    def risk_df(self):
        positions = self.positions_df.copy()
        positions['collateral_value'] = np.where(
            positions['position'] > 0,
            (positions['mid']) * positions['position'].abs() / 100,
            (100 -positions['mid']) * positions['position'].abs() / 100
        )
        risk_df = positions[['subtitle', 'strike', 'position', 'mid', "implied_vol_bid",
                             'implied_vol_mid', 'implied_vol_ask', 'collateral_value', 'delta_by_mid', 'position_delta']].copy()
        return risk_df






if __name__ == "__main__":
    # print balance
    balance = kpi.get_balance()
    # pull in data from kalshi
    positions = kpi.get_positions()

    # get enriched positions
    btc_markets = kpi.get_event_markets("KXBTCMINY-25").append(kpi.get_event_markets("KXBTCMAXY-25"))
    enriched_positions = Positions.enriched_position_df(positions, btc_markets)

    pos = Positions(enriched_positions, balance)
    btc_markets.to_pickle("app_data/btc_markets.pkl")
    pos.to_pickle()



    # create corresponding products

    # price

    # implied volatility

    # pickle


    pass

