"""Native-resolution environment art built from physical forms and material ramps."""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, rgba, shade, palette, seed, INK, METALS

GROUND = {
    'grass': '697c51', 'dirt': 'a28e6d', 'stone': '91948b', 'sand': 'c7b58e',
    'snow': 'cbd6d2', 'water': '487888', 'lava': '654338', 'wall': '667174',
    'wood': '967753', 'moss': '516f54', 'crystal': '777f8d', 'marsh': '637b62', 'ash': '736e67'
}


def terrain(kind, variant=0):
    image = Image.new('RGBA', (32, 32), rgba(GROUND[kind])); p = Pixel(image)
    base = GROUND[kind]; c = palette(base)
    if kind in {'stone', 'wall'}:
        p.rect((0, 0, 31, 31), shade(base, .66))
        for row in range(4):
            y = row * 8; offset = -8 if row % 2 else 0
            for x in range(offset, 32, 16):
                tone = shade(base, .88 + .035 * ((row + x // 8 + variant) % 4))
                p.poly([(x + 1, y + 1), (x + 13, y + 1), (x + 15, y + 3), (x + 14, y + 6), (x + 2, y + 7), (x, y + 5)], tone, None)
                p.line([(x + 2, y + 2), (x + 12, y + 2)], shade(base, 1.17))
                p.line([(x + 3, y + 6), (x + 13, y + 6)], shade(base, .78))
        if kind == 'wall': p.line([(0, 0), (31, 0)], shade(base, 1.3)); p.rect((0, 29, 31, 31), shade(base, .5))
    elif kind == 'wood':
        for y in range(0, 32, 8):
            p.plank((0, y, 31, y + 7), shade(base, .94 + ((y // 8 + variant) % 3) * .06))
            joint = (13 + y + variant * 5) % 32; p.line([(joint, y), (joint, y + 7)], c[1])
            if y == 8: p.ellipse((20, 11, 26, 14), c[2], c[1]); p.dot(23, 12, c[0])
    elif kind in {'water', 'lava'}:
        if kind == 'water':
            for y in (4, 13, 24):
                points = [(x, y + round(math.sin((x / 32 + variant / 4) * math.tau) * 1.5)) for x in range(33)]
                p.line(points, shade(base, 1.12), 2)
                p.line([(x, yy + 2) for x, yy in points], shade(base, .84))
            for x, y in ((5, 8), (20, 18), (28, 29)):
                x = (x + variant * 3) % 32; p.line([(x, y), (x + 4, y)], '8badae'); p.dot(x + 1, y - 1, 'a6bfba')
        else:
            for points in [[(-2, 8), (8, 11), (14, 4), (21, 9), (34, 7)], [(5, 33), (10, 23), (21, 24), (25, 14), (34, 18)]]:
                p.line(points, '8e5035', 6); p.line(points, 'c97842', 3); p.line(points, 'eeb267' if variant % 2 else 'e4a35b', 1)
            for x, y in ((5, 19), (18, 15), (28, 28)): p.poly([(x-3,y),(x,y-3),(x+4,y),(x+2,y+4)], '5c514a', None)
    else:
        # Each mark is a small coherent grass blade, pebble, or material cluster.
        marks = [(3, 5), (17, 3), (26, 12), (9, 17), (20, 24), (3, 29), (30, 28)]
        for i, (x, y) in enumerate(marks):
            x = (x + variant * 7) % 32; y = (y + variant * 3) % 32
            if kind in {'grass', 'moss', 'marsh'}:
                p.line([(x-2, y+2), (x, y), (x+1, y+2)], shade(base, .79))
                p.line([(x, y+1), (x-1, y-2)], shade(base, 1.14)); p.line([(x+1, y+2), (x+3, y-1)], shade(base, 1.07))
            elif kind == 'crystal':
                p.poly([(x-3,y),(x,y-3),(x+4,y+1),(x,y+4)], shade(base, 1.14), None); p.line([(x-2,y),(x,y-2),(x+2,y)], shade(base, 1.35))
            else:
                p.poly([(x-2,y),(x+1,y-1),(x+3,y+1),(x,y+2)], shade(base, .91 if kind == 'snow' else .83), None)
                p.line([(x-1,y),(x+1,y)], shade(base, 1.08))
    return image


def leaf_mass(p, cx, cy, rx, ry, base):
    c = palette(base)
    outline = [(cx-rx,cy),(cx-rx+3,cy-ry*.55),(cx-rx*.55,cy-ry*.75),(cx-rx*.3,cy-ry),(cx+rx*.2,cy-ry*.87),(cx+rx*.57,cy-ry*.72),(cx+rx,cy-ry*.22),(cx+rx*.9,cy+ry*.4),(cx+rx*.55,cy+ry*.75),(cx+rx*.1,cy+ry),(cx-rx*.5,cy+ry*.78),(cx-rx*.9,cy+ry*.3)]
    p.poly(outline, c[1], c[0])
    p.poly([(cx-rx+3,cy-1),(cx-rx*.6,cy-ry*.6),(cx,cy-ry+2),(cx+rx*.63,cy-ry*.45),(cx+rx-4,cy+ry*.1),(cx+rx*.3,cy+ry*.45),(cx-rx*.3,cy+ry*.5)], c[2], None)
    p.poly([(cx-rx*.6,cy-ry*.45),(cx-rx*.2,cy-ry*.76),(cx+rx*.32,cy-ry*.56),(cx+rx*.52,cy-ry*.1),(cx,cy+ry*.13),(cx-rx*.5,cy)], c[3], None)
    for dx, dy, sx in [(-.45,-.3,1),(-.2,-.6,-1),(.1,-.35,1),(.45,-.18,-1),(-.12,.15,1),(.42,.37,1),(-.62,.18,-1)]:
        x = cx + rx*dx; y = cy+ry*dy
        p.poly([(x-3,y),(x,y-2),(x+4,y),(x+sx,y+3)], c[4] if dy < 0 else c[3], None)
        if dy < -.2: p.line([(x-1,y-1),(x+1,y-1)],c[5])


def tree(kind):
    pine = kind in {'pine', 'snow_pine'}; image = canvas((96, 144 if pine else 128)); p = Pixel(image); h = image.height; x = 48
    bark = '826343' if kind not in {'dead_tree','snow_pine'} else '827768'; c = palette(bark)
    p.poly([(x-8,h-7),(x-4,56),(x+6,54),(x+9,h-9),(x+20,h-4),(x+10,h-2),(x+2,h-6),(x-12,h-2),(x-21,h-4)], c[2])
    p.poly([(x-3,62),(x+1,62),(x+2,h-9),(x-6,h-5)], c[4], None)
    for dx in (-5,3,6): p.line([(x+dx,66),(x+dx-1,89),(x+dx+2,h-11)],c[1])
    p.line([(x-12,h-5),(x-5,h-10)], c[5]); p.ellipse((x-3,93,x+4,105),c[1],c[0]); p.line([(x-1,96),(x-1,102)],c[4])
    if kind == 'dead_tree':
        for points in [[(48,83),(29,60),(24,31),(17,21)],[(49,66),(64,47),(72,18)],[(46,49),(41,25),(47,9)],[(29,60),(11,51),(7,32)],[(63,49),(86,39),(88,25)]]:
            p.line(points,c[0],7);p.line(points,c[2],5);p.line([(a-1,b-1) for a,b in points],c[4],1)
        return image
    if kind == 'palm':
        for tx,ty in [(6,36),(16,11),(37,7),(70,10),(89,30),(91,51),(73,69),(19,67)]:
            p.line([(48,46),((48+tx)/2,(46+ty)/2-9),(tx,ty)],'335945',4)
            for i in range(1,8):
                t=i/8;px=48+(tx-48)*t;py=46+(ty-46)*t-math.sin(t*math.pi)*8
                p.line([(px,py),(px-5,py+8)],'688459',2);p.line([(px,py),(px+5,py+5)],'8c9e66')
        for cx,cy in [(42,47),(51,51),(56,44)]: p.sphere((cx-4,cy-4,cx+4,cy+5),'8d7050')
        return image
    if pine:
        for y, width in [(91,42),(66,35),(42,26),(21,17)]:
            points=[(48,y-21),(48+width*.3,y-8),(48+width*.7,y+6),(48+width,y+19),(48+width*.6,y+16),(48+width*.67,y+25),(48+width*.2,y+21),(48,y+28),(48-width*.25,y+21),(48-width*.72,y+25),(48-width*.55,y+16),(48-width,y+19),(48-width*.55,y+1)]
            p.poly(points,'3d6255','2d493f');p.poly([(48,y-18),(48+width*.5,y+5),(48,y+16),(48-width*.67,y+18),(48-width*.35,y)],'547962',None)
            for dx,dy in [(-.4,8),(-.15,-2),(.1,6),(.35,12)]: p.line([(48+width*dx,y+dy),(48+width*dx+5,y+dy+2)],'8caa7c',2)
            if kind == 'snow_pine':
                p.poly([(48,y-19),(48+width*.3,y-7),(48+width*.55,y+6),(48+width*.2,y+4),(48+width*.05,y+8),(48-width*.35,y+6),(48-width*.54,y+13),(48-width*.28,y-5)],'c4d1cb',None)
                p.line([(47,y-13),(48-width*.24,y)],'e1e4d8',2)
        return image
    base='6e8a52' if kind=='oak' else '597e5b' if kind=='ancient_oak' else '728b58'
    for points in [[(47,83),(29,58),(17,44)],[(52,83),(71,59),(80,42)],[(48,64),(42,29)]]:
        p.line(points,c[0],8);p.line(points,c[3],5)
    for cx,cy,rx,ry in [(22,65,20,19),(73,66,21,20),(48,69,26,24),(20,45,18,21),(74,45,20,21),(47,30,28,24),(48,51,29,23)]:
        leaf_mass(p,cx,cy,rx,ry,base)
    if kind=='ancient_oak':
        p.line([(20,70),(18,89),(22,99)],'739573',2);p.line([(70,72),(76,88)],'819c76',2)
    if kind=='willow':
        for x in range(14,84,7):
            y=57+int(abs(x-48)*.25)
            p.line([(x,y),(x-3,y+14),(x-1,y+34)],'526e4c',3)
            for dy in (4,10,16,22,29): p.line([(x-2,y+dy),(x+2,y+dy+4)],'90a76c',2)
    return image


def rock(kind='rock', ore=''):
    image=canvas((56,44));p=Pixel(image);base='b4c3c6' if kind=='snow_rock' else '616269' if kind=='basalt' else '929488';c=palette(base)
    p.poly([(5,30),(10,14),(20,5),(39,7),(51,21),(49,35),(28,40),(8,36)],c[1])
    p.poly([(10,15),(20,6),(38,8),(43,19),(23,24),(6,29)],c[3]);p.poly([(23,24),(43,19),(50,23),(48,34),(28,38)],c[2]);p.poly([(12,16),(21,9),(33,10),(23,18)],c[4],None)
    p.line([(12,15),(22,7),(37,9)],c[5]);p.line([(23,25),(27,35)],c[0]);p.line([(31,15),(35,20)],c[1])
    if kind=='snow_rock':p.poly([(9,17),(19,6),(39,7),(44,19),(37,17),(31,22),(21,19),(14,24)],'dce1d6',None)
    if ore:
        color=METALS.get(ore,'bba879')
        for x,y in [(16,18),(28,12),(37,25),(20,31)]:
            p.poly([(x-4,y),(x,y-4),(x+5,y-1),(x+3,y+4),(x-3,y+3)],shade(color,.65));p.poly([(x-2,y),(x,y-2),(x+3,y),(x+1,y+2)],color,None);p.dot(x-1,y-1,shade(color,1.25,12))
    return image


def chest(kind='weathered', opened=False):
    image=canvas();p=Pixel(image)
    wood='967047' if kind not in {'cursed','ancient'} else '6a5b69' if kind=='cursed' else '959180';metal='c5a866' if kind=='royal' else 'a3a29a';c=palette(wood);m=palette(metal)
    p.poly([(8,31),(18,25),(55,28),(55,52),(45,58),(8,53)],c[1]);p.rect((9,32,45,52),c[2],INK);p.poly([(46,32),(54,28),(54,51),(46,56)],c[1])
    for y in (38,45,51):p.line([(10,y),(44,y)],c[0]);p.line([(11,y-1),(43,y-1)],c[4])
    p.line([(49,33),(49,51)],c[3]);p.line([(53,32),(53,48)],c[0])
    if opened:
        p.poly([(9,11),(45,7),(54,13),(54,28),(45,34),(9,30)],c[2]);p.poly([(13,13),(44,10),(49,14),(49,26),(44,29),(13,27)],c[0]);p.line([(14,14),(43,11)],c[4]);p.poly([(9,32),(19,27),(54,30),(45,37)],'332f2e')
    else:
        p.ellipse((8,15,47,41),c[2],INK);p.rect((8,28,46,36),c[3],INK);p.poly([(46,19),(55,24),(55,32),(46,36)],c[1]);
        p.line([(11,25),(44,25)],c[5]);p.line([(12,19),(41,19)],c[4]);p.line([(10,30),(44,30)],c[1])
    for x in (15,38):
        p.rect((x,17 if not opened else 10,x+4,53),m[2],INK);p.line([(x+1,20),(x+1,50)],m[4]);
        for y in (23,33,46,51):p.dot(x+2,y,m[5])
    p.rect((24,33,31,44),m[3],INK);p.rect((26,36,29,41),m[0]);p.dot(27,36,m[5]);
    if kind in {'runic','cursed'}:
        color='94bab2' if kind=='runic' else 'b191bb'
        for x in (21,34):p.line([(x,46),(x-2,41),(x,38),(x+2,41),(x,46)],color)
    if kind=='royal':
        p.line([(10,52),(44,52),(53,49)],m[4],2);p.poly([(23,25),(23,20),(27,23),(30,18),(33,23),(36,20),(35,26)],m[3]);p.dot(29,23,'e8d5a0')
    if kind=='mimic':
        p.rect((9,31,45,40),'37282c',INK)
        for x in range(12,43,6):p.poly([(x,32),(x+4,32),(x+2,38)],'dcd0aa');p.poly([(x+2,39),(x+6,39),(x+4,34)],'c9b692')
        p.line([(30,38),(34,48),(27,55),(22,55)],'bf786c',5);p.line([(30,40),(32,47),(26,53)],'e6a18b')
        p.limb((10,49),(3,59),4,'79794f');p.limb((50,49),(60,58),4,'79794f')
    return image


def prop(kind):
    if kind in {'oak','ancient_oak','pine','snow_pine','willow','dead_tree','palm'}:return tree(kind)
    if kind in {'rock','snow_rock','basalt'}:return rock(kind)
    if kind=='shadow':
        image=canvas((48,20));p=Pixel(image);p.ellipse((2,3,46,18),(15,24,22,42));p.ellipse((8,6,40,15),(12,18,18,40));return image
    image=canvas();p=Pixel(image)
    if kind=='stump':
        p.poly([(18,30),(44,30),(47,51),(55,58),(42,59),(34,54),(22,59),(9,57),(17,48)],'775b3d');p.ellipse((16,22,46,39),'b89967',INK);p.ellipse((21,26,41,35),'d2b782','8e714f');p.ellipse((26,28,36,33),'b99562','9d7b50');p.line([(21,41),(20,52)],'aa8757');p.line([(41,40),(43,51)],'4d4233')
    elif kind in {'bush','flowers','herb','grass_tuft','reeds','mushrooms','crop','sprout'}:
        if kind=='bush':
            for cx,cy,rx,ry in [(20,46,16,12),(43,44,17,14),(31,34,18,15)]:leaf_mass(p,cx,cy,rx,ry,'789061')
            for x,y in [(18,41),(34,31),(40,49),(29,48)]:p.sphere((x-2,y-2,x+2,y+2),'bd7662')
        elif kind=='mushrooms':
            for x,y,r in [(20,47,13),(43,52,11),(35,31,14)]:
                p.limb((x,y),(x,y-13),5,'c5b391');p.ellipse((x-r,y-24,x+r,y-9),'a97d69',INK);p.line([(x-r+3,y-12),(x+r-3,y-12)],'e0cfa7');
                for dx,dy in [(-5,-18),(3,-21),(6,-15)]:p.rect((x+dx,y+dy,x+dx+2,y+dy+1),'d9c594')
        else:
            for i,x in enumerate((13,23,34,45,52)):
                height=(14 if kind=='sprout' else 24 if kind=='grass_tuft' else 34)+((i*7)%17);top=58-height
                p.line([(x,59),(x-3,top+13),(x-1,top)],'557249',2)
                p.line([(x-1,52),(x-12,43),(x-14,36)],'7c9d5b',2);p.line([(x-1,48),(x+9,39),(x+11,29)],'8fa764',2)
                if kind=='reeds':p.limb((x-1,top+8),(x-1,top-2),3,'967d54');p.line([(x-2,top),(x-2,top+6)],'c2a371')
                elif kind=='crop':
                    for dy in (0,4,8,12):p.poly([(x-1,top+dy),(x-6,top+dy-3),(x-5,top+dy-6),(x,top+dy-1)],'c2ad67');p.line([(x-2,top),(x-2,top+13)],'e2cd87')
                elif kind in {'flowers','herb'}:
                    for dx,dy in [(0,-3),(3,-1),(2,3),(-2,3),(-3,-1)]:p.ellipse((x+dx-2,top+dy-2,x+dx+2,top+dy+2),'c7b4c1' if i%2 else 'c6a768')
                    p.dot(x,top,'eee0ac')
    elif kind=='crystal':
        for x,y,w,h in [(20,55,13,31),(38,58,17,48),(51,57,10,23)]:
            p.poly([(x-w//2,y),(x-w//2,y-h+10),(x,y-h),(x+w//2,y-h+9),(x+w//2,y-3)],'697e99');p.poly([(x-w//2+1,y-h+10),(x,y-h+2),(x,y-3),(x-w//2+1,y-1)],'a7bcc5',None);p.line([(x-2,y-h+8),(x-2,y-7)],'d1d9d5')
    elif kind=='cactus':
        p.limb((32,59),(32,13),12,'618368');p.limb((28,40),(16,37),8,'618368');p.limb((16,38),(15,25),8,'618368');p.limb((37,33),(49,29),8,'618368');p.limb((49,29),(49,19),8,'618368')
        for x,y in [(30,17),(33,27),(30,38),(35,48),(16,28),(48,23)]:p.line([(x,y),(x+2,y+2)],'b8bd88')
    elif kind=='signpost':
        p.plank((28,11,34,59),'92714b');p.poly([(8,14),(43,14),(52,20),(43,26),(8,26)],'b0915f');p.line([(12,17),(40,17)],'d2b47b');p.line([(12,23),(38,23)],'71543b');p.dot(30,20,'423d34');p.poly([(51,31),(18,31),(9,37),(18,43),(51,43)],'9c7f55');p.line([(22,34),(46,34)],'cbb180');p.dot(30,37,'423d34')
    elif kind=='waystone':
        p.poly([(16,57),(20,17),(28,6),(42,8),(49,18),(48,58)],'748788');p.poly([(20,18),(28,9),(32,11),(30,53),(18,56)],'a7b1a1',None);p.poly([(33,19),(41,24),(39,39),(30,44),(26,31)],'425963');p.line([(33,22),(38,28),(33,39),(29,31),(33,22)],'97cfc0',2);p.line([(22,50),(44,50)],'bac4aa');p.rect((10,56,54,62),'596c6c',INK)
    elif kind=='stairs':
        for i in range(6):
            y=12+i*8;left=17-i*2;right=47+i*2;p.poly([(left,y),(right,y),(right+2,y+5),(left-2,y+5)],'90958b');p.rect((left-2,y+5,right+2,y+8),'59635f');p.line([(left,y),(right,y)],'c0bfa9')
    elif kind=='loot':
        p.poly([(21,21),(42,21),(40,28),(50,43),(48,55),(36,61),(17,57),(12,45),(24,29)],'9e8260');p.line([(23,27),(39,27)],'504737',3);p.poly([(23,33),(19,46),(25,53),(30,51),(27,40)],'c5ac7b',None);p.line([(40,35),(44,48),(39,55)],'725b44')
        for x,y in [(45,55),(54,59),(50,49)]:p.sphere((x-4,y-2,x+4,y+2),'cdb779')
    elif kind=='barrel':
        p.ellipse((13,6,49,22),'b49361',INK);p.poly([(13,14),(49,14),(53,29),(50,56),(13,56),(10,32)],'916f49');p.ellipse((13,48,50,61),'7d6247',INK)
        for x in (16,23,31,39,46):p.line([(x,15),(x-2 if x<30 else x+2,33),(x,55)],'4e4438');p.line([(x+1,17),(x+1,53)],'b4915e')
        for y in (20,46):p.rect((11,y,51,y+5),'788183',INK);p.line([(13,y+1),(49,y+1)],'a9ae9d')
        p.ellipse((14,7,48,20),'b79a6b',INK);p.line([(18,12),(44,12)],'8c714e');p.line([(20,16),(43,16)],'8c714e')
    elif kind=='crate':
        p.poly([(7,21),(19,11),(56,17),(56,52),(44,61),(7,54)],'826545');p.plank((8,24,43,54),'a28253');p.poly([(44,24),(55,18),(55,52),(44,59)],'715a40');p.poly([(8,22),(19,13),(54,18),(43,26)],'b49868');
        p.line([(11,28),(39,50)],'d0b17b',5);p.line([(11,51),(39,29)],'c2a06b',4)
        for x,y in [(11,29),(39,30),(11,50),(39,51)]:p.dot(x,y,'574f42')
    elif kind in {'anvil','forge'}:
        p.plank((17,47,47,61),'7d6549');p.poly([(21,26),(44,26),(40,41),(46,45),(17,45),(25,40)],'5b6d76');p.poly([(7,15),(46,15),(57,19),(48,24),(13,24),(4,20)],'a1b0af');p.poly([(13,24),(48,24),(45,30),(19,31)],'75868b');p.line([(9,17),(45,17),(52,19)],'d4d8c7');p.rect((24,16,29,20),'48555e')
    elif kind=='campfire':
        for a,b in [((13,55),(49,43)),((14,43),(47,57))]:p.limb(a,b,7,'8a6545')
        p.poly([(16,46),(21,31),(29,36),(33,13),(39,29),(42,24),(49,43),(41,52),(25,53)],'b96842');p.poly([(23,44),(28,32),(31,40),(36,26),(42,44),(36,50),(28,50)],'e4a15b');p.poly([(29,45),(33,34),(38,45),(34,49)],'efd292')
    elif kind in {'bench','rune_table','loom'}:
        p.plank((7,26,55,37),'9e7c51');p.plank((11,38,18,60),'775b40');p.plank((46,38,53,60),'775b40');p.limb((15,49),(49,49),4,'6a533c')
        if kind=='rune_table':p.poly([(16,24),(34,15),(48,24),(30,32)],'798b95');p.line([(31,18),(39,24),(30,29),(23,24),(31,18)],'afcbbd')
        elif kind=='loom':
            p.plank((10,4,15,40),'a17e53');p.plank((48,4,53,40),'a17e53');p.plank((12,6,51,11),'b99866');
            for x in range(18,48,3):p.line([(x,12),(x,35)],'c6baa0')
            for y in range(23,35,3):p.line([(18,y),(46,y)],'8c9a8e',2)
        else:p.rect((20,18,26,25),'b5b6a3',INK);p.limb((34,21),(47,28),3,'8b6d46')
    elif kind=='fish_spot':
        for box in [(5,39,59,58),(13,44,52,54)]:p.ellipse(box,(100,158,165,75),(154,194,190,125))
        p.poly([(22,45),(18,37),(19,50)],'93ada5');p.sphere((22,39,46,51),'bac1aa');p.dot(42,43,'26383a')
    elif kind=='dig_site':
        p.ellipse((4,34,60,62),'74664f','a18c63');p.ellipse((13,38,50,57),'3e4140');p.poly([(17,47),(25,37),(39,39),(46,49),(35,54),(22,53)],'989283');p.line([(22,44),(35,45),(39,48)],'c4b79b');p.rect((9,29,16,39),'a28557',INK)
    elif kind=='pelt':
        p.poly([(15,19),(28,22),(40,17),(45,28),(55,36),(48,43),(50,58),(36,53),(25,61),(17,53),(5,55),(12,42),(8,29)],'9c8565');p.poly([(21,28),(36,26),(43,38),(36,49),(22,49),(16,39)],'b4a07d',None);p.line([(27,27),(28,49)],'736348');p.line([(15,30),(20,44)],'cbb58b')
    else:
        raise ValueError('No authored prop renderer for '+kind)
    return image


def resource(definition):
    skill=definition['skill'];ident=definition['id'];name=definition.get('name','').lower()
    if skill=='woodcutting':return tree('pine' if 'pine' in name else 'ancient_oak' if any(x in name for x in ['elder','iron','star']) else 'oak')
    if skill=='mining':return rock('rock',next((m for m in METALS if m in ident),'iron'))
    if skill=='fishing':return prop('fish_spot')
    if skill=='farming':return prop('crop')
    if skill=='skinning':return prop('pelt')
    if skill in {'excavation','treasure_hunting'}:return prop('dig_site')
    if skill=='herbalism':return prop('herb')
    if skill=='foraging':return prop('mushrooms' if 'mushroom' in name else 'bush')
    return prop('crystal')


CITY_PALETTES={
    'dawnreach':('965e54','c9bea3','6c5743'), 'emberhold':('696d74','a09b91','675b4d'),
    'thornhollow':('708a5b','b3a47d','70583e'), 'frostgate':('71848d','c0c6bd','79674f'),
    'gloamport':('557c78','b9bba5','675e49'), 'wayfarers_rest':('b19a69','c6b89a','785b42')}


def building(zone,b):
    w=b['width']*32;h=(b['height']+2)*32;image=canvas((w,h));p=Pixel(image)
    roof,wall,wood=CITY_PALETTES.get(zone['id'],CITY_PALETTES['wayfarers_rest']);r=palette(roof);s=palette(wall);t=palette(wood)
    name=(b.get('name','')+' '+b.get('style','')+' '+b.get('station','')).lower();eave=max(44,round(h*.47));bottom=h-8;left=8;right=w-10
    p.poly([(left+5,eave-5),(right-10,eave-5),(right-2,bottom),(left+5,bottom)],s[2]);p.poly([(right-10,eave),(right,eave-8),(right,bottom-7),(right-10,bottom)],s[1])
    p.rect((left+7,eave+2,right-12,bottom-6),s[3]);p.line([(left+8,eave+4),(right-14,eave+4)],s[4])
    if zone['id'] in {'dawnreach','emberhold','frostgate'} or any(x in name for x in ('bank','temple','tower','forge')):
        for y in range(eave+8,bottom-3,11):
            p.line([(left+7,y),(right-12,y)],s[1]);offset=9 if (y//11)%2 else 0
            for x in range(left+8+offset,right-12,20):p.line([(x,y-10),(x,y)],s[2])
    else:
        for x in (left+9,w//2,right-17):p.plank((x,eave,x+6,bottom-4),wood)
        p.plank((left+7,bottom-17,right-12,bottom-10),wood)
        for x in range(left+14,right-26,35):p.line([(x,eave+10),(x+25,bottom-22)],t[2],4)
    # Roof courses follow the gable boundary; cut tiles and edge caps remain legible.
    ridge=w//2;peak=9
    roof_points=[(2,eave+5),(ridge,peak),(w-3,eave+4),(w-6,eave+14),(ridge,eave//2),(6,eave+14)]
    if zone['id']=='gloamport':roof_points=[(3,eave+5),(w*.2,peak+10),(w*.72,peak),(w-3,eave+5),(w-6,eave+14),(5,eave+14)]
    p.poly(roof_points,r[1],INK)
    for y in range(peak+7,eave+7,7):
        if zone['id']=='gloamport':lo=max(6,int(w*.2*(1-(y-peak)/max(1,eave-peak))));hi=min(w-6,int(w*.72+(w*.28)*(y-peak)/max(1,eave-peak)))
        else:lo=max(4,int(ridge*(1-(y-peak)/max(1,eave-peak))));hi=min(w-4,w-lo)
        for x in range(lo-12,hi,12):
            x0=max(lo,x+(6 if (y//7)%2 else 0));x1=min(hi,x0+11)
            if x1<=x0:continue
            p.poly([(x0,y),(x1,y),(x1-1,y+5),(x0+1,y+6)],r[2+((x//12+y//7)%2)],None);p.line([(x0+1,y+1),(x1-1,y+1)],r[4]);p.line([(x0+2,y+6),(x1-1,y+5)],r[0])
    p.line([(4,eave+7),(ridge,peak+2),(w-5,eave+7)],r[4],3);p.line([(8,eave+13),(w-8,eave+13)],t[0],4)
    if zone['id']=='frostgate':
        p.line([(5,eave+4),(ridge,peak),(w-5,eave+4)],'d9e1da',7);p.line([(9,eave+10),(w-10,eave+10)],'c8d4cf',4)
        for x in range(14,w-12,19):p.line([(x,eave+12),(x-1,eave+20)],'b5d0ce',2)
    if zone['id']=='thornhollow':
        for x,y in [(w*.18,eave-3),(w*.77,eave-10)]:leaf_mass(p,x,y,17,10,'738557')
    if any(x in name for x in ('forge','smith','inn','cottage','house')):
        x=max(20,w-45);p.rect((x,13,x+21,eave-5),'817e75',INK)
        for y in range(17,eave-4,8):p.line([(x+1,y),(x+20,y)],'5a615d');p.line([(x+4,y-5),(x+4,y)],'a09b87')
        p.rect((x-3,10,x+24,17),'a7a08b',INK);p.rect((x+1,10,x+20,12),'383d3d')
    door_w=max(18,min(32,w//6));dx=w//2-door_w//2;dy=max(eave+20,bottom-45)
    p.poly([(dx-3,bottom),(dx-3,dy+8),(dx+3,dy),(dx+door_w-3,dy),(dx+door_w+3,dy+8),(dx+door_w+3,bottom)],s[1],INK)
    p.rect((dx,dy+8,dx+door_w,bottom-2),t[1],INK)
    for x in range(dx+2,dx+door_w,5):p.plank((x,dy+9,x+4,bottom-4),wood)
    for y in (dy+17,bottom-10):p.line([(dx+2,y),(dx+door_w-2,y)],'666f70',3);p.dot(dx+4,y,'b1b5a0')
    p.ellipse((dx+door_w-7,dy+26,dx+door_w-3,dy+30),'d1b775',INK)
    for x in (max(18,w//5-8),min(w-39,w*4//5-8)):
        y=min(bottom-36,eave+29);p.rect((x-3,y-3,x+19,y+27),t[1],INK);p.rect((x,y,x+16,y+24),'3a5359',INK);p.rect((x+2,y+2,x+7,y+10),'bba574');p.rect((x+10,y+3,x+14,y+11),'d2bd87');p.line([(x+8,y),(x+8,y+24)],t[3],2);p.line([(x,y+12),(x+16,y+12)],t[3],2);p.plank((x-5,y-1,x-1,y+24),wood);p.plank((x+17,y-1,x+21,y+24),wood);p.rect((x-6,y+25,x+22,y+29),s[1],INK)
    p.rect((left+6,bottom-2,right-7,bottom+4),s[1],INK);p.line([(left+8,bottom-2),(right-10,bottom-2)],s[4])
    if any(x in name for x in ('shop','market','merchant','provision')):
        x=dx-12;y=dy-12;p.poly([(x,y),(x+door_w+24,y),(x+door_w+32,y+15),(x-8,y+15)],'a67c57');
        for xx in range(x,x+door_w+26,10):p.poly([(xx,y),(xx+5,y),(xx+9,y+15),(xx+3,y+15)],'c8b28a',None)
    if zone['id']=='gloamport':
        for x in (14,w-24):p.line([(x,eave+24),(x+3,bottom-9)],'ad9d72',2);p.ellipse((x-4,bottom-22,x+5,bottom-12),'796a4e','b7a27b')
    return image
