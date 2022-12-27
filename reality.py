import copy
from collections import defaultdict
from functools import reduce

from choose import ChooseMaker
from clock import Clock
from graph import Graph
from graph_event import GraphMessage, EventType
from graph_objs import Vertex
from utils import merge_targets

class Reality:

    def __init__(self, clock: Clock, graph: Graph, effect_rules_map: dict, shortcut_maps: dict):
        self.clock = clock
        self.graph = graph

        self.effect_rules = defaultdict(list)

        # for each effect in the map, instantiate it
        for effect_key, effect_rule in effect_rules_map.items():
            v_id = effect_key[2]
            effect_rule(graph.vertices[v_id], self.effect_rules[effect_key])

        # for each shortcut, put it on a vertex
        for v_id, shortcut_map in shortcut_maps.items():
            self.graph.vertices[v_id].shortcut_map = shortcut_map

    def receive_message(self, message: GraphMessage):
        records = self.graph.update_graph(message)
        effect_messages = set()

        while len(records) > 0:
            record = records.pop()
            effect_rule = self.effect_rules.get(record)

            if effect_rule is not None:
                new_message = effect_rule.receive_record(record)
                effect_messages.add(new_message)
                new_records = self.graph.update_graph(new_message)

                records.extend(new_records)

        effect_messages = reduce(effect_messages, lambda x,y: x.merge(y))
        all_messages = message.merge(effect_messages)

        return all_messages, effect_messages

class SubjectiveReality(Reality):
    def __init__(self, clock: Clock, choosemaker: ChooseMaker, graph: Graph, effect_rules_map: dict, shortcut_maps: dict, action_rules_map: dict):
        super().__init__(clock, graph, effect_rules_map, shortcut_maps)

        self.choosemaker = choosemaker

        ego_concept = graph.vertices["Ego"]
        self.ego = list(ego_concept.in_edges.edgetype_to_vertex["Is"])[0]

        self.action_rules = defaultdict(list)

        # for each action rule in the map, instantiate it
        for v_id, action_rule in action_rules_map.items():
            action_rule(graph.vertices[v_id], self.action_rules[v_id])

        """
        # initialize effect rules
        for v_id, shortcut_map in shortcut_maps.items():
            action_rule_class(vertex, self.action_rules[v_id])
        """


    def choose_action(self):

        target_map = self.get_targets()
        action, target = self.choosemaker.consider(target_map, self.ego, self.graph)

        return (action, target) # (action vertex, action target)

    def check_action_validity(self, action_vertex, action_target):
        #TODO(Simon): implement in a not dumb way
        target_map = self.get_targets()
        return action_target in target_map.get(action_vertex, set())

    def get_action_targets(self, action_rules, target_set):
        local_target_set = {"allow":set(), "disallow":set()}
        for rule in action_rules:
            r_target_set, r_local_target_set, allow = rule.get_targets(self.ego, self.graph, target_set, local_target_set)
            if allow is False:
                return {}, {}, False
            target_set = merge_targets(target_set, r_target_set)
            r_local_target_set["disallow"] = r_local_target_set["disallow"].union(target_set["disallow"])
            local_target_set = merge_targets(local_target_set, r_local_target_set)
        return target_set, local_target_set, True

    def get_targets(self):
        target_map = dict()
        # get root action
        action_vert = self.graph.vertices["Action"]
        instance_vert = self.graph.vertices["Instance"]
        target_map = {action_vert: [{"allow":set(), "disallow":set()}, 0, 0]} # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        queue = [action_vert]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, allow = self.get_action_targets(self.action_rules[root.id], target_map[root][0])
            if allow is False:
                continue
            target_map[root][0] = merge_targets(target_set, local_target_set)

            for child in root.in_edges.edgetype_to_vertex["Is"]:
                if instance_vert in child.relationship_map["Is>"]:
                    continue
                if child not in target_map:
                    target_map[child] = [
                        copy.deepcopy(target_set), 1,
                        len([v for v in child.out_edges.edgetype_to_id["Is"] if action_vert in v.relationship_map["Is>"]])
                    ]
                else:
                    target_map[child][0] = merge_targets(target_map[child][0], target_set)
                    target_map[child][1] += 1
                if target_map[child][1] == target_map[child][2]:
                    queue.append(child)

        return {
            action: dumbass_list[0]["allow"] for action, dumbass_list in target_map.items() if len(dumbass_list[0]["allow"]) > 0
        }

class ObjectiveReality(Reality):
    def __init__(self, clock: Clock, graph: Graph, effect_rules_map: dict, shortcut_maps: dict):
        super().__init__(clock, graph, effect_rules_map, shortcut_maps)
