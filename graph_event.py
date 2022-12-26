from enum import Enum

from graph_objs import Edge, Vertex, GraphObject


class EventType(Enum):
    Add = 0
    Delete = 1
    Duplicate = 2
    Update = 3


class EventTarget(Enum):
    Vertex = 0
    Edge = 1
    Attribute = 2


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
