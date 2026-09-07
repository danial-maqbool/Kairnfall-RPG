"""Anatomical creature atlas source. Generated frames require visual acceptance."""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, palette, shade, seed, finish_frame, INK
from .people import npc_frame
from .environment import chest

FUR={'rat':'9b8d7e','mouse':'ae9b85','hare':'b29c7d','fox':'b77b50','wolf':'89908c','boar':'827162','weasel':'a38466','deer':'b08b66','stag':'8e8062','bear':'676564','polar_bear':'c9ceba','wolverine':'806d57','badger':'8e8b82','goat':'aea38a','ibex':'a8947c','leopard':'b7bab0','ox':'776d62','hound':'a6b3b6','arctic_fox':'c5c7b8','horse':'bcb5a3','jackal':'b6ad90','monkey':'967d65','armadillo':'aa9c8a'}

def quadruped(spec, state, frame, direction):
    family=spec.get('family','wolf'); text=spec.get('anatomy','').lower(); im=canvas(); p=Pixel(im)
    c=palette(FUR.get(family,'9b8b73')); moving=state=='walk'; step=math.sin(frame/8*math.tau) if moving else 0
    side=direction in (1,2); back=direction==3
    small=family in {'rat','mouse','hare','weasel','fox','arctic_fox','badger'}
    tall=family in {'deer','stag','goat','ibex','horse','ox','hound'}
    heavy=family in {'bear','polar_bear','boar','ox','wolverine','owlbear','tortoise','turtle','armadillo'}
    top=28 if small else 20 if heavy else 22
    bottom=44; leg=5 if small else 12 if tall else 9
    rearx,frontx=(20,41) if side else (24,39)
    # Far limbs are drawn before the rib cage; near limbs follow it.
    for x,phase in [(rearx+1,1),(frontx-2,-1),(rearx-2,-1),(frontx+2,1)]:
        yy=bottom-2+(2 if phase>0 else 0); foot=(x+round(step*3*phase),bottom+leg-round(step*2*phase))
        p.limb((x,yy),(x+phase*2,yy+leg*.55),4 if heavy else 3,c[2]); p.limb((x+phase*2,yy+leg*.55),foot,3,c[3]); p.line([(foot[0]-2,foot[1]),(foot[0]+3,foot[1])],c[0],2)
    tail=[(rearx-4,bottom-4),(rearx-12,bottom-10+round(step*2)),(rearx-15,bottom-19)]
    if family in {'rat','mouse','weasel','monkey'}: p.line(tail,'806c68',3); p.line([(x-1,y) for x,y in tail],'b79b8c')
    elif family not in {'boar','bear','polar_bear','hare','ox'}:
        p.limb(tail[0],tail[1],7 if 'fox' in family else 5,c[2]); p.limb(tail[1],tail[2],4,c[3]); p.line([tail[-2],tail[-1]],'c5bba5' if 'fox' in family else c[4],2)
    p.sphere((13 if side else 20,top,46 if side else 44,bottom+3),c[3]);
    # Shoulder, back line, belly, and coat clusters make the anatomy readable.
    p.line([(18,top+5),(26,top+2),(34,top+4)],c[4],2); p.line([(22,bottom),(33,bottom+1),(39,bottom-2)],c[1],2)
    for n in range(14):
        x=19+(n*7)%22; y=top+5+(n*11)%max(2,bottom-top-8)
        p.line([(x,y),(x+2,y+1)],c[4] if n%3 else c[1])
    hx,hy=(46,top+6) if side else (32,top-3 if back else bottom-4)
    if family=='weasel': hy+=3
    if family=='polar_bear': p.limb((40,top+8),(hx+2,hy-3),9,c[3]); hx+=2
    radius=8 if heavy else 6
    p.sphere((hx-radius,hy-radius,hx+radius,hy+radius+2),c[3])
    if family in {'hare'}:
        for dx in (-4,3): p.limb((hx+dx,hy-4),(hx+dx+2,hy-20),4,c[3]); p.line([(hx+dx,hy-8),(hx+dx+2,hy-17)],'c19d97')
        p.sphere((16,35,29,47),c[3])
    elif family in {'deer','stag','goat','ibex','ox'}:
        for s in (-1,1):
            horn=[(hx+s*4,hy-5),(hx+s*8,hy-13),(hx+s*6,hy-19)]
            if family=='ox': horn=[(hx+s*5,hy-3),(hx+s*12,hy-7),(hx+s*11,hy-12)]
            p.line(horn,'4a4b40',3); p.line(horn,'b9b294')
            if family in {'deer','stag'}:
                for off in (10,15): p.line([(hx+s*7,hy-off),(hx+s*12,hy-off-3)],'b9b294',2)
        if family=='goat': p.poly([(hx-3,hy+7),(hx+3,hy+7),(hx,hy+15)],'c4bf9f')
    elif family in {'wolf','fox','arctic_fox','jackal','leopard'}:
        for dx in (-4,4): p.poly([(hx+dx-3,hy-4),(hx+dx-2,hy-13),(hx+dx+4,hy-6)],c[3]); p.line([(hx+dx-1,hy-7),(hx+dx-1,hy-10)],c[1])
    elif family=='hound':
        for dx in (-6,6): p.limb((hx+dx,hy-4),(hx+dx,hy+7),4,c[1])
    else:
        for dx in (-radius+1,radius-1): p.sphere((hx+dx-3,hy-8,hx+dx+3,hy-2),c[3])
    if not back:
        snoutx=hx+5 if side else hx; snouty=hy+3 if side else hy+5
        p.sphere((snoutx-4,snouty-2,snoutx+6 if side else snoutx+4,snouty+4),c[4]); p.dot(snoutx+5 if side else snoutx,snouty+2,c[0])
        for dx in ((1,) if side else (-3,3)): p.dot(hx+dx,hy-1,'202b2c'); p.dot(hx+dx-1,hy-2,'dcd4b4')
        if family=='boar':
            for dx in (-4,4): p.poly([(hx+dx,hy+6),(hx+dx+2,hy+1),(hx+dx+3,hy+8)],'d6c6a0')
    if family in {'badger','wolverine'}:
        p.line([(hx-4,hy-6),(hx-2,hy+4)],c[0],2); p.line([(hx+3,hy-5),(hx+2,hy+3)],c[0],2)
    if family=='leopard':
        for x,y in [(20,30),(25,26),(31,31),(37,27),(29,38),(18,36)]: p.ellipse((x-1,y-1,x+2,y+1),c[3],c[0])
    if family in {'tortoise','turtle','armadillo'}:
        shell=palette('859078' if family!='armadillo' else '9a907e'); p.sphere((13,20,44,44),shell[3])
        for x in range(18,44,7): p.line([(x,24),(x-2,32),(x+1,40)],shell[1]); p.line([(x+1,25),(x-1,32)],shell[4])
    if 'undead' in text:
        for x in range(20,40,5): p.line([(x,top+5),(x+2,top+12),(x,bottom-2)],'d7cfb2',2)
        p.line([(19,top+3),(40,top+4)],'d7cfb2',2)
    if state=='attack':
        p.line([(hx+5,hy+4),(hx+9+frame%3,hy+7)],'644441',2)
    return im


