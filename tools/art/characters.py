"""Wayfarer: original layered 64px character artwork.

This renderer samples no previous sprite, portrait or generated concept sheet.
Materials, contour clusters, hands and fittings are drawn around shared joints.
Every public frame function returns transparent RGBA with feet anchored at y=55.
"""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, rgba, palette, shade, seed, INK, METALS, WOODS, ELEMENT_COLORS
from .character_motion import rig

SKINS = ('edc8a5','d8aa80','bd8967','a67150','80533e','593b31')
HAIRS = ('342c35','624033','957043','d5b977','963f35','242935','c7c8cc','775879')
ROLE_COLORS = {
 'blacksmith':'6c7185','armorer':'55738a','weaponsmith':'825948','fletcher':'57704a',
 'provisioner':'9f784d','alchemist':'3f8c85','rune_merchant':'6b63a3','enchanter':'866396',
 'jeweler':'b78a43','banker':'415e8b','auctioneer':'904d51','innkeeper':'bf8150',
 'guild_registrar':'774c73','tailor':'ae657d','tanner':'976346','carpenter':'917343',
 'woodworker':'74754e','scribe':'4e8098','guard':'658399','scholar':'74658b',
 'ferryman':'447886','herbalist':'5e864e','miner':'8e7160','fisher':'537f83',
 'trainer':'9a5f4c','traveler':'7b7958'}

_ORDERS = (
 ('cloak','body','legs','boots','chest','belt','hair','helmet','necklace','charm','trinket','offhand','weapon','gloves','ring'),
 ('cloak','weapon','body','legs','boots','chest','belt','hair','helmet','necklace','charm','trinket','offhand','gloves','ring'),
 ('cloak','offhand','body','legs','boots','chest','belt','hair','helmet','necklace','charm','trinket','weapon','gloves','ring'),
 ('weapon','offhand','body','legs','boots','chest','belt','cloak','hair','helmet','necklace','charm','trinket','gloves','ring'))


def layer_order(direction):
    if direction not in range(4): raise ValueError('Invalid layer direction')
    return list(_ORDERS[direction])


def _segment(p, a, b, width, base, far=False):
    """Tapered anatomical section with one selective light-facing contour."""
    c=palette(shade(base,.79) if far else base)
    dx,dy=b[0]-a[0],b[1]-a[1]; length=max(1,math.hypot(dx,dy)); nx,ny=-dy/length,dx/length
    wa=width/2; wb=max(1,wa-.65)
    p.poly([(a[0]+nx*wa,a[1]+ny*wa),(b[0]+nx*wb,b[1]+ny*wb),
            (b[0]-nx*wb,b[1]-ny*wb),(a[0]-nx*wa,a[1]-ny*wa)],c[2])
    p.line([(a[0]-1,a[1]+1),(b[0]-1,b[1]-1)],c[3],max(1,round(width)-2))
    if width>=4: p.line([(a[0]-2,a[1]+1),(b[0]-1,b[1]-2)],c[4])


def _hand(p, at, skin, sign=1):
    x,y=at; c=palette(skin)
    p.poly([(x-2,y-2),(x+1,y-2),(x+2,y),(x+1,y+2),(x-1,y+2),(x-2,y)],c[2])
    p.line([(x-1,y-1),(x,y+1)],c[4],2)
    p.dot(x+sign*2,y,c[3])


def _boot(p, at, base, sign=1, side=False):
    x,y=at; c=palette(base)
    tip=x+sign*(4 if side else 2)
    p.poly([(x-2,y-5),(x+2,y-5),(x+2,y-2),(tip,y-1),(tip,y),(x-2,y)],c[2])
    p.line([(x-1,y-4),(x+1,y-4)],c[4])
    p.line([(min(x-2,tip),y),(max(x+2,tip),y)],c[0])
    p.dot(x,y-2,c[3])


