"""Wayfarer creature artwork, constructed directly from catalogue anatomy.

Anatomy proportions are data, not images. No legacy actor frame is read,
translated, rotated, recoloured or used as a fallback by this renderer.
Projection is applied to individual joints and anatomical contours before ink.
"""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, palette, shade, seed, INK, ELEMENT_COLORS
from .characters import body_frame, hair_frame, armour_frame, layer_order, SKINS
from .character_motion import rig, STATES
from .creature_anatomy import describe, FAMILIES

SUPPORTED=frozenset(FAMILIES)


class Brush:
    def __init__(self, size, direction, extent=38):
        self.image=canvas((size,size)); self.p=Pixel(self.image)
        self.size=size; self.direction=direction
        self.scale=(size/64)*min(1.28,45/max(32,extent))
    def at(self,x,y,z):
        if self.direction==2: u,v=x,y*.38
        elif self.direction==1: u,v=-x,-y*.38
        elif self.direction==0: u,v=y,x*.42
        else: u,v=-y,-x*.42
        return (self.size/2+u*self.scale,self.size*.86+(v-z)*self.scale)
    def poly(self,points,color,outline=INK):
        self.p.poly([self.at(*v) for v in points],color,outline)
    def line(self,points,color,width=1):
        self.p.line([self.at(*v) for v in points],color,max(1,round(width*self.scale)))
    def dot(self,point,color): self.p.dot(*self.at(*point),color)
    def ellipsoid(self,center,rx,ry,rz,base):
        x,y,z=center; c=palette(base)
        horizontal=rx if self.direction in (1,2) else ry
        depth=ry if self.direction in (1,2) else rx
        cx,cy=self.at(x,y,z)
        w=horizontal*self.scale; h=(rz+depth*.18)*self.scale
        self.p.poly([(cx-w,cy-h*.30),(cx-w*.70,cy-h*.82),(cx-w*.1,cy-h),
                     (cx+w*.64,cy-h*.84),(cx+w,cy-h*.26),(cx+w*.95,cy+h*.5),
                     (cx+w*.45,cy+h),(cx-w*.55,cy+h*.93),(cx-w,cy+h*.32)],c[1])
        self.p.poly([(cx-w*.77,cy-h*.35),(cx-w*.4,cy-h*.78),(cx+w*.37,cy-h*.78),
                     (cx+w*.78,cy-h*.14),(cx+w*.52,cy+h*.5),(cx-w*.40,cy+h*.6),(cx-w*.78,cy+h*.2)],c[3],None)
        self.p.line([(cx-w*.65,cy-h*.35),(cx-w*.35,cy-h*.62),(cx+w*.20,cy-h*.64)],c[4],max(1,round(self.scale)))
    def limb(self,a,b,width,base):
        ax,ay=self.at(*a); bx,by=self.at(*b); c=palette(base)
        dx,dy=bx-ax,by-ay; length=max(1,math.hypot(dx,dy)); nx,ny=-dy/length,dx/length
        w=width*self.scale/2; end=max(.7,w*.64)
        self.p.poly([(ax+nx*w,ay+ny*w),(bx+nx*end,by+ny*end),(bx-nx*end,by-ny*end),(ax-nx*w,ay-ny*w)],c[2])
        self.p.line([(ax-self.scale*.5,ay),(bx-self.scale*.5,by)],c[4],max(1,round(w*.6)))


def movement(state,f):
    cycle=f*math.tau/8
    drive=(0,-.7,-1.3,2.0,3.6,2.2,.7,0)[f] if state=='attack' else 0
    recoil=(0,-2.4,-3.5,-1.8,-.6,0,0,0)[f] if state=='hit' else 0
    collapse=(0,.10,.28,.52,.75,.93,1,1)[f] if state=='death' else 0
    charge=(0,.12,.45,.82,1,.68,.24,0)[f] if state=='cast' else 0
    walk=math.sin(cycle) if state=='walk' else 0
    breath=.45 if state=='idle' and f in (3,4) else 0
    return dict(phase=cycle,stride=walk,drive=drive+recoil,collapse=collapse,charge=charge,
                lift=(.8*abs(walk) if state=='walk' else breath),state=state,frame=f)


def _tail(b,s,m,rear,z):
    if s.tail in ('','none'):return
    length=s.tail_length; wag=math.sin(m['phase']-.6)*(1.7 if m['state']=='walk' else .35)
    if s.tail in ('stub','puff'): length=3.2
    if s.tail=='curl':
        pts=[(rear,0,z),(rear-3,0,z+2),(rear-5,0,z+1),(rear-4,0,z-1)]
        b.line(pts,s.coat,1.6);return
    pts=[(rear,0,z),(rear-length*.35,wag,z-1),(rear-length*.72,wag*1.2,z-3),(rear-length,wag*.7,max(1,z-2))]
    width=3.4 if s.tail in ('brush','tassel','puff') else 1.5
    for a,c in zip(pts,pts[1:]):b.limb(a,c,width,s.coat);width*=.77
    if s.tail=='brush':b.line(pts[-2:],s.belly or shade(s.coat,1.3),1.5)


