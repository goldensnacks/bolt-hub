import pickle
import os

def get_security(secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__),  secname + ".pkl")
    with open(path, 'rb') as f:
        return pickle.load(f)


class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    def save(self):
        with open(f'{self.name}.pkl', 'wb') as f:
            pickle.dump(self, f)