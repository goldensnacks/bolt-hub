from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

class MyWrapper(EWrapper):
    def __init__(self):
        self.ask_price = None
        self.bid_price = None

    def tickPrice(self, reqId, tickType, price, attrib):
        if tickType == 1:  # Bid price
            self.bid_price = price
        elif tickType == 2:  # Ask price
            self.ask_price = price

        if self.ask_price and self.bid_price:
            # Compute the spot price as the average of the bid and ask prices
            spot_price = (self.bid_price + self.ask_price) / 2
            print(f"EUR/USD spot price: {spot_price:.6f}")


class MyClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)


class TwsApiDemo:
    def __init__(self):
        self.wrapper = MyWrapper()
        self.client = MyClient(self.wrapper)

    def run(self):
        # Connect to the TWS API
        self.client.connect("localhost", 7497, clientId=0)

        # Create a contract for the EUR/USD currency pair
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.currency = "USD"
        contract.exchange = "IDEALPRO"

        # Request real-time market data for the EUR/USD currency pair
        self.client.reqMktData(1, contract, "", False, False, [])

        # Wait for the spot price to be received
        while self.wrapper.bid_price is None or self.wrapper.ask_price is None:
            self.client.run()

        # Disconnect from the TWS API
        self.client.disconnect()
