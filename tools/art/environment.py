"""Original deterministic environment art. Native-size visual review remains required."""
from __future__ import annotations
import math
import random
from PIL import Image
from .common import Pixel, canvas, palette, rgba, shade, seed, INK

TERRAINS = ('grass','dirt','stone','sand','snow','water','lava','wall','wood','moss','crystal','marsh','ash')
PROPS = ('shadow','oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree','bush','flowers','rock','snow_rock','basalt','grass_tuft','reeds','mushrooms','cactus','crystal','signpost','waystone','stairs','stump','loot')
CHESTS = ('weathered','locked','ancient','runic','royal','cursed','mimic')
CITY = {
 'dawnreach': ('aaa18b','8e6752','c6ae76'),
 'emberhold': ('817c7c','645251','c79054'),
 'thornhollow': ('8d815e','55785e','b8bc80'),
 'frostgate': ('9ca9b0','687989','c7d4d4'),
 'gloamport': ('8e8d87','566f82','bba176'),
}

def terrain(kind: str, variant: int) -> Image.Image:
    bases = {'grass':'607852','dirt':'927b59','stone':'858780','sand':'b5a276','snow':'c4d0d0','water':'426e7c','lava':'a64e36','wall':'5b6065','wood':'8b7052','moss':'60756a','crystal':'77788f','marsh':'657663','ash':'716a67'}
    im = canvas((32,32)); p = Pixel(im); c = palette(bases[kind]); r = random.Random(seed(kind))
    p.rect((0,0,31,31),c[3])
    if kind in {'stone','wall','wood'}:
        step = 7 if kind != 'wood' else 6
        for y in range(-step,32,step):
            offset = ((y//step + variant)%2)*8
            for x in range(-16+offset,32,16):
                p.rect((x,y,x+15,y+step-1),c[2],c[1]); p.line([(x+1,y+1),(x+13,y+1)],c[4]); p.line([(x+14,y+2),(x+14,y+step-2)],c[1])
                if kind == 'wood': p.line([(x+2,y+3),(x+7,y+2),(x+12,y+3)],c[1]); p.dot(x+2,y+2,c[0])
        return im
    if kind in {'water','lava'}:
        for row in range(4):
            y = row*8+2
            pts = [(x,y+round(math.sin((x+variant*4+row*3)*.22)*2)) for x in range(32)]
            p.line(pts,c[4] if kind=='water' else 'e6a454')
            p.line([(x,py+2) for x,py in pts],c[2])
        if kind=='lava':
            for x,y in [(3,4),(19,18),(8,25)]:
                p.poly([(x,y),(x+5,y-2),(x+9,y+1),(x+6,y+5),(x,y+4)],'594d48')
                p.line([(x+1,y),(x+5,y-1),(x+7,y+1)],'b56843')
        return im
    # Small clustered detail retains broad readable ground planes.
    for n in range(24):
        x,y = r.randrange(32),r.randrange(32)
        if kind in {'grass','moss','marsh'}:
            p.line([(x-1,y+2),(x,y),(x+2,y+1)],c[2]); p.dot(x,y-1,c[4])
        elif kind=='snow':
            p.line([(x,y),(x+3,y-1),(x+6,y)],c[4] if n%2 else c[2])
        else:
            p.line([(x,y),(x+2,y)],c[2] if n%3 else c[4])
            if n%5==0: p.dot(x,y+1,c[1])
    return im


def rock(kind='rock', mineral: str | None = None) -> Image.Image:
    im=canvas((48,40)); p=Pixel(im)
    base='7f8790' if kind!='basalt' else '62636c'; c=palette(base)
    p.poly([(5,29),(10,15),(18,9),(30,10),(39,19),(44,31),(34,36),(14,36)],c[1])
    p.poly([(10,16),(18,10),(30,11),(26,23),(9,29)],c[3]); p.poly([(30,11),(38,20),(43,31),(27,29),(26,23)],c[2])
    p.poly([(18,11),(26,12),(22,21),(13,23)],c[4],None); p.line([(9,30),(21,29),(26,23),(35,24)],c[0])
    p.line([(21,29),(20,35)],c[0]); p.line([(31,14),(34,20)],c[4])
    for x,y in [(13,19),(31,29),(18,32),(37,27)]: p.dot(x,y,c[5])
    if kind=='snow_rock':
        p.poly([(9,17),(18,8),(30,9),(38,18),(34,20),(29,17),(24,21),(17,19),(13,21)],'c9d7da'); p.line([(13,15),(19,11),(28,12)],'e4ece7')
    if mineral:
        mc=palette(mineral)
        for x,y in [(16,20),(24,25),(32,22),(20,29)]:
            p.poly([(x-3,y),(x-1,y-4),(x+3,y-3),(x+4,y+2),(x,y+4)],mc[2]); p.line([(x-1,y-3),(x+2,y-2),(x+2,y+1)],mc[5])
    return im


def tree(kind: str) -> Image.Image:
    w,h=(112,140) if kind=='ancient_oak' else (80,112)
    im=canvas((w,h)); p=Pixel(im); cx=w//2; foot=h-5
    wood=palette('826348')
    p.poly([(cx-9,foot),(cx-5,55),(cx+4,49),(cx+8,foot),(cx+16,foot+1),(cx+3,foot-4),(cx-2,foot-2),(cx-17,foot+1)],wood[2])
    p.line([(cx-4,foot-2),(cx-2,63),(cx+1,55)],wood[4],2)
    p.line([(cx+3,foot-4),(cx+2,70)],wood[1],2)
    for y in range(67,foot-4,9): p.line([(cx-3,y),(cx+1,y-3),(cx+4,y-2)],wood[1])
    for x,y in [(cx-24,39),(cx+24,34),(cx-18,62)]: p.limb((cx,75),(x,y),5,'80634a')
    if kind=='dead_tree':
        for side in (-1,1):
            p.line([(cx+side*23,40),(cx+side*27,26),(cx+side*24,20)],wood[2],3)
            p.line([(cx+side*14,59),(cx+side*30,55),(cx+side*33,45)],wood[3],3)
        return im
    if kind in {'pine','snow_pine'}:
        c=palette('4e7567')
        for y,span in [(62,33),(43,27),(24,20),(8,13)]:
            p.poly([(cx,y),(cx-span,y+33),(cx-6,y+29),(cx+3,y+35),(cx+span,y+30)],c[2])
            p.poly([(cx,y+2),(cx-span+5,y+28),(cx-3,y+24)],c[4],None)
            for x in range(cx-span+7,cx+span-4,7): p.line([(x,y+27),(x+3,y+23)],c[1])
            if kind=='snow_pine': p.poly([(cx,y+1),(cx-span+8,y+25),(cx-7,y+21),(cx,y+25),(cx+span-9,y+23)],'c5d5d2'); p.line([(cx,y+3),(cx-7,y+16)],'e2e9df')
    elif kind=='palm':
        c=palette('739261')
        for dx,dy in [(-35,10),(-31,-15),(-18,-31),(8,-34),(28,-22),(35,0),(28,21)]:
            end=(cx+dx,40+dy)
            p.poly([(cx,41),(cx+dx*.6-3,36+dy*.6),(end[0],end[1]),(cx+dx*.6+4,44+dy*.6)],c[3])
            p.line([(cx,40),end],c[1])
            for t in (.35,.55,.75):
                x,y=cx+dx*t,40+dy*t; p.line([(x,y),(x-4,y+6)],c[4]); p.line([(x,y),(x+4,y+5)],c[1])
        for x in (-4,4): p.sphere((cx+x-3,39,cx+x+3,47),'806446')
    else:
        base='71926a' if kind!='willow' else '7b9670'; c=palette(base)
        centers=[(.29,.34,19),(.65,.30,21),(.47,.18,22),(.25,.50,20),(.70,.48,20),(.49,.44,24)]
        factor=w/80
        for tx,ty,rad in centers:
            x,y,rr=round(tx*w),round(ty*h),round(rad*factor)
            p.poly([(x-rr,y),(x-rr+5,y-rr//2),(x-rr//2,y-rr),(x+6,y-rr+2),(x+rr,y-rr//3),(x+rr-2,y+rr//2),(x+rr//3,y+rr),(x-rr//2,y+rr-3)],c[2])
            p.poly([(x-rr+5,y-2),(x-rr//2,y-rr+5),(x+4,y-rr+5),(x+rr-7,y-4),(x+4,y+rr//2),(x-rr//2,y+rr//2)],c[3],None)
            for i in range(17):
                lx=x-rr//2+(i*7)%(max(1,rr)); ly=y-rr//2+(i*11)%(max(1,rr))
                p.line([(lx,ly+1),(lx+2,ly),(lx+4,ly+1)],c[4] if i%3 else c[1]); p.dot(lx+1,ly,c[5] if i%4==0 else c[3])
        if kind=='willow':
            for x in range(11,w-8,5):
                y=50+abs(x-cx)//3; p.line([(x,y),(x-3,y+20),(x-1,y+31)],c[2],2)
                for yy in range(y+7,y+31,5): p.line([(x-2,yy),(x+1,yy+2)],c[4],2)
    return im


def chest(kind: str, opened=False) -> Image.Image:
    im=canvas((48,48)); p=Pixel(im)
    colors={'weathered':'8b7051','locked':'97734b','ancient':'786759','runic':'667a88','royal':'945d57','cursed':'716178','mimic':'97765b'}
    c=palette(colors[kind]); metal=palette('b3a06b' if kind in {'royal','runic','ancient'} else '939a9f')
    p.poly([(7,23),(16,18),(41,21),(41,37),(32,43),(7,39)],c[1]); p.rect((8,25,32,38),c[3],INK)
    p.poly([(33,25),(40,22),(40,36),(33,41)],c[2]);
    for y in (28,33,37): p.line([(9,y),(31,y+1)],c[1]); p.line([(11,y-1),(26,y)],c[4])
    for x in (11,28): p.rect((x,24,x+3,39),metal[2],metal[0]); p.line([(x+1,25),(x+1,37)],metal[4]); p.dot(x+2,35,metal[5])
    if opened:
        p.poly([(7,24),(9,9),(16,5),(40,8),(41,22),(33,27)],c[2]); p.poly([(11,21),(13,12),(17,9),(36,11),(37,20),(31,23)],c[0]); p.poly([(9,25),(18,22),(38,25),(31,30)],'25272d')
        for x in (17,23,28): p.ellipse((x,25,x+4,28),'cab76d','8a733d')
    else:
        p.poly([(7,24),(9,17),(16,12),(34,14),(41,20),(33,27)],c[3]); p.line([(10,19),(17,15),(32,17)],c[5]); p.line([(9,23),(32,26),(39,22)],c[1]);
        for x in (12,28): p.poly([(x,16),(x+3,15),(x+4,26),(x,25)],metal[3]); p.dot(x+1,21,metal[5])
    p.rect((20,26,25,33),metal[3],metal[0]); p.dot(22,29,metal[0]); p.line([(22,29),(22,31)],metal[0])
    if kind in {'runic','cursed'}: p.line([(15,31),(18,29),(18,35),(15,32)],'9ac8cf' if kind=='runic' else 'b99ac6')
    if kind=='royal': p.poly([(17,18),(19,20),(22,17),(25,21),(28,18),(27,24),(18,23)],'d2b56b')
    if kind=='mimic' and opened:
        for x in range(12,33,4): p.poly([(x,24),(x+3,24),(x+2,29)],'e1d2a1')
        p.line([(24,27),(26,33),(32,35)],'bd7b82',3)
    return im


def prop(kind: str) -> Image.Image:
    if kind in {'oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree'}: return tree(kind)
    if kind in {'rock','snow_rock','basalt'}: return rock(kind)
    im=canvas((48,56)); p=Pixel(im)
    if kind=='shadow':
        im=canvas((32,12)); p=Pixel(im); p.ellipse((1,1,30,10),(15,23,27,75)); p.ellipse((5,3,26,8),(15,23,27,45)); return im
    if kind=='stump':
        p.poly([(12,47),(14,29),(32,29),(36,48),(29,50),(24,47),(16,51)],'7e6046'); p.ellipse((13,23,33,34),'ba9361',INK)
        p.ellipse((17,26,29,32),'a67e51','775e40'); p.ellipse((21,28,26,30),'c5a477','8e6b48'); p.line([(17,35),(16,45)],'b08a56'); return im
    if kind=='signpost':
        p.plank((22,14,27,51),'866245'); p.poly([(6,12),(36,12),(43,19),(36,25),(6,25)],'a48858'); p.line([(10,16),(34,16)],'d2b57c'); p.line([(12,21),(32,21)],'584f3e'); p.dot(24,19,'c5bd9b'); return im
    if kind=='stairs':
        for n in range(6):
            y=20+n*5; p.rect((7+n,y,41-n,y+5),'7c8587',INK); p.line([(8+n,y),(40-n,y)],'b2b9ae')
        p.line([(5,20),(5,46)],'474d52',3); p.line([(43,20),(43,46)],'474d52',3); return im
    if kind in {'waystone','crystal'}:
        for x,y,size in [(13,45,20),(26,47,34),(36,48,18)]:
            p.poly([(x-5,y),(x-6,y-size+6),(x,y-size),(x+6,y-size+5),(x+4,y)],'777b9b'); p.poly([(x,y-size+2),(x+4,y-size+6),(x+3,y-2),(x,y)],'a4bac5',None); p.line([(x-4,y-size+7),(x-3,y-4)],'c6d7cf')
        if kind=='waystone': p.line([(24,30),(28,34),(24,39),(28,42)],'dfd9a7'); return im
        return im
    if kind=='loot':
        p.poly([(13,45),(12,34),(18,27),(18,22),(29,22),(29,28),(36,35),(35,46),(27,51),(19,50)],'927657'); p.line([(19,26),(29,26)],'d0b780',2); p.line([(18,33),(16,43),(22,47)],'b69568',2)
        for x,y in [(32,46),(38,48),(29,50)]: p.ellipse((x-3,y-2,x+3,y+1),'cab06c','735b3a'); p.line([(x-1,y-1),(x+1,y-1)],'e9d397')
        return im
    if kind=='cactus':
        for a,b,width in [((25,49),(25,13),9),((18,35),(10,33),7),((10,33),(10,22),6),((30,28),(38,27),6),((38,27),(38,17),5)]: p.limb(a,b,width,'66856b')
        for y in range(18,48,5): p.line([(22,y),(19,y-1)],'ccb99d'); p.line([(28,y+2),(31,y+1)],'ccb99d')
        p.ellipse((21,10,28,17),'b78291',INK); return im
    if kind=='mushrooms':
        for x,y,s in [(14,45,9),(29,46,13),(38,51,6)]:
            p.limb((x,y),(x,y-s),3,'c2b49c'); p.poly([(x-s,y-s),(x-s+2,y-s-5),(x,y-s-9),(x+s-2,y-s-4),(x+s,y-s),(x,y-s+2)],'9e776e'); p.line([(x-s+3,y-s-5),(x-1,y-s-7)],'d2ab88'); p.dot(x+3,y-s-4,'e0c4a0')
        return im
    if kind=='reeds':
        for n in range(8):
            x=8+n*4; y=12+(n*7)%14; p.line([(24,52),(x,y)],'8c9a69',2); p.line([(x,y),(x+1,y-5)],'866c4e',3); p.line([(x,y-1),(x,y-5)],'b59b69')
        return im
    if kind in {'bush','flowers','grass_tuft'}:
        r=random.Random(seed(kind))
        for n in range(12 if kind=='bush' else 7):
            x=6+r.randrange(36); y=28+r.randrange(19); p.line([(24,51),(x,y)],'607b53',2)
            p.poly([(x,y),(x-5,y-4),(x-7,y-1),(x-3,y+3)],'86a16c'); p.line([(x-5,y-2),(x,y+1)],'b0b383')
            if kind=='flowers':
                for dx,dy in [(-2,0),(2,0),(0,-2),(0,2)]: p.rect((x+dx-1,y+dy-1,x+dx+1,y+dy+1),'ceb8b7')
                p.dot(x,y,'e1c87a')
        return im
    raise ValueError('Unknown prop: '+kind)


def building(zone: dict, spec: dict) -> Image.Image:
    w,h=int(spec['width'])*32,(int(spec['height'])+2)*32
    im=canvas((w,h)); p=Pixel(im)
    town=next((name for name in CITY if name in zone['id']),None)
    stone,roof,trim=CITY.get(town,('a89b7d','766d5b','bea779'))
    sc,rc,tc=palette(stone),palette(roof),palette(trim)
    wall_top=max(53,h//3); eaves=wall_top+12; bottom=h-5; mid=w//2
    p.rect((5,eaves,w-6,bottom),sc[2],INK,2)
    for y in range(eaves+5,bottom,12):
        for x in range(7-(6 if (y//12)%2 else 0),w-7,24):
            p.line([(x,y),(min(w-8,x+21),y)],sc[1]); p.line([(x,y),(x,y+9)],sc[1]); p.line([(x+2,y+2),(min(w-8,x+19),y+2)],sc[3])
    p.poly([(1,eaves+4),(mid,7),(w-2,eaves+4),(w-6,eaves+13),(mid,23),(6,eaves+13)],rc[0])
    p.poly([(4,eaves+3),(mid,10),(w-5,eaves+3)],rc[2])
    for y in range(19,eaves+2,8):
        half=(y-10)/(max(1,eaves-10))*(w/2-4)
        for x in range(round(mid-half),round(mid+half),12):
            right=min(round(mid+half),x+10); p.line([(x,y),(right,y)],rc[4]); p.line([(right,y),(right,y+4)],rc[1])
    p.line([(2,eaves+7),(mid,15),(w-3,eaves+7)],tc[2],3)
    for x in (8,w-12): p.rect((x,eaves+10,x+4,bottom),tc[1],INK); p.line([(x+1,eaves+12),(x+1,bottom-2)],tc[3])
    door_w=min(30,max(18,w//7)); door_top=bottom-42
    p.rect((mid-door_w//2-3,door_top-3,mid+door_w//2+3,bottom),sc[0]); p.plank((mid-door_w//2,door_top,mid+door_w//2,bottom-2),'82634b')
    for x in range(mid-door_w//2+4,mid+door_w//2,5): p.line([(x,door_top+2),(x,bottom-3)],'5b493b')
    p.dot(mid+door_w//2-5,door_top+24,'dfc07e'); p.rect((mid-door_w//2-5,bottom-1,mid+door_w//2+5,bottom+3),sc[3],sc[0])
    for cx in (w//5,w*4//5):
        top=min(bottom-44,eaves+23); p.rect((cx-12,top-3,cx+12,top+26),tc[0]); p.rect((cx-9,top,cx+9,top+23),'415a64',INK)
        p.rect((cx-7,top+2,cx-1,top+10),'b2c2b8'); p.rect((cx+2,top+13,cx+7,top+20),'7e9391'); p.line([(cx,top),(cx,top+23)],tc[4],2); p.line([(cx-9,top+11),(cx+9,top+11)],tc[4],2)
        p.rect((cx-15,top+25,cx+15,top+29),sc[3],INK)
    if spec.get('station'):
        p.line([(w-16,eaves+27),(w-40,eaves+27)],'3c4348',2); p.line([(w-34,eaves+27),(w-34,eaves+36)],'3c4348',2); p.plank((w-47,eaves+35,w-23,eaves+51),trim)
        p.line([(w-42,eaves+46),(w-29,eaves+40)],'4b463d',2); p.line([(w-39,eaves+40),(w-34,eaves+46)],'4b463d',2)
    if town=='frostgate': p.line([(3,eaves+4),(mid,10),(w-4,eaves+4)],'d3dfdc',5)
    if town=='emberhold':
        p.rect((w-36,4,w-20,eaves-9),'787477',INK); p.line([(w-34,8),(w-23,8)],'c29d7b'); p.rect((w-39,1,w-17,8),'8d8580',INK)
    return im


def resource(spec: dict) -> Image.Image:
    skill=spec.get('skill',''); name=spec['id']
    if skill=='woodcutting': return tree('pine' if 'pine' in name else 'ancient_oak' if any(x in name for x in ('elder','ironwood')) else 'oak')
    if skill in {'mining','prospecting'}:
        from .common import METALS
        metal=next((value for key,value in METALS.items() if key in name),'a8aaa0')
        return rock(mineral=metal)
    if skill=='fishing':
        im=canvas((64,40)); p=Pixel(im); p.ellipse((3,12,61,36),'487987','364c58'); p.ellipse((8,17,56,32),'568d96','9dbab8')
        for x,y in [(21,24),(40,22)]: p.poly([(x-6,y),(x,y-3),(x+5,y),(x,y+3),(x-6,y)],'b6c4b3'); p.poly([(x-5,y),(x-10,y-4),(x-9,y+4)],'92a799'); p.dot(x+3,y,'354a4e')
        p.line([(12,29),(22,31),(33,29)],'a3c9c8'); return im
    if skill=='skinning':
        im=canvas((48,40)); p=Pixel(im); p.poly([(9,27),(16,19),(15,11),(23,16),(33,12),(32,22),(41,27),(31,31),(32,37),(23,34),(16,37),(16,31)],'a98c70'); p.line([(20,19),(27,22),(31,28),(24,32),(19,28)],'cfb091',2); return im
    if skill=='excavation':
        im=rock(); p=Pixel(im); p.poly([(16,17),(29,14),(35,23),(28,30),(17,27)],'bba686'); p.line([(21,18),(26,21),(23,25),(30,25)],'655c55'); return im
    return prop('reeds' if skill=='farming' else 'mushrooms' if 'mushroom' in name else 'flowers' if skill=='herbalism' else 'bush')


def structure(name: str) -> Image.Image:
    im=canvas((64,64)); p=Pixel(im)
    for x in (12,46): p.plank((x,32,x+5,58),'775d45')
    p.plank((8,27,55,38),'a18258')
    if any(k in name for k in ('forge','anvil','smith')):
        p.poly([(14,26),(17,15),(47,15),(57,20),(43,24),(39,30),(37,34),(20,34),(22,27)],'89969e'); p.line([(19,17),(47,17),(52,20)],'c3cbd0'); p.line([(22,28),(36,28)],'4e5864',3)
    elif any(k in name for k in ('loom','tannery')):
        p.plank((12,8,17,39),'9b7c58'); p.plank((46,8,51,39),'9b7c58'); p.plank((12,7,51,12),'9b7c58')
        for x in range(19,46,3): p.line([(x,13),(x,34)],'c1b599')
        p.rect((18,24,45,29),'887ba0'); p.line([(19,26),(44,26)],'d0bdac')
    elif any(k in name for k in ('alchemy','enchanter','rune','lapidary')):
        for x in (20,35,46):
            p.sphere((x-5,16,x+5,29),'91b0ae'); p.rect((x-2,12,x+2,17),'b4bcae',INK); p.rect((x-2,10,x+2,13),'8d7355')
    else:
        p.plank((15,19,42,24),'c3a475'); p.line([(42,19),(50,9)],'b4bbc1',3); p.rect((44,7,55,11),'a5adb1',INK); p.line([(16,23),(39,23)],'6d553e')
    return im