def _torso(p,j,base,kind='tunic',trim='c6a46d'):
    c=palette(base); hx,hy=j['hip']; nx,ny=j['neck']; width=5 if j['side'] else 7
    if j['collapse']>.5:
        _segment(p,(nx,ny),(hx,hy),8,base)
        p.line([(nx,ny-2),(hx,hy-2)],c[4]); return
    left=j['shoulder_l']; right=j['shoulder_r']
    lo,hi=sorted((left[0],right[0])); lo-=1; hi+=1
    points=[(nx-2,ny-1),(nx+2,ny-1),(hi,ny+2),(hx+width-1,hy-3),(hx+width-2,hy+2),
            (hx-width+2,hy+2),(hx-width+1,hy-3),(lo,ny+2)]
    p.poly(points,c[1])
    p.poly([(nx-1,ny+1),(nx+2,ny+2),(hx+width-2,hy-4),(hx+1,hy),(hx-width+3,hy-1),(lo+2,ny+3)],c[3],None)
    p.line([(lo+2,ny+3),(hx-width+3,hy-3)],c[4])
    p.line([(hi-1,ny+4),(hx+width-2,hy-2)],c[0])
    if kind=='plate':
        p.line([(lo+2,ny+5),(nx,ny+6),(hi-2,ny+5)],c[5])
        p.line([(nx,ny+5),(hx,hy-4)],c[1])
        p.line([(hx-width+2,hy-4),(hx,hy-2),(hx+width-2,hy-4)],c[4])
        p.line([(hx-width+2,hy-2),(hx+width-2,hy-2)],c[1])
    elif kind=='leather':
        p.line([(lo+2,ny+3),(hx+3,hy-3)],'c5a077',2)
        p.line([(lo+3,ny+3),(hx+4,hy-3)],c[0])
        p.rect((hx+1,hy-6,hx+3,hy-4),trim,c[0])
    elif not j['back']:
        p.line([(nx-2,ny),(nx,ny+4),(nx+2,ny)],trim)
        p.line([(nx,ny+5),(hx,hy-2)],c[1])
        p.dot(nx,ny+6,trim)


def _head(p,j,skin):
    x,y=j['head']; c=palette(skin); s=j['sign']
    if j['collapse']>.65:
        p.poly([(x-6,y-3),(x-3,y-5),(x+3,y-4),(x+6,y-1),(x+5,y+3),(x-3,y+4),(x-6,y+1)],c[2])
        p.poly([(x-4,y-2),(x,y-3),(x+4,y),(x+2,y+2),(x-3,y+2)],c[3],None)
        if not j['back']: p.line([(x+1,y),(x+3,y)],c[0])
        return
    p.poly([(x-4,y-6),(x+2,y-7),(x+5,y-4),(x+5,y+3),(x+2,y+6),(x-2,y+6),(x-5,y+3),(x-5,y-3)],c[2])
    p.poly([(x-3,y-4),(x+1,y-5),(x+3,y-2),(x+2,y+3),(x-1,y+4),(x-4,y+1)],c[3],None)
    p.line([(x-3,y-3),(x-3,y)],c[4])
    if j['back']:
        p.dot(x-5,y+1,c[3]); p.dot(x+5,y+1,c[2]); return
    blink=j['state']=='idle' and j['frame']==7
    if j['side']:
        p.poly([(x+4*s,y-1),(x+7*s,y+1),(x+4*s,y+2)],c[3])
        p.line([(x+2*s,y-2),(x+4*s,y-2)],c[0])
        p.dot(x+3*s,y,INK)
        if not blink: p.dot(x+2*s,y-1,'e9e4d9')
        p.line([(x+s,y+4),(x+3*s,y+4)],c[1])
        p.line([(x-2*s,y),(x-2*s,y+2)],c[1])
    else:
        for dx in (-2,2):
            p.line([(x+dx-1,y-2),(x+dx,y-2)],c[0])
            p.dot(x+dx,y,INK)
            if not blink: p.dot(x+dx-1,y-1,'eee7d8')
        p.dot(x,y+1,c[4]); p.dot(x+1,y+2,c[1])
        p.line([(x-1,y+4),(x+1,y+4)],c[1])
        p.dot(x-5,y+1,c[3]); p.dot(x+5,y+1,c[2])