def insect(spec,state,frame,direction):
    im=canvas(); p=Pixel(im); family=spec.get('family','beetle'); text=spec.get('anatomy','').lower(); gait=math.sin(frame/8*math.tau) if state=='walk' else 0
    spider='spider' in text or family in {'tick','automaton'}; crab='crab' in text; scorpion=family=='scorpion'; many=family=='centipede'
    c=palette('aa915d' if 'gilded' in spec['id'] or family=='automaton' else '7c8b83' if 'crystal' in text else '7f685d')
    legs=4 if spider or crab or scorpion else 8 if many else 3
    for n in range(legs):
        y=25+n*(3 if many else 5); yy=y+round(gait*(3 if n%2 else -3))
        for s in (-1,1):
            a=(32+s*6,y); elbow=(32+s*(18-(n%2)*2),yy-7); foot=(32+s*(23-(n%2)*3),yy+8)
            p.limb(a,elbow,2,c[2]); p.limb(elbow,foot,2,c[3]); p.dot(foot[0],foot[1],c[5])
    if many:
        for n in range(8): p.sphere((25,15+n*4,39,24+n*4),c[3]); p.line([(28,20+n*4),(36,20+n*4)],c[1])
    else:
        p.sphere((20,27,44,48),c[3]); p.sphere((24,19,40,34),c[2]); p.sphere((26,12,38,25),c[3])
    if 'beetle' in text or family=='scarab':
        p.line([(32,29),(32,46)],c[0]); p.line([(25,32),(24,39)],c[5]); p.line([(38,32),(40,40)],c[1])
    if spider:
        for x,y in [(28,18),(32,16),(36,18),(30,20),(34,20)]: p.dot(x,y,'cc9f74')
        for s in (-1,1): p.line([(32+s*3,14),(32+s*5,8),(32+s*2,7)],'d9c4a0',2)
    else:
        for s in (-1,1): p.line([(32+s*3,15),(32+s*9,7),(32+s*13,10)],c[4]); p.dot(32+s*4,19,INK)
    if crab or scorpion:
        for s in (-1,1):
            x=32+s*19; y=14+round(gait*2); p.limb((32+s*6,26),(x,y+7),4,c[3]); p.poly([(x-6,y+5),(x-7,y-1),(x-3,y-8),(x-1,y-2),(x+2,y-8),(x+7,y-2),(x+5,y+5)],c[3]); p.line([(x-4,y),(x-2,y-4)],c[5])
    if scorpion:
        pts=[(33,44),(43,48),(49,42),(49,32),(44,25)]
        for a,b in zip(pts,pts[1:]): p.limb(a,b,5,c[2]); p.sphere((a[0]-3,a[1]-3,a[0]+3,a[1]+3),c[3])
        p.poly([(44,25),(40,20),(42,29)],'d4c6ad')
    if family=='mantis':
        p.poly([(24,15),(40,15),(32,24)],'97a46f');
        for s in (-1,1): p.limb((32+s*5,27),(32+s*16,19),3,'8a985f'); p.limb((32+s*16,19),(32+s*10,35),3,'acb374')
    if family=='wasp':
        for y in (31,37,43): p.line([(24,y),(40,y)],'c7aa62',3)
        for s in (-1,1): p.poly([(32+s*4,27),(32+s*24,15),(32+s*22,31),(32+s*9,34)],(169,193,185,180)); p.line([(32+s*5,28),(32+s*21,20)],'798f8a')
    return im


