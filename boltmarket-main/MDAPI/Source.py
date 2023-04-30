from datetime import time

from ib_insync import *
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import pickle

class ISource(EWrapper, EClient):
    def __init__(self, symbol):
        self.ticker = symbol
        self.ib = IB()
        self.client = EClient.__init__(self, self)

    def set_connect(self):
        self.connect(host="127.0.0.1", port=7496, clientId=123)

    def spot(self):
        return self.client.reqMktData(1, Contract(), "", False, False, [])

class Coordinate:
    def __init__(self, source):
        self.source = source
        self.handle = "undef.pickle"


    def save_market_data(self):
        """save market data to pickle file"""
        with open(self.handle, 'wb') as handle:
            pickle.dump(pickle.dumps(self.market_data), handle, protocol=pickle.HIGHEST_PROTOCOL)

class Price(Coordinate):
    def __init__(self, source):
        super().__init__(source)
        """define handle as source, ticket"""
        self.handle = self.source.ticker +  ".pickle"

    def ret(self):
        return self.source.spot()

class Volatility(Coordinate):
    def __init__(self, source, delivery):
        super().__init__(source)

    def vol_surface(self):
        return self.source.vol_surface()