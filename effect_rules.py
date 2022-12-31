import inspect
import sys
import random
from pprint import pprint

from collections import defaultdict
from graph_event import EventType, EventTarget, GraphRecord, GraphMessage

class EffectRule:

    def __init__(self, reality):
        # add self to vertex action_rules
        self.reality = reality

    def receive_record(self, record: GraphRecord):
        pass

class er_PersonSpawn(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Person"),
    )

    def receive_record(self, record: GraphRecord):

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
        unknown_rels = tuple(self.reality.graph.vertices["Unknown_Relationship"].get_relationships("Is>", as_ids=True))
        person_v = self.reality.graph.vertices["Person"]
        for person_instance in person_v.in_edges.edgetype_to_vertex["Is"]:
            if person_instance is added_person:
                continue

            generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((person_instance.id, unknown_rels, added_person.id))
            generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((added_person.id, unknown_rels, person_instance.id))

        calm_v = self.reality.graph.vertices["Calm_Context"]
        byst_rels = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>", as_ids=True))
        generated_message.update_map[(EventType.Add, EventTarget.Edge)].add((added_person.id, byst_rels, calm_v.id))

        return generated_message


class er_RelationshipMod(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Relationship", "Person"),
    )
    rel_prios = dict(
        Hostile=float("inf"),
        Friendly=1000.0,
        Known=0.0,
        Unknown=float("-inf")
    )

    def receive_record(self, record: GraphRecord):

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
                        (existing_rel.src.id, tuple(existing_rel.edge_type), existing_rel.tgt.id)
                    ])
                })
            )
        else:
            return GraphMessage(
                update_map=defaultdict(set,
                {
                    (EventType.Delete, EventTarget.Edge): set([
                        (new_edge.src.id, tuple(new_edge.edge_type), new_edge.tgt.id)
                    ])
                })
            )


class er_Participant(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Participant", "Context"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when you become a participant in a context,
            delete all other participant edges
        """

        edge = record.o_ref
        source_v = edge.src

        other_part_es = { pedge for pedge in source_v.out_edges.edgetype_to_edge["Participant"] if pedge is not edge }

        message = GraphMessage()

        for pedge in other_part_es:
            
            message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                (pedge.src.id, tuple(pedge.edge_type), pedge.tgt.id)
            )

        return message


class er_Engage(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Engage"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when you engage someone,
            both you and the target join the combat context
        """

        edge_types = tuple(self.reality.graph.vertices["Participant"].get_relationships("Is>", as_ids=True))
        combat_c = self.reality.graph.vertices["Combat_Context"]
        engage_v = record.o_ref

        engager = list(engage_v.in_edges.edgetype_to_vertex["Source"])[0]
        engagee = list(engage_v.in_edges.edgetype_to_vertex["Target"])[0]

        message = GraphMessage(
            update_map=defaultdict(set,
            {
                (EventType.Add, EventTarget.Edge): set([
                    (engager.id, edge_types, combat_c.id),
                    (engagee.id, edge_types, combat_c.id)
                ])
            })
        )

        return message


class er_Attack(EffectRule):
    objective_rule = True

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Attack"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when you attack somebody,
            if your armedness is equal to their armoredness:
                50% chance to wound
            if your armedness is greater than their armoredness:
                100% chance to wound
            else:
                0% chance to wound
        """

        attack_v = record.o_ref

        attacker = list(attack_v.in_edges.edgetype_to_vertex["Source"])[0]
        attackee = list(attack_v.in_edges.edgetype_to_vertex["Target"])[0]

        attacker_armedness = int( "Armed" in attacker.get_relationships("Has>", as_ids=True) )
        attackee_armoredness = int( "Armored" in attackee.get_relationships("Has>", as_ids=True) )

        if attacker_armedness < attackee_armoredness:
            print("bonk!")
            return None
        elif attacker_armedness > attackee_armoredness or random.randint(0,1):
            print("boingo!")
            return GraphMessage(
                update_map=defaultdict(set,
                {
                    (EventType.Add, EventTarget.Edge): set([
                        (attackee.id, ("Has",), "Wounded")
                    ])
                })
            )
        else:
            print("whiff!")
            return None


class er_Death(EffectRule):
    objective_rule = True

    record_keys = (
        (EventType.Duplicate, EventTarget.Edge, "Person", "Has", "Wounded"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when somebody who is already wounded gets wounded,
            kill em
        """

        person = record.o_ref.src

        print(f"{person.id} is dead!")

        return GraphMessage(
            update_map=defaultdict(set,
            {
                (EventType.Add, EventTarget.Edge): set([
                    (person.id, ("Is",), "Dead")
                ]),
                (EventType.Delete, EventTarget.Edge): set([
                    (person.id, ("Is",), "Person")
                ]),
            })
        )


class er_RemPerson(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Delete, EventTarget.Vertex, "Person"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when somebody stops being a person,
            they aren't part of contexts or any of that stuff anymore
        """

        person = record.o_ref

        del_edges = person.out_edges.edgetype_to_edge["Involved"]
        del_edges |= person.out_edges.edgetype_to_edge["Relationship"]
        del_edges |= person.in_edges.edgetype_to_edge["Relationship"]

        message = GraphMessage()

        for del_edge in del_edges:
            message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                (del_edge.src.id, tuple(del_edge.edge_type), del_edge.tgt.id)
            )

        return message


obj_effect_rules_map = dict()
subj_effect_rules_map = dict()
 
classes = [cls_obj for _, cls_obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(cls_obj) and hasattr(cls_obj, "record_keys")]
for class_obj in classes:
    for key in class_obj.record_keys:
        if class_obj.objective_rule:
            obj_effect_rules_map[key] = class_obj
        else:
            subj_effect_rules_map[key] = class_obj
