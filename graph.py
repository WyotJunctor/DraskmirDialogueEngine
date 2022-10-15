import json
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict, Counter
from rules import ActionRule, InheritedActionRule
from utils import merge_targets


class EdgeMap:
    def __init__(self):
        self.edge_set = set()
        self.id_to_edgetype = defaultdict(Counter)
        self.id_to_edge = defaultdict(set)
        self.edgetype_to_id = defaultdict(Counter)
        self.edgetype_to_edge = defaultdict(set)

    def add(self, edge, endpoint):
        self.edge_set.add(edge)
        self.id_to_edgetype[endpoint.id].update({edge.edge_type:1})
        self.id_to_edge[endpoint.id].add(edge)
        self.edgetype_to_id[edge.edge_type].update({endpoint.id:1})
        self.edgetype_to_edge[edge.edge_type].add(edge)

class GraphObject:

    def __init__(self, created_timestep=None, updated_timestep=None, rules=None, attr_map=None):
        self.rules = dict() if rules is None else rules
        self.created_timestep = created_timestep
        self.updated_timestep = updated_timestep
        self.attr_map = dict() if attr_map is None else attr_map


class Vertex(GraphObject):

    def __init__(self, id, created_timestep, updated_timestep, rules=None, action_rules=None, attr_map=None):
        self.id = id
        self.in_edges = EdgeMap()
        self.out_edges = EdgeMap()
        self.action_rules = list() if action_rules is None else action_rules
        super().__init__(rules, created_timestep, updated_timestep, attr_map)

    def __repr__(self):
        return f"{self.id}, {self.attr_map}"


    def add_edge(self, edge, endpoint, target=False, twoway=False):
        if twoway or not target:
            self.out_edges.add(edge, endpoint)
        if twoway or target:
            self.in_edges.add(edge, endpoint)

    def get_targets(self, graph, target_set):
        local_target_set = {"allow":set(), "disallow":set()}
        for rule in self.action_rules:
            r_target_set, r_local_target_set, allow = rule.get_targets(graph, target_set, local_target_set)
            if allow is False:
                return {}, {}, False
            target_set = merge_targets(target_set, r_target_set)
            r_local_target_set["disallow"] = r_local_target_set["disallow"].union(target_set["disallow"])
            local_target_set = merge_targets(local_target_set, r_local_target_set)
        return target_set, local_target_set, True

class Edge(GraphObject):

    def __init__(self, edge_type:str, src:Vertex, tgt:Vertex, created_timestep, updated_timestep, rules=None, attr_map=None, twoway=False):
        self.edge_type = edge_type
        self.src = src
        self.tgt = tgt
        src.add_edge(self, tgt, twoway=twoway)
        tgt.add_edge(self, src, target=True, twoway=twoway)
        super().__init__(rules, created_timestep, updated_timestep, attr_map)
        # TODO: add logic for twoway

    def __repr__(self):
        return f"({self.src})-({self.tgt})"

class Graph:

    def __init__(self, timestep=0):
        self.timestep = timestep
        self.vertices = dict()
        self.edges = set()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def load_vert(self, id, attr_map):
        self.vertices[id] = Vertex(id, self.timestep, self.timestep, attr_map=attr_map)
        self.visgraph.add_node(id)

    def load_edge(self, edge_glob):
        idtup = (edge_glob["src"], edge_glob["tgt"])

        if not edge_glob["directed"]:
            sorted(idtup)

        tup = (self.vertices[idtup[0]], self.vertices[idtup[1]])

        self.edges.add(
            Edge(
                edge_glob["edge_type"],
                tup[0],
                tup[1],
                self.timestep,
                self.timestep,
                twoway=not edge_glob["directed"]
            )
        )
        self.visgraph.add_edge(*idtup)

    def load_json(self, json_path):
        with open(json_path) as f:
            glob = json.load(f)

        for vert, attr_map in glob["all_verts"].items():
            self.load_vert(vert, attr_map)

        for edge in glob["all_edges"]:
            self.load_edge(edge)

        print(self.edges)

    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
