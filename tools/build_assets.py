#!/usr/bin/env python3
"""Build the complete original Kairnfall art/audio pack, or explicit review previews."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import importlib
import json
import os
import re
import shutil
import sys
import tempfile
import textwrap
import time
import wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from art import common, people, environment, icons
from art.items import icon as item_icon

VISIBLE_SLOTS = {'weapon','offhand','helmet','chest','gloves','legs','boots','belt','cloak','ring','necklace','charm','trinket'}
PROPS = ('shadow','oak','ancient_oak','pine','snow_pine','willow','dead_tree','palm','rock','snow_rock','basalt','stump','bush','flowers','herb','grass_tuft','reeds','mushrooms','crop','sprout','crystal','cactus','signpost','waystone','stairs','loot','barrel','crate','anvil','forge','campfire','bench','rune_table','loom','fish_spot','dig_site','pelt')
CHESTS = ('weathered','locked','ancient','runic','royal','cursed','mimic')
STRUCTURES = {'campfire':'campfire','workbench':'bench','sawbench':'bench','kitchen':'campfire','rune_table':'rune_table'}
_DATA = {}
_INDEX = {}
_OUTPUT = Path('.')


def safe_id(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]+',value):
        raise ValueError('Unsafe asset identifier: '+repr(value))
    return value


def initialize(catalog_path, output):
    global _DATA, _INDEX, _OUTPUT
    _DATA=json.loads(Path(catalog_path).read_text(encoding='utf-8'))
    _INDEX={group:{entry['id']:entry for entry in _DATA[group]} for group in ('items','skills','abilities','mobs','resources','zones','classes')}
    _OUTPUT=Path(output)


def creature_module():
    try:return importlib.import_module('art.creatures')
    except ModuleNotFoundError as error:
        if error.name not in {'art.creatures','creatures'}:raise
        raise RuntimeError('Creature art is not integrated. Merge the reviewed creature-art workstream before building a complete game pack. Preview mode does not constitute a complete pack.') from error


def render_job(job):
    kind=job['kind'];key=job['key'];size=None
    if kind=='item':image=item_icon(_INDEX['items'][job['id']])
    elif kind=='skill':image=icons.skill_icon(_INDEX['skills'][job['id']],_DATA['items'])
    elif kind=='ability':image=icons.ability_icon(_INDEX['abilities'][job['id']])
    elif kind=='body':
        size=64;image=common.sheet(lambda state,frame,direction:people.body_frame(job['body'],job['skin'],state,frame,direction),size)
    elif kind=='hair':
        size=64;image=common.sheet(lambda state,frame,direction:people.hair_frame(job['style'],job['color'],state,frame,direction),size)
    elif kind=='equipment':
        definition=_INDEX['items'][job['id']];cached=item_icon(definition);size=64
        image=common.sheet(lambda state,frame,direction:people.equipment_frame(definition,state,frame,direction,cached),size)
    elif kind=='npc':
        size=64;image=common.sheet(lambda state,frame,direction:people.npc_frame(job['role'],state,frame,direction),size)
    elif kind=='mob':
        module=creature_module();definition=_INDEX['mobs'][job['id']];size=module.frame_size(definition)
        if size!=(128 if definition.get('boss',False) else 64):raise ValueError('Incorrect creature frame size: '+definition['id'])
        image=common.sheet(lambda state,frame,direction:module.creature_frame(definition,state,frame,direction),size)
    elif kind=='terrain':image=environment.terrain(job['terrain'],job['variant'])
    elif kind=='prop':image=environment.prop(job['prop'])
    elif kind=='resource':image=environment.resource(_INDEX['resources'][job['id']])
    elif kind=='structure':
        definition=_INDEX['items'][job['id']];category=definition['id'].removeprefix('structure_')
        if category not in STRUCTURES:raise ValueError('Unmapped structure art: '+category)
        image=environment.prop(STRUCTURES[category])
    elif kind=='chest':image=environment.chest(job['chest'],job['open'])
    elif kind=='building':
        zone=_INDEX['zones'][job['zone']];definition=next(b for b in zone.get('buildings',[]) if b['id']==job['id'])
        definition=dict(definition);definition.setdefault('width',5);definition.setdefault('height',4)
        image=environment.building(zone,definition)
    else:raise ValueError('Unknown render job: '+kind)
    if image.mode!='RGBA':raise ValueError('Asset is not RGBA: '+key)
    if image.getchannel('A').getbbox() is None:raise ValueError('Empty asset: '+key)
    if size is not None:
        if image.size!=(size*8,size*24):raise ValueError('Invalid animation matrix: '+key)
        for row in range(24):
            for column in range(8):
                alpha=image.crop((column*size,row*size,(column+1)*size,(row+1)*size)).getchannel('A')
                if alpha.getbbox() is None:raise ValueError(f'Empty animation frame: {key} row={row} column={column}')
    path=_OUTPUT/(key+'.png');common.save(image,path)
    return {'path':key+'.png','kind':kind,'width':image.width,'height':image.height,'frame_size':size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def jobs_for(data):
    jobs=[]
    for group,kind,prefix in [('items','item','items'),('skills','skill','skills'),('abilities','ability','abilities'),('mobs','mob','mobs'),('resources','resource','resources')]:
        for entry in data[group]:
            ident=safe_id(entry['id']);jobs.append(dict(kind=kind,key=prefix+'/'+ident,id=ident))
    for body in range(2):
        for skin in range(6):jobs.append(dict(kind='body',key=f'people/body_{body}_{skin}',body=body,skin=skin))
    for style in range(6):
        for color in range(8):jobs.append(dict(kind='hair',key=f'people/hair_{style}_{color}',style=style,color=color))
    for item in data['items']:
        ident=safe_id(item['id'])
        if item.get('slot','') in VISIBLE_SLOTS:jobs.append(dict(kind='equipment',key='equipment/'+ident,id=ident))
        if item.get('type')=='structure':jobs.append(dict(kind='structure',key='structures/'+ident,id=ident))
    for role in sorted({npc['role'] for npc in data['npcs']}):jobs.append(dict(kind='npc',key='npcs/'+safe_id(role),role=role))
    for terrain in environment.GROUND:
        for variant in range(4):jobs.append(dict(kind='terrain',key=f'terrain/{terrain}_{variant}',terrain=terrain,variant=variant))
    for prop in PROPS:jobs.append(dict(kind='prop',key='props/'+prop,prop=prop))
    for chest in CHESTS:
        for opened in (False,True):jobs.append(dict(kind='chest',key=f'chests/{chest}_'+('open' if opened else 'closed'),chest=chest,open=opened))
    for zone in data['zones']:
        for building in zone.get('buildings',[]):jobs.append(dict(kind='building',key='buildings/'+safe_id(zone['id'])+'/'+safe_id(building['id']),zone=zone['id'],id=building['id']))
    keys=[job['key'] for job in jobs]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate generated asset path.')
    return jobs


def contact(entries, path, columns=6, cell=(160,178), maximum_scale=2):
    if not entries:return
    rows=(len(entries)+columns-1)//columns;image=Image.new('RGBA',(columns*cell[0],rows*cell[1]),'#18252c');draw=ImageDraw.Draw(image);font=ImageFont.load_default(size=11)
    for index,(label,source) in enumerate(entries):
        x=(index%columns)*cell[0];y=(index//columns)*cell[1]
        scale=min(maximum_scale,(cell[0]-12)/source.width,(cell[1]-42)/source.height)
        if scale>=1:scale=max(1,math_floor(scale))
        size=(max(1,round(source.width*scale)),max(1,round(source.height*scale)))
        sprite=source.resize(size,Image.Resampling.NEAREST)
        image.alpha_composite(sprite,(x+(cell[0]-size[0])//2,y+5+(cell[1]-42-size[1])//2))
        text='\n'.join(textwrap.wrap(label,23)[:2]);draw.multiline_text((x+7,y+cell[1]-35),text,font=font,fill='#ded5bd',spacing=2)
        draw.rectangle((x,y,x+cell[0]-1,y+cell[1]-1),outline='#34484d')
    common.save(image,path)


def math_floor(value):return int(value//1)


def composite_character(cls,data,direction=0,state='idle',frame=0,index=0):
    by_id={item['id']:item for item in data['items']};image=people.body_frame(index%2,index%6,state,frame,direction)
    armor=by_id[cls['armor']];image.alpha_composite(people.equipment_frame(armor,state,frame,direction))
    image.alpha_composite(people.hair_frame(index%6,index%8,state,frame,direction))
    image.alpha_composite(people.equipment_frame(by_id[cls['weapon']],state,frame,direction))
    return image


def previews(data,output):
    output.mkdir(parents=True,exist_ok=True)
    for start in range(0,len(data['items']),72):
        entries=[(item['name'],item_icon(item)) for item in data['items'][start:start+72]]
        contact(entries,output/f'items-{start//72+1:02}.png',columns=8,cell=(112,112),maximum_scale=2)
    characters=[]
    for index,cls in enumerate(data['classes']):
        for direction in range(4):characters.append((cls['name']+' · '+common.DIRECTIONS[direction],composite_character(cls,data,direction,'walk',2,index)))
    contact(characters,output/'characters.png',columns=8,cell=(144,178))
    contact([(prop,environment.prop(prop)) for prop in PROPS],output/'environment.png',columns=6,cell=(170,190))
    buildings=[]
    for zone in data['zones']:
        if zone.get('kind') not in {'city','settlement'}:continue
        for building in zone.get('buildings',[])[:2]:
            definition=dict(building);definition.setdefault('width',5);definition.setdefault('height',4)
            buildings.append((zone['name']+' / '+building.get('name',building['id']),environment.building(zone,definition)))
    contact(buildings,output/'buildings.png',columns=4,cell=(300,270),maximum_scale=1)
    try:
        module=creature_module()
        for start in range(0,len(data['mobs']),30):
            contact([(mob['name'],module.creature_frame(mob,'idle',0,0)) for mob in data['mobs'][start:start+30]],output/f'creatures-{start//30+1:02}.png',columns=6,cell=(170,190))
        creature_status='rendered; visual approval still requires inspection'
    except RuntimeError as error:creature_status=str(error)
    result={'mode':'preview_only','game_pack_complete':False,'creatures':creature_status,'review_required':True,'files':sorted(p.name for p in output.glob('*.png'))}
    (output/'preview-status.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


def audio_metadata(path,base):
    with wave.open(str(path),'rb') as stream:
        rate=stream.getframerate();frames=stream.getnframes();channels=stream.getnchannels();sample_width=stream.getsampwidth()
        if rate!=22050 or channels!=2 or sample_width!=2 or frames==0:raise ValueError('Invalid audio format: '+str(path))
    return {'path':path.relative_to(base).as_posix(),'kind':'audio','rate':rate,'channels':channels,'samples':frames,'seconds':round(frames/rate,4),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def install_pack(stage,output,manifest):
    output.mkdir(parents=True,exist_ok=True)
    previous=[]
    old=output/'manifest.json'
    if old.is_file():
        try:previous=[entry['path'] for entry in json.loads(old.read_text(encoding='utf-8')).get('assets',[])]
        except (ValueError,KeyError,TypeError):raise ValueError('Existing asset manifest is invalid; refusing to remove unknown files.')
    incoming={entry['path'] for entry in manifest['assets']}
    for path in sorted(stage.rglob('*')):
        if not path.is_file() or path.name=='manifest.json':continue
        relative=path.relative_to(stage);target=output/relative;target.parent.mkdir(parents=True,exist_ok=True);os.replace(path,target)
    for name in previous:
        candidate=(output/name).resolve()
        if candidate.is_relative_to(output.resolve()) and name not in incoming and candidate.is_file():candidate.unlink()
    # The completed manifest is installed last. Unknown pre-existing files are preserved.
    temporary=output/'.manifest.next.json';temporary.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8');os.replace(temporary,output/'manifest.json')


def build(catalog,output,workers,review_dir):
    raw=catalog.read_bytes();data=json.loads(raw);creature_module()
    jobs=jobs_for(data);output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.kairnfall-art-',dir=output.parent));started=time.monotonic()
    try:
        results=[]
        if workers==1:
            initialize(catalog,stage)
            for index,job in enumerate(jobs):
                results.append(render_job(job))
                if index%100==0:print(f'Rendered {index+1}/{len(jobs)} images.',flush=True)
        else:
            with concurrent.futures.ProcessPoolExecutor(max_workers=workers,initializer=initialize,initargs=(str(catalog),str(stage))) as pool:
                for index,result in enumerate(pool.map(render_job,jobs,chunksize=2)):
                    results.append(result)
                    if index%100==0:print(f'Rendered {index+1}/{len(jobs)} images.',flush=True)
        # Runtime farming instances use a different ID from their resource definition.
        wheat=next((entry for entry in data['resources'] if entry['id']=='wheat_crop'),None)
        if wheat is None:raise ValueError('Missing wheat_crop resource definition.')
        aliases={'crop_wheat':environment.resource(wheat),'crop_wheat_stage0':environment.prop('sprout'),'crop_wheat_stage1':environment.prop('sprout'),'crop_wheat_stage2':environment.prop('crop'),'crop_wheat_stage3':environment.prop('crop')}
        for ident,image in aliases.items():
            path=stage/'resources'/(ident+'.png');common.save(image,path);results.append({'path':path.relative_to(stage).as_posix(),'kind':'resource_alias','width':image.width,'height':image.height,'frame_size':None,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        from art.audio import build_audio
        for path in build_audio(stage/'audio'):results.append(audio_metadata(path,stage))
        (stage/'catalog.json').write_bytes(raw)
        results.append({'path':'catalog.json','kind':'catalog','sha256':hashlib.sha256(raw).hexdigest()})
        source_hash=hashlib.sha256()
        for source in sorted((ROOT/'tools'/'art').rglob('*.py')):source_hash.update(source.relative_to(ROOT).as_posix().encode());source_hash.update(source.read_bytes())
        manifest={'schema':1,'mode':'complete_generated_pack','visual_review':'pending_independent_inspection','catalog_sha256':hashlib.sha256(raw).hexdigest(),'art_source_sha256':source_hash.hexdigest(),'animation':{'states':list(common.STATES),'directions':list(common.DIRECTIONS),'frames':8,'columns':8,'rows':24,'feet_anchor':[.5,.86]},'assets':sorted(results,key=lambda entry:entry['path'])}
        if len({entry['path'] for entry in results})!=len(results):raise ValueError('Duplicate final asset path.')
        install_pack(stage,output,manifest)
        if review_dir:previews(data,review_dir)
        print(json.dumps({'status':'generated_and_technically_validated','visual_approval':False,'output':str(output),'images':len(jobs)+len(aliases),'audio':sum(entry['kind']=='audio' for entry in results),'seconds':round(time.monotonic()-started,2)},indent=2))
    finally:shutil.rmtree(stage,ignore_errors=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);parser.add_argument('--catalog',type=Path,default=ROOT/'content'/'catalog.json');parser.add_argument('--workers',type=int,default=min(4,os.cpu_count() or 1));parser.add_argument('--preview',action='store_true');parser.add_argument('--review-dir',type=Path)
    args=parser.parse_args()
    if sys.version_info<(3,12):parser.error('Use Python 3.12 or newer with tools/requirements-art.txt.')
    if not args.catalog.is_file():parser.error('Missing catalog. Run python tools/build_content.py first.')
    if args.workers<1 or args.workers>8:parser.error('Choose 1–8 worker processes.')
    if args.preview:previews(json.loads(args.catalog.read_text(encoding='utf-8')),args.output or ROOT/'build'/'art-preview')
    else:build(args.catalog,args.output or ROOT/'client'/'Assets',args.workers,args.review_dir)

if __name__=='__main__':main()
