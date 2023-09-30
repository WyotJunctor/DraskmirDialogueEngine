from collections import defaultdict
from functools import reduce
from pprint import pprint

from choose import ChooseMaker
from clock import Clock
from graph import Graph, Vertex, Edge
from graph_event import GraphMessage, UpdateRecord
from utils import merge_targets

# make a copy of a rule object
# make a singleton reference of a rule object
# custom checker as to whether to copy


class SpawnRule:
    def __init__(self, graph: Graph):
        self.graph = graph

    def check_rule(self, ego_id: str) -> GraphMessage:
        message = GraphMessage()
        return message


class Rule:

    def __init__(self, rule_id: str, graph: Graph, vertex: Vertex, root_vertex: Vertex):
        self.rule_id = rule_id
        self.singleton = False
        self.graph = graph
        self.vertex = vertex
        self.root_vertex = root_vertex

    def check_rule(self, edge: Edge, add: bool) -> GraphMessage:
        message = GraphMessage()
        return message

    def check_add(self, vertex: Vertex):
        # if singleton, just return a reference to this rule
        if self.singleton is True:
            return self
        # otherwise, return a copy of this rule
        return Rule(self.rule_id, self.graph, vertex, self.root_vertex)


class RuleMap:

    def __init__(self):
        self.id_rules = defaultdict(dict)
        self.active_rules = defaultdict(dict)

    def init_rules(self, graph: Graph, vertex: Vertex, rules: dict):
        for rule_id, rule_class in rules.items():
            rule_obj = rule_class(rule_id, graph, vertex, vertex)
            self.id_rules[vertex][rule_id] = rule_obj
            active_rule = rule_obj.check_add(vertex)
            if active_rule is not None:
                self.active_rules[vertex][rule_id] = active_rule

    # given a vertex and a set of add or removed labels (ids), recalculate active rules for the vertex
    def recalculate_rules(self, labels: set, add: bool, vertex: Vertex):
        if add is False and vertex.id in labels:
            del self.id_rules[vertex]
            del self.active_rules[vertex]

        for label in labels:
            for rule_id, rule in self.id_rules.get(label, {}):
                if add is True:
                    active_rule = rule.check_add(vertex)
                    if active_rule is not None:
                        self.active_rules[vertex.id][rule_id] = active_rule
                else:
                    self.active_rules[vertex.id].pop(rule_id)

    def check_rules(self, records: UpdateRecord) -> GraphMessage:
        message = GraphMessage()
        for edges, add in ((records.add_records, True), (records.del_records, True)):
            for edge in edges:
                for vert in (edge.src, edge.tgt):
                    for _, rule in self.active_rules[vert].items():
                        message.merge(rule.check_rule(edge, add))
        return message


class Reality:

    def __init__(self, clock: Clock, graph: Graph, update_rules: list, deconflict_rules: dict, effect_rules: dict):
        self.clock = clock
        self.graph = graph
        self.deconflict_rules = RuleMap()
        self.effect_rules = RuleMap()

        self.initialize_rules(deconflict_rules, self.deconflict_rules)
        self.initialize_rules(effect_rules, self.effect_rules)

        self.update_rules = [update_rule(self) for update_rule in update_rules]

    def initialize_rules(self, input_rules, self_rules):
        for v_id, rules in input_rules.items():
            self_rules.init_rules(self.graph, self.graph.vertices[v_id], rules)

    def _update_graph(self, message: GraphMessage):
        records, lineage_add_map, lineage_del_map = self.graph.update_graph(
            message)
        for lineage_map, add in ((lineage_add_map, True), (lineage_del_map, False)):
            for vertex, labels in lineage_map.items():
                self.deconflict_rules.recalculate_rules(labels, add, vertex)
        return records

    def receive_message(self, message: GraphMessage) -> GraphMessage:
        full_message = message.copy()
        records = self._update_graph(message)

        while records.is_empty() is False:
            message = self.deconflict_rules.check_rules(records)
            full_message.merge(message)
            deconflict_records = self._update_graph(message)
            records.update_with(deconflict_records)
            message = self.effect_rules.check_rules(records)
            full_message.merge(message)
            records = self._update_graph(message)

        return full_message

    def check_update_rules(self):
        for update_rule in self.update_rules:
            message = update_rule.step()
            if message is not None:
                self.receive_message(message)


class SubjectiveReality(Reality):
    def __init__(self, clock: Clock, choosemaker: ChooseMaker, graph: Graph, ego_id: str, update_rules: list, deconflicting_rules: dict, effect_rules: dict, spawn_rules: list):
        super().__init__(clock, graph, update_rules, deconflicting_rules, effect_rules)

        self.choosemaker = choosemaker
        self.ego_id = ego_id
        self.ego = None
        self.spawn_rules = spawn_rules

        # self.vertex_rules["action"] = construct_rules_map()
        # self.initialize_rules(action_rules, self.vertex_rules["action"])

    def spawn(self, message: GraphMessage):
        self._update_graph(message)
        message = GraphMessage()
        for rule in self.spawn_rules:
            message.merge(rule.check_rule(self.ego_id))
        self.ego = self.graph.vertices[self.ego_id]

    """
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
        """


class ObjectiveReality(Reality):
    def __init__(self, clock: Clock, graph: Graph, update_rules: list, validation_rules: dict, effect_rules: dict):
        super().__init__(clock, graph, update_rules, validation_rules, effect_rules)
