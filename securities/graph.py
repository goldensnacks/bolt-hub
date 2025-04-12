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
    path = os.path.join(os.path.dirname(__file__), 'object_db', secname, secname + ".pkl")
    with open(path, 'rb') as f:
        sec = pd.read_pickle(f)
    node_paths = [os.path.join(os.path.dirname(__file__), 'object_db', secname, node + ".pkl") for node in sec.nodes]
    for node_path in node_paths:
        with open(node_path, 'rb') as f:
            node = pd.read_pickle(f)
            sec.nodes[node] = node
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


def wipe_db():
    path = os.path.join(os.path.dirname(__file__), 'object_db')
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))


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
            nodes = self.nodes
            for label, node in nodes.items():
                if label == key:
                    node.__setattr__(key, value)
                    path = os.path.join(os.path.dirname(__file__), 'object_db', self.name, label + ".pkl")
                    with open(path, 'wb') as f:
                        pickle.dump(node, f)
        else:
            super().__setattr__(key, value)
            self.save()

    @property
    def nodes(self):
        node_path = os.path.join(os.path.dirname(__file__), 'object_db', self.name)
        nodes = [node for node in os.listdir(node_path) if not node == self.name + ".pkl"]
        # read into memory
        nodes = {node.split('.')[0]:pd.read_pickle(os.path.join(node_path, node)) for node in nodes}
        return nodes

    def get_node(self, key):
        node_path = os.path.join(os.path.dirname(__file__), 'object_db', self.name, key + ".pkl")
        with open(node_path, 'rb') as f:
            node = pd.read_pickle(f)
        return node

    def __getattr__(self, key):
        if key not in ['name', 'obj', '_set_cache', 'nodes'] and not key.__contains__('__'):
            node = self.get_node(key)
            args = node.args
            for name, value in args.items():
                # arg_node = self.get_node(name)
                if name != key:
                    arg = self.__getattr__(name)
                    args[name] = arg
            node.args = args
            value = node.value()
            return value

        else:
            return super().__getattribute__(key)

    def make_nodes(self):
        methods = [node for node in self.obj.__dir__() if not node.__contains__('__')]
        nodes = {method:Node(self.obj.__getattribute__(method)) for method in methods}
        for label, node in nodes.items():
            path = os.path.join(os.path.dirname(__file__), 'object_db', self.name, label + ".pkl")
            with open(path, 'wb') as f:
                pickle.dump(node, f)
        self.save()

    def save(self): # dump just the nodes
        """dump as pickle"""
        path = os.path.join(os.path.dirname(__file__), 'object_db', self.name, self.name + ".pkl")

        # check if path exists
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        with open(path, 'wb') as f:
            pickle.dump(self, f)

        # if hasattr(self, 'nodes'):
        #     for node in self.nodes.items():
        #         path = os.path.join(os.path.dirname(__file__), 'object_db', self.name, node + ".pkl")
        #         with open(path, 'wb') as f:
        #             pickle.dump(node, f)

    def delete(self):
        path = os.path.join(os.path.dirname(__file__), self.name + ".pkl")
        os.remove(path)

def update(old_sec: Security, target_obj):
    new_sec = Security("temp_name", target_obj)
    new_sec.nodes = old_sec.nodes
    new_sec.name = old_sec.name
    return new_sec