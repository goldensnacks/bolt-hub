import logging
from datetime import datetime
import numpy as np
import pandas as pd
from securities.graph import Security, get_security
from kalshi_api import KalshiSession, snap_markets
from tradables.pricing_helper_fns import convert_kalshi_date_to_datetime
from tradables.products import OneTouch, BinaryOption


def assign_security(market):
    def is_one_touch(market):
        return market['title'].lower().find('minimum') != -1 or market['title'].lower().find('maximum') != -1
    if is_one_touch(market):
        return Security(market.name, OneTouch())
    else:
        return Security(market.name, BinaryOption())


def assign_underlier(market, enabled = None):
    if enabled is None:
        enabled = [ "EURUSD", "USDJPY"]
    if market['title'].lower().find('eur') != -1 and  "EURUSD" in enabled:
        return 'EURUSD'
    elif market['title'].lower().find('jpy') != -1 and "USDJPY" in enabled:
        return 'USDJPY'
    else:
        return None



def tradables_to_csv(securities):
    table = {}
    columns = ['price', 'floor_strike', 'cap_strike', 'spot', 'min_vol', 'max_vol', 'tenor', 'expiry', 'funding', 'underlier']
    for sec in securities:
        try:
            expiry = sec.expiry
            spot = sec.underlier.spot
            tenor = sec.tenor
            min_vol = sec.min_vol
            max_vol = sec.max_vol
            floor_strike = sec.floor_strike
            cap_strike = sec.cap_strike
            funding = sec.funding
            underlier = sec.underlier.name
            price = sec.price
            row = dict(zip(columns, [price, floor_strike, cap_strike, spot, min_vol, max_vol, tenor, expiry, funding, underlier]))
            table[f'{floor_strike}_{cap_strike}'] = row
        except Exception as e:
            print(f"Failed to add to table with error {e}")
    df = pd.DataFrame(table).T
    df.to_csv('tradables.csv')



def mark_kalshi_tradables():
    # create session
    session = KalshiSession()

    # snap markets
    markets = snap_markets(session)
    markets = pd.DataFrame(markets)
    markets['underlier'] = markets.apply(assign_underlier, axis = 1)
    markets = markets[~markets['underlier'].isna()]

    # # fetch or create tradables
    # markets['strike'] = markets.apply (lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)

    sec_list = []
    markets = markets.set_index('ticker')
    for ticker in markets.index:
        data = markets.loc[ticker]
        sec = assign_security(data)
        if 'strike_type' in data.keys():
            if data['strike_type'] == 'floor':
                sec.floor_strike = np.nan
                sec.cap_strike = data.loc['floor_strike']
            elif data['strike_type'] == 'greater':
                sec.cap_strike = np.nan
                sec.floor_strike = data.loc['floor_strike']
        else:
            sec.cap_strike = data.loc['cap_strike']
            sec.floor_strike = data.loc['floor_strike']
        underlier = data.loc['underlier']
        underlier = get_security(underlier)
        sec.underlier = underlier
        sec.expiry = convert_kalshi_date_to_datetime(data.loc['close_time'])
        sec.funding = .05
        sec_list.append(sec)

    # update csv
    tradables_to_csv(sec_list)


if __name__ == "__main__":
    res = mark_kalshi_tradables()