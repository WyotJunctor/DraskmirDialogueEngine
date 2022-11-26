import json
import networkx as nx
import matplotlib.pyplot as plt

from clock import Clock
from graph_event import GraphEvent, GraphDelta, EventType, EventTarget
from graph_objs import Edge, Vertex
from collections import defaultdict


class Graph:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.vertices = dict()
        self.edges = dict()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def consolidate_relationships(self, updated_verts=None, tree_recalculate=False):
        updated_verts = set(self.vertices.values()) if updated_verts is None else updated_verts
  
        starting_set = updated_verts
        if tree_recalculate == True:
            for v in updated_verts:
                for n in v.out_edges.edgetype_to_vertex["Is"]:
                    starting_set |= n.relationship_map["Is>"]

        # get list of verts which have ingoing Is, but no outgoing Is
        queue = list()
        dependency_map = defaultdict(int)

        for v in starting_set:
            if len(v.in_edges.edgetype_to_edge["Is"]) > 0 and len(v.out_edges.edgetype_to_edge["Is"]) == 0:
                queue.append(v)
                dependency_map[v] = 0

        while len(queue) > 0:
            root = queue.pop(0)
            for child in root.in_edges.edgetype_to_vertex["Is"]:
                dependency_map[child] += 1
                if dependency_map[child] == len(child.out_edges.edgetype_to_edge):
                    new_lineage = child.relationship_map["Is>"] | root.relationship_map["Is>"]
                    if child.relationship_map["Is>"] != new_lineage:
                        updated_verts.add(child)
                    child.relationship_map["Is>"] = new_lineage
                    queue.add(child)

        secondary_verts = set()


        while len(queue) > 0:
            vert = queue.pop(0)
            vert.clear_secondary_relationships()
            for dir, edge_map in ((">", vert.out_edges.edgetype_to_vertex), ("<", vert.in_edges.edgetype_to_vertex)):
                for edge_type, neighbor_set in edge_map.items():
                    if edge_type == "Is" and dir == ">":
                        continue
                    for neighbor in neighbor_set:
                        if vert not in secondary_verts and neighbor not in updated_verts:
                            updated_verts.add(neighbor)
                            secondary_verts.add(neighbor)
                        vert.relationship_map[edge_type+dir] |= neighbor.relationship_map["Is>"]
                        

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
