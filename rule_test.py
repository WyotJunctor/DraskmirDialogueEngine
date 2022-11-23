from brain import Brain
from graph import Graph
from subjective_action_rules import rules_map
from pprint import pprint

# populate brain with concepts, people, and some state
graph_json = "./drask_graph.json"

sub_graph = Graph()
sub_graph.load_json(graph_json)
sub_graph.load_rules(rules_map)
sub_brain = Brain(sub_graph, dict())

pprint(sub_brain.graph.vertices["Action"].in_edges.edgetype_to_id)

sub_brain.get_targets()
