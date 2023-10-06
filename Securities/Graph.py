class Graph:
    """All securities, hashmapped"""
    def __init__(self):
        self.securities = {}


class Security:
    """convert object to ongraph security"""
    def __init__(self, key, graph, obj):
        self.graph = graph
        for function in obj.functions():
            self.methods[''] = {}
        graph.object[key] = self

class Method:
    """function / attribute of security. Can be valid or not. """
    def __init__(self):
        self.valid = False
