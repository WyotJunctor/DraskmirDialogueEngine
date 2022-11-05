import copy
from enum import Enum
from utils import merge_targets, get_set, get_key_set
from collections import defaultdict

class PatternScope(Enum):
    graph = 0 # target_set
    local = 1 # local_target_set

class PatternCheckType(Enum):
    check = 0 # if pattern succeeds, cool, if pattern fails, not cool
    allow = 1 # success: allow target to scope, fails: ignore
    disallow = 2 # success: disallow target to scope, fails: ignore
    get = 3 # ignore

# context:
# dependencies: vertex: "dependent_on": "", "dependent_count":
# hop_count: int:int


# update hop_count
def add_dependencies(dependencies, hop_count, src, tgt, src_hop, tgt_hop):
    for vert in (src, tgt):
        if vert not in dependencies:
            dependencies[vert] = {"dependent_on":defaultdict(set), "dependent_count":defaultdict(int)}

    for pairs in ((src, tgt_hop, tgt), (tgt, src_hop, src)):
        dependencies[pairs[0]]["dependent_on"][pairs[1]].add(pairs[2])
        dependencies[pairs[0]]["dependent_count"][pairs[1]] += 1


def cleanup(cleanup_verts, dependencies, hop_count):
    cleaned = cleanup_verts
    cleanup_queue = list(cleanup_verts)
    while len(cleanup_queue) > 0:
        root = cleanup_queue.pop(0)
        for hop, vert_set in dependencies[vert]["dependent_on"].items():
            hop_count[hop] -= 1
            if hop_count[hop] <= 0:
                return False
            for dep_vert in vert_set:
                if dep_vert in cleaned:
                    continue
                dependencies[dep_vert]["dependent_count"][hop] -= 1
                if dependencies[dep_vert]["dependent_count"][hop] <= 0:
                    cleanup_queue.add(dep_vert)
                    cleaned.add(dep_vert)
    return True

class ActionRule:

    def __init__(self, vertex, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        vertex.action_rules.append(self)
        vertex.action_rules = sorted(vertex.action_rules, key=lambda x: x.priority)


    # paths is a map of id: list<paths>, each path is a list of fellas?... possibly just refs.

    def execute_traversal(graph, traversal, dependencies, context, hop_count, src_hop):

        src_ref, edge, tgt_ref = traversal

        valid_src = set()
        valid_tgt = set()

        allow = True

        tgt_hop = src_hop + 1

        src_set = set()
        if "ref" in src_ref:
            src_set = context.get(src_ref["ref"], set())
        elif "id" in src_ref:
            src_set = get_set(graph.vertices, src_ref["id"])
        elif "context" in src_ref:
            src_set = context[src_ref["context"]] # convert to set of verts
        elif "root" in src_ref:
            src_set = set([self.vertex])

        if "target" in src_ref:
            context["target"] += src_set

        if len(src_set) == 0:
            return False

        no_src_tgts = set()
        if "ref" in tgt_ref:
            no_src_tgts = context.get(tgt_ref["ref"], set())

        if "Not_Is" in edge:
            cleanup_set = src_set.intersection(no_src_tgts)
            if cleanup(cleanup_set, context, dependencies, hop_count) == False:
                return False
            valid_src = src_set.difference(no_src_tgts)
            valid_tgt = no_src_tgts.difference(src_set)
        else:
            for src_vert in src_set:
                edge_map = src_vert.in_edges if edge["dir"] == "<" else src_vert.out_edges

                tgt_set = set()
                if "id" in tgt_ref and tgt_ref["id"] in get_key_set(edge_map.edgetype_to_id, edge["type"]):
                    tgt_set = get_set(graph.vertices, tgt_ref["id"])
                elif "ref" in tgt_ref:
                    tgt_set = context.get(tgt_ref["ref"], set()) & get_set(edge_map.edgetype_to_vertex, edge["type"])
                elif "tag" in tgt_ref:
                    tgt_set = get_set(edge_map.edgetype_to_vertex, edge["type"])

                if "context" in tgt_ref:
                    tgt_set = tgt_set & context[tgt_ref["context"]]
                if "attr" in tgt_ref:
                    tgt_set = set([v for v in tgt_set if tgt_ref["attr"] == set(v.attr_map.keys())])
                if "target" in tgt_ref:
                    context["target"] += tgt_set

                no_src_tgts -= tgt_set

                if "tag" in tgt_ref:
                    context[tgt_ref["tag"]] = tgt_set

                if "ref" in src_ref and "ref" in tgt_ref:
                    for tgt_vert in tgt_set:
                        valid_tgt.add(tgt_vert)
                        add_dependencies(dependencies, src_vert, tgt_vert, src_hop, tgt_hop)

                if len(tgt_set) == 0:
                    if cleanup(set([src_vert]), context, dependencies, hop_count) == False:
                        return False
                else:
                    if "alias" in src_ref:
                        if src_ref["alias"] not in context:
                            context["src_ref"] = set()
                        context[src_ref["alias"]].add(src_vert)
                    valid_src.add(src_vert)

            for tgt_vert in no_src_tgts:
                if cleanup(set([tgt_vert]), context, dependencies, hop_count) == False:
                    return False

        if "ref" in src_ref:
            # update context
            context[src_ref["ref"]] = valid_src
        if "ref" or "tag" in tgt_ref:
            # update context
            tgt_key = "ref" if "ref" in tgt_ref else "tag"
            context[tgt_ref[tgt_key]] = valid_tgt

        hop_count[src_hop] += len(valid_src)
        hop_count[tgt_hop] += len(valid_tgt)

        return True

    def get_targets(self, graph, target_set, local_target_set):
        context = {
            "allowed": target_set["allow"].copy(),
            "disallowed": target_set["disallow"].copy(),
            "local_allowed": local_target_set["allow"].copy(),
            "local_disallowed": local_target_set["disallow"].copy(),
        }
        for pattern in self.__class__.patterns:
            dependencies = {}
            context["target"] = set()
            hop_count = Counter()
            check_type = pattern[0]
            scope = pattern[1]
            success = True
            for traversal in pattern[2]:
                # if traversal succeeds, proceed
                # if traversal fails, stop
                success = execute_traversal(traversal, dependencies, context, hop_count, hop)
                if success == False:
                    break
            # TODO: rewrite how success is handled
            if success == True:
                # TODO: only get target where they exist in the dependencies map
                allow_scope = "" if scope == PatternScope.graph else "local_"
                if check_type == PatternCheckType.allow:
                    context[allow_scope + "allow"] |= context.get("target", set())
                elif check_type == PatternCheckType.disallow:
                    context[allow_scope + "disallow"] |= context.get("target", set())
            elif check_type == PatternCheckType.check:
                # if check, return empty sets with allow = False
                return {}, {}, False

        return {}, {}, True
        # TODO: correctly merge


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
        (PatternCheckType.check, PatternScope.graph, (
            ({"id":"Ego"}, {"type":"Has", "dir":">"}, {"tag":"v_0", "attr":set(["Instance", "Is"])}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"id":"Person"}),
        )),
    )

