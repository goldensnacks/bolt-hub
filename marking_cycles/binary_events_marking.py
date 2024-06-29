from datetime import datetime
import numpy as np
import pandas as pd
from kalshi_api import KalshiSession, snap_markets
from securities.graph import Security, get_security
from tradables.underliers import Event
from tradables.products import SimpleEventBinary
BINARY_TICKERS = ["ZYNBAN-24", "TWOW-25", "SUPERCON", "UNIPRESIDENT-24DEC31"]


def assign_or_create_underlier(market):
    underlier = Security(market.get('event_ticker'), Event())

    # default decay curve

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Calculate the total number of days between start and end dates
    total_days = (end_date - start_date).days

    # Generate an array of timestamps using linspace
    timestamps = np.linspace(start_date.timestamp(), end_date.timestamp(), total_days)

    slope = -1 / (total_days - 1)
    intercept = 1
    linear_values = slope * (timestamps - timestamps[0]) + intercept

    # Convert timestamps back to datetime objects if needed
    underlier.decay_curve = pd.Series(linear_values, index=pd.to_datetime(timestamps, unit='s')).interpolate()

    underlier.start_date = start_date



def assign_or_create_tradable(market):
    tradable = Security(f'{market.get("event_ticker")}-tradable', SimpleEventBinary())
    tradable.expiry =  datetime(2024,12,31)# market.get('close_time')
    # tradable.tenor_in_days = (market.get('close_time') - datetime.utcnow()).days
    tradable.underlier = get_security(market.get('event_ticker'))

    print(tradable.price)


def main():
    markets = snap_markets(KalshiSession())
    markets = pd.DataFrame(markets)
    binary_markets = markets[markets['event_ticker'].isin(BINARY_TICKERS)]

    #convert to list of dicts
    binary_markets = binary_markets.to_dict(orient='records')

    for market in binary_markets:
        assign_or_create_underlier(market)
        assign_or_create_tradable(market)

    # save to csv
    binary_markets.to_csv('markets.csv')


if __name__ == "__main__":
    main()
