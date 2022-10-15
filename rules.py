
class ActionRule:

    def __init__(self, vertex, priority=0):
        # add self to vertex action_rules
        self.priority = priority
        self.vertex = vertex
        vertex.action_rules.append(self)
        vertex.action_rules = sorted(vertex.action_rules, key=lambda x: x.priority)
        pass

    def get_targets(self, graph, target_set, local_target_set):
        # return target_set, local_target_set, allow
        return target_set, local_target_set, True


class InheritedActionRule:

    def __init__(self, vertex, priority=0, replicate=True):
        if replicate is True:
            self.replicate(vertex)
        super().__init__(vertex, priority)

    def replicate(self, vertex):
        visited = set([vertex])
        queue = [vertex]
        while len(queue) > 0:
            root = queue.pop(0)
            for edge in root.in_edges.edgetype_to_edge["Is"]:
                child = self.graph.vertices[edge.src]
                if child in visited:
                    continue
                self.__class__(child, edge.attr_map.get("priority", 0), False)
                visited.add(child)
                queue.append(child)

"""
'Check' = If pattern fails, set allow to false. If pattern succeeds, set allow to true.
'Disallow' = If pattern matches, set allow to false.
'Allow Instance' = Allow every vertex 'instance' which matches the pattern.
'Disallow Instance' = Disallow every vertex 'instance' which matches the pattern.
'Get' = Simply exists to populate temporary variables. Note that all temporary vertex sets referenced in a 'Get' block should be initialized, even if not met.
'Disallow Allowed' = Disallow every vertex in target_set["allow"] which matches the pattern.

'(BFS)edge_type' = Iteratively traverse over this edge type until target ID is met.
v_0, v_1, v_2 = 'Variable' vertex. Anything that matches the pattern, regardless of id.
vertex("X") = Vertex has "X" in attr_map.

Action Rule

--Check--
Ego <-Is- v_0("Instance")
v_0 -Is-> v_1("Instance")
v_1 -Is-> Is
v_1 -Is-> Person

================================================================

Interaction_Action Rule

--Allow instance--
Person <-Is- v_0("Instance")
v_0 <-Is- Is
v_0 <-Is- instance

--Disallow instance--
Ego <-Is- instance("Instance")

================================================================

Conversation_Action Rule

--Disallow--
Ego <-Is- v_0("instance")
v_0 (BFS)-Is-> Involved
v_0 -Is-> Combat_Context
--Get--
Ego <-Is- v_1("instance")
v_1 -Is-> Participant
v_1 -Is-> v_2("Instance")
v_2 -Is-> Conversation_Context
--Disallow Allowed--
instance <-Is- v_3("instance")
v_3 -Is-> Participant
v_3 -Is-> v_4("Instance")
v_4 -Is-> Conversation_Context
v_4 != v_2

================================================================
"""
