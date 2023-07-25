from ib_insync import IB, Forex, Contract

def get_eurusd_spot():
    # Connect to the Interactive Brokers TWS (make sure TWS is running and API access is enabled)
    ib = IB()
    ib.connect('127.0.0.1', 7497, clientId=1)  # Make sure the port and clientId match your TWS settings

    # Define the contract for EURUSD
    contract = Forex('EURUSD')

    # Request market data
    ticker = ib.reqTickers(contract)

    # Print the spot price (last price) for EURUSD
    spot_price = ticker[0].marketPrice()
    print(f'EURUSD Spot Price: {spot_price}')

    # Disconnect from TWS
    ib.disconnect()

if __name__ == '__main__':
    # Run the synchronous function to get the spot price
    get_eurusd_spot()