class r_Interaction_Action(ActionRule):

    patterns = (
        (PatternCheckType.allow, PatternScope.graph, (
            ({"id":"Person"}, {"type":"Has", "dir":"<"}, {"tag":"v_0", "attr":set(["Instance", "Is"])}),
            ({"ref":"v_0"}, {"type":"Has", "dir":"<"}, {"tag":"v_1", "target":True, "attr":set(["Instance"])}),
        )),
        (PatternCheckType.disallow, PatternScope.graph, (
            ({"id":"Person"}, {"type":"Is", "dir":"<"}, {"id":"Ego", "target":True}),
        )),
    )

class r_Conversation_Action(ActionRule): # TODO: maybe rewrite

    patterns = (
        (PatternCheckType.disallow, PatternScope.graph, (
            ({"id":"Ego"}, {"type":"Has", "dir":"<"}, {"tag":"v_0", "attr":set(["Instance", "Involved"])}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"id":"Combat_Context"}),
        )),
        (PatternCheckType.get, PatternScope.graph, (
            ({"id":"Ego"}, {"type":"Has", "dir":"<"}, {"tag":"v_1", "attr":set(["Instance", "Participant"])}),
            ({"ref":"v_1"}, {"type":"Has", "dir":">"}, {"tag":"v_2", "attr":set(["Conversation_Context"])}),
        )),
        (PatternCheckType.disallow, PatternScope.graph, (
            ({"context":"allowed", "target":True}, {"type":"Has", "dir":"<"}, {"tag":"v_3", "attr":set(["Instance", "Participant"])}),
            ({"ref":"v_3"}, {"type":"Has", "dir":">"}, {"tag":"v_4", "attr":set(["Instance", "Conversation_Context"])}),
            ({"ref":"v_4"}, {"Not_Is":""}, {"ref":"v_2"}),
        )),
    )

