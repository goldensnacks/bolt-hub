import pickle
import os
import pandas as pd

class Graph:
    """All securities, hashmapped"""
    def __init__(self):
        self.securities = {}



def get_security(secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'rb') as f:
        sec = pd.read_pickle(f)
    return sec



class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj
        self._set_cache = {}
        self.save()

    def __setattr__(self, key, value):
        if key not in ['name', 'obj', '_set_cache']:
            self.obj.__setattr__(key, value)
            self.save()
        else:
            super().__setattr__(key, value)
            self.save()

    def __getattr__(self, key):
        if key not in ['name', 'obj', '_set_cache']:
            return self.obj.__getattribute__(key)
        else:
            return super().__getattribute__(key)

    def nodes(self):
        methods = [node for node in self.obj.__dir__() if not node.__contains__('__')]
        return methods

    def save(self):
        """load and return security"""
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        with open(path, 'wb') as f:
            return pickle.dump(self, f)

