import pandas as pd
from kalshi_api import KalshiSession, snap_markets

BINARY_TICKERS = ["ZYNBAN-24", "TWOW-25", "SUPERCON", "UNIPRESIDENT-24DEC31"]

def main():
    markets = snap_markets(KalshiSession())
    markets = pd.DataFrame(markets)
    binary_markets = markets[markets['event_ticker'].isin(BINARY_TICKERS)]

    # save to csv
    binary_markets.to_csv('markets.csv')


if __name__ == "__main__":
    main()
