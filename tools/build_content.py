#!/usr/bin/env python3
"""Build deterministic catalog files from the authored source modules."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from content_src import skills, items, abilities, mobs, world, quests, presentation, gear_progression


def build() -> dict:
    data={name:[] for name in ['skills','classes','items','abilities','recipes','zones','mobs','resources','npcs','quests']}
    for module in [skills,items,abilities,mobs,world,quests,presentation,gear_progression]: module.build(data)
    for category,entries in data.items():
        seen=set()
        for entry in entries:
            ident=entry['id']
            if not ident or ident in seen: raise ValueError(f'{category}: duplicate ID {ident}')
            seen.add(ident)
    # Names are identities, not anonymous NPC numbers.
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
    counts['bosses']=sum(m['boss'] for m in data['mobs'])
    counts['cities']=sum(z['kind']=='city' for z in data['zones'])
    counts['settlements']=sum(z['kind']=='settlement' for z in data['zones'])
    counts['dungeons']=sum(z['kind']=='dungeon' for z in data['zones'])
    counts['biomes']=len({z['biome'] for z in data['zones']})
    counts['surface_region_tiles']=sum(z['width']*z['height'] for z in data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface')
    counts['catalog_sha256']=hashlib.sha256(payload.encode()).hexdigest()
    counts['status']='Catalog records generated. Counts alone do not establish gameplay or art completion.'
    (ROOT/'content/counts.json').write_text(json.dumps(counts,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(counts,indent=2))

if __name__=='__main__': main()
