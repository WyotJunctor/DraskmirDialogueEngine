from brain import Brain

class ActionBrain(Brain):
    pass

sub_graph = Graph(self)
sub_graph.load_json(json_path)
sub_brain = ActionBrain(sub_graph, set())

"""
SUBJECTIVE BRAIN ACTION VIABILITY RULES

class r_Action(Rule):
    # if self is person, allow
    # else disallow
    # viability checker breadth-first searches down the list...
    # passing a set that diminishes each time
    pass

class r_InteractionAction(Rule):
    # get instance from Person not self
    # allow interaction action
    pass

class r_ConversationAction(Rule):
    # if self in combat, disallow for all people
    # for each allowed Person
    #   get self Participation ConversationContext (if none, fine)
    #   check last participation
    #   if ConversationContext and not same as self participation
    #       disallow for this person
    #   else allow for this person
    pass

class r_UniqueConversationAction(Rule):
    # PASS RULE TO ROOT ON ADD
    # for each allowed Person
    # if root not exist between self and other, allow
    # else disallow
    pass

class r_FriendlyConversationAction(Rule):
    # for each allowed Person
    # check last relationship between self and other
    # if not HostileRelationship, allow
    # else disallow
    pass

# CombatAction doesn't have a rule

class r_Greet(Rule):
    # TRACK which people have been disallowed (this should be a passed rule, I think)
    # for each allowed Person or (RESPONSE) Greet action with self as target
    # if self and person in same non-combat context, disallow
    pass

# AskTags doesn't have a rule

class r_ShareTags(Rule):
    # (RESPONSE) for each AskTags with self as target
    pass

# OfferTags doesn't have a rule

class r_Engage(Rule):
    # for each allowed Person
    # if self and person not in combat
    pass

class r_Attack(Rule):
    # if self not in combat, disallow
    # for each allowed Person
    # if person in combat allow
    # else disallow
    pass

class r_Rest(Rule):
    # if room empty allow
    # else disallow
    pass

class r_Wait(Rule):
    # wait until end,
    # if there is action that can be taken in response, disallow
    # if number of waits too great, disallow
    # else allow
    pass

class r_Loot(Rule):
    # if self in calm
    # for each instance of Dead
    pass

class r_Flee(Rule):
    # if self participant in combat
    # for each door, allow
    pass

class r_Enter(Rule):
    # if traverse last turn, FORCE
    pass

class r_Traverse(Rule):
    # if self in calm
    # for each door, allow
    pass

class r_SendOff(Rule):
    # for each allowed Person or each SendOff with self as target
    # if self not send off to person
    # if source or person traverse last turn, allow
    # allow (but force traverse next turn)
    # NOTE: remember to remove from conversation context
    pass
"""
