import pickle
import os
import pandas as pd

class Graph:
    """All securities, hashmapped"""
    def __init__(self):
        self.securities = {}

class Method:
    """function / attribute of security. Can be valid or not. """
    def __init__(self):
        self.valid = False

def get_security(secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'rb') as f:
        sec = pd.read_pickle(f)
    return sec

def save_security(sec, secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'wb') as f:
        return pickle.dump(sec,f)

class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    def save(self):
        """load and return security"""
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        with open(path, 'wb') as f:
            return pickle.dump(self, f)

