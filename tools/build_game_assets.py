#!/usr/bin/env python3
"""Build original art and audio; validate file coverage, not artistic acceptance."""
from __future__ import annotations
import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import random
import shutil
import sys
import wave
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT))
from art.common import Pixel,canvas,palette,shade,rgba,seed,sheet,save,STATES,DIRECTIONS,ELEMENT_COLORS
from art.items import icon
from art.people import body_frame,hair_frame,equipment_frame,npc_frame
from art.environment_pack import TERRAINS,PROPS,tile,prop,building,chest,resource,structure,crystal
from art.fauna import frame as creature_frame
from art.room_art import render as furnishing_image, building, edge as grass_edge
from content_src.presentation import FURNITURE
from integrate_atelier import integrate


def ability_icon(a):
    im=canvas((32,32)); p=Pixel(im); c=palette(ELEMENT_COLORS[a['element']]); kind=a['kind']; element=a['element']
    if kind in {'strike','charge','dash','interrupt','execute','taunt'}:
        im=icon({'id':a['id'],'type':'weapon','slot':'weapon','tags':['sword' if kind!='taunt' else 'mace'],'material':'silver','element':element})
        p=Pixel(im); p.line([(4,15),(7,7),(15,4)],c[4],2); p.line([(18,27),(25,24),(28,17)],c[3],2)
    elif kind in {'heal','purge'}:
        p.poly([(13,3),(20,3),(20,12),(28,12),(28,19),(20,19),(20,28),(13,28),(13,19),(4,19),(4,12),(13,12)],c[3]); p.line([(15,5),(15,14),(6,14)],c[5],2); p.line([(22,25),(26,22)],c[4])
    elif kind in {'shield','guard','buff','stealth'}:
        p.poly([(5,5),(16,2),(27,5),(26,18),(21,26),(16,30),(10,25),(6,18)],c[2]); p.poly([(8,8),(16,5),(24,8),(22,20),(16,26),(11,21)],c[3]); p.line([(10,9),(16,7),(21,9)],c[5]); p.line([(16,9),(12,16),(19,20)],c[0],2)
    elif element=='Fire':
        p.poly([(5,25),(8,17),(10,6),(16,14),(20,2),(23,13),(29,20),(25,28),(13,30)],c[3]); p.poly([(12,26),(16,14),(18,22),(22,16),(23,26),(18,29)],'efd38a',None)
    elif element=='Frost':
        for n in range(6):
            a0=n*math.tau/6; x,y=16+math.cos(a0)*13,16+math.sin(a0)*13; p.line([(16,16),(x,y)],c[4],2)
            xx,yy=16+math.cos(a0)*8,16+math.sin(a0)*8
            for s in (-1,1): p.line([(xx,yy),(xx+math.cos(a0+s*.8)*5,yy+math.sin(a0+s*.8)*5)],c[3])
        p.sphere((13,13,19,19),c[5])
    elif element=='Lightning':
        p.poly([(18,2),(8,17),(15,17),(11,30),(26,12),(18,12),(23,2)],c[3]); p.line([(19,4),(11,15),(18,15)],c[5],2)
    elif element in {'Nature','Poison'}:
        for dx,dy in [(-6,-4),(5,-7),(7,5)]: p.poly([(16,27),(16+dx-5,16+dy),(16+dx,7+dy),(16+dx+5,14+dy)],c[3]); p.line([(16,26),(16+dx,11+dy)],c[5])
        if element=='Poison': p.sphere((9,11,20,23),'b7bc7d'); p.rect((12,14,14,17),'4d5350'); p.rect((17,14,19,17),'4d5350')
    else:
        crystal(p,16,27,23,c[3]); p.d.arc((2,2,30,30),30,285,fill=rgba(c[4]),width=1)
    if kind in {'area','field'}: p.d.arc((1,19,30,31),0,340,fill=rgba(c[5]),width=1)
    elif kind in {'line','projectile'}: p.line([(2,26),(8,20)],c[5],2)
    elif kind=='cone': p.line([(1,26),(8,19),(11,29)],c[5])
    return im


def write_wav(path:Path,samples,sample_rate=22050):
    path.parent.mkdir(parents=True,exist_ok=True)
    data=array.array('h',(max(-32767,min(32767,round(v*32767))) for v in samples))
    if sys.byteorder!='little': data.byteswap()
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(sample_rate); out.writeframes(data.tobytes())


