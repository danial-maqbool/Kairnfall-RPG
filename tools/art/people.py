"""Compatibility entry point for the shared articulated humanoid renderer.

The asset builder and existing callers retain their original import paths.
The 64px frame contract and catalog item identities are unchanged.
"""
from .humanoid import (
    SKINS, HAIRS, ROLE_COLORS, rig, body_frame, hair_frame,
    clothing_base, equipment_frame, npc_frame, layer_order,
)
