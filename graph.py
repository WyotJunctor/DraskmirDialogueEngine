import json
import networkx as nx
import matplotlib.pyplot as plt


class Rule:

    def __init__(self, rule):
      self.rule = rule


class GraphObject:

    def __init__(self, created_timestep=None, updated_timestep=None, rules=None, attr_map=None):
        self.rules = dict() if rules is None else rules
        self.created_timestep = created_timestep
        self.updated_timestep = updated_timestep
        self.attr_map = dict() if attr_map is None else attr_map


class Vertex(GraphObject):

    def __init__(self, id, created_timestep, updated_timestep, rules=None, attr_map=None):
        self.id = id
        self.in_edges = set()
        self.out_edges = set()
        super().__init__(rules, created_timestep, updated_timestep, attr_map)


class Edge(GraphObject):

    def __init__(self, edge_type:str, src:Vertex, tgt:Vertex, created_timestep, updated_timestep, rules=None, attr_map=None, twoway=False):
        self.edge_type = edge_type
        self.src = src
        self.tgt = tgt
        src.out_edges.add(self)
        tgt.in_edges.add(self)
        if twoway == True:
            src.in_edges.add(self)
            tgt.out_edges.add(self)
        super().__init__(rules, created_timestep, updated_timestep, attr_map)
        # TODO: add logic for twoway

class Graph:

    def __init__(self, game):
        self.game = game
        self.vertices = dict()
        self.edges = set()
        self.visgraph = nx.Graph()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def load_vert(self, vert_glob):
        id = vert_glob["vertex_id"]
        self.vertices[id] = Vertex(id, self.game.timestep, self.game.timestep)
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
                self.game.timestep,
                self.game.timestep,
                twoway=not edge_glob["directed"]
            )
        )
        self.visgraph.add_edge(*idtup)

    def load_json(self, json_path):
        with open(json_path) as f:
            glob = json.load(f)

        for vert in glob["all_verts"]:
            self.load_vert(vert)

        for edge in glob["all_edges"]:
            self.load_edge(edge)