def body_frame(body,skin,state,frame,direction):
    if skin not in range(len(SKINS)): raise ValueError('Invalid skin')
    im=canvas(); p=Pixel(im); j=rig(state,frame,direction,body); skin=SKINS[skin]
    order=('l','r') if direction!=1 else ('r','l')
    for index,side in enumerate(order):
        hip=(j['hip'][0]+(-2 if side=='l' else 2),j['hip'][1])
        _segment(p,hip,j['knee_'+side],5,'515567',index==0 and j['side'])
        _segment(p,j['knee_'+side],j['foot_'+side],4,'545768',index==0 and j['side'])
        _boot(p,j['foot_'+side],'554235',j['sign'],j['side'])
    for index,side in enumerate(order):
        _segment(p,j['shoulder_'+side],j['elbow_'+side],5,'d7c3a0',index==0 and j['side'])
        _segment(p,j['elbow_'+side],j['hand_'+side],3,skin,index==0 and j['side'])
    _torso(p,j,'c9b595')
    hx,hy=j['hip']; p.line([(hx-4,hy),(hx+4,hy)],'644831',2); p.dot(hx,hy,'d4aa66')
    _segment(p,j['neck'],(j['head'][0],j['head'][1]+5),3,skin)
    _head(p,j,skin)
    for side in order: _hand(p,j['hand_'+side],skin,j['sign'])
    return im


def hair_frame(style,color,state,frame,direction):
    if style not in range(6) or color not in range(8): raise ValueError('Invalid hair')
    im=canvas(); p=Pixel(im); j=rig(state,frame,direction); x,y=j['head']; c=palette(HAIRS[color]); s=j['sign']
    if j['collapse']>.65:
        p.poly([(x-6,y-3),(x-3,y-6),(x+2,y-5),(x+4,y-3),(x,y-2),(x-3,y),(x-6,y)],c[2])
        p.line([(x-4,y-3),(x-1,y-4),(x+2,y-3)],c[4])
        if style in (1,2,4):
            p.poly([(x-4,y),(x-7,y+2),(x-12,y+3),(x-9,y+5),(x-3,y+3)],c[2])
            p.line([(x-6,y+2),(x-10,y+3)],c[3])
        if style==5: p.ellipse((x-8,y-4,x-3,y+1),c[2],INK)
        return im
    sway=j['cloth']
    if style in (1,2,4):
        if j['back']:
            p.poly([(x-5,y-1),(x+5,y-1),(x+5+sway,y+9),(x+2+sway,y+13),(x-3+sway,y+12),(x-5,y+6)],c[1])
            for dx in (-2,1): p.line([(x+dx,y+1),(x+dx+sway,y+10)],c[3])
        else:
            for dx in (-5,5):
                if j['side'] and dx*s>0: continue
                p.poly([(x+dx,y-2),(x+dx+2,y+1),(x+dx+2+sway,y+10),(x+dx-1+sway,y+9),(x+dx-2,y+3)],c[2])
                p.line([(x+dx,y),(x+dx+sway,y+7)],c[4])
        if style==2:
            bx=x-4*s+sway
            for k in range(4): p.poly([(bx,y+3+k*2),(bx+2,y+4+k*2),(bx,y+6+k*2),(bx-2,y+4+k*2)],c[2 if k%2 else 3])
            p.line([(bx-1,y+11),(bx+1,y+11)],'c6a16b')
        if style==4:
            bx=x-5*s
            p.poly([(bx,y-2),(bx-3*s,y),(bx-4*s+sway,y+8),(bx-2*s+sway,y+11),(bx+sway,y+5)],c[2])
            p.line([(bx-2*s,y+1),(bx-2*s+sway,y+7)],c[4]); p.dot(bx,y,'d5aa67')
    if style==0:
        contour=[(-6,-2),(-5,-6),(-3,-7),(-3,-9),(0,-8),(2,-10),(4,-7),(6,-6),(5,-2),(2,-3),(0,-1),(-2,-3),(-4,-1)]
    elif style==3:
        contour=[(-6,-3),(-4,-7),(0,-9),(4,-8),(6,-5),(4,-2),(1,-4),(-2,-1),(-5,1)]
    else:
        contour=[(-6,-2),(-5,-6),(-2,-8),(2,-8),(5,-6),(6,-2),(4,1),(3,-3),(0,-2),(-3,-4),(-5,2)]
    p.poly([(x+dx,y+dy) for dx,dy in contour],c[2])
    p.poly([(x-4,y-5),(x-1,y-7),(x+2,y-6),(x,y-4),(x-3,y-3)],c[3],None)
    p.line([(x-3,y-5),(x,y-6),(x+2,y-5)],c[4])
    p.line([(x+3,y-5),(x+4,y-3)],c[1])
    if style==5:
        p.ellipse((x-4,y-12,x+3,y-6),c[2],INK)
        p.line([(x-2,y-10),(x+1,y-9)],c[4]); p.line([(x-2,y-7),(x+2,y-7)],'b99861')
    if j['back']:
        p.poly([(x-5,y-3),(x+5,y-3),(x+4,y+4),(x+1,y+6),(x-3,y+4)],c[2])
        p.line([(x-3,y-2),(x-3,y+2),(x-1,y+4)],c[3])
        p.line([(x+1,y-3),(x+2,y+2)],c[4])
    elif j['side']: p.line([(x-4*s,y-2),(x-4*s,y+3)],c[2],2)
    return im


