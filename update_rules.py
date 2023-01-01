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

        for bucket_label, bucket_info in ur_TimeBucketing.bucket_infos:
            bucket_threshold, next_bucket = bucket_info

            bucket_members = {
                vertex for vertex in self.reality.graph[bucket_label].in_edges.edgetype_to_vertex["Has"]
                if vertex not in visited_vertices
            }
            visited_vertices |= bucket_members

            for member in bucket_members:
                delta = member.created_timestep - self.reality.clock.timestep

                if delta >= bucket_threshold:
                    message.update_map[(EventType.Add, EventTarget.Edge)].add(
                        (member.id, "Has", next_bucket)
                    )

        return message


obj_update_rules = list()
subj_update_rules = list()
 
classes = [cls_obj for _, cls_obj in inspect.getmembers(sys.modules[__name__]) if inspect.isclass(cls_obj) and hasattr(cls_obj, "objective_rule")]
for class_obj in classes:
    if class_obj.objective_rule:
        obj_update_rules.append(class_obj)
    else:
        subj_update_rules.append(class_obj)
