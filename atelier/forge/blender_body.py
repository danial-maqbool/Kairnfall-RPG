"""Load Blender-authored humanoid base sheets into the shared Atelier API.

The authored sheets are the source of truth for the twelve base bodies. If they
are absent in a development checkout, the previous refined procedural renderer
remains available as a deterministic fallback.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image

from . import refined_body, rig

ROOT = Path(__file__).resolve().parents[1]
AUTHORED = ROOT / "authored" / "humanoid"
FRAME = 64


@lru_cache(maxsize=12)
def _sheet(build: int, skin: int):
    path = AUTHORED / f"body_{build}_{skin}.png"
    if not path.exists():
        return None
    with Image.open(path) as image:
        loaded = image.convert("RGBA").copy()
    if loaded.size != (512, 1536):
        raise ValueError(f"Authored humanoid sheet has invalid size: {path} {loaded.size}")
    return loaded


def body_frame(build, skin, state, frame, direction):
    build_index = build if isinstance(build, int) else rig.BUILDS.index(build)
    skin_index = max(0, min(5, int(skin)))
    sheet = _sheet(build_index, skin_index)
    if sheet is None:
        return refined_body.body_frame(build_index, skin_index, state, frame, direction)
    state_index = rig.STATES.index(state)
    frame = max(0, min(rig.FRAMES - 1, int(frame)))
    direction = max(0, min(3, int(direction)))
    x = frame * FRAME
    y = (state_index * 4 + direction) * FRAME
    return sheet.crop((x, y, x + FRAME, y + FRAME))
