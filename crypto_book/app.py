import panel as pn
import pandas as pd   # only needed to type‑hint or test the function
import seaborn as sns
import pickle
import numpy as np
from btc_snap import Underlying
import panel_helpers as ph
from panel_helpers import show_df

risk_columns = ['subtitle', 'strike', 'position', 'mid', "implied_vol_bid",
                             'implied_vol_mid', 'implied_vol_ask', 'collateral_value', 'delta_by_mid', 'position_delta',
                'position_delta_marked']

def get_risk_df(enriched_df):
    ret_df = enriched_df.copy()
    ret_df = ret_df[risk_columns]
    # Add totals row to risk_df
    ret_df.loc['Total'] = ret_df.select_dtypes(include=[np.number]).sum()
    ret_df.loc['Total', 'implied_vol_mid'] = ''
    ret_df.loc['Total', 'mid'] = ''
    ret_df.loc['Total', 'subtitle'] = 'Total'
    ret_df.loc['Total', 'strike'] = None
    return ret_df

def get_trading_df(enriched_df):
    trading_df = enriched_df.copy()
    trading_df = trading_df[['ticker', 'strike', 'position', "yes_bid", 'mid', 'yes_ask','implied_vol_mid','vol_mark']]
    # marked vol mid

    return trading_df



positions_df =  pd.read_pickle('app_data/enriched_positions.pkl') # positions.get_positions()
with open('app_data/balance.pkl', 'rb') as f:
    balance = pickle.load(f)

# spot = positions.spot
underlying = Underlying.from_pickle("app_data/btc_underlying.pkl")  # load underlying from pickle
spot = underlying.spot



# Or as part of a dashboard script
# show balance in top right corner
balance_widget = pn.pane.Str(f"Balance: ${balance:,.2f}")
# Add the balance widget to the top right corner
events = pd.read_pickle("app_data/events.pkl")  # load events from pickle

# trading df
trading_df = get_trading_df(positions_df)


# orders
orders = pd.read_pickle("app_data/orders.pkl")  # load orders from pickle


dashboard = pn.Column(
    "# BTC Positions",
    pn.pane.Str(f"BTC Spot: ${spot:,.2f}"),
    pn.Row(pn.Spacer(sizing_mode="stretch_width"), balance_widget),
    show_df(positions_df),
    show_df(get_risk_df(positions_df)),
    show_df(orders),
    show_df(trading_df),
)

dashboard.servable()
