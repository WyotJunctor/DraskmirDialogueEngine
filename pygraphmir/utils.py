from collections import Counter

def bfs(graph, queue):
    pass

def merge_targets(target_set_1, target_set_2):
    merged_target_set = {
        "allow": target_set_1["allow"].union(target_set_2["allow"]),
        "disallow": target_set_1["disallow"].union(target_set_2["disallow"])
    }
    merged_target_set["allow"] = merged_target_set["allow"].difference(merged_target_set["disallow"])
    return merged_target_set

def get_set(target_map, key, fetch_lambda=lambda x, y: set(x[y]) ) :
    if key in target_map:
        return fetch_lambda(target_map, key)
    return set()

def get_key_set(target_map, key):
    return get_set(target_map, key, fetch_lambda=lambda x, y: set(x[y].keys()))

def to_counter(target_set):
    return Counter({v:1 for v in target_set})
