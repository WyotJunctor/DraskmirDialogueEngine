from utils import merge_targets
import copy
from graph import Graph
from graph_event import GraphEvent
from rules import ActionRule, InheritedActionRule
from utils import merge_targets


class Brain:

    def __init__(self, graph: Graph, effect_rules: dict, action_rules: dict):
        self.graph = graph
        self.effect_rules = effect_rules
        self.action_rules = action_rules

    def get_action_targets(self, action_rules, target_set):
        local_target_set = {"allow":set(), "disallow":set()}
        for rule in action_rules:
            r_target_set, r_local_target_set, allow = rule.get_targets(self.graph, target_set, local_target_set)
            if allow is False:
                return {}, {}, False
            target_set = merge_targets(target_set, r_target_set)
            r_local_target_set["disallow"] = r_local_target_set["disallow"].union(target_set["disallow"])
            local_target_set = merge_targets(local_target_set, r_local_target_set)
        return target_set, local_target_set, True

    def get_targets(self):
        # get root action
        action_vert = self.graph.vertices["Action"]
        target_map = {action_vert: [{"allow":set(), "disallow":set()}, 0, 0]} # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        queue = [action_vert]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, allow = self.get_action_targets(self.action_rules[root.id], self.target_map[root][0])
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
        print(target_map)

    def receive_event(self, event: GraphEvent):
        status = True
        if event.key in self.effect_rules:
            for event_response in self.effect_rules[event.key]:
                if event_response(event) is False:
                    status = False
                    break
        if status is False:
            return
        self.graph.update_json(event)
