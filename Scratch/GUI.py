from Cycles.cycles_base import GUICycle
from Securities.Securities import get_security
def eurusd_spot():
    try:
        return get_security("EURUSD").obj.get_spot()
    except Exception as e:
        return eurusd_spot()

def usdjpy_spot():
    try:
        return get_security("USDJPY").obj.get_spot()
    except Exception as e:
        return usdjpy_spot()

def market_table():
    try:
        return get_security("Tradables").obj.get_table()
    except Exception as e:
        return get_security("Tradables").obj.get_table()

def eurusd_label():
    return "EURUSD"

def usdjpy_label():
    return "USDJPY"

euroGUI = GUICycle("GUI.xlsx", "EURUSD",{"A1": eurusd_label,
                                         "A2": usdjpy_label,
                                         "B1": eurusd_spot,
                                         "B2": usdjpy_spot,
                                         "D5": market_table
                                         }
                   )
euroGUI.cycle()