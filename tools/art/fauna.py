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
from atelier.forge.grounded_heavy import render_arachnid, render_bear
from atelier.forge.grounded_spirits import render_spirit
from atelier.forge.grounded_chelonians import render_chelonian


def frame(definition, state, number, direction):
    spec=anatomy.describe(definition)
    family=definition.get('family','')
    if family in {'bear','polar_bear'}:
        return render_bear(definition,state,number,direction,spec)
    if family in {'spider','quartz_spider'}:
        return render_arachnid(definition,state,number,direction,spec)
    if family in {'turtle','tortoise'}:
        return render_chelonian(definition,state,number,direction,spec)
    if spec.archetype in {'construct','mineral','mimic'}:
        return render_construct(definition,state,number,direction,spec)
    if spec.archetype in {'spirit','elemental'}:
        return render_spirit(definition,state,number,direction,spec)
    if spec.archetype in {'bird','drake'} and state=='attack':
        return render_flying_attack(definition,state,number,direction,spec)
    return render_frame(definition,state,number,direction,spec)