def clothing_base(item):
    if item.get('_color'): return item['_color']
    tags=item.get('tags',[]); material=item.get('material',''); tier=item.get('tier',1)
    if 'heavy' in tags or material in METALS:
        return METALS.get(material,('8a9baa','7796ab','9eadc0','8babc4','a4bfd0','a0a3c3','bdd0dc')[min(6,max(0,int(tier)-1))])
    if 'light' in tags:
        return ('576a89','715b83','a65a74','5c86a7','59a2a9','795995','a182bd')[min(6,max(0,int(tier)-1))]
    return ('96714c','865a42','946b54','597561','688b9b','666078','a391a2')[min(6,max(0,int(tier)-1))]


def _weapon_kind(item):
    tags=set(item.get('tags',[])); ident=item.get('id','')
    for kind in ('crossbow','bow','spear','staff','wand','dagger','axe','mace','sword'):
        if kind in tags or kind in ident: return kind
    return 'sword'


def _weapon(p,j,item):
    j=dict(j)
    if j['state'] in ('interact','craft'):
        j['hand_r']=(j['hip'][0]-7*j['sign'],j['hip'][1]-5)
        j['angle']=155*j['sign'] if _weapon_kind(item) not in ('staff','spear','bow','crossbow') else -15*j['sign']
    kind=_weapon_kind(item); material=item.get('material','iron'); c=palette(METALS.get(material,'a5b9c7'))
    wood=WOODS.get(material,'896040'); gold=palette('c7a461'); hand=j['hand_r']; x,y=hand
    angle=j['angle']; angle=math.radians(angle)
    ux,uy=math.sin(angle),-math.cos(angle); nx,ny=-uy,ux
    def at(along,across=0): return (x+ux*along+nx*across,y+uy*along+ny*across)
    if kind in ('bow','crossbow'):
        # Both string and riser are attached to the shared hands, never an icon pivot.
        s=j['sign']; draw=(0,1,3,5,1,0,0,0)[j['frame']] if j['state'] in ('attack','bow_attack','crossbow_attack') else 0
        if j['collapse']>.6:
            p.line([(x-12*s,y-2),(x-7*s,y-5),(x-1*s,y-4),(x+2*s,y-1)],wood,3)
            p.line([(x-12*s,y-2),(x+2*s,y-1)],'cabc95'); return
        if kind=='crossbow':
            p.line([(x-9*s,y+2),(x+8*s,y-2)],wood,3)
            p.line([(x+4*s,y-9),(x+8*s,y-2),(x+6*s,y+7)],c[3],3)
            p.line([(x+4*s,y-9),(x+2*s,y-1),(x+6*s,y+7)],'d7caa3')
        else:
            tips=[(x-4*s,y-14),(x+2*s,y-9),(x+3*s,y-3),(x,y),(x+3*s,y+4),(x+s,y+9),(x-4*s,y+12)]
            p.line(tips,INK,4); p.line(tips,wood,2)
            p.line([(a-s,b) for a,b in tips[1:4]],shade(wood,1.3))
            pull=j['hand_l'] if j['state']=='bow_attack' else (x-(3+draw)*s,y-1)
            p.line([tips[0],pull,tips[-1]],'d6caa4')
            if j['state'] in ('attack','bow_attack') and j['frame'] in (1,2,3):
                p.line([(pull[0]-3*s,pull[1]),(x+10*s,y-1)],'e6dcc0')
                p.poly([(x+12*s,y-1),(x+8*s,y-3),(x+8*s,y+1)],c[4])
            p.line([(x,y-2),(x,y+2)],'6d4632',3)
        return
    # Foreshortening keeps a complete point and fittings inside the cell at contact.
    length={'sword':21,'dagger':12,'axe':20,'mace':19,'spear':26,'staff':25,'wand':15}[kind]
    margin=5 if kind in ('axe','mace','staff') else 2
    for component,origin in ((ux,x),(uy,y)):
        if component>0: length=min(length,(61-margin-origin)/component)
        elif component<0: length=min(length,(origin-2-margin)/-component)
    length=max(7,length)
    handle=6 if kind in ('spear','staff') else 4
    p.line([at(-handle),at(3)],INK,4); p.line([at(-handle+1),at(3)],wood,2)
    p.line([at(-handle+1,-1),at(1,-1)],shade(wood,1.25))
    p.line([at(-handle),at(-handle+1)],c[3],3)
    if kind in ('sword','dagger'):
        p.poly([at(3,-2),at(length-4,-2),at(length,0),at(length-4,2),at(3,2)],c[2])
        p.poly([at(4,-1),at(length,0),at(4,0)],c[5],None)
        p.line([at(4,1),at(length-4,1)],c[1])
        p.line([at(2,-4),at(2,4)],gold[1],3); p.line([at(2,-3),at(2,3)],gold[4])
        p.dot(*at(1),gold[5])
    elif kind=='axe':
        p.line([at(0),at(length)],wood,3); p.line([at(2,-1),at(length,-1)],shade(wood,1.3))
        p.poly([at(length-8,-2),at(length-9,-7),at(length-4,-8),at(length+1,-5),at(length-1,-2)],c[2])
        p.line([at(length-9,-7),at(length-4,-8),at(length+1,-5)],c[5])
        p.poly([at(length-5,1),at(length-2,4),at(length,2)],c[3])
        p.line([at(length-6,-1),at(length-3,1)],gold[3],2)
    elif kind=='mace':
        p.line([at(0),at(length-6)],wood,3)
        p.poly([at(length-8,-3),at(length-4,-5),at(length,-3),at(length,3),at(length-4,5),at(length-8,3)],c[2])
        p.line([at(length-7,-2),at(length-2,-3),at(length-1,-1)],c[5],2)
        p.line([at(length-7,1),at(length-2,2)],c[1])
        p.line([at(length-9,-2),at(length-9,2)],gold[3],2)
    elif kind=='spear':
        p.line([at(-7),at(length-7)],wood,3); p.line([at(-6,-1),at(length-7,-1)],shade(wood,1.3))
        p.poly([at(length-8,-3),at(length,0),at(length-8,3),at(length-6,0)],c[3])
        p.line([at(length-7,-2),at(length,0)],c[5])
        p.line([at(length-9,-2),at(length-9,2)],gold[3],2)
    else:
        p.line([at(-5),at(length-4)],wood,3); p.line([at(-4,-1),at(length-4,-1)],shade(wood,1.3))
        tone=ELEMENT_COLORS.get(item.get('element','Arcane'),'a493cf'); t=palette(tone)
        p.poly([at(length-8,-4),at(length-3,-5),at(length,0),at(length-3,5),at(length-8,4),at(length-5,0)],gold[2])
        p.poly([at(length-7,0),at(length-3,-3),at(length+1,0),at(length-3,3)],t[3])
        p.line([at(length-5,-1),at(length-2,-1)],t[5])
        p.line([at(length-9,-2),at(length-9,2)],gold[4],2)


