"""Original creature frames. Species geometry follows the catalog anatomy, not rarity colour."""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel,canvas,palette,rgba,shade,seed,animation_pose,finish_frame,INK
from .environment_pack import crystal,stone,chest
from .people import npc_frame

QUADRUPEDS={'rat','mouse','hare','fox','arctic_fox','weasel','boar','deer','stag','wolf','owlbear','wolverine','bear','polar_bear','badger','goat','ibex','leopard','ox','hound','jackal','horse','armadillo','lizard','salamander','crocodile','drake','wyrm','wyvern','griffon'}
INSECTS={'spider','quartz_spider','automaton','beetle','fire_beetle','crystal_beetle','scarab','mantis','wasp','moth','spore_moth','scorpion','tick'}
BIRDS={'owl','harpy','heron','skimmer','gull','vulture','crow','bat'}
HUMANS={'goblin','bandit','kobold','ogre','revenant','wraith','hermit','ghoul','pirate','monkey','djinn','knight','skeleton','phantom','cultist','demon'}
PLANTS={'sprite','wisp','tree','construct','scarecrow','fungus','myconid','coral','geode'}
STONES={'gargoyle','golem','elemental','prism','guardian','sentinel'}
SHELLS={'tortoise','turtle','crab','sand_crab','hermit_crab','snail'}
TUBES={'worm','leech','serpent','viper','grave_worm','centipede'}
AQUATICS={'manta','cuttle','horror','mudskipper','toad','frog'}


def body_colour(m):
    f=m['family']; named={'rat':'9a897c','mouse':'aa9686','hare':'b4a48c','fox':'b1845f','arctic_fox':'cdd1bf','boar':'847461','wolf':'929789','deer':'ad8d65','stag':'8f8167','bear':'6b625d','polar_bear':'d3d4bd','badger':'8c8b7e','leopard':'bbb394','ox':'817460','horse':'c2ba9e','jackal':'c5b899','crocodile':'788568','frog':'87aa67','toad':'9b9867','lizard':'9a9d72','wasp':'baa367','moth':'b2a091','spore_moth':'a899a9','scorpion':'a58a67','skeleton':'cbc2a4','goblin':'90a37d','kobold':'a79670','ghoul':'a1a68e','hermit':'9d9776','monkey':'9b805e','pirate':'887887','owl':'a5a291','crow':'676c78','vulture':'938673','heron':'b8c4be','gull':'c5cbbc','bat':'928494','drake':'a67c65','wyvern':'819595','wyrm':'b5c8bd','manta':'8c9fb2','cuttle':'b29fb9','mimic':'a08056','crab':'9db6bd','sand_crab':'ba9774'}
    return named.get(f,{'volcanic':'997767','glacier':'9eb7c2','tundra':'b1b7a7','fungal':'9c909f','crystal':'99a7b9','ruins':'a39e89','wasteland':'9b9290','arcane_anomaly':'a39cbe','swamp':'899a72'}.get(m['biome'],'899378'))


def antlers(p,x,y,kind,base):
    for sign in (-1,1):
        if kind in {'ibex','ox'}:
            points=[(x+sign*4,y),(x+sign*10,y-6),(x+sign*13,y-12),(x+sign*9,y-16)]
        else: points=[(x+sign*4,y),(x+sign*7,y-7),(x+sign*11,y-13)]
        p.limb(points[0],points[1],2,base); p.line(points[1:],base,2)
        if kind in {'deer','stag'}:
            p.line([(x+sign*7,y-7),(x+sign*2,y-12)],base,2); p.line([(x+sign*9,y-10),(x+sign*15,y-9)],base,2)