def bird(spec,state,frame,direction):
    im=canvas(); p=Pixel(im); f=spec.get('family','owl'); flap=round(math.sin(frame/8*math.tau)*7) if state in {'walk','attack'} else 0
    bat=f=='bat'; moth='moth' in f; heron=f=='heron'; c=palette('77718d' if bat else 'b9b5a0' if f in {'gull','heron','skimmer'} else '777b81' if f in {'crow','vulture'} else 'a18e70')
    for s in (-1,1):
        pts=[(32+s*4,30),(32+s*15,18-flap),(32+s*29,24-flap),(32+s*21,39),(32+s*9,44)]
        p.poly(pts,c[2]);
        if bat:
            for x,y in pts[1:-1]: p.line([(32+s*5,31),(x,y)],c[4],2)
            p.line([(32+s*15,18-flap),(32+s*18,13-flap)],'d0b8a3')
        else:
            for n in range(6):
                x=32+s*(10+n*3); y=29-flap+(n%2)*3; p.line([(32+s*7,31),(x,y+9)],c[1],3); p.line([(32+s*7,31),(x-1,y+7)],c[4])
        if moth: p.sphere((32+s*17-4,27-flap,32+s*17+4,35-flap),'bd9a72')
    p.sphere((25,21,39,43),c[3]); p.poly([(29,42),(25,52),(32,48),(38,52),(35,42)],c[2])
    hx,hy=32,21
    if heron: p.limb((32,30),(36,19),5,c[3]); p.limb((36,19),(31,11),4,c[3]); hy=10
    p.sphere((hx-7,hy-8,hx+7,hy+7),c[3])
    for dx in (-3,3):
        if f=='owl': p.sphere((hx+dx-3,hy-4,hx+dx+3,hy+3),'c1ac83')
        if direction!=3: p.dot(hx+dx,hy-1,'242b30'); p.dot(hx+dx,hy-2,'e7d5a3')
    if direction!=3: p.poly([(hx-2,hy+3),(hx+2,hy+3),(hx+(10 if heron else 0),hy+(5 if heron else 8))],'c6ad76')
    for s in (-1,1):
        p.line([(32+s*4,42),(32+s*5,57 if heron else 48),(32+s*8,59 if heron else 50)],'b8a585',2)
        if bat or f=='owl': p.poly([(32+s*4,15),(32+s*9,7),(32+s*8,19)],c[3])
    return im


