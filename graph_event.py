import itertools
from collections import defaultdict
from enum import Enum
from pprint import pprint


class EventType(Enum):
    Add = 0
    Delete = 1
    Duplicate = 2


class EventTarget(Enum):
    Vertex = 0
    Edge = 1
    Attribute = 2


class GraphMessage:
    def __init__(self, update_map=None):
        self.update_map = update_map if update_map is not None else defaultdict(
            set)

    def merge(self, message):
        new_update_map = self.update_map.copy()
        for key, val in message.update_map.items():
            new_update_map[key] = new_update_map[key] | val
        return GraphMessage(update_map=new_update_map)

    def copy(self):
        update_map = self.update_map.copy()
        return GraphMessage(update_map)


class UpdateRecord:
    def __init__(self):
        self.add_records = set()
        self.del_records = set()

    def add_edge(self, edge, add):
        if add == True:
            self.add_records.add(edge)
        else:
            self.del_records.add(edge)

    def is_empty(self) -> bool:
        return len(self.add_records) == 0 and len(self.del_records) == 0

    def update_with(self, records):
        # add del to del, add to add, sub del from add
        self.del_records = self.del_records.union(records.del_records)
        self.add_records = self.add_records.union(records.add_records)
        self.add_records = self.add_records.difference(records.add_records)
