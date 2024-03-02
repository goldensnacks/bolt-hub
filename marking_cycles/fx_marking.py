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


def mark_vol_surface(crosses = None):
    if crosses is None:
        crosses = ['eurusd', 'usdjpy']
    urls =  {
        'eurusd': 'https://cmegroup-tools.quikstrike.net/User/QuikStrikeView.aspx?viewitemid=FXOTC&pid=350&insid=118451761&qsid=6c17fa3e-c7d8-4665-9134-071371ff1187',
        'usdjpy': 'https://cmegroup-tools.quikstrike.net/User/QuikStrikeView.aspx?pid=355&pf=61&viewitemid=FXOTC&insid=118463761&qsid=8e7c1f6f-8d11-4879-a826-b989dbc4807c'
    }

    for cross in crosses:
        sec = get_security(cross)
        sec.vol_surface_by_delta = get_vol_surface(urls[cross])


def mark_decay_curve():
    pass

if __name__ == "__main__":
    # usd = Security('usd', Currency())
    # usd.country = 'united-states'
    #
    # jpy = Security('jpy', Currency())
    # jpy.country = 'japan'
    # usdjpy = Security('usdjpy', Cross())
    # usdjpy.asset =  get_security('jpy')
    # usdjpy.funding_asset =  get_security('usd')
    #
    #
    # eur = Security('eur', Currency())
    # eur.country = 'germany'
    # eurusd = Security('eurusd', Cross())
    # eurusd.asset =  get_security('jpy')
    # eurusd.funding_asset =  get_security('usd')

    # mark_usd_spots()
    mark_vol_surface()
    mark_curve()

    sec = get_security('usdjpy')

    vs = sec.vol_surface_by_delta
    vs2 = sec.vol_surface_by_strike
    vs3 = sec.vol_surface_as_fn
    mark_usd_spots()
    mark_vol_surface()
    mark_curve()

    sec = get_security('usdjpy')

    vs = sec.vol_surface_by_delta
    vs2 = sec.vol_surface_by_strike
    vs3 = sec.vol_surface_as_fn