from __future__ import annotations
import math
from PIL import Image
from .common import Pixel,canvas,palette,shade,rgba,animation_pose,finish_frame,seed,METALS,INK
from .items import icon as item_icon,metal_for

SKINS=('edcba6','d7b28c','bd936f','a57a59','825b45','604435')
HAIRS=('463b36','72543d','9d7749','c9ad70','8d4f3f','3a353e','b4bab4','765d77')
CLOTHS={'linen':'778d78','wool':'7e738d','silk':'916078','moonweave':'8099b2','frostweave':'83aeb2','duskweave':'775f89','aetherweave':'b19bc4'}


def joints(state,frame,direction,body=0):
    pose=animation_pose(state,frame,direction); bob=pose['bob']; stride=pose['stride']; side=pose['side']
    center=32; shoulder_width=5 if body==0 else 4
    hand_left=(center-8,37+bob+round(stride*2)); hand_right=(center+8,37+bob-round(stride*2))
    if side:
        hand_left=(center-2,37+bob+round(stride*3)); hand_right=(center+5,37+bob-round(stride*3))
    if pose['attack']:
        hand_right=(center+8+round(pose['attack']*5),37+bob-round(pose['attack']*17))
    if pose['cast']:
        hand_left=(center-10,35+bob-round(pose['cast']*10)); hand_right=(center+10,35+bob-round(pose['cast']*10))
    return dict(**pose,cx=center,head=(center+(2 if side else 0),16+bob),neck=(center,24+bob),hip=(center,40+bob),
        shoulder_l=(center-shoulder_width,27+bob),shoulder_r=(center+shoulder_width,27+bob),hand_l=hand_left,hand_r=hand_right,
        knee_l=(center-3,46+bob+round(stride*2)),knee_r=(center+3,46+bob-round(stride*2)),
        foot_l=(center-4+round(stride*2),54+round(stride*2)),foot_r=(center+4-round(stride*2),54-round(stride*2)))


def orient(image,state,frame,direction):
    if direction==1: image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return finish_frame(image,state,frame,direction)


def body_frame(body,skin,state,frame,direction):
    image=canvas(); p=Pixel(image); j=joints(state,frame,direction,body); base=SKINS[skin]; c=palette(base); b=j['bob']; cx=j['cx']
    # A jointed skeleton controls gait. Each limb keeps a separate contour.
    for side in ('l','r'):
        hip=(cx+(-3 if side=='l' else 3),40+b)
        p.limb(hip,j['knee_'+side],5,'69666a'); p.limb(j['knee_'+side],j['foot_'+side],4,base)
        fx,fy=j['foot_'+side]; p.ellipse((fx-3,fy-2,fx+3,fy+1),c[2],INK); p.line([(fx-2,fy-1),(fx+1,fy-1)],c[4])
    for side in ('l','r'):
        p.limb(j['shoulder_'+side],j['hand_'+side],5,base)
        hx,hy=j['hand_'+side]; p.ellipse((hx-2,hy-2,hx+2,hy+2),c[3],INK); p.dot(hx-1,hy-1,c[5])
    torso=[(cx-5,25+b),(cx+5,25+b),(cx+7,34+b),(cx+5,43+b),(cx-5,43+b),(cx-7,34+b)]
    p.poly(torso,'b1a691'); p.poly([(cx-3,27+b),(cx+2,27+b),(cx+4,39+b),(cx-3,40+b)],'c6baa3',None)
    p.line([(cx+4,28+b),(cx+5,39+b)],'857e74'); p.rect((cx-5,39+b,cx+5,43+b),'6f6863',INK)
    p.rect((cx-2,22+b,cx+2,26+b),c[2]); p.line([(cx-1,23+b),(cx-1,25+b)],c[4])
    hx,hy=j['head']
    p.sphere((hx-6,hy-8,hx+6,hy+7),base)
    if j['side']:
        p.poly([(hx+4,hy-3),(hx+8,hy),(hx+7,hy+2),(hx+4,hy+3)],c[3]); p.line([(hx+5,hy+4),(hx+7,hy+4)],c[1]); p.dot(hx+4,hy-2,INK); p.dot(hx+4,hy-3,c[5]); p.ellipse((hx-4,hy-1,hx-1,hy+3),c[2],c[1]); p.dot(hx-2,hy,c[4])
    elif not j['back']:
        p.ellipse((hx-8,hy-1,hx-5,hy+3),c[2],INK); p.ellipse((hx+5,hy-1,hx+8,hy+3),c[2],INK)
        for x in (hx-3,hx+3): p.line([(x-1,hy-2),(x+1,hy-2)],c[0]); p.dot(x,hy-1,INK); p.dot(x-1,hy-1,'e3dbc5')
        p.line([(hx,hy),(hx-1,hy+2),(hx+1,hy+2)],c[2]); p.line([(hx-2,hy+5),(hx+1,hy+5)],c[1]); p.dot(hx-2,hy+4,c[4])
    return orient(image,state,frame,direction)


