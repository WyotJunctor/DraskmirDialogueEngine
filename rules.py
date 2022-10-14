
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
