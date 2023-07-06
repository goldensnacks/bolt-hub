import pickle
from Cycles import GUICycle

def eurusd_spot():
    with open('../Securities/EURUSD.pkl', 'rb') as f:
        underlier = pickle.load(f)
    return underlier.get_spot()

euroGUI = GUICycle("GUI.xlsx", "EURUSD",{"A1": eurusd_spot})
euroGUI.cycle()