def quadruped(p,f,c,j,m):
    s=j['stride']; bob=j['bob']; side=j['side']; variant=seed(m['id'])
    reptile=f in {'lizard','salamander','crocodile','drake','wyrm','wyvern'}
    long=f in {'weasel','crocodile','wyrm'}; heavy=f in {'bear','polar_bear','ox','boar','owlbear','wolverine'}
    tall=f in {'deer','stag','goat','ibex','horse','griffon'}
    cy=36+bob; length=19 if long else 16 if heavy else 13; leg=15 if tall else 7 if reptile or long else 11
    # Rear limbs are drawn before the rib cage, with separate hock and paw joints.
    for back in (True,False):
        for rear in (True,False):
            xx=32+(-length+4 if rear else length-5); yy=cy+(0 if back else 6)
            stride=round(s*(3 if tall else 2))*(-1 if rear==back else 1)
            knee=(xx+(-3 if rear else 2)+stride,yy+leg*.5)
            foot=(xx+stride*2,yy+leg)
            p.limb((xx,yy),knee,4 if heavy else 3,c[1] if back else c[3]); p.limb(knee,foot,3,c[2])
            p.poly([(foot[0]-2,foot[1]-1),(foot[0]+4,foot[1]),(foot[0]+3,foot[1]+3),(foot[0]-2,foot[1]+3)],c[0] if tall else c[3])
            if not tall: p.line([(foot[0]+1,foot[1]+2),(foot[0]+4,foot[1]+2)],'d7c8a5')
        if back:
            if f not in {'bear','polar_bear','boar','owlbear','hare'}:
                thick=7 if f in {'fox','arctic_fox','leopard','wolf'} else 4 if reptile else 2
                p.limb((32-length+2,cy),(8,cy+round(s*3)-3),thick,c[2]); p.line([(8,cy+round(s*3)-3),(4,cy-11+round(s*2))],c[3],max(1,thick-1))
            p.sphere((32-length,cy-12-(3 if heavy else 0),32+length,cy+9),c[3])
            if f in {'fox','arctic_fox','wolf','badger','wolverine'}: p.poly([(36,cy-2),(45,cy-1),(43,cy+9),(36,cy+8)],c[4],None)
            if f in {'armadillo','crocodile','lizard','drake','wyrm','wyvern'}:
                for xx in range(20,43,5):
                    p.line([(xx,cy-8),(xx+3,cy-4),(xx+1,cy+4)],c[1]); p.line([(xx+1,cy-7),(xx+3,cy-4)],c[5])
            elif f in {'horse','jackal'}:
                for xx in range(20,40,4): p.line([(xx,cy-7),(xx+2,cy+5)],c[5],2)
                p.line([(20,cy-9),(39,cy-9)],c[0])
            elif f=='leopard':
                for xx,yy in [(20,cy),(25,cy-8),(31,cy-2),(36,cy+4),(40,cy-8)]: p.ellipse((xx,yy,xx+3,yy+2),c[0]); p.dot(xx+1,yy+1,c[3])
            else:
                for xx in range(20,43,5): p.line([(xx,cy-7),(xx+2,cy-5),(xx+1,cy-2)],c[2])
    hx,hy=(45,cy-10-(5 if tall else 0)) if side else (32,cy+(1 if not j['back'] else -13))
    if tall: p.limb((42,cy-2),(hx,hy),8,c[3])
    p.sphere((hx-7,hy-7,hx+8,hy+7),c[3]); muzzle=13 if f=='crocodile' else 9 if f in {'wolf','hound','horse','fox','jackal','leopard','drake'} else 5
    if side:
        p.poly([(hx+4,hy-3),(min(62,hx+muzzle),hy),(min(62,hx+muzzle),hy+5),(hx+3,hy+6)],c[3]); p.dot(min(62,hx+muzzle),hy+1,c[0]); p.line([(hx+5,hy+5),(min(62,hx+muzzle),hy+4)],c[0])
    elif not j['back']: p.sphere((hx-4,hy+1,hx+4,hy+8),c[4]); p.rect((hx-2,hy+3,hx+2,hy+4),c[0])
    if f in {'hare'}:
        for dx in (-5,3): p.limb((hx+dx,hy-3),(hx+dx+2,hy-21),4,c[3]); p.line([(hx+dx+1,hy-8),(hx+dx+2,hy-17)],'b38e88',2)
        p.sphere((15,cy+1,27,cy+13),c[3])
    elif f in {'deer','stag','goat','ibex','ox'}: antlers(p,hx,hy-5,f,'c9b78e')
    elif not reptile:
        for dx in (-6,5):
            if f in {'bear','polar_bear','mouse','rat','wolverine','badger'}: p.sphere((hx+dx-3,hy-10,hx+dx+3,hy-4),c[3])
            else: p.poly([(hx+dx-3,hy-3),(hx+dx,hy-12),(hx+dx+3,hy-3)],c[3])
    else:
        p.poly([(hx-6,hy-5),(hx-9,hy-13),(hx-2,hy-6)],'c3b49b'); p.poly([(hx+3,hy-5),(hx+8,hy-12),(hx+7,hy-2)],'c3b49b')
    if not j['back']:
        for dx in ((4,) if side else (-4,4)): p.dot(hx+dx,hy-1,c[0]); p.dot(hx+dx-1,hy-2,'e3dbc4')
    if f=='boar':
        for dx in (-5,6): p.poly([(hx+dx,hy+5),(hx+dx+1,hy-1),(hx+dx+4,hy+7)],'e1d2b2')
    if f in {'drake','wyvern','griffon'}:
        flap=round(math.sin(j['phase'])*4)
        for sign in (-1,1):
            p.poly([(30,cy-5),(30+sign*14,cy-24-flap),(30+sign*22,cy-11),(30+sign*13,cy-10),(30+sign*9,cy+2)],c[2]); p.line([(30,cy-5),(30+sign*14,cy-23-flap),(30+sign*21,cy-11)],c[4])
    if j['attack']: p.line([(hx+3,hy+6),(min(62,hx+13),hy+9)],'d6c4a1',2)