def hair_frame(style,color,state,frame,direction):
    image=canvas(); p=Pixel(image); j=joints(state,frame,direction); hx,hy=j['head']; base=HAIRS[color]; c=palette(base)
    if style==4:  # ponytail, visible as a tied articulated lock rather than a circle
        shift=round(j['stride']*2)
        p.poly([(hx-2,hy-6),(hx+3,hy-5),(hx+7+shift,hy+5),(hx+5+shift,hy+17),(hx+1+shift,hy+20),(hx+2+shift,hy+7)],c[2]); p.line([(hx+2,hy-4),(hx+5+shift,hy+7),(hx+3+shift,hy+16)],c[4]); p.rect((hx+2,hy+3,hx+6,hy+5),'b9a471',INK)
    if style==2:  # braid
        for n in range(6):
            y=hy+3+n*3; x=hx+(1 if n%2 else -1)
            p.poly([(x-3,y),(x,y-2),(x+3,y),(x,y+3)],c[3]); p.line([(x-2,y),(x,y+1)],c[4])
        p.rect((hx-2,hy+20,hx+2,hy+22),'bf9864',INK)
    if style==5: p.sphere((hx-5,hy-13,hx+4,hy-5),base)
    if style==1: p.poly([(hx-7,hy-4),(hx+7,hy-4),(hx+8,hy+8),(hx+4,hy+11),(hx-7,hy+8)],c[1])
    p.poly([(hx-6,hy-7),(hx-2,hy-10),(hx+4,hy-9),(hx+7,hy-5),(hx+6,hy-1),(hx+2,hy-4),(hx-1,hy-2),(hx-5,hy-3),(hx-7,hy+1)],c[2])
    p.poly([(hx-5,hy-6),(hx-1,hy-8),(hx+3,hy-7),(hx+4,hy-5),(hx-1,hy-5)],c[3],None); p.line([(hx-4,hy-6),(hx,hy-7),(hx+3,hy-6)],c[5])
    if style==3:
        p.poly([(hx-2,hy-9),(hx-2,hy-14),(hx+1,hy-12),(hx+3,hy-15),(hx+4,hy-8),(hx+2,hy-2)],c[3]); p.line([(hx,hy-11),(hx+2,hy-10)],c[5])
    if j['back']:
        p.poly([(hx-6,hy-4),(hx+6,hy-4),(hx+6,hy+5),(hx+3,hy+8),(hx-4,hy+7),(hx-6,hy+3)],c[2]);
        for x in (-3,0,3): p.line([(hx+x,hy-3),(hx+x+1,hy+5)],c[3])
        p.line([(hx-4,hy-4),(hx-4,hy+2)],c[4])
    elif j['side']: p.rect((hx-6,hy-3,hx-3,hy+4),c[2]); p.line([(hx-5,hy-2),(hx-5,hy+2)],c[4])
    return orient(image,state,frame,direction)


def clothing_base(item):
    weight=next((x for x in item.get('tags',[]) if x in {'light','medium','heavy'}),'medium')
    tier=item['id'].split('_')[0]
    if weight=='light': return CLOTHS.get(tier,'718893')
    if weight=='heavy':
        return {'linen':'929b9d','wool':'8e9b9f','silk':'abbec6','moonweave':'b6c5ce','frostweave':'82a6b8','duskweave':'b0c6c2','aetherweave':'c6c8dc'}.get(tier,metal_for(item))
    return {'linen':'95744e','wool':'8a6448','silk':'82694b','moonweave':'698071','frostweave':'94a5a4','duskweave':'6b687c','aetherweave':'a598ad'}.get(tier,'906c4c')


