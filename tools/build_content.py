#!/usr/bin/env python3
"""Build deterministic catalog files. Catalog coverage is not gameplay acceptance."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from content_rules import build_rules
from content_items import build_items
from content_world import make_mobs, build_world
from content_quests import build_quests

ROOT=Path(__file__).resolve().parents[1]


def validate(data: dict) -> None:
    groups={key:{row['id']:row for row in rows} for key,rows in data.items()}
    for key,rows in data.items():
        if len(rows)!=len(groups[key]):
            raise ValueError('Duplicate IDs in '+key)
    for cls in data['classes']:
        assert cls['weapon'] in groups['items'] and cls['armor'] in groups['items'], cls['id']
        assert all(a in groups['abilities'] for a in cls['abilities']), cls['id']
    for zone in data['zones']:
        assert all(m in groups['mobs'] for m in zone['species']), zone['id']
        assert all(r in groups['resources'] for r in zone['resources']), zone['id']
        assert not zone['boss'] or zone['boss'] in groups['mobs'], zone['id']
        for exit in zone['exits']:
            assert exit['target'] in groups['zones'], exit['id']
            destination=groups['zones'][exit['target']]
            assert any(e['target']==zone['id'] for e in destination['exits']), exit['id']
    for quest in data['quests']:
        assert quest['giver'] in groups['npcs'], quest['id']
        assert not quest['reward'] or quest['reward'] in groups['items'], quest['id']
        assert not quest['prerequisite'] or quest['prerequisite'] in groups['quests'], quest['id']
        for objective in quest['objectives']:
            action,target=objective['action'],objective['target']
            bucket={'kill':'mobs','explore':'zones','talk':'npcs','cast':'abilities',
                    'gather':'items','deliver':'items','craft':'items','buy':'items','consume':'items','loot':'items'}.get(action)
            assert target=='*' or bucket is None or target in groups[bucket], (quest['id'],action,target)
            assert objective['count']>0
    reachable={'wayfarers_rest'}
    pending=list(reachable)
    while pending:
        current=pending.pop()
        for edge in groups['zones'][current]['exits']:
            if edge['target'] not in reachable:
                reachable.add(edge['target']); pending.append(edge['target'])
    assert len(reachable)==len(data['zones']), 'Disconnected zones: '+str(set(groups['zones'])-reachable)


def main() -> None:
    skills,classes,abilities=build_rules()
    items,recipes,resources=build_items()
    mobs=make_mobs(items)
    zones,npcs=build_world(mobs,resources,items)
    quests=build_quests(zones,npcs,classes)
    data=dict(skills=skills,classes=classes,items=items,abilities=abilities,recipes=recipes,
              resources=resources,mobs=mobs,zones=zones,npcs=npcs,quests=quests)
    validate(data)
    encoded=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
    for relative in ('content/catalog.json','client/Data/catalog.json'):
        target=ROOT/relative; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(encoded,encoding='utf-8')
    for key,rows in data.items():
        target=ROOT/'content'/key/'catalog.json'; target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(rows,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    summary={key:len(rows) for key,rows in data.items()}
    summary.update(normal_species=sum(not m.get('boss') and not m.get('elite') for m in mobs),
                   elites=sum(bool(m.get('elite')) for m in mobs),bosses=sum(bool(m.get('boss')) for m in mobs),
                   cities=sum(z['kind']=='city' for z in zones),settlements=sum(z['kind']=='settlement' for z in zones),
                   dungeons=sum(z['kind']=='dungeon' for z in zones),biomes=len({z['biome'] for z in zones}),
                   surface_tiles=sum(z['width']*z['height'] for z in zones if z['layer']=='Surface' and z['kind']!='interior'),
                   sha256=hashlib.sha256(encoded.encode()).hexdigest(),
                   acceptance='Catalog references validated. Runtime, art, balance, and release gates are separate.')
    (ROOT/'content/coverage.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