def reptile(spec,state,frame,direction):
    im=canvas(); p=Pixel(im); f=spec.get('family','lizard'); phase=frame/8*math.tau; c=palette('86927a' if f not in {'drake','wyrm','wyvern'} else '967b68')
    snake=f in {'serpent','viper','worm','leech','grave_worm','wyrm','snail'}
    if snake:
        for i in range(20):
            angle=i/19*math.pi*1.8; x=31+math.cos(angle)*15; y=36+math.sin(angle)*10; rad=5 if f!='leech' else 3
            p.sphere((x-rad,y-rad,x+rad,y+rad),c[3]); p.line([(x-2,y+3),(x+2,y+4)],c[1])
        p.sphere((34,17,49,30),c[3]); p.poly([(42,25),(53,25),(51,31),(42,31)],c[2]); p.dot(45,23,'d3bc78'); p.line([(50,29),(57,30),(59,28)],'af766f')
        if f=='snail':
            p.sphere((17,15,41,41),'a88b71');
            pts=[(29+math.cos(t/10)*t*.06,28+math.sin(t/10)*t*.06) for t in range(140)]; p.line(pts,'6f5b50');
            for x in (45,50): p.line([(x,24),(x+1,15)],'879777',2); p.sphere((x-1,12,x+3,16),'a1ae87')
        return im
    if f in {'manta'}:
        p.poly([(31,13),(8,22),(2,41),(26,36),(31,43),(38,36),(61,40),(53,20)],c[3]); p.line([(32,34),(37,47),(34,59)],c[2],3); p.line([(9,25),(24,29),(30,18)],c[5]); return im
    frog=f in {'frog','toad'}
    for side in (-1,1):
        for y in (32,44):
            x=31+side*9; foot=(31+side*(18 if frog else 20),y+7+round(math.sin(phase)*2) if state=='walk' else y+7)
            p.limb((x,y),(31+side*19,y-2),5,c[2]); p.limb((31+side*19,y-2),foot,3,c[3]);
            for off in (-2,0,2): p.line([foot,(foot[0]+off,foot[1]+3)],c[4])
    p.sphere((20,24,42,49),c[3]); p.sphere((20 if frog else 23,15,42 if frog else 39,32),c[3])
    if not frog: p.limb((31,47),(38,56),7,c[2]); p.line([(38,56),(48,59),(54,53)],c[3],3)
    p.poly([(23,24),(39,24),(43 if f=='crocodile' else 38,14),(25,14),(20,21)],c[3]); p.line([(23,22),(38,22)],c[1])
    for x in (25,37): p.sphere((x-2,16,x+2,21),'d0bc75'); p.dot(x,18,'27342f')
    for n in range(16):
        x=24+(n*7)%14; y=29+(n*5)%16; p.line([(x,y),(x+2,y-1),(x+3,y)],c[4] if n%2 else c[1])
    if f in {'drake','wyvern','griffon','gargoyle'}:
        for s in (-1,1):
            p.poly([(31+s*6,28),(31+s*22,10),(31+s*28,16),(31+s*24,37),(31+s*14,34)],c[1]);
            for off in (10,20,29): p.line([(31+s*7,28),(31+s*24,off)],c[4],2)
        for y in range(27,46,5): p.poly([(30,y),(32,y-5),(34,y)],'c6ac7e')
    return im


