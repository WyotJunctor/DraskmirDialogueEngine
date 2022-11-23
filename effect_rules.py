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

    def add_entry(self, graph_delta):
        src_set = set()
        tgt_set = set()
        for pattern in self.vertex.shortcut_map:
            
            # get graph_delta
            pass

        # check whether base vertex is included in graph_event subgraph
        # check shortcut src and shortcut in graph event,
        #   create, check edge between src x tgt
        # add to internal map,
        # if local, instantiate new shortcut edge
        # if not, get associated shortcut edge?
            # if none, set up new one
        # add edge to managed edges
        pass
