#!/usr/bin/env python3
"""Patch the staged Ultimate mapper so known normal-species silhouette collisions use distinct masters.

The source bundle is materialized during CI before the final source files are committed.
This temporary bootstrap patch reserves dedicated authored mob variants for the species
that the game validator previously found to have identical alpha silhouettes.
"""
from pathlib import Path

TARGET = Path('tools/integrate_ultimate_pack.py')
text = TARGET.read_text(encoding='utf-8')

anchor = "MOB_TEMPLATES = ['slime','wolf','boar','goblin','skeleton','zombie','spider','bat','rat','snake','elemental','mushroom','imp','golem','troll','ogre']\n"
insert = anchor + "NORMAL_SPECIES_SOURCE_OVERRIDES = {\n    'field_rat':'rat_0',\n    'pirate_cutthroat':'goblin_0',\n    'fungal_hermit':'mushroom_0',\n    'lantern_fungus':'mushroom_1',\n    'hay_golem':'golem_0',\n    'obsidian_golem':'golem_1',\n    'prism_golem':'golem_2',\n    'quartz_spider':'spider_0',\n    'wood_spider':'spider_1',\n}\n"
if 'NORMAL_SPECIES_SOURCE_OVERRIDES' not in text:
    if anchor not in text:
        raise SystemExit('Ultimate mapper template anchor changed')
    text = text.replace(anchor, insert, 1)

old_used = "    overrides=[]; skipped=[]; groups=Counter(); used_mob_sources=set()\n"
new_used = "    overrides=[]; skipped=[]; groups=Counter()\n    used_mob_sources={source/'actors/mobs'/f'{name}.png' for name in NORMAL_SPECIES_SOURCE_OVERRIDES.values()}\n"
if old_used in text:
    text = text.replace(old_used, new_used, 1)
elif new_used not in text:
    raise SystemExit('Ultimate mapper used_mob_sources anchor changed')

old_branch = """            if bool(mob.get('boss')):\n                chosen=_boss_name(text)\n                if chosen:\n                    src=source/'actors/bosses'/f'{chosen}.png'\n                    if src not in used_mob_sources: used_mob_sources.add(src); override(key,src,128)\n            else:\n                chosen=_mob_template(text)\n                if chosen:\n                    # Prefer three authored variants; never duplicate an exact sheet across normal species.\n                    start=_hash_int(ident)%3; src=None\n                    for offset in range(3):\n                        candidate=source/'actors/mobs'/f'{chosen}_{(start+offset)%3}.png'\n                        if candidate not in used_mob_sources: src=candidate; break\n                    if src is not None: used_mob_sources.add(src); override(key,src,64)\n"""
new_branch = """            if bool(mob.get('boss')):\n                chosen=_boss_name(text)\n                if chosen:\n                    src=source/'actors/bosses'/f'{chosen}.png'\n                    if src not in used_mob_sources: used_mob_sources.add(src); override(key,src,128)\n            elif ident in NORMAL_SPECIES_SOURCE_OVERRIDES:\n                override(key,source/'actors/mobs'/f'{NORMAL_SPECIES_SOURCE_OVERRIDES[ident]}.png',64)\n            else:\n                chosen=_mob_template(text)\n                if chosen:\n                    # Prefer three authored variants; never duplicate an exact sheet across normal species.\n                    start=_hash_int(ident)%3; src=None\n                    for offset in range(3):\n                        candidate=source/'actors/mobs'/f'{chosen}_{(start+offset)%3}.png'\n                        if candidate not in used_mob_sources: src=candidate; break\n                    if src is not None: used_mob_sources.add(src); override(key,src,64)\n"""
if old_branch in text:
    text = text.replace(old_branch, new_branch, 1)
elif new_branch not in text:
    raise SystemExit('Ultimate mapper mob branch anchor changed')

TARGET.write_text(text, encoding='utf-8')
print('Patched Ultimate normal-species source allocation.')