def insect(p,f,c,j,m):
    t=j['phase']; spider=f in {'spider','quartz_spider','automaton','tick'}; moth=f in {'moth','spore_moth','wasp'}; mantis=f=='mantis'
    x,y=32,35+j['bob']; n=4 if spider or f=='scorpion' else 3
    for sign in (-1,1):
        for i in range(n):
            yy=y-7+i*5; swing=round(math.sin(t+i)*3) if j['stride'] else 0
            mid=(x+sign*(15+i%2*3),yy-8+swing); end=(x+sign*(23-i%2*2),yy+8+swing)
            p.limb((x+sign*5,yy),mid,2,c[2]); p.limb(mid,end,2,c[3]); p.dot(end[0],end[1],c[5])
    if moth:
        flap=4+round(math.sin(t)*5)
        for sign in (-1,1):
            p.poly([(x,y),(x+sign*(21+flap),y-20),(x+sign*28,y-8),(x+sign*18,y+6),(x+sign*24,y+18),(x+sign*8,y+21)],c[2]);
            p.line([(x+sign*4,y),(x+sign*(20+flap),y-17)],c[4],2); p.line([(x+sign*5,y+3),(x+sign*17,y+14)],c[4]);
            p.sphere((x+sign*15-4,y-8,x+sign*15+4,y),c[0]); p.dot(x+sign*15,y-4,c[5])
    p.sphere((x-10,y-9,x+10,y+14),c[3]); p.sphere((x-7,y-16,x+7,y-5),c[2]); p.sphere((x-5,y-22,x+5,y-14),c[3])
    if spider:
        p.sphere((x-12,y-2,x+12,y+19),c[3]);
        for dx in (-4,0,4): p.dot(x+dx,y-18,'d5b775')
    else:
        p.line([(x,y-6),(x,y+13)],c[0]);
        for yy in range(y-4,y+13,5): p.line([(x-7,yy),(x-2,yy-1)],c[4]); p.line([(x+2,yy),(x+7,yy-1)],c[1])
    for sign in (-1,1):
        p.line([(x+sign*3,y-19),(x+sign*10,y-28),(x+sign*16,y-29)],c[3],2)
        if mantis or f=='scorpion':
            p.limb((x+sign*6,y-10),(x+sign*18,y-20-round(j['attack']*4)),3,c[3]); p.poly([(x+sign*18,y-23),(x+sign*22,y-30),(x+sign*24,y-22),(x+sign*18,y-17)],c[3])
    if f=='scorpion':
        points=[(x,y+12),(x+10,y+20),(x+23,y+12),(x+25,y),(x+20,y-7)]
        for a,b in zip(points,points[1:]): p.limb(a,b,5,c[3])
        p.poly([(x+18,y-9),(x+23,y-6),(x+15,y-3)],c[0])
    if f in {'crystal_beetle','quartz_spider','automaton'}: crystal(p,x,y+11,14,'b5c7cc')


