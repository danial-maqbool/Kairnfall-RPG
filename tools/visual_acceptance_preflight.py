#!/usr/bin/env python3
"""Exhaustive structural visual acceptance for Kairnfall actor art.

This checks generated pixels and rig contracts. It does not grant artistic approval.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from art.common import STATES
from art.people import SKINS,HAIRS,body_frame,hair_frame,equipment_frame
from art.fauna import frame as creature_frame

CATALOG=ROOT/'content/catalog.json'
KEY_FRAME={'idle':0,'walk':3,'attack':4,'cast':4,'hit':1,'death':7}


def digest(image): return hashlib.sha256(image.tobytes()).hexdigest()


def check_frame(image,size,label):
    if image.size!=(size,size): raise ValueError(f'{label}: expected {size}x{size}, got {image.size}')
    box=image.getchannel('A').getbbox()
    if box is None: raise ValueError(label+': empty alpha mask')
    if min(box)<0 or box[2]>size or box[3]>size: raise ValueError(label+': pixels exceed frame bounds')
    return box


def main():
    data=json.loads(CATALOG.read_text(encoding='utf-8'))
    actor_frames=equipment_frames=creature_frames=deterministic=0

    for body in range(2):
        for skin in range(len(SKINS)):
            per_direction=[]
            for state in STATES:
                for direction in range(4):
                    hashes=[]
                    for number in range(8):
                        image=body_frame(body,skin,state,number,direction)
                        check_frame(image,64,f'body {body}/{skin}/{state}/{direction}/{number}')
                        hashes.append(digest(image)); actor_frames+=1
                    if state in {'walk','attack','cast','death'} and len(set(hashes))<2:
                        raise ValueError(f'body {body}/{skin}/{state}/{direction}: animation has no visible phase change')
                    per_direction.extend(hashes)
            if len(set(per_direction))<8: raise ValueError(f'body {body}/{skin}: insufficient directional/action variation')

    for style in range(6):
        for colour in range(len(HAIRS)):
            for state in STATES:
                for direction in range(4):
                    for number in range(8):
                        image=hair_frame(style,colour,state,number,direction)
                        check_frame(image,64,f'hair {style}/{colour}/{state}/{direction}/{number}')
                        actor_frames+=1

    equipped=[item for item in data['items'] if item.get('slot')]
    slots={item['slot'] for item in equipped}
    expected={'weapon','offhand','helmet','chest','legs','boots','gloves','belt','cloak','necklace','ring','charm','trinket'}
    missing=expected-slots
    if missing: raise ValueError('Missing equipped visual slots: '+', '.join(sorted(missing)))
    for item in equipped:
        first=None
        for state in STATES:
            number=KEY_FRAME[state]
            for direction in range(4):
                image=equipment_frame(item,state,number,direction)
                check_frame(image,64,f"equipment {item['id']}/{state}/{direction}/{number}")
                equipment_frames+=1
                if first is None: first=digest(image)
        again=digest(equipment_frame(item,'idle',0,0))
        if first!=again: raise ValueError(item['id']+': equipment renderer is not deterministic')
        deterministic+=1

    normal=elite=boss=0
    for mob in data['mobs']:
        size=128 if mob.get('boss') else 64
        if mob.get('boss'): boss+=1
        elif mob.get('elite'): elite+=1
        else: normal+=1
        action_hashes=set()
        for state in STATES:
            for direction in range(4):
                hashes=[]
                for number in range(8):
                    image=creature_frame(mob,state,number,direction)
                    check_frame(image,size,f"mob {mob['id']}/{state}/{direction}/{number}")
                    value=digest(image); hashes.append(value); action_hashes.add(value); creature_frames+=1
                if state in {'walk','attack','hit','death'} and len(set(hashes))<2:
                    raise ValueError(f"{mob['id']}/{state}/{direction}: animation has no visible phase change")
        if len(action_hashes)<8: raise ValueError(mob['id']+': insufficient action/direction variation')
        if digest(creature_frame(mob,'attack',4,2))!=digest(creature_frame(mob,'attack',4,2)):
            raise ValueError(mob['id']+': creature renderer is not deterministic')
        deterministic+=1

    coverage=json.loads((ROOT/'atelier/coverage.json').read_text(encoding='utf-8'))
    if coverage.get('artistic_review')!='pending': raise ValueError('Automated visual acceptance must not grant artistic approval')
    if normal+elite+boss!=len(data['mobs']): raise ValueError('Creature classification coverage mismatch')
    report={'humanoid_frames_checked':actor_frames,'equipment_items_checked':len(equipped),
        'equipment_key_frames_checked':equipment_frames,'creature_frames_checked':creature_frames,
        'normal_creatures':normal,'elite_creatures':elite,'bosses':boss,'determinism_pairs':deterministic,
        'states':list(STATES),'directions':4,'frames_per_cycle':8,'artistic_review':'pending'}
    target=ROOT/'artifacts/visual-acceptance/structural-report.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('VISUAL_ACCEPTANCE_PREFLIGHT:',json.dumps(report,sort_keys=True))
    print('VISUAL_ACCEPTANCE_PREFLIGHT: structural and deterministic checks passed; independent artwork approval remains pending.')

if __name__=='__main__': main()
