from collections import defaultdict
from random import sample
from string import ascii_lowercase
from pprint import pprint
num_ascii = len(ascii_lowercase)

def get_alphastring(num, string=""):

    mod = num % num_ascii
    num = (num - mod) // num_ascii
    string = ascii_lowercase[mod] + string

    if num > num_ascii:
        string = get_alphastring(num, string)
    elif num > 0:
        string = ascii_lowercase[num-1] + string
    
    return string


class ChooseMaker:
    def __init__(self):
        self.make = "choose"

    def consider(self, target_map, ego, graph):
        return graph.vertices["Wait"], ego


class PlayerChooseMaker(ChooseMaker):

    context_priority_map = {
        "Combat_Context": 2,
        "Conversation_Context": 1,
        "Calm_Context": 0
    }

    relationship_priority_map = {
        "Hostile_Relationship":3,
        "Friendly_Relationship":2,
        "Known_Relationship":1,
        "Unknown_Relationship":0,
    }

    def __init__(self):
        self.make = "player choose"

    def consider(self, target_map, ego, graph):

        # print context
        context_set = list(ego.out_edges.edgetype_to_vertex.get("Participant", set()))
        if len(context_set) == 0:
            context_set = ego.out_edges.edgetype_to_vertex.get("Bystander", set())
        context_id, context_priority = "Calm_Context", 0
        for context in context_set:
            if "Instance" in context.get_relationships("Is>", as_ids=True):
                context_parents = [p for p in context.out_edges.edgetype_to_vertex.get("Is") 
                    if "Context" in p.get_relationships("Is>", as_ids=True)]
                if len(context_parents) > 0:
                    new_context_id = context_parents[0].id
            else:
                new_context_id = context.id
            priority = self.__class__.context_priority_map.get(new_context_id, -1)
            if priority > context_priority:
                context_priority = priority
                context_id = new_context_id

        print(f"You are in: {context_id}")

        # print relationships
        relationship_map = defaultdict(lambda: ("Unknown_Relationship", -1))
        for edge in ego.out_edges.edgetype_to_edge.get("Relationship", set()):
            highest_key = max(edge.edge_type, key=lambda x: self.__class__.relationship_priority_map.get(x, float("-inf")))
            priority = self.__class__.relationship_priority_map.get(highest_key, -1)
            if priority > relationship_map[edge.tgt][1]:
                relationship_map[edge.tgt] = (highest_key, priority)

        for target_person, relationship in relationship_map.items():
            print(f"You have {relationship[0]} with {target_person.id}")

        if len(target_map) == 0:
            print(f"No actions to take, '{ego.id}'!")
            return graph.vertices["Wait"], ego

        print(f"Consider, '{ego.id}'...")

        action_label_map = dict()
        target_label_map = dict()

        num_actions = len(target_map)
        action_i_len = len(str(num_actions))
        for i, pair in enumerate(target_map.items()):
            action, targets = pair

            action_label_map[i] = action
            print(f"{i:>{action_i_len}}. {action}:")

            target_i_len = len(get_alphastring(len(targets)))
            for j, target in enumerate(targets):
                alpha = get_alphastring(j)
                target_label_map[(i, alpha)] = target
                print(f"\t{alpha:>{target_i_len}}. {target}")

        good_act = False
        while not good_act:
            print(f"Act, {ego.id}...")
            
            act_choose = input()

            try:
                act_choose = int(act_choose)
                chosen_action = action_label_map[act_choose]
                targets = target_map[chosen_action]
                good_act = True

            except:
                print(f"Action Input '{act_choose}' invalid.")
                continue

            good_target = False
            while not good_target:
                print(f"Target, {ego.id}...")
                print("[input '!' to return to Action choice]")
                target_choose = input()

                if target_choose == "!":
                    print("Cancelling Action Choice")
                    good_act = False
                    break

                try:
                    chosen_target = target_label_map[(act_choose, target_choose)]
                    good_target = True
                except:
                    print(f"Target Input '{target_choose}' invalid.")
                    continue
            
                print(f"{ego.id} Chooses...")
                print(f"Action: {chosen_action}")
                print(f"Target: {chosen_target}")
                print(f"[input 'y' to confirm choice or 'n' to return to Action choice]")

                good_confirm = False
                while not good_confirm:

                    confirm_choose = input()

                    if confirm_choose == "y":
                        print("Confirming Choice")
                        good_confirm = True
                    elif confirm_choose == "n":
                        print("Rejecting Choice - Returning to Action choice")
                        good_act = False
                        good_target = False
                        break
                    else:
                        print("Bad input. Please input 'y' or 'n'.")

        return chosen_action, chosen_target


class AIChooseMaker(ChooseMaker):
    def __init__(self):
        self.make = "AI choose"

    def consider(self, target_map, ego, graph):

        if len(target_map) == 0:
            return None, None

        action = sample(list(target_map.keys()), k=1)[0]
        target = sample(list(target_map[action]), k=1)[0]

        return action, target