def bird(p,f,c,j,m):
    x,y=32,34+j['bob']; t=j['phase']; flap=round(math.sin(t)*7)
    long=f=='heron'; bat=f=='bat'; owl=f=='owl'
    for sign in (-1,1):
        p.limb((x+sign*4,y+8),(x+sign*7,y+(23 if long else 18)),2,'b6a481'); p.line([(x+sign*7-3,y+19),(x+sign*7+3,y+19)],'c6b68f')
        if bat:
            outline=[(x+sign*4,y),(x+sign*20,y-20-flap),(x+sign*29,y+3),(x+sign*19,y-3),(x+sign*15,y+8),(x+sign*9,y+3)]
        else: outline=[(x+sign*5,y),(x+sign*21,y-17-flap),(x+sign*29,y-6),(x+sign*23,y+5),(x+sign*15,y+13)]
        p.poly(outline,c[2]); p.line([(x+sign*6,y),(x+sign*20,y-15-flap),(x+sign*26,y-5)],c[4])
        for i in range(3): p.line([(x+sign*(12+i*4),y-7),(x+sign*(15+i*4),y+6-i*3)],c[0])
    p.sphere((x-7,y-11,x+7,y+14),c[3]); p.poly([(x-6,y+10),(x-7,y+25),(x,y+21),(x+7,y+25),(x+6,y+10)],c[2])
    hy=y-17
    if long: p.limb((x,y-4),(x-5,y-14),4,c[3]); p.limb((x-5,y-14),(x+2,y-27),4,c[3]); hy=y-28
    p.sphere((x-7,hy-7,x+7,hy+7),c[3])
    if owl:
        for dx in (-4,4): p.sphere((x+dx-4,hy-3,x+dx+4,hy+5),'c2b798'); p.dot(x+dx,hy+1,INK)
        for sign in (-1,1): p.poly([(x+sign*3,hy-4),(x+sign*9,hy-13),(x+sign*7,hy+1)],c[3])
    elif not j['back']: p.dot(x+4,hy-1,INK); p.dot(x+3,hy-2,'e1d7ba')
    p.poly([(x+4,hy+2),(min(62,x+(22 if long else 12)),hy+5),(x+5,hy+7)],'bca46d' if not bat else c[1])
    if bat:
        for dx in (-5,5): p.poly([(x+dx-3,hy-3),(x+dx,hy-16),(x+dx+3,hy-3)],c[3])


def shell(p,f,c,j,m):
    x,y=32,38+j['bob']; aquatic=f=='turtle'; crab='crab' in f; snail=f=='snail'
    if snail:
        p.poly([(7,55),(12,48),(25,49),(44,44),(55,45),(60,53),(54,57),(15,59)],c[3]);
        for dx in (0,6): p.limb((50+dx,49),(50+dx,32),2,c[3]); p.sphere((48+dx,29,52+dx,33),c[4])
    else:
        for sign in (-1,1):
            for i in range(4 if crab else 2):
                yy=29+i*(5 if crab else 16); swing=round(j['stride']*2)*(-1 if i%2 else 1)
                p.limb((x+sign*11,yy),(x+sign*22,yy+5+swing),4 if not crab else 2,c[3]); p.line([(x+sign*22,yy+5+swing),(x+sign*25,yy+10)],c[1],2)
            if crab:
                p.limb((x+sign*9,28),(x+sign*20,19-round(j['attack']*5)),3,c[3]); p.poly([(x+sign*16,18),(x+sign*24,7),(x+sign*25,18),(x+sign*30,12),(x+sign*27,24),(x+sign*19,25)],c[3])
    p.sphere((14,20,48,53),c[3])
    if snail or f=='hermit_crab':
        points=[]
        for i in range(65):
            a=i*.18; radius=15*(1-i/70); points.append((31+math.cos(a)*radius,36+math.sin(a)*radius))
        p.line(points,c[0],2); p.line([(20,25),(28,22),(36,25)],c[5])
    else:
        p.poly([(25,24),(37,24),(42,35),(36,46),(25,46),(20,35)],c[2]); p.line([(25,25),(37,25),(41,35)],c[5]); p.line([(21,35),(41,35)],c[0]); p.line([(31,25),(31,45)],c[1])
    if not snail:
        p.sphere((25,10,39,25),c[3]);
        for dx in (-4,4): p.dot(x+dx,17,INK); p.dot(x+dx-1,16,'e6d6ba')


