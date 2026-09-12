"""Integrate checked-in Atelier catalog art without changing gameplay records.

Read-only sources: atelier/Assets plus the optional authored player hero sheet at
atelier/authored/player/hero.png. Derived output: client/Assets. The independent
Atelier gear/gear_worn ladder is NOT a second catalog and is never copied here.
People, worn equipment and NPCs switch as one complete rig cohort.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from PIL import Image

GROUPS=frozenset({'people','equipment','npcs','mobs','items','abilities','terrain','props','buildings','resources','chests','structures'})
RIG=frozenset({'people','equipment','npcs'})
STATES=('idle','walk','attack','cast','hit','death')
DIRECTIONS=('south','west','east','north')


def safe_path(root:Path,key:str)->Path:
    if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*',key):
        raise ValueError('Unsafe Atelier asset key')
    path=root/(key+'.png')
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError('Atelier asset escapes its root: '+key)
    return path


def plan(library:Path,output:Path,keys:list[str])->tuple[list[tuple[str,Path,str]],list[dict]]:
    metadata=json.loads((library/'manifest.json').read_text(encoding='utf-8'))
    if metadata.get('library')!='atelier' or metadata.get('schema')!=1:
        raise ValueError('Unrecognized Atelier manifest')
    if tuple(metadata.get('frame_order',()))!=STATES or tuple(metadata.get('directions',()))!=DIRECTIONS:
        raise ValueError('Atelier animation state or direction order differs')
    if metadata.get('frames_per_row')!=8 or metadata.get('actor_size')!=64 or metadata.get('boss_size')!=128 or metadata.get('foot_baseline')!=55:
        raise ValueError('Atelier rig dimensions or foot anchor differ')
    entries={}
    for entry in metadata.get('assets',[]):
        key=entry['key']; safe_path(library,key)
        if key in entries:raise ValueError('Duplicate Atelier manifest key: '+key)
        entries[key]=entry
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate output asset key')
    selected=[];skipped=[]
    for key in sorted(keys):
        group=PurePosixPath(key).parts[0]
        if group not in GROUPS:continue
        source=safe_path(library,key);destination=safe_path(output,key)
        if key not in entries or not source.is_file():
            if group in RIG:raise ValueError('Incomplete Atelier body/equipment cohort: '+key)
            skipped.append({'key':key,'reason':'No matching Atelier source; keep generated project art'});continue
        entry=entries[key]
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=entry.get('sha256'):raise ValueError('Atelier checksum mismatch: '+key)
        with Image.open(source) as image,Image.open(destination) as current:
            if image.mode!='RGBA' or image.getchannel('A').getbbox() is None:raise ValueError('Empty or non-RGBA Atelier source: '+key)
            if image.size!=(entry.get('width'),entry.get('height')):raise ValueError('Atelier manifest dimensions differ: '+key)
            if image.size!=current.size:
                if group in RIG:raise ValueError('Atelier rig does not match generated equipment dimensions: '+key)
                skipped.append({'key':key,'reason':'Different dimensions; preserve authored collision alignment'});continue
            animated=group in RIG or group=='mobs'
            if animated:
                size=image.width//8
                if image.width%8 or image.height!=size*24 or size not in (64,128):raise ValueError('Invalid Atelier animation grid: '+key)
                alpha=image.getchannel('A')
                for row in range(24):
                    for frame in range(8):
                        if alpha.crop((frame*size,row*size,(frame+1)*size,(row+1)*size)).getbbox() is None:
                            raise ValueError(f'Blank Atelier animation frame: {key}/{row}/{frame}')
        selected.append((key,source,digest))
    rig_keys={key for key in keys if key.split('/')[0] in RIG}
    if not rig_keys.issubset({key for key,_,_ in selected}):raise ValueError('Refuse a mixed humanoid rig')
    return selected,skipped


def install_authored_hero(library:Path,output:Path)->None:
    source=library.parent/'authored/player/hero.png'
    target=safe_path(output,'people/hero')
    if not source.is_file():
        target.unlink(missing_ok=True)
        return
    with Image.open(source) as image:
        rgba=image.convert('RGBA')
        if rgba.size!=(512,1536) or rgba.getchannel('A').getbbox() is None:
            raise ValueError('Authored hero must be a non-empty 512x1536 sprite sheet')
        alpha=rgba.getchannel('A')
        for row in range(24):
            for frame in range(8):
                if alpha.crop((frame*64,row*64,(frame+1)*64,(row+1)*64)).getbbox() is None:
                    raise ValueError(f'Blank authored hero frame: {row}/{frame}')
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:
        raise ValueError('Authored hero bytes changed while copying')


def integrate(library:Path,output:Path,keys:list[str])->dict:
    library=library.resolve();output=output.resolve()
    if output==library or library.is_relative_to(output) or output.is_relative_to(library):
        raise ValueError('Atelier source and generated output must be separate directories')
    selected,skipped=plan(library,output,keys)
    # Validate the entire cohort first. No corrupt or incompatible member is copied.
    with tempfile.TemporaryDirectory(prefix='.atelier-stage-',dir=output.parent) as stage_name:
        stage=Path(stage_name)
        for key,source,digest in selected:
            target=safe_path(stage,key);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest:raise ValueError('Staged Atelier bytes changed: '+key)
        for key,_,_ in selected:
            target=safe_path(output,key);target.parent.mkdir(parents=True,exist_ok=True)
            safe_path(stage,key).replace(target)
    install_authored_hero(library,output)
    counts=dict(sorted(Counter(key.split('/')[0] for key,_,_ in selected).items()))
    report={'schema':1,'source':'atelier/Assets','source_manifest_sha256':hashlib.sha256((library/'manifest.json').read_bytes()).hexdigest(),
            'integrated':len(selected),'groups':counts,'skipped':skipped,'rig':'complete Atelier people/equipment/NPC cohort',
            'catalog_ids_changed':False,'independent_gear_ladder_imported':False,'visual_approval':'not_granted_by_integrity_checks',
            'assets':[{'key':key,'sha256':digest} for key,_,digest in selected]}
    (output/'atelier-integration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'ATELIER_CREDITS.txt').write_text((library/'CREDITS.txt').read_text(encoding='utf-8'),encoding='utf-8')
    print('ATELIER INTEGRATION:',len(selected),'catalog assets;',counts,'; fallback:',len(skipped),flush=True)
    return report
