from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.common import *
from ibapi.contract import *
import pandas as pd
from typing import List

class MyWrapper(EWrapper):
    def __init__(self):
        self.option_params = {}
        self.ticks = []

    def securityDefinitionOptionParameter(self, reqId, exchange, underlyingConId, tradingClass, multiplier, expirations, strikes):
        if reqId == 1:
            self.option_params = {'exchange': exchange,
                                  'underlyingConId': underlyingConId,
                                  'tradingClass': tradingClass,
                                  'multiplier': multiplier,
                                  'expirations': expirations,
                                  'strikes': strikes}

    def historicalTicksBidAsk(self, reqId, ticks, done):
        if reqId == 2:
            for tick in ticks:
                self.ticks.append([tick.time, tick.priceBid, tick.priceAsk])


def main():
    # Create contract object for the underlying currency pair
    contract = Contract()
    contract.symbol = "FISV"
    contract.secType = "OPT"
    contract.currency = "USD"
    contract.exchange = "SMART"

    # Create a connection to the IBKR API
    client = EClient(MyWrapper())
    client.connect("localhost", 7496, clientId=0)

    # Request option parameters for the currency pair
    client.reqSecDefOptParams(1, contract.symbol, "", contract.secType, contract.conId)

    # Wait for option parameters to be received
    while not client.wrapper.option_params:
       pass

    # Extract option parameters
    option_params = client.wrapper.option_params

    # Request historical tick data for each expiration/strike combination
    for expiration in option_params['expirations']:
        for strike in option_params['strikes']:
            # Create contract object for the option
            option_contract = Contract()
            option_contract.symbol = contract.symbol
            option_contract.secType = "OPT"
            option_contract.currency = contract.currency
            option_contract.exchange = option_params['exchange']
            option_contract.lastTradeDateOrContractMonth = expiration
            option_contract.strike = strike
            option_contract.right = "C"
            option_contract.tradingClass = option_params['tradingClass']
            option_contract.multiplier = option_params['multiplier']
            option_contract.underlyingConId = option_params['underlyingConId']

            # Request historical tick data for the option
            client.reqHistoricalTicks(2, option_contract, "", "10000", "BID_ASK", 1, False, [])

    # Wait for tick data to be received
    while not client.wrapper.ticks:
        pass

    # Convert tick data to DataFrame
    ticks_df = pd.DataFrame(client.wrapper.ticks, columns=['time', 'bid', 'ask'])
    ticks_df['time'] = pd.to_datetime(ticks_df['time'], unit='s')

    # Pivot DataFrame to create volatility surface
    vol_surface = pd.pivot_table(ticks_df, values=['bid', 'ask'], index='time', columns=['strike'])
    vol_surface = vol_surface.apply(lambda x: x / x.mean() - 1, axis=1)

    # Display volatility surface
    print(vol_surface)

    # Disconnect from the IBKR API
    client.disconnect()

if __name__ == "__main__":
    main()