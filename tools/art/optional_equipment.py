"""Art-only descriptors for separately opted-in equipment.

These records give the sole Wayfarer actor generator a visible attachment. They
are never copied into the authoritative catalog or used to grant possessions,
stats, rewards or eligibility. Ordinary equipment definitions remain unchanged.
"""
from copy import deepcopy

_TUTORIAL_PICKAXE = {
    'id': 'classic_stone_pickaxe', 'slot': 'weapon', 'type': 'tool',
    'tags': ['pickaxe'], 'material': 'stone', 'handle_material': 'oak',
}


def optional_equipment():
    """Fresh descriptor copies prevent a drawer from changing shared source data."""
    return [deepcopy(_TUTORIAL_PICKAXE)]


def equipment_definitions(catalog):
    equipment = [deepcopy(item) for item in catalog['items'] if item.get('slot')]
    optional = optional_equipment()
    seen = set()
    for item in equipment + optional:
        if item['id'] in seen:
            raise ValueError('Duplicate equipped art identity: ' + item['id'])
        seen.add(item['id'])
    return equipment + optional
