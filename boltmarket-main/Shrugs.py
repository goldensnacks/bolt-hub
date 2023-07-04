import yfinance as yf
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from IBKRHelpers import MyWrapper, MyClient

class Shrugs:
    def __init__(self, name:str):
        self.name = name
        self.datasource = yFinanceDataSource(name)

    def get_val(self, ticker, coord="spot"):
        if ticker == "EURUSD":
            return self.datasource.get_eurusd_spot()

class DataSource:
    def __init__(self, name:str):
        self.name = name

class yFinanceDataSource(DataSource):
    def __init__(self, name:str):
        super().__init__(name)


    def get_spot(self, ticker):
        current_info = ticker.info
        spot_rate = current_info['bid'] / current_info['ask']
        return spot_rate

    def get_eurusd_spot(self):
        eurusd = yf.Ticker("EURUSD=X")
        return self.get_spot(eurusd)


class IBKR(DataSource):
    def __init__(self, name:str):
        self.wrapper = MyWrapper()
        self.client = MyClient(self.wrapper)
        super().__init__(name)

    def get_eurusd_spot(self):
        # Connect to the TWS API
        self.client.connect("localhost", 7497, clientId=0)

        # Create a contract for the EUR/USD currency pair
        contract = Contract()
        contract.Symbol = "EUR.USD"
        contract.SecType = "CASH"
        contract.Exchange = "ARCA"
        # Request real-time market data for the EUR/USD currency pair
        self.client.reqMktData(1001, contract, "", False, False, [])

        # Wait for the spot price to be received
        while self.wrapper.bid_price is None or self.wrapper.ask_price is None:
            self.client.run()

        # Disconnect from the TWS API
        self.client.disconnect()

def main():
    ibkr = IBKR("IBKR")
    print(ibkr.get_eurusd_spot())

if __name__ == "__main__":
    main()