def _horns(b,s,m,x,y,z):
    horn=s.horn
    if not horn:return
    tone='d9c9a0'
    if horn=='tusk':
        for side in (-1,1):b.line([(x+2,y+side*2,z-2),(x+4,y+side*3,z-1),(x+4,y+side*3,z+2)],tone,1.4)
    elif horn=='antler':
        for side in (-1,1):
            root=(x-1,y+side*2,z+2);tip=(x-4,y+side*5,z+11)
            b.line([root,(x-2,y+side*4,z+7),tip],tone,1.6)
            for k in (0,1):b.line([(x-2-k,y+side*(3+k),z+5+k*3),(x+1-k,y+side*(5+k),z+7+k*3)],tone)
    elif horn in ('curl','bull','ridge_horn'):
        for side in (-1,1):b.line([(x-1,y+side*2,z+2),(x-2,y+side*5,z+5),(x-4,y+side*6,z+7),(x-5,y+side*5,z+6)],tone,1.7)
    elif horn=='beak':
        b.poly([(x,y-2,z),(x+6,y,z-2),(x,y+2,z-1)],'cba34e')
    else:
        b.poly([(x-3,y-1,z+2),(x-4,y,z+8),(x,y+1,z+3)],s.accent or tone)


def _ears(b,s,x,y,z):
    if s.ear in ('','none'):return
    for side in (-1,1):
        yy=y+side*s.head*.6; height=s.ear_size
        if s.ear in ('tall','rabbit'):height*=1.6
        if s.ear=='drop':
            b.poly([(x-1,yy,z+2),(x+1,yy+side*2,z+2),(x,yy+side*3,z-3)],s.coat)
        elif s.ear=='round':
            b.ellipsoid((x-1,yy,z+2),height*.7,height*.6,height*.7,s.coat)
            b.dot((x,yy,z+2),'c29585')
        else:
            b.poly([(x-2,yy,z+1),(x-1,yy+side*1.2,z+2+height),(x+1,yy,z+2)],s.coat)
            b.line([(x-1,yy,z+2),(x-1,yy+side*.5,z+height)],shade(s.coat,1.35))


def _quadruped(b,s,m):
    dead=m['collapse']; stride=m['stride']; length=s.length
    rear=-length*.47; shoulder=length*.36
    ground=s.leg*(1-dead)+3*dead
    center=ground+s.girth*.36+m['lift']*(1-dead)+m['charge']*1.2
    drive=m['drive']; coat=s.coat
    def leg(front,side,far):
        x=shoulder if front else rear+2
        phase=m['phase']+(0 if front==(side>0) else math.pi)
        walk=math.sin(phase) if m['state']=='walk' else 0
        yy=side*s.girth*.62
        footx=x+walk*3.8+m['drive']*(.28 if front else -.2)
        footz=max(0,walk)*2.7
        hip=(x+drive,yy,ground)
        knee=(x+(1.6 if front else -2)+walk*1.6+drive*.6,yy,ground*.52)
        foot=(footx,yy,footz)
        if dead:
            knee=(knee[0]-dead*3,yy+side*dead*2,knee[2]*(1-dead)+dead*2)
            foot=(footx-dead*5,yy+side*dead*4,0)
        tone=shade(coat,.72) if far else coat
        b.limb(hip,knee,s.leg_width+1,tone);b.limb(knee,foot,s.leg_width,tone)
        b.ellipsoid((foot[0]+.7,foot[1],foot[2]+.6),1.6,1.2,.7,'403a34' if s.digit=='hoof' else tone)
    far_side=-1 if b.direction in (0,2) else 1
    for front in ((False,) if s.legs==2 and s.wings else (False,True)):leg(front,far_side,True)
    _tail(b,s,m,rear+drive,center+1)
    b.ellipsoid((drive-1,0,center),length*.50,s.girth*.73,s.girth*.83,coat)
    b.ellipsoid((shoulder+drive-1,0,center+1),s.girth*.85,s.girth*.75,s.girth*.9,coat)
    if s.belly:b.line([(rear+3+drive,0,center-s.girth*.55),(shoulder-2+drive,0,center-s.girth*.55)],s.belly,2)
    if s.back in ('shell','plates') or s.shell:
        b.ellipsoid((drive-2,0,center+2),length*.44,s.girth*.9,s.girth*.85,shade(coat,.9))
        for k in (-1,0,1):
            xx=drive-2+k*length*.2
            b.line([(xx,-s.girth*.6,center+3),(xx,0,center+s.girth*.78),(xx,s.girth*.6,center+3)],shade(coat,1.28))
        b.line([(rear+3+drive,0,center+s.girth*.72),(shoulder-2+drive,0,center+s.girth*.72)],shade(coat,.55))
    elif s.back in ('ridge','spikes') or s.mane:
        for k in range(5):
            xx=rear+3+drive+k*length*.16
            b.poly([(xx-1,0,center+s.girth*.7),(xx,0,center+s.girth*.7+2+s.mane),(xx+2,0,center+s.girth*.7)],shade(coat,.74))
    if s.pattern in ('stripes','bands','saddle','spots','patches','dapple','countershade'):
        tone=s.pattern_colour or shade(coat,.68)
        for k in range(4):
            xx=rear+length*(.22+k*.16)+drive
            if s.pattern in ('stripes','bands'):b.line([(xx,-s.girth*.52,center+2),(xx+1,-s.girth*.7,center-1)],tone,1.6)
            else:b.line([(xx,-s.girth*.68,center+1),(xx+2,-s.girth*.66,center+1)],tone,1.7)
    for front in ((False,) if s.legs==2 and s.wings else (False,True)):leg(front,-far_side,False)
    headx=shoulder+s.neck*.5+drive
    headz=center+s.neck*.42+2-m['charge']+dead*-4
    b.limb((shoulder+drive,0,center),(headx,0,headz),s.neck_width+2,coat)
    if b.direction!=3:_ears(b,s,headx,0,headz+s.head*.65)
    b.ellipsoid((headx,0,headz),s.head,s.head*.82,s.head*.84,coat)
    muzzlex=headx+s.head*.52
    b.ellipsoid((muzzlex+s.muzzle*.38,0,headz-s.muzzle_drop),s.muzzle*.7,s.head*.56,s.jaw*.70,s.belly or shade(coat,1.05))
    b.ellipsoid((muzzlex+s.muzzle*.91,0,headz-s.muzzle_drop+.3),.85,s.head*.38,.6,'302b30')
    eye_side=-1 if b.direction in (1,3) else 1
    for side in (-1,1):
        if b.direction in (1,2) and side!=eye_side:continue
        at=(headx+s.head*.4,side*s.head*.73,headz+s.head*.22)
        b.dot(at,'171a22' if dead>.8 else s.eye)
        if dead<.8:b.dot((at[0]-.6,at[1],at[2]+.8),'202027')
    if m['state']=='attack' and m['frame'] in (3,4):
        b.line([(muzzlex,eye_side*s.head*.55,headz-1),(muzzlex+s.muzzle*.7,eye_side*s.head*.45,headz-2)],'292330',1.8)
    if b.direction==3:_ears(b,s,headx,0,headz+s.head*.65)
    _horns(b,s,m,headx,0,headz+s.head*.5)
    if s.wings:_wings(b,s,m,(shoulder-4+drive,0,center+2),13)


