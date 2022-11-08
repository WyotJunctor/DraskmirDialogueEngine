from enum import Enum

class EventType(Enum):
    Add = 0
    Delete = 1
    Timestep = 2

class GraphEvent:
    def __init__(self, key, subgraph):
        self.key = key
        self.subgraph = subgraph

class GraphDelta:
    def __init__(self, key, subgraph):
        self.key = key
        self.subgraph = subgraph
