from collections import defaultdict
from functools import reduce
from pprint import pprint

from choose import ChooseMaker
from clock import Clock
from graph import Graph, Vertex
from graph_event import GraphMessage, EventType
from utils import merge_targets


def construct_rules_map():
    return {"native": defaultdict(
            lambda: defaultdict(list)), "added": defaultdict(
            lambda: defaultdict(list))}


class Reality:

    def __init__(self, clock: Clock, graph: Graph, update_rules: list, deconflicting_rules: dict, effect_rules: dict):
        self.clock = clock
        self.graph = graph
        self.vertex_rules = dict()
        self.vertex_rules["deconflict"] = construct_rules_map()
        self.vertex_rules["effect"] = construct_rules_map()

        for rules, self_rules in ((deconflicting_rules, self.vertex_rules["deconflict"]), (effect_rules, self.vertex_rules["effect"])):
            self.initialize_rules(rules, self_rules)

        self.update_rules = [update_rule(self) for update_rule in update_rules]

    def initialize_rules(self, input_rules, self_rules):
        for rule_key, rule_class in input_rules.items():
            self_rules[rule_key.v_id][rule_key].append(
                rule_class(self.graph.vertices[rule_key.v_id]))

    def update_graph(self, message: GraphMessage):
        # iterates vertices/edges to be added/removed
        return self.graph.update_graph(message, self.vertex_rules["deconflict"], self.vertex_rules["effect"])

    def receive_message(self, message: GraphMessage):
        # define records object
        records = self.update_graph(message)

        while records.not_empty() == True:
            message = records.check_rules(self.vertex_rules["deconflict"])
            # why not overwrite initial records? because some deltas don't have applicable deconflicting rules,
            # but we might still want their effect rules to trigger
            records.update_with(self.graph.update_graph(message))
            message = records.check_rules(self.vertex_rules["effect"])
            records = self.graph.update_graph(message)

    def check_update_rules(self):
        for update_rule in self.update_rules:
            message = update_rule.step()
            if message is not None:
                self.receive_message(message)


class SubjectiveReality(Reality):
    def __init__(self, clock: Clock, choosemaker: ChooseMaker, graph: Graph, update_rules: list, deconflicting_rules: dict, effect_rules: dict, action_rules: dict):
        super().__init__(clock, graph, update_rules, deconflicting_rules, effect_rules)

        self.choosemaker = choosemaker

        ego_concept = graph.vertices["Ego"]
        self.ego = list(ego_concept.in_edges.edgetype_to_vertex["Is"])[0]
        self.vertex_rules["action"] = construct_rules_map()

        self.initialize_rules(action_rules, self.vertex_rules["action"])

    def choose_action(self):

        target_map = self.get_targets()

        if len(target_map) == 0:
            return None

        action, target = self.choosemaker.consider(
            target_map, self.ego, self.graph)

        return (action, target)  # (action vertex, action target)

    def check_action_validity(self, action_vertex, action_target):
        # TODO(Simon): implement in a not dumb way
        target_map = self.get_targets()
        return action_target in target_map.get(action_vertex, set())

    def get_action_targets(self, action_rules, target_set):
        local_target_set = {"allow": set(), "disallow": set()}
        highlight_map = defaultdict(defaultdict, defaultdict(set))
        for rule in action_rules:
            r_target_set, r_local_target_set, highlight_map, allow = rule.get_targets(
                self.ego, self.graph, target_set, local_target_set)
            if allow is False:
                return dict(), dict(), dict(), False
            target_set = merge_targets(target_set, r_target_set)
            r_local_target_set["disallow"] = r_local_target_set["disallow"].union(
                target_set["disallow"])
            local_target_set = merge_targets(
                local_target_set, r_local_target_set)
        return target_set, local_target_set, highlight_map, True

    def get_targets(self):
        target_map = dict()
        # get root action
        action_vert = self.graph.vertices["Action"]
        instance_vert = self.graph.vertices["Instance"]
        # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        target_map = {action_vert: {"allow": set(), "disallow": set()}}
        dependency_map = {action_vert: [0, 0]}
        highlight_map = defaultdict(lambda: defaultdict(set))
        queue = [action_vert]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, r_highlight_map, allow = self.get_action_targets(
                self.action_rules[root], target_map[root])
            if allow is False:
                target_map[root] = {"allow": set(), "disallow": set()}
                continue

            for action, vertex_map in r_highlight_map.items():
                for target_vert, highlight_vert_set in vertex_map.items():
                    highlight_map[action][target_vert] |= highlight_vert_set

            target_map[root] = merge_targets(target_set, local_target_set)

            for child in root.in_edges.edgetype_to_vertex["Is"]:
                if instance_vert in child.relationship_map["Is>"]:
                    continue
                if child not in target_map:
                    target_map[child] = dict(
                        {"allow": target_set["allow"], "disallow": target_set["disallow"]})
                    dependency_map[child] = [
                        1,
                        len([v for v in child.out_edges.edgetype_to_vertex["Is"]
                            if action_vert in v.relationship_map["Is>"]])
                    ]
                else:
                    target_map[child] = merge_targets(
                        target_map[child], target_set)
                    dependency_map[child][0] += 1
                if dependency_map[child][0] == dependency_map[child][1]:
                    queue.append(child)

        real_actions = {
            vertex for vertex in self.graph.vertices["Real_Action"].in_edges.edgetype_to_vertex["Is"]}

        action_options = defaultdict(set)
        for action, target_set in target_map.items():
            if len(target_set["allow"]) > 0 and action in real_actions:
                # check if action is contained in highlight map
                # if so, iterate through allowed targets
                # if allowed target is contained in sub_highlight_map,
                # add that to the action options
                if action in highlight_map:
                    for allowed_target in target_set["allow"]:
                        if allowed_target in highlight_map[action]:
                            target_set["allow"].discard(allowed_target)
                            target_set["allow"] |= highlight_map[action][allowed_target]
                action_options[action] = target_set["allow"]

        return action_options


class ObjectiveReality(Reality):
    def __init__(self, clock: Clock, graph: Graph, update_rules: list, validation_rules: dict, effect_rules: dict):
        super().__init__(clock, graph, update_rules, validation_rules, effect_rules)
