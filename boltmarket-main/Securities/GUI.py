import pickle
from Cycles import GUICycle
from Securities import get_security
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

euroGUI = GUICycle("GUI.xlsx", "EURUSD",{"A1": eurusd_spot,
                                         "A2": usdjpy_spot
                                         }
                   )
euroGUI.cycle()