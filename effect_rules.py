from collections import defaultdict


class EffectRule:

    def __init__(self, vertex, rules, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        rules.append(self)
        rules.sort(key=lambda x: x.priority)

    def receive_event(self, graph_event):
        pass

class InheritedEffectRule(EffectRule):
    pass

class er_Shortcut(InheritedEffectRule):
    # map shortcut vertices to set of edges
    def __init__(self, vertex, rules, priority=0):
        super().__init__(vertex, rules, priority)
        self.managed_shortcuts = defaultdict(set)

    def add_entry(self, target_vertex, graph_delta):
        src_set = set()
        tgt_set = set()
        for pattern in self.vertex.shortcut_map:
            # ({"src":("Pred", "<"),"tgt":("Pred", ">")},)
            for key,obj_set in (("src", src_set), ("tgt", tgt_set)):
                edge_map = target_vertex.in_edges.edgetype_to_vertex if pattern[key][1] == "<" else target_vertex.out_edges.edgetype_to_vertex
                obj_set += edge_map.get(pattern[key][0], set())
        for src_v in src_set:
            for tgt_v in tgt_set:
                pass
                # insert edge...
