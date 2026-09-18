"""Integrate checked-in Atelier catalog art without changing gameplay records.

Wayfarer owns every active player, equipment-overlay, NPC and mob frame.
Those actor groups are deliberately never copied from the historical Atelier
binary library, so clean regeneration cannot silently restore rejected sprites.
Atelier remains available for compatible non-actor world and icon artwork.
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
ACTOR_GROUPS=frozenset({'people','equipment','npcs','mobs'})
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
        if key in entries: raise ValueError('Duplicate Atelier manifest key: '+key)
        entries[key]=entry
    if len(keys)!=len(set(keys)): raise ValueError('Duplicate output asset key')
    selected=[];skipped=[]
    for key in sorted(keys):
        group=PurePosixPath(key).parts[0]
        if group not in GROUPS: continue
        destination=safe_path(output,key)
        if not destination.is_file():
            raise ValueError('Project asset generator did not create required runtime asset: '+key)
        if group in ACTOR_GROUPS:
            with Image.open(destination) as current:
                if current.mode!='RGBA' or current.getchannel('A').getbbox() is None:
                    raise ValueError('Wayfarer actor output is empty or non-RGBA: '+key)
                size=current.width//8
                if current.width%8 or current.height!=size*24 or size not in (64,128):
                    raise ValueError('Wayfarer actor grid is invalid: '+key)
                alpha=current.getchannel('A')
                for row in range(24):
                    for frame in range(8):
                        if alpha.crop((frame*size,row*size,(frame+1)*size,(row+1)*size)).getbbox() is None:
                            raise ValueError(f'Blank Wayfarer actor frame: {key}/{row}/{frame}')
            skipped.append({'key':key,'reason':'Wayfarer runtime actor source owns this key; historical Atelier actor bytes are inactive'})
            continue
        source=safe_path(library,key)
        if key not in entries or not source.is_file():
            skipped.append({'key':key,'reason':'No matching Atelier source; keep generated project art'}); continue
        entry=entries[key]
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=entry.get('sha256'): raise ValueError('Atelier checksum mismatch: '+key)
        with Image.open(source) as image,Image.open(destination) as current:
            if image.mode!='RGBA' or image.getchannel('A').getbbox() is None: raise ValueError('Empty or non-RGBA Atelier source: '+key)
            if image.size!=(entry.get('width'),entry.get('height')): raise ValueError('Atelier manifest dimensions differ: '+key)
            if image.size!=current.size:
                skipped.append({'key':key,'reason':'Different dimensions; preserve authored collision alignment'}); continue
        selected.append((key,source,digest))
    return selected,skipped


def retire_authored_hero(output:Path)->None:
    # The former single-sheet hero is historical source only. Player appearance
    # now always composes the Wayfarer body/hair/equipment rig.
    safe_path(output,'people/hero').unlink(missing_ok=True)


def integrate(library:Path,output:Path,keys:list[str])->dict:
    library=library.resolve(); output=output.resolve()
    if output==library or library.is_relative_to(output) or output.is_relative_to(library):
        raise ValueError('Atelier source and generated output must be separate directories')
    selected,skipped=plan(library,output,keys)
    with tempfile.TemporaryDirectory(prefix='.atelier-stage-',dir=output.parent) as stage_name:
        stage=Path(stage_name)
        for key,source,digest in selected:
            target=safe_path(stage,key); target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(source,target)
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest: raise ValueError('Staged Atelier bytes changed: '+key)
        for key,_,_ in selected:
            target=safe_path(output,key); target.parent.mkdir(parents=True,exist_ok=True); safe_path(stage,key).replace(target)
    retire_authored_hero(output)
    counts=dict(sorted(Counter(key.split('/')[0] for key,_,_ in selected).items()))
    coverage=dict(sorted(Counter(key.split('/')[0] for key in keys if key.split('/')[0] in GROUPS).items()))
    actor_skips=[entry for entry in skipped if entry['key'].split('/')[0] in ACTOR_GROUPS]
    expected_actor_count=sum(1 for key in keys if key.split('/')[0] in ACTOR_GROUPS)
    if len(actor_skips)!=expected_actor_count:
        raise ValueError('An actor key unexpectedly entered the historical Atelier copy path')
    report={'schema':3,'source':'atelier/Assets','source_manifest_sha256':hashlib.sha256((library/'manifest.json').read_bytes()).hexdigest(),
            'integrated':len(selected),'groups':counts,'coverage':coverage,'skipped':skipped,
            'actor_runtime_source':'Wayfarer original joint construction','actor_historical_fallbacks':0,
            'historical_actor_bytes_active':False,'catalog_ids_changed':False,'independent_gear_ladder_imported':False,
            'visual_approval':'not_granted_by_integrity_checks','assets':[{'key':key,'sha256':digest} for key,_,digest in selected]}
    (output/'atelier-integration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (output/'ATELIER_CREDITS.txt').write_text((library/'CREDITS.txt').read_text(encoding='utf-8'),encoding='utf-8')
    print('ATELIER INTEGRATION:',len(selected),'historical non-actor catalog assets;',counts,'; runtime coverage:',coverage,'; generated/inactive skips:',len(skipped),'; Wayfarer actor fallbacks: 0',flush=True)
    return report
