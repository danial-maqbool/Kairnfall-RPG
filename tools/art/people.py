"""Active Grounded-2026 humanoid renderer compatibility entry point.

The runtime keeps the established 64 px sheet contract and catalog identities,
but all body, hair, worn-equipment and NPC pixels are newly constructed from
the shared articulated rig in atelier/forge/grounded_people.py. Legacy humanoid
renderers remain historical source only and are not sampled by this path.
"""
from .humanoid import SKINS, HAIRS, ROLE_COLORS, rig, clothing_base, layer_order
from atelier.forge.grounded_people import body_frame, hair_frame, armour_frame, npc_frame


def equipment_frame(item, state, frame, direction, cached_icon=None):
    # cached_icon is retained only for compatibility with existing callers.
    return armour_frame(item, state, frame, direction)
