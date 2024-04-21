from datetime import datetime
import time
import pandas as pd
import json

class MarketHours:
    def __init__(self, open_hour = 11, close_hour = 13, open_day = 0, close_day = 4):
        self.open_hour = open_hour
        self.close_hour = close_hour
        self.open_day = open_day
        self.close_day = close_day

    def open(self):
        hour = datetime.now().hour
        day = datetime.now().weekday()
        return self.open_hour <= hour < self.close_hour and self.open_day <= day <= self.close_day

class AutoTrader:
    def __init__(self, kalshi_server, alpha_min, hours):
        self.kalshi_server = kalshi_server
        self.alpha_min = alpha_min
        self.hours = hours


    def aq_validate(self, res, modelrec, position):
        if not self.hours.open():
            return False
        if not position['modelProb'] > 99:
            return False
        if max(res['cap_sigma'], res['floor_sigma']) >.6 or max(res['cap_sigma'], res['floor_sigma']) <.1:
            return False
        elif res['alpha'] > self.alpha_min and modelrec =='sell':
            return True
        else:
            return False

    @staticmethod
    def autotrade_order_size(row):
        return 20

    def trade(self, market_table, risk):
        auto_trade = pd.DataFrame()
        auto_trade['_id'] = market_table.index
        auto_trade['auto_order_valid'] = [self.aq_validate(res, modelrec, risk) for res,  modelrec in zip(market_table.to_dict('records'), market_table['model_rec'])]
        auto_trade['side'] = ['yes' if modelrec == 'buy' else 'no' for modelrec in market_table['model_rec']]
        auto_trade['size'] = [self.autotrade_order_size(row) for row in auto_trade.to_dict('records')]
        auto_trade['px'] = [100-yes_bid if modelrec == 'sell' else yes_ask for yes_bid, modelrec, yes_ask in
                            zip(market_table['yes_bid'], market_table['model_rec'], market_table['yes_ask'])]
        auto_trade = auto_trade[auto_trade['auto_order_valid']==True]
        orders = [{'count': row['size'], 'market_id': row['_id'], 'price': row['px'], 'side': row['side']}
                  for row in auto_trade.to_dict('records')]
        list(map(self.kalshi_server.user_order_create, orders))
        time.sleep(3)
        list(map(self.kalshi_server.user_order_cancel, [order['market_id'] for order in orders]))
