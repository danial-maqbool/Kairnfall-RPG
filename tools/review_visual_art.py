#!/usr/bin/env python3
"""Render source contact sheets. These are inspection evidence, not gameplay screenshots or approval."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-root',type=Path,default=ROOT)
    parser.add_argument('--catalog',type=Path,default=ROOT/'content/catalog.json')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/experience/visual/after')
    args=parser.parse_args(); output=args.output.resolve()
    if not output.is_relative_to(ROOT/'artifacts'): raise SystemExit('Review output must remain under artifacts.')
    output.mkdir(parents=True,exist_ok=True)
    source=args.source_root.resolve(); sys.path.insert(0,str(source/'tools'))
    from art.people import body_frame,hair_frame,equipment_frame,npc_frame
    from art.items import icon
    from art.environment_pack import prop,building,PROPS
    if (source/'tools/art/fauna.py').exists():
        from art.fauna import frame as creature_frame
    else:
        from art.species_refinement import frame as creature_frame
    from art.common import STATES
    data=json.loads(args.catalog.read_text(encoding='utf-8'))
    records=[]
    coverage={'normal_mobs':0,'elites':0,'bosses':0,'mob_action_direction_frames':0,
        'individual_creature_sheets':0,'visible_equipment_slots':0,'equipment_action_direction_frames':0,
        'individual_equipment_sheets':0}
    direction_names=('S','W','E','N')
    def save(image,name):
        path=output/(name+'.png'); path.parent.mkdir(parents=True,exist_ok=True); image.save(path,optimize=True)
        records.append({'file':path.relative_to(output).as_posix(),'width':image.width,'height':image.height,
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    def contact(entries,name,columns=6,cell=(144,156),scale=2):
        image=Image.new('RGBA',(columns*cell[0],max(1,math.ceil(len(entries)/columns))*cell[1]),'#24262b'); draw=ImageDraw.Draw(image)
        for i,(label,tile) in enumerate(entries):
            tile=tile.resize((tile.width*scale,tile.height*scale),Image.Resampling.NEAREST)
            x=(i%columns)*cell[0]; y=(i//columns)*cell[1]
            image.alpha_composite(tile,(x+(cell[0]-tile.width)//2,y+4))
            draw.text((x+4,y+cell[1]-17),label[:22],fill='#e9dfc5')
        save(image,name)
    def order(direction):
        # The baseline intentionally uses the historical order for a fair before-state.
        if not (source/'tools/art/humanoid.py').exists():
            return ('cloak','body','legs','boots','chest','belt','hair','helmet','necklace','charm','trinket','gloves','offhand','weapon')
        from art.humanoid import layer_order
        return layer_order(direction,{})
    def person(body,state,n,direction,gear):
        result=Image.new('RGBA',(64,64))
        for slot in order(direction):
            if slot=='body': layer=body_frame(body,2,state,n,direction)
            elif slot=='hair': layer=hair_frame(0,1,state,n,direction)
            elif slot in gear: layer=equipment_frame(gear[slot],state,n,direction)
            else: continue
            result.alpha_composite(layer)
        return result
    def representative_frame(state):
        return {'idle':0,'walk':3,'attack':3,'cast':3,'hit':2,'death':7}.get(state,0)
    def mob_action_matrix(mobs,name):
        entries=[]
        for mob in mobs:
            creature_entries=[]
            for state in STATES:
                n=representative_frame(state)
                for direction in range(4):
                    tile=creature_frame(mob,state,n,direction)
                    short=f'{state} {direction_names[direction]}'
                    entries.append((f'{mob["id"]} {short}',tile))
                    creature_entries.append((short,tile))
            contact(creature_entries,f'creatures/{mob["id"]}',columns=4,cell=(112,92),scale=1)
            coverage['individual_creature_sheets']+=1
        contact(entries,name,columns=max(4,len(STATES)*4),cell=(72,84),scale=1)
        coverage['mob_action_direction_frames']+=len(entries)

    equipment=[item for item in data['items'] if item.get('slot')]
    visible_slots=[]
    for slot in order(0):
        if slot not in {'body','hair'} and slot not in visible_slots and any(item['slot']==slot for item in equipment): visible_slots.append(slot)
    basegear={slot:next(item for item in equipment if item['slot']==slot) for slot in visible_slots if slot not in {'weapon','offhand'}}
    coverage['visible_equipment_slots']=len(visible_slots)

    contact([(f'body {b} skin {skin}',body_frame(b,skin,'idle',0,0)) for b in range(2) for skin in range(6)],'player-bodies')
    contact([(f'body {b} {state} {direction_names[direction]}',body_frame(b,2,state,representative_frame(state),direction))
        for b in range(2) for state in STATES for direction in range(4)],'player-body-actions',columns=max(4,len(STATES)*4),cell=(72,84),scale=1)

    layer_entries=[]
    for slot in visible_slots:
        item=next(item for item in equipment if item['slot']==slot)
        gear=dict(basegear); gear[slot]=item
        if slot!='weapon':
            weapon=next((candidate for candidate in equipment if candidate['slot']=='weapon' and 'sword' in candidate.get('tags',[])),None)
            if weapon is not None: gear['weapon']=weapon
        if slot!='offhand':
            shield=next((candidate for candidate in equipment if candidate['slot']=='offhand' and 'shield' in candidate.get('tags',[])),None)
            if shield is not None: gear['offhand']=shield
        slot_entries=[]
        for state in STATES:
            n=representative_frame(state)
            for direction in range(4):
                tile=person(0,state,n,direction,gear)
                short=f'{state} {direction_names[direction]}'
                layer_entries.append((f'{slot} {short}',tile))
                slot_entries.append((short,tile))
        contact(slot_entries,f'equipment-layers/{slot}',columns=4,cell=(112,92),scale=1)
        coverage['individual_equipment_sheets']+=1
    coverage['equipment_action_direction_frames']=len(layer_entries)
    contact(layer_entries,'equipment-all-layers',columns=max(4,len(STATES)*4),cell=(72,84),scale=1)

    for family in ('sword','axe','bow','staff','spear'):
        item=next(item for item in equipment if item['slot']=='weapon' and family in item.get('tags',[]))
        gear=dict(basegear,weapon=item)
        if family in ('sword','axe'): gear['offhand']=next(item for item in equipment if item['slot']=='offhand' and 'shield' in item.get('tags',[]))
        entries=[]
        for state in STATES:
            for d in range(4):
                for n in range(8): entries.append((f'{state} {direction_names[d]} / {n}',person(0,state,n,d,gear)))
        contact(entries,'equipment-'+family,columns=8,cell=(136,151))

    normal=[m for m in data['mobs'] if not m['boss'] and not m.get('elite')]
    elites=[m for m in data['mobs'] if m.get('elite')]
    bosses=[m for m in data['mobs'] if m['boss']]
    coverage['normal_mobs']=len(normal); coverage['elites']=len(elites); coverage['bosses']=len(bosses)
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in normal],'normal-mobs',columns=8)
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in elites],'elites')
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in bosses],'bosses',columns=5,cell=(160,158),scale=1)
    mob_action_matrix(normal,'normal-mob-actions')
    mob_action_matrix(elites,'elite-actions')
    mob_action_matrix(bosses,'boss-actions')

    for ident in ('field_rat','wild_hare','pine_wolf','polar_bear','sea_turtle','wood_spider'):
        mob=next(m for m in data['mobs'] if m['id']==ident)
        contact([(f'{state} {direction_names[d]} / {n}',creature_frame(mob,state,n,d)) for state in STATES for d in range(4) for n in range(8)],'animation-'+ident,8,(136,151))
    contact([(item['name'],icon(item)) for item in data['items']],'item-icons',columns=10,cell=(104,96),scale=2)
    contact([(role,npc_frame(role,'idle',0,0)) for role in sorted({npc['role'] for npc in data['npcs']})],'npc-roles')
    contact([(name,prop(name)) for name in PROPS],'environment',columns=5,cell=(168,166),scale=1)
    for zone in data['zones']:
        if zone['id']!='wayfarers_rest': continue
        for value in zone['buildings']: save(building(zone,value),'building-'+value['id'])
    lookup={item['id']:item for item in data['items']}
    for tier in data.get('equipmentTiers',[]):
        contact([(lookup[ident]['name'],icon(lookup[ident])) for ident in tier['entries'].values()],f'equipment-tier-{tier["level"]:03d}',columns=8,cell=(144,104))
        if tier['level'] in (5,27,55,75,100):
            gear={slot:lookup[tier['entries']['armor/heavy/'+slot]] for slot in ('helmet','chest','legs','boots','cloak','gloves','belt')}
            entries=[]
            for family,ident in tier['entries'].items():
                if not family.startswith('weapon/'): continue
                gear['weapon']=lookup[ident]
                for direction in range(4):
                    for state,number in (('idle',0),('walk',3),('attack',3),('cast',3),('hit',2),('death',7)):
                        entries.append((family.split('/')[-1]+' '+state+' '+direction_names[direction],person(0,state,number,direction,gear)))
            contact(entries,f'equipment-grade-{tier["level"]:03d}',columns=12,cell=(100,92),scale=1)
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    (output/'review-manifest.json').write_text(json.dumps({'source_revision':revision,'evidence_kind':'source-rendered contact sheets; not gameplay','visual_approval':'not_reviewed','coverage':coverage,'files':records},indent=2)+'\n',encoding='utf-8')
    print(f'VISUAL_REVIEW: {len(records)} source contact sheets; {coverage["normal_mobs"]} normal mobs, {coverage["elites"]} elites and {coverage["bosses"]} bosses covered across actions/directions; {coverage["individual_creature_sheets"]} readable creature sheets; {coverage["visible_equipment_slots"]} visible equipment slots and {coverage["individual_equipment_sheets"]} readable layer sheets covered; visual approval not inferred.')


if __name__=='__main__': main()
