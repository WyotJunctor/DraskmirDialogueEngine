from collections import defaultdict
import json
from random import shuffle

from choose import PlayerChooseMaker
from clock import Clock
from reality import SubjectiveReality, ObjectiveReality
from graph import Graph
from graph_event import GraphEvent, GraphMessage, EventType, EventTarget

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

        player_add_event = GraphMessage(update_map=defaultdict(set, {()}))

        self.reality.graph.update_graph([player_add_event])
        subjective_graph.update_graph([player_add_event])

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

            src_vert = action_entity.ego
            instance_id = f"{src_vert.id}~{action_vert.id}~{action_tgt.id}~{self.clock.timestep}"
            message = GraphMessage(update_map=defaultdict(
                set,
                {
                    (EventType.Add, EventTarget.Vertex): set([instance_id]),
                    (EventType.Add, EventTarget.Edge): set([
                            (instance_id, "Target", action_tgt.id), 
                            (src_vert.id, "Source", instance_id), 
                            (instance_id, "Is", "Instance"), 
                            (instance_id, "Is", action_vert.id)
                        ]),
                }
            ))

            graph_message = self.reality.receive_message(
                message
            )

            graph_message.strip_multitype_edges()

            for observing_entity in self.entities:
                observing_entity.reveive_events(graph_message)

        self.clock.step()