def audio_pack(root:Path):
    sr=22050
    music=['menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss','combat','interior']
    ambient=['meadow','forest','ancient_forest','coast','wind','cave','city','forge','harbor','tundra','swamp','interior','ruins','arcane']
    surfaces=['grass','dirt','stone','wood','water','snow']
    impacts=['blade','blunt','bow','magic']
    vocals=['beast','humanoid','undead','construct','spirit','monster']
    classes=['vanguard','berserker','ranger','rogue','arcanist','warden','templar','spellblade']
    effects=['gather','coins','hammer','equip','drink','ui','click','error','loot','quest_accept','quest_complete','skill_up','level_up','transition','chest','social','event_start','event_complete','heal','swing']
    modes=[(0,2,3,7,10),(0,2,5,7,9),(0,3,5,7,10),(0,2,3,5,7)]
    for k,name in enumerate(music):
        duration=16;count=duration*sr;output=[0.0]*count;mode=modes[k%len(modes)];root_note=45+k%7;step=.25 if name in {'boss','combat'} else .5
        for note in range(round(duration/step)):
            tone=mode[(note*3+note//4+k)%len(mode)]+root_note+(12 if note%4==0 else 0);hz=440*2**((tone-69)/12);start=round(note*step*sr)
            for t in range(min(round(sr*1.25),count-start)):
                secs=t/sr;env=min(1,secs/.012)*math.exp(-secs*(3.5 if name in {'boss','combat'} else 4.4));pulse=math.sin(math.tau*hz*secs)+.27*math.sin(math.tau*hz*2*secs)+.10*math.sin(math.tau*hz*3.01*secs)
                output[start+t]+=.16*env*pulse
        bed=84+7*(k%5)
        for t in range(count):
            secs=t/sr;fade=max(0,min(1,secs/.12,(duration-secs)/.28));output[t]=(output[t]+.023*math.sin(math.tau*bed*secs))*fade
        write_wav(root/f'music_{name}.wav',output)
    for k,key in enumerate(ambient):
        r=random.Random(seed('ambient:'+key));duration=12;count=sr*duration;last=0.0;output=[];base=52+11*(k%7)
        for t in range(count):
            secs=t/sr;last=last*.986+r.uniform(-1,1)*.014;v=last*.78+.018*math.sin(math.tau*base*secs)
            if key in {'forest','ancient_forest','meadow'} and secs%2.7<.16:v+=.055*math.sin(math.tau*(1250+k*73)*secs)*math.sin((secs%2.7)/.16*math.pi)
            if key in {'coast','harbor','swamp'}:v*=.7+.5*math.sin(secs*(1.15+k*.03))**2
            if key in {'forge'} and secs%1.8<.12:v+=.065*math.sin(math.tau*115*secs)*math.exp(-(secs%1.8)*22)
            if key in {'arcane'}:v+=.018*math.sin(math.tau*(310+40*math.sin(secs*.7))*secs)
            fade=max(0,min(1,secs/.18,(duration-secs)/.18));output.append(v*fade)
        write_wav(root/f'ambient_{key}.wav',output)
    for surface in surfaces:
        for variant in range(1,4):
            key=f'{surface}_{variant}';r=random.Random(seed('step:'+key));duration=.18+.015*variant;output=[];hz=78+variant*11+(35 if surface in {'stone','wood'} else 0)
            for t in range(round(sr*duration)):
                secs=t/sr;env=min(1,secs/.004)*math.exp(-secs*(25+variant));noise=r.uniform(-1,1);tone=math.sin(math.tau*hz*secs)
                texture=.19 if surface in {'dirt','grass','snow'} else .12;output.append((tone*.12+noise*texture)*env)
            write_wav(root/f'step_{key}.wav',output)
    for identity in impacts:
        for variant in range(1,4):
            key=f'{identity}_{variant}';r=random.Random(seed('impact:'+key));duration=.27;output=[];hz={'blade':430,'blunt':105,'bow':245,'magic':720}[identity]*(1+(variant-2)*.045)
            for t in range(round(sr*duration)):
                secs=t/sr;env=min(1,secs/.003)*math.exp(-secs*(17 if identity=='magic' else 24));noise=r.uniform(-1,1)*(.16 if identity!='magic' else .04);tone=math.sin(math.tau*hz*secs)+.22*math.sin(math.tau*hz*2.43*secs)
                output.append((tone*.16+noise)*env)
            write_wav(root/f'impact_{key}.wav',output)
    for family in vocals:
        for state in ['hurt','death']:
            key=f'{family}_{state}';r=random.Random(seed('vocal:'+key));duration=.42 if state=='hurt' else .56;output=[];base={'beast':185,'humanoid':145,'undead':95,'construct':110,'spirit':310,'monster':125}[family]
            for t in range(round(sr*duration)):
                secs=t/sr;progress=secs/duration;freq=base*(1+(.28 if state=='hurt' else -.30)*progress)+18*math.sin(secs*23);env=min(1,secs/.012)*max(0,1-progress)**1.35
                output.append((.16*math.sin(math.tau*freq*secs)+.05*math.sin(math.tau*freq*2.1*secs)+r.uniform(-1,1)*.035)*env)
            write_wav(root/f'vocal_{key}.wav',output)
    for k,cls in enumerate(classes):
        duration=.44;output=[];base=310+k*43;r=random.Random(seed('class:'+cls))
        for t in range(round(sr*duration)):
            secs=t/sr;env=min(1,secs/.006)*math.exp(-secs*7);sweep=base*(1+secs*(.7 if k%2 else .35));output.append((.15*math.sin(math.tau*sweep*secs)+.07*math.sin(math.tau*(base*1.5)*secs)+r.uniform(-1,1)*.025)*env)
        write_wav(root/f'class_{cls}.wav',output)
    for k,key in enumerate(effects):
        r=random.Random(seed('effect:'+key));duration=.24 if key not in {'quest_complete','level_up'} else .42;output=[];hz=160+(k*83)%1200
        for t in range(round(sr*duration)):
            secs=t/sr;env=min(1,secs/.006)*math.exp(-secs*(14 if duration>.3 else 23));tone=math.sin(math.tau*hz*secs)+.23*math.sin(math.tau*hz*2.31*secs);noise=r.uniform(-1,1)*(.12 if key in {'gather','hammer','swing'} else .035)
            output.append((tone*.15+noise)*env)
        write_wav(root/f'effect_{key}.wav',output)
    print('ASSETS: synthesized',len(list(root.glob('*.wav'))),'runtime WAV files',flush=True)


def preflight(data):
    errors=[]
    for mob in data['mobs']:
        try:
            expected=128 if mob['boss'] else 64
            for direction in range(4):
                image=creature_frame(mob,'idle',0,direction)
                if image.size!=(expected,expected) or image.getchannel('A').getbbox() is None:
                    raise ValueError('Empty or incorrectly sized creature frame.')
        except Exception as error:
            errors.append(mob['id']+': '+str(error))
    if errors:
        raise ValueError('Creature preflight failed:\n'+'\n'.join(errors))
    print('ASSETS: preflight passed for',len(data['mobs']),'creature definitions and four directions',flush=True)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='client/Assets'); parser.add_argument('--audio-only',action='store_true'); args=parser.parse_args()
    root=(ROOT/args.output).resolve()
    if root!=ROOT/'client/Assets' and not root.is_relative_to(ROOT/'artifacts'):
        raise SystemExit('Asset output must be client/Assets or a directory under artifacts.')
    root.mkdir(parents=True,exist_ok=True)
    if args.audio_only:
        audio_pack(root/'audio'); return
    catalog=ROOT/'content/catalog.json'
    if not catalog.is_file(): raise SystemExit('Run python tools/build_content.py first.')
    data=json.loads(catalog.read_text(encoding='utf-8')); generated=[]; sheets=[]
    preflight(data)
    def emit(image,key,animated=False):
        if key in generated: raise ValueError('Duplicate asset key: '+key)
        path=root/(key+'.png'); save(image,path); generated.append(key)
        if animated: sheets.append(key)
    print('ASSETS: terrain and environment',flush=True)
    for kind in TERRAINS:
        for n in range(4): emit(tile(kind,n),f'terrain/{kind}_{n}')
    for name in PROPS: emit(prop(name),'props/'+name)
    for name in FURNITURE: emit(furnishing_image(name),'furnishings/'+name)
    for mask in range(1,16): emit(grass_edge(mask),'terrain/grass_edge_'+str(mask))
    for z in data['zones']:
        for b in z['buildings']: emit(building(z,b),'buildings/'+z['id']+'/'+b['id'])
    for r in data['resources']: emit(resource(r),'resources/'+r['id'])
    if not any(r['id']=='crop_wheat' for r in data['resources']):
        crop=next((x for x in data['resources'] if x['id']=='wheat_crop'),{'id':'crop_wheat','skill':'farming'})
        emit(resource(crop),'resources/crop_wheat')
    for name in ['weathered','locked','ancient','runic','royal','cursed','mimic']:
        for opened in (False,True): emit(chest(name,opened),'chests/'+name+('_open' if opened else '_closed'))
    print('ASSETS: items and abilities',flush=True)
    for item in data['items']:
        emit(icon(item),'items/'+item['id'])
        if item['type']=='structure': emit(structure(item['id']),'structures/'+item['id'])
    for a in data['abilities']: emit(ability_icon(a),'abilities/'+a['id'])
    print('ASSETS: aligned player body and hair layers',flush=True)
    for body in range(2):
        for skin in range(6): emit(sheet(lambda st,n,d:body_frame(body,skin,st,n,d)),f'people/body_{body}_{skin}',True)
    for style in range(6):
        for colour in range(8): emit(sheet(lambda st,n,d:hair_frame(style,colour,st,n,d)),f'people/hair_{style}_{colour}',True)
    equipment=[i for i in data['items'] if i.get('slot')]
    for index,item in enumerate(equipment):
        cached=icon(item)
        emit(sheet(lambda st,n,d:equipment_frame(item,st,n,d,cached)),'equipment/'+item['id'],True)
        if index%50==0: print('ASSETS: equipment',index,'/',len(equipment),flush=True)
    print('ASSETS: named NPC roles',flush=True)
    for role in sorted({n['role'] for n in data['npcs']}): emit(sheet(lambda st,n,d:npc_frame(role,st,n,d)),'npcs/'+role,True)
    print('ASSETS: creature anatomy',flush=True)
    for index,m in enumerate(data['mobs']):
        emit(sheet(lambda st,n,d:creature_frame(m,st,n,d),128 if m['boss'] else 64),'mobs/'+m['id'],True)
        if index%20==0: print('ASSETS: creatures',index,'/',len(data['mobs']),flush=True)
    print('ASSETS: original audio',flush=True); audio_pack(root/'audio')
    shutil.copyfile(catalog,root/'catalog.json')
    atelier=integrate(ROOT/'atelier/Assets',root,generated)
    entries=[]; animated_keys=set(sheets)
    for key in sorted(generated):
        path=root/(key+'.png')
        with Image.open(path) as im:
            if im.mode!='RGBA' or im.getchannel('A').getbbox() is None: raise ValueError('Empty or non-RGBA asset: '+key)
            if key in animated_keys and (im.width%8 or im.height!=im.width//8*24): raise ValueError('Invalid animation grid: '+key)
            entries.append({'key':key,'width':im.width,'height':im.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'animated':key in animated_keys})
    manifest={'schema':1,'source':'Original project and checksum-verified Atelier catalog artwork; source scripts are included.','atelier_assets':atelier['integrated'],'artistic_review':'not_approved','frame_order':list(STATES),'directions':list(DIRECTIONS),'frames_per_row':8,'assets':entries}
    (root/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (root/'CREDITS.txt').write_text('Kairnfall original pixel-art generators and synthesized audio. Source code is included under tools/art and tools/build_game_assets.py. Original project source uses the repository MIT license. Matching Atelier assets from atelier/Assets replace compatible catalog artwork as a complete humanoid rig cohort. Read ATELIER_CREDITS.txt and atelier-integration.json for provenance and exact hashes. No independent gear records or third-party artwork are imported. Structural validation is not visual approval.\n',encoding='utf-8')
    evidence=ROOT/'artifacts/screenshots'; evidence.mkdir(parents=True,exist_ok=True)
    creatures=canvas((10*160,math.ceil(len(data['mobs'])/10)*175)); draw=ImageDraw.Draw(creatures)
    for i,m in enumerate(data['mobs']):
        size=128 if m['boss'] else 64
        with Image.open(root/'mobs'/(m['id']+'.png')) as source: f=source.crop((0,0,size,size)).convert('RGBA')
        scale=1 if m['boss'] else 2; f=f.resize((f.width*scale,f.height*scale),Image.Resampling.NEAREST)
        x=(i%10)*160; y=(i//10)*175; creatures.alpha_composite(f,(x+16,y)); draw.text((x+3,y+136),m['id'][:25],fill=(224,219,197,255))
    save(creatures,evidence/'creature-contact-sheet.png')
    (ROOT/'artifacts/asset-coverage.json').write_text(json.dumps({'png_files':len(entries),'animation_sheets':len(sheets),'audio_files':len(list((root/'audio').glob('*.wav'))),'all_catalog_images_generated':True,'artistic_review':'not_approved'},indent=2)+'\n',encoding='utf-8')
    print('ASSETS RESULT:',len(entries),'PNG files;',len(sheets),'animation sheets;',len(list((root/'audio').glob('*.wav'))),'audio files. Structural checks passed; visual review remains required.',flush=True)

if __name__=='__main__': main()
