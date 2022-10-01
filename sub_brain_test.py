from brain import Brain
from graph import Graph

class ActionBrain(Brain):

    def check_final_actions(self):

        pass

    def check_actions(self):
        self.check_final_actions()

# populate brain with concepts, people, and some state
sub_graph = Graph(self)
sub_graph.load_json(json_path)
sub_brain = ActionBrain(sub_graph, dict())

# special function which passes in a dict(str(allow/disallow): vertex, set(vertex)) [target -> actions], bool [allow/disallow]
# populates that thing.
sub_brain.check_actions()
sub_brain.check_final_actions()