def tube(p,f,c,j,m):
    count=10 if f=='centipede' else 8; pts=[]
    for n in range(count):
        x=12+n*4; y=34+math.sin(n*.7+j['phase'])*8
        pts.append((x,y))
        if f=='centipede':
            for sign in (-1,1): p.line([(x,y),(x-3,y+sign*10),(x+2,y+sign*14)],c[2],2)
    for n,(x,y) in enumerate(pts):
        radius=5 if f not in {'worm','grave_worm'} else 7
        p.sphere((x-radius,y-radius,x+radius,y+radius),c[3]); p.line([(x,y-radius+1),(x-2,y)],c[1])
    x,y=pts[-1]; p.poly([(x-4,y-6),(x+6,y-5),(x+11,y),(x+5,y+6),(x-4,y+5)],c[3]); p.dot(x+5,y-2,INK); p.line([(x+9,y+1),(x+14,y),(x+16,y-2)],'bc8076')
    if f=='viper':
        p.poly([(x+2,y-5),(x+4,y-11),(x+6,y-4)],'cfb78b')


def human(p,f,c,j,m):
    # Humanoid articulation comes from the same frame grid as the player.
    role='guard' if f in {'knight','skeleton','revenant'} else 'scholar' if f in {'cultist','phantom','wraith','djinn'} else 'traveler'
    im=npc_frame(role,j['state'],j['frame'],0 if not j['side'] else 2)
    p.image.alpha_composite(im)
    hy=16+j['bob']
    if f in {'goblin','kobold','demon'}:
        p.sphere((26,9+j['bob'],39,24+j['bob']),c[3]);
        for sign in (-1,1): p.poly([(32+sign*5,hy-4),(32+sign*14,hy-7),(32+sign*6,hy+3)],c[3])
        p.dot(29,hy,INK); p.dot(36,hy,INK); p.line([(30,hy+6),(35,hy+6)],c[0])
        if f=='kobold': p.poly([(34,hy+1),(44,hy+4),(40,hy+8),(34,hy+6)],c[3])
    elif f in {'skeleton','ghoul'}:
        p.sphere((26,9+j['bob'],39,24+j['bob']),'c7bea4'); p.rect((28,14+j['bob'],30,17+j['bob']),INK); p.rect((34,14+j['bob'],36,17+j['bob']),INK)
        for dx in (28,31,34): p.line([(dx,21+j['bob']),(dx,24+j['bob'])],INK)
    elif f=='knight': p.rect((25,5,40,23),(0,0,0,0)); p.ellipse((28,23+j['bob'],37,27+j['bob']),'353941',INK)
    elif f in {'wraith','phantom','djinn'}:
        p.poly([(24,26),(40,26),(44,51),(37,47),(36,60),(30,53),(21,57)],c[2]);
        for dx in (25,30,35,40): p.line([(dx,31),(dx+2,49)],c[4]);
        p.ellipse((28,12,36,20),c[0]); p.dot(30,16,'c9d4cd'); p.dot(35,16,'c9d4cd')
    elif f=='ogre':
        p.sphere((22,24,45,43),c[3]); p.poly([(25,31),(41,31),(43,48),(23,48)],'b4a287'); p.rect((28,36,38,41),'786c56',INK)
    elif f=='monkey': p.limb((25,43),(12,45),3,c[2]); p.line([(12,45),(7,38),(10,30)],c[3],3)
    if f in {'pirate','bandit'}: p.line([(25,12),(39,12)],'a38669',3); p.line([(27,10),(34,18)],INK,2)


