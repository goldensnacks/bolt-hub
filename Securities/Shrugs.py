from ib_insync import IB, Forex


class Shrugs:
    def __init__(self, source = "IBKR"):
        self.source = source
        self.datasource = IBKR() if source == "IBKR" else yFinanceDataSource()

    def get_val(self, tickers, coord="spot"):
        if self.source == "IBKR":
            self.datasource.get_spots(tickers)

class DataSource:
    def __init__(self):
        pass
class yFinanceDataSource(DataSource):
    def __init__(self):
        pass
    def get_spot(self, ticker):
        current_info = ticker.info
        spot_rate = (current_info['bid'] + current_info['ask'])/2
        return spot_rate

    def get_eurusd_spot(self):
        eurusd = yf.Ticker("EURUSD=X")
        return self.get_spot(eurusd)

    def get_usdjpy_spot(self):
        usdjpy = yf.Ticker("USDJPY=X")
        return self.get_spot(usdjpy)

class IBKR(DataSource):
    def __init__(self):
        super().__init__()

    def get_spots(self, tickers):
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

    def get_eurusd_spot(self):
        # Connect to the Interactive Brokers TWS (make sure TWS is running and API access is enabled)

        ib = IB()
        ib.connect('127.0.0.1', 7497, clientId=1)  # Make sure the port and clientId match your TWS settings

        # Define the contract for EURUSD
        contract = Forex('EURUSD')

        # Request market data
        ticker = ib.reqTickers(contract)

        # Print the spot price (last price) for EURUSD
        spot_price = ticker[0].marketPrice()
        print("Successfully read spot of ", spot_price)
        ib.disconnect()
        return spot_price

