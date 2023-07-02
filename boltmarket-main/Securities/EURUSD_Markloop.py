import pickle
import yfinance as yf

while True:
    """load EURUSD.pkl from pickle file"""
    with open('Securities/EURUSD.pkl', 'rb') as f:
        underlier = pickle.load(f)

    """get spot from yahoo finance"""
    ticker = yf.Ticker('EURUSD=X')
    data = ticker.history(period='1d')
    spot_price = data['Close'][0]

    """update spot in underlier"""
    underlier.mark_spot(spot_price)


    """save updated underlier"""
    with open('Securities/EURUSD.pkl', 'wb') as f:
        pickle.dump(underlier, f)

    print(f'updated spot: {spot_price}')