def plant(p,f,c,j,m):
    x,y=32,52+j['bob']; s=j['stride']
    for sign in (-1,1): p.limb((x+sign*4,y-10),(x+sign*9+round(s*2),y+6),5,c[2]); p.line([(x+sign*9,y+5),(x+sign*15,y+8)],c[3],2)
    p.poly([(24,y-32),(39,y-32),(42,y-4),(34,y+1),(23,y-3),(21,y-20)],c[2]); p.line([(27,y-28),(29,y-5)],c[4],2)
    for sign in (-1,1):
        arm=(x+sign*17,y-18-round(j['attack']*8)); p.limb((x+sign*7,y-27),arm,4,c[3]);
        for n in range(3): p.line([arm,(arm[0]+sign*(3+n*2),arm[1]-6+n*4)],c[2],2)
    if f in {'fungus','myconid','hermit'}:
        p.sphere((12,y-53,51,y-25),c[3]); p.line([(17,y-26),(47,y-26)],'ded2ac',2)
        for xx in range(19,47,4): p.line([(xx,y-24),(32,y-16)],'b4a887')
        for xx,yy in [(21,y-44),(36,y-48),(42,y-37),(18,y-34)]: p.ellipse((xx,yy,xx+4,yy+2),'dacbaa')
    elif f in {'construct','scarecrow'}:
        p.plank((14,y-29,51,y-24),'9c835b'); p.poly([(24,y-41),(39,y-42),(40,y-30),(25,y-30)],'b6a27f')
        p.poly([(18,y-40),(25,y-50),(38,y-48),(47,y-39)],'9a8154');
        for xx in (26,29,33,37): p.line([(xx,y-12),(xx-2,y-1)],'c1ac73')
    elif f=='tree':
        for sign in (-1,1): p.limb((x+sign*3,y-28),(x+sign*17,y-49),4,'877657'); p.line([(x+sign*17,y-49),(x+sign*23,y-53)],'b3a077',2)
        for xx in (24,29,35): p.line([(xx,y-33),(xx+2,y-11)],c[0])
    elif f=='coral':
        for dx,hh in [(-14,36),(-6,49),(3,41),(12,45),(18,30)]:
            p.limb((x,y-13),(x+dx,y-hh),5,c[3]); p.limb((x+dx,y-hh+8),(x+dx-5,y-hh-2),3,c[4]); p.line([(x+dx,y-hh+2),(x+dx+4,y-hh-3)],c[2],2)
    elif f in {'wisp','geode','sprite'}:
        crystal(p,x,y-17,25,c[4])
        for sign in (-1,1): p.poly([(x+sign*6,y-28),(x+sign*21,y-40),(x+sign*16,y-22)],c[3])
    p.dot(28,y-33,INK); p.dot(36,y-33,INK)


def construct(p,f,c,j,m):
    y=35+j['bob']; arm=round(j['attack']*10)
    for sign in (-1,1):
        p.limb((32+sign*7,y+9),(32+sign*10+round(j['stride']*3)*sign,57),6,c[2]);
        stone(p,32+sign*12,61,14,9,c[3]); p.limb((32+sign*10,y-9),(32+sign*23,y+7-arm),6,c[2]); stone(p,32+sign*23,y+13-arm,12,13,c[3])
    p.poly([(23,y-15),(41,y-15),(47,y-5),(40,y+14),(24,y+14),(17,y-5)],c[2]); p.poly([(25,y-12),(38,y-12),(39,y+8),(30,y+12),(23,y+3)],c[4],None)
    p.poly([(25,y-28),(39,y-28),(41,y-17),(37,y-11),(25,y-12),(22,y-19)],c[3]); p.rect((27,y-22,37,y-20),c[0]); p.dot(28,y-21,'e1d2a9'); p.dot(36,y-21,'e1d2a9')
    p.line([(31,y-10),(35,y-4),(30,y+1),(34,y+7)],'d7cc9b' if f=='golem' else 'b4c9cc',2)
    if f in {'elemental','prism','sentinel'}: crystal(p,31,y+5,24,'bdcbd4')
    if f=='gargoyle':
        for sign in (-1,1): p.poly([(32+sign*6,y-13),(32+sign*23,y-28),(32+sign*28,y-5),(32+sign*19,y-10),(32+sign*13,y+1)],c[2]); p.line([(32+sign*8,y-12),(32+sign*23,y-25)],c[4])


