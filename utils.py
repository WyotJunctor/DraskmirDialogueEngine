def bfs(graph, queue):
    pass

def merge_targets(target_set_1, target_set_2):
    merged_target_set = {
        "allow": target_set_1["allow"].union(target_set_2["allow"]),
        "disallow": target_set_1["disallow"].union(target_set_2["disallow"])
    }
    merged_target_set["allow"] = merged_target_set["allow"].difference(merged_target_set["disallow"])
    return merged_target_set
