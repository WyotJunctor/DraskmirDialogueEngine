import copy
from enum import Enum
from utils import merge_targets, get_set, get_key_set
from collections import defaultdict, Counter

class PatternScope(Enum):
    graph = 0 # target_set
    local = 1 # local_target_set
    terminal = 2

class PatternCheckType(Enum):
    allow = 0 # success: allow target to scope, fails: ignore
    disallow = 1 # success: disallow target to scope, fails: ignore
    get = 2 # ignore
    x_allow = 3 # disallow everything else that was previously allowed

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


def cleanup(cleanup_verts, context, dependencies, hop_count):
    cleaned = cleanup_verts
    cleanup_queue = list(cleanup_verts)
    while len(cleanup_queue) > 0:
        root = cleanup_queue.pop(0)
        for hop, vert_set in dependencies[vert]["dependent_on"].items():
            hop_count[hop].remove(root)
            if len(hop_count[hop]) <= 0:
                return False
            for dep_vert in vert_set:
                if dep_vert in cleaned:
                    continue
                dependencies[dep_vert]["dependent_count"][hop] -= 1
                if dependencies[dep_vert]["dependent_count"][hop] <= 0:
                    cleanup_queue.add(dep_vert)
    context["removed"] += cleaned
    return True

class ActionRule:

    def __init__(self, vertex, rules, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        rules.append(self)
        rules.sort(key=lambda x: x.priority)


    def check_relationships(self, context, check_set, ref):
        valid_set = set()
        for v in check_set:
            success = True
            if "rel" in ref:
                for rel_key, rel_set in ref["rel"]:
                    if isinstance(rel_set, str):
                        rel_set = context[rel_set]
                    if rel_set.issubset(v.relationship_map["rel_key"]) == False:
                        success = False
                        break
            if "no_rel" in ref:
                for rel_key, rel_set in ref["no_rel"]:
                    if isinstance(rel_set, str):
                        rel_set = context[rel_set]
                    if rel_set.isdisjoint(v.relationship_map["rel_key"]) == False:
                        success = False
                        break
            if success == True:
                valid_set.add(v)
        return valid_set


    def check_src(self, src_set, no_src_tgts, context, dependencies, hop_count):
        cleanup_set = src_set.intersection(no_src_tgts)
        if cleanup(cleanup_set, context, dependencies, hop_count) == False:
            return set(), set()
        valid_src = src_set.difference(no_src_tgts)
        valid_tgt = no_src_tgts.difference(src_set)
        return valid_src, valid_tgt


    def check_step(self, src_set, no_src_tgts, edge, tgt_ref, context, dependencies, hop_count, src_hop, tgt_hop):
        valid_src = set()
        valid_tgt = set()
        for src_vert in src_set:
            edge_map = src_vert.in_edges if edge["dir"] == "<" else src_vert.out_edges

            tgt_set = set()
            if "id" in tgt_ref and tgt_ref["id"] in get_key_set(edge_map.edgetype_to_id, edge["type"]):
                tgt_set = get_set(graph.vertices, tgt_ref["id"])
            elif "ref" in tgt_ref:
                tgt_set = context.get(tgt_ref["ref"], set()) & get_set(edge_map.edgetype_to_vertex, edge["type"])
            elif "tag" in tgt_ref:
                tgt_set = get_set(edge_map.edgetype_to_vertex, edge["type"])

            tgt_set = self.check_relationships(context, tgt_set, tgt_ref)

            no_src_tgts -= tgt_set

            if len(tgt_set) == 0:
                if cleanup(set([src_vert]), context, dependencies, hop_count) == False:
                    return set(), set()
                continue

            if "ref" in src_ref and "ref" in tgt_ref:
                for tgt_vert in tgt_set:
                    valid_tgt.add(tgt_vert)
                    add_dependencies(dependencies, src_vert, tgt_vert, src_hop, tgt_hop)

            valid_src.add(src_vert)

        for tgt_vert in no_src_tgts:
            if cleanup(set([tgt_vert]), context, dependencies, hop_count) == False:
                return set(), set()
        return valid_src, valid_tgt

    # paths is a map of id: list<paths>, each path is a list of fellas?... possibly just refs.

    def check_traversal(self, ego, graph, traversal, dependencies, context, hop_count, src_hop):

        src_ref, edge, tgt_ref = traversal

        valid_src = set()
        valid_tgt = set()
        src_set = set()
        tgt_hop = src_hop + 1

        if "ref" in src_ref:
            src_set = context.get(src_ref["ref"], set())
        elif "id" in src_ref:
            src_set = get_set(graph.vertices, src_ref["id"])

        src_set = self.check_relationships(context, src_set, src_ref)

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
        elif "null" in edge:
            valid_src, valid_tgt = self.check_step(ego, src_set, no_src_tgts, context, dependencies, hop_count, src_hop, tgt_hop)
        else:
            valid_src, valid_tgt = self.check_src(src_set, no_src_tgts, edge, tgt_ref, context, dependencies, hop_count, src_hop, tgt_hop)

        if len(valid_src) == 0 or len(valid_tgt) == 0:
            return False

        for ref, valid_set, hop in ((src_ref, valid_src, src_hop), (tgt_ref, valid_tgt, tgt_hop)):
            if "target" in ref:
                context["target"] = ref["alias"]
            if "alias" in ref:
                context[ref["alias"]] = valid_set
            if "ref" in ref:
                hop_count[hop] = valid_set

        return True


    def get_targets(self, ego, graph, target_set, local_target_set):
        context = {
            "allowed": target_set["allow"].copy(),
            "disallowed": target_set["disallow"].copy(),
            "local_allowed": local_target_set["allow"].copy(),
            "local_disallowed": local_target_set["disallow"].copy(),
            "root":set([self.vertex]),
            "ego":set([ego]),
        }
        for pattern in self.__class__.patterns:
            dependencies = {}
            context["removed"] = set()
            hop_count = defaultdict(set) # TODO: change to set?
            check_type = pattern["check_type"]
            scope = pattern["scope"]
            success = True
            hop = 0
            for traversal in pattern["traversal"]:
                success = self.check_traversal(traversal, dependencies, context, hop_count, hop)
                if success == False:
                    break
                hop += 1
            if (
                    success == True and
                    "target" in context and
                    scope in (PatternScope.graph, PatternScope.local) and
                    check_type in (PatternCheckType.allow, PatternCheckType.disallow, PatternCheckType.x_allow)):
                allow_scope = "" if scope == PatternScope.graph else "local_"
                action = "disallow" if PatternCheckType.disallow else "allow"
                targets = context[context["target"]] - context["removed"]
                if check_type == PatternCheckType.x_allow:
                    context[allow_scope + action] = targets
                else:
                    context[allow_scope + action] |= targets
            if (scope == PatternScope.terminal and
                    (PatternCheckType.allow, PatternCheckType.disallow)[success] == check_type):
                return {}, {}, False
        context["allow"] -= context["disallow"]
        context["local_allow"] -= context["disallow"] + context["local_disallow"]
        target_set = {"allow":context["allow"], "disallow":context["disallow"]}
        local_target_set = {"allow":context["local_allow"], "disallow":context["local_disallow"]}
        return target_set, local_target_set, True


class InheritedActionRule:

    def __init__(self, vertex, rules, priority=0, replicate=True):
        if replicate is True:
            self.replicate(vertex)
        super().__init__(vertex, rules, priority)

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
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego", "rel":(("Is>",set(["Person"])))}, {"null":""}, {})
            )
        },
    )