def humanoid(spec,state,frame,direction):
    f=spec.get('family','bandit'); text=spec.get('anatomy','').lower(); role='guard' if f in {'knight','revenant','guardian','sentinel','skeleton'} else 'scholar' if f in {'phantom','wraith','djinn','elemental'} else 'traveler' if f=='pirate' else 'blacksmith' if f=='ogre' else 'herbalist' if f in {'myconid','hermit','fungus'} else 'fletcher'
    # Draw details on the same animation skeleton as the human characters.
    im=npc_frame(role,state,frame,direction); p=Pixel(im)
    if 'undead' in text and f not in {'revenant','knight'} and direction!=3:
        p.sphere((26,7,39,23),'c4baa0'); p.rect((28,12,31,15),'343838'); p.rect((34,12,37,15),'343838'); p.poly([(32,16),(31,19),(34,19)],'514b42')
        for x in range(29,37,2): p.line([(x,20),(x,23)],'655c4f')
    if f=='goblin':
        for s in (-1,1): p.poly([(32+s*5,12),(32+s*15,7),(32+s*10,18)],'96a079'); p.line([(32+s*7,13),(32+s*12,10)],'c0b091')
    if f=='kobold':
        p.poly([(28,11),(39,10),(45,18),(37,23),(29,21)],'92996d'); p.line([(34,19),(43,19)],'4a5547'); p.dot(35,13,'e0c58a')
    if f in {'myconid','hermit','fungus'}:
        p.poly([(17,16),(20,7),(31,3),(43,8),(48,17),(39,21),(24,21)],'a88679'); p.line([(21,13),(29,7),(39,10)],'d4b696',2)
        for x in range(22,45,4): p.line([(32,18),(x,20)],'665e68')
    if f=='knight' and 'headless' in spec['id']: p.rect((23,4,41,23),(0,0,0,0)); p.ellipse((27,22,38,27),'a2aaa8',INK); p.ellipse((29,23,36,25),'282d32')
    if f in {'wraith','phantom','djinn','elemental','wisp','sprite','geode'}:
        c=palette('a6acba' if f!='djinn' else 'b8a180')
        p.poly([(24,32),(38,31),(43,49),(38,47),(34,55),(31,48),(23,54),(24,45),(19,46)],c[2]); p.line([(27,33),(26,48)],c[4]); p.line([(34,34),(36,45)],c[1])
    return im


