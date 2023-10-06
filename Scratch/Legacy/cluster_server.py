import xmlrpc.client
import pandas as pd
import time
from TDAPI.Tradables import BinaryOption, Portfolio, Range
from datetime import datetime
from datetime import timedelta
from MDAPI.underlier import Pair

class Market:
    def __init__(self, underlier, exp_min, exp_max, kalshi_server, market_data_handle):
        self.underlier = underlier
        self.exp_min = exp_min
        self.exp_max = exp_max
        self.tickerPairMap =  {"NASDAQ100": ("USD", "NDX"), "INX": ("USD", "SPX")}
        self.kalshi_server = kalshi_server
        self.market_data_handle = market_data_handle

    def set_table(self):
        underlier = self.underlier
        res = pd.DataFrame(self.kalshi_server.get_markets_cached()['markets']).query("category == 'Financials'")
        res = res.join(res['rulebook_variables'].apply(pd.Series))
        res['Date'] = list(map(lambda x: datetime.strptime(x, "%B %d, %Y")+timedelta(hours=16), res['Date']))
        res = res[res['contract_ticker'].isin([underlier])]
        res = res.set_index('id', drop=True)
        res['floor'] = list(map(lambda x, y, z:   (float(x.replace(',','')) if y == "above" else 'NA') if (y == "above" or y == "below")
                            else float(z.replace(',','')), res['Value'], res["Above/Below/Between"], res["Floor_strike"]))
        res['cap']   = list(map(lambda x, y, z:   (float(x.replace(',','')) if y == "below" else 'NA') if (y == "above" or y == "below")
                            else float(z.replace(',','')), res['Value'], res["Above/Below/Between"], res["Cap_strike"]))
        #res['expiry'] = list(map(lambda x: datetime.strftime(x, "%Y-%m-%d %H:%M"), res['Date']))
        res['time'] = [(date - datetime.now()) / timedelta(days=1) for date  in res['Date']]
        res = res[res['time'].between(self.exp_min, self.exp_max)]
        pairs = dict(zip(set(res['Date']), [Pair(self.tickerPairMap[self.underlier][0],
                                                 self.tickerPairMap[self.underlier][1], time, self.market_data_handle)
                                            for time in set(res['time'])]))

        def build_port(contractTicker, floor, cap, expiry, tickerPairMap, pair):
            if cap == 'NA':
                return Portfolio([BinaryOption(tickerPairMap[contractTicker], floor, expiry, True, pair)],[1])
            elif floor == 'NA':
                return Portfolio([BinaryOption(tickerPairMap[contractTicker], cap, expiry, False, pair)], [1])
            return Range(BinaryOption(tickerPairMap[contractTicker], floor, expiry, True, pair),
                         BinaryOption(tickerPairMap[contractTicker], cap, expiry, True, pair))
        res['portfolio'] = [build_port(contractTicker, floor, cap, expiry, self.tickerPairMap, pairs[expiry])
                            for contractTicker, floor, cap, expiry
                            in zip(res['contract_ticker'], res['floor'], res['cap'], res['Date'])]

        self.market_table = res

    def pricing_and_risk(self):
        self.market_table['price'] = [100*port.price() for port in self.market_table['portfolio']]
        self.market_table['spot'] = [port.spot() for port in self.market_table['portfolio']]
        self.market_table['delta'] = [port.delta() for port in self.market_table['portfolio']]
        self.market_table['vega'] = [port.vega() for port in self.market_table['portfolio']]
        self.market_table['theta'] = [port.theta() for port in self.market_table['portfolio']]

        self.market_table['alpha'] = [abs(bid-price) if price < bid else abs(price-ask) if price>ask else 0
                                      for price, bid, ask
                                      in zip(self.market_table['price'],
                                             self.market_table['yes_bid'],
                                             self.market_table['yes_ask'])
                                      ]
        self.market_table['model_rec'] = ['sell' if price < bid else ('buy' if price>ask else 'mm')
                                          for price, bid, ask
                                          in zip(self.market_table['price'],
                                                 self.market_table['yes_bid'],
                                                 self.market_table['yes_ask'])]
        try:
            self.market_table['cap_sigma'] = [port.cap_sigma() for port in self.market_table['portfolio']]
            self.market_table['floor_sigma'] = [port.floor_sigma() for port in self.market_table['portfolio']]
        except:
            self.market_table['cap_sigma']   = [port.sigma() for port in self.market_table['portfolio']]
            self.market_table['floor_sigma'] = [port.sigma() for port in self.market_table['portfolio']]

    def position(self, load=False):
        risk = pd.DataFrame(self.kalshi_server.user_get_market_positions()['market_positions'])[['market_id', 'position', 'position_cost']]
        risk = risk.set_index('market_id', drop=True)
        risk = risk[abs(risk['position'])>0]
        self.market_table['pos'] = [0 if not index in list(set(risk.index)&set(self.market_table.index))
                      else risk.loc[index,'position'] for index in self.market_table.index]
        self.market_table['pos_cost'] = [0 if not index in list(set(risk.index)&set(self.market_table.index))
                           else risk.loc[index,'position_cost']/-1000 for index in self.market_table.index]

        self.market_table['pos_value'] = [abs(pos)*price for pos, price in zip(self.market_table['pos'],
                                                                               self.market_table['price'])]
        self.market_table['PnL']       = [value-cost for value, cost in zip(self.market_table['pos_value'],
                                                                            self.market_table['pos_cost'])]
        self.market_table['pos_vega']  = [pos*vega for pos, vega in zip(self.market_table['pos'],
                                                                        self.market_table['vega'])]
        self.market_table['pos_delta'] = [pos*delta for pos, delta in zip(self.market_table['pos'],
                                                                          self.market_table['delta'])]
        self.market_table['pos_theta'] = [pos*theta for pos, theta in zip(self.market_table['pos'],
                                                                          self.market_table['theta'])]

    def set_risk(self):
        delta = sum(self.market_table['pos_delta'])
        vega = sum(self.market_table['pos_vega'])
        theta = sum(self.market_table['pos_theta'])
        PnL   = sum(self.market_table['PnL'])
        modelProb = sum(self.market_table['price'])*100
        askProb = sum(self.market_table['yes_ask'])
        bidProb = sum(self.market_table['yes_bid'])
        risk = {'PnL': PnL, 'delta':delta, 'vega':vega, 'theta':theta,
                 'modelProb': modelProb, 'bidProb':bidProb, "askProb":askProb }
        self.risk = risk

    def market_data_session(self, message):
        return self.market_data_session.catch(message)