def aquatic(p,f,c,j,m):
    x,y=32,37+j['bob']
    if f in {'frog','toad','mudskipper'}:
        for sign in (-1,1):
            p.sphere((x+sign*17-7,y+1,x+sign*17+7,y+17),c[2]); p.limb((x+sign*10,y),(x+sign*14,y+20-round(j['stride']*3)),4,c[3])
            for n in range(3): p.line([(x+sign*14,y+19),(x+sign*(14+n*3),y+23)],c[4],2)
        p.sphere((16,y-17,48,y+13),c[3]);
        for dx in (-11,11): p.sphere((x+dx-5,y-20,x+dx+5,y-10),c[4]); p.dot(x+dx,y-15,INK)
        p.line([(22,y-5),(32,y-2),(43,y-6)],c[0]);
        if f=='toad':
            for xx,yy in [(25,y),(38,y+2),(21,y+6),(31,y+9)]: p.sphere((xx-1,yy-1,xx+2,yy+2),c[2])
        if j['attack']: p.line([(32,y-2),(33,y+21),(43,y+24)],'c99689',2)
    else:
        p.sphere((21,14,44,44),c[3])
        for sign in (-1,1):
            if f=='manta': p.poly([(32,26),(32+sign*29,16),(32+sign*21,39),(32+sign*7,48)],c[2]); p.line([(32+sign*7,28),(32+sign*24,21)],c[4])
            else:
                for n in range(3):
                    xx=32+sign*(5+n*4); offset=round(math.sin(j['phase']+n)*4)
                    p.limb((xx,37),(xx+offset,50+n),3,c[3]); p.line([(xx+offset,50+n),(xx+sign*6,59-n),(xx+sign*10,56-n)],c[4],2)
        p.line([(30,43),(28,56),(34,62)],c[3],2)
        for dx in (-6,6): p.sphere((32+dx-3,28,32+dx+3,34),c[4]); p.dot(32+dx,31,INK)


def frame(m,state,n,direction):
    im=canvas(); p=Pixel(im); j=animation_pose(state,n,direction); j.update(phase=n/8*math.tau,state=state,frame=n)
    f=m['family']; c=palette(body_colour(m))
    if f in QUADRUPEDS: quadruped(p,f,c,j,m)
    elif f in INSECTS: insect(p,f,c,j,m)
    elif f in BIRDS: bird(p,f,c,j,m)
    elif f in HUMANS: human(p,f,c,j,m)
    elif f in PLANTS: plant(p,f,c,j,m)
    elif f in STONES: construct(p,f,c,j,m)
    elif f in SHELLS: shell(p,f,c,j,m)
    elif f in TUBES: tube(p,f,c,j,m)
    elif f in AQUATICS: aquatic(p,f,c,j,m)
    elif f=='mimic': im.alpha_composite(chest('mimic',state in {'attack','cast'}),(8,14))
    else: raise ValueError('No anatomical renderer for species '+m['id']+' / '+f)
    if m.get('elite'):
        p.line([(21,26),(27,34)],'d0b093',2); p.line([(22,26),(28,34)],c[0])
    if m.get('boss'):
        # Individually keyed crests and trophies distinguish named bosses from their family.
        ident=seed(m['id']); gold=palette('b9a674')
        for i in range(3+(ident%3)):
            xx=17+i*7; p.poly([(xx-3,18),(xx-2,4+(ident+i)%7),(xx+2,9),(xx+4,18)],gold[3]); p.line([(xx-1,7+(ident+i)%7),(xx,15)],gold[5])
        p.poly([(19,35),(23,31),(27,35),(23,40)],gold[2]); p.dot(23,34,'e0d8b0')
    if direction==1: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    # Creature state changes use articulation above, then hit/death presentation.
    if f not in HUMANS: im=finish_frame(im,state,n,direction)
    if m.get('boss'):
        large=im.resize((128,128),Image.Resampling.NEAREST); q=Pixel(large)
        if state!='death':
            for xx,yy in [(48,69),(77,63),(68,38)]: q.dot(xx,yy,'e3d0a2'); q.dot(xx+1,yy+1,'6b5c50')
        return large
    return im
