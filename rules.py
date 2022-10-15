import copy
from enum import Enum
from utils import merge_targets

class PatternType(Enum):
    check = 0
    disallow = 1
    allow_instance = 2
    disallow_instance = 3
    get = 4
    disallow_allowed = 5
    allow_local_instance = 6
    disallow_local_instance = 7
    disallow_local_allowed = 8
    allow_local_allowed = 9

class ActionRule:

    def __init__(self, vertex, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        vertex.action_rules.append(self)
        vertex.action_rules = sorted(vertex.action_rules, key=lambda x: x.priority)
        pass

    def get_targets(self, graph, target_set, local_target_set):
        # return target_set, local_target_set, allow
        return target_set, local_target_set, True

    def process_patterns(self, patterns, graph, target_set, local_target_set):

        allow = True
        context = dict()
        for pattern in patterns:

            type = pattern[0]

            if type == PatternType.check:
                allow = self.check(graph, pattern, context)
            elif type == PatternType.disallow:
                allow = self.disallow(graph, pattern, context)
            elif type == PatternType.allow_instance:
                target_set["allow"] |= self.allow_instance(graph, pattern, context)
            elif type == PatternType.disallow_instance:
                target_set["disallow"] |= self.disallow_instance(graph, pattern, context)
            elif type == PatternType.get:
                self.get(graph, pattern, context)
            elif type == PatternType.disallow_allowed:
                target_set["allow"] -= self.disallow_allowed(graph, pattern, context, target_set)
            elif type == PatternType.allow_local_instance:
                local_target_set["allow"] |= self.allow_local_instance(graph, pattern, context)
            elif type == PatternType.disallow_local_instance:
                local_target_set["disallow"] |= self.disallow_local_instance(graph, pattern, context)
            elif type == PatternType.disallow_local_allowed:
                local_target_set["allow"] -= self.disallow_local_allowed(graph, pattern, context, local_target_set)
            elif type == PatternType.allow_local_allowed:
                self.allow_local_allowed(graph, pattern, context, target_set, local_target_set)
            else:
                raise Exception("Bad PatternType!")

            if not allow:
                return target_set, local_target_set, allow

        return target_set, local_target_set, allow

    def check(self, graph, pattern, context):
        # deepcopy context
        context = copy.deepcopy(context)
        for traversal in pattern:
            _, src_rule, edge_rule, tgt_rule = traversal
            src_vert = None
            if "id" in src_rule:
                src_vert = graph.vertices.get(src_rule["id"])
            elif "ref" in src_rule:
                src_vert = context.get(src_rule["ref"])
            
            if src_vert is None:
                return context, False

            if edge_rule["dir"] == "<":
                edgeset = { e for e in src_vert.in_edges.edge_set if e.edge_type == edge_rule["type"] }
            elif edge_rule["dir"] == ">":
                edgeset = { e for e in src_vert.out_edges.edge_set if e.edge_type == edge_rule["type"] }
            else:
                return context, False

            seeking_id = "id" in tgt_rule
            found_id = False
            for edge in edgeset:

                if seeking_id and edge.tgt.id == tgt_rule["id"]:
                    found_id = True
                    break
                elif "tag" in tgt_rule and edge.tgt.id == tgt_rule["tag"] and tgt_rule["attr"] in edge.tgt.attr_map:
                    context[tgt_rule["tag"]] = edge.tgt

            if seeking_id and not found_id:
                return context, False

            # if src is ref, check/set ref
            # if tgt is ref, check/set ref
            # get src vert, if no existy, return false
            # if target has id, check id to edgetype
            # if target is tag, get edgetype to id
            # if target has attr, filter by attr
            # add target to context

        return context, True

    def disallow(self, graph, pattern, context):
        return set()

    def allow_instance(self, graph, pattern, context):
        return set()

    def disallow_instance(self, graph, pattern, context):
        return set()

    def get(self, graph, pattern, context):
        return set()

    def disallow_allowed(self, graph, pattern, context):
        return set()

    def allow_local_instance(self, graph, pattern, context):
        return set()

    def disallow_local_instance(self, graph, pattern, context):
        return set()

    def disallow_local_allowed(self, graph, pattern, context):
        return set()

    def allow_local_allowed(self, graph, pattern, context):
        return set()

class InheritedActionRule:

    def __init__(self, vertex, priority=0, replicate=True):
        if replicate is True:
            self.replicate(vertex)
        super().__init__(vertex, priority)

    def replicate(self, vertex):
        visited = set([vertex])
        queue = [vertex]
        while len(queue) > 0:
            root = queue.pop(0)
            for edge in root.in_edges.edgetype_to_edge["Is"]:
                child = self.graph.vertices[edge.src]
                if child in visited:
                    continue
                self.__class__(child, edge.attr_map.get("priority", 0), False)
                visited.add(child)
                queue.append(child)

class r_Action(ActionRule):

    patterns = (
        (PatternType.check, {"id":"Ego"}, {"type":"Is", "dir":"<"}, {"tag":"v_0", "attr":"Instance"}),
        (PatternType.check, {"ref":"v_0"}, {"type":"Is", "dir":">"}, {"tag":"v_1", "attr":"Instance"}),
        (PatternType.check, {"ref":"v_1"}, {"type":"Is", "dir":">"}, {"id":"Is"}),
        (PatternType.check, {"ref":"v_1"}, {"type":"Is", "dir":">"}, {"id":"Person"}),
    )

    def get_targets(self, graph, target_set, local_target_set):
        return {"allow":set(), "disallow":set()}, {"allow":set(), "disallow":set()}, True

class r_Interaction_Action(ActionRule):

    patterns = (
        (PatternType.allow_instance, {"id":"Person"}, {"type":"Is", "dir":"<"}, {"tag":"v_0", "attr":"Instance"}),
        (PatternType.allow_instance, {"ref":"v_0"}, {"type":"Is", "dir":"<"}, {"id":"Is"}),
        (PatternType.allow_instance, {"ref":"v_0"}, {"type":"Is", "dir":"<"}, {"tag":"instance", "attr":"Instance"}),
        (PatternType.disallow_instance, {"id":"Ego"}, {"type":"Is", "dir":"<"}, {"tag":"instance", "attr":"Instance"}),
    )

    def get_targets(self, graph, target_set, local_target_set):
        return {"allow":set(), "disallow":set()}, {"allow":set(), "disallow":set()}, True

rules_map = {
    "Action": r_Action,
    "Interaction_Action": r_Interaction_Action,
}

"""
class r_Conversation_Action(ActionRule):

    def get_targets(self, graph, target_set, local_target_set):
        disallow = [
            (),
            (),
            (),
        ]
"""

"""
'Check' = If pattern fails, set allow to false. If pattern succeeds, set allow to true.
'Disallow' = If pattern matches, set allow to false.
'Allow Instance' = Allow every vertex 'instance' which matches the pattern.
'Disallow Instance' = Disallow every vertex 'instance' which matches the pattern.
'Get' = Simply exists to populate temporary variables. Note that all temporary vertex sets referenced in a 'Get' block should be initialized, even if not met.
'Disallow Allowed' = Disallow every vertex in target_set["allow"] which matches the pattern.
'Allow Local Instance'
'Disallow Local Instance'
'Disallow Local Allowed'
'Allow Local Allowed'

'(BFS)edge_type' = Iteratively traverse over this edge type until target ID is met.
v_0, v_1, v_2 = 'Variable' vertex. Anything that matches the pattern, regardless of id.
vertex("X") = Vertex has "X" in attr_map.

Action Rule

--Check--
Ego <-Is- v_0("Instance")
v_0 -Is-> v_1("Instance")
v_1 -Is-> Is
v_1 -Is-> Person

================================================================

Interaction_Action Rule

--Allow instance--
Person <-Is- v_0("Instance")
v_0 <-Is- Is
v_0 <-Is- instance("Instance")

--Disallow instance--
Ego <-Is- instance("Instance")

================================================================

Conversation_Action Rule

--Disallow--
Ego <-Is- v_0("instance")
v_0 (BFS)-Is-> Involved
v_0 -Is-> Combat_Context
--Get--
Ego <-Is- v_1("instance")
v_1 -Is-> Participant
v_1 -Is-> v_2("Instance")
v_2 -Is-> Conversation_Context
--Disallow Allowed--
instance <-Is- v_3("instance")
v_3 -Is-> Participant
v_3 -Is-> v_4("Instance")
v_4 -Is-> Conversation_Context
v_4 != v_2

================================================================
"""
