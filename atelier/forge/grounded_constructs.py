"""Grounded-2026 construct/mineral gait renderer.

Heavy artificial creatures are rebuilt from joints each frame: planted feet,
flexing knees, weight transfer, counter-swinging arms, cast lift, hit recoil and
a staged collapse. No source bitmap is moved, rotated, stretched or sampled.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw
from . import pigment

INK=(21,21,25,255)
FRAMES=8


def _pt(p): return int(round(p[0])),int(round(p[1]))
def _axis(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; n=math.hypot(dx,dy) or 1.0
    return dx/n,dy/n
def _normal(a,b):
    ux,uy=_axis(a,b); return -uy,ux
def _quad(a,b,wa,wb):
    px,py=_normal(a,b)
    return [(a[0]+px*wa/2,a[1]+py*wa/2),(b[0]+px*wb/2,b[1]+py*wb/2),
            (b[0]-px*wb/2,b[1]-py*wb/2),(a[0]-px*wa/2,a[1]-py*wa/2)]


class Stage:
    def __init__(self,size):
        self.size=size; self.scale=size/64; self.cx=size/2-.5; self.ground=size*.86
        self.image=Image.new('RGBA',(size,size),(0,0,0,0)); self.draw=ImageDraw.Draw(self.image)
    def at(self,x,y): return self.cx+x*self.scale,self.ground-y*self.scale
    def poly(self,points,fill,outline=INK):
        pts=[_pt(self.at(x,y)) for x,y in points]; self.draw.polygon(pts,fill=fill)
        if outline:self.draw.line(pts+[pts[0]],fill=outline,width=max(1,round(self.scale)))
    def segment(self,a,b,wa,wb,fill):
        self.draw.polygon([_pt(p) for p in _quad(self.at(*a),self.at(*b),wa*self.scale,wb*self.scale)],fill=fill)
        pts=[_pt(p) for p in _quad(self.at(*a),self.at(*b),wa*self.scale,wb*self.scale)]
        self.draw.line(pts+[pts[0]],fill=INK,width=max(1,round(self.scale)))
    def disc(self,p,r,fill,outline=INK):
        x,y=self.at(*p); rr=r*self.scale
        self.draw.ellipse((round(x-rr),round(y-rr),round(x+rr),round(y+rr)),fill=fill,outline=outline,width=max(1,round(self.scale)))
    def line(self,points,fill,width=1): self.draw.line([_pt(self.at(x,y)) for x,y in points],fill=fill,width=max(1,round(width*self.scale)))


def _motion(state,frame):
    t=frame/(FRAMES-1); phase=frame/FRAMES*math.tau
    result={'phase':phase,'stride':0.0,'bob':0.0,'lunge':0.0,'charge':0.0,'recoil':0.0,'collapse':0.0,'fade':1.0,'flash':0.0}
    if state=='idle': result['bob']=math.sin(phase)*.32
    elif state=='walk':
        result['stride']=1.0; result['bob']=abs(math.cos(phase))*.55-.25
    elif state=='attack':
        result['lunge']=math.sin(min(1,t*1.35)*math.pi)*4.0
    elif state=='cast':
        result['charge']=math.sin(t*math.pi)**.72
    elif state=='hit':
        result['recoil']=math.sin(min(1,t*1.9)*math.pi)**.7*3.0
        result['flash']=.58 if frame==0 else .36 if frame==1 else .15 if frame==2 else 0
    elif state=='death':
        result['collapse']=min(1,(t*1.22)**.85); result['fade']=1 if frame<6 else .85 if frame==6 else .68
    return result


def _gait(m,offset):
    if not m['stride']: return 0.0,0.0
    angle=m['phase']+offset*math.tau
    return math.cos(angle)*3.4,max(0,-math.sin(angle))*2.2


def _ramps(spec):
    body=pigment.ramp(spec.coat)
    accent=pigment.ramp(spec.accent or '#6c675c')
    glow=pigment.ramp(spec.glow or '#d4b45d')
    return body,accent,glow


def render_construct(definition,state,frame,direction,spec):
    size=128 if definition.get('boss') else 64
    stage=Stage(size); m=_motion(state,frame); body,accent,glow=_ramps(spec)
    side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 0; back=direction==3
    collapse=m['collapse']; width=max(5.2,spec.girth)
    # Heavy weight transfer: opposite feet advance, torso shifts over the planted leg.
    near_dx,near_lift=_gait(m,0.0); far_dx,far_lift=_gait(m,.5)
    support=math.sin(m['phase'])*1.1*m['stride']
    lean=(near_dx-far_dx)*.10 + (m['lunge']-m['recoil'])*(.45 if side else .18)*(facing or 1)
    y=max(5.0,spec.height*.45*(1-collapse*.72)+m['bob']+abs(support)*.18)
    leg_spread=width*.46 if not side else 1.9
    feet=[]
    for near,sign,dx,lift in ((False,-1,far_dx,far_lift),(True,1,near_dx,near_lift)):
        lateral=sign*leg_spread if not side else sign*1.3
        travel=dx*(facing if side else .28)
        splay=collapse*(5.2 if near else 3.8)*(facing if side else sign)
        foot=(lateral+travel+splay,max(0,lift-collapse*.25))
        hip=(lateral*.72+lean*.25,y)
        knee=(lateral*.86+travel*.42+splay*.45,y*.50+lift*.18)
        stage.segment(hip,knee,3.5 if near else 3.1,2.9 if near else 2.6,body[3 if near else 2])
        stage.disc(knee,1.5,accent[3 if near else 2])
        stage.segment(knee,foot,2.9 if near else 2.6,2.3 if near else 2.1,body[3 if near else 2])
        stage.poly([(foot[0]-2.2,foot[1]),(foot[0]+2.8,foot[1]),(foot[0]+2.3,foot[1]+1.5),(foot[0]-1.8,foot[1]+1.5)],accent[2])
        feet.append(foot)
    # Torso is newly drawn around the current centre of mass.
    centre=lean
    top=y+7.5*(1-collapse*.48); bottom=y-6.8*(1-collapse*.25)
    stage.poly([(centre-width,bottom+1),(centre-width*.92,top-2),(centre-width*.45,top+2.2),(centre,top+3.8),
                (centre+width*.45,top+2.2),(centre+width*.92,top-2),(centre+width,bottom+1),(centre+width*.56,bottom-2.5),(centre-width*.56,bottom-2.5)],body[3])
    stage.line([(centre-width*.65,y+1),(centre+width*.65,y+1)],accent[4],1.4)
    stage.line([(centre,y-3),(centre,y+5.5)],body[1],1)
    # Cast visibly lifts the core/head and both forearms; hit/attack recoil changes carriage.
    head_y=top+5.0*(1-collapse*.55)+m['charge']*2.0
    head_x=centre*1.18 + (m['lunge']-m['recoil'])*(.23 if side else 0)*(facing or 1)
    head_r=max(3.4,spec.head)
    stage.poly([(head_x-head_r,head_y-head_r*.75),(head_x-head_r*.55,head_y+head_r*.75),(head_x,head_y+head_r),
                (head_x+head_r*.55,head_y+head_r*.75),(head_x+head_r,head_y-head_r*.75),(head_x,head_y-head_r)],accent[3])
    if not back:
        eye_y=head_y+.2
        if side: stage.disc((head_x+(facing or 1)*head_r*.38,eye_y),.85,glow[5],None)
        else:
            stage.disc((head_x-head_r*.36,eye_y),.75,glow[5],None); stage.disc((head_x+head_r*.36,eye_y),.75,glow[5],None)
    arm_swing=math.cos(m['phase'])*3.2*m['stride']
    for near,sign in ((False,-1),(True,1)):
        shoulder=(centre+sign*width*.88,top-1.5)
        counter=arm_swing*(-1 if near else 1)*(facing if side else .32)
        attack=m['lunge']*(1 if near else .35)*(facing if side else sign*.45)
        recoil=-m['recoil']*(1 if near else .6)*(facing if side else sign*.35)
        lift=m['charge']*(5.5 if near else 4.5)
        hand=(shoulder[0]+sign*4.5+counter+attack+recoil,shoulder[1]-7.0-lift-collapse*2.2)
        elbow=((shoulder[0]+hand[0])*.5+sign*1.3,(shoulder[1]+hand[1])*.5+1.3)
        stage.segment(shoulder,elbow,3.2,2.7,body[3 if near else 2]); stage.disc(elbow,1.35,accent[3 if near else 2]); stage.segment(elbow,hand,2.7,2.1,body[3 if near else 2]); stage.disc(hand,1.5,accent[3 if near else 2])
    # Visible core, plates and boss identity.
    core_y=y+1.6+m['charge']*.8
    stage.disc((centre*.5,core_y),2.1,glow[5],accent[1])
    if spec.back in ('spikes','plates','ridge') or definition.get('elite') or definition.get('boss'):
        for offset,height in ((-3.4,2.4),(0,3.8),(3.4,2.7)):
            stage.poly([(centre+offset-1,top+1),(centre+offset,top+1+height),(centre+offset+1,top+1)],accent[4])
    if definition.get('boss'):
        stage.line([(head_x-head_r*.85,head_y+head_r*.55),(head_x-head_r*1.4,head_y+head_r*1.45)],glow[4],1.8)
        stage.line([(head_x+head_r*.85,head_y+head_r*.55),(head_x+head_r*1.4,head_y+head_r*1.45)],glow[4],1.8)
    if m['flash']:
        overlay=Image.new('RGBA',stage.image.size,(255,236,210,0)); overlay.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['flash']*.45))); stage.image=Image.alpha_composite(stage.image,overlay)
    if m['fade']<1: stage.image.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['fade'])))
    return stage.image
