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


class ActionViabilityRule(Rule):
    def __call__(self, target_set: dict, allow: bool):
        pass

class r_Action(ActionViabilityRule):
    # if self is person, allow
    # else disallow
    # viability checker breadth-first searches down the list...
    # passing a set that diminishes each time
    pass

class r_InteractionAction(ActionViabilityRule):
    # get instance from Person not self
    # allow interaction action
    pass

class r_ConversationAction(ActionViabilityRule):
    # if self in combat, disallow for all people
    # for each allowed Person
    #   get self Participation ConversationContext (if none, fine)
    #   check last participation
    #   if ConversationContext and not same as self participation
    #       disallow for this person
    #   else allow for this person
    pass

class r_UniqueConversationAction(ActionViabilityRule):
    # PASS RULE TO ROOT ON ADD
    # for each allowed Person
    # if root not exist between self and other, allow
    # else disallow
    # PASS RULE to instance,
    # check target as self for viability of possible response?
    pass

class r_FriendlyConversationAction(ActionViabilityRule):
    # for each allowed Person
    # check last relationship between self and other
    # if not HostileRelationship, allow
    # else disallow
    pass

# CombatAction doesn't have a rule

class r_Greet(ActionViabilityRule):
    # TRACK which people have been disallowed (this should be a passed rule, I think)
    # for each allowed Person
    # if self and person in same non-combat context, disallow
    pass

class r_ReturnGreeting(ActionViabilityRule): # is Greet, Response
    (RESPONSE) Greet action with self as target
    pass

# AskTags doesn't have a rule

class r_ShareTags(ActionViabilityRule):
    # (RESPONSE) for each AskTags with self as target
    pass

# OfferTags doesn't have a rule

class r_Engage(ActionViabilityRule):
    # for each allowed Person
    # if self and person not in combat
    pass

class r_Attack(ActionViabilityRule):
    # if self not in combat, disallow
    # for each allowed Person
    # if person in combat allow
    # else disallow
    pass

class r_Rest(ActionViabilityRule):
    # if room empty allow
    # else disallow
    pass

class r_ResponseConversationAction(ConversationAction):
    # PASS RULE TO ROOT
    # if wait too long, disallow
    #
    pass

class r_Wait(ActionViabilityRule):
    # if number of waits too great, disallow
    # defer until end,
    # if there is action that can be taken as RESPONSE, disallow
    # else allow
    pass

class r_Loot(ActionViabilityRule):
    # if self in calm
    # for each instance of Dead
    pass

class r_Flee(ActionViabilityRule):
    # if self participant in combat
    # for each door, allow
    pass

class r_Enter(ActionViabilityRule):
    # if traverse last turn, FORCE
    pass

class r_Traverse(ActionViabilityRule):
    # if self in calm
    # for each door, allow
    pass

class r_SendOff(ActionViabilityRule):
    # for each allowed Person or (RESPONSE) each SendOff with self as target
    # if source or person traverse last turn, allow
    # allow (but force traverse next turn)
    # NOTE: remember to remove from conversation context
    pass

class r_ReturnSendOff
"""
