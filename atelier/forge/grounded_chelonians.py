"""Grounded-2026 chelonian action renderer.

Turtles and tortoises retain the shared newly-authored quadruped anatomy while
making head-on and rear attack/recoil silhouettes directionally distinct.  The
base quadruped renderer already expresses signed lunge in side views; front and
rear views project that depth movement onto the screen while retaining planted
feet, so action frames change real geometry rather than relying on hit flash.
"""
from __future__ import annotations

from PIL import Image

from . import pigment
from .grounded_beasts import Stage, _motion, quadruped


def render_chelonian(definition, state, number, direction, spec):
    size = 128 if definition.get('boss') else 64
    stage = Stage(size)
    motion = _motion(state, number)

    # South-facing actions move toward the camera (down-screen) while north-
    # facing actions move away (up-screen); recoil reverses those directions.
    # A larger recoil projection is deliberate: the shared hit crouch partially
    # cancels the depth offset, and sub-pixel projection used to quantize frame 3
    # back onto the exact idle alpha silhouette at native 64 px resolution.
    if direction in (0, 3) and state in ('attack', 'hit'):
        motion = dict(motion)
        depth_sign = -1.0 if direction == 0 else 1.0
        depth_scale = 0.55 if state == 'attack' else 0.72
        motion['bob'] += depth_sign * motion['lunge'] * depth_scale

    quadruped(stage, spec, motion, direction)

    if definition.get('elite') or definition.get('boss'):
        tone = pigment.ramp(spec.glow or '#d4aa5a')
        stage.line([(-5, spec.height + 5), (0, spec.height + 8), (5, spec.height + 5)], tone[4], 1.4)
    if motion['flash']:
        overlay = Image.new('RGBA', stage.image.size, (255, 234, 210, 0))
        overlay.putalpha(stage.image.getchannel('A').point(lambda a: round(a * motion['flash'] * .45)))
        stage.image = Image.alpha_composite(stage.image, overlay)
    if motion['fade'] < 1:
        stage.image.putalpha(stage.image.getchannel('A').point(lambda a: round(a * motion['fade'])))
    return stage.image
