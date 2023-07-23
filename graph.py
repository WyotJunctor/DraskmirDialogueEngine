import json
import networkx as nx
import matplotlib.pyplot as plt
from pprint import pprint

from clock import Clock
from graph_event import GraphMessage, GraphRecord_Vertex, GraphRecord_Edge, EventType, EventTarget, UpdateRecord
from collections import defaultdict, Counter
from utils import to_counter
import itertools


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
            self.id_to_edgetype[endpoint.id].update({edge_type: 1})
            self.edgetype_to_id[edge_type].update({endpoint.id: 1})
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
            (self.edgetype_to_id, "counter_del", endpoint.id, "src"),
                (self.edgetype_to_edge, "set", edge, "src")):
            for edge_type in edge.edge_type:
                if edge_key == "src":
                    src_key = edge_type
                    tgt_key = other_key
                else:
                    tgt_key = edge_type
                    src_key = other_key
                if index_type == "counter":
                    indexer[src_key].update({tgt_key: -1})
                    if indexer[src_key][tgt_key] == 0:
                        # NOTE(Wyatt): NOT GOOD! NOT GOOD AT ALL! BURN IT ALL DOWN!
                        if edge_key == "src":
                            self.edgetype_to_vertex[edge_key].discard(endpoint)
                            if len(self.edgetype_to_vertex[edge_key] == 0):
                                del self.edgetype_to_vertex[edge_key]
                        del indexer[src_key][tgt_key]
                    if len(indexer[src_key]) == 0:
                        del indexer[src_key]
                elif index_type == "set":
                    indexer[src_key].discard(tgt_key)
                    if len(indexer[src_key]) == 0:
                        del indexer[src_key]

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
            subscriber()  # NOTE: when we need templated event-listener we'll add it


class Vertex(GraphObject):

    def __init__(self, id, created_timestep, updated_timestep, attr_map=None, edge_ref=None):
        self.id = id
        self.in_edges = EdgeMap()
        self.out_edges = EdgeMap()
        self.relationship_map = defaultdict(Counter)
        self.relationship_map["Is>"][self] = 1
        self.edge_ref = edge_ref
        super().__init__(created_timestep, updated_timestep, attr_map)

    def get_relationships(self, key, exclude_self=False, as_counter=False, as_ids=False):
        if key in self.relationship_map:
            result = set(self.relationship_map[key].keys())
            if exclude_self:
                result.remove(self)
            if as_counter == True:
                return to_counter(result)
            if as_ids == True:
                return [r.id for r in result]
            return result
        return set()

    def clear_secondary_relationships(self):
        lineage = self.relationship_map["Is>"]
        self.relationship_map = defaultdict(Counter)
        self.relationship_map["Is>"] = lineage

    def __repr__(self):
        return f"|{self.id}|"  # {id(self)}" # f"{self.id}, {self.attr_map}"

    def update_relationships(self, edge_type, target_counter: Counter, add: bool):
        result_set = set()
        for key, value in target_counter.items():
            if add == True:
                if key not in self.relationship_map[edge_type]:
                    result_set.add(key)
                self.relationship_map[edge_type][key] += value
            elif key in self.relationship_map.get(edge_type, Counter()):
                self.relationship_map[edge_type][key] -= value
                if self.relationship_map[edge_type][key] <= 0:
                    del self.relationship_map[edge_type][key]
                    if len(self.relationship_map[edge_type]) == 0:
                        del self.relationship_map[edge_type]
                    result_set.add(key)

        return result_set

    def propagate_lineage_delta(self, updated_lineage: set, add: bool):
        lineage_counter = to_counter(updated_lineage)
        for edge_map, dir in ((self.in_edges, ">"), (self.out_edges, "<")):
            for edge_type, target_set in edge_map.edgetype_to_vertex.items():
                if edge_type != "Is":
                    for target in target_set:
                        target.update_relationships(
                            edge_type+dir, lineage_counter, add=add)

    def add_edge(self, edge, update_relationships=True):
        dir = "<" if edge.tgt == self else ">"
        endpoint = edge.tgt if edge.tgt is not self else edge.src
        result = set()

        if self is edge.src:
            self.out_edges.add(edge, endpoint)
        elif self is edge.tgt:
            self.in_edges.add(edge, endpoint)

        for edge_type in edge.edge_type:
            if update_relationships == True:
                result = self.update_relationships(
                    edge_type+dir, endpoint.get_relationships("Is>", as_counter=True), add=True)

        return result

    def remove_edge(self, edge, update_relationships=True):
        dir = "<" if edge.tgt == self else ">"
        endpoint = edge.tgt if edge.tgt is not self else edge.src
        result = set()

        if self is edge.src:
            self.out_edges.remove(edge, endpoint)
        elif self is edge.tgt:
            self.in_edges.remove(edge, endpoint)

        for edge_type in edge.edge_type:
            if update_relationships == True:
                result = self.update_relationships(
                    edge_type+dir, endpoint.get_relationships("Is>", as_counter=True), add=False)

        return result

    def remove_edges_with(self, vertex):
        self.in_edges.remove_edges_with(vertex)
        self.out_edges.remove_edges_with(vertex)


