from collections import defaultdict
from pprint import pprint
from os.path import join as pjoin
from random import shuffle
import re, os, json

from action_rules import rules_map as action_rules_map
from choose import PlayerChooseMaker
from clock import Clock
from effect_rules import obj_effect_rules_map, subj_effect_rules_map
from instancegen import get_next_instance_id
from reality import SubjectiveReality, ObjectiveReality
from graph import Graph
from graph_event import GraphMessage, EventType, EventTarget
from update_rules import obj_update_rules, subj_update_rules

ENTITY_ID_REPLACE = re.compile(r"\$[^\$]*\$")

filepath = os.path.dirname(__file__)
obj_path = pjoin(filepath, "Graphs", "obj_base_graph.json")
subj_path = pjoin(filepath, "Graphs", "subj_base_graph.json")
player_path = pjoin(filepath, "Graphs", "player_spawn_graph.json")

class Game:

    def __init__(self, objective_json=obj_path, subjective_json=subj_path, entity_json=player_path, player_json=player_path):
        self.clock = Clock()

        reality_graph = Graph(self.clock)
        reality_graph.load_json_file(objective_json)
        self.reality = ObjectiveReality(self.clock, reality_graph, obj_update_rules, obj_effect_rules_map)

        self.entity_json_path = entity_json
        self.subjective_json_path = subjective_json

        self.entities = set()
        self.player_json = player_json

    def spawn_player(self, choose_weapons=False):
        self.player_entity = self.create_entity(
            PlayerChooseMaker(),
            entity_json_path=self.player_json
        )

        if not choose_weapons:
            return

        good_choose = False
        while not good_choose:
            print(f"'{self.player_entity.ego.id}', choose your equipment...")
            print("[input '1' for nothing, '2' for a weapon only, '3' for armor only, '4' for both arms and armor]")
            choose = input()

            try:
                choose = int(choose)

                good_choose = choose in (1, 2, 3, 4)
            except:
                print(f"Choice '{choose}' invalid.")
                continue
        
        if choose == 1:
            return

        message = GraphMessage()

        if choose in (2, 4):
            print(f"'{self.player_entity.ego.id}', you are Armed")
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (self.player_entity.ego.id, ("Has",), "Armed")
            )
        if choose in (3, 4):
            print(f"'{self.player_entity.ego.id}', you are Armored")
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (self.player_entity.ego.id, ("Has",), "Armored")
            )

        self.player_entity.graph.update_graph(message)
        self.reality.graph.update_graph(message)

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
        
        for instance_v in self.reality.graph.vertices["Instance"].in_edges.edgetype_to_vertex["Is"]:
            graph_message.update_map[(EventType.Add, EventTarget.Vertex)].add((instance_v.id))
            for out_edge in instance_v.out_edges.edge_set:
                graph_message.update_map[(EventType.Add, EventTarget.Edge)].add(
                    (out_edge.src.id, tuple(out_edge.edge_type), out_edge.tgt.id)
                )
            for in_edge in instance_v.in_edges.edge_set:
                graph_message.update_map[(EventType.Add, EventTarget.Edge)].add(
                    (in_edge.src.id, tuple(in_edge.edge_type), in_edge.tgt.id)
                )

        subjective_graph.update_graph(graph_message)

        if entity_json_path is None:
            entity_json_path = self.entity_json_path

        graph_message = self.convert_json_to_graph_message(entity_json_path)
        subjective_graph.update_graph(graph_message)
        subjective_reality = SubjectiveReality(
            self.clock,
            choose_maker,
            subjective_graph,
            subj_update_rules,
            subj_effect_rules_map,
            action_rules_map
        )
        graph_message.update_map[(EventType.Add, EventTarget.Edge)].remove((
            subjective_reality.ego.id, ("Is",), "Ego"
        ))
        full_message, effect_message = self.reality.receive_message(graph_message)

        for entity in self.entities:
            entity.receive_message(full_message)

        subjective_reality.receive_message(effect_message)
        self.entities.add(subjective_reality)

        return subjective_reality

    def step(self):

        self.reality.step()
        for entity in self.entities:
            entity.step()

        actions = list()

        dead_entities = set()
        for entity in self.entities:
            # action: (action_vert, action_target)
            action = entity.choose_action()

            if action is not None:
                actions.append(
                    ( entity, action )
                )
            else:
                dead_entities.add(entity)

        self.entities -= dead_entities

        shuffle(actions)

        for action_entity, action_pair in actions:
            action_vert, action_tgt = action_pair


            if action_vert is None:
                continue

            if action_entity.check_action_validity(action_vert, action_tgt) is False:
                continue

            src_vert = action_entity.ego
            instance_id = f"{src_vert.id}~{action_vert.id}~{action_tgt.id}~{self.clock.timestep}"
            print(instance_id)
            message = GraphMessage(update_map=defaultdict(
                set,
                {
                    (EventType.Add, EventTarget.Vertex): set([instance_id]),
                    (EventType.Add, EventTarget.Edge): set([
                            (action_tgt.id, ("Target",), instance_id),
                            (instance_id, ("Is",), action_vert.id),
                            (src_vert.id, ("Source",), instance_id), 
                            (instance_id, ("Is",), "Instance"), 
                        ]),
                }
            ))

            graph_message, _ = self.reality.receive_message(
                message
            )

            graph_message.strip_multitype_edges()

            for observing_entity in self.entities:
                observing_entity.receive_message(graph_message)

        self.clock.step()