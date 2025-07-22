"""
Dashboards module for crypto trading applications.

This module contains dashboard components and trading visualization tools.
"""

from .trading_app import (
    algo_trading_df,
    get_vol_smile_plot,
    dashboard
)

__all__ = [
    'algo_trading_df', 
    'get_vol_smile_plot',
    'dashboard'
] 