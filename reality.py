from brain import Brain
from graph import Graph, Vertex, Edge
from graph_event import GraphEvent, EventType

class Reality:

    def __init__(self, graph: Graph, effect_rules: dict):
        self.graph = graph
        self.effect_rules = effect_rules

    def receive_action(self, timestep: int, acting_entity: Brain, action_vertex: Vertex, action_target: Vertex):

        action_isses = action_vertex.relationship_map["is"]

        rules = set()

        for action_is in action_isses:
            # collect the rules associated with the action's conceptual parent vertices
            rules |= self.effect_rules.get(action_is, set())

        graph_events = {
            GraphEvent(EventType.Add, dict(
                all_verts=[ action_vertex ],
                all_edges=[Edge(
                    edge_type="target", src=acting_entity, tgt=action_target,
                    created_timestep=timestep, updated_timestep=timestep
                )]
            ))
        }

        for rule in rules:
            # assume mutation in the function
            rule(graph_events)

        return graph_events
