#!/usr/bin/env python3
"""Render source contact sheets. These are not gameplay screenshots or approval."""
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
    def save(image,name):
        path=output/(name+'.png'); image.save(path,optimize=True)
        records.append({'file':path.name,'width':image.width,'height':image.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    def contact(entries,name,columns=6,cell=(144,156),scale=2):
        image=Image.new('RGBA',(columns*cell[0],max(1,math.ceil(len(entries)/columns))*cell[1]),'#24262b'); draw=ImageDraw.Draw(image)
        for i,(label,tile) in enumerate(entries):
            tile=tile.resize((tile.width*scale,tile.height*scale),Image.Resampling.NEAREST)
            x=(i%columns)*cell[0]; y=(i//columns)*cell[1]
            image.alpha_composite(tile,(x+(cell[0]-tile.width)//2,y+4))
            draw.text((x+5,y+cell[1]-19),label[:26],fill='#e9dfc5')
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
    equipment=[item for item in data['items'] if item.get('slot')]
    basegear={slot:next(item for item in equipment if item['slot']==slot) for slot in ('helmet','chest','legs','boots','cloak')}
    contact([(f'body {b} skin {skin}',body_frame(b,skin,'idle',0,0)) for b in range(2) for skin in range(6)],'player-bodies')
    for family in ('sword','axe','bow','staff','spear'):
        item=next(item for item in equipment if item['slot']=='weapon' and family in item.get('tags',[]))
        gear=dict(basegear,weapon=item)
        if family in ('sword','axe'): gear['offhand']=next(item for item in equipment if item['slot']=='offhand' and 'shield' in item.get('tags',[]))
        entries=[]
        for state in STATES:
            for d in range(4):
                for n in range(8): entries.append((f'{state} {d} / {n}',person(0,state,n,d,gear)))
        contact(entries,'equipment-'+family,columns=8,cell=(136,151))
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in data['mobs'] if not m['boss'] and not m.get('elite')],'normal-mobs',columns=8)
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in data['mobs'] if m.get('elite')],'elites')
    contact([(m['id'],creature_frame(m,'idle',0,0)) for m in data['mobs'] if m['boss']],'bosses',columns=5,cell=(160,158),scale=1)
    for ident in ('field_rat','wild_hare','pine_wolf','polar_bear','sea_turtle','wood_spider'):
        mob=next(m for m in data['mobs'] if m['id']==ident)
        contact([(f'{state} {d} / {n}',creature_frame(mob,state,n,d)) for state in STATES for d in range(4) for n in range(8)],'animation-'+ident,8,(136,151))
    contact([(item['name'],icon(item)) for item in data['items']],'item-icons',columns=10,cell=(104,96),scale=2)
    contact([(role,npc_frame(role,'idle',0,0)) for role in sorted({npc['role'] for npc in data['npcs']})],'npc-roles')
    contact([(name,prop(name)) for name in PROPS],'environment',columns=5,cell=(168,166),scale=1)
    for zone in data['zones']:
        if zone['id']!='wayfarers_rest': continue
        for value in zone['buildings']: save(building(zone,value),'building-'+value['id'])
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    (output/'review-manifest.json').write_text(json.dumps({'source_revision':revision,'evidence_kind':'source-rendered contact sheets; not gameplay','visual_approval':'not_reviewed','files':records},indent=2)+'\n',encoding='utf-8')
    print(f'VISUAL_REVIEW: {len(records)} source contact sheets; visual approval not inferred.')


if __name__=='__main__': main()
