import json
import networkx as nx
import matplotlib.pyplot as plt

from clock import Clock
from graph_event import GraphEvent, GraphDelta, EventType, EventTarget
from graph_objs import Edge, Vertex


class Graph:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.vertices = dict()
        self.edges = dict()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def consolidate_relationships(self, moded_verts):

        for vertex in self.vertices.values():
            vertex.consolidate_relationships()

    def load_vert(self, id, attr_map):
        self.vertices[id] = Vertex(id, self.clock.timestep, self.clock.timestep, attr_map=attr_map)
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
            self.clock.timestep,
            self.clock.timestep,
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

    def handle_graph_event(self, event: GraphEvent):

        moded_objs = { "verts": set(), "edges": set() }
        obj_subgraph = event.get_objs_subgraph(self)

        for vertex in obj_subgraph["all_verts"].values():

            if event.key is EventType.Add and vertex.id not in self.vertices:

                # ensure vertex is in graph
                self.vertices[vertex.id] = vertex
                moded_objs["verts"].add(vertex)

            elif event.key is EventType.Delete and vertex.id in self.vertices:

                # remove vertex from graph
                del self.vertices[vertex.id]
                moded_objs["verts"].add(vertex)

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

        for edge in obj_subgraph["all_edges"]:

            if event.key is EventType.Add and edge.id not in self.edges:

                # ensure edge is in graph
                self.edges[edge.id] = edge
                moded_objs["edges"].add(edge)

                # look at src and tgt
                # make sure they're bookkeeping
                edge.src.add_edge(edge, edge.tgt, target=False, twoway=edge.twoway)
                edge.tgt.add_edge(edge, edge.src, target=True, twoway=edge.twoway)

            elif event.key is EventType.Delete and edge.id in self.edges:

                # remove edge from graph
                del self.edges[edge.id]
                moded_objs["edges"].add(edge)

                edge.src.remove_edge(edge)
                edge.tgt.remove_edge(edge)

        self.consolidate_relationships(moded_objs["verts"])

        graph_deltas = list()
        for vert in moded_objs["verts"]:
            graph_deltas.append(GraphDelta(
                event.key,
                EventTarget.Vertex,
                vert.relationship_map["Is>"],
                vert
            ))

        for edge in moded_objs["edges"]:
            graph_deltas.append(GraphDelta(
                event.key,
                EventTarget.Edge,
                edge.edge_type,
                edge
            ))

        return graph_deltas

    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
