import pandas as pd  # only needed to type‑hint or test the function
import numpy as np
import panel as pn

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

def get_risk_df(positions):
    risk_df = positions.risk_df
    # Add totals row to risk_df
    risk_df.loc['Total'] = risk_df.select_dtypes(include=[np.number]).sum()
    risk_df.loc['Total', 'implied_vol_mid'] = ''
    risk_df.loc['Total', 'mid'] = ''
    risk_df.loc['Total', 'subtitle'] = 'Total'
    risk_df.loc['Total', 'strike'] = None
    return risk_df



