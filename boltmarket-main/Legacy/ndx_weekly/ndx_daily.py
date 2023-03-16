import kalshi
import numpy as np
from MDAPI.underlier import YFinanceSource
from autotrader import AutoTrader, MarketHours
from cluster_server import main_loop, Market

if __name__ == "__main__":
    kalshi = kalshi.Session(email="jacobreedijk@gmail.com", password="DJDSOLwr69?")
    at = AutoTrader(kalshi, 3, MarketHours(open_hour=10, close_hour=15))
    ndx_market = Market("NASDAQ100", 0, 1, kalshi)
    main_loop(ndx_market, at, freq = 0)
