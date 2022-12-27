from collections import defaultdict
from enum import Enum
import itertools

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
    def __init__(self, update_map:defaultdict):
        self.update_map = update_map

    def merge(self, message):
        for key, val in message.items():
            self.update_map[key] |= val
        return self

    def strip_multitype_edges(self):
        if self.update_map.get((EventType.Add, EventTarget.Edge)) is not None:
            self.update_map[
                (EventType.Add, EventTarget.Edge)
                ] = { edge for edge in self.update_map.get((EventType.Add, EventTarget.Edge)) if len(edge[1]) == 1 }
        
        if self.update_map.get((EventType.Delete, EventTarget.Edge)) is not None:
            self.update_map[
                (EventType.Delete, EventTarget.Edge)
                ] = { edge for edge in self.update_map.get((EventType.Delete, EventTarget.Edge)) if len(edge[1]) == 1 }        

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
            if event_target == EventTarget.Vertex:
                for vert_id in event_set:
                    if graph.vertices.get(vert_id) is None:
                        realized[event_key].add(Vertex(
                            vert_id, graph.clock.timestep, graph.clock.timestep
                        ))
                    else:
                        vert = graph.vertices.get(vert_id)
                        if event_act is EventType.Add:
                            for label in vert.get_relationships("Is>"):
                                duplicate_records.add(GraphRecord_Vertex(EventType.Duplicate, graph.vertices.get(vert_id), label))
                        else:
                            realized[event_key].add(vert)
            elif event_target == EventTarget.Edge:
                for edge_tuple in event_set:
                    s_id, t_set, t_id = edge_tuple
                    verts = [None, None]
                    for i, vert_id in enumerate((s_id, t_id)):
                        verts[i] = graph.vertices.get(
                            vert_id,
                            realized_verts.get(vert_id)    
                        )
                        if verts[i] is None:
                            raise BufferError() # because I can

                    s_vert, t_vert = verts
                    dupe_edge = False
                    for edge in s_vert.out_edges.id_to_edge.get(t_id, set()):
                        if edge.edge_type == t_set:
                            for src_label, e_type, tgt_label in itertools.product(
                                s_vert.get_relationships("Is>"), t_set, t_vert.get_relationships("Is>")):
                                duplicate_records.add(GraphRecord_Edge(EventType.Duplicate, edge, src_label, e_type, tgt_label)) 
                            dupe_edge = True
                            break
                    if dupe_edge is False:
                        realized[event_key].add(Edge(t_set, s_vert, t_vert, graph.clock.timestep))
        return realized, duplicate_records
            


class GraphRecord:
    def __init__(self, act, tgt, o_ref):
        self.act = act
        self.tgt = tgt
        self.o_ref = o_ref

    def __hash__(self):
        raise NotImplementedError()


class GraphRecord_Vertex(GraphRecord):
    def __init__(self, act, o_ref, label):
        super().__init__(act, EventTarget.Vertex, o_ref)
        self.label = label

    def __hash__(self):
        return hash((self.act, EventTarget.Vertex, self.label))

class GraphRecord_Edge(GraphRecord):
    def __init__(self, act, o_ref, src_label, e_type, tgt_label):
        super().__init__(act, EventTarget.Edge, o_ref)
        self.src_label = src_label
        self.e_type = e_type
        self.tgt_label = tgt_label
        
    def __hash__(self):
        return hash((self.act, EventTarget.Edge, self.src_label, self.e_type, self.tgt_label))


class GraphRecord_Attribute(GraphRecord):
    def __init__(self, act, o_ref, attr_name, *o_type):
        super().__init__(act, EventTarget.Attribute, o_ref)
        self.attr_name = attr_name
        self.o_type = tuple(o_type)

    def __hash__(self):
        return hash((self.act, EventTarget.Attribute, self.attr_name, *self.o_type))


class GraphEvent:
    def __init__(self, event_type: EventType, subgraph: dict):
        self.event_type = event_type
        self.subgraph = subgraph

    def get_objs_subgraph(self, graph):

        objs_subgraph = dict(all_verts=dict(), all_edges=[])

        for vert_id, attr_map in self.subgraph["all_verts"].items():

            if graph.vertices.get(vert_id) is None:
                objs_subgraph["all_verts"][vert_id] = Vertex(
                    vert_id, graph.clock.timestep, graph.clock.timestep, attr_map=attr_map
                )
            else:
                objs_subgraph["all_verts"][vert_id] = graph.vertices.get(vert_id)

        for edge in self.subgraph["all_edges"]:

            edge_id = edge["src"] + "~" + edge["edge_type"] + "~" + edge["tgt"]

            if graph.edges.get(edge_id) is None:
                idtup = (edge["src"], edge["tgt"])

                if not edge["directed"]:
                    sorted(idtup)

                vert_0 = graph.vertices.get(idtup[0], objs_subgraph["all_verts"].get(idtup[0]))
                vert_1 = graph.vertices.get(idtup[1], objs_subgraph["all_verts"].get(idtup[1]))
                tup = (vert_0, vert_1)

                objs_subgraph["all_edges"].append(
                    Edge(
                        edge["edge_type"],
                        tup[0],
                        tup[1],
                        graph.clock.timestep,
                        graph.clock.timestep,
                        twoway=not edge["directed"]
                    )
                )
            else:
                objs_subgraph["all_edges"].append(
                    graph.edges[edge_id]
                )

        return objs_subgraph
