import panel as pn
import pandas as pd   # only needed to type‑hint or test the function
import seaborn as sns
import holoviews as hv
import pickle
import numpy as np
import matplotlib.pyplot as plt
from btc_snap import get_stock_price
import panel_helpers as ph
from panel_helpers import show_df
import os
import dotenv
dotenv.load_dotenv()

APP_DATA_PATH = os.getenv("APP_DATA_PATH")

risk_columns = [ 'strike',          'position',         'mid', "implied_vol_bid",
                 'implied_vol_mid', 'implied_vol_ask', 'collateral_value',
                 'delta_by_mid', 'position_delta', 'position_delta_marked']

algo_trading_columns = [ 'strike',          'position',         'mid', "implied_vol_bid",
                         'implied_vol_mid', 'implied_vol_ask', 'collateral_value',
                         'delta_by_mid', 'position_delta', 'position_delta_marked', 'vol_mark',
                         'spread_to_marked',
                         ]

def portfolio_greeks_df(enriched_df):
    delta = enriched_df['position_delta'].sum()
    delta_marked = enriched_df['position_delta_marked'].sum()

    df = pd.DataFrame([{ 'delta_kalshi_implied_vols': delta,
                        'delta_marked_implied_vols': delta_marked,
                        'vega': 0,
                        'gamma': 0,
                        'theta': 0,
                       }]
                      )

    return df


def algo_trading_df(enriched_df):
    ret_df = enriched_df.copy()
    ret_df['spread_to_marked'] = ret_df['vol_mark'] * 100 - ret_df['mid']
    ret_df = ret_df[algo_trading_columns]

    return ret_df

def get_vol_smile_plot(enriched_df):
    enriched_df = enriched_df.copy()
    vols_df = enriched_df[['strike', 'implied_vol_ask', 'implied_vol_mid', 'implied_vol_bid', 'vol_mark']].dropna().set_index('strike')
    vols_df.sort_index(inplace=True)

    fig, ax = plt.subplots()

    ax.plot(vols_df.index, vols_df['implied_vol_bid'], label='Bid')
    ax.plot(vols_df.index, vols_df['implied_vol_mid'], label='Mid')
    ax.plot(vols_df.index, vols_df['implied_vol_ask'], label='Ask')
    ax.plot(vols_df.index, vols_df['vol_mark'], label='Marked')

    ax.set_title('Volatility Smile')
    ax.set_ylabel('Implied Volatility')
    ax.set_xlabel('Strike')
    ax.legend()

    # add a red verticle line at the spot price
    # Read BTC-USD spot from app_data/spot.pkl
    with open('app_data/BTC-USD.pkl', 'rb') as f:
        spot_price = pickle.load(f)
    ax.axvline(x=spot_price, color='red', linestyle='--', label='Spot Price')

    return pn.pane.Matplotlib(fig)

positions_df =  pd.read_pickle('app_data/enriched_positions.pkl') # positions.get_positions()

with open('app_data/balance.pkl', 'rb') as f:
    balance = pickle.load(f)

# spot = positions.spot
spot =  get_stock_price("BTC-USD")  # Assuming you have a function to get the current BTC price



# Or as part of a dashboard script
# show balance in top right corner
balance_widget = pn.pane.Str(f"Balance: ${balance:,.2f}")
# Add the balance widget to the top right corner
# events = pd.read_pickle("app_data/events.pkl")  # load events from pickle

# trading df
# trading_df = get_trading_df(positions_df)
greeks = portfolio_greeks_df(positions_df)


# orders
orders = pd.read_pickle("app_data/orders.pkl")  # load orders from pickle

dashboard = pn.Column(
    "# BTC Positions",
    pn.pane.Str(f"BTC Spot: ${spot:,.2f}"),
    show_df(greeks),
    pn.Row(pn.Spacer(sizing_mode="stretch_width"), balance_widget),
    # show_df(positions_df),
    show_df(algo_trading_df(positions_df)),
    get_vol_smile_plot(positions_df),

)

dashboard.servable()
