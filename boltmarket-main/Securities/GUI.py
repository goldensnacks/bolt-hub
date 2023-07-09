import pickle
from Cycles import GUICycle
from Securities import get_security
def eurusd_spot():
    try:
        return get_security("EURUSD").obj.get_spot()
    except Exception as e:
        return eurusd_spot()

euroGUI = GUICycle("GUI.xlsx", "EURUSD",{"A1": eurusd_spot})
euroGUI.cycle()