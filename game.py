from brain import Brain
from graph import Graph

class Game:
    timestep = 0

    def __init__(self, json_path="drask_graph.json"):
        self.timestep

        reality_graph = Graph(self)
        reality_graph.load_json(json_path)
        self.reality_brain = Brain(reality_graph, dict())

    def step(self):
        ...
