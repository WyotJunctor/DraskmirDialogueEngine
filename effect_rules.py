import inspect
import sys
import random
from pprint import pprint

from collections import defaultdict
from graph_event import EventType, EventTarget, GraphRecord, GraphMessage
from instancegen import get_next_instance_id

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
    rel_prios = {
        "Hostile_Relationship":float("inf"),
        "Friendly_Relationship":1000.0,
        "Known_Relationship":0.0,
        "Unknown_Relationship":-1000.0,
    }

    def receive_record(self, record: GraphRecord):

        """
        look at the existing Relationship edge between these two
        if the existing Relationship has priority delete the new one,
            otherwise delete the existing one
        """

        new_edge = record.o_ref
        new_tgt = record.o_ref.tgt
        existing_rels = set([
            ex_edge for ex_edge in new_edge.src.out_edges.edgetype_to_edge["Relationship"] if ex_edge.tgt is new_tgt
        ])

        # assert(len(existing_rels) <= 1)

        if len(existing_rels) == 0:
            return None

        highest_prio_rel, highest_prio = None, float("-inf")
        for rel in existing_rels:
            highest_key = max(rel.edge_type, key=lambda x: self.__class__.rel_prios.get(x, float("-inf")))
            prio = self.__class__.rel_prios.get(highest_key, float("-inf"))
            if prio >= highest_prio:
                highest_prio_rel = rel
                highest_prio = prio

        existing_rels.discard(highest_prio_rel)

        message = GraphMessage()
        for rel in existing_rels:
            # print(rel)
            message.update_map[(EventType.Delete, EventTarget.Edge)].add((rel.src.id, tuple(rel.edge_type), rel.tgt.id))
        return message

class er_ParticipantCulling(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Participant", "Context"),
        (EventType.Duplicate, EventTarget.Edge, "Person", "Participant", "Context"),
    )

    def receive_record(self, record: GraphRecord):

        """
        when you become a participant in a context,
            delete all other participant edges
        """

        edge = record.o_ref
        source_v = edge.src

        other_involve_es = { iedge for iedge in source_v.out_edges.edgetype_to_edge["Involved"] if iedge is not edge }

        message = GraphMessage()

        for iedge in other_involve_es:
            
            message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                (iedge.src.id, tuple(iedge.edge_type), iedge.tgt.id)
            )

        return message


class er_OnParticipantDelete(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Delete, EventTarget.Edge, "Person", "Participant", "Context"),
    )

    def receive_record(self, record: GraphRecord):
        """
        when a participation edge is deleted, become a bystander of the calm context
        """

        # get person vertex
        person = record.o_ref.src

        # add edge
        message = GraphMessage()

        bystander_labels = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>"))

        message.update_map[(EventType.Add, EventTarget.Edge)].add(
            (person.id, bystander_labels, "Calm_Context")
        )


class er_BystanderCulling(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Bystander", "Context")
    )

    def receive_record(self, record: GraphRecord):
        """
        If the person is becoming a Bystander and is already a participant, delete the Bystander
        """

        new_edge = record.o_ref
        source_person = new_edge.src
        target_context = new_edge.tgt

        # if the person is already a participant in the context, delete the bystanderitude
        if target_context in source_person.get_relationships("Participant>"):
            return GraphMessage(defaultdict(set,{
                (EventType.Delete, EventTarget.Edge): set([
                    (source_person.id, tuple(new_edge.edgetype), target_context.id)
                ])
            }))

        return None


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

        bystander_types = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>", as_ids=True))
        participant_types = tuple(self.reality.graph.vertices["Participant"].get_relationships("Is>", as_ids=True))
        people = self.reality.graph.vertices["Person"].in_edges.edgetype_to_vertex["Is"]

        for person in people:
            if person in (engager, engagee):
                continue

            # add bystander edge to Combat
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (person.id, bystander_types, combat_c.id)
            )

            # remove participation in other contexts
            person_participations = person.out_edges.edgetype_to_id["Participant"]

            for participation_id in person_participations:
                message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                    (person.id, participant_types, participation_id)
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

        print(f"'{attacker}' attacks '{attackee}'")

        if attacker_armedness < attackee_armoredness:
            print("bonk!")
            return None
        elif attacker_armedness > attackee_armoredness:
            print("kazoingo!")
            return GraphMessage(
                update_map=defaultdict(set,
                {
                    (EventType.Add, EventTarget.Edge): set([
                        (attackee.id, ("Has",), "Wounded")
                    ])
                })
            )
        elif attacker_armedness == attackee_armoredness and random.randint(0,1):
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

class er_AddResponseAction(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Response_Conversation_Action"),
    )

    def receive_record(self, record: GraphRecord):
        """
        when someone responds to an action, it should actually target both the action and the source of the action
        """
        action = record.o_ref

        # get source of action
        target_action = list(action.in_edges.edgetype_to_vertex["Target"])[0]
        target_person = list(target_action.in_edges.edgetype_to_vertex["Source"])
        if len(target_person) == 0:
            return None
        target_person = target_person[0]

        message = GraphMessage(update_map=defaultdict(
            set,
            {
                (EventType.Add, EventTarget.Edge): {(target_person.id, ("Target",), action.id)}
            }
        ))

        return message


