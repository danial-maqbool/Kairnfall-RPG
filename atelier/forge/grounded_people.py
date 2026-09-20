"""Grounded 2026 humanoid renderer for Kairnfall.

This is a new authored visual construction for the active player/NPC/equipment rig.
It keeps the runtime's 64 px, four-direction, six-state, eight-frame contract and
shared foot anchor, but redraws anatomy, hair, clothing, armour, tools and held
weapons from the common skeletal joints. No legacy sprite pixels are sampled.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw

from . import pigment, rig

SIZE = 64
INK = (24, 22, 24, 255)
DEEP = (15, 14, 16, 255)
EYE = (31, 28, 28, 255)
UNDERSHIRT = '#71624f'
TROUSER = '#4d4840'
BOOT = '#3a2d25'
BELT = '#493426'


def _pt(p): return int(round(p[0])), int(round(p[1]))
def _axis(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; n=math.hypot(dx,dy) or 1.0
    return dx/n,dy/n
def _normal(a,b):
    ux,uy=_axis(a,b); return -uy,ux
def _quad(a,b,wa,wb):
    px,py=_normal(a,b)
    return [(a[0]+px*wa/2,a[1]+py*wa/2),(b[0]+px*wb/2,b[1]+py*wb/2),
            (b[0]-px*wb/2,b[1]-py*wb/2),(a[0]-px*wa/2,a[1]-py*wa/2)]
def _poly(draw,points,fill,outline=INK):
    pts=[_pt(p) for p in points]; draw.polygon(pts,fill=fill)
    if outline: draw.line(pts+[pts[0]],fill=outline,width=1)
def _line(draw,points,fill,width=1): draw.line([_pt(p) for p in points],fill=fill,width=width)
def _disc(draw,p,r,fill,outline=INK):
    x,y=p; draw.ellipse((round(x-r),round(y-r),round(x+r),round(y+r)),fill=fill,outline=outline,width=1)

def _segment(draw,a,b,wa,wb,ramp,near=True):
    shade=ramp[3] if near else ramp[2]; _poly(draw,_quad(a,b,wa,wb),shade)
    px,py=_normal(a,b)
    _line(draw,[(a[0]-px*wa*.18,a[1]-py*wa*.18),(b[0]-px*wb*.18,b[1]-py*wb*.18)],ramp[1])
    _line(draw,[(a[0]+px*wa*.22-.4,a[1]+py*wa*.22-.4),(b[0]+px*wb*.22-.4,b[1]+py*wb*.22-.4)],ramp[5])

def _hand(draw,elbow,hand,ramp,near=True):
    ux,uy=_axis(elbow,hand); px,py=-uy,ux; length=3.0 if near else 2.7; width=2.8 if near else 2.4
    wrist=(hand[0]-ux,hand[1]-uy); tip=(hand[0]+ux*length,hand[1]+uy*length)
    _poly(draw,[(wrist[0]+px*width*.48,wrist[1]+py*width*.48),(tip[0]+px*width*.28,tip[1]+py*width*.28),
                (tip[0]+ux*.45,tip[1]+uy*.45),(tip[0]-px*width*.32,tip[1]-py*width*.32),
                (wrist[0]-px*width*.48,wrist[1]-py*width*.48)],ramp[3])
    thumb=(hand[0]+px*(1.25 if near else 1.0),hand[1]+py*(1.25 if near else 1.0)); _disc(draw,thumb,.9,ramp[3],None)
    _line(draw,[(hand[0]+ux*.6,hand[1]+uy*.6),(hand[0]+ux*1.8-px*.7,hand[1]+uy*1.8-py*.7)],ramp[1])

def _boot(draw,knee,foot,ramp,facing,near=True):
    ux,uy=_axis(knee,foot); px,py=-uy,ux; toe=facing if facing else (1 if near else -1)
    ankle=(foot[0]-ux*3.1,foot[1]-uy*3.1); forward=(px*toe,py*toe); sole=(foot[0]+ux*.25,foot[1]+uy*.25)
    shape=[(ankle[0]-forward[0]*1.7,ankle[1]-forward[1]*1.7),(ankle[0]+forward[0]*1.4,ankle[1]+forward[1]*1.4),
           (sole[0]+forward[0]*4.2,sole[1]+forward[1]*4.2),(sole[0]+forward[0]*3.2+ux*.5,sole[1]+forward[1]*3.2+uy*.5),
           (sole[0]-forward[0]*2.1,sole[1]-forward[1]*2.1)]
    _poly(draw,shape,ramp[3]); ys=[p[1] for p in shape]; xs=[p[0] for p in shape]
    _line(draw,[(min(xs)+1,max(ys)-1),(max(xs)-1,max(ys)-1)],ramp[0])

def _leg(draw,pose,key,trouser,boot,near):
    hip,knee,foot=pose.hip[key],pose.knee[key],pose.foot[key]
    thigh_end=(hip[0]+(knee[0]-hip[0])*.83,hip[1]+(knee[1]-hip[1])*.83)
    calf_start=(knee[0]+(foot[0]-knee[0])*.08,knee[1]+(foot[1]-knee[1])*.08)
    boot_top=(knee[0]+(foot[0]-knee[0])*.62,knee[1]+(foot[1]-knee[1])*.62); depth=1.0 if near else .88
    _segment(draw,hip,thigh_end,pose.build.thigh*1.02*depth,pose.build.thigh*.78*depth,trouser,near)
    _segment(draw,thigh_end,knee,pose.build.thigh*.80*depth,pose.build.thigh*.66*depth,trouser,near)
    _disc(draw,knee,pose.build.thigh*.26*depth,trouser[3 if near else 2],None)
    _segment(draw,calf_start,boot_top,pose.build.thigh*.68*depth,pose.build.thigh*.54*depth,trouser,near)
    _segment(draw,boot_top,(foot[0],foot[1]-1.6),pose.build.thigh*.59*depth,pose.build.thigh*.48*depth,boot,near)
    _boot(draw,knee,foot,boot,pose.facing,near)

def _arm(draw,pose,key,skin,cloth,near):
    shoulder,elbow,hand=pose.shoulder[key],pose.elbow[key],pose.hand[key]; depth=1.0 if near else .86
    sleeve_end=(shoulder[0]+(elbow[0]-shoulder[0])*.56,shoulder[1]+(elbow[1]-shoulder[1])*.56)
    _disc(draw,shoulder,pose.build.limb*.61*depth,cloth[3 if near else 2])
    _segment(draw,shoulder,sleeve_end,pose.build.limb*1.16*depth,pose.build.limb*.98*depth,cloth,near)
    _line(draw,[(sleeve_end[0]-1.5,sleeve_end[1]),(sleeve_end[0]+1.5,sleeve_end[1])],cloth[0])
    _segment(draw,sleeve_end,elbow,pose.build.limb*.83*depth,pose.build.limb*.69*depth,skin,near)
    _disc(draw,elbow,pose.build.limb*.25*depth,skin[3 if near else 2],None)
    _segment(draw,elbow,hand,pose.build.limb*.68*depth,pose.build.limb*.54*depth,skin,near); _hand(draw,elbow,hand,skin,near)

def _torso(draw,pose,skin,cloth,belt):
    chest,pelvis=pose.chest,pose.pelvis; ux,uy=_axis(pelvis,chest); px,py=-uy,ux
    top=(pose.neck[0]-ux*.8,pose.neck[1]-uy*.8); ribs=(chest[0]+(pelvis[0]-chest[0])*.45,chest[1]+(pelvis[1]-chest[1])*.45)
    waist=(chest[0]+(pelvis[0]-chest[0])*.76,chest[1]+(pelvis[1]-chest[1])*.76); bottom=(pelvis[0]-ux,pelvis[1]-uy)
    shoulder=pose.build.chest_depth if pose.side else pose.build.shoulder*.93; rib=pose.build.chest_depth*.95 if pose.side else pose.build.shoulder*.76
    waist_w=pose.build.chest_depth*.76 if pose.side else pose.build.hip*.92; hip=pose.build.chest_depth*.82 if pose.side else pose.build.hip+1.0
    _poly(draw,[(top[0]-px*shoulder*.58,top[1]-py*shoulder*.58),(chest[0]-px*shoulder,chest[1]-py*shoulder),(ribs[0]-px*rib,ribs[1]-py*rib),
                (waist[0]-px*waist_w,waist[1]-py*waist_w),(bottom[0]-px*hip,bottom[1]-py*hip),(bottom[0]+px*hip,bottom[1]+py*hip),
                (waist[0]+px*waist_w,waist[1]+py*waist_w),(ribs[0]+px*rib,ribs[1]+py*rib),(chest[0]+px*shoulder,chest[1]+py*shoulder),
                (top[0]+px*shoulder*.58,top[1]+py*shoulder*.58)],cloth[3])
    _line(draw,[(chest[0]-px*shoulder*.55-1,chest[1]-py*shoulder*.55-1),(ribs[0]-1,ribs[1]-1)],cloth[5])
    _line(draw,[(chest[0]+px*shoulder*.58+1,chest[1]+py*shoulder*.58+1),(waist[0]+px*waist_w*.8+1,waist[1]+py*waist_w*.8+1)],cloth[1])
    if not pose.back:
        _line(draw,[(top[0]-px*2.4,top[1]-py*2.4),(top[0],top[1]+uy*2.2),(top[0]+px*2.4,top[1]+py*2.4)],cloth[0])
        if not pose.side: _line(draw,[(chest[0],chest[1]-1),(waist[0],waist[1]-1)],cloth[1])
    _segment(draw,(pose.chest[0]+ux*4.0,pose.chest[1]+uy*4.0),(pose.head[0]-ux*pose.head_r*.65,pose.head[1]-uy*pose.head_r*.65),4.1,3.7,skin,True)
    _line(draw,[(waist[0]-px*(hip+.2),waist[1]-py*(hip+.2)),(waist[0]+px*(hip+.2),waist[1]+py*(hip+.2))],belt[2],2)
    if not pose.side: _disc(draw,waist,1.4,belt[5],belt[0])

def _head(draw,pose,skin):
    x,y=pose.head; r=pose.head_r
    if pose.side:
        f=pose.facing or 1; pts=[(x-f*r*.78,y-r*.92),(x+f*r*.30,y-r),(x+f*r*.80,y-r*.65),(x+f*r*.98,y-r*.08),
                               (x+f*r*.80,y+r*.46),(x+f*r*.48,y+r*.87),(x+f*r*.10,y+r*1.02),(x-f*r*.43,y+r*.75),(x-f*r*.72,y+r*.18),(x-f*r*.78,y-r*.43)]
    else:
        pts=[(x-r*.66,y-r*.96),(x+r*.66,y-r*.96),(x+r*.90,y-r*.58),(x+r*.94,y+r*.12),(x+r*.68,y+r*.63),(x+r*.35,y+r*.88),
             (x+r*.16,y+r*1.02),(x-r*.16,y+r*1.02),(x-r*.35,y+r*.88),(x-r*.68,y+r*.63),(x-r*.94,y+r*.12),(x-r*.90,y-r*.58)]
    _poly(draw,pts,skin[3]); _poly(draw,[(x-r*.56,y-r*.72),(x-r*.12,y-r*.87),(x+r*.13,y-r*.74),(x-r*.28,y-r*.25)],skin[5],None)
    _poly(draw,[(x+r*.40,y+r*.06),(x+r*.66,y+r*.38),(x+r*.28,y+r*.80),(x-r*.04,y+r*.89)],skin[2],None)
    if pose.back: return
    if pose.side:
        f=pose.facing or 1; _disc(draw,(x-f*r*.56,y+.3),1.1,skin[2]); _poly(draw,[(x+f*(r-.5),y-.3),(x+f*(r+1.4),y+1.0),(x+f*(r-.2),y+1.45)],skin[3])
        _disc(draw,(x+f*2.0,y-.55),.75,EYE,None); _line(draw,[(x+f*.8,y-2.0),(x+f*2.8,y-1.7)],skin[0]); _line(draw,[(x+f*1.1,y+3.0),(x+f*2.7,y+3.0)],DEEP)
    else:
        for s in (-1,1):
            _disc(draw,(x+s*1.9,y-.55),.75,EYE,None); draw.point(_pt((x+s*1.7,y-1.1)),fill=(225,211,185,255)); _line(draw,[(x+s*.9,y-1.8),(x+s*2.8,y-1.65)],skin[0])
        _line(draw,[(x-.1,y+.1),(x+.2,y+1.8)],skin[1]); _line(draw,[(x-1.4,y+3.35),(x+1.4,y+3.35)],skin[0])
    if pose.state=='hit': _line(draw,[(x-1.5,y+3.5),(x,y+2.9),(x+1.5,y+3.5)],DEEP)
    elif pose.state=='attack': _line(draw,[(x-1.4,y+3.1),(x,y+3.65),(x+1.7,y+3.05)],DEEP)

def body_frame(build,skin_index,state,frame,direction):
    pose=rig.pose(build,state,frame,direction); image=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0)); draw=ImageDraw.Draw(image)
    skin=pigment.ramp(pigment.SKIN[max(0,min(5,skin_index))]); cloth=pigment.ramp(UNDERSHIRT); trouser=pigment.ramp(TROUSER); boot=pigment.ramp(BOOT); belt=pigment.ramp(BELT)
    raised={k:pose.hand[k][1]<pose.shoulder[k][1]-1.5 for k in ('far','near')}
    if not raised['far']: _arm(draw,pose,'far',skin,cloth,False)
    _leg(draw,pose,'far',trouser,boot,False); _torso(draw,pose,skin,cloth,belt); _leg(draw,pose,'near',trouser,boot,True)
    if not raised['near']: _arm(draw,pose,'near',skin,cloth,True)
    _head(draw,pose,skin)
    for k in ('far','near'):
        if raised[k]: _arm(draw,pose,k,skin,cloth,k=='near')
    if pose.flash:
        overlay=Image.new('RGBA',image.size,(255,235,210,0)); overlay.putalpha(image.getchannel('A').point(lambda a:round(a*pose.flash*.45))); image=Image.alpha_composite(image,overlay)
    if pose.fade<1: image.putalpha(image.getchannel('A').point(lambda a:round(a*pose.fade)))
    return image

HAIR_STYLES=('crop','long','tail','braids','curls','topknot')
def hair_frame(style,colour,state,frame,direction):
    pose=rig.pose(0,state,frame,direction); image=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0)); draw=ImageDraw.Draw(image); ramp=pigment.ramp(pigment.HAIR[max(0,min(7,colour))])
    name=HAIR_STYLES[max(0,min(5,style))]; x,y=pose.head; r=pose.head_r
    _poly(draw,[(x-r*.95,y-r*.12),(x-r*.78,y-r*.88),(x,y-r*1.22),(x+r*.78,y-r*.88),(x+r*.95,y-r*.12),(x+r*.58,y-r*.62),(x,y-r*.47),(x-r*.58,y-r*.62)],ramp[3])
    _line(draw,[(x-r*.62,y-r*.55),(x-.2,y-r*.98),(x+r*.48,y-r*.62)],ramp[5])
    if name=='crop':
        _poly(draw,[(x-r,y),(x-r+.4,y+2.6),(x-r-1,y+2.2)],ramp[2]); _poly(draw,[(x+r,y),(x+r-.4,y+2.6),(x+r+1,y+2.2)],ramp[2])
    elif name=='long':
        for s in (-1,1): _poly(draw,[(x+s*(r-.4),y-1),(x+s*(r+1.5),y+3),(x+s*(r+1),y+10),(x+s*(r-1.5),y+9),(x+s*(r-2),y+2)],ramp[3])
    elif name=='tail':
        s=-(pose.facing or -1); _poly(draw,[(x+s*(r-.5),y-1),(x+s*(r+2.5),y+1),(x+s*(r+3),y+7),(x+s*(r+.8),y+8),(x+s*(r-.3),y+2)],ramp[3])
    elif name=='braids':
        sides=(-1,1) if not pose.side else (-(pose.facing or 1),)
        for s in sides:
            for i in range(4): _disc(draw,(x+s*(r+.3),y+1.5+i*2.2),1.5-i*.12,ramp[3 if i%2==0 else 2])
    elif name=='curls':
        for deg in range(200,341,28):
            a=math.radians(deg); _disc(draw,(x+math.cos(a)*(r+.2),y+math.sin(a)*(r+.2)),2.0,ramp[3])
    else: _disc(draw,(x,y-r*1.35),2.45,ramp[3]); _line(draw,[(x-1.6,y-r*.9),(x+1.6,y-r*.9)],ramp[1],2)
    if pose.fade<1: image.putalpha(image.getchannel('A').point(lambda a:round(a*pose.fade)))
    return image

def _item_ramp(item):
    material=item.get('material',''); base={'cloth':'#6f6477','leather':'#75533d','wood':'#7c5d3c','copper':'#9a6748','bronze':'#9c784a','iron':'#777d80','steel':'#879196','silver':'#b6bdc1','mithril':'#90acb3','obsidian':'#504b5b','aetherium':'#8e93bd','metal':'#80868a'}.get(material,'#7a7064')
    return pigment.ramp(base)
def _trim(item):
    colors=('#967044','#a37a49','#6e94aa','#9479b1','#c1914b','#b8666e','#d2c878'); tier=int(item.get('tier',1)); return pigment.ramp(colors[min(len(colors)-1,max(0,tier//20))])

def _armor_torso(draw,pose,item):
    tone=_item_ramp(item); trim=_trim(item); chest,pelvis=pose.chest,pose.pelvis; ux,uy=_axis(pelvis,chest); px,py=-uy,ux
    w=pose.build.chest_depth+1 if pose.side else pose.build.shoulder+1.1; hw=pose.build.chest_depth+.8 if pose.side else pose.build.hip+1.4
    top=(chest[0]+ux*4.6,chest[1]+uy*4.6); bottom=(pelvis[0]-ux*1.3,pelvis[1]-uy*1.3)
    _poly(draw,[(top[0]-px*w*.78,top[1]-py*w*.78),(chest[0]-px*w,chest[1]-py*w),(bottom[0]-px*hw,bottom[1]-py*hw),(bottom[0]+px*hw,bottom[1]+py*hw),(chest[0]+px*w,chest[1]+py*w),(top[0]+px*w*.78,top[1]+py*w*.78)],tone[3])
    _line(draw,[(chest[0]-px*w*.75,chest[1]-py*w*.75),(chest[0]+px*w*.75,chest[1]+py*w*.75)],trim[4],2)
    if not pose.side: _line(draw,[(chest[0],chest[1]-2),(pelvis[0],pelvis[1]-2)],tone[1]); _line(draw,[(chest[0]-w*.62,chest[1]+3),(chest[0]+w*.62,chest[1]+3)],tone[5])

def _armor_helmet(draw,pose,item):
    tone=_item_ramp(item); trim=_trim(item); x,y=pose.head; r=pose.head_r; heavy='heavy' in item.get('tags',[])
    if heavy:
        _poly(draw,[(x-r-1,y+2.8),(x-r-.8,y-r*.6),(x,y-r*1.45),(x+r+.8,y-r*.6),(x+r+1,y+2.8),(x+r*.45,y+3.5),(x-r*.45,y+3.5)],tone[3])
        if not pose.back: draw.rectangle((round(x-r*.72),round(y-.8),round(x+r*.72),round(y+.6)),fill=DEEP); _line(draw,[(x,y-r*1.35),(x,y+3)],trim[4])
    else:
        _poly(draw,[(x-r-.6,y+.7),(x-r*.75,y-r),(x,y-r*1.35),(x+r*.75,y-r),(x+r+.6,y+.7),(x+r*.4,y-.2),(x-r*.4,y-.2)],tone[3]); _line(draw,[(x-r*.82,y-r*.2),(x+r*.82,y-r*.2)],trim[4])

def _armor_limb(draw,pose,item,slot):
    tone=_item_ramp(item); trim=_trim(item)
    if slot=='gloves':
        for key in ('far','near'):
            e,h=pose.elbow[key],pose.hand[key]; mid=(e[0]+(h[0]-e[0])*.55,e[1]+(h[1]-e[1])*.55); _segment(draw,mid,h,pose.build.limb*.92,pose.build.limb*.72,tone,key=='near'); _disc(draw,h,pose.build.limb*.47,tone[3 if key=='near' else 2])
    elif slot=='legs':
        for key in ('far','near'):
            hip,knee=pose.hip[key],pose.knee[key]; _segment(draw,hip,(knee[0],knee[1]+1),pose.build.thigh*1.12,pose.build.thigh*.88,tone,key=='near'); _line(draw,[(knee[0]-2,knee[1]),(knee[0]+2,knee[1])],trim[4])
    elif slot=='boots':
        for key in ('far','near'):
            knee,foot=pose.knee[key],pose.foot[key]; mid=(knee[0]+(foot[0]-knee[0])*.48,knee[1]+(foot[1]-knee[1])*.48); _segment(draw,mid,(foot[0],foot[1]-1.8),pose.build.thigh*.82,pose.build.thigh*.64,tone,key=='near'); _boot(draw,knee,foot,tone,pose.facing,key=='near')

def _weapon_kind(item):
    tags=set(item.get('tags',()))
    for kind in ('bow','staff','greataxe','axe','mace','dagger','spear','halberd','wand','crossbow','knuckles'):
        if kind in tags: return kind
    return 'sword'

def _weapon(draw,pose,item,offhand=False):
    tone=_item_ramp(item); trim=_trim(item); hand=pose.hand['far' if offhand else 'near']; angle=pose.guard_angle if offhand else pose.grip_angle
    ux,uy=math.cos(angle),math.sin(angle); px,py=-uy,ux; kind=_weapon_kind(item)
    if offhand or item.get('slot')=='offhand':
        center=(hand[0]+ux*1.6,hand[1]+uy*1.6); r=5.0; _poly(draw,[(center[0]-px*r,center[1]-py*r),(center[0]+ux*r*.7,center[1]+uy*r*.7),(center[0]+px*r,center[1]+py*r),(center[0]-ux*r*.75,center[1]-uy*r*.75)],tone[3]); _line(draw,[(center[0]-px*r*.65,center[1]-py*r*.65),(center[0]+px*r*.65,center[1]+py*r*.65)],trim[4]); return
    if kind=='bow':
        a=(hand[0]-uy*8,hand[1]+ux*8); b=(hand[0]+uy*8,hand[1]-ux*8); mid=(hand[0]+ux*2,hand[1]+uy*2); _line(draw,[a,(mid[0]+px*3,mid[1]+py*3),b],tone[3],2); _line(draw,[a,hand,b],trim[5]); return
    if kind in ('staff','wand'):
        length=15 if kind=='staff' else 9; base=(hand[0]-ux*4,hand[1]-uy*4); tip=(hand[0]+ux*length,hand[1]+uy*length); _line(draw,[base,tip],tone[2],3); _disc(draw,(tip[0]+ux*1.2,tip[1]+uy*1.2),2.2,trim[4]); return
    if kind in ('spear','halberd'):
        base=(hand[0]-ux*5,hand[1]-uy*5); tip=(hand[0]+ux*16,hand[1]+uy*16); _line(draw,[base,tip],tone[2],2); _poly(draw,[(tip[0]+ux*4,tip[1]+uy*4),(tip[0]+px*2,tip[1]+py*2),(tip[0]-px*2,tip[1]-py*2)],trim[4]); return
    grip_a=(hand[0]-ux*4,hand[1]-uy*4); grip_b=(hand[0]+ux*2.5,hand[1]+uy*2.5); _line(draw,[grip_a,grip_b],pigment.ramp('#4b3428')[2],2); _line(draw,[(hand[0]-px*3,hand[1]-py*3),(hand[0]+px*3,hand[1]+py*3)],trim[4],2); _disc(draw,(grip_a[0]-ux,grip_a[1]-uy),1.4,trim[3])
    if kind in ('axe','greataxe'):
        head=(hand[0]+ux*(10 if kind=='axe' else 13),hand[1]+uy*(10 if kind=='axe' else 13)); _line(draw,[grip_b,head],tone[2],2); span=4 if kind=='axe' else 6; _poly(draw,[(head[0]-px*1.3,head[1]-py*1.3),(head[0]+px*span+ux*2,head[1]+py*span+uy*2),(head[0]+px*(span-1)-ux*3,head[1]+py*(span-1)-uy*3),(head[0]-px*1.3-ux*2,head[1]-py*1.3-uy*2)],tone[4])
    elif kind=='mace':
        head=(hand[0]+ux*11,hand[1]+uy*11); _line(draw,[grip_b,head],tone[2],2); _disc(draw,head,3.2,tone[4]);
        for s in (-1,1): _line(draw,[head,(head[0]+px*s*4,head[1]+py*s*4)],tone[5])
    else:
        length=8 if kind=='dagger' else 13; tip=(hand[0]+ux*length,hand[1]+uy*length); _poly(draw,[(grip_b[0]-px*1.4,grip_b[1]-py*1.4),tip,(grip_b[0]+px*1.4,grip_b[1]+py*1.4)],tone[5]); _line(draw,[grip_b,tip],tone[3])

def _cloak(draw,pose,item):
    tone=_item_ramp(item); chest,pelvis=pose.chest,pose.pelvis; sway=math.sin(pose.frame/8*math.tau)*(1.6 if pose.state=='walk' else .5)
    if pose.side:
        back=-(pose.facing or 1); _poly(draw,[(chest[0]+back,chest[1]-3),(chest[0]+back*6,chest[1]),(pelvis[0]+back*(7+abs(sway)),pelvis[1]+11),(pelvis[0]+sway,pelvis[1]+12),(pelvis[0]-back*2,pelvis[1]+5)],tone[3])
    else: _poly(draw,[(chest[0]-pose.build.shoulder*.7,chest[1]-3),(chest[0],chest[1]-5),(chest[0]+pose.build.shoulder*.7,chest[1]-3),(pelvis[0]+pose.build.shoulder*1.1+sway,pelvis[1]+11),(pelvis[0]+sway,pelvis[1]+13),(pelvis[0]-pose.build.shoulder*1.1+sway,pelvis[1]+11)],tone[3])

def armour_frame(item,state,frame,direction):
    pose=rig.pose(0,state,frame,direction); image=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0)); draw=ImageDraw.Draw(image); slot=item.get('slot','')
    if slot=='helmet': _armor_helmet(draw,pose,item)
    elif slot=='chest': _armor_torso(draw,pose,item)
    elif slot in ('gloves','legs','boots'): _armor_limb(draw,pose,item,slot)
    elif slot=='belt':
        tone=_item_ramp(item); p=pose.pelvis; _line(draw,[(p[0]-pose.build.hip-2,p[1]-1),(p[0]+pose.build.hip+2,p[1]-1)],tone[3],3); _disc(draw,(p[0],p[1]-1),1.4,_trim(item)[4])
    elif slot=='cloak': _cloak(draw,pose,item)
    elif slot in ('ring','necklace','charm','trinket'):
        tone=_trim(item); anchor=pose.neck if slot=='necklace' else pose.hand['near'] if slot=='ring' else pose.pelvis; _disc(draw,(anchor[0],anchor[1]+(4 if slot=='necklace' else 0)),1.3,tone[4])
    elif slot=='weapon': _weapon(draw,pose,item,False)
    elif slot=='offhand': _weapon(draw,pose,item,True)
    if pose.fade<1: image.putalpha(image.getchannel('A').point(lambda a:round(a*pose.fade)))
    return image

ROLE_COLORS={'innkeeper':'#7e624b','blacksmith':'#5a5550','weaponsmith':'#5b6066','armorer':'#596169','alchemist':'#557265','trainer':'#665844','traveler':'#5c6754','guard':'#535f6a','scholar':'#545e78','scribe':'#5d6480','provisioner':'#756248','woodworker':'#755e40','carpenter':'#806647','tailor':'#73596e','tanner':'#704f39','herbalist':'#587446','rune_merchant':'#5f567c','enchanter':'#65568c','banker':'#4e5870','auctioneer':'#74577f'}
def npc_frame(role,state,frame,direction):
    build=pigment.keyed(role,2); skin=pigment.keyed(role+'skin',6); hair=pigment.keyed(role+'hair',6); colour=pigment.keyed(role+'hairc',8)
    image=body_frame(build,skin,state,frame,direction); image.alpha_composite(hair_frame(hair,colour,state,frame,direction)); pose=rig.pose(build,state,frame,direction); draw=ImageDraw.Draw(image); coat=pigment.ramp(ROLE_COLORS.get(role,'#676158'))
    chest,pelvis=pose.chest,pose.pelvis; ux,uy=_axis(pelvis,chest); px,py=-uy,ux; w=pose.build.chest_depth if pose.side else pose.build.shoulder*.78; hw=pose.build.chest_depth*.78 if pose.side else pose.build.hip*.95
    _poly(draw,[(chest[0]-px*w,chest[1]-py*w),(pelvis[0]-px*hw,pelvis[1]-py*hw),(pelvis[0]+px*hw,pelvis[1]+py*hw),(chest[0]+px*w,chest[1]+py*w)],coat[3]); _line(draw,[(chest[0]-px*w*.7,chest[1]-py*w*.7),(chest[0]+px*w*.7,chest[1]+py*w*.7)],coat[5])
    hand=pose.hand['near']
    if role in ('blacksmith','armorer'): _weapon(draw,pose,{'slot':'weapon','material':'steel','tags':['mace']},False)
    elif role in ('guard','trainer','weaponsmith'): _weapon(draw,pose,{'slot':'weapon','material':'steel','tags':['sword']},False)
    elif role in ('alchemist','herbalist'): _disc(draw,(hand[0],hand[1]-2),2.0,pigment.ramp('#6e9b72')[4]); _line(draw,[(hand[0],hand[1]-4),(hand[0],hand[1]-6)],coat[5])
    elif role in ('scholar','scribe','banker','auctioneer'): _poly(draw,[(hand[0]-3,hand[1]-3),(hand[0]+3,hand[1]-3),(hand[0]+3,hand[1]+2),(hand[0]-3,hand[1]+2)],pigment.ramp('#c2b68f')[3]); _line(draw,[(hand[0],hand[1]-2.5),(hand[0],hand[1]+1.5)],INK)
    if pose.fade<1: image.putalpha(image.getchannel('A').point(lambda a:round(a*pose.fade)))
    return image
