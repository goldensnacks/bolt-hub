import dill
import pickle
import os
import pandas as pd
import inspect

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


class Node:
    def __init__(self, method):
        self._value = None
        self._is_valid = False
        self.method = method
        self.args = []

    def is_valid(self):
        if not self._is_valid:
            return False
        else:
            for arg in self.args:
                if isinstance(arg, Node):
                    if not arg.is_valid():
                        return False
        return True
    def value(self):
        if self.is_valid:
            self.is_valid = True
            return self._value
        else:
            self._evaluate()
            return self.value()

    def _evaluate(self):
        self.args = [arg if not isinstance(arg, Node) else arg.value() for arg in self.args]


class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj
        self._set_cache = {}
        self.make_nodes()
        self.save()

    def __setattr__(self, key, value):
        """setters set node args, not values in memory"""
        if key not in ['name', 'nodes', 'obj', '_set_cache']:
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

    def make_nodes(self):
        methods = [node for node in self.obj.__dir__() if not node.__contains__('__')]
        nodes = [Node(method) for method in methods]
        self.nodes = nodes

    def save(self):
        """dump as pickle"""
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        with open(path, 'wb') as f:
            return pickle.dump(self, f)

