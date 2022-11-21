from random import sample
from string import ascii_lowercase

def get_alphastring(num):

    

    ...

class ChooseMaker:
    def __init__(self):
        self.make = "choose"

    def consider(self, target_map, ego, graph):
        return graph.vertices["Wait"], 

class PlayerChooseMaker(ChooseMaker):
    def __init__(self):
        self.make = "player choose"

    def consider(self, target_map, ego, graph):

        print(f"Act, '{ego.id}'...")

        num_actions = len(target_map)
        action_i_len = len(str(num_actions))
        for i, pair in enumerate(target_map.items()):
            action, targets = pair

            print(f"{i}. {action}:")
            for j, target in enumerate(targets):
                alpha = get_alphastring(j)
                print(f"{alpha} {target}")



        return graph.vertices["Wait"]

class AIChooseMaker(ChooseMaker):
    def __init__(self):
        self.make = "AI choose"

    def consider(self, target_map, ego, graph):

        action = sample(list(target_map.keys()), k=1)
        target = sample(list(target_map[action]), k=1)

        return graph.vertices[action], graph.vertices[target]
