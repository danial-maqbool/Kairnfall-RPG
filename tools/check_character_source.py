#!/usr/bin/env python3
"""Fast source-level actor checks before atlas generation. Not artistic acceptance.

Exercises every rig frame and representative material/weapon construction plus
all NPC roles and creature definitions. Full generated-atlas checks remain separate.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import sys
from PIL import ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from art.character_motion import STATES,EXTRA_STATES,rig
from art.characters import body_frame,hair_frame,armour_frame,npc_frame,_weapon_kind
from art.wildlife import frame as creature_frame


def main():
    data=json.loads((ROOT/'content/catalog.json').read_text())
    errors=[];error_count=0;checks=0;frames=0
    def need(condition,message):
        nonlocal checks,error_count
        checks+=1
        if not condition:
            error_count+=1
            if len(errors)<200:errors.append(message)
    for state in STATES+EXTRA_STATES:
        for body in range(2):
            for direction in range(4):
                for number in range(8):
                    try:
                        joints=rig(state,number,direction,body)
                        need(joints['sign'] in (-1,1),f'Invalid direction sign: {state}/{direction}/{number}')
                        for key,value in joints.items():
                            if isinstance(value,tuple):need(len(value)==2 and all(isinstance(n,(int,float)) and math.isfinite(n) for n in value),f'Invalid joint: {state}/{direction}/{number}/{key}')
                        if state=='walk':need(joints['foot_l'][1]==55 or joints['foot_r'][1]==55,'No planted walking foot')
                    except Exception as error:need(False,f'Rig exception {state}/{body}/{direction}/{number}: {type(error).__name__}: {error}')
    def verify(label,draw,states,required,size=64):
        nonlocal frames
        for direction in range(4):
            try:idle=draw('idle',0,direction)
            except Exception as error:need(False,label+'/idle: '+repr(error));continue
            for state in states:
                maximum=0
                for number in (0,2,3,4,7):
                    try:
                        image=draw(state,number,direction);frames+=1
                        box=image.getchannel('A').getbbox()
                        need(image.mode=='RGBA' and image.size==(size,size),f'Invalid canvas {label}/{state}/{direction}/{number}')
                        need(box is not None,f'Empty {label}/{state}/{direction}/{number}')
                        if box:need(box[0]>0 and box[1]>0 and box[2]<size and box[3]<size,f'Clipped {label}/{state}/{direction}/{number}: {box}')
                        if state in required:
                            changed=sum(any(channel for channel in pixel) for pixel in ImageChops.difference(idle,image).getdata())
                            maximum=max(maximum,changed)
                    except Exception as error:need(False,f'Render exception {label}/{state}/{direction}/{number}: {type(error).__name__}: {error}')
                if state in required:
                    threshold=4 if label.startswith('equipment/') else 8
                    need(maximum>=threshold,f'Insufficient {state} motion in direction {direction}: {label} ({maximum} pixels, need {threshold})')
    moving=('walk','attack','cast','hit','death')
    for body in range(2):
        verify(f'people/body_{body}_2',lambda s,f,d,b=body:body_frame(b,2,s,f,d),STATES+EXTRA_STATES,moving)
    for style in range(6):
        verify(f'people/hair_{style}_3',lambda s,f,d,h=style:hair_frame(h,3,s,f,d),STATES+EXTRA_STATES,moving)
    representatives={}
    for item in data['items']:
        if not item.get('slot'):continue
        tags=item.get('tags',[]);ident=item['id']
        key=(item['slot'],_weapon_kind(item),'heavy' in tags,'light' in tags,int(item.get('tier',1))>=3,
             'shield' in ident,any(word in ident for word in ('book','tome','codex')))
        representatives.setdefault(key,item)
    for item in representatives.values():
        slot=item['slot']
        required=('walk','attack','hit','death') if slot in ('weapon','offhand','chest','helmet','cloak','gloves') else ('walk','death') if slot in ('legs','boots') else ()
        verify('equipment/'+item['id'],lambda s,f,d,i=item:armour_frame(i,s,f,d),STATES+EXTRA_STATES,required)
    for role in sorted({n['role'] for n in data['npcs']}):
        verify('npcs/'+role,lambda s,f,d,r=role:npc_frame(r,s,f,d),STATES+EXTRA_STATES,moving)
    for mob in data['mobs']:
        verify('mobs/'+mob['id'],lambda s,f,d,m=mob:creature_frame(m,s,f,d),STATES,moving,128 if mob.get('boss') else 64)
    report={'checks':checks,'sampled_frames':frames,'equipment_constructions':len(representatives),
            'creature_definitions':len(data['mobs']),'errors':errors,'error_count':error_count,
            'passed':error_count==0,'full_atlas_validation':False,'artistic_approval':False}
    output=ROOT/'artifacts/test-results/character-source.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    if error_count:raise SystemExit(1)

if __name__=='__main__':main()
