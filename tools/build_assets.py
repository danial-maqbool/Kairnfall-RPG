"""Build and validate the client pack. Structural validation is not visual approval."""
from __future__ import annotations
import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from PIL import Image
from art.common import Pixel, canvas, palette, sheet, ELEMENT_COLORS
from art import people, items, environment, creatures

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'client'/'Assets'
SAFE=re.compile(r'^[a-zA-Z0-9_/-]+$')

def icon_ability(spec):
    im=canvas((32,32)); p=Pixel(im); color=ELEMENT_COLORS.get(spec['element'],'c3b6a2'); c=palette(color)
    p.rect((1,1,30,30),'343d47','1c252e'); p.rect((3,3,28,28),'4d5156','8e8c79')
    kind=spec['kind']
    if kind in {'shield','taunt','buff','purge'}:
        p.poly([(9,7),(23,7),(23,18),(20,23),(16,26),(12,23),(9,18)],c[2]); p.poly([(11,9),(16,9),(16,23),(13,20),(11,16)],c[4],None); p.line([(16,9),(16,22)],c[5]); p.line([(12,15),(20,15)],c[5],2)
    elif kind in {'strike','drain','interrupt','dash'}:
        p.poly([(10,22),(21,7),(25,6),(25,10),(13,24)],c[3]); p.line([(12,21),(23,8)],c[5]); p.line([(8,20),(15,26)],'c7ab76',3); p.line([(7,27),(11,23)],'9a785a',3)
    elif kind=='heal':
        p.poly([(13,8),(19,8),(19,13),(24,13),(24,19),(19,19),(19,25),(13,25),(13,19),(7,19),(7,13),(13,13)],c[3]); p.line([(14,10),(17,10),(17,14),(22,14)],c[5],2)
    elif kind in {'summon','stealth'}:
        p.poly([(9,21),(10,12),(7,7),(14,10),(19,10),(25,6),(23,14),(24,22),(17,26)],c[2]); p.line([(11,16),(14,16)],c[5],2); p.line([(19,16),(22,16)],c[5],2); p.poly([(15,20),(19,20),(17,23)],'d3c6a4')
    else:
        p.line([(8,26),(19,10)],'9a805b',3); p.line([(9,25),(18,12)],'d0b88b')
        p.poly([(15,10),(18,4),(22,8),(26,7),(24,13),(28,17),(21,17),(18,22),(16,15),(11,13)],c[3]); p.poly([(18,9),(21,7),(23,12),(20,16),(18,14)],c[5],None)
        if kind in {'area','field','cone','line'}:
            p.line([(6,23),(11,26),(23,25),(27,20)],c[4]); p.line([(7,25),(13,28),(24,27)],c[1])
    return im

def task_image(task):
    key,category,payload=task
    if not SAFE.fullmatch(key) or '..' in key.split('/'): raise ValueError('Unsafe asset key: '+key)
    if category=='body': im=sheet(lambda s,f,d:people.body_frame(payload[0],payload[1],s,f,d))
    elif category=='hair': im=sheet(lambda s,f,d:people.hair_frame(payload[0],payload[1],s,f,d))
    elif category=='equipment': im=sheet(lambda s,f,d:people.equipment_frame(payload,s,f,d))
    elif category=='npc': im=sheet(lambda s,f,d:people.npc_frame(payload,s,f,d))
    elif category=='mob': im=sheet(lambda s,f,d:creatures.frame(payload,s,f,d),128 if payload.get('boss') else 64)
    elif category=='item': im=items.icon(payload)
    elif category=='ability': im=icon_ability(payload)
    elif category=='terrain': im=environment.terrain(*payload)
    elif category=='prop': im=environment.prop(payload)
    elif category=='chest': im=environment.chest(*payload)
    elif category=='building': im=environment.building(*payload)
    elif category=='resource': im=environment.resource(payload)
    elif category=='structure': im=environment.structure(payload)
    else: raise ValueError('Unknown image category: '+category)
    if im.mode!='RGBA': im=im.convert('RGBA')
    path=OUT/(key+'.png'); path.parent.mkdir(parents=True,exist_ok=True); im.save(path,compress_level=6)
    return key

