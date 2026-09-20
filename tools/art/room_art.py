"""Original furniture, service-building details, and terrain edge sprites.

The floor footprint comes from content_src.presentation. Furniture sprites extend
upwards by Rise; neither art nor renderer guesses a different collision box.
"""
from __future__ import annotations
import math
from content_src.presentation import FURNITURE
from .common import Pixel, canvas, palette, shade, INK
from .environment_pack import building as old_building

WOOD='866344'
IRON='78828a'
STONE='77776e'
PARCHMENT='d6c69f'


def board(p, box, base=WOOD):
    x0,y0,x1,y1=box; c=palette(base)
    p.rect(box,c[2],c[0]); p.line([(x0+1,y0+1),(x1-1,y0+1)],c[4])
    for y in range(int(y0)+5,int(y1),7):
        p.line([(x0+3,y),(x1-4,y-1)],shade(base,.8))
    p.line([(x0+1,y1-1),(x1-1,y1-1)],c[1])


def bottle(p,x,y,color,large=False):
    r=4 if large else 3; h=14 if large else 10
    p.poly([(x-1,y-h),(x+2,y-h),(x+2,y-h+3),(x+r,y-h+5),(x+r,y-1),
            (x+r-1,y),(x-r+1,y),(x-r,y-1),(x-r,y-h+5),(x-1,y-h+3)],'93a5a0')
    p.rect((x-r+1,y-5,x+r-1,y-1),color); p.line([(x-r+1,y-7),(x-r+1,y-2)],'d4dfce')
    p.rect((x-1,y-h-2,x+2,y-h),'a17a4b',INK)


def book(p,x,y,h,color):
    p.rect((x,y-h,x+5,y),shade(color,.7),INK)
    p.rect((x+1,y-h+1,x+4,y-1),color)
    p.line([(x+1,y-h+3),(x+4,y-h+3)],'c6ae78'); p.line([(x+1,y-3),(x+4,y-3)],'bda674')


def mug(p,x,y):
    p.ellipse((x+3,y-7,x+9,y-1),(0,0,0,0),'b9b7a4',2)
    p.rect((x-3,y-8,x+4,y),'aaaba0',INK); p.line([(x-2,y-6),(x-2,y-1)],'d4d2b9')
    p.ellipse((x-3,y-10,x+4,y-6),'604c34','d3c9a6')


def plate(p,x,y,food=True):
    p.ellipse((x-10,y-5,x+10,y+5),'bebca4',INK)
    p.ellipse((x-7,y-3,x+7,y+3),'ded4b9','888a80')
    if food: p.poly([(x-5,y),(x-2,y-2),(x+4,y-1),(x+5,y+2),(x-3,y+2)],'af754e')


def sack(p,x,y,base='ac9267'):
    p.poly([(x-6,y-26),(x+6,y-26),(x+4,y-21),(x+12,y-8),(x+10,y),(x-9,y+1),(x-12,y-5),(x-4,y-21)],base)
    p.line([(x-6,y-22),(x+5,y-22)],'5c4a32',2)
    p.line([(x-6,y-15),(x-8,y-5),(x-3,y-3)],shade(base,1.1,8))
    p.line([(x+5,y-16),(x+8,y-6)],shade(base,.72))


def rack_weapon(p,x,y,family):
    # The rack holds actual weapon shapes rather than item letters.
    if family=='bow':
        p.line([(x,y-34),(x+8,y-24),(x+10,y-15),(x+5,y-5),(x,y)],'b49161',3)
        p.line([(x,y-34),(x,y)],'d7c9a5'); return
    p.line([(x,y),(x,y-32)],'4a3a2d',4); p.line([(x-1,y-1),(x-1,y-30)],'ab8555',2)
    if family=='sword':
        p.poly([(x-3,y-15),(x-3,y-43),(x,y-50),(x+3,y-43),(x+3,y-15)],IRON)
        p.line([(x-2,y-42),(x-2,y-16)],'d0d6c8'); p.line([(x-7,y-14),(x+7,y-14)],'bda576',3)
    else:
        p.poly([(x,y-35),(x+10,y-39),(x+15,y-35),(x+15,y-25),(x+10,y-22),(x+7,y-28),(x,y-29)],IRON)
        p.line([(x+14,y-34),(x+14,y-26),(x+10,y-24)],'cbd4ce')


