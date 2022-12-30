from collections import defaultdict
from pprint import pprint
from random import shuffle
import json
import re

from action_rules import rules_map as action_rules_map
from choose import PlayerChooseMaker
from clock import Clock
from effect_rules import rules_map as effect_rules_map
from instancegen import get_next_instance_id
from reality import SubjectiveReality, ObjectiveReality
from graph import Graph
from graph_event import GraphMessage, EventType, EventTarget

ENTITY_ID_REPLACE = re.compile(r"\$[^\$]*\$")

class Game:

    def __init__(self, objective_json="objective_graph.json", subjective_json="drask_graph.json", entity_json="entity.json", player_json="player.json"):
        self.clock = Clock()

        reality_graph = Graph(self.clock)
        reality_graph.load_json_file(objective_json)
        self.reality = ObjectiveReality(self.clock, reality_graph, dict())

        self.entity_json_path = entity_json
        self.subjective_json_path = subjective_json

        self.entities = set()

        self.player_entity = self.create_entity(
            PlayerChooseMaker(),
            entity_json_path=player_json
        )

    def convert_json_to_graph_message(self, json_path):
        with open(json_path) as f:
            globstring = f.read()

            matches = ENTITY_ID_REPLACE.findall(globstring)
            for match in matches:
                globstring = globstring.replace(
                    match, str(get_next_instance_id())
                )
            glob = json.loads(globstring)

        message_map = defaultdict(set)
        for vertex in glob["vertices"]:
            message_map[(EventType.Add, EventTarget.Vertex)].add(vertex["label"])

        for edge in glob["edges"]:
            message_map[(EventType.Add, EventTarget.Edge)].add((
                edge["src"], tuple(sorted([edge["types"]] if isinstance(edge["types"], str) else edge["types"])), edge["tgt"]
            ))
        return GraphMessage(update_map=message_map)

    def create_entity(self, choose_maker, entity_json_path=None):

        subjective_graph = Graph(self.clock)

        graph_message = self.convert_json_to_graph_message(self.subjective_json_path)
        subjective_graph.update_graph(graph_message)
        # subjective_graph.load_json_file(self.subjective_json_path)

        if entity_json_path is None:
            entity_json_path = self.entity_json_path

        graph_message = self.convert_json_to_graph_message(entity_json_path)
        subjective_graph.update_graph(graph_message)
        subjective_reality = SubjectiveReality(
            self.clock,
            choose_maker,
            subjective_graph,
            effect_rules_map,
            action_rules_map
        )

        full_message, effect_message = self.reality.receive_message(graph_message)

        for entity in self.entities:
            entity.receive_message(full_message)

        subjective_reality.receive_message(effect_message)
        self.entities.add(subjective_reality)

        return subjective_reality

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
                            (instance_id, {"Target"}, action_tgt.id), 
                            (instance_id, {"Is"}, action_vert.id),
                            (src_vert.id, {"Source"}, instance_id), 
                            (instance_id, {"Is"}, "Instance"), 
                        ]),
                }
            ))

            graph_message, _ = self.reality.receive_message(
                message
            )

            graph_message.strip_multitype_edges()

            for observing_entity in self.entities:
                observing_entity.reveive_events(graph_message)

        self.clock.step()