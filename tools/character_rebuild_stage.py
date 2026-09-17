#!/usr/bin/env python3
"""Inactive replacement review. It never changes runtime source ownership."""
from pathlib import Path
import json, hashlib, sys
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT))
from art.characters import body_frame,hair_frame,armour_frame,npc_frame,layer_order
from art.character_motion import rig,STATES
from art.wildlife import frame as creature_frame


def main():
    data=json.loads((ROOT/'content/catalog.json').read_text())
    out=ROOT/'docs/art/character-rebuild';out.mkdir(parents=True,exist_ok=True)
    items={x['id']:x for x in data['items']}
    def person(cls,state,frame,direction,skin=1,hair=0):
        layers={'body':body_frame(0,skin,state,frame,direction),'hair':hair_frame(0,hair,state,frame,direction)}
        for key in ('weapon','armor'):
            item=items[cls[key]];layers[item['slot']]=armour_frame(item,state,frame,direction)
        result=Image.new('RGBA',(64,64))
        for slot in layer_order(direction):
            if slot in layers:result.alpha_composite(layers[slot])
        return result
    classes=data['classes']
    board=Image.new('RGBA',(136*len(classes),620),'#171e2a');d=ImageDraw.Draw(board)
    d.text((20,12),'WAYFARER / NATIVE RENDERER REVIEW - NOT AN IN-GAME SCREENSHOT',fill='#e6d8b5')
    for i,cls in enumerate(classes):
        d.text((i*136+12,42),cls['name'][:18],fill='#e6d8b5')
        for direction in range(4):
            im=person(cls,'idle',0,direction,i%6,i%8).resize((128,128),Image.Resampling.NEAREST)
            board.alpha_composite(im,(i*136+4,70+direction*136))
    board.save(out/'heroes.png',optimize=True)
    board=Image.new('RGBA',(8*128+100,6*112+40),'#171e2a');d=ImageDraw.Draw(board)
    for row,state in enumerate(STATES):
        d.text((8,row*112+56),state,fill='#e6d8b5')
        for frame in range(8):
            im=person(classes[0],state,frame,2).resize((112,112),Image.Resampling.NEAREST)
            board.alpha_composite(im,(100+frame*128,row*112+20))
    board.save(out/'motion.png',optimize=True)
    errors=[]; checked=0; shapes={}
    def verify(label,render,size=64):
        nonlocal checked
        alpha=hashlib.sha256()
        for state in STATES:
            for direction in range(4):
                for f in range(8):
                    try:
                        im=render(state,f,direction); box=im.getchannel('A').getbbox()
                        if im.size!=(size,size) or im.mode!='RGBA' or box is None:raise ValueError('blank/wrong frame')
                        if box and (box[0]==0 or box[1]==0 or box[2]==size or box[3]==size):raise ValueError('cell boundary touched: '+str(box))
                        alpha.update(im.getchannel('A').tobytes());checked+=1
                    except Exception as exc:
                        if len(errors)<200:errors.append(f'{label}/{state}/{direction}/{f}: {exc}')
        return alpha.hexdigest()
    for body in range(2):
        for skin in range(6):verify(f'body_{body}_{skin}',lambda s,f,d,b=body,k=skin:body_frame(b,k,s,f,d))
    for style in range(6):
        for color in range(8):verify(f'hair_{style}_{color}',lambda s,f,d,a=style,c=color:hair_frame(a,c,s,f,d))
    for item in data['items']:
        if item.get('slot'):verify(item['id'],lambda s,f,d,i=item:armour_frame(i,s,f,d))
    for role in sorted({n['role'] for n in data['npcs']}):verify(role,lambda s,f,d,r=role:npc_frame(r,s,f,d))
    creature_board=Image.new('RGBA',(10*160,((len(data['mobs'])+9)//10)*170),'#171e2a');cd=ImageDraw.Draw(creature_board)
    for i,mob in enumerate(data['mobs']):
        size=128 if mob.get('boss') else 64
        digest=verify(mob['id'],lambda s,f,d,m=mob:creature_frame(m,s,f,d),size)
        if not mob.get('boss') and not mob.get('elite'):shapes.setdefault(digest,[]).append(mob['id'])
        try:
            im=creature_frame(mob,'idle',0,2)
            if size==64:im=im.resize((128,128),Image.Resampling.NEAREST)
            x=(i%10)*160;y=(i//10)*170;creature_board.alpha_composite(im,(x+16,y+4));cd.text((x+3,y+140),mob['id'][:24],fill='#e6d8b5')
        except Exception:pass
    creature_board.save(out/'creatures.png',optimize=True)
    duplicates=[v for v in shapes.values() if len(v)>1]
    if duplicates:errors.append('Duplicate creature silhouettes: '+repr(duplicates))
    for state in STATES:
        for f in range(8):
            j=rig(state,f,0)
            if state=='walk' and min(abs(j['foot_l'][1]-55),abs(j['foot_r'][1]-55))!=0:errors.append('No support foot in walk')
    report={'checkedFrames':checked,'errors':errors,'duplicateCreatureSilhouettes':duplicates,'runtimeIntegrated':False,'artisticApproval':False,
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools/art/characters.py',ROOT/'tools/art/character_motion.py',ROOT/'tools/art/wildlife.py')}}
    (out/'stage-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
