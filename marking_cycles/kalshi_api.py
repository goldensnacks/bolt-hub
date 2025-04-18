import json
import time
from datetime import timedelta
from typing import Any, Dict, Optional
import requests
import logging
from datetime import datetime
import numpy as np
import pandas as pd
from securities.graph import Security, get_security
from tradables.pricing_helper_fns import convert_kalshi_date_to_datetime
from tradables.products import OneTouch, BinaryOption, MarketTable

OBJECT_DB = 'securities/object_db'


def snap_markets(session):
    return session.exchange_client.get_markets(**session.config)['markets']


class KalshiClient:
    """A simple client that allows utils to call authenticated kalshi API endpoints."""
    def __init__(
        self,
        host: str,
        email: str,
        password: str,
        token: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Initializes the client and logs in the specified user.
        Raises an HttpError if the user could not be authenticated.
        """

        self.host = host
        self.email = email
        self.password = password
        self.token = token
        self.user_id = user_id
        self.last_api_call = datetime.now()

    """Built in rate-limiter. We STRONGLY encourage you to keep 
    some sort of rate limiting, just in case there is a bug in your 
    code. Feel free to adjust the threshold"""
    def rate_limit(self) -> None:
        # Adjust time between each api call
        THRESHOLD_IN_MILLISECONDS = 100

        now = datetime.now()
        threshold_in_microseconds = 1000 * THRESHOLD_IN_MILLISECONDS
        threshold_in_seconds = THRESHOLD_IN_MILLISECONDS / 1000
        if now - self.last_api_call < timedelta(microseconds=threshold_in_microseconds):
            time.sleep(threshold_in_seconds)
        self.last_api_call = datetime.now()

    def post(self, path: str, body: dict) -> Any:
        """POSTs to an authenticated kalshi HTTP endpoint.
        Returns the response body. Raises an HttpError on non-2XX results.
        """
        self.rate_limit()

        response = requests.post(
            self.host + path, data=body, headers=self.request_headers()
        )
        self.raise_if_bad_response(response)
        return response.json()

    def get(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """GETs from an authenticated kalshi HTTP endpoint.
        Returns the response body. Raises an HttpError on non-2XX results."""
        self.rate_limit()

        response = requests.get(
            self.host + path, headers=self.request_headers(), params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def delete(self, path: str, params: Dict[str, Any] = {}) -> Any:
        """Posts from an authenticated kalshi HTTP endpoint.
        Returns the response body. Raises an HttpError on non-2XX results."""
        self.rate_limit()

        response = requests.delete(
            self.host + path, headers=self.request_headers(), params=params
        )
        self.raise_if_bad_response(response)
        return response.json()

    def request_headers(self) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.user_id + " " + self.token
        return headers

    def raise_if_bad_response(self, response: requests.Response) -> None:
        if response.status_code not in range(200, 299):
            raise HttpError(response.reason, response.status_code)

    def query_generation(self, params:dict) -> str:
        relevant_params = {k:v for k,v in params.items() if v != None}
        if len(relevant_params):
            query = '?'+''.join("&"+str(k)+"="+str(v) for k,v in relevant_params.items())[1:]
        else:
            query = ''
        return query

class HttpError(Exception):
    """Represents an HTTP error with reason and status code."""
    def __init__(self, reason: str, status: int):
        super().__init__(reason)
        self.reason = reason
        self.status = status

    def __str__(self) -> str:
        return "HttpError(%d %s)" % (self.status, self.reason)

class ExchangeClient(KalshiClient):
    def __init__(self,
                    exchange_api_base: str,
                    email: str,
                    password: str):
        super().__init__(
            exchange_api_base,
            email,
            password,
        )

        """You must log in before making authenticated calls. We store the token and 
        pass it into each call."""

        login_json = json.dumps({"email": self.email, "password": self.password})
        result = self.post(path = "/login", body = login_json)
        self.token = result["token"]
        self.user_id = result["member_id"]

        self.exchange_url = "/exchange"
        self.markets_url = "/markets"
        self.events_url = "/events"
        self.series_url = "/series"
        self.portfolio_url = "/portfolio"

    def logout(self,):
        result = self.post("/logout")
        return result

    def get_exchange_status(self,):
        result = self.get(self.exchange_url + "/status")
        return result

    # market endpoints!

    def get_markets(self,
                        limit:Optional[int]=None,
                        cursor:Optional[str]=None,
                        event_ticker:Optional[str]=None,
                        series_ticker:Optional[str]=None,
                        max_close_ts:Optional[int]=None,
                        min_close_ts:Optional[int]=None,
                        status:Optional[str]=None,
                        tickers:Optional[str]=None,
                            ):
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        dictr = self.get(self.markets_url+query_string)
        return dictr

    def get_market_url(self,
                        ticker:str):
        return self.markets_url+'/'+ticker

    def get_market(self,
                    ticker:str):
        market_url = self.get_market_url(ticker=ticker)
        dictr = self.get(market_url)
        return dictr

    def get_event(self,
                    event_ticker:str):
        dictr = self.get(self.events_url+'/'+event_ticker)
        return dictr

    def get_series(self,
                    series_ticker:str):
        dictr = self.get(self.series_url+'/'+series_ticker)
        return dictr

    def get_market_history(self,
                            ticker:str,
                            limit:Optional[int]=None,
                            cursor:Optional[str]=None,
                            max_ts:Optional[int]=None,
                            min_ts:Optional[int]=None,
                            ):
        relevant_params = {k: v for k,v in locals().items() if k!= 'ticker'}
        query_string = self.query_generation(params = relevant_params)
        market_url = self.get_market_url(ticker = ticker)
        dictr = self.get(market_url + '/history' + query_string)
        return dictr

    def get_orderbook(self,
                        ticker:str,
                        depth:Optional[int]=None,
                        ):
        relevant_params = {k: v for k,v in locals().items() if k!= 'ticker'}
        query_string = self.query_generation(params = relevant_params)
        market_url = self.get_market_url(ticker = ticker)
        dictr = self.get(market_url + "/orderbook" + query_string)
        return dictr

    def get_trades(self,
                    ticker:Optional[str]=None,
                    limit:Optional[int]=None,
                    cursor:Optional[str]=None,
                    max_ts:Optional[int]=None,
                    min_ts:Optional[int]=None,
                    ):
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        if ticker != None:
            if len(query_string):
                query_string += '&'
            else:
                query_string += '?'
            query_string += "ticker="+str(ticker)

        trades_url = self.markets_url + '/trades'
        dictr = self.get(trades_url + query_string)
        return dictr

    # portfolio endpoints!

    def get_balance(self,):
        dictr = self.get(self.portfolio_url+'/balance')
        return dictr

    def create_order(self,
                        ticker:str,
                        client_order_id:str,
                        side:str,
                        action:str,
                        count:int,
                        type:str,
                        yes_price:Optional[int]=None,
                        no_price:Optional[int]=None,
                        expiration_ts:Optional[int]=None,
                        sell_position_floor:Optional[int]=None,
                        buy_max_cost:Optional[int]=None,
                        ):

        relevant_params = {k: v for k,v in locals().items() if k != 'self' and v != None}

        print(relevant_params)
        order_json = json.dumps(relevant_params)
        orders_url = self.portfolio_url + '/orders'
        result = self.post(path = orders_url, body = order_json)
        return result

    def batch_create_orders(self,
                                orders:list
        ):
        orders_json = json.dumps({'orders': orders})
        batched_orders_url = self.portfolio_url + '/orders/batched'
        result = self.post(path = batched_orders_url, body = orders_json)
        return result

    def decrease_order(self,
                        order_id:str,
                        reduce_by:int,
                        ):
        order_url = self.portfolio_url + '/orders/' + order_id
        decrease_json = json.dumps({'reduce_by': reduce_by})
        result = self.post(path = order_url + '/decrease', body = decrease_json)
        return result

    def cancel_order(self,
                        order_id:str):
        order_url = self.portfolio_url + '/orders/' + order_id
        result = self.delete(path = order_url + '/cancel')
        return result

    def batch_cancel_orders(self,
                                order_ids:list
        ):
        order_ids_json = json.dumps({"ids":order_ids})
        batched_orders_url = self.portfolio_url + '/orders/batched'
        result = self.delete(path = batched_orders_url, body = order_ids_json)
        return result

    def get_fills(self,
                        ticker:Optional[str]=None,
                        order_id:Optional[str]=None,
                        min_ts:Optional[int]=None,
                        max_ts:Optional[int]=None,
                        limit:Optional[int]=None,
                        cursor:Optional[str]=None):

        fills_url = self.portfolio_url + '/fills'
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        dictr = self.get(fills_url + query_string)
        return dictr

    def get_orders(self,
                        ticker:Optional[str]=None,
                        event_ticker:Optional[str]=None,
                        min_ts:Optional[int]=None,
                        max_ts:Optional[int]=None,
                        limit:Optional[int]=None,
                        cursor:Optional[str]=None
                        ):
        orders_url = self.portfolio_url + '/orders'
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        dictr = self.get(orders_url + query_string)
        return dictr

    def get_order(self,
                    order_id:str):
        orders_url = self.portfolio_url + '/orders'
        dictr = self.get(orders_url + '/' +  order_id)
        return dictr

    def get_positions(self,
                        limit:Optional[int]=None,
                        cursor:Optional[str]=None,
                        settlement_status:Optional[str]=None,
                        ticker:Optional[str]=None,
                        event_ticker:Optional[str]=None,
                        ):
        positions_url = self.portfolio_url + '/positions'
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        dictr = self.get(positions_url + query_string)
        return dictr

    def get_portfolio_settlements(self,
                                    limit:Optional[int]=None,
                                    cursor:Optional[str]=None,):

        positions_url = self.portfolio_url + '/settlements'
        query_string = self.query_generation(params={k: v for k,v in locals().items()})
        dictr = self.get(positions_url + query_string)
        return dictr

class KalshiSession:
    def __init__(self):
        self.underliers = ["EURUSD", "USDJPY"]
        self.display_columns = ['title',       "floor_strike", "cap_strike",   'mrp',
                                'pricing_vol', "hours_to_expiry", "underlier",
                                'delta', 'alpha_long',  "yes_ask", 'price',   "yes_bid", 'alpha_short',
                                ]# 'last_price',



        # from TDAPI.tradables import VanillaOption, Portfolio, Range
        self.prod_email = "jacobreedijk@gmail.com"  # change these to be your personal credentials
        self.prod_password = "DJDSOLwr11??"
        self.prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"
        self.exchange_client = ExchangeClient(exchange_api_base=self.prod_api_base, email=self.prod_email, password=self.prod_password)
        self.config = {
                        # 'limit': 1000,
                       'cursor': None,  # passing in the cursor from the previous get_markets call
                       'event_ticker': None,
                       'series_ticker': None,
                       'max_close_ts': None,  # pass in unix_ts
                       'min_close_ts': None,  # pass in unix_ts
                       'status': 'open',  # open, closed, settled
                       'tickers': None
                       }


    def assign_underlier(self, market, enabled = [ "EURUSD", "USDJPY"]):
        if market['title'].lower().find('eur') != -1 and  "EURUSD" in enabled:
            return 'EURUSD'
        elif market['title'].lower().find('jpy') != -1 and "USDJPY" in enabled:
            return 'USDJPY'
        else:
            return None
    def filter_by_underlier(self, markets):
        return markets[markets['underlier'].isin(self.underliers)]

    def save_markets(self, markets):
        try:
            tradable_sec = get_security("tradables")
        except Exception as e:
            tradable_sec = Security("tradables", MarketTable())
        tradable_sec.obj.update_table(markets)
        tradable_sec.save()

    def markets_as_table(self):
        markets = pd.DataFrame(self.snap_markets())
        markets['underlier'] = markets.apply(self.assign_underlier, axis = 1)
        markets = markets[~markets['underlier'].isna()]
        markets['expiration_time'] = markets.apply(lambda x: x.close_time, axis = 1)
        markets['hours_to_expiry'] = markets.apply(lambda x: (convert_kalshi_date_to_datetime(x.expiration_time) -
                                                              datetime.utcnow()).total_seconds( ) /3600, axis = 1)
        markets['one_touch'] = markets.apply(self.is_one_touch, axis = 1)
        markets['strike'] = markets.apply (lambda x: x.floor_strike if not np.isnan(x.floor_strike) else x.cap_strike, axis = 1)
        if True: # exclude one touch
            markets = markets[~markets['one_touch']]

        products = markets.apply(self.assign_tradable, axis = 1)
        markets['price'] = 100 *products.apply(lambda x: x.price())
        markets['delta'] = products.apply(lambda x: x.delta())

        markets['mrp'] = products.apply(lambda x: x.underlying_price())
        markets['pricing_vol'] = products.apply(lambda x: x.pricing_vol())
        markets['is_liquid'] = products.apply(lambda x: x.is_liquid())
        markets = markets[markets['is_liquid'] == True]

        def calculate_alpha(view_price, market_price):
            px = 0 if market_price in [0,100] else view_price - market_price
            return px if px > 0 else 0

        markets['alpha_long'] = markets.apply(lambda x: calculate_alpha(x.price, x.yes_ask), axis = 1)
        markets['alpha_short'] = markets.apply(lambda x: calculate_alpha(x.yes_bid, x.price), axis = 1)
        markets = markets[self.display_columns]

        return markets

    def cycle(self):
        while True:
            try:
                self.save_markets(self.markets_as_table())
                logging.info("Saved markets")
            except Exception as e:
                print(e)
                pass    # if the cycle fails, just try again

class KalshiSession:
    def __init__(self):
        self.display_columns = ['title',       "floor_strike", "cap_strike",   'mrp',
                                'pricing_vol', "hours_to_expiry", "underlier",
                                'delta', 'alpha_long',  "yes_ask", 'price',   "yes_bid", 'alpha_short',
                                ]# 'last_price',



        # from TDAPI.tradables import VanillaOption, Portfolio, Range
        self.prod_email = "jacobreedijk@gmail.com"  # change these to be your personal credentials
        self.prod_password = "DJDSOLwr11??"
        self.prod_api_base = "https://trading-api.kalshi.com/trade-api/v2"
        self.exchange_client = ExchangeClient(exchange_api_base=self.prod_api_base, email=self.prod_email, password=self.prod_password)
        self.config = {
                        'limit': 1000,
                       'cursor': None,  # passing in the cursor from the previous get_markets call
                       'event_ticker': None,
                       'series_ticker': None,
                       'max_close_ts': None,  # pass in unix_ts
                       'min_close_ts': None,  # pass in unix_ts
                       'status': 'open',  # open, closed, settled
                       'tickers': None
                       }


def snap_markets(session):
    market_table = []
    new_markets_found = 1000
    while not new_markets_found < 1000:
        res = session.exchange_client.get_markets(**session.config)
        markets = res['markets']
        cursor = res['cursor']
        market_table += markets
        session.config['cursor'] = cursor
        new_markets_found = len(markets)
    return market_table
