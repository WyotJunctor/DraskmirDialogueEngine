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
    def __init__(self):
        self.make = "player choose"

    def consider(self, target_map, ego, graph):

        if len(target_map) == 0:
            print(f"No actions to take, 'ego.id'!")
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

        action = sample(list(target_map.keys()), k=1)
        target = sample(list(target_map[action]), k=1)

        return graph.vertices[action], graph.vertices[target]
