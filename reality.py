from collections import defaultdict
from functools import reduce
from pprint import pprint

from action_rules import InheritedActionRule
from choose import ChooseMaker
from clock import Clock
from graph import Graph, Vertex
from graph_event import GraphMessage, EventType
from utils import merge_targets

"""
(actions)
s.r. sends proposal actions to o.r. (action rules, planning)
o.r. processes deltas (validation rules, effect rules)
sends deltas back to s.r.
s.r. processes deltas (validation rules, effect rules)
sends 'follow-through' reactions (reaction rules, planning?)
o.r. processes deltas (validation rules, effect rules)
sends deltas back to s.r.
s.r. processes deltas (validation rules, effect rules)
(spawning, do this sequentially for now)
spawn s.r. (already starts with concept graph)
special send deltas to o.r.
o.r. special processes and sends only downstream deltas to spawning s.r.
sends full message to other s.r.

validation rules process deltas and temporarily add (and do all the lineage stuff)
then they remove or transform the graph
then effect rules can generate additional deltas (which get processed by validation rules...)
"""

class Reality:

    def __init__(self, clock: Clock, graph: Graph, update_rules: list, validation_rules: dict, effect_rules: dict):
        self.clock = clock
        self.graph = graph
        self.validation_rules = defaultdict(dict)
        self.effect_rules = defaultdict(dict)

        for rules, self_rules in ((validation_rules, self.validation_rules), (effect_rules, self.effect_rules)):
            for rule_key, rule_class in rules.items():
                self_rules[graph.vertices[rule_key.v_id]][rule_key] = rule_class(graph.vertices[rule_key.v_id])

        self.update_rules = [ update_rule(self) for update_rule in update_rules ]

    def update_self(self):
        for update_rule in self.update_rules:
            message = update_rule.step()
            if message is not None:
                self.receive_message(message)

    # rewrite this
    # pass records through validation
    # pass records through effect rules
    # iterate and accumulate
    # return cumulative records
    def receive_message(self, message: GraphMessage):
        records = self.graph.update_graph(message)
        effect_messages = list()

        while len(records) > 0:
            record = records.pop()
            effect_rule = self.effect_rules.get(record.key)

            if effect_rule is not None:
                new_message = effect_rule.receive_record(record)

                if new_message is not None:
                    effect_messages.append(new_message)
                    new_records = self.graph.update_graph(new_message)

                    records |= (new_records)

        if len(effect_messages) > 1:
            effect_messages = reduce(lambda x,y: x.merge(y), effect_messages)
        elif len(effect_messages) == 1:
            effect_messages = effect_messages.pop(0)
        else:
            effect_messages = GraphMessage()
        all_messages = message.merge(effect_messages)

        return all_messages, effect_messages


class SubjectiveReality(Reality):
    def __init__(self, clock: Clock, choosemaker: ChooseMaker, graph: Graph, update_rules: list, validation_rules: dict, effect_rules: dict, action_rules: dict):
        super().__init__(clock, graph, update_rules, validation_rules, effect_rules)

        self.choosemaker = choosemaker

        ego_concept = graph.vertices["Ego"]
        self.ego = list(ego_concept.in_edges.edgetype_to_vertex["Is"])[0]
        self.action_rules = defaultdict(list)

        # rewrite this, we shouldn't have any inherited stuff...
        # specialized templates should just be different.
        # for each action rule in the map, instantiate it
        for v_id, action_rule in action_rules_map.items():
            if v_id not in graph.vertices:
                continue
            vertex = graph.vertices[v_id]
            rule_instance = action_rule(vertex) 
            self.action_rules[vertex].append(rule_instance)
            if isinstance(rule_instance, InheritedActionRule):
                rule_instance.replicate(self.action_rules)

    def choose_action(self):

        target_map = self.get_targets()

        if len(target_map) == 0:
            return None

        action, target = self.choosemaker.consider(target_map, self.ego, self.graph)

        return (action, target) # (action vertex, action target)

    def check_action_validity(self, action_vertex, action_target):
        #TODO(Simon): implement in a not dumb way
        target_map = self.get_targets()
        return action_target in target_map.get(action_vertex, set())

    def get_action_targets(self, action_rules, target_set):
        local_target_set = {"allow":set(), "disallow":set()}
        highlight_map = defaultdict(defaultdict, defaultdict(set))
        for rule in action_rules:
            r_target_set, r_local_target_set, highlight_map, allow = rule.get_targets(self.ego, self.graph, target_set, local_target_set)
            if allow is False:
                return dict(), dict(), dict(), False
            target_set = merge_targets(target_set, r_target_set)
            r_local_target_set["disallow"] = r_local_target_set["disallow"].union(target_set["disallow"])
            local_target_set = merge_targets(local_target_set, r_local_target_set)
        return target_set, local_target_set, highlight_map, True

    def get_targets(self):
        target_map = dict()
        # get root action
        action_vert = self.graph.vertices["Action"]
        instance_vert = self.graph.vertices["Instance"]
        target_map = {action_vert: {"allow":set(), "disallow":set()}} # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        dependency_map = {action_vert: [0, 0]}
        highlight_map = defaultdict(lambda: defaultdict(set))
        queue = [action_vert]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, r_highlight_map, allow = self.get_action_targets(self.action_rules[root], target_map[root])
            if allow is False:
                target_map[root] = {"allow":set(), "disallow":set()}
                continue

            for action, vertex_map in r_highlight_map.items():
                for target_vert, highlight_vert_set in vertex_map.items():
                    highlight_map[action][target_vert] |= highlight_vert_set

            target_map[root] = merge_targets(target_set, local_target_set)

            for child in root.in_edges.edgetype_to_vertex["Is"]:
                if instance_vert in child.relationship_map["Is>"]:
                    continue
                if child not in target_map:
                    target_map[child] = dict({"allow":target_set["allow"], "disallow": target_set["disallow"]})
                    dependency_map[child] = [
                        1,
                        len([v for v in child.out_edges.edgetype_to_vertex["Is"] if action_vert in v.relationship_map["Is>"]])
                    ]
                else:
                    target_map[child] = merge_targets(target_map[child], target_set)
                    dependency_map[child][0] += 1
                if dependency_map[child][0] == dependency_map[child][1]:
                    queue.append(child)

        real_actions = { vertex for vertex in self.graph.vertices["Real_Action"].in_edges.edgetype_to_vertex["Is"] }

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
