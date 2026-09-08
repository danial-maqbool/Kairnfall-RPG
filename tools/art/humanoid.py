"""Original 64px articulated people and equipment. No raster rotation or random detail.

All layers share one integer rig, including both body silhouettes. The artist-facing
anchor is (32,55). Death bends the joints; it never rotates a standing bitmap.
"""
from __future__ import annotations
import math
from .common import Pixel, canvas, palette, rgba, shade, seed, INK, ELEMENT_COLORS
from .items import metal_for

SKINS=('edcba6','d7b28c','bd936f','a57a59','825b45','604435')
HAIRS=('463b36','72543d','9d7749','c9ad70','8d4f3f','3a353e','b4bab4','765d77')
ROLE_COLORS={'blacksmith':'827369','armorer':'778b96','weaponsmith':'8b7467','fletcher':'6f8665','provisioner':'b09872','alchemist':'6d8b82','rune_merchant':'7c78a1','enchanter':'8e7199','jeweler':'ad9971','banker':'707f99','auctioneer':'956c65','innkeeper':'a28568','guild_registrar':'8a6679','tailor':'a08199','tanner':'947153','carpenter':'967e61','woodworker':'8d8468','scribe':'71899a','guard':'80949e','scholar':'91839e','ferryman':'6b8b9b','herbalist':'7f9975','miner':'877b6f','fisher':'809993','trainer':'987a6c','traveler':'8b876f'}


