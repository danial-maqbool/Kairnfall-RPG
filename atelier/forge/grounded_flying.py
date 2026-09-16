"""Articulated attack motion for Grounded-2026 birds and drakes.

The shared beast motion model produces lunge/crouch channels for attacks. The
bird rig uses wing charge and body bob channels, so this adapter maps the same
authoritative animation phase into a real downstroke/dive before pixels are
drawn. It never transforms or samples a completed sprite frame.
"""
from __future__ import annotations

from . import pigment
from .grounded_beasts import Stage, _motion, bird


def render_flying_attack(definition, state, number, direction, spec):
    size = 128 if definition.get('boss') else 64
    stage = Stage(size)
    motion = _motion(state, number)
    # Attack drive rises and falls over the eight-frame cycle. Translate it into
    # actual rig channels that bird() consumes: wing reach/lift and body dive.
    drive = min(1.0, abs(motion['lunge']) / 4.8)
    motion['charge'] = max(motion['charge'], drive)
    motion['bob'] -= motion['crouch'] * 0.8 + drive * 1.2
    bird(stage, spec, motion, direction)
    if definition.get('elite') or definition.get('boss'):
        tone = pigment.ramp(spec.glow or '#d4aa5a')
        stage.line([(-5, spec.height + 5), (0, spec.height + 8), (5, spec.height + 5)], tone[4], 1.4)
    return stage.image