def _shield(p,j,item):
    j=dict(j)
    if j['state'] in ('interact','craft'): j['hand_l']=(j['hip'][0]+3*j['sign'],j['hip'][1]-4)
    x,y=j['hand_l']; base=clothing_base(item); c=palette(base); s=j['sign']
    if j['collapse']>.6:
        p.poly([(x-7,y-4),(x+4,y-5),(x+8,y-1),(x+2,y+1),(x-6,y)],c[2]); p.line([(x-5,y-3),(x+3,y-4)],c[4]); return
    if j['side']:
        p.poly([(x-3,y-9),(x+3,y-8),(x+4,y+2),(x,y+7),(x-3,y+3)],c[2])
        p.line([(x-2,y-7),(x-1,y+3)],c[5]); return
    p.poly([(x-8,y-9),(x,y-12),(x+8,y-9),(x+7,y+1),(x+3,y+6),(x,y+8),(x-5,y+4),(x-8,y)],c[1])
    p.poly([(x-6,y-7),(x,y-9),(x+6,y-7),(x+5,y),(x,y+5),(x-5,y)],c[3])
    p.line([(x-6,y-7),(x,y-9),(x+6,y-7)],c[5])
    p.line([(x,y-7),(x,y+3)],'d6b77a',2); p.line([(x-4,y-3),(x+4,y-3)],'d6b77a')
    for dx,dy in ((-6,-6),(6,-6),(-4,1),(4,1)): p.dot(x+dx,y+dy,c[5])


