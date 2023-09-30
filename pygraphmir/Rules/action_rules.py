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
def add_dependencies(dependencies, src, tgt, src_hop, tgt_hop):
    for vert in (src, tgt):
        if vert not in dependencies:
            dependencies[vert] = {"dependent_on":defaultdict(set), "dependent_count":defaultdict(int)}

    for pairs in ((src, tgt_hop, tgt), (tgt, src_hop, src)):
        dependencies[pairs[0]]["dependent_on"][pairs[1]].add(pairs[2])
        dependencies[pairs[0]]["dependent_count"][pairs[1]] += 1


def cleanup(cleanup_verts, context, dependencies, hop_count):
    cleaned = set(cleanup_verts)
    cleanup_queue = list(cleanup_verts)
    while len(cleanup_queue) > 0:
        root = cleanup_queue.pop(0)
        if root not in dependencies:
            continue
        for hop, vert_set in dependencies[root]["dependent_on"].items():
            hop_count[hop].discard(root)
            if len(hop_count[hop]) <= 0:
                return False
            for dep_vert in vert_set:
                if dep_vert in cleaned:
                    continue
                dependencies[dep_vert]["dependent_count"][hop] -= 1
                if dependencies[dep_vert]["dependent_count"][hop] <= 0:
                    cleaned.add(dep_vert)
                    cleanup_queue.append(dep_vert)
    context["removed"] |= cleaned
    return True

