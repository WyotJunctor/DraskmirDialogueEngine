import inspect
import sys

from collections import defaultdict
from graph_event import EventType, EventTarget, GraphRecord, GraphMessage

class EffectRule:

    def __init__(self, reality):
        # add self to vertex action_rules
        self.reality = reality

    def receive_record(self, record: GraphRecord):
        pass

class er_PersonSpawn(EffectRule):
    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Person"),
    )

    def receive_record(self, _, record: GraphRecord):

        """
        look at all of the other people in the room,
        give them unknown relationships to the new person
        give the new person an unknown relationship to them

        give the new person a bystander involvement in the calm context
        # check for ingoing involvement edges to Combat
        # if there are any, add a bystander involvement to Combat
        """

        generated_message = GraphMessage()

        added_person = record.o_ref

        # find all the other people
        unknown_rels = self.reality.graph.vertices["Unknown_Relationship"].get_relationships("Is>")
        person_v = self.reality.graph.vertices["Person"]
        for person_instance in person_v.in_edges.edgetype_to_vertex["Is"]:
            if person_instance is added_person:
                continue

            generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((person_instance.id, unknown_rels.copy(), added_person.id))
            generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((added_person.id, unknown_rels.copy(), person_instance.id))

        calm_v = self.reality.graph.vertices["Calm_Context"]
        byst_rels = self.reality.graph.vertices["Bystander"].get_relationships("Is>")
        generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((added_person.id, byst_rels, calm_v.id))

        return generated_message


class er_RelationshipMod(EffectRule):
    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Relationship", "Person"),
    )
    rel_prios = dict(
        Hostile=float("inf"),
        Friendly=1000.0,
        Known=0.0,
        Unknown=float("-inf")
    )

    def receive_record(self, _, record: GraphRecord):

        """
        look at the existing Relationship edge between these two
        if the existing Relationship has priority delete the new one,
            otherwise delete the existing one
        """

        new_edge = record.o_ref
        new_tgt = record.o_ref.tgt
        existing_rels = [
            ex_edge for ex_edge in new_edge.src.out_edges.edgetype_to_edge["Relationship"] if ex_edge is not new_edge and ex_edge.tgt is new_tgt 
        ]

        assert(len(existing_rels) <= 1)

        if len(existing_rels) == 0:
            return None

        existing_rel = existing_rels[0]

        new_rel_prio = er_RelationshipMod.rel_prios[new_edge.ref_vert.id]
        ex_rel_prio = er_RelationshipMod.rel_prios[existing_rel.ref_vert.id]

        if new_rel_prio >= ex_rel_prio:
            return GraphMessage(
                update_map=defaultdict(set,
                {
                    (EventType.Delete, EventTarget.Edge): set([
                        (existing_rel.src.id, existing_rel.edge_type, existing_rel.tgt.id)
                    ])
                })
            )
        else:
            return GraphMessage(
                update_map=defaultdict(set,
                {
                    (EventType.Delete, EventTarget.Edge): set([
                        (new_edge.src.id, new_edge.edge_type, new_edge.tgt.id)
                    ])
                })
            )

rules_map = dict()
 
classes = [cls_obj for _, cls_obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(cls_obj) and hasattr(cls_obj, "record_keys")]
for class_obj in classes:
    for key in class_obj.record_keys:
        rules_map[key] = class_obj