def equipment_frame(item,state,frame,direction,cached_icon=None):
    image=canvas(); p=Pixel(image); j=joints(state,frame,direction); cx=j['cx']; b=j['bob']; slot=item.get('slot',''); c=palette(clothing_base(item)); base=clothing_base(item)
    weight=next((x for x in item.get('tags',[]) if x in {'light','medium','heavy'}),'medium')
    if slot=='weapon':
        art=cached_icon if cached_icon is not None else item_icon(item)
        weapon=canvas(); weapon.alpha_composite(art,(24,2)); angle=-15-round(j['attack']*100)
        if j['cast']: angle=-30-round(j['cast']*35)
        if j['side']: angle-=15
        if j['back']: angle=20-round(j['attack']*80)
        weapon=weapon.rotate(angle,resample=Image.Resampling.NEAREST,center=(40,30))
        hx,hy=j['hand_r']; image.alpha_composite(weapon,(round(hx-40),round(hy-30)))
    elif slot=='offhand':
        family=item.get('tags',['shield'])[0]; hx,hy=j['hand_l']
        if family=='shield':
            p.poly([(hx-7,hy-12),(hx,hy-15),(hx+7,hy-12),(hx+6,hy+1),(hx,hy+8),(hx-6,hy+1)],'859397'); p.poly([(hx-5,hy-10),(hx,hy-12),(hx+5,hy-10),(hx+4,hy),(hx,hy+5),(hx-4,hy)],'596f7b'); p.line([(hx,hy-11),(hx,hy+4)],'c0bb92'); p.sphere((hx-3,hy-7,hx+3,hy-1),'c3bda0'); p.line([(hx-5,hy-10),(hx-5,hy-1)],'b8c4bd')
        elif family=='quiver':
            p.poly([(cx+4,25+b),(cx+10,23+b),(cx+11,43+b),(cx+6,46+b)],'8f6c46');
            for x in (cx+5,cx+8,cx+10): p.line([(x,18+b),(x+1,35+b)],'baa16a'); p.line([(x-1,18+b),(x+1,21+b)],'c4ccbb')
        else:
            art=(cached_icon if cached_icon is not None else item_icon(item)).resize((18,18),Image.Resampling.NEAREST); image.alpha_composite(art,(round(hx-9),round(hy-15)))
    elif slot=='chest':
        if weight=='light':
            p.poly([(cx-6,25+b),(cx+6,25+b),(cx+7,38+b),(cx+10,50+b),(cx+4,52+b),(cx,49+b),(cx-5,52+b),(cx-10,50+b),(cx-7,37+b)],c[2]); p.poly([(cx-3,28+b),(cx+2,28+b),(cx+5,48+b),(cx,49+b),(cx-4,48+b)],c[3],None)
            for dx in (-6,0,6): p.line([(cx+dx*.6,36+b),(cx+dx,49+b)],c[1])
            p.line([(cx-5,27+b),(cx,33+b),(cx+5,27+b)],'d4c193'); p.line([(cx-7,49+b),(cx-4,50+b)],c[5]); p.line([(cx+3,50+b),(cx+7,49+b)],c[4])
        else:
            p.poly([(cx-6,25+b),(cx+6,25+b),(cx+8,31+b),(cx+6,42+b),(cx,44+b),(cx-6,42+b),(cx-8,31+b)],c[2]);
            p.poly([(cx-4,27+b),(cx+4,27+b),(cx+5,36+b),(cx,40+b),(cx-5,36+b)],c[3]); p.line([(cx-4,28+b),(cx-3,34+b)],c[5]); p.line([(cx+4,28+b),(cx+4,36+b)],c[1])
            if weight=='heavy':
                p.line([(cx,27+b),(cx,39+b)],c[1]); p.line([(cx-5,36+b),(cx,39+b),(cx+5,36+b)],c[4]);
                for y in (40,43): p.line([(cx-5,y+b),(cx+5,y+b)],c[1]); p.line([(cx-5,y-1+b),(cx+4,y-1+b)],c[4])
                for side in ('l','r'):
                    sx,sy=j['shoulder_'+side]; p.sphere((sx-4,sy-3,sx+4,sy+4),base); p.line([(sx-3,sy+2),(sx+3,sy+2)],c[0]); p.dot(sx-2,sy-1,c[5])
            else:
                p.line([(cx,27+b),(cx,40+b)],c[0]);
                for y in (30,34,38): p.line([(cx-2,y+b),(cx+2,y-1+b)],'c4ad79')
                p.rect((cx-6,39+b,cx+6,41+b),'5d4635',INK); p.rect((cx-1,38+b,cx+2,42+b),'b6a16b',INK)
        for side in ('l','r'):
            sx,sy=j['shoulder_'+side]; hx,hy=j['hand_'+side]
            elbow=(sx+(hx-sx)*.55,sy+(hy-sy)*.55)
            p.limb((sx,sy+1),elbow,5,base); p.line([(elbow[0]-2,elbow[1]),(elbow[0]+2,elbow[1])],c[0])
    elif slot=='legs':
        for side in ('l','r'):
            hip=(cx+(-3 if side=='l' else 3),40+b); knee=j['knee_'+side]; foot=j['foot_'+side]
            p.limb(hip,knee,5,base); p.limb(knee,(foot[0],foot[1]-3),4,base)
            if weight=='heavy': p.sphere((knee[0]-3,knee[1]-2,knee[0]+3,knee[1]+2),base)
            else: p.line([(knee[0]-1,knee[1]-2),(knee[0]+1,knee[1]+1)],c[1])
    elif slot=='boots':
        for side in ('l','r'):
            foot=j['foot_'+side]; knee=j['knee_'+side]; fx,fy=foot
            p.limb((knee[0],knee[1]+2),(fx,fy-1),5,base)
            p.poly([(fx-3,fy-2),(fx+2,fy-2),(fx+4,fy),(fx+3,fy+2),(fx-4,fy+2)],c[2]); p.line([(fx-2,fy),(fx+2,fy)],c[4]); p.line([(fx-4,fy+2),(fx+3,fy+2)],c[0]); p.line([(knee[0]-2,knee[1]+2),(knee[0]+2,knee[1]+2)],c[4])
    elif slot=='gloves':
        for side in ('l','r'):
            hx,hy=j['hand_'+side]; p.sphere((hx-3,hy-4,hx+3,hy+2),base); p.line([(hx-2,hy-2),(hx+2,hy-2)],c[1]); p.line([(hx-2,hy),(hx+1,hy)],c[4])
    elif slot=='helmet':
        hx,hy=j['head']
        if weight=='heavy':
            p.sphere((hx-7,hy-9,hx+7,hy+7),base)
            if not j['back']:
                p.poly([(hx-5,hy-2),(hx+6,hy-2),(hx+6,hy+2),(hx+3,hy+3),(hx-4,hy+2)],'252b32'); p.rect((hx-1,hy-8,hx+1,hy+5),c[4]); p.line([(hx-5,hy-3),(hx+5,hy-3)],c[5]);
                for x in (-3,3,5): p.dot(hx+x,hy+5,c[0])
            p.line([(hx-5,hy-6),(hx-2,hy-8),(hx+2,hy-8)],c[5])
        elif weight=='medium':
            p.poly([(hx-7,hy-6),(hx-3,hy-10),(hx+4,hy-9),(hx+7,hy-5),(hx+6,hy+3),(hx+3,hy-3),(hx-4,hy-3),(hx-6,hy+3)],c[2]); p.line([(hx-5,hy-5),(hx+5,hy-5)],c[4]); p.line([(hx,hy-8),(hx,hy-4)],c[1])
        else:
            p.poly([(hx-8,hy+6),(hx-7,hy-7),(hx-2,hy-11),(hx+4,hy-9),(hx+8,hy+6),(hx+4,hy+9),(hx+4,hy-3),(hx-3,hy-4),(hx-5,hy+8)],c[2]); p.line([(hx-5,hy-5),(hx-4,hy-8),(hx-1,hy-9)],c[4]); p.line([(hx+5,hy-2),(hx+6,hy+5)],c[1])
    elif slot=='cloak':
        sway=round(j['stride']*2)
        p.poly([(cx-5,26+b),(cx+5,26+b),(cx+8+sway,46+b),(cx+5+sway,51),(cx+sway,49),(cx-6+sway,52),(cx-9+sway,48)],c[2]); p.poly([(cx-3,28+b),(cx+1,28+b),(cx+3+sway,48),(cx-3+sway,49)],c[3],None); p.line([(cx-4,30+b),(cx-6+sway,47)],c[4]); p.line([(cx+4,30+b),(cx+6+sway,47)],c[1])
    elif slot=='belt':
        p.rect((cx-7,39+b,cx+7,42+b),'6f4f39',INK); p.line([(cx-6,40+b),(cx+6,40+b)],'b2915c'); p.rect((cx-1,39+b,cx+2,42+b),'ccb573',INK); p.poly([(cx+5,40+b),(cx+9,41+b),(cx+9,46+b),(cx+5,46+b)],'876847')
    elif slot in {'necklace','charm','trinket'}:
        p.line([(cx-4,26+b),(cx-2,30+b),(cx+2,30+b),(cx+4,26+b)],'c8b877'); p.sphere((cx-1,29+b,cx+2,33+b),'a5b8b8')
    elif slot=='ring':
        hx,hy=j['hand_r']; p.line([(hx,hy),(hx+2,hy)],'d8c48d')
    return orient(image,state,frame,direction)


