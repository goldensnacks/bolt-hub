from datetime import datetime
import requests
from bs4 import BeautifulSoup
from ib_insync import IB, Forex
import pandas as pd
import re
#import time deltas
from datetime import timedelta
from securities.graph import get_security, Security
from tradables.underliers import Cross, Currency


def mark_and_warn_if_failed(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print(f"Failed to mark {func.__name__} with error {e}")
    return wrapper

def currency_to_usd_cross(currency: str):
    currency = currency.lower()
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


@mark_and_warn_if_failed
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

@mark_and_warn_if_failed
def mark_curve(currencies = None):
    if currencies is None:
        currencies = ['usd', 'eur', 'jpy']
    for currency in currencies:
        sec = get_security(currency)
        curve = get_curve(sec.country)
        sec.curve_pairs = curve

# pair marks
def get_vol_surface(url):
    response = requests.post(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    vals = soup.find_all("a", caption=re.compile("(.*) Tenor (.*)"))
    rows = []
    for val in vals:
        val = str(val)
        tenor, delta, type, vol = re.match(r".*=\"(.*) Tenor (.*) Delta (.*) Details.*>(.*)<.*",
                                           val).groups()  # , vol
        row = {'tenor': tenor.lower(), 'delta': delta, "type": type, "vol": vol}
        rows.append(row)
    df = pd.DataFrame(rows)
    df['vol'] = [vol.replace(',','') for vol in df['vol']]
    df['vol'] = [float(vol) for vol in df['vol']]
    df['type'] = [type[0] for type in df.type]
    df['delta'] = df['delta'] + df['type']
    df = df.pivot(index='tenor', columns='delta', values='vol')
    sorted_columns = sorted(df.columns)
    df = df.reindex(columns=sorted_columns)

    # Sample DataFrame index with time period strings
    index_data = df.index

    # Dictionary to map time period strings to corresponding numbers of days
    period_to_days = {
        'd': 1,  # 1 day
        'w': 7,  # 1 week = 7 days
        'm': 30,  # 1 month = 30 days (approximation)
        'y': 365  # 1 year = 365 days (approximation)
    }

    # Convert index to pandas Timedelta objects
    timedelta_index = pd.to_timedelta([int(period[:-1]) * period_to_days[period[-1]] for period in index_data],
                                      unit='d')
    df.index = timedelta_index
    sorted_index = sorted(df.index)
    df = df.reindex(index=sorted_index)
    return df


@mark_and_warn_if_failed
def mark_vol_surface(crosses = None):
    if crosses is None:
        crosses = ['eurusd']
    urls =  {
        'eurusd': "https://cmegroup-tools.quikstrike.net/User/QuikStrikeView.aspx?pid=350&pf=61&viewitemid=FXOTC&insid=121507361&qsid=76af1647-2ae8-48c1-9701-d8a2c5f1fd72",
        'usdjpy': "https://cmegroup-tools.quikstrike.net/User/QuikStrikeView.aspx?pid=355&pf=61&viewitemid=FXOTC&insid=121851682&qsid=00f0ba66-b8c7-4a90-80e5-27194dc29d67"
    }
    for cross in crosses:
        sec = get_security(cross)
        sec.vol_surface_by_delta = get_vol_surface(urls[cross])


@mark_and_warn_if_failed
def mark_decay_curve(crosses = None):
    if crosses is None:
        crosses = ['eurusd']
    curves = pd.read_csv('decay_curves.csv')
    for cross in crosses:
        sec = get_security(cross)
        sec.intraday_weights = curves[cross]


if __name__ == "__main__":
    create_new_securities = False
    if create_new_securities:
        usd = Security('usd', Currency())
        eur = Security('eur', Currency())
        jpy = Security('jpy', Currency())

        # crosses
        eurusd = Security('eurusd', Cross())
        usdjpy = Security('usdjpy', Cross())

        # set assets
        usd.value_in_usd = 1
        eurusd.funding_asset = eur
        eurusd.asset = usd
        usdjpy.funding_asset = usd
        usdjpy.asset = jpy


    # mark_usd_spots()
    mark_vol_surface()
    # mark_curve()
    # mark_decay_curve()
