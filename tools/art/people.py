"""Active Grounded-2026 humanoid renderer compatibility entry point.

The tools/art package is also imported by review scripts executed from the
`tools/` directory. Bootstrap the repository root before importing Atelier so
those scripts use the same authored Grounded source as module-based test runs.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .humanoid import SKINS, HAIRS, ROLE_COLORS, rig, clothing_base, layer_order
from atelier.forge.grounded_people import body_frame, hair_frame, armour_frame, npc_frame


def equipment_frame(item,state,frame,direction,body=0):
    # Grounded-2026 equipment rendering is body-agnostic. Keep the historical
    # compatibility parameter in this wrapper because callers still pass it,
    # but do not forward it into the new renderer.
    return armour_frame(item,state,frame,direction)
