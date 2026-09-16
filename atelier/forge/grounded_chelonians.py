"""Grounded-2026 chelonian action renderer.

Turtles and tortoises retain the shared newly-authored quadruped anatomy while
making head-on and rear attack/recoil silhouettes directionally distinct.  The
base quadruped renderer already expresses signed lunge in side views; front and
rear views need a depth cue because screen-space X cannot represent movement
toward or away from the camera.
"""
from __future__ import annotations

from PIL import Image

from . import pigment
from .grounded_beasts import Stage, _motion, quadruped


def render_chelonian(definition, state, number, direction, spec):
    size = 128 if definition.get('boss') else 64
    stage = Stage(size)
    motion = _motion(state, number)

    # Preserve the common anatomy and timing contract.  For south/north views,
    # turn signed attack/recoil travel into vertical depth motion: attacks drive
    # the shell/head toward the camera while hits recoil it away.  This changes
    # actual geometry rather than relying on the transient hit flash.
    if direction in (0, 3) and state in ('attack', 'hit'):
        motion = dict(motion)
        motion['bob'] -= motion['lunge'] * .18

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
