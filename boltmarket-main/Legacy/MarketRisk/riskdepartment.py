import kalshi
from autotrader import AutoTrader, MarketHours
from cluster_server import Market, risk_loop

if __name__ == "__main__":
    kalshi = kalshi.Session(email="jacobreedijk@gmail.com", password="DJDSOLwr69?")
    at = AutoTrader(kalshi, 5, MarketHours(open_hour=10, close_hour=13))
    ndx_market = Market("NASDAQ100", 0, 5, kalshi)
    risk_loop(ndx_market)

