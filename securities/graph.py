import pickle
import os
import pandas as pd
import inspect
from builtins import staticmethod



class Graph:
    """All object_db, hashmapped"""
    def __init__(self):
        self.securities = {}



def get_security(secname):
    """load and return security"""
    path = os.path.join(os.path.dirname(__file__), 'object_db',  secname + ".pkl")
    with open(path, 'rb') as f:
        sec = pd.read_pickle(f)
    return sec

class NodeDec(staticmethod):
    pass

class Node:
    def __init__(self, method: callable):
        """method really needs kwargs for this to work"""
        self._value = None
        self._is_valid = False
        self.method = method

        args = {}
        for arg in inspect.signature(method).parameters:
            args = args | {arg: None}
        self.args = args

    def __setattr__(self, key, value):
        if key in ['_value', '_is_valid', 'method', 'args'] or key.__contains__('__'):
            super().__setattr__(key, value)
        elif key in self.args.keys():
            self.args[key] = value
            self._is_valid = False
        else:
            raise ValueError("Value not in node.")

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
        if self.is_valid():
            return self._value
        else:
            self._evaluate()
            self._is_valid = True

            return self.value()

    def _evaluate(self):
        args = [arg if not isinstance(arg, Node) else arg.value() for arg in self.args.values()]
        self._value = self.method(*args)


class Security:
    def __init__(self, name, obj):
        self.name = name
        self.obj = obj
        self._set_cache = {}
        self.make_nodes()
        self.save()

    def __get__(self):
        return get_security(self.name)

    def __setattr__(self, key, value):
        if key not in ['name', 'nodes', 'obj', '_set_cache']:
            for node in self.nodes.values():
                if key in node.args.keys():
                    node.__setattr__(key, value)
            self.save()
        else:
            super().__setattr__(key, value)
            self.save()

    def __getattr__(self, key):
        if key not in ['name', 'obj', '_set_cache', 'nodes'] and not key.__contains__('__'):
            val = self.nodes[key].value()
            self.__setattr__(key, val)
            return self.nodes[key].value()
        else:
            return super().__getattribute__(key)

    def make_nodes(self):
        methods = [node for node in self.obj.__dir__() if not node.__contains__('__')]
        nodes = {method:Node(self.obj.__getattribute__(method)) for method in methods}
        self.nodes = nodes

    def save(self): # dump just the nodes
        """dump as pickle"""
        path = os.path.join(os.path.dirname(__file__), 'object_db', self.name + ".pkl")
        with open(path, 'wb') as f:
            return pickle.dump(self, f)

    def delete(self):
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        os.remove(path)

def update(old_sec: Security, target_obj):
    new_sec = Security("temp_name", target_obj)
    new_sec.nodes = old_sec.nodes
    new_sec.name = old_sec.name
    return new_sec