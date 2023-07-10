import pickle
import os
import sys
sys.path.append('C:\\Users\\jacob\\bolt-hub\\boltmarket-main\\Securities')

def get_security(secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'rb') as f:
        return pickle.load(f)

def save_security(sec, secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'wb') as f:
        return pickle.dumps(sec,f)

class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    def save(self):
        """load and return security"""
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        with open(path, 'wb') as f:
            return pickle.dump(self, f)