def armour_frame(item,state,frame,direction):
    im=canvas(); p=Pixel(im); j=rig(state,frame,direction); slot=item.get('slot',''); base=clothing_base(item); c=palette(base)
    tags=set(item.get('tags',[])); metal='heavy' in tags or item.get('material','') in METALS
    cloth='light' in tags; trim='d0ad69' if metal else 'c9ad7e'; hx,hy=j['hip']; nx,ny=j['neck']
    if slot=='weapon': _weapon(p,j,item)
    elif slot=='offhand':
        if 'shield' in tags or 'shield' in item.get('id',''): _shield(p,j,item)
        else:
            x,y=j['hand_l']; t=palette(ELEMENT_COLORS.get(item.get('element','Arcane'),'ab98ce'))
            if any(k in item.get('id','') for k in ('book','tome','codex')):
                p.poly([(x-5,y-5),(x+2,y-6),(x+5,y-2),(x+4,y+5),(x-4,y+4)],c[2]); p.line([(x-2,y-4),(x-2,y+3)],trim,2)
                p.line([(x+1,y-4),(x+3,y-2),(x+3,y+3)],'ece0b9')
            else:
                p.poly([(x,y-9),(x+5,y-4),(x+3,y+2),(x-3,y+2),(x-5,y-4)],t[2]); p.line([(x,y-7),(x-2,y-3)],t[5],2)
                p.line([(x-4,y+1),(x+4,y+1)],trim,2)
    elif slot=='chest':
        for index,side in enumerate(('l','r')):
            _segment(p,j['shoulder_'+side],j['elbow_'+side],6,base,index==0 and j['side'])
        _torso(p,j,base,'plate' if metal else 'tunic' if cloth else 'leather',trim)
        if j['collapse']<.5:
            for side in ('l','r'):
                x,y=j['shoulder_'+side]
                if metal:
                    p.poly([(x-4,y),(x-2,y-3),(x+2,y-3),(x+4,y),(x+3,y+4),(x-2,y+3)],c[2])
                    p.line([(x-2,y-2),(x+1,y-2),(x+3,y)],c[5]); p.line([(x-2,y+3),(x+2,y+3)],c[0])
                else: p.line([(x-2,y+1),(x+1,y+2)],c[4])
            if cloth:
                sway=j['cloth']
                p.poly([(hx-5,hy-2),(hx+5,hy-2),(hx+8+sway,hy+11),(hx+3,hy+12),(hx,hy+8),(hx-2,hy+12),(hx-7+sway,hy+10)],c[2])
                p.line([(hx-3,hy),(hx-3+sway,hy+9)],c[4]); p.line([(hx+3,hy),(hx+4+sway,hy+9)],c[0])
                p.line([(hx-6+sway,hy+10),(hx-2,hy+11)],trim)
            if metal and int(item.get('tier',1))>=3:
                p.poly([(nx,ny+7),(nx+2,ny+9),(nx,ny+11),(nx-2,ny+9)],trim)
    elif slot=='legs':
        for index,side in enumerate(('l','r')):
            hip=(hx+(-2 if side=='l' else 2),hy)
            _segment(p,hip,j['knee_'+side],6,base,index==0 and j['side'])
            _segment(p,j['knee_'+side],j['foot_'+side],4,base,index==0 and j['side'])
            x,y=j['knee_'+side]
            p.poly([(x-2,y-2),(x+2,y-2),(x+3,y),(x,y+2),(x-2,y+1)],c[3]); p.dot(x-1,y-1,c[5] if metal else c[4])
    elif slot=='boots':
        for side in ('l','r'):
            _segment(p,j['knee_'+side],j['foot_'+side],5,base)
            _boot(p,j['foot_'+side],base,j['sign'],j['side'])
            x,y=j['foot_'+side]; p.line([(x-2,y-4),(x+1,y-4)],trim)
    elif slot=='gloves':
        for side in ('l','r'):
            ex,ey=j['elbow_'+side]; x,y=j['hand_'+side]
            cuff=((ex+x)/2,(ey+y)/2)
            _segment(p,cuff,(x,y),4,base); _hand(p,(x,y),base,j['sign'])
            p.line([(cuff[0]-1,cuff[1]),(cuff[0]+1,cuff[1])],trim)
    elif slot=='helmet':
        x,y=j['head']
        if j['collapse']>.65:
            p.poly([(x-6,y-3),(x-2,y-6),(x+3,y-4),(x+4,y-2),(x-1,y-1),(x-5,y+1)],c[2]); p.line([(x-3,y-4),(x+1,y-4)],c[5]); return im
        if cloth:
            p.poly([(x-7,y+3),(x-7,y-5),(x-3,y-9),(x+2,y-10),(x+6,y-6),(x+7,y+3),(x+4,y+5),(x+4,y-3),(x,y-5),(x-4,y-3),(x-4,y+5)],c[2])
            p.line([(x-5,y-5),(x-1,y-8),(x+3,y-7)],c[4])
            p.line([(x-4,y-3),(x,y-5),(x+4,y-3)],trim)
        else:
            p.poly([(x-6,y-2),(x-6,y-5),(x-3,y-8),(x+2,y-9),(x+6,y-5),(x+6,y-1),(x+3,y-3),(x-3,y-3)],c[2])
            p.line([(x-4,y-5),(x-1,y-7),(x+3,y-6)],c[5]); p.line([(x-5,y-2),(x+5,y-2)],trim)
            if metal:
                p.line([(x-5,y-1),(x-5,y+4)],c[3],2); p.line([(x+5,y-1),(x+5,y+4)],c[2],2)
                p.line([(x,y-7),(x,y-3)],c[4])
        if j['back']:
            p.poly([(x-5,y-2),(x+5,y-2),(x+4,y+3),(x,y+5),(x-4,y+3)],c[2]); p.line([(x-3,y),(x+2,y+1)],c[4])
    elif slot=='cloak':
        if j['collapse']>.5:
            p.poly([(nx-3,ny-3),(nx+3,ny-2),(hx-8,hy+3),(hx-12,hy+2),(hx-5,hy-3)],c[2]); p.line([(nx-2,ny-2),(hx-8,hy+1)],c[4])
        else:
            sway=j['cloth']; width=5 if j['side'] else 8
            p.poly([(nx-width,ny+1),(nx+width,ny+1),(hx+width+3+sway,52),(hx+3+sway,54),(hx+sway,51),(hx-5+sway,54),(hx-width-2+sway,51)],c[1])
            p.poly([(nx-width+2,ny+3),(nx+1,ny+4),(hx+2+sway,51),(hx-4+sway,52),(hx-width+sway,49)],c[3],None)
            p.line([(nx-width+2,ny+3),(hx-width+sway,49)],c[4]); p.line([(nx+3,ny+5),(hx+5+sway,49)],c[0])
            p.line([(hx-width-1+sway,51),(hx-5+sway,53)],trim)
    elif slot=='belt':
        p.line([(hx-5,hy),(hx+5,hy)],'493a33',4); p.line([(hx-4,hy-1),(hx+4,hy-1)],base,2)
        p.rect((hx-1,hy-2,hx+2,hy+1),trim,INK); p.dot(hx,hy-1,'725536')
        p.poly([(hx+4,hy),(hx+7,hy+1),(hx+7,min(55,hy+5)),(hx+3,min(55,hy+5))],c[2])
    elif slot in ('necklace','charm','trinket'):
        x,y=(nx,ny+5) if slot=='necklace' else (hx+4,hy-1) if slot=='charm' else (hx-4,hy)
        p.line([(x-2,y-2),(x,y+1),(x+2,y-2)],trim)
        p.poly([(x,y),(x+2,y+2),(x,y+4),(x-2,y+2)],c[3]); p.dot(x,y+1,c[5])
    elif slot=='ring':
        x,y=j['hand_r']; p.line([(x-1,y),(x+1,y)],trim,2); p.dot(x,y-1,c[5])
    else:
        raise ValueError('Unsupported visible equipment slot: '+str(slot))
    return im