ROLE_COLORS={'blacksmith':'827369','armorer':'778b96','weaponsmith':'8b7467','fletcher':'6f8665','provisioner':'b09872','alchemist':'6d8b82','rune_merchant':'7c78a1','enchanter':'8e7199','jeweler':'ad9971','banker':'707f99','auctioneer':'956c65','innkeeper':'a28568','guild_registrar':'8a6679','tailor':'a08199','tanner':'947153','carpenter':'967e61','woodworker':'8d8468','scribe':'71899a','guard':'80949e','scholar':'91839e','ferryman':'6b8b9b','herbalist':'7f9975','miner':'877b6f','fisher':'809993','trainer':'987a6c','traveler':'8b876f'}


def npc_frame(role,state,frame,direction):
    number=seed(role); skin=number%6; body=(number//6)%2
    image=body_frame(body,skin,state,frame,direction)
    # NPC clothing uses the same skeleton and alignment contract as equipment.
    base=ROLE_COLORS.get(role,'839079')
    item=dict(id='linen_medium_chest',slot='chest',tags=['medium'],material='leather')
    overlay=equipment_frame(item,state,frame,direction)
    # Replace only the clothing ramp. Skin and hair are never recolored together.
    source=palette(clothing_base(item)); target=palette(base); mapping=dict(zip(source,target))
    overlay.putdata([mapping.get(pixel,pixel) for pixel in overlay.getdata()]); image.alpha_composite(overlay)
    legs=dict(id='linen_medium_legs',slot='legs',tags=['medium'],material='leather')
    image.alpha_composite(equipment_frame(legs,state,frame,direction)); image.alpha_composite(equipment_frame(dict(legs,id='linen_medium_boots',slot='boots'),state,frame,direction))
    image.alpha_composite(hair_frame((number//11)%6,(number//17)%8,state,frame,direction))
    accessory=canvas(); p=Pixel(accessory); j=joints(state,frame,direction,body); cx=j['cx']; b=j['bob']
    if role in {'blacksmith','tanner','carpenter','woodworker','miner'}:
        p.poly([(cx-4,29+b),(cx+4,29+b),(cx+6,44+b),(cx-5,44+b)],'aa987a'); p.line([(cx-3,31+b),(cx-3,42+b)],'d0bd97'); p.rect((cx-2,35+b,cx+3,39+b),'87735b',INK)
    if role in {'scribe','scholar','guild_registrar','banker','auctioneer'}:
        art=item_icon(dict(id='copper_tome',type='weapon',tags=['tome'],material='leather',element='Arcane')).resize((15,15),Image.Resampling.NEAREST)
        hx,hy=j['hand_l']; accessory.alpha_composite(art,(round(hx-7),round(hy-9)))
    if role=='guard':
        helm=dict(id='linen_heavy_helmet',slot='helmet',tags=['heavy'],material='metal'); image.alpha_composite(equipment_frame(helm,state,frame,direction))
        weapon=dict(id='iron_spear',type='weapon',slot='weapon',tags=['spear'],material='iron'); image.alpha_composite(equipment_frame(weapon,state,frame,direction))
    if role in {'fisher','ferryman','traveler'}:
        hx,hy=j['head']; p.poly([(hx-10,hy-5),(hx-4,hy-10),(hx+5,hy-9),(hx+10,hy-4),(hx+5,hy-2),(hx-6,hy-2)],'9b8c6c'); p.line([(hx-8,hy-4),(hx+7,hy-3)],'d5c29b')
    if role in {'alchemist','herbalist','rune_merchant','enchanter'}:
        hx,hy=j['hand_l']; p.sphere((hx-3,hy-5,hx+3,hy+1),'92b4a2'); p.rect((hx-1,hy-7,hx+1,hy-5),'b39872',INK)
    accessory=orient(accessory,state,frame,direction); image.alpha_composite(accessory)
    return image
