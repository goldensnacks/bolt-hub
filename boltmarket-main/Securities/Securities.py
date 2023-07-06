import pickle

def get_security(secname):
    """load and return security"""
    with open(f'/Securities/{secname}.pkl', 'rb') as f:
        return pickle.load(f)


class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj

    def save(self):
        with open(f'{self.name}.pkl', 'wb') as f:
            pickle.dump(self, f)