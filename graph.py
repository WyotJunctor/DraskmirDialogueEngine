import json
import networkx as nx
import matplotlib.pyplot as plt

from clock import Clock
from graph_event import GraphEvent, EventType, EventTarget
from graph_objs import Edge, Vertex
from collections import defaultdict, Counter
from utils import to_counter
import itertools


class Graph:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.vertices = dict()
        self.edges = dict()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def split_edge_set(self, edge_set):
        primary_edge_set = {edge for edge in edge_set if "Is" in edge.edge_type}
        return primary_edge_set, edge_set - primary_edge_set

    def calculate_dependencies(self, queue, original_set, visited):
        while len(queue) > 0:
            root = queue.pop(0)
            for child in root.get_relationships("Is<"):
                original_set.remove(child)
                if child in visited:
                    visited[child][0] += 1
                else:
                    visited[child] = [1, 0]
                    queue.append(child)

    def apply_primary_edges(self, original_set, visited, update_map, lineage_map, add):
        queue = list(original_set)
        while len(queue) > 0:
            root = queue.pop(0)
            # apply update map removal
            lineage_map[root] = root.update_relationships(update_map[root], add=add)
            update_counter = to_counter(lineage_map[root])
            for child in root.get_relationships("Is<"):
                if child in visited: # this should always be true
                    update_map[child] += update_counter
                    visited[child][1] += 1
                    if visited[child][1] == visited[child][0]:
                        queue.append(child)

    def update_graph(self, events: list[GraphEvent]):


        add_verts = set()
        add_edges = set()
        del_verts = set()
        del_edges = set()

        for event in events:
            obj_subgraph = event.get_objs_subgraph(self)

            set_key = (event.event_type, event.event_target)

            match set_key:
                case (EventType.Add):
                    vert_set = add_verts
                    edge_set = add_edges
                case (EventType.Delete):
                    vert_set = del_verts
                    edge_set = del_edges

            vert_set |= set(obj_subgraph["all_verts"].values())
            edge_set |= set(obj_subgraph["all_edges"].values())

        add_edges = set([e for e in add_edges if e.src not in del_verts and e.tgt not in del_verts])
        add_p_edges, add_s_edges = self.split_edge_set(add_edges)
        del_p_edges, del_s_edges = self.split_edge_set(del_edges)

        lineage_add_map = defaultdict(set)
        lineage_del_map = defaultdict(set)
        edge_add_map = dict()
        edge_del_map = dict()

        update_map = defaultdict(Counter)
        original_set = set()
        visited = dict()
        queue = list()
        # HANDLE DELETED VERTICES
        for v in del_verts:
            del self.vertices[v.id]
            lineage_del_map[v] = v.get_relationships("Is>")
            for edge_map in (v.out_edges, v.in_edges):
                for edge_type, edge_set in edge_map.edgetype_to_edge.items():
                    if edge_type == "Is":
                        del_p_edges += edge_set
                    else:
                        del_s_edges += edge_set

        # BEGIN DELETED PRIMARY EDGES
        for e in del_p_edges:
            del self.edges[e.id]
            if e.src not in del_verts:
                original_set.add(e.src)
                visited[e.src] = [0,0]
                queue.append(e.src)
                update_map[e.src] += e.tgt.get_relationships("Is>", as_counter=True)
            if e.src in del_verts and e.tgt in del_verts:
                continue
            for v in (e.src, e.tgt):
                if v not in del_verts:
                    v.remove_edge(e, update_relationships=v == e.tgt) # this is basically a secondary edge

        self.calculate_dependencies(self, queue, original_set, visited)

        self.apply_primary_edges(self, original_set, visited, update_map, lineage_del_map, add=False)
        # END DELETED PRIMARY EDGES

        # HANDLE DELETED SECONDARY EDGES
        for e in del_s_edges:
            del self.edges[e.id]
            for v in (e.src, e.tgt):
                if v not in del_verts:
                    v.remove_edge(e)

        # BEGIN ADDED PRIMARY EDGES
        update_map = defaultdict(Counter)
        visited = dict()
        original_set = set()
        queue = list()
        for e in add_p_edges:
            visited[e.src] = [0, 0]
            original_set.add(e.src)
            queue.append(e.src)
            update_map[e.src] += e.tgt.get_relationships("Is>", as_counter=True)
            e.src.add_edge(e, e.twoway, update_relationships=False)
            e.tgt.add_edge(e, e.twoway, update_relationships=True)

        self.calculate_dependencies(self, queue, original_set, visited)

        self.apply_primary_edges(self, original_set, visited, update_map, lineage_add_map, add=True)
        # END ADDED PRIMARY EDGES

        # PROPAGATE LINEAGE TO NEIGHBORS
        for lineage_map, add in ((lineage_del_map, False), (lineage_add_map,True)):
            for v, updated_lineage in lineage_map:
                v.propagate_lineage_delta(updated_lineage, add=add)
                # this is about propagating changes to neighbors via remaining secondary edges

        # HANDLE ADDED SECONDARY EDGES
        for e in add_s_edges:
            e.src.add_edge(e, e.twoway, update_relationships=True)
            e.tgt.add_edge(e, e.twoway, update_relationships=True)

        # HANDLE ADDED VERTS (POSSIBLE MERGING)
        for v in add_verts:
            self.vertices[v.id] = v
        # if the v.id already exists and doesn't equal v, we have to figure out merging...

        # iterate through secondary edge additions/deletions and generate edge delta maps 
        for edge_set, edge_delta_map in ((add_s_edges, edge_add_map), (del_s_edges, edge_del_map)):
            for edge in edge_set:
                edge_delta_map[edge] = set(itertools.product(edge.src.get_relationships("Is>"), edge.edge_type, edge.tgt.get_relationships("Is>")))


        return lineage_add_map, lineage_del_map, edge_add_map, edge_del_map


    def load_vert(self, id, attr_map):
        vertex = Vertex(id, self.clock.timestep, self.clock.timestep, attr_map=attr_map)
        self.vertices[id] = vertex
        self.visgraph.add_node(id)
        return vertex

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
        return edge

    def load_json(self, json_path):
        with open(json_path) as f:
            glob = json.load(f)

        for vert, attr_map in glob["all_verts"].items():
            self.load_vert(vert, attr_map)

        for edge in glob["all_edges"]:
            self.load_edge(edge)


    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
