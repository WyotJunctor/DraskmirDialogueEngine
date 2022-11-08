import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, Counter

from graph_event import GraphDelta, GraphEvent


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
        self.id_to_edgetype[endpoint.id].update({edge.edge_type:1})
        self.id_to_edge[endpoint.id].add(edge)
        self.edgetype_to_id[edge.edge_type].update({endpoint.id:1})
        self.edgetype_to_edge[edge.edge_type].add(edge)
        self.edgetype_to_vertex[edge.edge_type].add(endpoint)

class GraphObject:

    def __init__(self, created_timestep=None, updated_timestep=None, attr_map=None):
        self.created_timestep = created_timestep
        self.updated_timestep = updated_timestep
        self.attr_map = dict() if attr_map is None else attr_map


class Vertex(GraphObject):

    def __init__(self, id, created_timestep, updated_timestep, attr_map=None):
        self.id = id
        self.in_edges = EdgeMap()
        self.out_edges = EdgeMap()
        self.relationship_map = defaultdict(set)
        super().__init__(created_timestep, updated_timestep, attr_map)

    def __repr__(self):
        return f"{self.id}, {self.attr_map}"

    def consolidate_relationships(self):

        for out_edge in self.out_edges.edge_set:
            tgt = out_edge.tgt if out_edge.tgt is not self else out_edge.src

            tgt.consolidate_relationships()

            self.relationship_map[out_edge.edge_type] |= tgt.relationship_map["is"]

    def add_edge(self, edge, endpoint, target=False, twoway=False):
        if twoway or not target:
            self.out_edges.add(edge, endpoint)
        if twoway or target:
            self.in_edges.add(edge, endpoint)

class Edge(GraphObject):

    def __init__(self, edge_type:str, src:Vertex, tgt:Vertex, created_timestep, updated_timestep, attr_map=None, twoway=False):
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

    def calculate_parents(self): # TODO: finish this 
        pass

    def load_vert(self, id, attr_map):
        self.vertices[id] = Vertex(id, self.timestep, self.timestep, attr_map=attr_map)
        self.visgraph.add_node(id)

    def load_edge(self, edge_glob):
        idtup = (edge_glob["src"], edge_glob["tgt"])

        if not edge_glob["directed"]:
            sorted(idtup)

        tup = (self.vertices[idtup[0]], self.vertices[idtup[1]])

        edge = Edge(
            edge_glob["edge_type"],
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

        for vert_id, attr_map in event.subgraph["all_verts"]:

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

                tup = (self.vertices[idtup[0]], self.vertices[idtup[1]])

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

    def handle_graph_delta(self, delta: GraphDelta): # TODO: actually code this

        for vertex in delta.subgraph["all_verts"]:

            ...

        for edge in delta.subgraph["all_edges"]:
            ...

        # if event actually updates the graph...
        # recalculate parents?
        pass



    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
