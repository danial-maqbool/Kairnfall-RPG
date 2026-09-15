"""Active Grounded-2026 creature renderer entry point.

Every mob frame is newly constructed from catalogue anatomy and motion data.
No standing frame is translated, stretched, rotated, or sampled from the legacy
fauna renderer. The public SUPPORTED inventory remains available to validators.
"""
from __future__ import annotations
from .fauna_base import SUPPORTED
from atelier.forge import beasts as anatomy
from atelier.forge.grounded_beasts import render_frame


def frame(definition, state, number, direction):
    return render_frame(definition, state, number, direction, anatomy.describe(definition))
