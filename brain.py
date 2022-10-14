from utils import merge_targets
import copy

class Brain:

    def __init__(self, graph, rules: dict):
        self.graph = graph
        self.rules = rules

    def get_targets(self):
        # get root action
        target_map = {"Action": [{"allow":set(), "disallow":set()}, 0, 0]} # vertex: [target_set, num_calculated_dependencies, num_dependencies]
        queue = [self.graph.vertices.["Action"]]
        while len(queue) > 0:
            root = queue.pop(0)
            target_set, local_target_set, allow = root.get_targets(self.graph, target_map[root])
            if allow is False:
                continue
            target_map[root][0] = merge_targets(target_set, local_target_set)
            for child in root.in_edges.edgetype_to_id["Is"]:
                child_vert = self.graph.vertices[child]
                if child not in target_map:
                    target_map[child] = [
                        copy.deepcopy(target_set), 1,
                        len([v for v in child_vert.out_edges.edgetype_to_id["Is"] if "Action" in self.graph.vertices[v].attr_map])
                    ]
                else:
                    target_map[child][0] = merge_targets(target_map[child][0], target_set)
                    target_map[child][1] += 1
                if target_map[child][1] == target_map[child][2]:
                    queue.append(child_vert)
        print(target_map)