class Edge(GraphObject):

    def __init__(self, edge_type: set, src: Vertex, tgt: Vertex, created_timestep, updated_timestep, attr_map=None, ref_vert=None):
        self.edge_type = edge_type
        self.src = src
        self.tgt = tgt
        self.ref_vert = ref_vert
        super().__init__(created_timestep, updated_timestep, attr_map)

    def __repr__(self):
        return f"({self.src.id})-({self.tgt.id})"


class Graph:

    def __init__(self, clock: Clock):
        self.clock = clock
        self.vertices = dict()
        self.visgraph = nx.Graph()
        self.shortcut_map = dict()

    def draw_graph(self):
        nx.draw(self.visgraph, with_labels=True)
        plt.savefig("reality.png")

    def update_rules(self, vertex, updated_lineage, rules, add):
        for vert_id in updated_lineage:
            # iterate through each rule key -> this maps to a rule_id : rule_obj maps
            for rule_key, rule_map in rules[vert_id].items():
                if add == True:
                    rules[vertex.id].get(rule_key, {}).update(rule_map)
                else:
                    for rule_id, _ in rules[vert_id]:
                        rules[vertex.id].get(rule_key, {}).pop(rule_id)

    def split_edge_set(self, edge_set):
        primary_edge_set = {
            edge for edge in edge_set if "Is" in edge.edge_type}
        return primary_edge_set, {edge for edge in edge_set if len(edge.edge_type) > 1 or "Is" not in edge.edge_type}

    def calculate_dependencies(self, queue, original_set, visited):
        while len(queue) > 0:
            root = queue.pop(0)
            for child in root.get_relationships("Is<"):
                original_set.discard(child)
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
            lineage_map[root] = root.update_relationships(
                "Is>", update_map[root], add=add)
            update_counter = to_counter(lineage_map[root])
            for child in root.get_relationships("Is<"):
                if child in visited:  # this should always be true
                    update_map[child] += update_counter
                    visited[child][1] += 1
                    if visited[child][1] == visited[child][0]:
                        queue.append(child)

    def get_verts_from_ids(self, id_set):
        if isinstance(id_set, set):
            return {self.vertices[v_id] for v_id in id_set}
        else:
            return {self.vertices[id_set]}

    def update_graph(self, events: GraphMessage, vertex_rules):

        add_verts = set()
        add_edges = set()
        del_verts = set()
        del_edges = set()

        realized_events, duplicate_records = events.realize(self)

        for event_key, event_set in realized_events.items():
            match event_key:
                case (EventType.Add, EventTarget.Vertex):
                    add_verts = event_set
                case (EventType.Add, EventTarget.Edge):
                    add_edges = event_set
                case (EventType.Delete, EventTarget.Vertex):
                    del_verts = event_set
                case (EventType.Delete, EventTarget.Edge):
                    del_edges = event_set

        add_edges = set(
            [e for e in add_edges if e.src not in del_verts and e.tgt not in del_verts])
        add_p_edges, add_s_edges = self.split_edge_set(add_edges)
        del_p_edges, del_s_edges = self.split_edge_set(del_edges)

        lineage_add_map = defaultdict(set)
        lineage_del_map = defaultdict(set)

        records = UpdateRecord()

        update_map = defaultdict(Counter)
        original_set = set()
        visited = dict()
        queue = list()
        # HANDLE DELETED VERTICES
        for v in del_verts:
            if v.id in self.vertices:
                del self.vertices[v.id]
            # TODO: check if this is correct
            if v.edge_ref is not None:
                if "Is" in v.get_relationships("Is>"):
                    del_p_edges.add(v.edge_ref)
                else:
                    del_s_edges.add(v.edge_ref)
            lineage_del_map[v] = v.get_relationships("Is>")
            for edge_map in (v.out_edges, v.in_edges):
                for edge_type, edge_set in edge_map.edgetype_to_edge.items():
                    if edge_type == "Is":
                        del_p_edges |= edge_set
                    else:
                        del_s_edges |= edge_set

        # BEGIN DELETED PRIMARY EDGES
        for e in del_p_edges:
            if e.src not in del_verts:
                original_set.add(e.src)
                visited[e.src] = [0, 0]
                queue.append(e.src)
                update_map[e.src] += e.tgt.get_relationships(
                    "Is>", as_counter=True)
            if e.src in del_verts and e.tgt in del_verts:
                continue
            records.add_edge(e, False)
            for v in (e.src, e.tgt):
                if v not in del_verts:
                    # this is basically a secondary edge
                    v.remove_edge(e, update_relationships=v == e.tgt)

        self.calculate_dependencies(queue, original_set, visited)

        self.apply_primary_edges(
            original_set, visited, update_map, lineage_del_map, add=False)
        # END DELETED PRIMARY EDGES

        # HANDLE DELETED SECONDARY EDGES
        for e in del_s_edges:
            records.add_edge(e, False)
            for v in (e.src, e.tgt):
                if v not in del_verts:
                    v.remove_edge(e)

        # HANDLE ADDED VERTS (POSSIBLE MERGING)
        for v in add_verts:
            self.vertices[v.id] = v
        # if the v.id already exists and doesn't equal v, we have to figure out merging...

        # BEGIN ADDED PRIMARY EDGES
        update_map = defaultdict(Counter)
        visited = dict()
        original_set = set()
        queue = list()
        for e in add_p_edges:
            records.add_edge(e, True)
            visited[e.src] = [0, 0]
            original_set.add(e.src)
            queue.append(e.src)
            update_map[e.src] += e.tgt.get_relationships(
                "Is>", as_counter=True)
            e.src.add_edge(e, update_relationships=False)
            e.tgt.add_edge(e, update_relationships=True)

        self.calculate_dependencies(queue, original_set, visited)

        self.apply_primary_edges(
            original_set, visited, update_map, lineage_add_map, add=True)
        # END ADDED PRIMARY EDGES

        # PROPAGATE LINEAGE TO NEIGHBORS
        for lineage_map, add in ((lineage_del_map, False), (lineage_add_map, True)):
            for v, updated_lineage in lineage_map.items():
                for _, rules in vertex_rules.items():
                    self.update_rules(v, updated_lineage, rules, add)
                v.propagate_lineage_delta(updated_lineage, add=add)
                # this is about propagating changes to neighbors via remaining secondary edges

        # HANDLE ADDED SECONDARY EDGES
        for e in add_s_edges:
            records.add_edge(e, True)
            e.src.add_edge(e, update_relationships=True)
            e.tgt.add_edge(e, update_relationships=True)

        for v in del_verts:
            for _, rules in vertex_rules.items():
                del rules[v.id]

        return records

    def load_vert(self, vert):
        label = vert["label"]
        attr_map = vert.get("attr_map", dict())

        vertex = Vertex(label, self.clock.timestep,
                        self.clock.timestep, attr_map=attr_map)
        self.vertices[label] = vertex
        self.visgraph.add_node(label)
        return vertex

    def load_edge(self, edge_glob):
        src_id = edge_glob["src"]
        tgt_id = edge_glob["tgt"]
        src = self.vertices[src_id]
        tgt = self.vertices[tgt_id]

        edge_types = set([edge_glob["types"]] if isinstance(
            edge_glob["types"], str) else edge_glob["types"])
        attr_map = edge_glob.get("attr_map", dict())

        edge = Edge(
            edge_types,
            src,
            tgt,
            self.clock.timestep,
            self.clock.timestep,
            attr_map=attr_map
        )

        self.visgraph.add_edge(src_id, tgt_id)
        return edge

    def load_json_file(self, json_path):
        with open(json_path) as f:
            glob = json.load(f)
            self.load_json(glob)

    def load_json(self, glob):

        for vert in glob["vertices"]:
            self.load_vert(vert)

        for edge in glob["edges"]:
            self.load_edge(edge)

    def load_rules(self, rule_map):
        for v_id, rule_class in rule_map.items():
            rule_class(self.vertices[v_id])
