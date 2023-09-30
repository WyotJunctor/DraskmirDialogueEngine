from game import Game
from choose import AIChooseMaker

"""
reality brain probably needs functions for:
    player, person:
        entering,
        leaving,
        dying
a dict/container for:
    person to brain (and maybe reverse)
    active rule hooks


graph objects need hooks for
on create
on turn (only if defined is it invoked)
on attribute updated (if anything gets changed)
on edge change (+ enum of what kind of change, attribute update? addition? deletion?)
on delete

as context, the rules are given the relevant brain
rules know which event to hook into

code loop:
reality brain checks on turn events in the reality brain
propagate reality to subjective brains (keep track of timesteps, created and updated, I think)
subjective brains update received reality
subjective brains check on turn events
subjective brains present (print state) and select filtered actions
reality brain resolves selected actions in sequence
update timestep
loop
"""

if __name__ == "__main__":

    game = Game()

    game.spawn_player()
    game.spawn_player()
    game.spawn_player()
    """
    for _ in range(2):
        game.create_entity(
            AIChooseMaker()
        )
    """

    print(f"starting graph size: {len(game.reality.graph.vertices)} vertices", flush=True)

    step_count = 0
    while len(game.entities) > 1:
        game.step()
        step_count += 1

    print(f"it took {step_count} steps for everyone to kill each other", flush=True)
    print(f"final graph size was: {len(game.reality.graph.vertices)} vertices", flush=True)

    """
    Start the world loop
    . world will repeatedly step the current room
    . understand when the room changes
    . steppng the room will
        . show the player their current brain
        . list their possible actions
        . store action chose
        . choose actions for NPCs
        . resolve all actions
    """
