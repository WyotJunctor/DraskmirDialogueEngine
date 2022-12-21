from collections import defaultdict, Counter
from utils import to_counter

class EdgeMap:
    def __init__(self):
        self.edge_set = set()
        self.id_to_edgetype = defaultdict(Counter)
        self.id_to_edge = defaultdict(set)
        self.edgetype_to_id = defaultdict(Counter)
        self.edgetype_to_edge = defaultdict(set)
        self.edgetype_to_vertex = defaultdict(set)

    def add(self, edge, endpoint):
        self.edge_set.add(edge)
        self.id_to_edge[endpoint.id].add(edge)
        for edge_type in edge.edge_type:
            self.id_to_edgetype[endpoint.id].update({edge_type:1})
            self.edgetype_to_id[edge_type].update({endpoint.id:1})
            self.edgetype_to_edge[edge_type].add(edge)
            self.edgetype_to_vertex[edge_type].add(endpoint)

    # optimize?
    def remove(self, edge, endpoint):
        self.edge_set.remove(edge)
        self.id_to_edge[endpoint.id].remove(edge)
        if len(self.id_to_edge[endpoint.id]) == 0:
            del self.id_to_edge[endpoint.id]

        for indexer, index_type, other_key, edge_key in (
            (self.id_to_edgetype, "counter", endpoint.id, "tgt"),
            (self.edgetype_to_id, "counter", endpoint.id, "src"),
            (self.edgetype_to_edge, "set", edge, "src"),
            (self.edgetype_to_vertex, "set", endpoint, "tgt")):
            for edge_type in edge.edge_type:
                if edge_key == "src":
                    src_key = edge_type
                    tgt_key = other_key
                else:
                    tgt_key = edge_type
                    src_key = other_key
                if index_type == "counter":
                    indexer[src_key].update({tgt_key:-1})
                    if indexer[src_key] == 0:
                        del indexer[src_key][tgt_key]
                elif index_type == "set":
                    indexer[src_key].remove(tgt_key)
                    if len(indexer[src_key]) == 0:
                        del indexer[src_key][tgt_key]

    def remove_edges_with(self, vertex):

        edgetypes = self.id_to_edgetype[vertex.id]
        edges = self.id_to_edge[vertex.id]

        self.edge_set -= edges
        del self.id_to_edgetype[vertex.id]
        del self.id_to_edge[vertex.id]

        for edgetype in edgetypes:
            del self.edgetype_to_id[edgetype]

            for edge in edges:
                self.edgetype_to_edge[edgetype].remove(edge)

            self.edgetype_to_vertex[edgetype].remove(edge)


class GraphObject:

    def __init__(self, created_timestep=None, updated_timestep=None, attr_map=None):
        self.created_timestep = created_timestep
        self.updated_timestep = updated_timestep
        self.attr_map = dict() if attr_map is None else attr_map
        self.event_map = defaultdict(set)

    def subscribe(self, subscriber, event_key):
        self.event_map[event_key].add(subscriber)

    def delete(self):
        for subscriber in self.event_map["delete"]:
            subscriber() # NOTE: when we need templated event-listener we'll add it


class Vertex(GraphObject):

    def __init__(self, id, created_timestep, updated_timestep, shortcut_map=None, attr_map=None):
        self.id = id
        self.in_edges = EdgeMap()
        self.out_edges = EdgeMap()
        self.relationship_map = defaultdict(Counter)
        self.relationship_map["Is>"][self] = 1
        # ({"src":"Pred","src_dir":"<","tgt":"Pred","tgt_dir":">"},)
        self.shortcut_map = shortcut_map
        super().__init__(created_timestep, updated_timestep, attr_map)

    def get_relationships(self, key, exclude_self=False, as_counter=False):
        if key in self.relationship_map:
            result = set(self.relationship_map[key].keys())
            if exclude_self:
                result.remove(self)
            if as_counter == True:
                return to_counter(result)
            return result
        return set()

    def clear_secondary_relationships(self):
        lineage = self.relationship_map["Is>"]
        self.relationship_map = defaultdict(Counter)
        self.relationship_map["Is>"] = lineage

    def __repr__(self):
        return f"|{self.id}| {id(self)}" # f"{self.id}, {self.attr_map}"

    def update_relationships(self, target_counter:Counter, add:bool):
        result_set = set()
        for key,value in target_counter.items():
            if add == True:
                if key not in self.relationship_map:
                    result_set.add(key)
                self.relationship_map[key] += value
            elif key in self.relationship_map:
                self.relationship_map[key] -= value
                if self.relationship_map[key] <= 0:
                    del self.relatipnship_map[key]
                    result_set[key].add(key)

        return result_set

    def propagate_lineage_delta(self, updated_lineage:set, add:bool):
        lineage_counter = to_counter(updated_lineage)
        for edge_map in (self.in_edges, self.out_edges):
            for edge_type, target in edge_map.edgetype_to_vertex.items():
                if edge_type != "Is":
                    target.update_relationships(lineage_counter, add=add)

    def add_edge(self, edge, twoway=False, update_relationships=True):
        target = edge.tgt == self
        endpoint = edge.tgt if edge.tgt is not self else edge.src
        result = set()

        if twoway or not target:
            self.out_edges.add(edge, endpoint)
        if twoway or target:
            self.in_edges.add(edge, endpoint)

        if update_relationships == True:
            result = self.update_relationships(endpoint.get_relationships("Is>", as_counter=True), add=True)

        return result

    def remove_edge(self, edge, update_relationships=True):

        endpoint = edge.tgt if edge.tgt is not self else edge.src
        result = set()

        if edge.twoway:
            self.in_edges.remove(edge, endpoint)
            self.out_edges.remove(edge, endpoint)
        elif self is edge.src:
            self.out_edges.remove(edge, endpoint)
        elif self is edge.tgt:
            self.in_edges.remove(edge, endpoint)

        if update_relationships == True:
            result = self.update_relationships(endpoint.get_relationships("Is>", as_counter=True), add=False)

        return result

    def remove_edges_with(self, vertex):
        self.in_edges.remove_edges_with(vertex)
        self.out_edges.remove_edges_with(vertex)


class Edge(GraphObject):

    def __init__(self, edge_type:set, src:Vertex, tgt:Vertex, created_timestep, updated_timestep, attr_map=None, twoway=False):
        self.id = f"{src.id}~{edge_type}~{tgt.id}"
        self.edge_type = edge_type
        self.src = src
        self.tgt = tgt
        self.twoway = twoway
        super().__init__(created_timestep, updated_timestep, attr_map)
        # TODO: add logic for twoway

    def __repr__(self):
        return f"({self.src.id})-({self.tgt.id})"
