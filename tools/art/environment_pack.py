"""Original native-resolution environmental pixel art for the game asset pack."""
from __future__ import annotations
import math
import random
from .common import Pixel, canvas, palette, shade, rgba, seed, INK, METALS, WOODS

TERRAINS = {'grass':'687a46','dirt':'8b7452','stone':'7e8380','sand':'baa171','snow':'c5d2cf','water':'426f86','lava':'bb6040','wall':'696b70','wood':'93754e','moss':'586b4c','crystal':'777a99','marsh':'63725b','ash':'716e6c'}
PROPS = ['oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree','bush','flowers','rock','snow_rock','basalt','grass_tuft','reeds','mushrooms','cactus','crystal','signpost','waystone','stairs','stump','loot','shadow']


def tile(kind: str, variant: int):
    im = canvas((32,32)); p = Pixel(im); c = palette(TERRAINS[kind]); r = random.Random(seed(kind)+variant)
    p.rect((0,0,31,31),c[3])
    if kind in {'stone','wall','wood'}:
        height = 8 if kind != 'wood' else 6
        for y in range(-height,32,height):
            shift = (y//height%2)*8
            for x in range(-16,32,16):
                box = (x+shift,y,x+shift+15,y+height-1)
                if kind=='wood': p.plank(box,c[3])
                else:
                    p.rect(box,c[2+(r.randrange(2))],c[1]); p.line([(box[0]+1,y+1),(box[2]-1,y+1)],c[4]); p.dot(box[0]+3,y+3,c[2])
        return im
    if kind in {'water','lava'}:
        for y in range(2,32,6):
            dx = (variant*3+y*2)%13
            for x in range(-12,32,16):
                p.line([(x+dx,y),(x+dx+5,y),(x+dx+7,y+1),(x+dx+10,y+1)],c[4])
                p.line([(x+dx+3,y+3),(x+dx+10,y+3)],c[2])
        if kind=='lava':
            for x,y in [(6,8),(22,24)]: p.poly([(x-5,y),(x,y-3),(x+5,y),(x+2,y+4),(x-4,y+3)],'49494d'); p.line([(x-4,y-1),(x,y-2)],'736159')
        return im
    for _ in range(12):
        x,y = r.randrange(32),r.randrange(32)
        p.poly([(x,y),(x+3,y-1),(x+5,y+1),(x+2,y+2)],c[2 if r.randrange(2) else 3],None)
        if kind in {'grass','moss','marsh'}:
            p.line([(x,y+2),(x-1,y-1)],c[4]); p.line([(x,y+2),(x+2,y)],c[2])
        elif kind in {'sand','snow','ash','dirt'}: p.line([(x,y),(x+3,y)],c[4]); p.dot(x+4,y+1,c[2])
        elif kind=='crystal': p.poly([(x,y+2),(x+1,y-3),(x+3,y+1),(x+2,y+3)],c[4])
    return im


def stone(p, x, y, w=24, h=18, base='8d8c7e'):
    c=palette(base)
    p.poly([(x-w//2,y),(x-w//2+4,y-h+5),(x-3,y-h),(x+w//2-3,y-h+4),(x+w//2,y-3),(x+4,y+2)],c[2])
    p.poly([(x-w//2+4,y-h+5),(x-3,y-h),(x+4,y-h+7),(x-2,y-3),(x-w//2+2,y-1)],c[4],None)
    p.poly([(x+4,y-h+7),(x+w//2-3,y-h+4),(x+w//2,y-3),(x+4,y+2),(x-2,y-3)],c[1],None)
    p.line([(x-w//2+5,y-h+5),(x-3,y-h+1),(x+4,y-h+7)],c[5]); p.line([(x+3,y-h+8),(x+1,y-4),(x+5,y-1)],c[0])


def crystal(p,x,y,size=24,base='91b8bd'):
    c=palette(base)
    for dx,dy,s in [(-9,0,.65),(8,0,.8),(0,2,1.)]:
        xx,yy=x+dx,y+dy; h=int(size*s)
        p.poly([(xx-5,yy),(xx-6,yy-h+7),(xx,yy-h),(xx+5,yy-h+5),(xx+4,yy-1)],c[2])
        p.poly([(xx,yy-h+1),(xx+4,yy-h+5),(xx+3,yy-2),(xx,yy)],c[4],None)
        p.line([(xx-4,yy-h+7),(xx-1,yy-h+3),(xx-1,yy-5)],c[5])


def tree(kind: str):
    w,h = (112,144) if kind=='ancient_oak' else (80,112)
    im=canvas((w,h)); p=Pixel(im); x=w//2; foot=h-5; wood=palette('807055' if kind=='willow' else '8b694c')
    p.ellipse((x-16,foot-7,x+17,foot+2),(20,28,26,65))
    p.poly([(x-7,foot-3),(x-4,foot-65),(x+5,foot-68),(x+7,foot-8),(x+16,foot),(x+4,foot-2),(x-1,foot+1),(x-13,foot)],wood[2])
    p.line([(x-3,foot-6),(x-1,foot-53)],wood[4],2); p.line([(x+4,foot-8),(x+2,foot-58)],wood[0])
    for yy in range(foot-49,foot-9,11): p.line([(x-3,yy),(x+1,yy+3),(x+2,yy+7)],wood[1])
    p.ellipse((x-2,foot-29,x+3,foot-22),wood[1]); p.dot(x-1,foot-27,wood[4])
    for dx,yy in [(-19,-56),(22,-66),(-16,-80)]: p.limb((x,foot-35),(x+dx,foot+yy),5,wood[2])
    if kind=='dead_tree':
        for dx,yy in [(-23,-58),(24,-68),(-16,-82)]: p.line([(x+dx,foot+yy),(x+dx-5,foot+yy-13)],wood[2],3)
        return im
    if kind=='palm':
        for n in range(7):
            ang=n*math.tau/7
            tip=(x+math.cos(ang)*34,foot-66+math.sin(ang)*22)
            p.poly([(x,foot-67),(tip[0]-6,tip[1]+1),tip,(tip[0]+5,tip[1]+6)],'607c4e'); p.line([(x,foot-67),tip],'9aaa65')
        for dx in (-4,2,7): p.sphere((x+dx-3,foot-65,x+dx+3,foot-56),'8c7150')
        return im
    leaf = palette('698153' if kind!='willow' else '718e69')
    if 'pine' in kind:
        for yy,ww in [(foot-20,34),(foot-40,28),(foot-61,20)]:
            p.poly([(x,yy-31),(x-ww,yy),(x-ww//2,yy-3),(x-ww//2-3,yy+5),(x,yy+8),(x+ww,yy)],leaf[1]); p.poly([(x-1,yy-29),(x-ww+3,yy-1),(x-5,yy+3),(x+ww-5,yy-2)],leaf[3],None)
            if kind=='snow_pine': p.poly([(x,yy-28),(x-ww+5,yy-2),(x-12,yy-5),(x-3,yy),(x+9,yy-5),(x+ww-6,yy-2)],'d5dfd5',None)
            else: p.line([(x-1,yy-25),(x-ww+7,yy-2)],leaf[4])
        return im
    clusters=[(-20,-61,22),(18,-66,24),(-8,-88,25),(6,-54,28),(-27,-82,18),(26,-88,18),(6,-107,20)]
    if kind=='ancient_oak': clusters += [(-36,-104,20),(33,-110,22),(0,-125,20)]
    r=random.Random(seed(kind))
    for dx,dy,s in clusters:
        xx,yy=x+dx,foot+dy
        outline=[(xx-s,yy),(xx-s+3,yy-s//2),(xx-s//2,yy-s//2-4),(xx-2,yy-s),(xx+s//2,yy-s+3),(xx+s,yy-s//2),(xx+s-2,yy+5),(xx+s//3,yy+s//2),(xx-s//2,yy+s//2-1)]
        p.poly(outline,leaf[2]); p.poly([(xx-s+4,yy-2),(xx-s//2,yy-s//2),(xx,yy-s+3),(xx+s//2,yy-s+5),(xx+s-4,yy-3),(xx,yy+5)],leaf[3],None)
        for _ in range(13):
            lx=xx+r.randrange(-s+5,s-4); ly=yy+r.randrange(-s//2,s//3+1)
            p.line([(lx,ly),(lx+3,ly-1),(lx+5,ly)],leaf[4 if ly<yy else 1])
    if kind=='willow':
        for dx in range(-30,35,8):
            length=15+abs(dx)//2
            p.line([(x+dx,foot-64),(x+dx-3,foot-64+length)],leaf[2],2)
            for yy in range(foot-61,foot-64+length,5): p.line([(x+dx-2,yy),(x+dx+2,yy+2)],leaf[4])
    return im


def prop(kind: str):
    if kind in {'oak','ancient_oak','pine','snow_pine','willow','palm','dead_tree'}: return tree(kind)
    if kind=='shadow':
        im=canvas((32,12)); Pixel(im).ellipse((1,1,30,10),(17,23,24,75)); return im
    im=canvas((48,64)); p=Pixel(im); x,y=24,58
    if kind in {'rock','snow_rock','basalt'}:
        stone(p,x,y,34,28,'6d707a' if kind=='basalt' else '989c8b')
        if kind=='snow_rock': p.poly([(9,39),(21,31),(36,38),(32,44),(22,41),(12,45)],'dce5d8')
    elif kind=='crystal': crystal(p,x,y,43)
    elif kind=='stump':
        p.plank((13,39,35,57),'8d6c48'); p.ellipse((12,34,36,45),'bca077',INK)
        p.d.ellipse((16,36,32,42),outline=rgba('8f734f')); p.d.ellipse((21,37,28,41),outline=rgba('8f734f'))
        p.line([(15,54),(7,58)],'72543c',3); p.line([(33,54),(40,59)],'72543c',3)
    elif kind=='signpost':
        p.plank((22,13,26,59),'8d6e4c'); p.poly([(5,15),(36,15),(43,21),(36,27),(5,27)],'b89562'); p.line([(8,18),(34,18)],'d0b381'); p.line([(12,23),(28,23)],'725b43'); p.dot(24,20,'d5c6a0'); p.plank((13,31,39,40),'987449')
    elif kind=='waystone':
        stone(p,x,y,34,13,'8d8c86'); p.poly([(16,48),(14,19),(24,6),(34,19),(32,48)],'6f848c'); p.poly([(24,9),(30,20),(29,45),(24,49)],'97aead',None); p.line([(24,17),(20,25),(27,30),(21,37)],'b0d3cd',2); p.dot(24,41,'e4edca')
    elif kind=='stairs':
        for i in range(6): p.rect((4+i,28+i*5,43-i,35+i*5),'626977',INK); p.line([(5+i,29+i*5),(42-i,29+i*5)],'a3ada7')
    elif kind=='loot':
        p.poly([(18,33),(31,33),(28,39),(35,47),(34,57),(14,59),(11,51),(20,40)],'a08355'); p.line([(19,39),(28,39)],'574936',2); p.line([(16,46),(15,53),(21,55)],'d1b275'); p.sphere((30,53,37,59),'d9b064'); p.sphere((35,50,42,56),'c9a057')
    elif kind=='cactus':
        p.limb((24,58),(24,16),10,'788c56'); p.limb((24,39),(11,39),7,'788c56'); p.limb((11,39),(11,28),7,'788c56'); p.limb((25,32),(36,32),7,'788c56'); p.limb((36,32),(36,22),7,'788c56')
        for yy in range(19,55,7): p.line([(21,yy),(26,yy+1)],'cad19b')
    elif kind=='mushrooms':
        for xx,yy,s in [(14,58,9),(31,54,12),(38,60,6)]:
            p.rect((xx-2,yy-s,xx+2,yy),'c2baa1',INK); p.sphere((xx-s,yy-s*2,xx+s,yy-s+3),'b18e76'); p.line([(xx-s+2,yy-s+2),(xx+s-2,yy-s+2)],'e0cfa4'); p.dot(xx-3,yy-s*2+4,'e5d8b9')
    elif kind=='bush':
        for xx,yy,s in [(14,53,11),(28,44,13),(36,53,10)]: p.sphere((xx-s,yy-s,xx+s,yy+s//2),'758a54')
        for xx,yy in [(12,44),(27,39),(35,49)]: p.rect((xx,yy,xx+2,yy+1),'c9946b')
    else:
        for n in range(7):
            xx=8+n*5; height=10+(n*7)%21
            p.line([(xx,y),(xx-3,y-height)],'6b8453',2); p.line([(xx,y-2),(xx+4,y-height//2)],'95a96c')
            if kind=='flowers': p.sphere((xx-5,y-height-3,xx,y-height+2),'bd9bb6' if n%2 else 'd5c18a'); p.dot(xx-2,y-height,'e8d28c')
            elif kind=='reeds': p.line([(xx-3,y-height),(xx-3,y-height-7)],'96724e',3)
    return im


def chest(kind: str, opened: bool):
    im=canvas((48,48)); p=Pixel(im); base={'weathered':'8c795c','ancient':'827a68','locked':'9e7850','runic':'746787','royal':'a48654','cursed':'655867','mimic':'98704d'}.get(kind,'90764f'); c=palette(base)
    p.ellipse((4,39,44,46),(20,24,22,75)); p.poly([(5,23),(32,21),(42,27),(40,41),(12,43),(5,37)],c[2]);
    for y in (27,32,37): p.line([(8,y),(32,y-2),(39,y+2)],c[0]); p.line([(8,y+1),(30,y-1)],c[4])
    top=6 if opened else 14
    p.poly([(5,top+8),(12,top),(35,top),(43,top+7),(40,26),(32,24),(6,26)],c[3]); p.line([(12,top+2),(34,top+2)],c[5]);
    if opened: p.poly([(8,24),(31,22),(39,27),(14,32)],'343136'); p.line([(10,25),(32,24)],'a79169')
    for x in (11,32):
        p.rect((x,top+5,x+3,39),'78888a',INK); p.line([(x+1,top+6),(x+1,38)],'c4c3ab'); p.dot(x+1,30,'e0d4ad')
    p.rect((20,25,27,34),'c5a46a',INK); p.dot(23,29,'473a32'); p.line([(23,30),(23,32)],'473a32')
    if kind in {'runic','cursed'}: p.line([(16,33),(19,37),(16,40)],'acbed0' if kind=='runic' else 'af7995')
    if kind=='mimic' and opened:
        for x in range(10,35,6): p.poly([(x,24),(x+3,31),(x+5,24)],'e1ceb0')
        p.line([(25,28),(32,38),(30,46)],'bd807c',4)
    return im


def building(zone, b):
    w,h=b['width']*32,(b['height']+2)*32
    im=canvas((w,h)); p=Pixel(im); style=b.get('style','cottage'); biome=zone['biome']; r=random.Random(seed(zone['id']+b['id']))
    roof={'dawnreach':'766b83','emberhold':'786556','thornhollow':'668365','frostgate':'7f98aa','gloamport':'687d82'}.get(zone['id'],'7f765e')
    wall='a3a08c' if biome not in {'volcanic','tundra','glacier'} else '828e94'; c=palette(wall); eave=max(38,min(85,h//3)); bottom=h-5
    p.rect((3,eave-4,w-4,bottom),c[2],INK)
    for yy in range(eave,bottom,10):
        for xx in range(-14,w,22):
            offset=11 if yy//10%2 else 0; x=xx+offset
            p.rect((max(4,x),yy,min(w-5,x+20),min(bottom,yy+9)),c[2+r.randrange(2)],c[1]); p.line([(max(4,x+1),yy+1),(min(w-5,x+19),yy+1)],c[4])
    for xx in (4,w//3,2*w//3,w-8): p.plank((xx,eave,xx+4,bottom),'755b42')
    roofc=palette(roof)
    p.poly([(0,eave),(w*.23,7),(w*.76,7),(w-1,eave),(w-1,eave+8),(0,eave+8)],roofc[1])
    p.poly([(3,eave-2),(w*.23,9),(w*.76,9),(w-4,eave-2)],roofc[3],None)
    for yy in range(13,eave,6):
        inset=max(1,int((eave-yy)/(eave-7)*w*.23))
        p.line([(inset,yy),(w-inset,yy)],roofc[1]); p.line([(inset+1,yy+1),(w-inset-1,yy+1)],roofc[4])
        for xx in range(inset+5,w-inset,13): p.line([(xx+(yy%3),yy-4),(xx+(yy%3),yy)],roofc[2])
    p.line([(2,eave+2),(w-3,eave+2)],'baa17b',3)
    doorx=w//2; top=max(eave+20,bottom-48)
    p.poly([(doorx-15,bottom),(doorx-15,top+8),(doorx-9,top),(doorx+9,top),(doorx+15,top+8),(doorx+15,bottom)],'463e36')
    p.plank((doorx-12,top+10,doorx+12,bottom-2),'8c6947'); p.line([(doorx,top+12),(doorx,bottom-3)],'493d31'); p.rect((doorx-11,top+18,doorx+11,top+21),'687374',INK); p.sphere((doorx+5,bottom-22,doorx+10,bottom-17),'bfad77')
    for xx in (w//5,4*w//5):
        wy=eave+18; ww=min(13,w//12)
        p.rect((xx-ww-3,wy-3,xx+ww+3,wy+30),'605441',INK); p.rect((xx-ww,wy,xx+ww,wy+26),'ceb989',INK); p.rect((xx-ww+2,wy+2,xx-2,wy+12),'e1d3a8'); p.line([(xx,wy),(xx,wy+26)],'6a665a',2); p.line([(xx-ww,wy+13),(xx+ww,wy+13)],'6a665a',2); p.rect((xx-ww-4,wy+29,xx+ww+4,wy+32),'9a8463',INK)
    if biome in {'tundra','glacier'}: p.poly([(3,eave-3),(w*.23,7),(w*.76,7),(w-4,eave-3),(w-18,eave-8),(w*.69,16),(w*.27,15),(14,eave-7)],'d5ded4',None)
    if style in {'forge','blacksmith'} or b.get('station')=='forge':
        p.rect((w-30,8,w-14,eave-2),'6c6c67',INK)
        for yy in range(10,eave-2,8): p.line([(w-28,yy),(w-16,yy)],'929483')
        p.rect((w-32,6,w-12,11),'aaa48d',INK)
    p.rect((doorx-19,bottom-1,doorx+19,h-1),'6a726e',INK); p.line([(doorx-17,bottom),(doorx+17,bottom)],'a5a68e')
    return im


def resource(definition):
    skill=definition['skill']; ident=definition['id']
    if skill=='woodcutting': return tree('pine' if 'pine' in ident or 'frost' in ident else 'oak')
    if skill in {'mining','prospecting','excavation'}:
        im=prop('rock'); p=Pixel(im); metal=next((METALS[m] for m in METALS if m in ident),'b8ab77')
        for x,y in [(16,41),(28,39),(24,49),(34,47)]: p.poly([(x-2,y),(x,y-4),(x+4,y-2),(x+3,y+2)],metal); p.dot(x,y-2,shade(metal,1.3,15))
        return im
    if skill=='fishing':
        im=canvas((48,48)); p=Pixel(im)
        for x,y in [(15,28),(29,17),(31,32)]: p.d.arc((x-9,y-3,x+9,y+3),0,300,fill=rgba('9dcbcc'),width=1); p.line([(x-3,y),(x+2,y-1),(x+5,y)],'b4b9a0',2)
        return im
    if skill in {'farming','herbalism','foraging'}:
        return prop('mushrooms' if 'mushroom' in ident else 'reeds' if skill=='farming' else 'flowers')
    return prop('crystal' if 'crystal' in ident else 'stump')


def structure(ident):
    im=canvas((64,72)); p=Pixel(im)
    if 'campfire' in ident:
        for x,y in [(19,63),(44,64),(14,54),(48,53),(31,67)]: stone(p,x,y,13,9)
        p.limb((19,59),(44,48),5,'9a7650'); p.limb((19,47),(43,60),5,'8b6547')
        p.poly([(20,52),(26,36),(27,23),(35,35),(40,29),(46,49),(37,58),(26,58)],'d27a47'); p.poly([(27,53),(32,38),(35,48),(40,43),(38,56)],'edc071',None)
    elif 'forge' in ident:
        for yy in range(20,62,10):
            for xx in range(9,53,11): p.rect((xx,yy,xx+10,yy+9),'80877f',INK)
        p.rect((20,35,43,56),'3d3636',INK); p.poly([(23,53),(26,40),(31,46),(36,36),(40,54)],'d6964e'); p.rect((9,16,54,22),'a5a992',INK)
    elif 'anvil' in ident:
        p.plank((23,49,42,67),'866345'); p.poly([(14,31),(53,31),(50,40),(37,41),(36,48),(46,53),(17,53),(26,46),(25,39),(9,37)],'88979c'); p.line([(16,33),(50,33)],'cad3c3',2)
    else:
        p.plank((6,32,59,43),'9c7b50'); p.plank((10,43,17,67),'816246'); p.plank((48,43,55,67),'816246'); p.limb((14,57),(51,57),4,'795b41')
        if 'rune' in ident or 'enchan' in ident: crystal(p,32,32,21,'b1a7ce')
        elif 'loom' in ident or 'tailor' in ident:
            p.plank((13,6,17,34),'a28157'); p.plank((47,6,51,34),'a28157'); p.plank((13,5,51,10),'a28157')
            for xx in range(20,47,3): p.line([(xx,11),(xx,34)],'c6b99c')
        elif 'alchemy' in ident:
            for x in (19,35,47): p.sphere((x-5,19,x+5,32),'79a695'); p.rect((x-2,14,x+2,19),'cab991',INK)
        else: p.plank((18,24,44,28),'c1a078'); p.line([(43,23),(51,12)],'877657',3); p.rect((44,8,55,14),'9aa5a2',INK)
    return im
