# Dashboards Module

This module contains dashboard components and trading visualization tools for the crypto trading application.

## Structure

```
dashboards/
├── __init__.py          # Module initialization and exports
├── trading_app.py       # Main BTC trading dashboard
└── README.md           # This file
```

## Components

### trading_app.py
The main trading dashboard that provides:
- Portfolio Greeks calculation (`portfolio_greeks_df`)
- Algorithmic trading data preparation (`algo_trading_df`)
- Volatility smile visualization (`get_vol_smile_plot`)
- Complete dashboard interface (`dashboard`)

## Usage

### Running the Dashboard

From the project root (recommended) - with autoreload for development:
```bash
python run_dashboard.py
```

Disable autoreload (useful for production):
```bash
python run_dashboard.py --no-autoreload
```

Use custom port:
```bash
python run_dashboard.py --port 5006
```

Or make it executable and run directly:
```bash
chmod +x run_dashboard.py
./run_dashboard.py
```

**Features:**
- **Autoreload**: Automatically refreshes the dashboard when you make changes to the code
- **Configurable Port**: Default port 5006, can be changed with `--port` flag
- **Production Ready**: Can disable autoreload with `--no-autoreload` flag

### Importing Functions

```python
# Recommended: Use absolute imports
from crypto_book.dashboards import portfolio_greeks_df, algo_trading_df
from crypto_book.dashboards.trading_app import get_vol_smile_plot

# Alternative: Import specific functions
from crypto_book.dashboards.trading_app import dashboard
```

## Dependencies

- panel: For dashboard interface
- pandas: For data manipulation
- matplotlib: For plotting
- seaborn: For enhanced plotting
- holoviews: For interactive visualizations

## Data Requirements

The dashboard expects the following data files in `app_data/`:
- `enriched_positions.pkl`: Enriched position data
- `balance.pkl`: Account balance
- `BTC-USD.pkl`: Current BTC spot price
- `greeks.pkl`: Portfolio Greeks
- `orders.pkl`: Current orders 