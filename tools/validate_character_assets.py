#!/usr/bin/env python3
"""Validate Wayfarer source ownership, pose grids, motion and retired-byte removal.

This is technical evidence. Image counts and uniqueness do not confer artistic approval.
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from PIL import Image, ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from art.character_motion import STATES,EXTRA_STATES,rig
from art.characters import body_frame,hair_frame,armour_frame,npc_frame,layer_order
from art.wildlife import frame as creature_frame


def expected(data):
    base={f'people/body_{b}_{s}' for b in range(2) for s in range(6)}
    base.update(f'people/hair_{h}_{c}' for h in range(6) for c in range(8))
    base.update('equipment/'+i['id'] for i in data['items'] if i.get('slot'))
    base.update('npcs/'+n['role'] for n in data['npcs'])
    base.update('mobs/'+m['id'] for m in data['mobs'])
    extra={f'motions/{state}/{key}' for state in EXTRA_STATES for key in base if not key.startswith('mobs/')}
    return base,extra


def main():
    assets=ROOT/'client/Assets'
    data=json.loads((ROOT/'content/catalog.json').read_text())
    manifest=json.loads((assets/'manifest.json').read_text())
    entries={e['key']:e for e in manifest['assets']}
    base,extra=expected(data);keys=base|extra
    errors=[];checks=0;frames=0;motions=0;replaced=0
    def need(ok,message):
        nonlocal checks
        checks+=1
        if not ok and len(errors)<150:errors.append(message)
    need(manifest.get('motion_order')==list(EXTRA_STATES),'Additional motion order differs from the renderer.')
    report=json.loads((assets/'atelier-integration.json').read_text())
    need(report.get('actor_runtime_source')=='Wayfarer original joint construction','The active actor source is not Wayfarer.')
    need(report.get('actor_historical_fallbacks')==0,'Historical actor fallback is enabled.')
    need(not any(e['key'].split('/')[0] in {'people','equipment','npcs','mobs'} for e in report.get('assets',[])),'The non-actor library copied an actor.')
    actual={key for key in entries if key.split('/')[0] in {'people','equipment','npcs','mobs','motions'}}
    need(actual==keys,'Actor keys differ: '+repr(sorted(actual^keys)[:20]))
    old=json.loads((ROOT/'art/wayfarer/retired-actors.json').read_text())
    old_by_key={e['key']:e for e in old['assets']}
    for name in old.get('removed_files',[]):need(not (ROOT/name).exists(),'Retired actor artifact reappeared: '+name)
    for group in ('people','equipment','npcs','mobs','gear_worn'):
        need(not list((ROOT/'atelier/Assets'/group).rglob('*.png')),'Historical actor directory is not empty: '+group)
    equipment={i['id']:i for i in data['items'] if i.get('slot')};normal={m['id'] for m in data['mobs'] if not m['boss'] and not m['elite']}
    alpha_hashes={};image_hashes={}
    for key in sorted(keys):
        path=assets/(key+'.png')
        if not path.is_file():need(False,'Missing actor '+key);continue
        entry=entries[key];size=128 if key.startswith('mobs/') and next(m for m in data['mobs'] if m['id']==key[5:]).get('boss') else 64
        count=1 if key.startswith('motions/') else len(STATES)
        image=Image.open(path).convert('RGBA');alpha=image.getchannel('A')
        need(image.size==(size*8,size*4*count),'Wrong actor grid: '+key)
        need(entry.get('state_count',6)==count,'Wrong state metadata: '+key)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        need(digest==entry['sha256'],'Manifest digest mismatch: '+key)
        if key in old_by_key:
            historical=old_by_key[key]
            need(digest not in {historical.get('grounded_sha256'),historical.get('atelier_sha256')},'Retired actor bytes survived: '+key)
            replaced+=1
        for row in range(4*count):
            for column in range(8):
                box=alpha.crop((column*size,row*size,(column+1)*size,(row+1)*size)).getbbox();frames+=1
                need(box is not None,'Empty actor cell: '+key+f'/{row}/{column}')
                if box:need(box[0]>0 and box[1]>0 and box[2]<size and box[3]<size,'Actor touches a cell boundary: '+key+f'/{row}/{column}')
        if key.startswith('mobs/') and key[5:] in normal:
            alpha_hashes.setdefault(hashlib.sha256(alpha.tobytes()).hexdigest(),[]).append(key)
            image_hashes.setdefault(hashlib.sha256(image.tobytes()).hexdigest(),[]).append(key)
        if key in base:
            # Compare within the same direction: changing a facing row is not motion.
            group=key.split('/')[0];slot=equipment.get(key.split('/',1)[1],{}).get('slot','')
            states=('walk','attack','cast','hit','death') if group in ('people','npcs') else ('walk','attack','cast','hit','death') if group=='mobs' else ('walk','attack','hit','death') if slot in ('weapon','offhand','chest','helmet','cloak','gloves') else ('walk','death') if slot in ('legs','boots') else ()
            for state in states:
                for direction in range(4):
                    row=STATES.index(state)*4+direction
                    idle=image.crop((0,direction*size,size,(direction+1)*size))
                    changed=max(sum(any(channel for channel in pixel) for pixel in ImageChops.difference(idle,image.crop((f*size,row*size,(f+1)*size,(row+1)*size))).getdata()) for f in (2,3,4,7))
                    # A single noise pixel is not an animation. Small equipment retains its scale.
                    threshold=4 if group=='equipment' else 8
                    need(changed>=threshold,'No meaningful '+state+' motion in direction '+str(direction)+': '+key);motions+=1
            if group in ('npcs','mobs') or key.startswith('people/body_'):
                for direction in range(4):
                    idle=image.crop((0,direction*size,size,(direction+1)*size))
                    dead=image.crop((7*size,(20+direction)*size,8*size,(21+direction)*size))
                    for angle in (90,180,270):need(dead.tobytes()!=idle.rotate(angle).tobytes(),'Death is a rotated standing raster: '+key)
        image.close()
    for label,lookup in (('silhouette',alpha_hashes),('complete frame set',image_hashes)):
        duplicates=[v for v in lookup.values() if len(v)>1]
        need(not duplicates,'Normal species share a '+label+': '+repr(duplicates))
    for direction in range(4):
        order=layer_order(direction);need(len(order)==len(set(order)) and 'ring' in order,'Duplicate/missing layer in direction '+str(direction))
        for f in range(8):
            j=rig('walk',f,direction)
            need(j['foot_l'][1]==55 or j['foot_r'][1]==55,'Walking has no grounded support foot.')
        j=rig('bow_attack',3,direction)
        need(j['hand_l']!=j['hand_r'],'A drawn bow needs distinct grip and string hands.')
    # Re-render sampled source cells and compare them with the actual runtime atlas.
    for state,direction,f in (('idle',0,0),('walk',2,3),('attack',1,4),('death',3,7),('interact',0,3),('craft',2,4),('run',1,2),('bow_attack',2,3),('crossbow_attack',2,3)):
        samples=[('people/body_0_2',lambda:body_frame(0,2,state,f,direction)),('people/hair_4_3',lambda:hair_frame(4,3,state,f,direction))]
        for key,render in samples:
            extra_state=state in EXTRA_STATES;path=assets/(f'motions/{state}/{key}.png' if extra_state else key+'.png');row=direction if extra_state else STATES.index(state)*4+direction
            with Image.open(path) as sheet:cell=sheet.crop((f*64,row*64,(f+1)*64,(row+1)*64))
            need(cell.tobytes()==render().tobytes(),'Runtime pixels do not match the retained source: '+key+'/'+state)
    value={'validation_revision':1,'actor_runtime_source':'Wayfarer original joint construction','checks':checks,
           'base_sheets':len(base),'additional_motion_sheets':len(extra),'actor_sheets':len(keys),
           'frame_cells_checked':frames,'meaningful_motion_checks':motions,'historical_hashes_replaced':replaced,
           'actor_historical_fallbacks':0,'errors':errors,'passed':not errors,
           'artistic_approval':False,'native_rendering':'not_asserted_by_this_validator','release_approval':False}
    target=ROOT/'artifacts/test-results/character-assets.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
