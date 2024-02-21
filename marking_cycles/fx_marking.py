from datetime import datetime
from financepy.utils.date import Date
import pandas as pd
import requests
from bs4 import BeautifulSoup
from ib_insync import IB, Forex
import pandas as pd
import re
#import time deltas
from datetime import timedelta
from securities.graph import get_security, Security
from tradables.underliers import Currency

def currency_to_usd_cross(currency: str):
    cross_map = {
        'eur': 'EURUSD',
        'jpy': 'USDJPY'
    }
    return cross_map[currency]

# currency marks
def get_fx_spots(tickers):
    # Connect to the Interactive Brokers TWS (make sure TWS is running and API access is enabled)
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)  # Make sure the port and clientId match your TWS settings

    # Define the contract for EURUSD
    contracts = [Forex(ticker) for ticker in tickers]
    # Request market data
    contracts = [ib.reqTickers(contract) for contract in contracts]

    # Print the spot price (last price) for EURUSD
    spots = {ticker:contract[0].marketPrice() for ticker, contract in zip(tickers, contracts)}
    ib.disconnect()
    return spots


def mark_usd_spots(currencies = None):
    if currencies is None:
        currencies = ['eur', 'jpy']


    spots = get_fx_spots([currency_to_usd_cross(cur) for cur in currencies])
    for sec in currencies:
        sec = get_security(sec)
        sec.value_in_usd = spots[currency_to_usd_cross(sec.name)]

def get_curve(country: str):
    main_url = "https://www.worldgovernmentbonds.com/country/" + country
    result = requests.get(main_url)
    soup = BeautifulSoup(result.text, 'html.parser')
    vals = soup.find_all("script", type="text/javascript")
    country = country.replace('-', ' ')
    pudb.set_trace()
    for val in vals:
        if f'{country} yield curve' in val.text.lower():
            break

    data = val.get_text().split("series:")[1].split('data:')[1]
    matches = re.findall(r'\[(\d+),\s+(-?\d+\.\d+)\]', data)
    # Convert the matched pairs into a list of tuples
    pairs = [(datetime.today() + timedelta(30*int(day)), float(rate)) for day, rate in matches]
    # Create a pandas Series
    series = pd.Series(dict(pairs))
    return series

def mark_curve(currencies = None):
    if currencies is None:
        currencies = ['usd', 'eur', 'jpy']
    for currency in currencies:
        sec = get_security(currency)
        curve = get_curve(sec.country)
        sec.curve_pairs = curve

# pair marks
def mark_vol_surface():
    pass

def mark_decay_curve():
    pass

if __name__ == "__main__":
    while True:
        # mark_usd_spots()
        mark_curve()
