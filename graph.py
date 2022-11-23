import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

from graph_event import GraphDelta, GraphEvent, EventType


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
        # ({"src":"Pred","src_dir":"<","tgt":"Pred","tgt_dir":">"},)
        self.shortcut_map = shortcut_map
        super().__init__(created_timestep, updated_timestep, attr_map)

    def __repr__(self):
        return f"{self.id}, {self.attr_map}"

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


    def consolidate_relationships(self):

        for out_edge in self.out_edges.edge_set:
            tgt = out_edge.tgt if out_edge.tgt is not self else out_edge.src

            if tgt is not self:
                tgt.consolidate_relationships()

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


class Graph:

    def __init__(self, timestep=0):
        self.timestep = timestep
        self.vertices = dict()
        self.edges = dict()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def consolidate_relationships(self):

        for vertex in self.vertices.values():
            vertex.consolidate_relationships()

    def load_vert(self, id, attr_map):
        self.vertices[id] = Vertex(id, self.timestep, self.timestep, attr_map=attr_map)
        self.visgraph.add_node(id)

    def load_edge(self, edge_glob):
        idtup = (edge_glob["src"], edge_glob["tgt"])

        if not edge_glob["directed"]:
            sorted(idtup)

        tup = (self.vertices[idtup[0]], self.vertices[idtup[1]])

        edge = Edge(
            set([edge_glob["edge_type"]]),
            tup[0],
            tup[1],
            self.timestep,
            self.timestep,
            twoway=not edge_glob["directed"]
        )

        self.edges[edge.id] = edge
        self.visgraph.add_edge(*idtup)

    def load_json(self, json_path):
        with open(json_path) as f:
            glob = json.load(f)

        for vert, attr_map in glob["all_verts"].items():
            self.load_vert(vert, attr_map)

        for edge in glob["all_edges"]:
            self.load_edge(edge)

    # TODO: do this
    # def delete edge/vertex

    def convert_graph_event_to_delta(self, event: GraphEvent):

        delta_subgraph = dict(all_verts=dict(), all_edges=[])

        for vert_id, attr_map in event.subgraph["all_verts"].items():

            if self.vertices.get(vert_id) is None:
                delta_subgraph["all_verts"][vert_id] = Vertex(
                    vert_id, self.timestep, self.timestep, attr_map=attr_map
                )
            else:
                delta_subgraph["all_verts"][vert_id] = self.vertices.get(vert_id)

        for edge in event.subgraph["all_edges"]:

            edge_id = edge["src"] + "~" + edge["edge_type"] + "~" + edge["tgt"]

            if self.edges.get(edge_id) is None:
                idtup = (edge["src"], edge["tgt"])

                if not edge["directed"]:
                    sorted(idtup)

                vert_0 = self.vertices.get(idtup[0], delta_subgraph["all_verts"].get(idtup[0]))
                vert_1 = self.vertices.get(idtup[1], delta_subgraph["all_verts"].get(idtup[1]))
                tup = (vert_0, vert_1)

                delta_subgraph["all_edges"].append(
                    Edge(
                        edge["edge_type"],
                        tup[0],
                        tup[1],
                        self.timestep,
                        self.timestep,
                        twoway=not edge["directed"]
                    )
                )
            else:
                delta_subgraph["all_edges"].append(
                    self.edges[edge_id]
                )

        return GraphDelta(
            event.key,
            delta_subgraph
        )


    def convert_graph_delta_to_event(self, delta: GraphDelta):

        event_subgraph = dict(all_verts=dict(), all_edges=[])

        for vertex in delta.subgraph["all_verts"]:
            event_subgraph["all_verts"][vertex.id] = { }

        for edge in delta.subgraph["all_edges"]:
            event_subgraph["all_edges"].append(
                {
                    "directed": edge.twoway is False,
                    "edge_type": edge.edge_type,
                    "src": edge.src.id,
                    "tgt": edge.tgt.id
                }
            )

        return GraphEvent(
            delta.key,
            event_subgraph
        )

    def handle_graph_event(self, event: GraphEvent):

        delta = self.convert_graph_event_to_delta(event)
        self.handle_graph_delta(delta)

    def handle_graph_delta(self, delta: GraphDelta):

        for vertex in delta.subgraph["all_verts"].values():

            if delta.key is EventType.Add and vertex.id not in self.vertices:

                # ensure vertex is in graph
                self.vertices[vertex.id] = vertex

            elif delta.key is EventType.Delete and vertex.id in self.vertices:

                # remove vertex from graph
                del self.vertices[vertex.id]

                # find set of neighbors (we can't modify edge sets while iterating over them)
                neighbors = set()

                for in_edge in vertex.in_edges.edge_set:
                    tgt = out_edge.tgt if out_edge.tgt is not vertex else out_edge.src
                    neighbors.add(tgt)

                for out_edge in vertex.out_edges.edge_set:
                    src = in_edge.src if in_edge.src is not vertex else in_edge.tgt
                    neighbors.add(src)

                # remove edges to deleted vertex
                for neighbor in neighbors:
                    neighbor.remove_edges_with(vertex)

        for edge in delta.subgraph["all_edges"]:

            if delta.key is EventType.Add and edge.id not in self.edges:

                # ensure edge is in graph
                self.edges[edge.id] = edge

                # look at src and tgt
                # make sure they're bookkeeping
                edge.src.add_edge(edge, edge.tgt, target=False, twoway=edge.twoway)
                edge.tgt.add_edge(edge, edge.src, target=True, twoway=edge.twoway)

            elif delta.key is EventType.Delete and edge.id in self.edges:

                # remove edge from graph
                del self.edges[edge.id]

                edge.src.remove_edge(edge)
                edge.tgt.remove_edge(edge)

        self.consolidate_relationships()

    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
