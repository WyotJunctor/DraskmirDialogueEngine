from utils import merge_targets
import copy
from collections import defaultdict
from choose import ChooseMaker
from clock import Clock
from graph import Graph
from graph_event import GraphEvent
from utils import merge_targets


class Brain:

    def __init__(self, clock: Clock, choosemaker: ChooseMaker, graph: Graph, effect_rules_map: dict, action_rules_map: dict, shortcut_maps: dict):
        self.clock = clock
        self.choosemaker = choosemaker
        self.ego = graph.vertices["Ego"]  # TODO(Simon): this should grab the instance not the concept
        self.graph = graph
        self.effect_rules = defaultdict(list)
        self.action_rules = defaultdict(list)

        # for each shortcut, put it on a vertex
        for v_id, shortcut_map in shortcut_maps.items():
            self.graph.vertices[v_id].shortcut_map = shortcut_map

        # alert
        # alert
        # stinky Wyatt code incoming
        # alrt
        # TODO(Simon): WYatt fix your shit
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
        target_map = {action_vert: [{"allow":set(), "disallow":set()}, 0, 0]} # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        queue = [action_vert]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, allow = self.get_action_targets(self.action_rules[root.id], target_map[root][0])
            if allow is False:
                continue
            target_map[root][0] = merge_targets(target_set, local_target_set)

            for child in root.in_edges.edgetype_to_id["Is"]:
                child = self.graph.vertices[child]
                if child not in target_map:
                    target_map[child] = [
                        copy.deepcopy(target_set), 1,
                        len([v for v in child.out_edges.edgetype_to_id["Is"] if "Action" in self.graph.vertices[v].attr_map])
                    ]
                else:
                    target_map[child][0] = merge_targets(target_map[child][0], target_set)
                    target_map[child][1] += 1
                if target_map[child][1] == target_map[child][2]:
                    queue.append(child)

        return { 
            action: dumbass_list[0]["allow"] for action, dumbass_list in target_map.items() if len(dumbass_list[0]["allow"]) > 0
        }

    def receive_event(self, event: GraphEvent):
        self.graph.handle_graph_event(event)
"""
        status = True
        if event.key in self.effect_rules:
            for event_response in self.effect_rules[event.key]:
                if event_response.receive_event(event) is False:
                    status = False
                    break
        if status is False:
            return
        self.graph.update_json(event)
"""