def tasks(data):
    output=[]
    def add(key,category,payload): output.append((key,category,payload))
    for body in range(2):
        for skin in range(6): add(f'people/body_{body}_{skin}','body',(body,skin))
    for hair in range(6):
        for color in range(8): add(f'people/hair_{hair}_{color}','hair',(hair,color))
    for item in data['items']:
        add('items/'+item['id'],'item',item)
        if item.get('slot'): add('equipment/'+item['id'],'equipment',item)
    for ability in data['abilities']: add('abilities/'+ability['id'],'ability',ability)
    for role in sorted({npc['role'] for npc in data['npcs']}): add('npcs/'+role,'npc',role)
    for mob in data['mobs']: add('mobs/'+mob['id'],'mob',mob)
    for terrain in environment.TERRAINS:
        for variant in range(4): add(f'terrain/{terrain}_{variant}','terrain',(terrain,variant))
    for prop in environment.PROPS: add('props/'+prop,'prop',prop)
    for kind in environment.CHESTS:
        for opened in (False,True): add('chests/'+kind+('_open' if opened else '_closed'),'chest',(kind,opened))
    for node in data['resources']: add('resources/'+node['id'],'resource',node)
    stations={r['station'] for r in data['recipes']}|{n.get('station','') for n in data['npcs']}|{'campfire','workbench','forge','chest','house','wheat_crop','fishing_trap'}
    for station in sorted(stations-{''}): add('structures/structure_'+station,'structure',station)
    for zone in data['zones']:
        for building in zone['buildings']: add('buildings/'+zone['id']+'/'+building['id'],'building',(zone,building))
    if len({x[0] for x in output})!=len(output): raise ValueError('Duplicate asset output keys.')
    return output

def validate(data, jobs):
    failures=[]; entries=[]; species_hash={}
    for key,category,payload in jobs:
        path=OUT/(key+'.png')
        if not path.is_file(): failures.append('Missing '+key); continue
        with Image.open(path) as im:
            im.load()
            if im.mode!='RGBA' or im.getchannel('A').getbbox() is None: failures.append('Empty or invalid '+key)
            if category in {'body','hair','equipment','npc','mob'}:
                size=128 if category=='mob' and payload.get('boss') else 64
                if im.size!=(size*8,size*24): failures.append('Atlas dimensions '+key)
                for row in range(24):
                    frame=im.crop((0,row*size,size,(row+1)*size))
                    if frame.getchannel('A').getbbox() is None: failures.append(f'Empty animation row {row}: '+key)
                if category=='mob' and not payload.get('boss') and not payload.get('elite'):
                    digest=hashlib.sha256(im.crop((0,0,size,size)).tobytes()).hexdigest(); species_hash.setdefault(digest,[]).append(payload['id'])
            entries.append({'key':key,'category':category,'width':im.width,'height':im.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    duplicates=[values for values in species_hash.values() if len(values)>1]
    manifest={'schema':1,'source_commit':os.environ.get('GITHUB_SHA','local'),'files':entries,'structural_errors':failures,'visual_review':'not_approved','normal_species_matching_first_frames':duplicates,'notice':'Dimensions, existence, and unique hashes do not prove visual quality, distinct anatomy, or complete MMORPG acceptance.'}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    report=ROOT/'artifacts'/'test-results'; report.mkdir(parents=True,exist_ok=True)
    (report/'assets.json').write_text(json.dumps({'files':len(entries),'errors':failures,'matching_species_first_frames':duplicates,'visual_approval':False},indent=2)+'\n',encoding='utf-8')
    if failures: raise RuntimeError('\n'.join(failures[:50]))
    print(f'ASSET STRUCTURE: {len(entries)} PNG files; zero structural errors; {len(duplicates)} matching species-frame groups. Visual approval remains open.',flush=True)
    return manifest

def contact_sheets(jobs):
    dest=ROOT/'artifacts'/'art-review'; dest.mkdir(parents=True,exist_ok=True)
    for category in ('item','mob','npc','terrain','prop','equipment'):
        selected=[job for job in jobs if job[1]==category][:64]; cols=8; rows=(len(selected)+cols-1)//cols
        if not selected: continue
        sheet_image=Image.new('RGBA',(cols*96,rows*108),'#333b40')
        from PIL import ImageDraw
        draw=ImageDraw.Draw(sheet_image)
        for i,(key,cat,payload) in enumerate(selected):
            with Image.open(OUT/(key+'.png')) as source:
                if cat in {'mob','npc','equipment'}:
                    size=source.width//8; picture=source.crop((0,0,size,size))
                else: picture=source.copy()
                if picture.width>88 or picture.height>88: picture.thumbnail((88,88),Image.Resampling.NEAREST)
                x=(i%cols)*96; y=(i//cols)*108
                sheet_image.alpha_composite(picture,(x+(96-picture.width)//2,y+(88-picture.height)//2))
                draw.text((x+2,y+90),key.split('/')[-1][:14],fill='#dfd2b7')
        sheet_image.convert('RGB').save(dest/(category+'.png'))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--verify-only',action='store_true'); parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args(); os.chdir(ROOT)
    data=json.loads((ROOT/'content'/'catalog.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True,exist_ok=True); jobs=tasks(data)
    if not args.verify_only:
        with ProcessPoolExecutor(max_workers=max(1,min(args.workers,4))) as pool:
            for i,key in enumerate(pool.map(task_image,jobs,chunksize=2),1):
                if i%100==0: print(f'Built {i}/{len(jobs)} art files',flush=True)
        shutil.copy2(ROOT/'content'/'catalog.json',OUT/'catalog.json')
        from art.audio import build as build_audio
        build_audio(OUT/'audio',data)
    validate(data,jobs); contact_sheets(jobs)
    print('Client pack built. Visual review and full-game release gates are separate.',flush=True)

if __name__=='__main__': main()
