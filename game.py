import json
from random import shuffle

from choose import PlayerChooseMaker
from clock import Clock
from reality import SubjectiveReality, ObjectiveReality
from graph import Graph
from graph_event import GraphEvent, EventType

class Game:

    def __init__(self, objective_json="objective_graph.json", subjective_json="drask_graph.json", player_json="player.json"):
        self.clock = Clock()

        reality_graph = Graph(self.clock)
        reality_graph.load_json(objective_json)
        self.reality = ObjectiveReality(self.clock, reality_graph, dict(), dict())

        self.player_json_path = player_json
        self.subjective_json_path = subjective_json

        self.player_entity = None
        self.entities = set()

        self.create_player()

    def create_player(self):

        subjective_graph = Graph(self.clock)
        subjective_graph.load_json(self.subjective_json_path)

        with open(self.player_json_path) as f:
            glob = json.load(f)

        player_add_event = GraphEvent(
            EventType.Add,
            glob
        )

        self.reality.graph.handle_graph_event(player_add_event)
        subjective_graph.handle_graph_event(player_add_event)

        self.player_entity = SubjectiveReality(
            self.clock,
            PlayerChooseMaker(),
            subjective_graph,
            dict(),
            dict(),
            dict()
        )
        self.entities.add(self.player_entity)

    def step(self):

        actions = list()

        for entity in self.entities:
            # action: (action_vert, action_target)
            action = entity.choose_action()

            if action is not None:
                actions.append(
                    ( entity, action )
                )

        shuffle(actions)

        for action_entity, action_pair in actions:
            action_vert, action_tgt = action_pair

            if action_vert is None:
                continue

            if action_entity.check_action_validity(action_vert, action_tgt) is False:
                continue

            graph_events = self.reality.receive_action(
                action_entity, action_vert, action_tgt
            )

            for graph_event in graph_events:

                self.reality.receive_event(graph_event)

                for observing_entity in self.entities:
                    observing_entity.reveive_event(graph_event)

        self.clock.step()
