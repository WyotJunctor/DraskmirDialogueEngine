
class ChooseMaker:
    def __init__(self):
        self.make = "choose"

    def consider(self, ego, graph):
        return graph.vertices["Wait"]

class PlayerChooseMaker(ChooseMaker):
    def __init__(self):
        self.make = "player choose"

class AIChooseMaker(ChooseMaker):
    def __init__(self):
        self.make = "AI choose"
