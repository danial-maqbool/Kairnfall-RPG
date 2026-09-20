#!/usr/bin/env python3
"""Complete catalog skill references using existing object and ability artwork."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from art.items import icon as item_icon
from art.common import save
from build_game_assets import ability_icon

OBJECTS = {
    'evasion': 'linen_light_boots', 'endurance': 'healing_potion',
    'meditation': 'mana_potion', 'hunting': 'copper_bow', 'slayer': 'copper_sword',
    'survival': 'bread', 'exploration': 'treasure_map_1',
    'mining': 'copper_pickaxe', 'woodcutting': 'woodcutters_axe',
    'fishing': 'field_rod', 'farming': 'wheat_seed', 'foraging': 'wild_berry',
    'herbalism': 'sickle', 'skinning': 'skinning_knife', 'excavation': 'shovel',
    'prospecting': 'rough_gem', 'treasure_hunting': 'treasure_map_1',
    'smithing': 'crafting_hammer', 'woodworking': 'oak_plank',
    'fletching': 'arrow_bundle', 'tailoring': 'thread',
    'leatherworking': 'cured_leather', 'cooking': 'bread', 'alchemy': 'healing_potion',
    'enchanting': 'enchanted_thread', 'runecrafting': 'rune_embers_1',
    'jewelcrafting': 'copper_ring', 'carpentry': 'structure_workbench',
    'scribing': 'lore_book_1', 'tinkering': 'crafting_hammer',
    'lockpicking': 'lockpick', 'bartering': 'copper_ring',
    'cartography': 'treasure_map_1', 'animal_handling': 'animal_bait',
    'construction': 'structure_campfire'
}


def select_source(skill: dict, catalog: dict) -> tuple[str, dict]:
    ident = skill['id']
    items = {item['id']: item for item in catalog['items']}
    if ident in OBJECTS:
        target = OBJECTS[ident]
        if target not in items:
            raise ValueError(f'Skill {ident} refers to an absent icon source: {target}')
        return 'item', items[target]
    if skill['category'] == 'Magic':
        candidates = [a for a in catalog['abilities'] if a.get('skill') == ident]
        if candidates:
            return 'ability', sorted(candidates, key=lambda a: (a.get('requirement', 1), a['id']))[0]
    candidates = [item for item in catalog['items'] if item.get('skill') == ident
                  and item.get('type') in {'weapon', 'offhand', 'armor'}]
    if candidates:
        return 'item', sorted(candidates, key=lambda i: (i.get('requirement', 1), i['id']))[0]
    raise ValueError(f'No object or ability icon is defined for skill {ident}.')


def main() -> None:
    assets = ROOT / 'client/Assets'
    catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
    manifest_path = assets / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    entries = [entry for entry in manifest['assets'] if not entry['key'].startswith('skills/')]
    sources = []
    for skill in catalog['skills']:
        kind, source = select_source(skill, catalog)
        image = ability_icon(source) if kind == 'ability' else item_icon(source)
        if image.mode != 'RGBA' or image.size != (32, 32) or image.getchannel('A').getbbox() is None:
            raise ValueError('Invalid skill icon: ' + skill['id'])
        key = 'skills/' + skill['id']
        path = assets / (key + '.png')
        save(image, path)
        entries.append({'key': key, 'width': 32, 'height': 32,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'animated': False})
        sources.append({'skill': skill['id'], 'source_kind': kind, 'source_id': source['id']})
    manifest['assets'] = sorted(entries, key=lambda entry: entry['key'])
    manifest['skill_icon_sources'] = sources
    temporary = manifest_path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    temporary.replace(manifest_path)
    report = ROOT / 'artifacts/asset-coverage.json'
    data = json.loads(report.read_text(encoding='utf-8')) if report.is_file() else {}
    data.update(png_files=len(entries), skill_icons=len(sources), artistic_review='not_approved')
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    print(f'SKILL_ICONS: {len(sources)} catalog references generated and recorded. Visual review remains required.')


if __name__ == '__main__':
    main()