def construct(spec,state,frame,direction):
    f=spec.get('family','golem'); text=spec.get('anatomy','').lower(); im=canvas(); p=Pixel(im)
    c=palette('9a9578' if 'hay' in text or f=='scarecrow' else '91999d' if 'crystal' in text else '7f8380')
    stride=round(math.sin(frame/8*math.tau)*3) if state=='walk' else 0
    for s in (-1,1):
        p.limb((32+s*7,36),(32+s*8,51+stride*s),7,c[2]); p.poly([(23 if s<0 else 35,49+stride*s),(30 if s<0 else 43,49+stride*s),(33 if s<0 else 47,57+stride*s),(20 if s<0 else 34,57+stride*s)],c[3])
        p.limb((32+s*10,24),(32+s*18,39-stride*s),7,c[2]); p.sphere((32+s*18-5,36-stride*s,32+s*18+5,46-stride*s),c[3])
    p.poly([(22,20),(40,20),(45,33),(39,43),(25,43),(19,31)],c[2]); p.poly([(24,23),(34,22),(37,37),(26,38)],c[4],None)
    p.poly([(26,7),(37,8),(41,17),(36,24),(26,23),(23,16)],c[3]); p.line([(28,10),(35,11)],c[5]); p.line([(27,16),(30,16)],'d5bd77',2); p.line([(34,16),(37,16)],'d5bd77',2)
    for x,y in [(23,28),(32,34),(37,26),(27,39)]: p.line([(x,y),(x+3,y+3),(x+1,y+7)],c[0]); p.line([(x+1,y),(x+4,y+3)],c[4])
    if 'tree' in text or 'hay' in text or f=='scarecrow':
        for y in range(25,42,4): p.line([(24,y),(39,y-1)],'c3ae75')
        for s in (-1,1): p.line([(32+s*12,26),(32+s*23,16),(32+s*26,18)],'95754f',3); p.line([(32+s*23,16),(32+s*22,11)],'ba9b66',2)
    if 'crystal' in text or 'obsidian' in spec['id']:
        color='d8aa7b' if 'obsidian' in spec['id'] else 'c1d2d3'; p.line([(29,24),(33,30),(29,35),(35,40)],color,2)
    return im


def frame(spec: dict, state: str, index: int, direction: int) -> Image.Image:
    family=spec.get('family',''); text=spec.get('anatomy','').lower(); identity=spec['id']
    if family=='mimic' or 'monster:chest' in text:
        im=canvas(); im.alpha_composite(chest('mimic',state=='attack' or index>=4),(8,8))
    elif any(t in text for t in ('spider','beetle','scorpion','mantis','centipede','wasp','scarab','crab','tick')):
        im=insect(spec,state,index,direction)
    elif any(t in text.split(';')[0] for t in ('owl','bird','heron','gull','vulture','crow','moth','bat')) and 'owlbear' not in text:
        im=bird(spec,state,index,direction)
    elif any(t in text.split(';')[0] for t in ('lizard','salamander','drake','wyvern','wyrm','snake','worm','leech','frog','toad','snail','ray','mudskipper')):
        im=reptile(spec,state,index,direction)
    elif text.startswith(('humanoid:','undead:human','undead:armored','undead:spirit','spirit:humanoid','spirit:air','spirit:plant','spirit:thorn','spirit:stone','elemental:','plant:')):
        im=humanoid(spec,state,index,direction)
    elif text.startswith('construct:'): im=construct(spec,state,index,direction)
    elif text.startswith(('animal:','undead:canine','undead:horse')): im=quadruped(spec,state,index,direction)
    else:
        # Marine and rift creatures have articulated tentacles, not a blob silhouette.
        im=construct(spec,state,index,direction); p=Pixel(im)
        for n in range(5):
            x=20+n*6; wave=math.sin(index/8*math.tau+n)*3
            p.limb((x,37),(x+wave,47),5,'8c91a2'); p.line([(x+wave,47),(x-5,55),(x-8,51)],'aab9b6',3)
    if spec.get('boss'):
        out=im.resize((128,128),Image.Resampling.NEAREST); p=Pixel(out)
        # Additional native-resolution material and ornament detail for large encounters.
        gold=palette('c2a366')
        for s in (-1,1):
            p.poly([(64+s*13,29),(64+s*31,12),(64+s*26,30),(64+s*20,38)],gold[2]); p.line([(64+s*14,28),(64+s*27,17)],gold[5],2)
        for n in range(7):
            x=47+n*5; y=52+int(math.sin(n*.6)*4); p.rect((x,y,x+2,y+2),gold[4]); p.dot(x+1,y+1,gold[0])
        im=out
    if direction==1: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return finish_frame(im,state,index,direction)
