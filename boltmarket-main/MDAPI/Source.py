from datetime import time

from ib_insync import *
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract


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

class Price(Coordinate):
    def __init__(self, source, delivery):
        super().__init__(source)

    def spot(self):
        return self.source.spot()

class Volatility(Coordinate):
    def __init__(self, source, delivery):
        super().__init__(source)

    def vol_surface(self):
        return self.source.vol_surface()