class er_CombatContextJoin(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Edge, "Person", "Participant", "Combat_Context")
    )

    def receive_record(self, record: GraphRecord):
        """
        When anybody starts participating in combat, everyone else becomes a bystander
        """

        message = GraphMessage()

        bystander_labels = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>", as_ids=True))
        people = self.reality.graph.vertices["Person"].in_edges.edgetype_to_vertex["Is"]

        for person in people:
            combat_relationship = person.out_edges.id_to_edge.get("Combat_Context")

            if len(people) == 1:
                message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                    (person.id, tuple(combat_relationship.edge_type), "Combat_Context")
                ) 

            # if the person already has a relationship to Combat, don't set anything up
            if combat_relationship is not None:
                continue

            # otherwise, the person needs to be a bystander
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (person.id, bystander_labels, "Combat_Context")
            )

        return message


class er_Immediateify(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Track_Time"),
    )

    def receive_record(self, record: GraphRecord):
        """
        When a track time is added, it needs to be put in the "Immediate" time bucket
        """

        return GraphMessage(update_map=defaultdict(set,{
            (EventType.Add, EventTarget.Edge): set([
                (record.o_ref.id, ("Has",), "Immediate")
            ])
        }))


class er_Convo(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Conversation_Action"),
    )

    def receive_record(self, record: GraphRecord):
        """
        if neither person is in a conversation, create one, add source as participant, target as bystander
        if one persion is in a conversation, 
        """

        message = GraphMessage()

        conv_v = record.o_ref

        conversator = list(conv_v.in_edges.edgetype_to_vertex["Source"])[0]
        conversatee = list(conv_v.in_edges.edgetype_to_vertex["Target"])[0]

        known_rel_labels = tuple(self.reality.graph.vertices["Known_Relationship"].get_relationships("Is>", as_ids=True))

        message.update_map[(EventType.Add, EventTarget.Edge)].add((conversator.id, known_rel_labels, conversatee.id))

        src_convos = [ 
            vertex for vertex in conversator.out_edges.edgetype_to_vertex["Participant"] 
            if "Conversation_Context" in vertex.get_relationships("Is>", as_ids=True)
        ]
        tgt_convos = [ 
            vertex for vertex in conversatee.out_edges.edgetype_to_vertex["Participant"] 
            if "Conversation_Context" in vertex.get_relationships("Is>", as_ids=True)
        ]

        convo_id = None

        if len(src_convos) > 0:
            convo_id = src_convos[0].id
        elif len(tgt_convos) > 0:
            convo_id = tgt_convos[0].id

        if convo_id is None:
            convo_id = get_next_instance_id()
            message.update_map[(EventType.Add, EventTarget.Vertex)].add(convo_id)
            message.update_map[(EventType.Add, EventTarget.Edge)].add((convo_id, ("Is",), "Instance"))
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (convo_id, ("Is",), "Conversation_Context")
            )

        part_labels = tuple(self.reality.graph.vertices["Participant"].get_relationships("Is>", as_ids=True))
        byst_labels = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>", as_ids=True))
        message.update_map[(EventType.Add, EventTarget.Edge)].add(
            (conversator.id, part_labels, convo_id)
        )
        message.update_map[(EventType.Add, EventTarget.Edge)].add(
            (conversatee.id, byst_labels, convo_id)
        )

        return message


class er_OnCombatAction(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Combat_Action"),
    )

    def receive_record(self, record: GraphRecord):
        """
        when add combat action, make relationship hostile
        """
        message = GraphMessage()

        conv_v = record.o_ref

        src_person = list(conv_v.in_edges.edgetype_to_vertex["Source"])[0]
        tgt_person = list(conv_v.in_edges.edgetype_to_vertex["Target"])[0]

        rel_labels = tuple(self.reality.graph.vertices["Hostile_Relationship"].get_relationships("Is>", as_ids=True))

        message.update_map[(EventType.Add, EventTarget.Edge)].add((src_person.id, rel_labels, tgt_person.id))
        message.update_map[(EventType.Add, EventTarget.Edge)].add((tgt_person.id, rel_labels, src_person.id))

        return message


class er_OnFriendlyAction(EffectRule):
    objective_rule = False

    record_keys = (
        (EventType.Add, EventTarget.Vertex, "Friendly_Conversation_Action"),
    )

    def receive_record(self, record: GraphRecord):
        """
        when add combat action, make relationship hostile
        """
        message = GraphMessage()

        conv_v = record.o_ref

        src_person = list(conv_v.in_edges.edgetype_to_vertex["Source"])[0]
        tgt_person = list(conv_v.in_edges.edgetype_to_vertex["Target"])[0]

        rel_labels = tuple(self.reality.graph.vertices["Friendly_Relationship"].get_relationships("Is>", as_ids=True))

        message.update_map[(EventType.Add, EventTarget.Edge)].add((src_person.id, rel_labels, tgt_person.id))

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