class r_Response_Conversation_Action(ActionRule): # TODO: rewrite

    patterns = (
        (PatternCheckType.get, PatternScope.graph, (
            ({"context":"allowed"}, {"type":"Has", "dir":">"}, {"tag":"v_0", "attr":set("Instance","Is")}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"id":"Person"})
        )),
        (PatternCheckType.allow, PatternScope.local, (
            ({"root":""}, {"type":"Can_Respond", "dir":">"}, {"tag":"v_2", "attr":set(["Action"])}),
            ({"ref":"v_2"}, {"type":"Has", "dir":">"}, {"tag":"v_3", "target":True, "attr":set(["Instance", "Target"])}),
            ({"ref":"v_3"}, {"type":"Has", "dir":">"}, {"id":"Recent"}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"tag":"v_4", "attr":set(["Instance", "Source"])}),
            ({"ref":"v_4"}, {"type":"Has", "dir":">"}, {"ref":"v_3"}),
            ({"id":"Ego"}, {"type":"Has", "dir":">"}, {"tag":"v_5", "attr":set(["Instance", "Target"])}),
            ({"ref":"v_5"}, {"type":"Has", "dir":">"}, {"ref":"v_2"})
        )),
        (PatternCheckType.disallow, PatternScope.local, (
            ({"ref":"v_3", "target":True}, {"type":"Response", "dir":"<"}, {"tag":"v_7", "attr":set(["Instance"])}),
            ({"ref":"v_7"}, {"type":"Has", "dir":"<"}, {"tag":"v_8", "attr":set(["Instance", "Source"])}),
            ({"ref":"v_8"}, {"type":"Has", "dir":">"}, {"id":"Ego"}),
        )),
    )

class r_Unique_Conversation_Action(ActionRule): # TODO: rewrite
    pattern = (
        (PatternCheckType.get, PatternScope.graph, (
            ({"context":"allowed"}, {"type":"Has", "dir":">"}, {"tag":"v_0", "attr":set("Instance","Is")}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"id":"Person"})
        )),

        (PatternCheckType.disallow, PatternScope.local, (
            ({"root":""}, {"type":"As_Unique", "dir":">"}, {"tag":"v_1", "attr":set(["Action"])}),
            ({"ref":"v_1"}, {"type":"Has", "dir":"<"}, {"tag":"v_2", "attr":set(["Instance", "Source"])}),
            ({"ref":"v_2"}, {"type":"Has", "dir":"<"}, {"tag":"v_3", "attr":set(["Instance", "Ego"])}),
            ({"ref":"v_1"}, {"type":"Has", "dir":"<"}, {"tag":"v_4", "attr":set(["Instance", "Target"])}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"ref":"v_4"}),
        )),
    )

class r_Friendly_Conversation_Action(ActionRule): # TODO: FINISH
    pattern = (
        (PatternCheckType.get, PatternScope.graph, (
            ({"context":"allowed", "alias":"v_0"}, {"type":"Has", "dir":">"}, {"tag":"v_1", "attr":set("Instance","Is")}),
            ({"ref":"v_0"}, {"type":"Has", "dir":">"}, {"id":"Person"})
        )),
        (PatternCheckType.disallow, PatternScope.graph, (
            ({"id":"Ego"}, {"type":"Has", "dir":">"}, {"tag":"v_1", "attr":set(["Instance", "Hostile_Relationship"])}),
            ({"ref":"v_1"}, {"type":"Has", "dir":"<"}, {"ref":"v_0", "target":True})
        )),
    )




"""

class PatternFetchType(Enum):
    null = 0
    instance = 1 # instance = vertex in graph
    allowed = 2 # instance = member of scope set, graph = target_set, local = local_target_set

class PatternScope(Enum):
    graph = 0 # target_set
    local = 1 # local_target_set

class PatternCheckType(Enum):
    check = 0 # if pattern succeeds, cool, if pattern fails, not cool
    allow = 1 # success: allow target to scope, fails: ignore
    disallow = 2 # success: disallow target to scope, fails: ignore
    get = 3 # ignore
"""

rules_map = {
    "Action": r_Action,
    "Interaction_Action": r_Interaction_Action,
    "Conversation_Action": r_Conversation_Action,
    "Response_Conversation_Action": r_Response_Conversation_Action,
    "Unique_Conversation_Action": r_Unique_Conversation_Action,
    "Friendly_Conversation_Action": r_Friendly_Conversation_Action,
}



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

Response_Action Rule

--Get Allowed--
Person <-Is- v_0("Instance", target)
--Allow Local--
root -Can_Respond-> v_1("Action")
v_1 <-Is- v_2("Instance", target)
v_2 -Is-> Recent
v_0 -Is-> v_3("Instance")
v_3 -Is-> Source
v_3 -Is-> v_2
Ego <-Is- v_4("Instance")
v_4 -Is-> v_5("Instance")
v_5 -Is-> Target
v_5 -Is-> v_1
--Disallow Local--
v_2 <-Response- v_6("Instance")
v_6 <-Is- v_7("Instance")
v_7 -Is-> Source
v_7 -Is-> v_4

================================================================

Unique_Action Rule

--Disallow Local--
Person <-Is- v_0("Instance") # get all people
root -As_Unique-> v_1("Action") # get set of actions which count as unique for the root
v_1 <-Is- v_2("Instance", "Source") # get instances of source of action
v_2 <-Is- v_3("Instance", "Ego")
v_1 <-Is- v_4("Instance", "Target")
v_0 -Is-> v_4

"""
