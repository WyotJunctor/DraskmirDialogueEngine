from brain import Brain
from clock import Clock
from graph import Graph, Vertex, Edge
from graph_event import GraphEvent, EventType

class Reality:

    def __init__(self, clock: Clock, graph: Graph, effect_rules: dict):
        self.clock = clock
        self.graph = graph
        self.effect_rules = effect_rules

    def receive_action(self, timestep: int, acting_entity: Brain, action_vertex: Vertex, action_target: Vertex):

        actor_id = acting_entity.ego.id
        act_id = actor_id + "_act_" + self.game.timestep
        act_type = action_vertex.id
        act_event = GraphEvent(
            EventType.Add,
            {
                "all_verts": [ act_id ],
                "all_edges": [
                    { "directed": True, "edge_tpye": "inst", "src": act_id, "tgt": act_type },
                    { "directed": True, "edge_tpye": "src", "src": actor_id, "tgt": act_id },
                 ]
            }
        )

        action_isses = action_vertex.relationship_map["is"]

        rules = set()

        for action_is in action_isses:
            # collect the rules associated with the action's conceptual parent vertices
            rules |= self.effect_rules.get(action_is, set())

        graph_deltas = [
            self.graph.convert_graph_event_to_delta(act_event)
        ]

        for rule in rules:
            # assume mutation in the function
            rule(graph_deltas)

        return graph_deltas

    def receive_event(self, event: GraphEvent):
        # TODO(Simon): refactor to convert into Delta and apply
        status = True
        if event.key in self.effect_rules:
            for event_response in self.effect_rules[event.key]:
                if event_response(event) is False:
                    status = False
                    break
        if status is False:
            return
        self.graph.update_json(event)

