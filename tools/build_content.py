#!/usr/bin/env python3
"""Build deterministic catalog files from the authored source modules."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_src import opening_journey, skills, items, abilities, mobs, encounter_variety, boss_uniques, world, dungeon_depth, profession_depth, exploration_rewards, quests, world_density, presentation, gear_progression, build_defining_loot


def build() -> dict:
    data={name:[] for name in ['skills','classes','items','abilities','recipes','zones','mobs','resources','npcs','quests']}
    for module in [skills,items,abilities,mobs,encounter_variety,boss_uniques,world,dungeon_depth,profession_depth,exploration_rewards,quests,world_density,presentation,gear_progression,build_defining_loot]: module.build(data)
    profession_depth.finalize_values(data)
    opening_journey.build(data)
    for category,entries in data.items():
        seen=set()
        for entry in entries:
            ident=entry['id']
            if not ident or ident in seen: raise ValueError(f'{category}: duplicate ID {ident}')
            seen.add(ident)
    names=set()
    for npc in data['npcs']:
        if npc['name'] in names: npc['name']+=' the '+npc['role'].replace('_',' ').title()
        if npc['name'] in names: npc['name']+=' of '+next(z['name'] for z in data['zones'] if z['id']==npc['zone'])
        names.add(npc['name'])
    return data


def main() -> None:
    data=build()
    payload=json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+'\n'
    for path in [ROOT/'content/catalog.json',ROOT/'client/Data/catalog.json']:
        path.parent.mkdir(parents=True,exist_ok=True); path.write_text(payload,encoding='utf-8')
    counts={key:len(value) for key,value in data.items()}
    counts['normal_species']=sum(not m['boss'] and not m['elite'] for m in data['mobs'])
    counts['elite_variants']=sum(m['elite'] for m in data['mobs'])
    counts['champion_elites']=sum(m['id'] in encounter_variety.CHAMPIONS for m in data['mobs'])
    counts['rare_elites']=counts['elite_variants']-counts['champion_elites']
    counts['bosses']=sum(m['boss'] for m in data['mobs'])
    counts['cities']=sum(z['kind']=='city' for z in data['zones'])
    counts['settlements']=sum(z['kind']=='settlement' for z in data['zones'])
    counts['dungeons']=sum(z['kind']=='dungeon' for z in data['zones'])
    counts['task21_compact_rooms']=sum(z['id'] in dungeon_depth.ROOM_IDS for z in data['zones'])
    counts['biomes']=len({z['biome'] for z in data['zones']})
    counts['profession_rare_resources']=len(profession_depth.RARE_RESOURCE_IDS)
    counts['profession_specialty_tools']=len(profession_depth.SPECIALTY_TOOL_IDS)
    counts['profession_specialty_recipes']=len(profession_depth.SPECIALTY_RECIPE_IDS)
    counts['surface_region_tiles']=sum(z['width']*z['height'] for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface')
    counts['catalog_sha256']=hashlib.sha256(payload.encode()).hexdigest()
    counts['status']='Catalog records generated. Counts alone do not establish gameplay or art completion.'
    (ROOT/'content/counts.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts,indent=2))

if __name__=='__main__': main()
