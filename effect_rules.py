from collections import defaultdict
from graph_event import GraphEvent, GraphDelta, EventType, EventTarget


class EffectRule:

    def __init__(self, vertex, rules, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        rules.append(self)
        rules.sort(key=lambda x: x.priority)

    def receive_delta(self, vertex, graph):
        pass

    def generate_deltas(self, lineage_add, lineage_remove):
        pass

class er_AddPerson(EffectRule):
    def receive_delta(self, graph_delta, graph):
        target_vertex = graph_delta.graph_object
        src_set = set()
        tgt_set = set()
        for pattern in self.vertex.shortcut_map:
            # ({"src":("Pred", "<"),"tgt":("Pred", ">")},)
            for key,obj_set in (("src", src_set), ("tgt", tgt_set)):
                edge_map = target_vertex.in_edges.edgetype_to_vertex if pattern[key][1] == "<" else target_vertex.out_edges.edgetype_to_vertex
                obj_set += edge_map.get(pattern[key][0], set())
        for src_v in src_set:
            for tgt_v in tgt_set:
                shortcut = graph.load_edge({
                      "directed": True,
                      "edge_type": target_vertex.id,
                      "src": src_v.id,
                      "tgt": tgt_v.id
                      })
                self.managed_shortcuts[target_vertex].add(shortcut)

        graph_deltas = list()
        lineage_add, lineage_remove = graph.consolidate_relationships(src_v | tgt_v)
        for vert, add_set in lineage_add.items():
            graph_deltas.add(GraphDelta(
                EventType.Add,
                EventTarget.Vertex,
                add_set,
                vert
            ))
        return graph_deltas

class er_AddShortcut(EffectRule):
    # map shortcut vertices to set of edges
    def __init__(self, vertex, rules, priority=0):
        super().__init__(vertex, rules, priority)
        self.managed_shortcuts = defaultdict(set)

    def receive_delta(self, graph_delta, graph):
        target_vertex = graph_delta.graph_object
        src_set = set()
        tgt_set = set()
        for pattern in self.vertex.shortcut_map:
            # ({"src":("Pred", "<"),"tgt":("Pred", ">")},)
            for key,obj_set in (("src", src_set), ("tgt", tgt_set)):
                edge_map = target_vertex.in_edges.edgetype_to_vertex if pattern[key][1] == "<" else target_vertex.out_edges.edgetype_to_vertex
                obj_set += edge_map.get(pattern[key][0], set())
        for src_v in src_set:
            for tgt_v in tgt_set:
                shortcut = graph.load_edge({
                      "directed": True,
                      "edge_type": target_vertex.id,
                      "src": src_v.id,
                      "tgt": tgt_v.id
                      })
                self.managed_shortcuts[target_vertex].add(shortcut)

        graph_deltas = list()
        lineage_add, lineage_remove = graph.consolidate_relationships(src_v | tgt_v)
        for vert, add_set in lineage_add.items():
            graph_deltas.add(GraphDelta(
                EventType.Add,
                EventTarget.Vertex,
                add_set,
                vert
            ))
        return graph_deltas