class ActionRule:

    def __init__(self, vertex):
        # add self to vertex action_rules
        self.vertex = vertex


    def check_relationships(self, graph, context, check_set, ref):
        valid_set = set()
        for v in check_set:
            success = True
            if "rel" in ref:
                for rel_key, rel_set in ref["rel"]:
                    if isinstance(rel_set, str):
                        rel_set = context.get(rel_set, set())
                    elif isinstance(rel_set, set):
                        rel_set = graph.get_verts_from_ids(rel_set)
                    if rel_set.issubset(v.get_relationships(rel_key)) == False:
                        success = False
                        break
            if success is True and "any_rel" in ref:
                for rel_key, rel_set in ref["any_rel"]:
                    if isinstance(rel_set, str):
                        rel_set = context.get(rel_set, set())
                    elif isinstance(rel_set, set):
                        rel_set = graph.get_verts_from_ids(rel_set)
                    if rel_set.isdisjoint(v.get_relationships(rel_key)) == True:
                        success = False
                        break
            if success is True and "not_rel" in ref:
                for rel_key, rel_set in ref["not_rel"]:
                    if isinstance(rel_set, str):
                        if rel_set not in context:
                            success = False
                            break
                        rel_set = context.get(rel_set, set())
                    elif isinstance(rel_set, set):
                        rel_set = graph.get_verts_from_ids(rel_set)
                    if rel_set.isdisjoint(v.get_relationships(rel_key)) == False:
                        success = False
                        break
            if success is True:
                valid_set.add(v)
        return valid_set


    def check_src(self, src_set, no_src_tgts, context, dependencies, hop_count):
        cleanup_set = src_set.intersection(no_src_tgts)
        if cleanup(cleanup_set, context, dependencies, hop_count) == False:
            return set(), set()
        valid_src = src_set.difference(no_src_tgts)
        valid_tgt = no_src_tgts.difference(src_set)
        return valid_src, valid_tgt


    def check_step(self, src_set, no_src_tgts, src_ref, edge, tgt_ref, graph, context, highlight_map, dependencies, hop_count, src_hop, tgt_hop):
        valid_src = set()
        valid_tgt = set()
        for src_vert in src_set:
            edge_map = src_vert.in_edges if edge["dir"] == "<" else src_vert.out_edges

            tgt_set = set()
            if "id" in tgt_ref and tgt_ref["id"] in get_key_set(edge_map.edgetype_to_id, edge["type"]):
                tgt_set = graph.get_verts_from_ids(tgt_ref["id"])
            elif "ref" in tgt_ref:
                if tgt_ref["alias"] in context:
                    tgt_set = context.get(tgt_ref["alias"], set()) & get_set(edge_map.edgetype_to_vertex, edge["type"])
                else:
                    tgt_set = edge_map.edgetype_to_vertex.get(edge["type"], set())

            tgt_set = self.check_relationships(graph, context, tgt_set, tgt_ref)

            no_src_tgts -= tgt_set

            if len(tgt_set) == 0:
                if cleanup(set([src_vert]), context, dependencies, hop_count) == False:
                    return set(), set()
                continue

            for tgt_vert in tgt_set:
                if "highlight_target" in src_ref:
                    highlight_map[self.vertex][tgt_vert].add(src_vert)
                elif "highlight_target" in tgt_ref:
                    highlight_map[self.vertex][src_vert].add(tgt_vert)
                valid_tgt.add(tgt_vert)
                if "ref" in src_ref and "ref" in tgt_ref:
                    add_dependencies(dependencies, src_vert, tgt_vert, src_hop, tgt_hop)

            valid_src.add(src_vert)

        for tgt_vert in no_src_tgts:
            if cleanup(set([tgt_vert]), context, dependencies, hop_count) == False:
                return set(), set()
        return valid_src, valid_tgt

    # paths is a map of id: list<paths>, each path is a list of fellas?... possibly just refs.

    def check_traversal(self, ego, graph, traversal, context, highlight_map, dependencies, hop_count, src_hop):
        src_ref, edge, tgt_ref = traversal
        for ref in (src_ref, tgt_ref):
            if "ref" in ref and "alias" not in ref:
                ref["alias"] = ref["ref"]

        valid_src = set()
        valid_tgt = set()
        src_set = set()
        tgt_hop = src_hop + 1

        if "ref" in src_ref:
            src_set = context.get(src_ref["alias"], set()) if "alias" in src_ref and src_ref["alias"] in context else context.get(src_ref["ref"], set())
        elif "id" in src_ref:
            src_set = graph.get_verts_from_ids(src_ref["id"])

        src_set = self.check_relationships(graph, context, src_set, src_ref)

        if len(src_set) == 0:
            return False

        no_src_tgts = set()
        if "ref" in tgt_ref:
            no_src_tgts = context.get(tgt_ref["alias"], set())

        if "Not_Is" in edge:
            cleanup_set = src_set.intersection(no_src_tgts)
            if cleanup(cleanup_set, context, dependencies, hop_count) == False:
                return False
            valid_src = src_set.difference(no_src_tgts)
            valid_tgt = no_src_tgts.difference(src_set)
        elif "null" in edge:
            # self, src_set, no_src_tgts, context, dependencies, hop_count
            valid_src, valid_tgt = self.check_src(src_set, no_src_tgts, context, dependencies, hop_count)
        else:
            #  def check_step(self, src_set, no_src_tgts, src_ref, edge, tgt_ref, graph, context, highlight_map, dependencies, hop_count, src_hop, tgt_hop):
            valid_src, valid_tgt = self.check_step(src_set, no_src_tgts, src_ref, edge, tgt_ref, graph, context, highlight_map, dependencies, hop_count, src_hop, tgt_hop)
        if len(valid_src) == 0 or (len(valid_tgt) == 0 and "null" not in edge):
            return False

        for ref, valid_set, hop in ((src_ref, valid_src, src_hop), (tgt_ref, valid_tgt, tgt_hop)):
            if "target" in ref:
                context["target"] = ref["alias"] if "alias" in ref else ref["ref"]
            if "alias" in ref:
                context[ref["alias"]] = valid_set
            if "ref" in ref:
                hop_count[hop] = valid_set

        return True


    def get_targets(self, ego, graph, target_set, local_target_set):
        context = {
            "allow": target_set["allow"].copy(),
            "disallow": target_set["disallow"].copy(),
            "local_allow": local_target_set["allow"].copy(),
            "local_disallow": local_target_set["disallow"].copy(),
            "root":set([self.vertex]),
            "ego":set([ego]),
        }
        if self.vertex.id == "Ask_Smalltalk" and self.__class__.__name__ == "r_Ask_Smalltalk":
            pass
        highlight_map = defaultdict(lambda: defaultdict(set))    
        for pattern in self.__class__.patterns:
            dependencies = dict()
            context["removed"] = set()
            context["target"] = ""
            hop_count = defaultdict(set) # TODO: change to set?
            check_type = pattern["check_type"]
            scope = pattern["scope"]
            success = True
            hop = 0
            for traversal in pattern["traversal"]:
                #  ego, graph, traversal, context, highlight_map, dependencies, hop_count, src_hop):
                success = self.check_traversal(ego, graph, traversal, context, highlight_map, dependencies, hop_count, hop)
                if success == False:
                    break
                hop += 1
            if (
                    success == True and
                    "target" in context and
                    scope in (PatternScope.graph, PatternScope.local) and
                    check_type in (PatternCheckType.allow, PatternCheckType.disallow, PatternCheckType.x_allow)):
                allow_scope = "" if scope == PatternScope.graph else "local_"
                action = "disallow" if check_type == PatternCheckType.disallow else "allow"
                targets = context[context["target"]] - context["removed"]
                if check_type == PatternCheckType.x_allow:
                    context[allow_scope + action] = targets
                else:
                    context[allow_scope + action] |= targets
            elif (
                    success == False and "target" in context and check_type == PatternCheckType.x_allow):
                allow_scope = "" if scope == PatternScope.graph else "local_"
                context[allow_scope + "disallow"] |= context[allow_scope+"allow"].copy()
            if (scope == PatternScope.terminal and
                    (PatternCheckType.allow, PatternCheckType.disallow)[success] == check_type):
                return dict(), dict(), dict(), False
        context["allow"] -= context["disallow"]
        context["local_allow"] -= context["disallow"] | context["local_disallow"]
        target_set = {"allow":context["allow"], "disallow":context["disallow"]}
        local_target_set = {"allow":context["local_allow"], "disallow":context["local_disallow"]}
        return target_set, local_target_set, highlight_map, True


