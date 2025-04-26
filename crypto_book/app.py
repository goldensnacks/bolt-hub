import panel as pn
import pandas as pd   # only needed to type‑hint or test the function
import seaborn as sns
import pickle
import numpy as np
from btc_snap import Positions

pn.extension('tabulator')        # activate Panel and load the Tabulator widget

def show_df(df: pd.DataFrame,
            height: int = 400,
            width: int = 800,
            sizing_mode: str = "stretch_width") -> pn.widgets.Tabulator:
    """
    Return a Panel `Tabulator` widget that displays `df`.

    Parameters
    ----------
    df : pandas.DataFrame
        The data you want to view.
    height, width : int, optional
        Pixel dimensions of the table (ignored if you set `sizing_mode` to stretch).
    sizing_mode : str, optional
        'stretch_width', 'stretch_both', 'fixed', etc.  See Panel docs.

    Returns
    -------
    pn.widgets.Tabulator
        A Panel object you can `.servable()` or embed in layouts.
    """
    return pn.widgets.Tabulator(
        df,
        height=height,
        width=width,
        sizing_mode=sizing_mode,
        pagination='remote',    # keeps large tables snappy
        theme='simple',         # or 'site', 'material', etc.
    )

# df = sns.load_dataset("tips")        # sample data
positions = Positions.from_pickle("app_data/positions.pkl")  # load positions from pickle

positions_df = positions.get_positions()
balance = positions.get_balance()

spot = positions.spot


# Or as part of a dashboard script
# show balance in top right corner
balance_widget = pn.pane.Str(f"Balance: ${balance:,.2f}")
# Add the balance widget to the top right corner


events = pd.read_pickle("app_data/events.pkl")  # load events from pickle
# only events who's event_ticker is in positions_df['ticker']
# events = events[events['event_ticker'].isin(positions_df['ticker'])]
# btc_markets = pd.read_pickle("app_data/btc_markets.pkl")  # load btc markets from pickle
risk_df = positions.risk_df
# Add totals row to risk_df
risk_df.loc['Total'] = risk_df.select_dtypes(include=[np.number]).sum()
risk_df.loc['Total', 'implied_vol_mid'] = ''
risk_df.loc['Total', 'subtitle'] = 'Total'
risk_df.loc['Total', 'strike'] = None



dashboard = pn.Column(
    "# BTC Positions",
    pn.pane.Str(f"BTC Spot: ${spot:,.2f}"),
    pn.Row(pn.Spacer(sizing_mode="stretch_width"), balance_widget),
    show_df(positions_df),
    show_df(risk_df),
)

dashboard.servable()