"""
allow graph
Ego(Inherits:"Person")
"""

class r_Interaction_Action(ActionRule):

    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                (
                    {"id":"Person"},
                    {"type":"Is", "dir":"<"},
                    {"tag":"v_0", "alias":"v_0", "target":"", "rel":(("Is>",set(["Instance","Person"]))), "not_rel":(("Is>",set(["Ego"])))}
                ),
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, {})
            )
        }
    )

"""
allow instance graph
Person <-Is- v_0(Inherits:"Instance", Inherits:"Person", Not: Inherits:"Ego", target)
disallow instance graph
Ego(target)
"""

class r_Conversation_Action(ActionRule): # TODO: maybe rewrite

    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Involved", "dir":">"}, {"id":"Combat_Context"}),
            )
        },
        {
            "check_type":PatternCheckType.get,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant", "dir":">"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Instance","Conversation_Context"])))})
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"allowed","alias":"v_1","target":""}, {"type":"Participant",">"}, {"ref":"v_0"})
            )
        },
    )

"""
disallow
Ego -Involved-> Combat_Context
get
Ego -Participant-> v_0(Inherits:"Instance", Inherits:"Conversation_Context")
disallow instance graph
v_1(context:"allowed", target) -Participant-> v_0
"""

class r_Response_Conversation_Action(InheritedActionRule): # TODO: rewrite

    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.local,
            "traversal":(
                ({"ref":"root"}, {"type":"Can_Respond","dir":">"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Action"])))}),
                (
                    {"id":"Recent"},
                    {"type":"Has_Attr","dir":"<"},
                    {"tag":"v_1","alias":"v_1","target":"",
                        "rel":(("Is>",set(["Instance","Action"])),("Target<",set(["Ego"])),("Is>","v_0"),("Source<","allowed"))
                    }
                ),
            )
        }
    )

"""
allow local
root -Can_Respond-> v_0(Inherits:"Action")
Recent <-Has_Attr- v_1(Inherits:"Instance", Inherits:"Action", "Has":"Recent", "Target":"Ego", "Is":v_0, "Source":context["allowed"], target)
"""

class r_Unique_Conversation_Action(InheritedActionRule): # TODO: rewrite
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.local,
            "traversal":(
                ({"ref":"root"}, {"type":"As_Unique", "dir":">"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Action"])))}),
                ({"ref":"ego"}, {"type":"Source","dir":">"}, {"tag":"v_1","alias":"v_1","rel":(("Is>","v_0"))}),
                ({"ref":"allowed","alias":"v_2","target":""}, {"type":"Target","dir":">"}, {"ref":"v_1"}),
            )
        },
    )

