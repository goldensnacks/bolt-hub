import panel as pn
import pandas as pd
import seaborn as sns
import holoviews as hv
import pickle
import numpy as np
import matplotlib.pyplot as plt
from crypto_book.btc_snap import get_stock_price
import crypto_book.panel_helpers as ph
from crypto_book.panel_helpers import show_df
import os
import dotenv
from typing import Optional, Dict, Any
import logging

dotenv.load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

APP_DATA_PATH = os.getenv("APP_DATA_PATH", "app_data")

class TradingDashboard:
    """
    A class-based dashboard for displaying crypto trading data.
    
    This dashboard shows positions, greeks, balance, orders, and volatility analysis
    for crypto trading activities.
    """
    
    def __init__(self, underlier: str = "BTC"):
        """
        Initialize the trading dashboard.
        
        Parameters
        ----------
        underlier : str, optional
            The underlying asset (default: "BTC")
        """
        self.underlier = underlier
        self.positions_df = None
        self.balance = None
        self.spot = None
        self.greeks = None
        self.orders = None
        
        # Load data on initialization
        self._load_data()
        
    def _load_data(self):
        """Load all required data from pickle files."""
        try:
            # Load positions
            self.positions_df = pd.read_pickle(f'{APP_DATA_PATH}/enriched_positions.pkl')
            logger.info(f"Loaded positions data: {self.positions_df.shape}")
            
            # Filter positions by underlier if the column exists
            if 'underlier' in self.positions_df.columns:
                original_count = len(self.positions_df)
                self.positions_df = self.positions_df[self.positions_df['underlier'] == self.underlier]
                filtered_count = len(self.positions_df)
                logger.info(f"Filtered positions for {self.underlier}: {filtered_count}/{original_count} positions")
            else:
                logger.warning("No 'underlier' column found in positions data - showing all positions")
            
            # Load balance
            with open(f'{APP_DATA_PATH}/balance.pkl', 'rb') as f:
                self.balance = pickle.load(f)
            logger.info(f"Loaded balance: ${self.balance:,.2f}")
            
            # Load greeks
            with open(f'{APP_DATA_PATH}/greeks.pkl', 'rb') as f:
                self.greeks = pickle.load(f)
            logger.info("Loaded greeks data")
            
            # Filter greeks by underlier if the column exists
            if 'underlier' in self.greeks.columns:
                original_count = len(self.greeks)
                self.greeks = self.greeks[self.greeks['underlier'] == self.underlier]
                filtered_count = len(self.greeks)
                logger.info(f"Filtered greeks for {self.underlier}: {filtered_count}/{original_count} records")
            else:
                logger.warning("No 'underlier' column found in greeks data - showing all greeks")
            
            # Load orders
            self.orders = pd.read_pickle(f"{APP_DATA_PATH}/orders.pkl")
            logger.info(f"Loaded orders data: {self.orders.shape}")
            
            # Filter orders by underlier if the column exists
            if 'underlier' in self.orders.columns:
                original_count = len(self.orders)
                self.orders = self.orders[self.orders['underlier'] == self.underlier]
                filtered_count = len(self.orders)
                logger.info(f"Filtered orders for {self.underlier}: {filtered_count}/{original_count} orders")
            else:
                logger.warning("No 'underlier' column found in orders data - showing all orders")
            
            # Get current spot price
            self.spot = get_stock_price(f"{self.underlier}-USD")
            logger.info(f"Current {self.underlier} spot: ${self.spot:,.2f}")
            
        except FileNotFoundError as e:
            logger.error(f"Data file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            raise
    
    def algo_trading_df(self, enriched_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Create algorithm trading dataframe with spread calculations.
        
        Parameters
        ----------
        enriched_df : pd.DataFrame, optional
            Enriched positions dataframe. If None, uses self.positions_df
            
        Returns
        -------
        pd.DataFrame
            DataFrame with spread calculations
        """
        if enriched_df is None:
            enriched_df = self.positions_df
            
        ret_df = enriched_df.copy()
        ret_df['spread_to_marked'] = ret_df['vol_mark'] * 100 - ret_df['mid']
        return ret_df
    
    def algo_trading_df_widget(self):
        """
        Widget for selecting and ordering columns & display the dataframe.
        """
        algo_trading_df = self.algo_trading_df()

        columns = list(algo_trading_df.columns)
        cross_selector = pn.widgets.CrossSelector(
            name="Select and order columns",
            options=columns,
            value=["strike", "vol_mark", "implied_vol_mid", "implied_vol_ask", "implied_vol_bid"],
            size=10,
            width=400,
        )

        @pn.depends(cross_selector.param.value)
        def display_selected_columns(selected_columns):
            if not selected_columns:
                return pn.pane.Alert("No columns selected.", alert_type="warning")
            selected_df = algo_trading_df[selected_columns]
            
            # Create Tabulator with default sorting by strike if available
            if 'strike' in selected_df.columns:
                return pn.widgets.Tabulator(selected_df, height=300, sorters=[{'field': 'strike', 'dir': 'asc'}])
            else:
                return pn.widgets.Tabulator(selected_df, height=300)

            # return algo_trading_df[selected_columns]

        return pn.Column(
            "## Algorithmic Trading Data",
            cross_selector,
            display_selected_columns,
            sizing_mode="stretch_width"
        )

    
    def get_vol_smile_plot(self, enriched_df: Optional[pd.DataFrame] = None) -> pn.pane.Matplotlib:
        """
        Create volatility smile plot.
        
        Parameters
        ----------
        enriched_df : pd.DataFrame, optional
            Enriched positions dataframe. If None, uses self.positions_df
            
        Returns
        -------
        pn.pane.Matplotlib
            Panel matplotlib pane with volatility smile plot
        """
        if enriched_df is None:
            enriched_df = self.positions_df
            
        if enriched_df is None or len(enriched_df) == 0:
            # Create empty plot with message
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'No {self.underlier} data available', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=14)
            ax.set_title(f'{self.underlier} Volatility Smile')
            ax.set_ylabel('Implied Volatility')
            ax.set_xlabel('Strike Price')
            plt.tight_layout()
            return pn.pane.Matplotlib(fig)
            
        enriched_df = enriched_df.copy()
        
        # Check if required columns exist
        required_cols = ['strike', 'implied_vol_ask', 'implied_vol_mid', 'implied_vol_bid', 'vol_mark']
        missing_cols = [col for col in required_cols if col not in enriched_df.columns]
        if missing_cols:
            # Create error plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f'Missing columns: {", ".join(missing_cols)}', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12, color='red')
            ax.set_title(f'{self.underlier} Volatility Smile')
            ax.set_ylabel('Implied Volatility')
            ax.set_xlabel('Strike Price')
            plt.tight_layout()
            return pn.pane.Matplotlib(fig)
        
        vols_df = enriched_df[required_cols].dropna().set_index('strike')
        vols_df.sort_index(inplace=True)

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(vols_df.index, vols_df['implied_vol_bid'], label='Bid', marker='o')
        ax.plot(vols_df.index, vols_df['implied_vol_mid'], label='Mid', marker='s')
        ax.plot(vols_df.index, vols_df['implied_vol_ask'], label='Ask', marker='^')
        ax.plot(vols_df.index, vols_df['vol_mark'], label='Marked', marker='*', linewidth=2)

        ax.set_title(f'{self.underlier} Volatility Smile')
        ax.set_ylabel('Implied Volatility')
        ax.set_xlabel('Strike Price')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Add spot price line
        if self.spot:
            ax.axvline(x=self.spot, color='red', linestyle='--', label='Spot Price', linewidth=2)

        plt.tight_layout()
        return pn.pane.Matplotlib(fig)
    
    def create_balance_widget(self) -> pn.pane.Str:
        """
        Create balance display widget.
        
        Returns
        -------
        pn.pane.Str
            Panel string pane showing balance
        """
        if self.balance is None:
            return pn.pane.Str("Balance: Loading...")
        return pn.pane.Str(f"Balance: ${self.balance:,.2f}")
    
    def create_spot_widget(self) -> pn.pane.Str:
        """
        Create spot price display widget.
        
        Returns
        -------
        pn.pane.Str
            Panel string pane showing current spot price
        """
        if self.spot is None:
            return pn.pane.Str(f"{self.underlier} Spot: Loading...")
        return pn.pane.Str(f"{self.underlier} Spot: ${self.spot:,.2f}")
    
    def create_dashboard(self) -> pn.Column:
        """
        Create the main dashboard layout.
        
        Returns
        -------
        pn.Column
            Panel column containing the complete dashboard
        """
        # Create widgets
        balance_widget = self.create_balance_widget()
        spot_widget = self.create_spot_widget()
        
        # Create tabs with data validation
        tabs = []
        
        # Portfolio Greeks tab
        if self.greeks is not None and len(self.greeks) > 0:
            tabs.append(("Portfolio Greeks", show_df(self.greeks)))
        else:
            tabs.append(("Portfolio Greeks", pn.pane.Alert(f"No {self.underlier} greeks data available", alert_type="warning")))
        
        # Algo Trading tab
        tabs.append(("Algo Trading", self.algo_trading_df_widget()))
        # Volatility Smile tab
        tabs.append(("Volatility Smile", self.get_vol_smile_plot()))
        
        # Orders tab
        if self.orders is not None and len(self.orders) > 0:
            tabs.append(("Orders", show_df(self.orders)))
        else:
            tabs.append(("Orders", pn.pane.Alert(f"No {self.underlier} orders data available", alert_type="warning")))
        
        # Create dashboard layout
        dashboard = pn.Column(
            f"# {self.underlier} Trading Dashboard",
            pn.Row(
                spot_widget,
                pn.Spacer(sizing_mode="stretch_width"),
                balance_widget
            ),
            pn.Tabs(*tabs, active=1),
            sizing_mode="stretch_width"
        )
        
        return dashboard
    
    def refresh_data(self):
        """Refresh all data by reloading from files."""
        logger.info("Refreshing dashboard data...")
        self._load_data()
        logger.info("Data refresh complete")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the dashboard.
        
        Returns
        -------
        Dict[str, Any]
            Dictionary containing summary statistics
        """
        if self.positions_df is None:
            return {}
            
        return {
            "total_positions": len(self.positions_df),
            "total_notional": self.positions_df.get('notional', pd.Series([0])).sum(),
            "total_delta": self.positions_df.get('position_delta', pd.Series([0])).sum(),
            "balance": self.balance,
            "spot_price": self.spot,
            "last_updated": pd.Timestamp.now()
        }


# Create a default dashboard instance for backward compatibility
dashboard = TradingDashboard().create_dashboard()

# Export the class for use in other modules
__all__ = ['TradingDashboard', 'dashboard']
