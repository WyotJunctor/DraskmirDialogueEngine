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

# if list, get union of
# if set, get intersection of members of fetch_op
def get_members(src, tgt_dict, fetch_op=lambda x,y : x.get(y,None)):
    if type(src) is list:
        return set.union([set.intersection([fetch_op(tgt_dict, src_elem) for src_set in src for src_elem in src_set])])
    elif type(src) is set:
        return set.intersection([fetch_op(tgt_dict, src_elem) for src_elem in src])
    else:
        return fetch_op(tgt_dict, src)

def get_vertex_set(context, vertex, member_edge, group_edge):
    result = None
    v_set = context.graph.vertices[vertex.id].in_edges.edgetype_to_id[member_edge]
    if len(v_set) > 0:
        result = set(v_set)
    else:
        v_set = context.graph.vertices[vertex.id].in_edges.edgetype_to_id[group_edge]
        result = list()
        for v_group in v_set:
            result.append(set(context.graph.vertices[v_group].in_edges.edgetype_to_id[member_edge]))
    return result


def check_member_is(context, src, tgt_set):
    return True

def get_current_context(context, vertex, involved_edge):
    return ""

class ActionRule(Rule):
    def __init__(self, context, vertex):
        self.ego = vertex.in_edges.edgetype_to_id("Is_Ego")

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

    def __init__(self, context, vertex):
        super().__init__(context, vertex)
        self.allow_type = get_vertex_set(context, vertex, "Allow_Type", "Allow_group")

    def transform(self, context, target_set: dict, allow: bool):
        return target_set, check_member(self.allow_type, self.ego.out_edges.edgetype_to_id["Is"].keys())

class r_AllowIndividual(ActionRule):
    # get instance from Person not self
    # allow interaction action

    def __init__(self, context, vertex):
        super().__init__(context, vertex)
        self.allow_type = get_vertex_set(context, vertex, "Allow_type", "Allow_Group")

    def transform(self, context, target_set: dict, allow: bool):
        allow_set = get_members(allow_type, context.graph.vertices, fetch_op=lambda x,y : x[y].edgetype_to_id["Is"].keys())
        target_set["allow"] = target_set["allow"].union(allow_set)
        target_set.remove(self.ego)
        return target_set, allow


class r_SameContext(ActionRule):

    def __init__(self, context, vertex):
        super().__init__(context, vertex)
        self.allow_context = get_vertex_set(context, vertex, "Allow_Context", "Allow_Group")
        self.disallow_context = get_vertex_set(context, vertex, "Disallow_Context", "Disallow_Group")
        self.same_context_check = get_vertex_set(context, vertex, "Check_Context", "Check_Group")

    def transform(self, context, target_set: dict, allow: bool):
        most_recent_context = get_current_context(context, self.ego, "Participant")
        allow = len(self.allow_context) == 0 or check_member(self.allow_context, most_recent_context)
        allow = allow and not check_member_is(self.allow_context, most_recent_context)
        if allow == False:
            return target_set, allow
        allow_set = set([p for p in target_set["allow"] if get_current_context(context, p, "Participant") == most_recent_context])
        target_set["disallow"].union(target_set["allow"].difference(allow_set))
        target_set["allow"] = allow_set
        return target_set, allow

"""
metagraph vertices contain a reference to a class.
when they add an instance, they instantiate that instance 'on' the instance vertex

if ego in disallow context, disallow
if ego and other in same context, allow other, else disallow other

NOTE: 'in context' check involves getting most recent edge
"""

class r_ResponseConversationAction(ActionRule):
    # PASS RULE TO ROOT ON ADD
    # for each action last timestep that is of a type that 'CanRespond'
    #   if not responded to by self and within some time threshold, allow
    #   else disallow
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



def generate_metagraph():
    import sys
    import inspect
    print([c[0] for c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if "main" in str(c[1])])

generate_metagraph()
#metagraph = Graph()
#metagraph.load_json("./metagraph.json")

"""
"""

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
