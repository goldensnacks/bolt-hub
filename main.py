import os
from cryptography.hazmat.primitives import serialization
import asyncio
from clients import KalshiHttpClient, KalshiWebSocketClient, Environment

import pandas as pd

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature

from api_functions import load_private_key_from_file, sign_pss_text


import requests
import datetime

# Get the current time
current_time = datetime.datetime.now()

# Convert the time to a timestamp (seconds since the epoch)
timestamp = current_time.timestamp()

# Convert the timestamp to milliseconds
current_time_milliseconds = int(timestamp * 1000)
timestampt_str = str(current_time_milliseconds)

# Load the RSA private key
private_key = load_private_key_from_file('mkt_key_2.txt')
method = "GET"
base_url = 'https://api.elections.kalshi.com'




def get_balance():
    path='/trade-api/v2/portfolio/balance'
    msg_string = timestampt_str + method + path

    sig = sign_pss_text(private_key, msg_string)
    headers = {
            'KALSHI-ACCESS-KEY': '9ef4bded-dca9-4121-aa72-845966544df3',
            'KALSHI-ACCESS-SIGNATURE': sig,
            'KALSHI-ACCESS-TIMESTAMP': timestampt_str
        }
    response = requests.get(base_url + path, headers=headers).json()
    try:
        balance = response['balance']
        return balance / 100
    except KeyError:
        print(response)


def get_positions():
    path='/trade-api/v2/portfolio/positions'
    msg_string = timestampt_str + method + path

    sig = sign_pss_text(private_key, msg_string)
    headers = {
            'KALSHI-ACCESS-KEY': '9ef4bded-dca9-4121-aa72-845966544df3',
            'KALSHI-ACCESS-SIGNATURE': sig,
            'KALSHI-ACCESS-TIMESTAMP': timestampt_str
        }
    response = requests.get(base_url + path, headers=headers).json()
    positions = response['market_positions']
    positions = pd.DataFrame(positions)
    # filter for where position is not 0
    positions = positions[positions['position'] != 0]
    return positions

def get_events():
    path='/trade-api/v2/events'
    msg_string = timestampt_str + method + path

    sig = sign_pss_text(private_key, msg_string)
    all_events = []
    count_events_found = 201
    cursor = None
    while not count_events_found < 200:
        headers = {
                'KALSHI-ACCESS-KEY': '9ef4bded-dca9-4121-aa72-845966544df3',
                'KALSHI-ACCESS-SIGNATURE': sig,
                'KALSHI-ACCESS-TIMESTAMP': timestampt_str
            }
        params = {'limit': '200', 'status':'open'}
        if cursor is not None:
            params['cursor'] = cursor
        response = requests.get(base_url + path, headers=headers, params=params).json()
        events = response['events']
        cursor = response['cursor']
        all_events += events

        count_events_found = len(events)
    all_events = pd.DataFrame(all_events)

    return all_events


def get_event_markets(ticker):
    path=f'/trade-api/v2/events/{ticker}?with_nested_markets=true'
    msg_string = timestampt_str + method + path

    sig = sign_pss_text(private_key, msg_string)
    headers = {
            'KALSHI-ACCESS-KEY': '9ef4bded-dca9-4121-aa72-845966544df3',
            'KALSHI-ACCESS-SIGNATURE': sig,
            'KALSHI-ACCESS-TIMESTAMP': timestampt_str,
        }
    response = requests.get(base_url + path, headers=headers).json()
    events = response['event']
    markets = events['markets']
    # columns include
    markets = pd.DataFrame(markets)

    # drop rows where status == finalized
    markets = markets[markets['status'] != 'finalized']
    columns = [
        "ticker",
        "subtitle",
        "close_time",
        "yes_bid",
        "yes_ask",
        "last_price",
        "volume_24h",
        "strike_type",
    ]
    if "cap_strike" in markets.columns:
        columns.append("cap_strike")
    if "floor_strike" in markets.columns:
        columns.append("floor_strike")

    markets = markets[columns]
    return markets


if __name__ == "__main__":
    balance = get_balance()
    portfolio = get_positions()
    events = get_events()
    # event = get_event("KXBTCMINY-25")
    print(balance)
    print(portfolio)

