#!/usr/bin/env python3
"""Temporary, inactive renderer review. Does not modify runtime routing."""
from pathlib import Path
import json, hashlib, sys
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from art.characters import body_frame,hair_frame,armour_frame,npc_frame,layer_order
from art.character_motion import rig,STATES

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
    d.text((20,12),'WAYFARER / NATIVE RENDERER REVIEW — NOT AN IN-GAME SCREENSHOT',fill='#e6d8b5')
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
    errors=[]; checked=0
    def verify(label,render):
        nonlocal checked
        for state in STATES:
            for direction in range(4):
                for f in range(8):
                    try:
                        im=render(state,f,direction); box=im.getchannel('A').getbbox()
                        if im.size!=(64,64) or im.mode!='RGBA' or box is None:raise ValueError('blank/wrong frame')
                        if box and (box[0]==0 or box[1]==0 or box[2]==64 or box[3]==64):raise ValueError('cell boundary touched: '+str(box))
                        checked+=1
                    except Exception as exc:
                        if len(errors)<100:errors.append(f'{label}/{state}/{direction}/{f}: {exc}')
    for body in range(2):
        for skin in range(6):verify(f'body_{body}_{skin}',lambda s,f,d,b=body,k=skin:body_frame(b,k,s,f,d))
    for style in range(6):
        for color in range(8):verify(f'hair_{style}_{color}',lambda s,f,d,a=style,c=color:hair_frame(a,c,s,f,d))
    for item in data['items']:
        if item.get('slot'):verify(item['id'],lambda s,f,d,i=item:armour_frame(i,s,f,d))
    for role in sorted({n['role'] for n in data['npcs']}):verify(role,lambda s,f,d,r=role:npc_frame(r,s,f,d))
    for state in STATES:
        for f in range(8):
            j=rig(state,f,0)
            if state=='walk' and min(abs(j['foot_l'][1]-55),abs(j['foot_r'][1]-55))!=0:errors.append('No support foot in walk')
    report={'checkedFrames':checked,'errors':errors,'runtimeIntegrated':False,'artisticApproval':False,
            'sourceHashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools/art/characters.py',ROOT/'tools/art/character_motion.py')}}
    (out/'stage-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
