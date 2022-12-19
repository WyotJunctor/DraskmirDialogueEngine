from collections import defaultdict, Counter

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
        self.relationship_map = defaultdict(set)
        self.relationship_map["Is>"].add(self)
        # ({"src":"Pred","src_dir":"<","tgt":"Pred","tgt_dir":">"},)
        self.shortcut_map = shortcut_map
        super().__init__(created_timestep, updated_timestep, attr_map)

    def clear_secondary_relationships(self):
        lineage = self.relationship_map["Is>"]
        self.relationship_map = defaultdict(set)
        self.relationship_map["Is>"] = lineage

    def __repr__(self):
        return f"|{self.id}| {id(self)}" # f"{self.id}, {self.attr_map}"

    def add_edge(self, edge, endpoint, target=False, twoway=False):
        if twoway or not target:
            self.out_edges.add(edge, endpoint)
        if twoway or target:
            self.in_edges.add(edge, endpoint)

    def remove_edge(self, edge):

        endpoint = edge.tgt if edge.tgt is not self else edge.src

        if edge.twoway:
            self.in_edges.remove(edge, endpoint)
            self.out_edges.remove(edge, endpoint)
        elif self is edge.src:
            self.out_edges.remove(edge, endpoint)
        elif self is edge.tgt:
            self.in_edges.remove(edge, endpoint)

    def remove_edges_with(self, vertex):
        self.in_edges.remove_edges_with(vertex)
        self.out_edges.remove_edges_with(vertex)


    def consolidate_relationships(self, called_from=None):

        for out_edge in self.out_edges.edge_set:
            tgt = out_edge.tgt if out_edge.tgt is not self else out_edge.src

            if tgt is not called_from:
                tgt.consolidate_relationships(self)

            for edge_type in out_edge.edge_type:
                self.relationship_map[edge_type + ">"].add(tgt)
                self.relationship_map[edge_type + ">"] |= tgt.relationship_map["Is>"]

        for in_edge in self.in_edges.edge_set:
            src = in_edge.src if in_edge.src is not self else in_edge.tgt
            for edge_type in in_edge.edge_type:
                self.relationship_map[edge_type + "<"].add(src)


class Edge(GraphObject):

    def __init__(self, edge_type:set, src:Vertex, tgt:Vertex, created_timestep, updated_timestep, attr_map=None, twoway=False):
        self.id = f"{src.id}~{edge_type}~{tgt.id}"
        self.edge_type = edge_type
        self.src = src
        self.tgt = tgt
        self.twoway = twoway
        src.add_edge(self, tgt, twoway=twoway)
        tgt.add_edge(self, src, target=True, twoway=twoway)
        super().__init__(created_timestep, updated_timestep, attr_map)
        # TODO: add logic for twoway

    def __repr__(self):
        return f"({self.src.id})-({self.tgt.id})"