class InheritedActionRule(ActionRule):
    def replicate(self, rule_map):
        visited = set([self.vertex])
        queue = [self.vertex]
        while len(queue) > 0:
            root = queue.pop(0)
            for edge in root.in_edges.edgetype_to_edge["Is"]:
                child = edge.src
                if child in visited:
                    continue
                rule_map[child].append(self.__class__(child))
                visited.add(child)
                queue.append(child)

class r_Action(ActionRule):

    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego", "rel":(("Is>",{"Person"}),)}, {"null":""}, dict()),
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
                    {"ref":"v_0", "alias":"v_0", "target":"", "rel":(("Is>",{"Instance","Person"}),), "not_rel":(("Is>",set(["Ego"])),)}
                ),
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, dict()),
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
                ({"ref":"ego"}, {"type":"Participant", "dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Instance","Conversation_Context"}),)}),
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                (
                    {"ref":"allow","alias":"v_1","target":"", "not_rel":(("Participant>", "v_0"),)}, 
                    {"type":"Participant", "dir":">"}, 
                    {"ref":"v_2", "rel":(("Is>", {"Context"}),)}
                ),
            )
        },
    )

"""
disallow
Ego -Involved-> Combat_Context
get
Ego -Participant-> v_0(Inherits:"Instance", Inherits:"Conversation_Context")
disallow instance graph
v_1(context:"allow", target) -Participant-> v_0
"""

class r_Response_Conversation_Action(InheritedActionRule): # TODO: rewrite

    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.local,
            "traversal":(
                ({"ref":"root"}, {"type":"Can_Respond","dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}), )}),
                (
                    {"id":"Immediate"},
                    {"type":"Has","dir":"<"},
                    {
                        "ref":"v_1",
                        "alias":"v_1",
                        "rel":(("Is>",{"Instance","Action"}),("Target<",set(["Ego"])),("Is>","v_0"),),
                        "any_rel":(("Source<","allow"),),
                        "not_rel":(("Has>",{"Recent"}),),
                    }
                ),
                (
                    {"ref":"v_1", "highlight_target":""},
                    {"type":"Source", "dir":"<"},
                    {"ref":"v_2", "alias":"v_2", "target":"", "not_rel":( ("Is>", set( ["Ego"] ) ), )}
                ),
            )
        },
    )

"""
allow local
root -Can_Respond-> v_0(Inherits:"Action")
Recent <-Has- v_1(Inherits:"Instance", Inherits:"Action", "Has":"Recent", "Target":"Ego", "Is":v_0, "Source":context["allow"], target)
"""


class r_Unique_Conversation_Action(InheritedActionRule): # TODO: rewrite
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.local,
            "traversal":(
                ({"ref":"root"}, {"type":"As_Unique", "dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}),)}),
                ({"ref":"ego"}, {"type":"Source","dir":">"}, {"ref":"v_1","alias":"v_1","any_rel":(("Is>","v_0"), )}),
                ({"ref":"allow","alias":"v_2","target":""}, {"type":"Target","dir":">"}, {"ref":"v_1", "alias":"v_1"}),
            )
        },
    )

