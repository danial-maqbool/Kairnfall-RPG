"""Active Grounded-2026 creature renderer entry point.

Every mob frame is newly constructed from catalogue anatomy and motion data.
No standing frame is translated, stretched, rotated, or sampled from the legacy
fauna renderer. The public SUPPORTED inventory remains available to validators.
"""
from __future__ import annotations
from .fauna_base import SUPPORTED
from atelier.forge import beasts as anatomy
from atelier.forge.grounded_beasts import render_frame
from atelier.forge.grounded_constructs import render_construct
from atelier.forge.grounded_flying import render_flying_attack
from atelier.forge.grounded_spirits import render_spirit


def frame(definition, state, number, direction):
    spec=anatomy.describe(definition)
    if spec.archetype in {'construct','mineral','mimic'}:
        return render_construct(definition,state,number,direction,spec)
    if spec.archetype in {'spirit','elemental'}:
        return render_spirit(definition,state,number,direction,spec)
    if spec.archetype in {'bird','drake'} and state=='attack':
        return render_flying_attack(definition,state,number,direction,spec)
    return render_frame(definition,state,number,direction,spec)
