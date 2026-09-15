#!/usr/bin/env python3
"""Fail-closed structural acceptance for the Grounded-2026 actor migration.

This proves active coverage, dimensions, alpha/state/direction completeness and
that historical Atelier actor bytes did not re-enter runtime output. Motion is
checked only where a layer's shared joints actually move in that state: lower
body overlays need walk/attack/hit/death but need not change for a stationary
cast; anchored jewelry may keep its local shape. This does not claim artistic
approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'client'/'Assets'
ATELIER=ROOT/'atelier'/'Assets'
STATES=('idle','walk','attack','cast','hit','death')
DIRECTIONS=('south','west','east','north')
FRAMES=8
ACTOR_GROUPS={'people','equipment','npcs','mobs'}
UPPER_EQUIPMENT={'weapon','offhand','helmet','chest','gloves','cloak'}
LOWER_EQUIPMENT={'legs','boots'}


def need(value,message):
    if not value: raise RuntimeError(message)


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def frame(image,size,state,direction,number):
    row=STATES.index(state)*len(DIRECTIONS)+DIRECTIONS.index(direction)
    return image.crop((number*size,row*size,(number+1)*size,(row+1)*size))


def expected_keys(data):
    keys={f'people/body_{body}_{skin}' for body in range(2) for skin in range(6)}
    keys|={f'people/hair_{style}_{colour}' for style in range(6) for colour in range(8)}
    keys|={f'equipment/{item["id"]}' for item in data['items'] if item.get('slot')}
    keys|={f'npcs/{role}' for role in {npc['role'] for npc in data['npcs']}}
    keys|={f'mobs/{mob["id"]}' for mob in data['mobs']}
    return keys


def required_motion_states(key,slots):
    if key.startswith(('people/body_','people/hair_','npcs/','mobs/')):
        return ('walk','attack','cast','hit','death')
    if key.startswith('equipment/'):
        slot=slots.get(key,'')
        if slot in UPPER_EQUIPMENT: return ('walk','attack','cast','hit','death')
        if slot in LOWER_EQUIPMENT: return ('walk','attack','hit','death')
    return ()


def main():
    data=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
    runtime=json.loads((RUNTIME/'manifest.json').read_text(encoding='utf-8'))
    integration=json.loads((RUNTIME/'atelier-integration.json').read_text(encoding='utf-8'))
    historical=json.loads((ATELIER/'manifest.json').read_text(encoding='utf-8'))
    expected=expected_keys(data)
    entries={entry['key']:entry for entry in runtime['assets']}
    old={entry['key']:entry for entry in historical['assets']}
    slots={f'equipment/{item["id"]}':item.get('slot','') for item in data['items'] if item.get('slot')}
    need(integration.get('actor_runtime_source')=='Grounded-2026 procedural construction','Runtime actor source is not Grounded-2026.')
    need(integration.get('actor_historical_fallbacks')==0 and not integration.get('historical_actor_bytes_active',True),'Historical actor fallbacks are active.')
    copied={entry['key'] for entry in integration.get('assets',[]) if entry['key'].split('/')[0] in ACTOR_GROUPS}
    need(not copied,'Historical Atelier actor assets were copied into runtime: '+', '.join(sorted(copied)[:8]))
    missing=sorted(expected-set(entries)); need(not missing,'Missing active actor assets: '+', '.join(missing[:12]))
    extras={key for key in entries if key.split('/')[0] in ACTOR_GROUPS}-expected
    need(not extras,'Unexpected active actor assets: '+', '.join(sorted(extras)[:12]))
    replacement_count=0; checked_frames=0; state_motion_checks=0
    for key in sorted(expected):
        path=RUNTIME/(key+'.png'); need(path.is_file(),'Missing runtime actor PNG: '+key)
        entry=entries[key]; need(entry.get('animated') is True,'Actor is not marked animated: '+key)
        with Image.open(path) as image:
            need(image.mode=='RGBA','Actor is not RGBA: '+key)
            size=image.width//FRAMES
            need(image.width==size*FRAMES and image.height==size*len(STATES)*len(DIRECTIONS),'Actor grid mismatch: '+key)
            need(size in (64,128),'Unexpected actor frame size: '+key)
            for state in STATES:
                for direction in DIRECTIONS:
                    for number in range(FRAMES):
                        cell=frame(image,size,state,direction,number)
                        need(cell.getchannel('A').getbbox() is not None,f'Blank actor frame {key}/{state}/{direction}/{number}')
                        checked_frames+=1
            idle=frame(image,size,'idle','south',0)
            for state in required_motion_states(key,slots):
                direction='east' if state in {'attack','hit','death'} else 'north' if state=='cast' else 'south'
                number=7 if state=='death' else 3
                candidate=frame(image,size,state,direction,number)
                need(ImageChops.difference(idle,candidate).getbbox() is not None,f'{state.title()} repeats the standing frame: {key}')
                state_motion_checks+=1
            if 'death' in required_motion_states(key,slots):
                death=frame(image,size,'death','east',7)
                rotated=[idle.rotate(angle,expand=False) for angle in (90,180,270)]
                need(all(ImageChops.difference(candidate,death).getbbox() is not None for candidate in rotated),'Death is a rotated standing frame: '+key)
        need(digest(path)==entry['sha256'],'Runtime manifest hash mismatch: '+key)
        if key in old:
            need(entry['sha256']!=old[key]['sha256'],'Rejected historical actor artwork reappeared: '+key)
            replacement_count+=1
    people=(ROOT/'tools/art/people.py').read_text(encoding='utf-8')
    fauna=(ROOT/'tools/art/fauna.py').read_text(encoding='utf-8')
    need('grounded_people' in people and 'grounded_beasts' in fauna,'Active actor wrappers no longer name the Grounded-2026 sources.')
    need('base_frame' not in fauna and '_articulate_frame' not in fauna,'Legacy translated-frame creature fallback returned to the active wrapper.')
    print(f'GROUNDED_ACTOR_ACCEPTANCE: {len(expected)} active sheets; {checked_frames} state/direction frames; {state_motion_checks} anatomy-appropriate motion checks; {replacement_count} historical hashes replaced; actor fallbacks 0. Structural acceptance only; human artistic review remains separate.')


if __name__=='__main__': main()