def equipment_frame(item,state,frame,direction,*unused):
    return armour_frame(item,state,frame,direction)


def npc_frame(role,state,frame,direction):
    if role=='fletcher' and state=='attack': state='bow_attack'
    identity=seed('wayfarer:'+role); body=identity%2; skin=(identity//3)%6
    im=body_frame(body,skin,state,frame,direction)
    color=ROLE_COLORS.get(role,'7e7769')
    heavy=role in ('guard','armorer','trainer')
    robe=role in ('alchemist','rune_merchant','enchanter','scholar','scribe','guild_registrar')
    tags=['heavy'] if heavy else ['light'] if robe else ['medium']
    items={
        'legs': {'id':'role_legs','slot':'legs','_color':'4d4b59','tags':['medium']},
        'boots': {'id':'role_boots','slot':'boots','_color':'594332','tags':['medium']},
        'chest': {'id':'role_coat','slot':'chest','_color':color,'tags':tags},
        'belt': {'id':'role_belt','slot':'belt','_color':'8d6741','tags':['medium']},
    }
    if role in ('guard','ferryman','traveler','herbalist'): items['cloak']={'id':'role_cloak','slot':'cloak','_color':color,'tags':['light']}
    if heavy: items['helmet']={'id':'role_helm','slot':'helmet','_color':color,'tags':['heavy']}
    weapon={'blacksmith':'mace','weaponsmith':'sword','fletcher':'bow','guard':'spear','miner':'axe','trainer':'sword','scholar':'staff','rune_merchant':'staff'}.get(role)
    if weapon: items['weapon']={'id':'role_'+weapon,'slot':'weapon','tags':[weapon],'material':'iron','element':'Arcane'}
    if role in ('scribe','alchemist','enchanter','banker'): items['offhand']={'id':'role_book','slot':'offhand','tags':['focus'],'_color':color}
    hair_style=(identity//7)%6; hair_color=6 if role in ('scholar','scribe') else (identity//11)%8
    layers={'body':im,'hair':hair_frame(hair_style,hair_color,state,frame,direction)}
    layers.update({slot:armour_frame(item,state,frame,direction) for slot,item in items.items()})
    result=canvas()
    order=layer_order(direction)
    if state in ('interact','craft'): order=['weapon','offhand']+[k for k in order if k not in ('weapon','offhand')]
    for layer in order:
        if layer in layers: result.alpha_composite(layers[layer])
    p=Pixel(result); j=rig(state,frame,direction,body); nx,ny=j['neck']; hx,hy=j['hip']
    if role in ('blacksmith','weaponsmith','innkeeper','tanner','carpenter','woodworker') and j['collapse']<.5:
        apron='684737' if role!='innkeeper' else 'd1bea0'; a=palette(apron)
        p.poly([(nx-3,ny+5),(nx+3,ny+5),(hx+5,hy+9),(hx-5,hy+9)],a[2])
        p.line([(nx-2,ny+6),(hx-3,hy+7)],a[4]); p.line([(hx-2,hy+2),(hx+2,hy+2)],a[0])
    if role in ('blacksmith','miner','carpenter') and not j['back'] and j['collapse']<.5:
        x,y=j['head']; h=palette(HAIRS[hair_color]); p.poly([(x-3,y+3),(x,y+4),(x+3,y+3),(x+2,y+7),(x,y+8),(x-2,y+6)],h[2]); p.dot(x-1,y+5,h[4])
    return result
