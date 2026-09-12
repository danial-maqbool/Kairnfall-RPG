#!/usr/bin/env python3
"""Validate asset references and animation files without claiming visual approval."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import wave
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'client/Assets'
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT))
from content_src.presentation import FURNITURE
from art.common import STATES,DIRECTIONS
from art.environment_pack import TERRAINS,PROPS


def main():
    manifest=json.loads((ASSETS/'manifest.json').read_text(encoding='utf-8'))
    catalog=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
    errors=[]; warnings=[]; checks=0; checked_frames=0
    def check(condition,message):
        nonlocal checks
        checks+=1
        if not condition: errors.append(message)
    entries=manifest['assets']; keys=[entry['key'] for entry in entries]; key_set=set(keys)
    check(len(key_set)==len(keys),'Duplicate keys in manifest.')
    check(manifest['artistic_review']=='not_approved','File validation must not silently grant visual approval.')
    check(manifest['frame_order']==list(STATES),'Animation state order differs from the client.')
    check(manifest['directions']==list(DIRECTIONS),'Direction order differs from the client.')
    check(manifest['frames_per_row']==8,'The client requires eight columns per animation sheet.')
    expected={f'terrain/{terrain}_{n}' for terrain in TERRAINS for n in range(4)}
    expected.update('props/'+name for name in PROPS)
    expected.update('furnishings/'+name for name in FURNITURE)
    expected.update('terrain/grass_edge_'+str(mask) for mask in range(1,16))
    expected.update('furnishings/'+f['kind'] for z in catalog['zones'] for f in z.get('furnishings',[]))
    expected.update('items/'+item['id'] for item in catalog['items'])
    expected.update('equipment/'+item['id'] for item in catalog['items'] if item.get('slot'))
    expected.update('structures/'+item['id'] for item in catalog['items'] if item['type']=='structure')
    expected.update('abilities/'+a['id'] for a in catalog['abilities'])
    expected.update('skills/'+skill['id'] for skill in catalog['skills'])
    expected.update('resources/'+r['id'] for r in catalog['resources'])
    expected.add('resources/crop_wheat')
    expected.update('mobs/'+m['id'] for m in catalog['mobs'])
    expected.update('npcs/'+n['role'] for n in catalog['npcs'])
    expected.update(f'people/body_{body}_{skin}' for body in range(2) for skin in range(6))
    expected.update(f'people/hair_{hair}_{colour}' for hair in range(6) for colour in range(8))
    expected.update('buildings/'+z['id']+'/'+b['id'] for z in catalog['zones'] for b in z['buildings'])
    expected.update('chests/'+kind+'_'+state for kind in ['weathered','locked','ancient','runic','royal','cursed','mimic'] for state in ['open','closed'])
    for key in sorted(expected): check(key in key_set,'Required client reference is absent: '+key)
    check((ASSETS/'catalog.json').read_bytes()==(ROOT/'content/catalog.json').read_bytes(),'Client and server catalogs differ.')
    alpha_fingerprints={}; rgb_fingerprints={}
    normal_species={m['id'] for m in catalog['mobs'] if not m['boss'] and not m['elite']}
    for entry in entries:
        key=entry['key']; path=(ASSETS/(key+'.png')).resolve()
        safe=not any(part in {'','.','..'} for part in key.split('/')) and '\\' not in key and path.is_relative_to(ASSETS.resolve())
        check(safe,'Unsafe asset path: '+key)
        if not safe: continue
        if not path.is_file(): check(False,'Missing PNG: '+key); continue
        check(hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'],'PNG checksum differs: '+key)
        with Image.open(path) as image:
            check(image.mode=='RGBA','PNG is not RGBA: '+key)
            check(image.size==(entry['width'],entry['height']),'Recorded image size differs: '+key)
            if key.startswith('furnishings/'):
                definition=FURNITURE.get(key.split('/',1)[1])
                check(definition is not None,'Unknown furnishing asset: '+key)
                if definition is not None:
                    width,height,rise,_,_=definition
                    check(image.size==(width*32,height*32+rise),'Furnishing art differs from the authoritative footprint: '+key)
            alpha=image.getchannel('A')
            check(alpha.getbbox() is not None,'Completely transparent PNG: '+key)
            if entry['animated']:
                size=image.width//8
                check(image.width%8==0 and image.height==24*size,'Invalid animation grid: '+key)
                # Equipment can be hidden by occlusion. Standalone actors must remain visible.
                if key.startswith(('mobs/','npcs/','people/body_')):
                    for row in range(24):
                        for column in range(8):
                            checked_frames+=1
                            bounds=(column*size,row*size,(column+1)*size,(row+1)*size)
                            check(alpha.crop(bounds).getbbox() is not None,f'Invisible actor frame: {key}, row {row}, frame {column}')
                if key.startswith('mobs/') and key[5:] in normal_species:
                    alpha_hash=hashlib.sha256(alpha.tobytes()).hexdigest()
                    rgb_hash=hashlib.sha256(image.tobytes()).hexdigest()
                    alpha_fingerprints.setdefault(alpha_hash,[]).append(key[5:])
                    rgb_fingerprints.setdefault(rgb_hash,[]).append(key[5:])
    duplicate_shapes=[ids for ids in alpha_fingerprints.values() if len(ids)>1]
    duplicate_images=[ids for ids in rgb_fingerprints.values() if len(ids)>1]
    check(not duplicate_shapes,'Normal species share exact animation silhouettes. Replace duplicate anatomy before integration.')
    check(not duplicate_images,'Normal species share identical complete animation images. These are not distinct species assets.')
    from audio_quality_audit import EXPECTED as AUDIO_EXPECTED
    audio_names=set(AUDIO_EXPECTED)
    for key in sorted(audio_names):
        path=ASSETS/'audio'/(key+'.wav')
        if not path.is_file(): check(False,'Missing audio: '+key); continue
        with wave.open(str(path),'rb') as audio:
            check(audio.getnchannels()==1 and audio.getsampwidth()==2,'Unsupported audio format: '+key)
            check(audio.getframerate()==22050 and audio.getnframes()>100,'Empty or invalid audio: '+key)
    report={'technical_checks':checks,'passed':checks-len(errors),'failed':len(errors),'actor_frames_checked':checked_frames,'required_image_keys':len(expected),'generated_image_files':len(entries),'required_skill_icons':len(catalog['skills']),'required_audio_files':len(audio_names),'errors':errors,'warnings':warnings,'duplicate_normal_species_silhouettes':duplicate_shapes,'identical_normal_species_images':duplicate_images,'visual_review':'not_performed','visual_acceptance':'not_approved','audio_review':'not_performed','gameplay_acceptance':'not_tested_by_this_tool'}
    target=ROOT/'artifacts/test-results/asset-structure.json'; target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if errors: raise SystemExit(1)
    print('ASSET STRUCTURE PASSED. Visual, audio, and gameplay acceptance remain separate and unapproved.')

if __name__=='__main__': main()
