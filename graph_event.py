import itertools
from collections import defaultdict
from enum import Enum
from pprint import pprint

from graph_objs import Edge, Vertex, GraphObject


class EventType(Enum):
    Add = 0
    Delete = 1
    Duplicate = 2


class EventTarget(Enum):
    Vertex = 0
    Edge = 1
    Attribute = 2


class GraphMessage:
    def __init__(self, update_map: defaultdict = None):
        self.update_map = update_map if update_map is not None else defaultdict(
            set)

    def merge(self, message):
        new_update_map = self.update_map.copy()
        for key, val in message.update_map.items():
            new_update_map[key] = new_update_map[key] | val
        return GraphMessage(update_map=new_update_map)

    def strip_multitype_edges(self):
        if self.update_map.get((EventType.Add, EventTarget.Edge)) is not None:
            self.update_map[
                (EventType.Add, EventTarget.Edge)
            ] = {edge for edge in self.update_map.get((EventType.Add, EventTarget.Edge)) if len(edge[1]) == 1}

        if self.update_map.get((EventType.Delete, EventTarget.Edge)) is not None:
            self.update_map[
                (EventType.Delete, EventTarget.Edge)
            ] = {edge for edge in self.update_map.get((EventType.Delete, EventTarget.Edge)) if len(edge[1]) == 1}

    # TODO(Wyatt): add attribute updates
    def realize(self, graph):
        realized = defaultdict(set)
        duplicate_records = set()
        realized_verts = dict()
        for iter_key in itertools.product(
                (EventTarget.Vertex, EventTarget.Edge), (EventType.Add, EventType.Delete)):
            event_target, event_act = iter_key
            event_key = (event_act, event_target)
            event_set = self.update_map.get(event_key)
            if event_set is None:
                continue
            if event_target == EventTarget.Vertex:
                for vert_id in event_set:
                    if graph.vertices.get(vert_id) is None:
                        realized_vert = Vertex(
                            vert_id, graph.clock.timestep, graph.clock.timestep
                        )
                        realized_verts[vert_id] = realized_vert
                        realized[event_key].add(realized_vert)
                    else:
                        vert = graph.vertices.get(vert_id)
                        if event_act is EventType.Add:
                            for label in vert.get_relationships("Is>"):
                                duplicate_records.add(GraphRecord_Vertex(
                                    EventType.Duplicate, graph.vertices.get(vert_id), label.id))
                        else:
                            realized[event_key].add(vert)
            elif event_target == EventTarget.Edge:
                for edge_tuple in event_set:
                    s_id, t_set, t_id = edge_tuple
                    t_set = set(t_set)
                    verts = [None, None]
                    for i, vert_id in enumerate((s_id, t_id)):
                        verts[i] = graph.vertices.get(
                            vert_id,
                            realized_verts.get(vert_id)
                        )
                        """
                        if verts[i] is None:
                            raise BufferError() # because I can
                        """
                    s_vert, t_vert = verts
                    if s_vert is None or t_vert is None:
                        continue
                    dupe_edge = False
                    for edge in s_vert.out_edges.id_to_edge.get(t_id, set()):
                        if edge.edge_type == t_set:
                            if event_act == EventType.Delete:
                                realized[event_key].add(edge)
                            else:
                                for src_label, e_type, tgt_label in itertools.product(
                                        s_vert.get_relationships("Is>"), t_set, t_vert.get_relationships("Is>")):
                                    duplicate_records.add(GraphRecord_Edge(
                                        EventType.Duplicate, edge, src_label.id, e_type, tgt_label.id))
                            dupe_edge = True
                            break
                    if dupe_edge is False and event_act == EventType.Add:
                        realized[event_key].add(
                            Edge(t_set, s_vert, t_vert, graph.clock.timestep, graph.clock.timestep))
        return realized, duplicate_records


class GraphRecord:
    def __init__(self, act, tgt, o_ref):
        self.act = act
        self.tgt = tgt
        self.o_ref = o_ref
        self.key = None


class GraphRecord_Vertex(GraphRecord):
    def __init__(self, act, o_ref, label):
        super().__init__(act, EventTarget.Vertex, o_ref)
        self.label = label
        self.key = (self.act, EventTarget.Vertex, self.label)


class GraphRecord_Edge(GraphRecord):
    def __init__(self, act, o_ref, src_label, e_type, tgt_label):
        super().__init__(act, EventTarget.Edge, o_ref)
        self.src_label = src_label
        self.e_type = e_type
        self.tgt_label = tgt_label
        self.key = (self.act, EventTarget.Edge, self.src_label,
                    self.e_type, self.tgt_label)


class GraphRecord_Attribute(GraphRecord):
    def __init__(self, act, o_ref, attr_name, *o_type):
        super().__init__(act, EventTarget.Attribute, o_ref)
        self.attr_name = attr_name
        self.o_type = tuple(o_type)
        self.key = (self.act, EventTarget.Attribute,
                    self.attr_name, *self.o_type)


class UpdateRecord:
    def __init__(self):
        self.add_records = dict()
        self.del_records = dict()

    def add_edge(self, edge, add):
        if add == True:
            self.add_records[edge] = list()
        else:
            self.del_records[edge] = list()

    def check_rules(self, rules):
        # TODO: apply rule-checking and generate a graph message
        # iterate over add_records, it's always going to be an edge,
        # visit source vertex first, then check native rules and then added rules
        # then iterate over patterns? or over edge types? what about other vertex types?
        # complex rules? they don't have simple entry points, they just have to be evaluated... but when?
        # rule keys are light-weight entry-points to enter the more intensive pattern check
        pass

    def update_with(self, records):
        pass
