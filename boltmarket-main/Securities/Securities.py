import pickle

def get_security(secname):
    """load and return security"""
    with open(f'./Securities/{secname}.pkl', 'rb') as f:
        return pickle.load(f)