def risk_loop(market_data_session, child_conn):
    while (True):
        start_time = time.time()
        try:
            market_data_session.set_table()
            print("--- %s seconds --- mkt table" % (time.time() - start_time))
            market_data_session.pricing_and_risk()
            print("--- %s seconds --- risk" % (time.time() - start_time))
            market_data_session.position()
            print("--- %s seconds --- positions" % (time.time() - start_time))
            market_data_session.set_risk()
            market_data_session.save_risk()
            print("--- %s seconds --- positions risk rotation" % (time.time() - start_time))

        except Exception as ex:
            print("In risk loop: ", ex)

def market_data_loop(pair):
    while (True):
        start_time = time.time()
        try:
            pair.save_market_data()
            print("--- %s seconds --- market data saved" % (time.time() - start_time))

        except Exception as ex:
            print("In market data loop: ", ex)

def main_loop(market_data_session, autotrader, freq=0):
    while(True):
        start_time = time.time()
        time.sleep(freq)
        try:
            market_data_session.set_table()
            print("--- %s seconds --- mkt table" % (time.time() - start_time))
            market_data_session.pricing_and_risk()
            print("--- %s seconds --- risk" % (time.time() - start_time))
            market_data_session.position(load=True)
            print("--- %s seconds --- positions" % (time.time() - start_time))
            market_data_session.set_risk()
            print("--- %s seconds --- positions risk rotation" % (time.time() - start_time))
            autotrader.trade(market_data_session.market_table, market_data_session.risk)
            print("--- %s seconds --- trade" % (time.time() - start_time))
        except Exception as ex:
            print(ex)





