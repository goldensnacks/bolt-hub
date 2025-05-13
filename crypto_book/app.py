import panel as pn
import pandas as pd   # only needed to type‑hint or test the function
import seaborn as sns
import pickle
import numpy as np
from btc_snap import Positions, Underlying
import panel_helpers as ph
from panel_helpers import show_df

# df = sns.load_dataset("tips")        # sample data
positions = Positions.from_pickle("app_data/positions.pkl")  # load positions from pickle

positions_df = positions.get_positions()
balance = positions.get_balance()

# spot = positions.spot
underlying = Underlying.from_pickle("app_data/btc_underlying.pkl")  # load underlying from pickle
spot = underlying.spot

# orders
orders = pd.read_pickle("app_data/orders.pkl")  # load orders from pickle


# Or as part of a dashboard script
# show balance in top right corner
balance_widget = pn.pane.Str(f"Balance: ${balance:,.2f}")
# Add the balance widget to the top right corner


events = pd.read_pickle("app_data/events.pkl")  # load events from pickle
# only events who's event_ticker is in positions_df['ticker']
# events = events[events['event_ticker'].isin(positions_df['ticker'])]
# btc_markets = pd.read_pickle("app_data/btc_markets.pkl")  # load btc markets from pickle
risk_df = ph.get_risk_df(positions)



dashboard = pn.Column(
    "# BTC Positions",
    pn.pane.Str(f"BTC Spot: ${spot:,.2f}"),
    pn.Row(pn.Spacer(sizing_mode="stretch_width"), balance_widget),
    show_df(positions_df),
    show_df(risk_df),
    show_df(orders),
)

dashboard.servable()