class r_Combat_Action(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                (
                    {"ref":"ego"},
                    {"type":"Friendly_Relationship", "dir":">"},
                    {"ref":"allow", "alias":"v0", "target":""}
                ),
            )
        },
    )

class r_Friendly_Conversation_Action(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Hostile_Relationship","dir":">"}, {"ref":"v_0","alias":"v_0","target":"","rel":(("Is>",{"Instance","Person"}),)}),
            )
        },
    )

"""
disallow instance graph
Ego -Hostile_Relationship-> v_0(Inherits:"Instance", Inherits:"Person", target)
"""

class r_Greet(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Known_Relationship","dir":">"}, {"ref":"allow","alias":"v_0","target":""}),
            )
        },
    )

"""
disallow instance
Ego -Acknowledged-> v_1(context:"allow", target)
"""


class r_Engage(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                (
                    {"ref":"ego"},
                    {"type":"Participant","dir":">"},
                    {
                        "ref":"v_0",
                        "alias":"v_0",
                        "rel": (
                            (
                                "Is>", {"Instance","Conversation_Context"}
                            )
                        ,)
                    }
                ,)
            ,)
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Combat_Context"}),
                ({"id":"Combat_Context"}, {"type":"Participant","dir":"<"}, {"ref":"allow","alias":"v_1","target":""}),
            )
        },
    )

"""
disallow
Ego -Participant-> v_0(Inherits:"Instance", Inherits:"Conversation_Context")
disallow instance
Ego -Participant-> Combat_Context
Combat_Context <-Participant- v_1(context:"allow")
"""

class r_Attack(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Combat_Context"}),
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Person"}, {"type":"Is","dir":"<"}, {"ref":"allow","alias":"v_0","target":"","not_rel":(("Participant>",{"Combat_Context"}),)}),
            )
        },
    )

"""
check
Ego -Participant-> Combat_Context
disallow instance
Person <-Is- v_0(context:"allow", Not: "Participant":"Combat_Context")
"""

class r_Rest(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.terminal,
            "traversal":(
                (
                    {"id":"Person"}, 
                    {"type":"Is", "dir":"<"}, 
                    {"ref":"v_0", "alias":"v_0", "rel": (("Is>", {"Instance", "Person"}),), "not_rel":(("Is>", {"Ego"}), ) }
                ),
                # ({"id":"Room"}, {"type":"In","dir":"<"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Instance","Person"}),),"not_rel":(("Is>",{"Ego"}),)}),
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, dict()),
            )
        },
    )

"""
disallow
Room <-In- v_0(Inherits:"Instance", Inherits:"Person", not: Ego)
"""

"""
{
    "check_type":PatternCheckType.disallow,
    "scope":PatternScope.terminal,
    "traversal":(
        (
            {"id":"Immediate"}, 
            {"type":"Is","dir":"<"}, 
            {
                "ref":"v_0","alias":"v_0",
                "rel":(("Is>",{"Instance","Action"}),),
                "not_rel":( ("Is>", {"Inactive_Action"} ), )
            }
        ),
    )
},
"""

class r_Wait(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"ego", "target":""}, {"null":""}, dict()),
            )
        },
    )

class r_Loot(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Bystander","dir":">"}, {"id":"Calm_Context"}),
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Dead"}, {"type":"Is","dir":"<"}, {"ref":"v_0","alias":"v_0","target":"","rel":(("Is>",{"Instance","Dead"}),("Was>",{"Person"}),)}),
            )
        },
    )

"""
allow
Ego -Participant-> Calm
allow instance graph
Dead <-Is- v_0(Inherits:"Instance", Inherits:"Dead", "Was":"Person")
"""

class r_Flee(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participation","dir":">"}, {"id":"Combat"}),
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Door"}, {"type":"Is","dir":"<"}, {"ref":"v_0","alias":"v_0","target":"","rel":(("Is>",{"Instance"}),)}),
            )
        },
    )

"""
allow
Ego -Participant-> Combat
allow instance graph
Door <-Is- v_0(Inherits:"Instance", Inherits:"Door")
"""

"""
class r_Enter(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Source","dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Instance","Traverse"}),("Has>",{"Immediate"}),)}),
            )
        },
    )
"""