def _wings(b,s,m,root,span):
    x,y,z=root; beat=math.sin(m['phase'])*4 if m['state'] in ('walk','attack') else m['charge']*4
    span*=1-m['collapse']*.7
    if m['state'] in ('idle','hit','death'): span*=.42; beat=-3
    for side in (-1,1):
        tip=(x-4,y+side*span,z+beat+2)
        wrist=(x+3,y+side*span*.6,z+beat+5)
        b.poly([(x,y+side*2,z),wrist,tip,(x-9,y+side*span*.55,z-4),(x-4,y+side*2,z-3)],s.accent or shade(s.coat,.72))
        b.line([(x,y+side*2,z),wrist,tip],shade(s.coat,1.25),1.6)
        for k in range(1,4):
            yy=y+side*span*k/4
            b.line([wrist,(x-8,yy,z-3)],shade(s.coat,.60))


def _bird(b,s,m):
    dead=m['collapse']; lift=m['lift']+m['charge']*2
    z=s.leg+s.girth*(1-dead)*.7+lift
    x=m['drive']
    for side in (-1,1):
        step=math.sin(m['phase']+(0 if side<0 else math.pi))*2.5 if m['state']=='walk' else 0
        hip=(x,side*2.4,z-1);knee=(x-1,side*2.5,(z-1)*.55);foot=(x+step-4*dead,side*3,0)
        b.limb(hip,knee,1.7,'b3a17c');b.limb(knee,foot,1.3,'b3a17c')
        for toe in (-1,0,1):b.line([foot,(foot[0]+2,foot[1]+toe*1.5,0)],'b8a983')
    b.ellipsoid((x-2,0,z),s.length*.42,s.girth*.7,s.girth*(1-dead*.65),s.coat)
    _wings(b,s,m,(x-1,0,z+2),10 if s.family_key!='heron' else 13)
    neck=(x+3,0,z+s.neck*(1-dead)*.7)
    b.limb((x+1,0,z+1),neck,max(2,s.neck_width*.65),s.coat)
    head=(neck[0]+1,0,neck[2]+s.head*.6)
    b.ellipsoid(head,s.head,s.head*.87,s.head,s.coat)
    hx,hy,hz=head
    b.poly([(hx+2,-1,hz),(hx+2+s.muzzle,0,hz-1),(hx+2,1,hz-2)],'c4a86a')
    for side in (-1,1):b.dot((hx+1,side*s.head*.8,hz+.5),s.eye if dead<.8 else '3c3540')
    _ears(b,s,hx,0,hz+1)
    b.poly([(x-6,-2,z),(x-13,-4,z-2),(x-15,0,z-3),(x-13,4,z-2),(x-6,2,z)],s.accent or shade(s.coat,.7))


