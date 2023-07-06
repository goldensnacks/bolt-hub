from MDAPI.underlier import Pair
from cluster_server import market_data_loop

if __name__ == "__main__":
    pair = Pair("USD", "NDX", 1, 'marketdata.pickle')
    market_data_loop(pair)