"""
disallow instance local
root -As_Unique-> v_0(Inherits:"Action")
Ego -Source-> v_1(Inherits:v_0)
v_2(context:"allowed", target) -Target-> v_1
"""

class r_Friendly_Conversation_Action(ActionRule): # TODO: FINISH
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Hostile_Relationship","dir":">"}, {"tag":"v_0","alias":"v_0","target":"","rel":(("Is>",set(["Instance","Person"])))})
            )
        }
    )

"""
disallow instance graph
Ego -Hostile_Relationship-> v_0(Inherits:"Instance", Inherits:"Person", target)
"""

class r_Greet(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Acknowledged","dir":">"}, {"ref":"allowed","alias":"v_0","target":""})
            )
        }
    )

"""
disallow instance
Ego -Acknowledged-> v_1(context:"allowed", target)
"""

class r_Engage(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Instance","Conversation_Context"])))})
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Combat_Context"}),
                ({"id":"Combat_Context"}, {"type":"Participant","dir":"<"}, {"ref":"allowed","alias":"v_1","target"})
            )
        },
    )

"""
disallow
Ego -Participant-> v_0(Inherits:"Instance", Inherits:"Conversation_Context")
disallow instance
Ego -Participant-> Combat_Context
Combat_Context <-Participant- v_1(context:"allowed")
"""

class r_Attack(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Combat_Context"})
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.instance,
            "traversal":(
                ({"id":"Person"}, {"type":"Is","dir":"<"}, {"ref":"allowed","alias":"v_0","target":"","not_rel":(("Participant>",set(["Combat_Context"])))})
            )
        }
    )

"""
check
Ego -Participant-> Combat_Context
disallow instance
Person <-Is- v_0(context:"allowed", Not: "Participant":"Combat_Context")
"""

class r_Rest(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"id":"Room"}, {"type":"In","dir":"<"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Instance","Person"]))),"not_rel":(("Is>",set(["Ego"])))})
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, {})
            )
        }
    )

"""
disallow
Room <-In- v_0(Inherits:"Instance", Inherits:"Person", not: Ego)
"""

class r_Wait(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"id":"Immediate"}, {"type":"Is","dir":"<"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Instance","Action"]))),"not_rel":(("Is>":set(["Inactive_Action"])))})
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, {})
            )
        }
    )

"""
disallow
Immediate <-Is- v_0(Inherits:"Instance", Inherits:"Action", not: Inherits:"InactiveAction")
"""

class r_Loot(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Calm_Context"})
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Dead"}, {"type":"Is","dir":"<"}, {"tag":"v_0","alias":"v_0","target":"","rel":(("Is>",set(["Instance","Dead"])),("Was>",set(["Person"])))})
            )
        }
    )

"""
allow
Ego -Participant-> Calm
allow instance graph
Dead <-Is- v_0(Inherits:"Instance", Inherits:"Dead", "Was":"Person")
"""

class r_Flee(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participation","dir":">"}, {"id":"Combat"})
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Door"}, {"type":"Is","dir":"<"}, {"tag":"v_0","alias":"v_0","target":"","rel":(("Is>",set(["Instance"])))})
            )
        }
    )

"""
allow
Ego -Participant-> Combat
allow instance graph
Door <-Is- v_0(Inherits:"Instance", Inherits:"Door")
"""

class r_Enter(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Source","dir":">"}, {"tag":"v_0","alias":"v_0","rel":(("Is>",set(["Instance","Traverse"])),("Has_Attr>",set(["Immediate"])))})
            )
        }
    )

"""
allow, force
Ego -Source-> v_0(Inherits:"Instance", Inherits:"Traverse", "Has":"Immediate")
"""

class r_Traverse(ActionRule):
    pattern = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Calm_Context"})
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Door"}, {"type":"Is","dir":"<"}, {"tag":"v_0","alias":"v_0","target":"","rel":(("Is>",set(["Instance"])))})
            )
        }
    )

"""
allow
Ego -Participant-> Calm
allow instance
Door <-Is- v_0(Inherits:"Instance", Inherits:"Door")
"""

rules_map = {
    "Action": r_Action,
    "Interaction_Action": r_Interaction_Action,
    "Conversation_Action": r_Conversation_Action,
    "Response_Conversation_Action": r_Response_Conversation_Action,
    "Unique_Conversation_Action": r_Unique_Conversation_Action,
    "Friendly_Conversation_Action": r_Friendly_Conversation_Action,
    "Greet": r_Greet,
    "Engage": r_Engage,
    "Attack": r_Attack,
    "Rest": r_Rest,
    "Wait": r_Wait,
    "Loot": r_Loot,
    "Flee": r_Flee,
    "Enter": r_Enter,
    "Traverse": r_Traverse,
}