def rig(state, frame, direction, body=0):
    if state not in ('idle','walk','attack','cast','hit','death') or not 0 <= frame < 8 or not 0 <= direction < 4:
        raise ValueError('Invalid humanoid animation address')
    side=direction in (1,2); sign=-1 if direction==1 else 1
    stride=math.sin(frame*math.tau/8) if state=='walk' else 0
    # Head and pelvis do not jump at the idle/walk boundary. Lift only the moving foot.
    j={'head':(32+(1 if side else 0),18),'neck':(32,26),'hip':(32,42),
       'shoulder_l':(28 if not side else 31,28),'shoulder_r':(36 if not side else 34,28),
       'elbow_l':(25 if not side else 29,34),'elbow_r':(39 if not side else 37,34),
       'hand_l':(24 if not side else 28,39+round(stride*2)),
       'hand_r':(40 if not side else 38,39-round(stride*2)),
       'knee_l':(29,48),'knee_r':(35,48),
       'foot_l':(28+round(stride*3),55-max(0,round(stride*3))),
       'foot_r':(36-round(stride*3),55-max(0,round(-stride*3))),
       'angle':-12,'side':side,'back':direction==3,'sign':sign,'stride':stride,'collapse':0.0}
    if side:
        j['foot_l']=(32+round(stride*5),55-max(0,round(stride*3)))
        j['foot_r']=(34-round(stride*5),55-max(0,round(-stride*3)))
        j['knee_l']=(31+round(stride*2),48); j['knee_r']=(34-round(stride*2),48)
        if sign<0:
            for name in tuple(j):
                if isinstance(j[name],tuple): j[name]=(64-j[name][0],j[name][1])
    if state=='idle' and frame in (3,4):
        for name in ('shoulder_l','shoulder_r','elbow_l','elbow_r','hand_l','hand_r'):
            x,y=j[name]; j[name]=(x,y-1)
    if state=='attack':
        swing=(-2,-4,-5,1,5,4,1,0)[frame]
        hx,hy=j['hand_r']; j['hand_r']=(hx+sign*round(swing*.4),hy-abs(swing))
        ex,ey=j['elbow_r']; j['elbow_r']=(ex+sign*round(swing*.4),ey-abs(swing)//2)
        j['angle']=(-20,-38,-48,18,45,35,8,-12)[frame]*sign
    elif state=='cast':
        lift=(0,3,6,8,8,6,3,0)[frame]
        for hand in ('hand_l','hand_r'):
            hx,hy=j[hand]; j[hand]=(hx,hy-lift)
        j['angle']=-25*sign
    elif state=='hit':
        shift=(0,1,1,0,0,0,0,0)[frame]
        j['head']=(j['head'][0]-sign*shift,18)
    elif state=='death':
        t=(0,.12,.28,.48,.7,.9,1,1)[frame]; j['collapse']=t
        end={'head':(38,44),'neck':(33,45),'hip':(28,49),
             'shoulder_l':(30,45),'shoulder_r':(37,46),
             'elbow_l':(23,48),'elbow_r':(43,48),'hand_l':(20,52),'hand_r':(47,52),
             'knee_l':(26,52),'knee_r':(34,52),'foot_l':(24,55),'foot_r':(38,55)}
        for name,target in end.items():
            if direction==1: target=(64-target[0],target[1])
            origin=j[name]; j[name]=tuple(round(a+(b-a)*t) for a,b in zip(origin,target))
        j['angle']=(-12+(-90+12)*t)*sign
    return j


def finish(image,state,frame):
    if state=='hit' and frame==1:
        from PIL import Image
        flash=Image.new('RGBA',image.size,(240,220,188,0))
        flash.putalpha(image.getchannel('A').point(lambda a:round(a*.22)))
        return Image.alpha_composite(image,flash)
    return image


def limb(p,a,b,width,base):
    """Tapered contour with one lit edge, not nested cylindrical outlines."""
    dx,dy=b[0]-a[0],b[1]-a[1]; length=max(1,math.hypot(dx,dy)); nx,ny=-dy/length,dx/length
    w=width/2; end=max(1,w-.65); c=palette(base)
    pts=[(a[0]+nx*w,a[1]+ny*w),(b[0]+nx*end,b[1]+ny*end),
         (b[0]-nx*end,b[1]-ny*end),(a[0]-nx*w,a[1]-ny*w)]
    p.poly(pts,c[2]); p.line([(a[0]-1,a[1]),(b[0]-1,b[1])],c[3],max(1,width-2))
    if width>=4: p.line([(a[0]-2,a[1]+1),(b[0]-1,b[1]-1)],c[4])


def torso(p,j,base,width=6,coat=False):
    c=palette(base); nx,ny=j['neck']; hx,hy=j['hip']; narrow=2 if j['side'] else 0
    w=width-narrow
    p.poly([(nx-w,ny+1),(nx-2,ny),(nx+2,ny),(nx+w,ny+1),
            (hx+w-1,hy-4),(hx+w-2,hy+1),(hx-w+2,hy+1),(hx-w+1,hy-4)],c[2])
    p.poly([(nx-w+2,ny+2),(nx,ny+3),(hx+1,hy-3),(hx-w+3,hy-1)],c[3],None)
    p.line([(nx-w+2,ny+3),(hx-w+3,hy-5)],c[4])
    p.line([(nx+w-1,ny+4),(hx+w-2,hy-2)],c[1])
    if not j['back']: p.line([(nx-2,ny+1),(nx,ny+4),(nx+2,ny+1)],c[0])
    if coat:
        p.poly([(hx-w+1,hy-2),(hx+w-1,hy-2),(hx+w+2,hy+8),(hx+1,hy+9),(hx,hy+6),(hx-3,hy+9),(hx-w-2,hy+7)],c[2])
        p.line([(hx-2,hy),(hx-3,hy+6)],c[4]); p.line([(hx+2,hy),(hx+3,hy+7)],c[1])


def face(p,j,skin):
    hx,hy=j['head']; c=palette(skin)
    outline=[(hx-3,hy-6),(hx+3,hy-6),(hx+5,hy-3),(hx+5,hy+3),(hx+2,hy+6),(hx-2,hy+6),(hx-5,hy+3),(hx-5,hy-3)]
    p.poly(outline,c[2]); p.poly([(hx-3,hy-4),(hx+1,hy-5),(hx+3,hy-2),(hx+2,hy+3),(hx-2,hy+4),(hx-4,hy+1)],c[3],None)
    p.line([(hx-3,hy-3),(hx-3,hy+1)],c[4])
    if j['back']: return
    if j['side']:
        s=j['sign']; p.poly([(hx+4*s,hy-1),(hx+7*s,hy+1),(hx+4*s,hy+2)],c[3])
        p.dot(hx+3*s,hy-1,INK); p.dot(hx+2*s,hy-2,c[4]); p.line([(hx+2*s,hy+4),(hx+4*s,hy+4)],c[1])
        p.line([(hx-2*s,hy),(hx-2*s,hy+2)],c[1])
    else:
        for dx in (-2,2): p.dot(hx+dx,hy,INK); p.dot(hx+dx-1,hy-1,c[4])
        p.line([(hx,hy+1),(hx+1,hy+2)],c[1]); p.line([(hx-1,hy+4),(hx+1,hy+4)],c[1])
        p.dot(hx-5,hy+1,c[3]); p.dot(hx+5,hy+1,c[2])


def body_frame(body,skin,state,frame,direction):
    image=canvas(); p=Pixel(image); j=rig(state,frame,direction,body); base=SKINS[skin]; c=palette(base)
    for side in ('l','r'):
        hip=(j['hip'][0]+(-2 if side=='l' else 2),j['hip'][1])
        limb(p,hip,j['knee_'+side],4,'686365'); limb(p,j['knee_'+side],j['foot_'+side],3,base)
        x,y=j['foot_'+side]; p.poly([(x-2,y-2),(x+1,y-2),(x+3,y),(x+2,y+1),(x-2,y+1)],c[2]); p.line([(x-1,y-1),(x+1,y-1)],c[4])
    for side in ('l','r'):
        limb(p,j['shoulder_'+side],j['elbow_'+side],4,base)
        limb(p,j['elbow_'+side],j['hand_'+side],3,base)
    torso(p,j,'aca28e',5 if body else 6)
    x,y=j['hip']; p.line([(x-4,y),(x+4,y)],'544b43',2)
    limb(p,j['neck'],(j['head'][0],j['head'][1]+5),3,base)
    face(p,j,base)
    for side in ('l','r'):
        x,y=j['hand_'+side]; p.poly([(x-1,y-2),(x+1,y-2),(x+2,y),(x+1,y+2),(x-1,y+1)],c[3]); p.dot(x-1,y-1,c[4])
    return finish(image,state,frame)


def hair_frame(style,color,state,frame,direction):
    image=canvas(); p=Pixel(image); j=rig(state,frame,direction); x,y=j['head']; c=palette(HAIRS[color])
    if style in (1,2,4):
        offset=2 if style==4 else -2
        p.poly([(x-4,y-2),(x+4,y-2),(x+5+offset,y+8),(x+2+offset,y+15),(x-3+offset,y+14),(x-4,y+5)],c[1])
        p.line([(x+offset,y+5),(x+offset+1,y+12)],c[3])
        if style==2:
            for dy in (6,9,12): p.line([(x-1,y+dy),(x+2,y+dy+1)],c[4])
        if style==4: p.line([(x+1,y+6),(x+5,y+6)],'bfa36f',2)
    p.poly([(x-5,y-3),(x-4,y-6),(x-1,y-8),(x+3,y-7),(x+5,y-4),(x+5,y-1),(x+2,y-3),(x,y-2),(x-3,y-4),(x-5,y+1)],c[2])
    p.poly([(x-3,y-5),(x,y-7),(x+3,y-5),(x,y-4)],c[3],None)
    p.line([(x-3,y-5),(x,y-6),(x+2,y-5)],c[4])
    if style==3: p.poly([(x-1,y-7),(x-1,y-10),(x+2,y-11),(x+3,y-6)],c[3])
    if style==5: p.ellipse((x-3,y-11,x+3,y-6),c[2],INK); p.line([(x-1,y-10),(x+1,y-9)],c[4])
    if j['back']:
        p.poly([(x-5,y-3),(x+5,y-3),(x+4,y+4),(x+1,y+6),(x-3,y+4)],c[2])
        for dx in (-3,0,2): p.line([(x+dx,y-2),(x+dx,y+3)],c[3])
    elif j['side']:
        s=j['sign']; p.line([(x-4*s,y-2),(x-4*s,y+3)],c[2],2)
    return finish(image,state,frame)


def clothing_base(item):
    if item.get('_color'): return item['_color']
    weight=next((tag for tag in item.get('tags',[]) if tag in ('light','medium','heavy')),'medium')
    tier=item['id'].split('_')[0]
    if weight=='heavy': return {'linen':'8e999e','wool':'8496a0','silk':'a4b7c0','moonweave':'9eb7c3','frostweave':'83a7b6','duskweave':'8996a4','aetherweave':'b0b9ce'}.get(tier,metal_for(item))
    if weight=='light': return {'linen':'788b78','wool':'7c7088','silk':'965c75','moonweave':'829bb6','frostweave':'83aeb2','duskweave':'785f89','aetherweave':'b19bc4'}.get(tier,'708699')
    return {'linen':'96774f','wool':'89664a','silk':'826b52','moonweave':'698273','frostweave':'849ba3','duskweave':'6a6678','aetherweave':'a598ad'}.get(tier,'936e4c')


def weapon(p,j,item):
    """Draw model-space fittings around the actual gripping hand. No icon pivot guessing."""
    tags=item.get('tags',[]); family=tags[0] if tags else 'sword'
    hx,hy=j['hand_r']; angle=math.radians(j['angle']); cs,sn=math.cos(angle),math.sin(angle)
    c=palette(metal_for(item)); wood=palette('90704f'); leather=palette('684936')
    def xy(x,y): return (hx+x*cs-y*sn,hy+x*sn+y*cs)
    def poly(points,color): p.poly([xy(x,y) for x,y in points],color)
    def line(points,color,width=1): p.line([xy(x,y) for x,y in points],color,width)
    if family in ('bow','crossbow'):
        if family=='bow':
            line([(0,-17),(5,-11),(7,-4),(7,4),(4,12),(0,17)],INK,3)
            line([(0,-17),(5,-11),(7,-4),(7,4),(4,12),(0,17)],wood[3],1)
            line([(0,-17),(0,17)],'d9c9a8'); line([(-1,-2),(7,-2)],leather[3],3)
            line([(-8,0),(15,0)],'c3b397'); poly([(17,0),(13,-2),(13,2)],c[4])
        else:
            poly([(-3,-12),(2,-12),(3,8),(0,11),(-3,8)],wood[2])
            line([(-12,-8),(-7,-4),(0,-3),(7,-4),(12,-8)],c[3],3)
            line([(-12,-8),(0,2),(12,-8)],'d9c9a8'); line([(0,-13),(0,3)],c[4])
        return
    if family=='tome':
        poly([(-7,-10),(4,-12),(8,-8),(8,6),(-4,8),(-7,5)],'594b69')
        poly([(-4,-8),(5,-9),(5,4),(-4,6)],'887499'); line([(-6,-8),(-6,4)],leather[3],2)
        line([(6,-6),(6,3)],'dfd2ad',2); poly([(0,-6),(3,-2),(0,2),(-3,-2)],'c8b079'); return
    length=19 if family in ('dagger','wand','knuckles') else 27
    if family in ('spear','halberd','staff'): length=31
    line([(0,5),(0,-length+5)],INK,4); line([(0,4),(0,-length+5)],wood[3],2)
    if family in ('sword','greatsword','dagger'):
        width=3 if family=='greatsword' else 2
        poly([(-width,-5),(-width,-length+5),(0,-length),(width,-length+5),(width,-5)],c[2])
        line([(-1,-length+5),(-1,-6)],c[5]); line([(1,-length+6),(1,-6)],c[1])
        poly([(-6,-5),(-4,-7),(4,-7),(6,-5),(5,-4),(2,-5),(-2,-5),(-5,-4)],c[3])
        line([(0,-3),(0,3)],leather[2],3); line([(-1,-2),(1,-1)],leather[4]); poly([(-2,4),(0,6),(2,4),(0,2)],c[3])
    elif family in ('axe','greataxe','halberd'):
        poly([(0,-length+5),(5,-length+6),(10,-length+9),(9,-length+15),(5,-length+18),(3,-length+14),(0,-length+13)],c[2])
        line([(9,-length+9),(8,-length+14),(5,-length+17)],c[5])
        if family=='greataxe': poly([(0,-length+5),(-6,-length+6),(-10,-length+10),(-8,-length+15),(-4,-length+17),(-2,-length+13)],c[3])
        if family=='halberd': poly([(-2,-length+5),(0,-length),(2,-length+5),(1,-length+8)],c[4])
    elif family in ('mace','greatmace','hammer'):
        poly([(-5,-length+5),(4,-length+4),(7,-length+8),(5,-length+14),(-5,-length+14),(-7,-length+8)],c[2])
        line([(-4,-length+6),(3,-length+5)],c[5]); line([(-3,-length+7),(-3,-length+12)],c[4],2)
    elif family=='spear':
        poly([(-3,-length+6),(0,-length),(3,-length+6),(0,-length+11)],c[2]); line([(0,-length+2),(0,-length+8)],c[5])
    elif family in ('staff','wand'):
        gem=ELEMENT_COLORS.get(item.get('element','Arcane'),'ae9ccf')
        poly([(-4,-length+7),(-5,-length+2),(0,-length-2),(5,-length+2),(4,-length+7)],'a08a64')
        poly([(0,-length),(3,-length+3),(0,-length+6),(-3,-length+3)],gem)
        line([(-1,-length+1),(-2,-length+3)],shade(gem,1.15,15))
    elif family=='knuckles':
        poly([(-3,-5),(3,-5),(4,0),(2,3),(-3,2)],c[2]); line([(-2,-4),(2,-4)],c[5])
    else:
        poly([(-4,-length+7),(4,-length+6),(6,-length+12),(-4,-length+13)],c[3])
    line([(0,0),(0,3)],leather[2],3)


def equipment_frame(item,state,frame,direction,cached_icon=None):
    image=canvas(); p=Pixel(image); j=rig(state,frame,direction); slot=item.get('slot',''); base=clothing_base(item); c=palette(base)
    weight=next((tag for tag in item.get('tags',[]) if tag in ('light','medium','heavy')),'medium')
    hx,hy=j['hip']; nx,ny=j['neck']
    if slot=='weapon': weapon(p,j,item)
    elif slot=='chest':
        for side in ('l','r'): limb(p,j['shoulder_'+side],j['elbow_'+side],5,base)
        torso(p,j,base,6,weight=='light' and state!='death')
        if weight=='heavy':
            p.line([(nx,ny+4),(hx,hy-4)],c[1]); p.line([(hx-4,hy-5),(hx,hy-3),(hx+4,hy-5)],c[4])
            for side in ('l','r'):
                x,y=j['shoulder_'+side]; p.poly([(x-3,y-1),(x,y-3),(x+3,y),(x+2,y+3),(x-2,y+2)],c[2]); p.line([(x-2,y),(x,y-1)],c[4])
        else:
            p.line([(nx-3,ny+3),(hx+2,hy-3)],'574738',2)
            p.line([(nx-2,ny+3),(hx+3,hy-3)],'b89b6c')
        p.line([(hx-4,hy),(hx+4,hy)],'594838',2); p.rect((hx-1,hy-1,hx+1,hy+1),'bca16a',INK)
    elif slot=='legs':
        for side in ('l','r'):
            x=j['hip'][0]+(-2 if side=='l' else 2); limb(p,(x,hy),j['knee_'+side],5,base); limb(p,j['knee_'+side],j['foot_'+side],4,base)
            if weight=='heavy':
                kx,ky=j['knee_'+side]; p.poly([(kx-2,ky-2),(kx+2,ky-2),(kx+2,ky+1),(kx,ky+3),(kx-2,ky+1)],c[3]); p.dot(kx-1,ky-1,c[5])
    elif slot=='boots':
        for side in ('l','r'):
            x,y=j['foot_'+side]; kx,ky=j['knee_'+side]
            limb(p,(kx,ky+1),(x,y-1),5,base)
            p.poly([(x-2,y-2),(x+2,y-2),(x+4,y),(x+3,y+1),(x-3,y+1)],c[2]); p.line([(x-2,y),(x+2,y)],c[4]); p.line([(x-3,y+1),(x+3,y+1)],c[0])
    elif slot=='gloves':
        for side in ('l','r'):
            x,y=j['hand_'+side]; p.poly([(x-2,y-3),(x+2,y-3),(x+3,y),(x+1,y+2),(x-2,y+1)],c[2]); p.line([(x-1,y-2),(x+1,y-2)],c[4])
    elif slot=='helmet':
        x,y=j['head']
        p.poly([(x-5,y-3),(x-4,y-6),(x,y-8),(x+4,y-6),(x+5,y-3),(x+5,y+3),(x+3,y+5),(x+2,y),(x-2,y),(x-3,y+5),(x-5,y+3)],c[2])
        p.line([(x-3,y-4),(x-1,y-6),(x+1,y-6)],c[4]); p.line([(x-4,y-2),(x+4,y-2)],c[1])
        if weight=='heavy':
            p.line([(x,y-6),(x,y+4)],c[4]);
            if not j['back']: p.line([(x-3,y),(x-1,y)],INK); p.line([(x+1,y),(x+3,y)],INK)
        elif weight=='light': p.line([(x-4,y+2),(x-3,y-3),(x,y-5)],c[3])
    elif slot=='cloak':
        sway=round(j['stride']); end=min(55,hy+10)
        p.poly([(nx-4,ny),(nx+4,ny),(hx+8+sway,end-3),(hx+4+sway,end),(hx+sway,end-1),(hx-6+sway,end),(hx-8+sway,end-3)],c[2])
        p.poly([(nx-2,ny+2),(nx+1,ny+2),(hx+2+sway,end-3),(hx-3+sway,end-1)],c[3],None)
        p.line([(nx-3,ny+4),(hx-5+sway,end-3)],c[4]); p.line([(nx+3,ny+3),(hx+5+sway,end-2)],c[1])
    elif slot=='belt':
        p.line([(hx-5,hy),(hx+5,hy)],'71533b',3); p.rect((hx-1,hy-1,hx+1,hy+1),'cbb474',INK)
        p.poly([(hx+3,hy+1),(hx+6,hy+1),(hx+6,hy+5),(hx+3,hy+6)],c[2]); p.dot(hx+4,hy+2,c[4])
    elif slot=='offhand':
        family=item.get('tags',['shield'])[0]; x,y=j['hand_l']
        if family=='shield':
            metal=palette(metal_for(item)); narrow=3 if j['side'] else 6
            p.poly([(x-narrow,y-10),(x,y-12),(x+narrow,y-10),(x+narrow-1,y),(x,y+6),(x-narrow+1,y)],metal[2])
            p.poly([(x-narrow+2,y-8),(x,y-10),(x+narrow-2,y-8),(x+narrow-2,y-1),(x,y+3),(x-narrow+2,y-1)],'526b79')
            p.line([(x-narrow+1,y-9),(x,y-11)],metal[5]); p.line([(x,y-8),(x,y+2)],'baa46b'); p.rect((x-1,y-5,x+1,y-3),metal[4],INK)
        elif family=='quiver':
            p.poly([(nx+3,ny+1),(nx+7,ny),(hx+8,hy+3),(hx+4,hy+5)],'806143')
            for dx in (4,6): p.line([(nx+dx,ny-7),(hx+dx,hy)],'bba073'); p.line([(nx+dx-1,ny-7),(nx+dx+1,ny-4)],'d4d0b8')
        else:
            gem=ELEMENT_COLORS.get(item.get('element','Arcane'),'a5b8ca'); p.poly([(x,y-8),(x+4,y-4),(x+3,y+1),(x-3,y+1),(x-4,y-4)],c[2]); p.poly([(x,y-6),(x+2,y-3),(x,y-1),(x-2,y-3)],gem); p.dot(x-1,y-4,shade(gem,1.2,8))
    elif slot in ('necklace','charm','trinket'):
        if not j['back']: p.line([(nx-3,ny+1),(nx,ny+5),(nx+3,ny+1)],'b9a06a'); p.poly([(nx,ny+4),(nx+1,ny+6),(nx,ny+7),(nx-1,ny+6)],'a9bbb7')
        else: p.line([(hx+2,hy),(hx+4,hy+2)],'b9a06a')
    elif slot=='ring':
        x,y=j['hand_r']; p.line([(x,y),(x+1,y)],'dac48a')
    return finish(image,state,frame)


def layer_order(direction,equipment):
    if direction==3: return ('weapon','offhand','body','legs','boots','chest','belt','cloak','hair','helmet','necklace','charm','trinket','gloves','ring')
    far=('offhand',) if direction==2 else ('weapon',) if direction==1 else ()
    front=('weapon',) if direction==2 else ('offhand',) if direction==1 else ('offhand','weapon')
    return ('cloak',)+far+('body','legs','boots','chest','belt','hair','helmet','necklace','charm','trinket')+front+('gloves','ring')


def npc_frame(role,state,frame,direction):
    number=seed(role); skin=number%6; body=(number//6)%2; base=ROLE_COLORS.get(role,'839079')
    weight='light' if role in ('alchemist','enchanter','scholar','scribe','rune_merchant') else 'medium'
    gear={slot:dict(id='linen_'+weight+'_'+slot,slot=slot,tags=[weight],material='leather',_color=base) for slot in ('chest','legs','boots')}
    if role=='guard':
        gear['helmet']=dict(id='linen_heavy_helmet',slot='helmet',tags=['heavy'],material='iron')
        gear['weapon']=dict(id='iron_spear',slot='weapon',tags=['spear'],material='iron')
    if role in ('scholar','scribe','banker','guild_registrar'): gear['weapon']=dict(id='copper_tome',slot='weapon',tags=['tome'],material='leather')
    image=canvas()
    for slot in layer_order(direction,gear):
        if slot=='body': layer=body_frame(body,skin,state,frame,direction)
        elif slot=='hair': layer=hair_frame((number//11)%6,(number//17)%8,state,frame,direction)
        elif slot in gear: layer=equipment_frame(gear[slot],state,frame,direction)
        else: continue
        image.alpha_composite(layer)
    if role in ('blacksmith','tanner','carpenter','woodworker','miner'):
        p=Pixel(image); j=rig(state,frame,direction); nx,ny=j['neck']; x,y=j['hip']
        if not j['back']:
            p.poly([(nx-3,ny+4),(nx+3,ny+4),(x+4,y+3),(x-4,y+3)],'967c59'); p.line([(nx-2,ny+5),(x-2,y+1)],'b99c70'); p.line([(x-2,y-3),(x+2,y-3)],'5c4a37')
    return image