def render(kind: str):
    if kind not in FURNITURE: raise ValueError('Unknown furnishing: '+kind)
    tw,th,rise,solid,ground=FURNITURE[kind]
    w,depth=tw*32,th*32; h=depth+rise
    im=canvas((w,h)); p=Pixel(im); wood=palette(WOOD); iron=palette(IRON)
    if ground:
        if kind=='flower_bed':
            p.poly([(2,16),(8,4),(w-9,3),(w-3,14),(w-7,h-4),(10,h-3)],'637d4b',None)
            for x,y in [(10,13),(22,8),(35,16),(48,10),(17,24),(43,24)]:
                p.line([(x,y+3),(x+2,y-3)],'8b9e62'); p.poly([(x-3,y),(x,y-3),(x+3,y),(x,y+3)],'bd9a85' if x%2 else 'd0bd7f',None); p.dot(x,y,'ded1a0')
        elif kind=='paving_mosaic':
            for y in range(4,h-4,10):
                for x in range(4,w-4,14):
                    c='929187' if (x//14+y//10)%3 else '777c74'
                    p.poly([(x,y+2),(x+10,y),(x+12,y+7),(x+1,y+8)],c,None)
            for r in (24,35,39): p.ellipse((w//2-r,h//2-r,w//2+r,h//2+r),(0,0,0,0),'b0a98e')
            for a in range(8):
                t=a*math.tau/8; x=w/2+math.cos(t)*26; y=h/2+math.sin(t)*26
                p.poly([(w/2,h/2),(x-3,y),(x,y-3),(x+3,y)],'697e75',None)
        elif kind=='practice_ring':
            p.ellipse((8,8,w-9,h-9),(0,0,0,0),(185,177,148,170),2)
            p.ellipse((14,14,w-15,h-15),(0,0,0,0),(132,128,112,120))
            for x in (w*.25,w*.75):
                p.line([(x-8,h/2),(x+8,h/2)],(192,182,154,200),2)
                p.line([(x,h/2-8),(x,h/2+8)],(192,182,154,200),2)
                # Paired chalk boot outlines teach the two practice stances.
                # Toe, heel, and worn sole marks remain readable at tile scale.
                for dx,dy in ((-10,-12),(10,7)):
                    bx,by=x+dx,h/2+dy
                    p.poly([(bx-3,by-7),(bx+2,by-8),(bx+4,by-4),(bx+3,by+6),(bx-2,by+7),(bx-4,by+3)],
                           (218,205,169,175),(100,91,76,145))
                    p.line([(bx-2,by-5),(bx+1,by-6),(bx+2,by-3)],(235,222,190,205))
                    p.line([(bx-2,by+3),(bx+2,by+3)],(128,116,95,165))
        else:
            base='73514b' if kind=='rug_warm' else '536b72' if kind=='rug_work' else '7d6951'
            p.rect((3,3,w-4,h-4),shade(base,.65),'3a342b')
            p.rect((7,7,w-8,h-8),base,'b29b6c',2)
            p.rect((14,14,w-15,h-15),shade(base,.9),'938164')
            for x in range(11,w-10,8):
                p.line([(x,3),(x,0)],'b5a079'); p.line([(x,h-4),(x,h-1)],'b5a079')
            for y in range(21,h-18,23):
                for x in range(25,w-20,28):
                    p.poly([(x,y-6),(x+6,y),(x,y+6),(x-6,y)],shade(base,1.15,5),None)
                    p.dot(x,y,'b3a078')
            for y in range(18,h-16,5): p.line([(18,y),(w-19,y)],shade(base,.96))
        return im
    # Consistent low-opacity contact shadow inside the authoritative footprint.
    p.ellipse((2,rise+depth-14,w-3,h-2),(15,15,15,85))
    if kind in ('dining_table','workbench','bar_counter','shop_counter'):
        for x in (5,w-12):
            board(p,(x,depth-7,x+7,h-4),'654930')
        board(p,(3,7,w-4,depth-2),'805c3e')
        for y in range(13,depth-3,8): p.line([(5,y),(w-6,y)],'644b35'); p.line([(5,y+1),(w-6,y+1)],'9d7750')
        p.line([(4,7),(w-5,7)],'bc9360',2)
        if kind=='dining_table':
            for x,y in [(w*.24,23),(w*.72,depth-17)]: plate(p,x,y); mug(p,x+18,y)
            board(p,(w*.45,19,w*.6,33),'bc9460'); p.line([(w*.49,24),(w*.55,22)],'ddbb7d',2)
        elif kind=='bar_counter':
            for x in (16,47,78): mug(p,x,18)
            bottle(p,w-20,24,'7c9060',True)
            for x in range(13,w-8,23): p.rect((x,depth+4,x+16,h-5),'624933','382f27'); p.line([(x+2,depth+6),(x+14,depth+6)],'8f6e49')
        elif kind=='shop_counter':
            p.poly([(13,13),(37,10),(45,18),(42,27),(17,29)],PARCHMENT)
            for y in (16,20,24): p.line([(20,y),(35,y-1)],'837052')
            for x,y in [(66,18),(72,22),(80,17)]: p.ellipse((x-3,y-2,x+3,y+2),'bb9c58',INK); p.dot(x,y-1,'e0c486')
            p.rect((w-26,13,w-8,27),'715e49',INK)
        else:
            p.line([(14,26),(29,13)],'b79a6c',3); p.rect((23,9,37,15),iron[2],INK); p.line([(24,10),(35,10)],iron[4])
            p.line([(46,12),(58,25),(68,12)],iron[3],2)
            p.poly([(74,9),(88,12),(85,25),(71,23)],'c6b899'); p.line([(75,15),(84,17)],'786650')
    elif kind in ('shelf_food','shelf_potions','shelf_goods','bookcase'):
        board(p,(3,3,w-4,h-5),'65503a')
        p.rect((9,9,w-10,h-10),'39382f','211f1b')
        for shelf_y in (26,54,82):
            if shelf_y>h-6: continue
            board(p,(5,shelf_y,w-6,shelf_y+6),'9a7952')
            for index,x in enumerate(range(14,w-10,13)):
                y=shelf_y-1
                if kind=='bookcase': book(p,x-3,y,13+(index%3)*4,('697b83','887159','85645f','8b835f')[index%4])
                elif kind=='shelf_potions': bottle(p,x,y,('92774d','65879c','826385','809457')[index%4],index%3==0)
                elif kind=='shelf_food':
                    if index%3==0: bottle(p,x,y,'807b4f')
                    else:
                        p.ellipse((x-5,y-7,x+6,y),'bc945f',INK); p.line([(x-3,y-4),(x,y-6)],'debb83')
                elif index%2: book(p,x-3,y,16,'8e7753')
                else: p.rect((x-5,y-10,x+5,y),'9a845f',INK); p.line([(x,y-9),(x,y-1)],'c7b288')
    elif kind=='bed':
        board(p,(3,3,w-4,18),'745738')
        board(p,(4,17,w-5,h-6),'60452f')
        p.rect((8,13,w-9,h-15),'a89f83','524c40')
        p.rect((12,15,w-13,34),'d5ceb4','9b957f'); p.line([(14,18),(w-17,18)],'eee2c4')
        p.poly([(9,39),(w-10,37),(w-8,h-16),(10,h-15)],'777d69')
        for y in range(45,h-18,12): p.line([(11,y),(w-12,y-2)],'969b7d')
        for x in (15,31,47): p.line([(x,40),(x+2,h-17)],'5d675a')
        board(p,(3,h-14,w-4,h-5),'85613e')
    elif kind in ('barrel','quench'):
        base='6f614a' if kind=='quench' else '917048'; c=palette(base)
        p.poly([(6,8),(w-7,8),(w-3,20),(w-5,h-7),(w-10,h-4),(9,h-4),(4,h-8),(2,20)],c[2])
        for x in range(7,w-5,6): p.line([(x,15),(x-1,h-9)],c[1]); p.line([(x+1,16),(x,h-10)],c[3])
        for y in (21,h-13): p.rect((4,y,w-5,y+4),iron[2],INK); p.line([(6,y+1),(w-7,y+1)],iron[4])
        p.ellipse((4,4,w-5,17),'426a72' if kind=='quench' else c[3],c[0],2)
        if kind=='quench': p.line([(9,9),(19,8),(23,10)],'90b5b0')
        else: p.line([(7,10),(w-9,10)],c[1]); p.line([(14,6),(14,14)],c[1])
    elif kind in ('hearth','forge'):
        c=palette(STONE)
        p.poly([(5,26),(20,26),(22,3),(w-23,3),(w-21,26),(w-6,26),(w-3,h-5),(3,h-5)],c[2])
        for y in range(7,h-4,10):
            for x in range(7,w-6,19):
                inset=18 if y<27 else 0
                if x<inset+5 or x+17>w-inset-5: continue
                p.rect((x,y,min(x+17,w-7),min(y+8,h-6)),c[2],c[1]); p.line([(x+2,y+1),(min(x+15,w-8),y+1)],c[3])
        opening_y=36
        p.poly([(21,h-20),(21,opening_y+15),(31,opening_y),(w-32,opening_y),(w-22,opening_y+15),(w-22,h-20)],'262725')
        p.rect((17,h-24,w-18,h-16),'4b4537',INK)
        for x in range(29,w-24,11):
            base=h-27
            p.line([(x-6,base),(x+8,base-7)],'6e4d35',5)
            p.poly([(x-6,base-3),(x-5,base-18),(x,base-34),(x+3,base-18),(x+8,base-22),(x+10,base-5),(x+4,base+1)],'bd7044',None)
            p.poly([(x-2,base-4),(x+1,base-21),(x+5,base-8),(x+4,base)],'e3ba69',None)
        if kind=='forge':
            p.rect((12,h-22,w-13,h-14),iron[1],INK)
            for x in range(18,w-17,8): p.line([(x,h-23),(x,h-14)],iron[4])
            p.line([(w-18,37),(w-8,50),(w-13,65)],'5a4835',3)
    elif kind=='anvil':
        board(p,(w*.36,24,w*.67,h-4),'745132')
        p.poly([(3,14),(16,5),(w-7,6),(w-4,15),(w-19,22),(w-28,23),(w-24,32),(w-17,35),(19,35),(26,30),(25,21),(14,20)],iron[2])
        p.line([(6,13),(18,7),(w-8,8)],iron[5]); p.line([(19,18),(w-18,18)],iron[1]); p.rect((w-19,8,w-15,12),iron[0])
    elif kind in ('weapon_rack','map_board','target_board'):
        for x in (6,w-13): board(p,(x,5,x+6,h-4),'745535')
        board(p,(3,13,w-4,20),'96704a'); board(p,(3,h-25,w-4,h-19),'745535')
        if kind=='weapon_rack':
            for x,family in [(18,'sword'),(44,'axe'),(69,'bow')]: rack_weapon(p,x,h-9,family)
        elif kind=='map_board':
            p.poly([(11,23),(w-12,21),(w-10,h-22),(12,h-20)],PARCHMENT)
            p.line([(20,30),(31,37),(29,48),(48,54),(64,45),(w-19,h-28)],'6b8b83',3)
            p.line([(22,h-29),(41,48),(54,32),(w-23,31)],'92734e',2)
            for x,y in [(22,h-29),(54,32),(64,45)]: p.rect((x-2,y-2,x+2,y+2),'97684f')
        else:
            p.ellipse((8,7,w-9,h-20),'b7a076',INK)
            for r,c in ((23,'8b6a51'),(17,'c8b691'),(10,'975c4b'),(4,'d7c699')):
                p.ellipse((w/2-r,(h-16)/2-r,w/2+r,(h-16)/2+r),c,'76634d')
    elif kind=='armor_stand':
        board(p,(w/2-3,10,w/2+3,h-7),'806445'); board(p,(3,h-8,w-4,h-3),'79563a')
        p.poly([(8,28),(13,24),(19,24),(25,28),(27,48),(22,62),(10,62),(5,48)],iron[2])
        p.line([(11,29),(10,44),(16,51),(22,44)],iron[4]); p.line([(16,29),(16,53)],iron[1])
        p.poly([(7,7),(13,3),(21,6),(25,14),(23,24),(18,28),(9,24),(6,16)],iron[3])
        p.line([(9,16),(22,16)],iron[0],3); p.line([(11,7),(15,5)],iron[5])
    elif kind in ('bench','chair'):
        board(p,(4,h-13,w-5,h-7),'896441')
        for x in (5,w-10): board(p,(x,9,x+5,h-4),'725337')
        board(p,(3,4,w-4,13),'a47c4f')
        if kind=='chair': board(p,(3,16,w-4,24),'947049')
    elif kind=='lectern':
        board(p,(w/2-3,20,w/2+3,h-9),'775435'); board(p,(5,h-11,w-6,h-4),'85613e')
        p.poly([(3,17),(23,4),(w-3,14),(10,30)],'95734c')
        p.poly([(6,17),(15,9),(25,13),(22,23),(13,27)],PARCHMENT)
        p.line([(15,11),(14,25)],'968267'); p.line([(8,17),(12,14)],'74674f'); p.line([(18,15),(22,16)],'74674f')
    elif kind=='practice_dummy':
        board(p,(w/2-3,17,w/2+3,h-5),'866947'); board(p,(3,h-9,w-4,h-4),'6f5539')
        p.line([(3,30),(w-4,30)],'9b8057',5)
        p.poly([(8,24),(22,24),(25,45),(20,55),(10,55),(6,45)],'b39767')
        p.ellipse((8,5,23,22),'bca779',INK); p.line([(10,14),(21,14)],'6e634a')
        p.line([(7,33),(24,38)],'78613b',2); p.line([(9,45),(21,42)],'8a6f48',2)
    elif kind=='ore_sacks':
        sack(p,18,h-5); sack(p,46,h-7,'857e68')
        for x,y in [(13,h-24),(19,h-24),(44,h-26),(49,h-24)]: p.poly([(x-3,y),(x,y-4),(x+4,y-1),(x+1,y+3)],'77838b'); p.dot(x,y-2,'b5bcb1')
    elif kind=='woodpile':
        for x,y in [(13,h-7),(30,h-7),(47,h-7),(22,h-20),(40,h-20)]:
            p.poly([(x-9,y-13),(x+5,y-16),(x+10,y-5),(x-4,y)],'6f5033')
            p.ellipse((x-8,y-10,x+8,y),'ae8755',INK); p.ellipse((x-4,y-7,x+4,y-2),(0,0,0,0),'705435')
    elif kind=='crate_stack':
        for x,y,ww,hh in [(3,28,34,40),(29,36,32,32),(12,4,32,30)]:
            y=min(y,h-hh-3); board(p,(x,y,x+ww-2,y+hh-2),'97734a')
            p.line([(x+3,y+4),(x+ww-6,y+hh-6)],'b38a59',4)
            for yy in (y+4,y+hh-7): p.line([(x+2,yy),(x+ww-3,yy)],'594b3a',2)
    elif kind=='well':
        p.ellipse((4,h-49,w-5,h-6),'808078',INK); p.ellipse((11,h-48,w-12,h-22),'303936','b1ad98',3)
        for y in (h-23,h-13): p.line([(7,y),(w-8,y)],'555b57')
        for x in (9,w-16): board(p,(x,14,x+6,h-15),'81603f')
        board(p,(6,13,w-7,20),'9a7952')
        p.poly([(1,14),(w/2,1),(w-2,14),(w-7,22),(w/2,10),(6,22)],'63766e')
        p.line([(w/2,17),(w/2,h-28)],'c0a87a'); p.rect((w/2-6,h-37,w/2+6,h-25),'7d7660',INK)
    elif kind=='fence':
        for x in (4,w/2,w-10):
            p.poly([(x,9),(x+3,3),(x+6,9),(x+6,h-3),(x,h-3)],'87694a'); p.line([(x+1,11),(x+1,h-5)],'b49a6d')
        board(p,(3,19,w-4,25),'93724d'); board(p,(3,38,w-4,44),'806142')
    elif kind=='cart':
        for x in (6,w-15): p.ellipse((x,h-29,x+11,h-5),'766342',INK); p.line([(x+5,h-26),(x+5,h-8)],'c0a071')
        board(p,(13,20,w-13,h-15),'86613d'); board(p,(13,9,w-13,23),'9c764b')
        p.line([(17,h-18),(5,h-2)],'6c5037',4); p.line([(w-18,h-18),(w-6,h-2)],'6c5037',4)
        sack(p,38,h-23); sack(p,61,h-26,'908263')
    else:
        raise ValueError('Furnishing lacks an authored construction: '+kind)
    return im


def edge(mask: int, base='grass'):
    """Sparse transition pixels on the neighboring path tile; no smoothing."""
    im=canvas((32,32)); p=Pixel(im)
    c=palette('718153' if base=='grass' else '988161')
    for side,bit in enumerate((1,2,4,8)):
        if not mask & bit: continue
        for n in range(0,32,4):
            depth=2+(n//4+side)%3
            pts=[(n,0),(n+3,0),(n+2,depth),(n+1,1),(n,depth-1)]
            def transform(pt):
                x,y=pt
                return (x,y) if side==0 else (31-y,x) if side==1 else (31-x,31-y) if side==2 else (y,31-x)
            p.poly([transform(pt) for pt in pts],c[3],None)
            p.dot(*transform((n+1,1)),c[4])
    return im


def building(zone,b):
    """Preserve the exact doorway and footprint. Add role-specific construction."""
    im=old_building(zone,b); p=Pixel(im); w,h=im.size
    style=b.get('style','cottage'); name=b['name'].casefold()
    if style=='cottage':
        style='inn' if 'inn' in name else 'shop' if 'market' in name else 'workshop' if 'workshop' in name else 'cottage'
    eave=max(38,min(85,h//3)); bottom=h-5; door=w//2
    if style=='inn':
        # A dormer, carved canopy, and paired lanterns change the silhouette.
        p.poly([(w*.38,eave-19),(w*.38,29),(w*.5,16),(w*.62,29),(w*.62,eave-19)],'8c8067')
        p.poly([(w*.35,31),(w*.5,11),(w*.65,31),(w*.63,36),(w*.5,20),(w*.37,36)],'69695e')
        p.rect((door-10,31,door+10,51),'d6bf8e','493d30',2); p.line([(door,32),(door,50)],'6c5a41',2)
        p.poly([(door-28,bottom-52),(door+28,bottom-52),(door+35,bottom-44),(door-35,bottom-44)],'8b6a42')
        for x in (door-35,door+35):
            p.line([(x,bottom-42),(x,bottom-31)],'45433a',2)
            p.rect((x-4,bottom-32,x+4,bottom-19),'cda76a','4b493e',2); p.line([(x,bottom-29),(x,bottom-22)],'f0dba5')
        sx=w-38; p.line([(sx-14,eave+27),(sx+10,eave+27)],'4c4436',3)
        board(p,(sx-13,eave+32,sx+11,eave+52),'73583b'); mug(p,sx-3,eave+48)
    elif style in ('forge','blacksmith'):
        for y in range(15,eave-12,6): p.line([(w-28,y),(w-16,y)],'9c9280')
        p.poly([(12,bottom-35),(39,bottom-38),(46,bottom-33),(42,bottom-25),(33,bottom-24),(37,bottom-12),(17,bottom-12),(22,bottom-24),(9,bottom-29)],'79858b')
        p.line([(15,bottom-33),(37,bottom-35)],'c0c7bb',2)
        for x,y in [(w-48,bottom-12),(w-40,bottom-18),(w-31,bottom-13)]: p.poly([(x-7,y),(x-4,y-7),(x+3,y-8),(x+7,y),(x,y+3)],'474748')
        p.line([(door-18,bottom-48),(door+18,bottom-48)],'55584f',3)
    elif style=='shop':
        x0,x1=10,w//3+20; top=eave+9
        p.poly([(x0,top),(x1,top),(x1+7,top+23),(x0-5,top+23)],'667b72')
        for x in range(x0+3,x1-1,14):
            p.poly([(x,top+1),(x+6,top+1),(x+9,top+23),(x+2,top+23)],'c1b391',None)
        p.line([(x0-5,top+24),(x1+7,top+24)],'454538',2)
        board(p,(12,bottom-25,56,bottom-8),'927149')
        for x in (20,32,44): bottle(p,x,bottom-24,'809261')
        sack(p,w-28,bottom-8)
    elif style=='workshop':
        p.line([(w-36,eave+8),(w-36,eave+67)],'b9a170',2)
        p.poly([(w-34,eave+11),(w-13,eave+11),(w-13,eave+53),(w-23,eave+46),(w-34,eave+53)],'6b808a')
        p.line([(w-29,eave+20),(w-19,eave+38)],'c4cbbf',2); p.line([(w-19,eave+20),(w-29,eave+38)],'c4cbbf',2)
        p.ellipse((12,bottom-47,42,bottom-17),'b49b72','5e5745',2)
        p.ellipse((19,bottom-40,35,bottom-24),'886858','d0b995',2)
        p.dot(27,bottom-32,'d8c49c')
    return im
