import kalshi
import pandas as pd
from datetime import datetime

def get_markets():
    s = kalshi.Session(email="jacobreedijk@gmail.com", password="DJDSOLwr69?")
    markets = pd.DataFrame(s.get_markets_cached()['markets']).query("category == 'Financials'")
    markets = markets.join(markets['rulebook_variables'].apply(pd.Series))
    markets['Date'] = list(map( lambda x : datetime.strptime(x, "%B %d, %Y"), markets['Date']))
    markets = markets[ markets['Date'] > datetime.today()]
    markets = markets[markets['contract_ticker'] == "NASDAQ100"]
    markets['Cap_strike']   = list(map( lambda x,y, z: x if(y=="above") else z, markets['Value'], markets["Above/Below/Between"], markets["Cap_strike"]))
    markets['Floor_strike'] = list(map( lambda x,y, z: x if(y=="below") else z, markets['Value'], markets["Above/Below/Between"], markets["Floor_strike"]))
    markets = markets[["contract_ticker", "Floor_strike", "Cap_strike","Date"]]
    return markets


