"""Authored action offsets for small creatures, in logical sprite pixels.

Only joints and appendages move. The frame canvas, ground anchor, shell and
body orientation remain fixed. These offsets do not change server combat.
"""
from dataclasses import dataclass

STATES = ('idle', 'walk', 'attack', 'cast', 'hit', 'death')


@dataclass(frozen=True)
class ActionPose:
    advance: int = 0
    foreleg: int = 0
    fang: int = 0
    neck: int = 0
    tuck: float = 0.0


def pose(family: str, state: str, frame: int) -> ActionPose:
    if state not in STATES or not isinstance(frame, int) or not 0 <= frame < 8:
        raise ValueError('Expected a known action and frame 0 through 7')
    if family in ('spider', 'quartz_spider'):
        if state == 'attack':
            # Set the front legs, withdraw, strike with fangs, then recover.
            return ActionPose(
                advance=(0, -1, -2, 3, 2, 1, 0, 0)[frame],
                foreleg=(0, -2, -3, 3, 2, 1, 0, 0)[frame],
                fang=(0, -1, -2, 3, 2, 0, 0, 0)[frame])
        if state == 'hit':
            return ActionPose(
                advance=(0, -2, -3, -2, -1, 0, 0, 0)[frame],
                foreleg=(0, -2, -2, -1, 0, 0, 0, 0)[frame])
    elif family in ('turtle', 'tortoise'):
        if state == 'attack':
            # The shell stays planted while the neck withdraws and extends.
            return ActionPose(neck=(0, -2, -3, 3, 2, 1, 0, 0)[frame],
                              tuck=(0, .10, .18, 0, 0, .08, 0, 0)[frame])
        if state == 'hit':
            return ActionPose(neck=(0, -3, -5, -4, -3, -2, -1, 0)[frame],
                              tuck=(0, .25, .40, .35, .25, .15, .05, 0)[frame])
    return ActionPose()
