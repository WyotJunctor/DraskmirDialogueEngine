from random import shuffle

from brain import Brain
from graph import Graph
from reality import Reality

class Game:

    def __init__(self, json_path="drask_graph.json"):
        self.timestep = 0

        reality_graph = Graph(self)
        reality_graph.load_json(json_path)
        self.reality = Reality(reality_graph, dict())

        self.entities = set()
        self.player_entity = None

    def step(self):

        actions = list()

        actions = [  ]

        for entity in self.entities:
            action = entity.choose_action()

            if action is not None:
                actions.append(
                    ( entity, action )
                )

        actions = shuffle(actions)

        for action_entity, action_vert, action_tgt in actions:

            if action_vert is None:
                continue

            if action_entity.check_action_validity(action_vert, action_tgt) is False:
                continue

            graph_events = self.reality.receive_action(
                self.timestep, action_entity, action_vert, action_tgt
            )

            for graph_event in graph_events:

                for observing_entity in self.entities:
                    observing_entity.reveive_event(graph_event)

        self.timestep += 1