class r_Traverse(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.terminal,
            "traversal":(
                ({"ref":"ego"}, {"type":"Participant","dir":">"}, {"id":"Calm_Context"}),
            )
        },
        {
            "check_type":PatternCheckType.allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"id":"Door"}, {"type":"Is","dir":"<"}, {"ref":"v_0","alias":"v_0","target":"","rel":(("Is>",{"Instance"}),)}),
            )
        },
    )


class r_SendOff(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.x_allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"root"}, {"type":"Can_Respond","dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}), )}),
                (
                    {"id":"Immediate"},
                    {"type":"Has","dir":"<"},
                    {
                        "ref":"v_1",
                        "alias":"v_1",
                        "rel":(("Is>",{"Instance","Action"}),("Target<",set(["Ego"])),("Is>","v_0"),),
                        "any_rel":(("Source<","allow"),),
                        "not_rel":(("Has>",{"Recent"}),),
                    }
                ),
                (
                    {"ref":"v_1", "highlight_target":""},
                    {"type":"Source", "dir":"<"},
                    {"ref":"v_2", "alias":"v_2", "target":"", "not_rel":( ("Is>", set( ["Ego"] ) ), )}
                ),
            )
        },
    )

class r_Respond_Smalltalk(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.x_allow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"root"}, {"type":"Can_Respond","dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}), )}),
                (
                    {"id":"Immediate"},
                    {"type":"Has","dir":"<"},
                    {
                        "ref":"v_1",
                        "alias":"v_1",
                        "rel":(("Is>",{"Instance","Action"}),("Target<",set(["Ego"])),("Is>","v_0"),),
                        "any_rel":(("Source<","allow"),),
                        "not_rel":(("Has>",{"Recent"}),),
                    }
                ),
                (
                    {"ref":"v_1", "highlight_target":""},
                    {"type":"Source", "dir":"<"},
                    {"ref":"v_2", "alias":"v_2", "target":"", "not_rel":( ("Is>", set( ["Ego"] ) ), )}
                ),
            )
        },
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                (
                    {"id":"Person"},
                    {"type":"Is", "dir":"<"},
                    {
                        "ref":"v_3", "alias":"v_3", "target":"", 
                        "rel":(("Is>",{"Instance","Person"}),), 
                        "not_rel":((("Is>", "v_2"),))
                    }
                ),
            )
        },
    )


class r_Ask_Smalltalk(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"root"}, {"type":"Answered_By","dir":">"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}), )}),
                (
                    {"ref":"v_0"},
                    {"type":"Is","dir":"<"},
                    {
                        "ref":"v_1",
                        "alias":"v_1",
                        "rel":(("Is>",{"Instance","Action"}),("Target<",set(["Ego"]))),
                    }
                ),
                (
                    {"ref":"v_1"},
                    {"type":"Source", "dir":"<"},
                    {
                        "ref":"v_2",
                        "target":"",
                    }
                )
            )
        },
    )

class r_Offer_Smalltalk(ActionRule):
    patterns = (
        {
            "check_type":PatternCheckType.disallow,
            "scope":PatternScope.graph,
            "traversal":(
                ({"ref":"root"}, {"type":"Answered_By","dir":"<"}, {"ref":"v_0","alias":"v_0","rel":(("Is>",{"Action"}), )}),
                (
                    {"ref":"v_0"},
                    {"type":"Is","dir":"<"},
                    {
                        "ref":"v_1",
                        "alias":"v_1",
                        "rel":(("Is>",{"Instance","Action"}),("Target<",set(["Ego"]))),
                    }
                ),
                (
                    {"ref":"v_1"},
                    {"type":"Source", "dir":"<"},
                    {
                        "ref":"v_2",
                        "target":"",
                    }
                )
            )
        },
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
    "Combat_Action": r_Combat_Action,
    "Greet": r_Greet,
    "Engage": r_Engage,
    "Attack": r_Attack,
    "Rest": r_Rest,
    "Wait": r_Wait,
    "Loot": r_Loot,
    "Flee": r_Flee,
    # "Enter": r_Enter,
    "Traverse": r_Traverse,
    "Send_Off": r_SendOff,
    "Respond_Smalltalk": r_Respond_Smalltalk,
    "Offer_Smalltalk": r_Offer_Smalltalk,
}