def _many_legs(b,s,m,count):
    z=s.girth+4*(1-m['collapse']); span=s.girth*1.4
    for side in (-1,1):
        for k in range(count//2):
            along=(k-(count/2-1)/2)*3.3
            wave=math.sin(m['phase']+k*.9+side*1.5)*(2 if m['state']=='walk' else .45*m['charge'])
            root=(along,side*s.girth*.45,z)
            knee=(along+wave,side*(span+2),z-1)
            foot=(along+wave-3,side*(span+5-m['collapse']*3),.5+max(0,wave))
            if m['collapse']>.5:knee=(along-2,side*(span-3),3);foot=(along-4,side*(span-4),2)
            b.limb(root,knee,1.6,s.coat);b.limb(knee,foot,1.2,s.coat)
    b.ellipsoid((-3+m['drive'],0,z),s.length*.36,s.girth,s.girth*.65,s.coat)
    if s.shell:
        shell=s.accent or 'b49476';sx=-5+m['drive']*.35;sz=z+3-m['collapse']*2
        b.ellipsoid((sx,0,sz),6.5,6,6,shell)
        for side in (-1,1):
            points=[]
            for k in range(11):
                a=k*math.pi/3;r=max(.5,4-k*.30)
                points.append((sx+math.cos(a)*r,side*5.5,sz+math.sin(a)*r))
            b.line(points,shade(shell,.65),1.1)
    b.ellipsoid((s.length*.27+m['drive'],0,z),s.head+1,s.head,s.head*.7,s.accent or shade(s.coat,.8))
    hx=s.length*.27+m['drive']
    for side in (-1,1):
        b.dot((hx+2,side*s.head*.7,z+1),'d8c064' if m['collapse']<.8 else '34313a')
        b.line([(hx+2,side*2,z),(hx+4,side*4,z-1),(hx+5,side*2,z-2)],'a2947c',1.4)
    if s.archetype=='crustacean':
        for side in (-1,1):
            end=(hx+7+m['drive']+m['charge']*1.5,side*(8+m['charge']*2),z+2+m['charge']*4)
            b.limb((hx,side*3,z),end,2.7,s.coat)
            b.poly([end,(end[0]+4,end[1]-2,end[2]+1),(end[0]+5,end[1],end[2]),(end[0]+3,end[1]+3,end[2]-2)],s.coat)
    elif s.archetype=='arachnid':
        for side in (-1,1):b.line([(hx+1,side,z),(hx+3,side*2,z-3)],'ded3af',1.3)
    else:
        b.line([(-7,0,z+s.girth*.55),(2,0,z+s.girth*.55)],shade(s.coat,.5))
        for side in (-1,1):b.line([(hx,side*2,z+2),(hx+4,side*4,z+7)],s.accent or s.coat,1.2)
    if s.wings:_wings(b,s,m,(0,0,z+2),14 if s.wings=='moth' else 11)


def _serpent(b,s,m):
    count=max(7,s.segments); dead=m['collapse']; points=[]
    for k in range(count+1):
        t=k/count; phase=m['phase']*(1 if m['state']=='walk' else .15)
        x=(t-.5)*s.length+m['drive']*t
        y=math.sin(t*math.tau+phase)*s.girth*(1-dead*.6)
        z=s.girth*.65+(t**3)*s.height*(1-dead)*.65+m['charge']*t*3
        points.append((x,y,z))
    for k,(a,c) in enumerate(zip(points,points[1:])):
        width=max(1,s.girth*1.7*(.25+.75*k/count))
        b.limb(a,c,width,s.coat)
        if s.segments or s.pattern=='bands':b.line([(c[0],c[1]-1,c[2]+width*.3),(c[0],c[1]+1,c[2]+width*.3)],s.accent or shade(s.coat,.65))
        if s.legs>4:
            for side in (-1,1):b.line([c,(c[0]-1,c[1]+side*4,max(0,c[2]-2))],s.accent or s.coat)
    x,y,z=points[-1]
    b.ellipsoid((x+1,y,z),s.head,s.head*.8,s.head*.6,s.coat)
    for side in (-1,1):b.dot((x+2,y+side*s.head*.65,z+1),s.eye if dead<.8 else '34313a')
    if s.shell:
        b.ellipsoid((0,0,7),7,6,7,s.accent or 'a78d6a')
        for k in range(8):
            a=k*math.pi/3
            b.dot((math.cos(a)*(4-k*.3),-5,7+math.sin(a)*(4-k*.3)),shade(s.coat,.6))
    if m['state']=='attack' and m['frame']==4:b.line([(x+3,y,z),(x+6,y,z-1),(x+7,y+1,z-1)],'b6606d')


def _spirit(b,s,m):
    phase=m['phase']; dead=m['collapse']; x=m['drive']; z=s.height*(1-dead*.72)+3
    tone=s.glow or s.coat
    for k in range(5):
        angle=k*math.tau/5
        root=(x+math.cos(angle)*s.girth*.6,math.sin(angle)*s.girth*.6,z-3)
        reach=5+(2*math.sin(phase+k) if m['state']=='walk' else 3*m['charge'])
        tip=(x+math.cos(angle)*(s.girth+reach),math.sin(angle)*(s.girth+reach),max(1,z-12+math.sin(phase+k)*2))
        mid=((root[0]+tip[0])*.5,(root[1]+tip[1])*.5,z-7)
        b.limb(root,mid,3.6,tone);b.limb(mid,tip,1.8,tone)
    b.ellipsoid((x,0,z),s.girth*.75,s.girth*.65,s.girth*(1-dead*.5),s.coat)
    for side in (-1,1):b.dot((x+2,side*s.girth*.5,z+1),'f0edc2' if dead<.8 else shade(tone,1.2))
    if s.archetype=='elemental':
        for k in range(5):
            xx=x+(k-2)*2
            b.poly([(xx,-2,z+2),(xx+math.sin(phase+k)*2,-1,z+8+2*math.sin(k)),(xx+2,1,z+2)],tone)


def _construct(b,s,m):
    dead=m['collapse']; z=s.height*(1-dead*.6); x=m['drive']; span=s.girth*.7
    for side in (-1,1):
        step=math.sin(m['phase']+(0 if side<0 else math.pi))*3 if m['state']=='walk' else 0
        hip=(x,side*span,z*.55); knee=(x+step*.5,side*span,z*.25); foot=(step-4*dead,side*(span+dead*3),0)
        b.limb(hip,knee,4.5,s.coat);b.limb(knee,foot,3.6,s.coat)
        b.ellipsoid((foot[0]+1,foot[1],1),3,2.4,1.5,shade(s.coat,.9))
    b.ellipsoid((x,0,z*.72),s.girth*.65,s.girth*.86,s.girth*.76,s.coat)
    for side in (-1,1):
        shoulder=(x,side*(span+2),z*.9)
        elbow=(x+2+m['drive']*.5,side*(span+4),z*.6+m['charge']*4)
        hand=(x+4+m['drive'],side*(span+3),z*.38+m['charge']*7)
        b.limb(shoulder,elbow,5.2,s.coat);b.limb(elbow,hand,4.4,s.coat)
        b.ellipsoid(hand,2.6,2.6,2.6,shade(s.coat,.85))
    b.ellipsoid((x,0,z+2),4.3,3.7,4.6,s.coat)
    for side in (-1,1):b.dot((x+3,side*2,z+2),s.glow or 'd6bd6d')
    b.line([(x+3,-2,z*.78),(x+4,0,z*.65),(x+3,2,z*.78)],s.accent or 'b6a16e',1.7)
    if s.wings:_wings(b,s,m,(x-1,0,z*.83),12)


def _mineral(b,s,m):
    dead=m['collapse']; charge=m['charge']; phase=m['phase'];tone=s.accent or s.coat
    shift=m['drive']
    lift=abs(math.sin(phase))*2.5 if m['state']=='walk' else 0
    for k in range(5):
        angle=k*math.tau/5; height=(8+(k%3)*4)*(1-dead*.8)+charge*3+lift*(.65 if k%2 else 1)
        x=shift+math.cos(angle)*(5+math.sin(phase+k)*m['stride']*2); y=math.sin(angle)*5+math.cos(phase+k)*m['stride']*2
        b.poly([(x-3,y-2,2),(x+3,y-2,2),(x+2,y+2,3),(x,y,height),(x-2,y+2,3)],tone)
        b.line([(x-2,y-1,3),(x,y,height-1)],shade(tone,1.3))
    b.poly([(-4,-3,3),(5,-3,3),(4,4,3),(shift*.45,0,18*(1-dead*.7)+charge*3+lift),(-4,3,3)],s.coat)
    b.line([(0,-3,4),(shift*.45,0,17*(1-dead*.7)+charge*3+lift)],s.glow or shade(tone,1.4),1.5)


def _plant(b,s,m):
    dead=m['collapse']; z=s.height*(1-dead*.8)+m['charge']*3; x=m['drive']+m['charge']*2; phase=m['phase']
    for side in (-1,1):
        wave=math.sin(phase+side)*3 if m['state']=='walk' else 0
        b.limb((x,side*3,z*.6),(x-2+wave,side*7,0),3.5,s.coat)
        b.limb((x,side*2,z*.75),(x+wave,side*8,z*.55+m['charge']*5),2.6,s.coat)
    b.limb((x,0,3),(x,0,z),s.girth+1,s.coat)
    if s.family_key in ('myconid','fungus') or 'mushroom' in s.family_key:
        b.ellipsoid((x,0,z+1),9+m['charge']*2,8+m['charge']*2,4+m['charge'],s.accent or 'ab655b')
        for k in range(4):b.dot((x+(k-2)*2,-4,z+3+(k%2)), 'd0b58a')
    else:
        for k in range(7):
            angle=k*math.tau/7; reach=7+m['charge']*3; yy=math.sin(angle)*reach;xx=x+math.cos(angle)*reach
            b.limb((x,0,z*.7),(xx,yy,z+1),1.5,s.coat)
            b.poly([(xx-3,yy,z),(xx,yy+2,z+7),(xx+4,yy,z+1),(xx,yy-2,z-2)],s.accent or '628348')
    if m['charge']:
        for side in (-1,1):
            shoulder=(x,side*2,z*.68)
            elbow=(x+3,side*(5+m['charge']*3),z*.65+m['charge']*4)
            hand=(x+6,side*(7+m['charge']*3),z*.62+m['charge']*7)
            b.limb(shoulder,elbow,2.7,s.coat);b.limb(elbow,hand,1.8,s.coat)
            b.poly([hand,(hand[0]+2,hand[1]+side*2,hand[2]+3),(hand[0]-1,hand[1]+side*3,hand[2]+1)],s.accent or '628348')
    for side in (-1,1):b.dot((x+3,side*2,z*.7),s.eye)


def _mimic(b,s,m):
    gape=abs(m['drive']*.9)+m['charge']*3;dead=m['collapse']
    w=8; h=8*(1-dead*.65)
    b.poly([(-w,-6,1),(w,-6,1),(w,-6,h),(-w,-6,h)],s.coat)
    b.poly([(w,-6,1),(w,6,1),(w,6,h),(w,-6,h)],shade(s.coat,.75))
    b.poly([(-w,-6,h+gape),(-w,6,h+gape),(w,6,h+gape),(w,-6,h+gape)],shade(s.coat,1.2))
    for xx in (-5,5):b.line([(xx,-6,1),(xx,-6,h),(xx,6,h)],'c8a360',2)
    for xx in (-6,-2,2,6):
        b.poly([(xx,-6,h),(xx+2,-6,h),(xx+1,-6,h-2)],'e9d8b1')
    for side in (-1,1):
        wave=math.sin(m['phase']+side)*2 if m['state']=='walk' else 0
        b.limb((0,side*5,4),(wave,side*10,0),2.5,'926772')
    if gape>0:b.line([(0,-6,h),(m['drive'],-10,2)],'bb6f80',2)


def _humanoid(definition,s,state,n,d):
    """Humanoid mobs use the same new joint construction, with species anatomy."""
    family=definition['family']; identity=seed(definition['id']);skin=identity%6
    im=body_frame(identity%2,skin,state,n,d);j=rig(state,n,d,identity%2);p=Pixel(im)
    if family in ('goblin','kobold','ogre','ghoul','skeleton','revenant'):
        # Remap only the known skin ramp, not an old source image.
        old=palette(SKINS[skin]);new=palette(s.coat);lut=dict(zip(old,new))
        im.putdata([lut.get(pixel,pixel) for pixel in im.getdata()]);p=Pixel(im)
    items=[{'id':'mob_legs','slot':'legs','tags':['medium'],'_color':s.accent or '56505f'},
           {'id':'mob_chest','slot':'chest','tags':['heavy'] if family in ('knight','revenant') else ['medium'],'_color':s.coat},
           {'id':'mob_belt','slot':'belt','tags':['medium'],'_color':'916e48'}]
    kind='axe' if family in ('ogre','goblin') else 'spear' if family=='scarecrow' else 'sword'
    items.append({'id':'mob_'+kind,'slot':'weapon','tags':[kind],'material':'iron'})
    layers={'body':im,'hair':hair_frame(identity%6,(identity//7)%8,state,n,d)}
    layers.update({i['slot']:armour_frame(i,state,n,d) for i in items})
    out=canvas()
    for slot in layer_order(d):
        if slot in layers:out.alpha_composite(layers[slot])
    p=Pixel(out);x,y=j['head']
    if family in ('goblin','kobold'):
        for side in (-1,1):p.poly([(x+side*4,y-1),(x+side*10,y-4),(x+side*5,y+3)],s.coat)
    elif family=='skeleton':
        p.poly([(x-4,y-4),(x+3,y-4),(x+5,y),(x+2,y+5),(x-2,y+5),(x-5,y)],'d7cfac')
        for dx in (-2,2):p.rect((x+dx-1,y-1,x+dx,y+1),'3a3540')
        p.line([(x-2,y+3),(x+2,y+3)],'625b50')
    elif family=='pirate':
        # Tricorn, bandanna and eyepatch; not a colour-only human silhouette.
        if j['collapse']>.6:
            p.poly([(x-8,y-1),(x-5,y-4),(x+4,y-3),(x+8,y),(x+6,y+1),(x-7,y+1)],'393c48')
        else:
            p.poly([(x-8,y-3),(x-6,y-8),(x,y-7),(x+6,y-8),(x+8,y-3),(x+3,y-4),(x,y-2),(x-3,y-4)],'393c48')
            p.line([(x-6,y-6),(x-2,y-5),(x+2,y-5),(x+6,y-6)],'b79c68')
        if not j['back']:
            p.line([(x-5,y-2),(x+5,y-2)],'883e42',2);p.rect((x+1,y-1,x+3,y+1),'252632')
    elif family=='ghoul':
        for hand in ('hand_l','hand_r'):
            hx,hy=j[hand]
            for claw in (-1,1):p.line([(hx+claw,hy+1),(hx+claw*2,hy+4)],'c9cfb0')
    if definition.get('boss'):
        # Boss ink is rebuilt on a larger canvas; scale the joint-authored pixel grid uniformly.
        return out.resize((128,128),Image.Resampling.NEAREST)
    return out



def _amphibian(b,s,m):
    dead=m['collapse'];x=m['drive'];z=4+s.girth*.45*(1-dead)+m['charge']*2
    for side in (-1,1):
        kick=math.sin(m['phase']+(0 if side<0 else math.pi))*3 if m['state']=='walk' else 0
        b.limb((x-3,side*3,z),(x-7+kick,side*6,3),4,s.coat)
        b.limb((x-7+kick,side*6,3),(x-2,side*8,0),2.3,s.coat)
        b.limb((x+3,side*3,z),(x+6+kick*.4,side*5,0),2,s.coat)
        for toe in (-1,0,1):b.line([(x+6,side*5,0),(x+8,side*(5+toe),0)],shade(s.coat,1.2))
    b.ellipsoid((x-1,0,z),s.length*.43,s.girth*.95,s.girth*.62,s.coat)
    b.ellipsoid((x+4,0,z+1),s.head+2,s.head+1,s.head*.7,s.coat)
    for side in (-1,1):
        b.ellipsoid((x+4,side*3,z+4),1.6,1.5,1.5,shade(s.coat,1.25))
        b.dot((x+5,side*3,z+4),s.eye if dead<.8 else '464138')
    b.line([(x+6,-3,z),(x+8,0,z-1),(x+6,3,z)],shade(s.coat,.6))
    if m['state']=='attack' and m['frame'] in (3,4):b.line([(x+8,0,z),(x+13,0,z-1)],'c48283',1.4)


def _aquatic(b,s,m):
    dead=m['collapse'];x=m['drive'];wave=math.sin(m['phase'])*(3 if m['state']=='walk' else .5)
    z=5+s.girth*(1-dead)*.55+m['charge']*2
    b.ellipsoid((x,0,z),s.length*.45,s.girth*.58,s.girth*.8,s.coat)
    rear=x-s.length*.4
    b.poly([(rear,0,z),(rear-7,wave,z+6*(1-dead)),(rear-5,wave,z),(rear-7,wave,z-5*(1-dead))],s.accent or shade(s.coat,.8))
    b.poly([(x-3,0,z+s.girth*.6),(x,0,z+s.girth+5),(x+4,0,z+s.girth*.6)],s.accent or shade(s.coat,1.2))
    for side in (-1,1):
        b.poly([(x+2,side*2,z),(x-2,side*(7+m['charge']),z-3),(x+4,side*3,z-1)],s.accent or shade(s.coat,.8))
        b.dot((x+s.length*.30,side*s.girth*.5,z+1),s.eye if dead<.8 else '35353a')
    b.line([(x+s.length*.22,-s.girth*.45,z+2),(x+s.length*.22,-s.girth*.5,z-2)],shade(s.coat,.6))



def _snail(b,s,m):
    """A muscular foot, retractile eyestalks and a carried shell, not a static shell icon."""
    dead=m['collapse'];charge=m['charge'];phase=m['phase']
    glide=math.sin(phase) if m['state']=='walk' else 0
    drive=m['drive'];body=s.coat;shell=s.accent or 'a78d6a'
    # The front of the foot rolls into contact as the rear releases it.
    foot=[(-10,-3,0),(-8,-4,1),(2,-4,1),(8+drive,-2,1),(10+drive,0,1),
          (8+drive,2,1),(2,4,1),(-8,4,1)]
    b.poly([(x,y+(glide*.7 if x<0 else -glide*.7),z) for x,y,z in foot],body)
    b.line([(-8,-3,1),(0,-3,1),(8+drive,-1,1)],shade(body,1.3),1.5)
    shell_z=8+abs(glide)*1.1-dead*1.7
    shell_y=glide*.9
    b.ellipsoid((-2+drive*.18,shell_y,shell_z),7,6,7*(1-dead*.1),shell)
    # A spiral on each visible shell side follows the shell, preserving material identity.
    for side in (-1,1):
        points=[]
        for k in range(13):
            a=k*math.pi/3;radius=max(.5,4.8-k*.32)
            points.append((-2+drive*.18+math.cos(a)*radius,shell_y+side*5.6,shell_z+math.sin(a)*radius))
        b.line(points,shade(shell,.62),1.1)
    rise=(1-dead)*(2+charge*3+max(0,-drive)*.4)
    neck=(7+drive,0,4+rise+glide*.8)
    b.limb((3+drive*.3,0,2),neck,4.4,body)
    b.ellipsoid(neck,3.2,3.0,2.6,body)
    for side in (-1,1):
        root=(neck[0]+1,side*1.3,neck[2]+1)
        tip=(neck[0]+2-charge*2+glide,side*(3.5+charge*2),neck[2]+5*(1-dead)+charge*2)
        b.limb(root,tip,1.5,body)
        b.ellipsoid(tip,1.2,1.1,1.1,shade(body,1.3))
        b.dot((tip[0]+.5,tip[1],tip[2]+.4),s.eye if dead<.8 else '51473b')
        b.line([(neck[0]+1,side,neck[2]-1),(neck[0]+3,side*3,neck[2]-2)],shade(body,.8))
    if m['state']=='attack' and m['frame'] in (3,4):
        b.line([(neck[0]+2,-1,neck[2]-1),(neck[0]+4,0,neck[2]-2),(neck[0]+2,1,neck[2]-1)],'b88d82',2)



def _manta(b,s,m):
    """A broad diamond disk with undulating pectoral fins and a single whip tail."""
    dead=m['collapse'];drive=m['drive'];charge=m['charge'];phase=m['phase']
    beat=(math.sin(phase)*3 if m['state']=='walk' else charge*3)+drive*.3
    z=5*(1-dead)+1;span=12+charge*2-dead*2;x=drive
    tone=s.coat
    for side in (-1,1):
        b.poly([(x+6,side*1,z),(x+1,side*span,z+beat*(1-dead)),(x-8,side*5,z-1),(x-6,0,z)],tone)
        b.line([(x+5,side*2,z+.5),(x+1,side*(span-1),z+beat*(1-dead)),(x-7,side*5,z-.5)],shade(tone,1.25))
        b.poly([(x+4,side*2,z+.7),(x+1,side*7,z+beat*.5),(x-5,side*4,z)],shade(tone,1.1),None)
    b.ellipsoid((x,0,z),7,3.4,1.6,tone)
    tail=[(x-6,0,z),(x-11,math.sin(phase)*1.1,z-1),(x-16,math.sin(phase-.7)*2,z-1),(x-19,math.sin(phase-1)*2.5,z)]
    b.line(tail,shade(tone,.65),1.5)
    for side in (-1,1):
        b.line([(x+5,side*2,z),(x+8,side*3,z),(x+9,side*2,z+.5)],shade(tone,1.15),1.8)
        b.dot((x+4,side*3,z+1),s.eye if dead<.8 else '343440')
        for k in range(3):b.dot((x-k*2,side*(4+k),z+.7+beat*.15),s.accent or shade(tone,1.35))
    b.line([(x+6,-1,z-.5),(x+7,0,z-1),(x+6,1,z-.5)],shade(tone,.55))


def _cuttle(b,s,m):
    """Tapered mantle, rippling fin skirt, eight arms and two feeding tentacles."""
    dead=m['collapse'];phase=m['phase'];drive=m['drive'];charge=m['charge'];x=drive
    z=4+2*(1-dead)+charge*2
    wave=math.sin(phase)*1.7 if m['state']=='walk' else drive*.25
    for side in (-1,1):
        rim=[(x-9,0,z),(x-6,side*4,z+wave),(x-2,side*6,z-wave),(x+3,side*5,z+wave),(x+6,side*3,z)]
        b.poly(rim,s.accent or shade(s.coat,1.2))
        b.line(rim,shade(s.coat,1.3))
    b.ellipsoid((x-2,0,z),8,4.2,3.7*(1-dead*.5),s.coat)
    for k in range(4):b.line([(x-6+k*2,-2,z+2),(x-5+k*2,2,z+2)],s.accent or shade(s.coat,.72))
    b.ellipsoid((x+5,0,z),3.4,3.6,2.7,s.coat)
    for side in (-1,1):b.dot((x+5,side*3.2,z+1),s.eye if dead<.8 else '36363a')
    for arm in range(8):
        spread=(arm-3.5)*1.65*(1-dead*.5)
        ripple=math.sin(phase+arm*.7)*(1.3 if m['state']=='walk' else .4)+charge*1.2
        root=(x+7,(arm-3.5)*.65,z-1)
        mid=(x+10+ripple,spread,z-1+charge)
        tip=(x+12+math.cos(arm)*1.2+drive*.4,spread*.9,1+charge*2)
        b.limb(root,mid,1.6,s.coat);b.limb(mid,tip,1.1,s.accent or shade(s.coat,1.2))
    extension=2+(max(0,drive)*1.4 if m['state']=='attack' else charge*3)
    for side in (-1,1):
        root=(x+7,side*1.2,z)
        # A horizontal feeding strike stays above the south-facing cell boundary.
        tip=(min(23,x+12+extension),side*2,5+charge*2)
        b.line([root,(x+11,side*3,z-1),tip],shade(s.coat,1.12),1.4)
        b.ellipsoid(tip,1.6,1,.7,s.accent or s.coat)


def _scorpion(b,s,m):
    """Eight walking legs, paired pincers and an articulated stinging metasoma."""
    _many_legs(b,s,m,8)
    dead=m['collapse'];phase=m['phase'];charge=m['charge'];drive=m['drive']
    z=s.girth+4*(1-dead)
    wag=math.sin(phase)*1.2 if m['state']=='walk' else 0
    bend=drive*.65+charge*2
    points=[(-8+drive*.3,0,z),(-12,0,z+2*(1-dead)),(-13,0,z+7*(1-dead)),
            (-10+bend,wag,z+12*(1-dead)+charge),(-5+bend,wag,z+14*(1-dead)+charge),
            (-2+max(0,drive),wag,z+10*(1-dead)+charge)]
    for index,(a,c) in enumerate(zip(points,points[1:])):
        b.limb(a,c,3.1-index*.32,s.coat)
        b.ellipsoid(c,1.5,1.3,1.2,shade(s.coat,1.12))
    tip=points[-1]
    b.poly([tip,(tip[0]+3,tip[1],tip[2]-3),(tip[0]+1,tip[1]+1,tip[2]-1)],s.accent or 'd1ae75')


def frame(definition,state,number,direction):
    if state not in STATES or number not in range(8) or direction not in range(4):raise ValueError('Invalid creature pose')
    family=definition.get('family','')
    if family not in FAMILIES:raise ValueError('Unmapped creature anatomy: '+family)
    s=describe(definition);m=movement(state,number)
    if s.archetype=='humanoid':return _humanoid(definition,s,state,number,direction)
    size=128 if definition.get('boss') else 64
    extent=max(s.length+s.tail_length+s.head+s.muzzle+8,s.height+s.leg+s.head+14,s.girth*4+16)
    b=Brush(size,direction,extent)
    if s.archetype in ('quadruped','primate','drake'):_quadruped(b,s,m)
    elif s.archetype=='amphibian':_amphibian(b,s,m)
    elif s.archetype=='bird':_bird(b,s,m)
    elif s.family_key=='scorpion':_scorpion(b,s,m)
    elif s.archetype in ('arachnid','insect','crustacean'):_many_legs(b,s,m,4 if s.shell else 8 if s.archetype in ('arachnid','crustacean') else 6)
    elif s.archetype in ('serpent','worm'):
        if s.shell:_snail(b,s,m)
        else:_serpent(b,s,m)
    elif s.archetype=='aquatic':
        if s.family_key=='manta':_manta(b,s,m)
        elif s.family_key=='cuttle':_cuttle(b,s,m)
        else:_aquatic(b,s,m)
    elif s.archetype in ('spirit','elemental'):_spirit(b,s,m)
    elif s.archetype=='construct':_construct(b,s,m)
    elif s.archetype=='mineral':_mineral(b,s,m)
    elif s.archetype=='plant':_plant(b,s,m)
    elif s.archetype=='mimic':_mimic(b,s,m)
    else:raise ValueError('Unimplemented creature archetype: '+s.archetype)
    return b.image
