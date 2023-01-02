import inspect, sys

from graph_event import EventType, EventTarget, GraphMessage

class UpdateRule():
    def __init__(self, reality):
        self.reality = reality

    def step(self):
        pass

class ur_TimeBucketing(UpdateRule):
    objective_rule = False

    bucket_infos = {
        "Past": (float("inf"), "Past"),
        "Recent": (3.0, "Past"),
        "Immediate": (1.0, "Recent"),
    }

    def step(self):
        """
        Every step, time bucketables need to add themselves to older buckets if necessary
        """

        message = GraphMessage()
        visited_vertices = set()

        for bucket_label, bucket_info in ur_TimeBucketing.bucket_infos.items():
            bucket_threshold, next_bucket = bucket_info

            bucket_members = {
                vertex for vertex in self.reality.graph.vertices[bucket_label].in_edges.edgetype_to_vertex["Has"]
                if vertex not in visited_vertices
            }
            visited_vertices |= bucket_members

            for member in bucket_members:
                delta = self.reality.clock.timestep - member.created_timestep

                if delta >= bucket_threshold:
                    message.update_map[(EventType.Add, EventTarget.Edge)].add(
                        (member.id, ("Has",), next_bucket)
                    )

        return message


class ur_CombatEnd(UpdateRule):
    objective_rule = False

    def step(self):
        """
        If there are no Recent, non-Past Combat_Actions, end the combat
        """

        non_past_combats = { 
            vertex for vertex in self.reality.graph.vertices["Instance"].in_edges.edgetype_to_vertex["Is"]
            if "Past" not in vertex.get_relationships("Has>", as_ids=True)
            and "Combat_Action" in vertex.get_relationships("Is>", as_ids=True)
        }

        # if there are non-past combat actions, fight continues
        if len(non_past_combats) > 0:
            return None

        # otherwise end the fight

        message = GraphMessage()
        combat_v = self.reality.graph.vertices["Combat_Context"]
        calm_v = self.reality.graph.vertices["Calm_Context"]
        byst_rels = tuple(self.reality.graph.vertices["Bystander"].get_relationships("Is>", as_ids=True))

        for invol_v in combat_v.in_edges.edgetype_to_vertex["Involved"]:
            invol_v_rels = tuple(invol_v.out_edges.id_to_edgetype["Combat_Context"].keys())
            message.update_map[(EventType.Delete, EventTarget.Edge)].add(
                (invol_v.id, invol_v_rels, combat_v.id)
            )
            message.update_map[(EventType.Add, EventTarget.Edge)].add(
                (invol_v.id, byst_rels, calm_v.id)
            )

        return message


class ur_ConvoEnd(UpdateRule):
    objective_rule = False

    def step(self):
        """
        If there are no Recent, non-Past Conversation_Actions, end the Conversation
        """
        
        message = GraphMessage()
        # get all conversation instances
        conversations = (
            vertex for vertex in self.reality.graph.vertices["Instance"].in_edges.edgetype_to_vertex["Is"]
            if "Conversation_Context" in vertex.get_relationships("Is>", as_ids=True)
        )

        # get participants
        # if no participants, delete the instance
        # if no non-past actions by participants... delete the instance
        for conversation in conversations:
            participants = conversation.in_edges.edgetype_to_vertex.get("Participant", set())
            if len(participants) == 0:
                message.update_map[(EventType.Delete, EventTarget.Vertex)].add(conversation.id)
                continue
            conversation_ok = False
            for participant in participants:
                for action in participant.in_edges.edgetype_to_vertex.get("Source", set()):
                    if "Past" not in action.get_relationships("Has>", as_ids=True) and participants.isdisjoint(action.get_relationships("<Target")):
                        conversation_ok = True
                        break
                if conversation_ok is True:
                    break
            if conversation_ok is False:
                message.update_map[(EventType.Delete, EventTarget.Vertex)].add(conversation.id)

        return message


obj_update_rules = list()
subj_update_rules = list()
 
classes = [cls_obj for _, cls_obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(cls_obj) and hasattr(cls_obj, "objective_rule")]
for class_obj in classes:
    if class_obj.objective_rule:
        obj_update_rules.append(class_obj)
    else:
        subj_update_rules.append(class_obj)
