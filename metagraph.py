from graph import Graph, Rule

# object which checks groups, AND within groups, OR outside groups

# if tgt_set is a dict...
# 

def check_member(src, tgt_set):
    # src is a list of sets or a single set, tgt_set is always one set
    if type(src) is list:
        return any([src_set.issubset(tgt_set) for src_set in src])
    elif type(src) is set:
        return src.issubset(tgt_set)
    else:
        return src in tgt_set


def get_members(src, tgt_dict, fetch_op=lambda x,y : x.get(y,None)):
    if type(src) is list:
        return set([src.issubset(tgt_set) for src_set in src])
    elif type(src) is set:
        return src.issubset(tgt_set)
    else:
        return src in tgt_set


class ActionRule(Rule):
    def transform(self, context, target_set: dict, allow: bool):
        return target_set, allow

    def __call__(self, context, target_set: dict, allow: bool):
        target_set = target_set.copy()
        t_target_set, t_allow = self.transform(context, target_set, allow)
        target_set["disallow"] = target_set["disallow"].union(t_target_set["disallow"])
        target_set["allow"] = target_set["allow"].union(t_target_set["allow"]).difference(target_set["disallow"])
        return target_set, allow and t_allow

class r_Allow(ActionRule):
    # if self is person, allow
    # else disallow}

    def __init__(self, allow_type):
        self.allow_type = allow_type

    def transform(self, context, target_set: dict, allow: bool):
        return target_set, check_member(self.allow_type, context.graph.vertices["ego"].out_edges.edgetype_to_id["Is"].keys())

class r_AllowIndividual(ActionRule):
    # get instance from Person not self
    # allow interaction action

    def __init__(self, allow_type):
        self.allow_type = allow_type

    def transform(self, context, target_set: dict, allow: bool):


        return target_set, allow


def generate_metagraph():
    import sys
    import inspect
    print([c[0'] for c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if "main" in str(c[1])])

generate_metagraph()
#metagraph = Graph()
#metagraph.load_json("./metagraph.json")

"""
SUBJECTIVE BRAIN ACTION VIABILITY RULES


what prevents one doing a unique conversation action again?
while timer disallows or if target has gotten an opportunity to respond***, you can't target them again
timer might need to be more sophisticated...
    geometric functional relationship? long-term and short-term timer?
    timer resets when you are no longer able? at least short-term timer does

what prevents a conversation response?
after some time, you aren't able to respond anymore
if you were allowed to respond, but failed within some time, you ignored it
if you were interrupted, that's fine

how should unique conversation actions work...
AsUnique edge...

CountsAs
RespondTag and ShareTag block each other
alternatively you just have a limit... greet limit = 1
CanRespond

class ActionRule(Rule):
    def __call__(self, target_set: dict, allow: bool):
        pass

class r_Action(ActionRule):
    # if self is person, allow
    # else disallow
    # viability checker breadth-first searches down the list...
    # passing a set that diminishes each time
    pass

class r_InteractionAction(ActionRule):
    # get instance from Person not self
    # allow interaction action
    pass

class r_ConversationAction(ActionRule):
    # if self in combat, disallow
    # for each allowed Person
    #   get self Participation ConversationContext (if none, fine)
    #   check last participation
    #   if ConversationContext and not same as self participation
    #       disallow for this person
    #   else allow for this person
    pass

class r_ResponseConversationAction(ActionRule):
    # PASS RULE TO ROOT ON ADD
    # for each action last timestep that is of a type that 'CanRespond'
    #   if not responded to by self and within some time threshold, allow
    #   else disallow
    pass

class r_UniqueConversationAction(ActionRule):
    # PASS RULE TO ROOT ON ADD
    # for each allowed Person
    # if root (or something AsUnique) not exist between self and other, allow
    # else disallow
    pass

class r_FriendlyConversationAction(ActionRule):
    # for each allowed Person
    # check last relationship between self and other
    # if not HostileRelationship, allowl
    # else disallow
    pass

# CombatAction doesn't have a rule

class r_Greet(ActionRule):
    # TRACK which people have been disallowed (this should be a passed rule, I think)
    # for each allowed Person
    # if self and person in same non-combat context, disallow
    pass

# AskTags doesn't have a rule

# RespondTags doesn't have a rule

# OfferTags doesn't have a rule

class r_Engage(ActionRule):
    # for each allowed Person
    # if self in calm or if not (self and person participant in combat)
    pass

class r_Attack(ActionRule):
    # if self not in combat, disallow
    # for each allowed Person
    # if person in combat allow
    # else disallow
    pass

class r_Rest(ActionRule):
    # if room empty allow
    # else disallow
    pass

class r_Wait(ActionRule):
    # if number of waits too great, disallow
    # defer until end,
    # if there is action that can be taken as RESPONSE, disallow
    # else allow
    pass

class r_Loot(ActionRule):
    # if self in calm
    # for each instance of Dead
    pass

class r_Flee(ActionRule):
    # if self participant in combat
    # for each door, allow
    pass

class r_Enter(ActionRule):
    # if traverse last turn, FORCE
    pass

class r_Traverse(ActionRule):
    # if self in calm
    # for each door, allow
    pass

class r_SendOff(ActionRule):
    # for each allowed Person
    # if source or person traverse last turn, allow
    # allow (but force traverse next turn)
    # NOTE: remember to remove from conversation context
    pass
"""
