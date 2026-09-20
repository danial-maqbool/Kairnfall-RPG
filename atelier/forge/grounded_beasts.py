"""Grounded 2026 creature renderer.

Every active mob keeps the existing runtime sheet contract, but its pixels are
reconstructed from anatomy data rather than sampled or transformed from legacy
frames. Motion changes feet, joints, body carriage, head and action silhouette;
death collapses into a new final pose instead of rotating a standing sprite.
"""
from __future__ import annotations

import math
from PIL import Image, ImageDraw
from . import pigment

INK=(22,21,24,255)
DEEP=(14,14,17,255)
FRAMES=8


def _pt(p): return int(round(p[0])),int(round(p[1]))
def _axis(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; n=math.hypot(dx,dy) or 1
    return dx/n,dy/n
def _normal(a,b):
    ux,uy=_axis(a,b); return -uy,ux
def _quad(a,b,wa,wb):
    px,py=_normal(a,b); return [(a[0]+px*wa/2,a[1]+py*wa/2),(b[0]+px*wb/2,b[1]+py*wb/2),(b[0]-px*wb/2,b[1]-py*wb/2),(a[0]-px*wa/2,a[1]-py*wa/2)]

class Stage:
    def __init__(self,size):
        self.size=size; self.scale=size/64; self.cx=size/2-.5; self.ground=size*.86
        self.image=Image.new('RGBA',(size,size),(0,0,0,0)); self.draw=ImageDraw.Draw(self.image)
    def at(self,x,y): return self.cx+x*self.scale,self.ground-y*self.scale
    def poly(self,points,fill,outline=INK):
        pts=[_pt(self.at(x,y)) for x,y in points]; self.draw.polygon(pts,fill=fill)
        if outline: self.draw.line(pts+[pts[0]],fill=outline,width=max(1,round(self.scale)))
    def screen_poly(self,points,fill,outline=INK):
        pts=[_pt(p) for p in points]; self.draw.polygon(pts,fill=fill)
        if outline:self.draw.line(pts+[pts[0]],fill=outline,width=max(1,round(self.scale)))
    def line(self,points,fill,width=1): self.draw.line([_pt(self.at(x,y)) for x,y in points],fill=fill,width=max(1,round(width*self.scale)))
    def disc(self,p,r,fill,outline=INK):
        x,y=self.at(*p); rr=r*self.scale
        self.draw.ellipse((round(x-rr),round(y-rr),round(x+rr),round(y+rr)),fill=fill,outline=outline,width=max(1,round(self.scale)))
    def ellipse(self,center,rx,ry,fill,outline=INK):
        x,y=self.at(*center); rx*=self.scale; ry*=self.scale
        self.draw.ellipse((round(x-rx),round(y-ry),round(x+rx),round(y+ry)),fill=fill,outline=outline,width=max(1,round(self.scale)))
    def segment(self,a,b,wa,wb,fill,outline=INK): self.screen_poly(_quad(self.at(*a),self.at(*b),wa*self.scale,wb*self.scale),fill,outline)

def _motion(state,frame):
    t=frame/(FRAMES-1); phase=frame/FRAMES*math.tau
    m={'phase':phase,'bob':0.0,'stride':0.0,'lunge':0.0,'crouch':0.0,'charge':0.0,'collapse':0.0,'flash':0.0,'fade':1.0}
    if state=='idle': m['bob']=math.sin(phase)*.45
    elif state=='walk': m['stride']=1; m['bob']=abs(math.cos(phase))*.65-.3
    elif state=='attack':
        drive=math.sin(min(1,t*1.35)*math.pi); m['lunge']=drive*4.8; m['crouch']=drive*1.4
    elif state=='cast': m['charge']=math.sin(t*math.pi)**.75; m['bob']=-m['charge']*1.2
    elif state=='hit':
        shock=math.sin(min(1,t*1.8)*math.pi)**.65; m['lunge']=-shock*3; m['crouch']=shock
        m['flash']=.6 if frame==0 else .4 if frame==1 else .18 if frame==2 else 0
    elif state=='death':
        m['collapse']=min(1,(t*1.25)**.82); m['fade']=1 if frame<6 else .86 if frame==6 else .7
    return m

def _ramps(spec):
    coat=pigment.ramp(spec.coat); dark=pigment.ramp(spec.accent or '#443d3b'); pale=pigment.ramp(spec.belly or '#c4b69d')
    return coat,dark,pale

def _gait(m,offset,reach=4,lift=2.2):
    if not m['stride']: return 0,0
    a=m['phase']+offset*math.tau; return math.cos(a)*reach,max(0,-math.sin(a))*lift

def _paw(stage,p,digit,pale):
    if digit=='hoof':
        x,y=p; stage.poly([(x-1.7,y),(x+1.8,y),(x+1.4,y+1.5),(x-1.4,y+1.5)],pale[2])
    else:
        stage.ellipse((p[0]+.4,p[1]+.7),2.3,1.2,pale[1]); stage.line([(p[0]+1.3,p[1]+.7),(p[0]+2.3,p[1]+.4)],pale[0])

def _leg(stage,spec,hip,offset,m,near,forward=0):
    coat,dark,pale=_ramps(spec); dx,lift=_gait(m,offset,4.2,2.4); collapse=m['collapse']
    spread=(5 if near else -4)*collapse; foot=(hip[0]+dx+spread+forward, max(0,lift-collapse*.3)); knee=(hip[0]+dx*.42+spread*.45+forward*.4,hip[1]*.48*(1-collapse*.72)+.5)
    tone=coat[3] if near else coat[2]; w=spec.leg_width*(1 if near else .86)
    stage.segment(hip,knee,w*1.15,w*.88,tone); stage.segment(knee,foot,w*.88,w*.68,tone); _paw(stage,foot,spec.digit,pale)
    return foot

def _tail(stage,spec,root,m,facing,back=False):
    if spec.tail in ('','none'): return
    coat,dark,pale=_ramps(spec); c=m['collapse']; sway=math.sin(m['phase'])*1.4
    if spec.tail=='stub': stage.disc((root[0]-facing*2,root[1]+.5),2.0,coat[3]); return
    if spec.tail=='puff': stage.disc((root[0]-facing*2.4,root[1]+.6),2.5,pale[3]); return
    length=spec.tail_length*(1-c*.25); end=(root[0]-facing*length,root[1]+(2 if not back else -2)-c*root[1]*.65+sway*.35)
    mid=((root[0]+end[0])/2-facing*.8,(root[1]+end[1])/2+2+sway*.5)
    width={'brush':4.2,'rope':1.5,'whip':2.0,'taper':3.4,'tassel':2.2,'curl':2.0,'sting':2.0}.get(spec.tail,2.8)
    stage.line([root,mid,end],coat[3],width)
    if spec.tail=='brush': stage.disc(end,2.2,coat[3])
    elif spec.tail=='tassel': stage.disc(end,1.8,dark[3])
    elif spec.tail=='sting': stage.poly([(end[0],end[1]+2.8),(end[0]+2,end[1]-1),(end[0]-2,end[1]-1)],dark[4])

def _ears(stage,spec,head,side,facing):
    if spec.ear in ('','none'): return
    coat,dark,pale=_ramps(spec); size=spec.ear_size
    roots=[(head[0]-spec.head*.65,head[1]+spec.head*.6),(head[0]+spec.head*.65,head[1]+spec.head*.6)] if not side else [(head[0]-facing*spec.head*.4,head[1]+spec.head*.55)]
    for x,y in roots:
        if spec.ear in ('tall','rabbit','pointed','tuft'):
            high=size*(1.55 if spec.ear=='rabbit' else 1.15); stage.poly([(x-1.3,y),(x,y+high),(x+1.3,y)],coat[3]); stage.poly([(x-.55,y+.4),(x,y+high*.72),(x+.55,y+.4)],pale[2],None)
        elif spec.ear=='drop': stage.poly([(x-1.2,y),(x+1.8,y-.5),(x+2.4,y-size),(x-.2,y-size*.7)],coat[3])
        else: stage.disc((x,y+.6),max(1.5,size*.55),coat[3])

def _horns(stage,spec,head,side,facing):
    if not spec.horn or spec.horn=='beak': return
    horn=pigment.ramp('#c8b996'); r=spec.head
    signs=(facing,) if side else (-1,1)
    for s in signs:
        root=(head[0]+s*r*.45,head[1]+r*.55)
        if spec.horn=='antler':
            stage.line([root,(root[0]+s*1.5,root[1]+4),(root[0]+s*3.5,root[1]+7)],horn[3],1.8); stage.line([(root[0]+s*1.4,root[1]+3),(root[0]+s*4.4,root[1]+5)],horn[3],1.4)
        elif spec.horn in ('curl','bull','ridge_horn'): stage.line([root,(root[0]+s*3,root[1]+3),(root[0]+s*4,root[1]+.5)],horn[3],2)
        else: stage.poly([(root[0]-s*.8,root[1]),(root[0]+s*1.2,root[1]+4),(root[0]+s*1.8,root[1])],horn[3])

def _face(stage,spec,head,side,facing,back,m):
    coat,dark,pale=_ramps(spec); _ears(stage,spec,head,side,facing); _horns(stage,spec,head,side,facing)
    if back:return
    if side:
        tip=(head[0]+facing*(spec.head*.6+spec.muzzle),head[1]-.4); stage.poly([(head[0]+facing*spec.head*.15,head[1]+spec.head*.25),(tip[0],tip[1]+1.3),(tip[0]+facing*.4,tip[1]-1.1),(head[0]+facing*spec.head*.2,head[1]-spec.head*.55)],coat[3])
        stage.disc((tip[0]+facing*.2,tip[1]),1.0,dark[1]); eye=(head[0]+facing*spec.head*.42,head[1]+spec.head*.18); stage.disc(eye,1.0,pigment.ramp(spec.eye)[4],None)
        if m['lunge']>1: stage.line([(head[0]+facing*spec.head*.35,head[1]-spec.head*.35),(tip[0],tip[1]-1.1)],DEEP,1.2)
    else:
        stage.ellipse((head[0],head[1]-spec.head*.42),spec.head*.48,max(1.2,spec.muzzle*.25),pale[2]);
        for s in (-1,1): stage.disc((head[0]+s*spec.head*.40,head[1]+spec.head*.18),.95,pigment.ramp(spec.eye)[4],None)

def _back_feature(stage,spec,center,half,top):
    if spec.back in ('','hump'): return
    _,dark,_=_ramps(spec)
    if spec.back=='shell': stage.ellipse((center,top+.8),half*.88,spec.girth*.9,dark[3]); stage.line([(center-half*.55,top+.2),(center+half*.55,top+.2)],dark[5])
    elif spec.back in ('ridge','plates','spikes'):
        for i in range(5):
            x=center-half*.65+i*half*.325; h=2.2+(2.4 if spec.back=='spikes' else 1.1)*(1-abs(i-2)/3); stage.poly([(x-1,top),(x,top+h),(x+1,top)],dark[3])

def quadruped(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 0; back=direction==3; c=m['collapse']
    body_y=spec.height*(1-c*.73)-m['crouch']*.45+m['bob']; body_y=max(spec.girth*.35,body_y)
    if not side:
        spread=spec.girth*.72; rear_y=body_y-.3
        for s,off in ((-1,0),(1,.5)): _leg(stage,spec,(s*spread,rear_y-spec.girth*.25),off,m,s>0)
        stage.ellipse((0,body_y),spec.girth*.95,spec.girth*1.08,coat[3]); _back_feature(stage,spec,0,spec.girth,body_y+spec.girth*.72)
        for s,off in ((-1,.5),(1,0)): _leg(stage,spec,(s*spread*.58,body_y-spec.girth*.18),off,m,s>0)
        if back:
            _tail(stage,spec,(0,body_y+spec.girth*.7),m,1,True); return
        head=(0,body_y+spec.girth*.95+spec.neck*.55*(1-c)+spec.head*.45); stage.segment((0,body_y+spec.girth*.45),head,spec.neck_width*1.15,spec.neck_width*.85,coat[3]); stage.ellipse(head,spec.head,spec.head*1.02,coat[3]); _face(stage,spec,head,False,1,False,m); return
    half=spec.length/2; lunge=m['lunge']*facing; front=(facing*half*.78+lunge,body_y); rear=(-facing*half*.78+lunge*.15,body_y-.2)
    _leg(stage,spec,(rear[0]+facing*.6,rear[1]-spec.girth*.3),.5,m,False); _leg(stage,spec,(front[0]-facing*.8,front[1]-spec.girth*.3),0,m,False)
    top=body_y+spec.girth*(1.18 if spec.back=='hump' else .95); belly=body_y-spec.girth*.82
    stage.poly([(rear[0]-facing*half*.28,rear[1]+spec.girth*.62),(rear[0]+facing*half*.18,top-.4),(front[0]-facing*half*.16,top),
                (front[0]+facing*half*.28,front[1]+spec.girth*.55),(front[0]+facing*half*.30,belly+.2),(front[0]-facing*half*.08,belly),
                (rear[0]+facing*half*.10,belly+.2),(rear[0]-facing*half*.25,rear[1]-spec.girth*.5)],coat[3])
    stage.poly([(rear[0]-facing*half*.12,body_y-spec.girth*.35),(front[0]+facing*half*.10,body_y-spec.girth*.33),(front[0],belly+.1),(rear[0],belly+.15)],pale[2],None); _back_feature(stage,spec,(front[0]+rear[0])/2,half*.85,top)
    _leg(stage,spec,(rear[0]+facing*.6,rear[1]-spec.girth*.3),0,m,True); _leg(stage,spec,(front[0]-facing*.8,front[1]-spec.girth*.3),.5,m,True)
    _tail(stage,spec,(rear[0]-facing*half*.24,body_y+spec.girth*.48),m,facing)
    neck=(front[0]+facing*half*.12,body_y+spec.girth*.50); head=(neck[0]+facing*spec.neck*.72*(1-c),neck[1]+spec.neck*.70*(1-c))
    if c>.45: head=(neck[0]+facing*(spec.neck*.5+3),spec.head*.85)
    stage.segment(neck,head,spec.neck_width*1.12,spec.neck_width*.84,coat[3]); stage.ellipse(head,spec.head,spec.head,coat[3]); _face(stage,spec,head,True,facing,False,m)

def humanoid(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 0; back=direction==3; c=m['collapse']; phase=m['phase']
    pelvis_y=max(5,spec.height*.48*(1-c*.62)); chest_y=pelvis_y+spec.height*.34*(1-c*.45); head_y=chest_y+spec.head*1.45*(1-c*.35)
    spread=3 if not side else 1.5; swing=math.cos(phase)*4*m['stride']
    for near,s in ((False,-1),(True,1)):
        hip=(s*spread*.55,pelvis_y); foot=(s*spread+swing*(1 if near else -1)+s*c*5,max(0,c*.2)); knee=(s*spread*.8+swing*.35, (pelvis_y+foot[1])/2)
        stage.segment(hip,knee,spec.leg_width*1.15,spec.leg_width*.85,coat[3 if near else 2]); stage.segment(knee,foot,spec.leg_width*.85,spec.leg_width*.65,coat[3 if near else 2]); _paw(stage,foot,'paw',dark)
    torso_w=spec.girth*.85; stage.poly([(-torso_w,chest_y-spec.girth*.8),(-torso_w*.9,chest_y+spec.girth*.7),(0,chest_y+spec.girth),(torso_w*.9,chest_y+spec.girth*.7),(torso_w,chest_y-spec.girth*.8),(torso_w*.55,pelvis_y),(-torso_w*.55,pelvis_y)],coat[3])
    for near,s in ((False,-1),(True,1)):
        shoulder=(s*torso_w*.92,chest_y+spec.girth*.5); strike=m['lunge']*(facing or s)*(.75 if near else .3); hand=(shoulder[0]+s*2+strike,shoulder[1]-5-m['charge']*6); elbow=((shoulder[0]+hand[0])/2+s*1,(shoulder[1]+hand[1])/2+1)
        stage.segment(shoulder,elbow,spec.leg_width*.9,spec.leg_width*.7,coat[3 if near else 2]); stage.segment(elbow,hand,spec.leg_width*.7,spec.leg_width*.55,coat[3 if near else 2]); stage.disc(hand,1.4,pale[3])
    head=(0,head_y); stage.ellipse(head,spec.head,spec.head*1.06,coat[3]); _ears(stage,spec,head,side,facing or 1); _horns(stage,spec,head,side,facing or 1)
    if not back:
        for s in ((facing,) if side else (-1,1)): stage.disc((head[0]+s*spec.head*.35,head[1]+spec.head*.18),.8,pigment.ramp(spec.eye)[4],None)
    if spec.family_key in ('bandit','pirate','knight','goblin','kobold'):
        stage.line([(-torso_w*.65,chest_y+.3),(torso_w*.65,chest_y+.3)],dark[4],2)
    if spec.family_key in ('knight','construct','automaton','sentinel','guardian'): stage.poly([(-torso_w*.85,chest_y+.2),(0,chest_y+spec.girth*.75),(torso_w*.85,chest_y+.2),(torso_w*.6,chest_y-spec.girth*.6),(-torso_w*.6,chest_y-spec.girth*.6)],dark[3])

def bird(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 1; back=direction==3; c=m['collapse']; body_y=max(4,spec.leg*(1-c*.8)+m['bob'])
    for s,off in ((-1,0),(1,.5)):
        dx,lift=_gait(m,off,2.4,1.8); hip=(s*1.2,body_y-spec.girth*.3); foot=(s*1.4+dx+s*c*4,lift); knee=(s*1.8+dx*.4,body_y*.45); stage.segment(hip,knee,1.8,1.3,dark[3]); stage.segment(knee,foot,1.3,1,dark[3]); stage.line([(foot[0]-1.8,foot[1]),(foot[0]+2.2,foot[1])],dark[1])
    stage.ellipse((0,body_y),spec.girth,spec.girth*.9,coat[3]); wing=spec.girth*(1.3+m['charge']*.6)
    if side: stage.poly([(-facing*1,body_y+2),( -facing*wing,body_y+5+m['charge']*5),(-facing*(wing+2),body_y-1),(-facing*1,body_y-2)],dark[3])
    else:
        stage.poly([(-2,body_y+2),(-wing,body_y+5+m['charge']*5),(-wing-2,body_y-1),(-1,body_y-2)],dark[3]); stage.poly([(2,body_y+2),(wing,body_y+5+m['charge']*5),(wing+2,body_y-1),(1,body_y-2)],dark[3])
    neck=(facing*spec.neck*.3,body_y+spec.girth*.65); head=(facing*spec.neck*.65,body_y+spec.girth+spec.neck*.65*(1-c)); stage.segment(neck,head,2.4,1.7,coat[3]); stage.ellipse(head,spec.head,spec.head*.95,coat[3])
    if not back:
        beak=(head[0]+facing*(spec.head+spec.muzzle),head[1]); stage.poly([(head[0]+facing*spec.head*.5,head[1]+1.2),beak,(head[0]+facing*spec.head*.5,head[1]-1.2)],pale[4]); stage.disc((head[0]+facing*spec.head*.35,head[1]+.6),.8,pigment.ramp(spec.eye)[4],None)

def serpent(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 1; c=m['collapse']; count=max(7,spec.segments or 9); length=spec.length
    pts=[]
    for i in range(count):
        t=i/(count-1); x=(t-.5)*length*(facing if side else .3); wave=math.sin(m['phase']+t*math.tau*1.6)*(1.4 if m['stride'] else .55); y=1.8+math.sin(t*math.pi)*4*(1-c*.7)+wave*(1-t)
        if not side:x=wave*1.6
        pts.append((x,y))
    for i,p in enumerate(pts): stage.disc(p,spec.girth*(.85-.45*i/(count-1)),coat[3 if i%2==0 else 2])
    head=(pts[0][0]+facing*m['lunge']*.4,pts[0][1]+spec.head*.6); stage.ellipse(head,spec.head,spec.head*.8,coat[3]); _face(stage,spec,head,side,facing, direction==3,m)

def insect(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 1; c=m['collapse']; body_y=max(3,spec.height*(1-c*.65)*.55+m['bob']); seg=spec.segments or 3
    centers=[((i-(seg-1)/2)*spec.length/max(2,seg)*(.9 if side else .2),body_y+math.sin(m['phase']+i)*.25) for i in range(seg)]
    for i,p in enumerate(centers): stage.ellipse(p,spec.girth*(.72 if i else .55),spec.girth*.62,coat[3 if i%2==0 else 2])
    legs=max(6,min(8,spec.legs)); root=centers[len(centers)//2]
    for i in range(legs):
        s=-1 if i<legs/2 else 1; k=i%(legs//2); angle=(-.6+k*.55); end=(root[0]+s*(spec.girth+5),max(0,root[1]-spec.girth*.6+math.sin(angle+m['phase'])*2)); mid=(root[0]+s*(spec.girth+1.8),root[1]+math.cos(angle)*2); stage.line([root,mid,end],dark[2],1.4)
    if spec.wings:
        stage.ellipse((-spec.girth*.6,body_y+spec.girth*.7),spec.girth*1.2,spec.girth*.55,(180,195,190,130),dark[2]); stage.ellipse((spec.girth*.6,body_y+spec.girth*.7),spec.girth*1.2,spec.girth*.55,(180,195,190,130),dark[2])
    head=(centers[0][0]+facing*spec.head*.6,centers[0][1]+.4); stage.ellipse(head,spec.head,spec.head*.8,dark[3]);
    if direction!=3:
        for s in (-1,1): stage.disc((head[0]+s*spec.head*.35,head[1]+.6),.7,pigment.ramp(spec.eye)[4],None)

def spirit(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); c=m['collapse']; charge=m['charge']
    side=direction in (1,2); facing=1 if direction==2 else -1 if direction==1 else 0
    # Spirits express action weight through the core, mantle and tendrils.
    drive=m['lunge']*(facing if side else .28)
    y=max(3,spec.height*(1-c*.75)*.55+m['bob']+2 + charge*1.7 - m['crouch']*.25)
    x=drive
    squash=1.0 + min(.18,abs(m['lunge'])*.025) - c*.28
    stage.ellipse((x,y),spec.girth*(1+charge*.16)*squash,spec.girth*(1.25-charge*.08)*(1-c*.18),coat[3])
    reach=spec.girth+2+abs(m['lunge'])*.55+charge*2.2
    lift=5+charge*4+m['crouch']*.45
    for s in (-1,1):
        forward=(facing if side else s)
        stage.poly([(x+s*1.4,y+1),(x+s*reach + forward*m['lunge']*.16,y+lift),(x+s*(spec.girth+1),y-1)],dark[3])
    trail=-m['lunge']*(facing if side else .18)
    for i in range(3):
        left=-spec.girth+i*spec.girth
        stage.poly([(x+left,y-spec.girth*.5),(x+left+spec.girth*.5+trail,y-spec.girth-5-c*4-charge*1.3),(x+left+spec.girth,y-spec.girth*.5)],coat[2])
    if spec.glow:
        g=pigment.ramp(spec.glow)
        radius=max(1.2,spec.girth*.28)*(1+charge*.38+min(.24,abs(m['lunge'])*.035))
        stage.disc((x+(facing if side else 0)*m['lunge']*.12,y+.8+charge*.8),radius,g[5],None)
        if charge>.25:
            stage.line([(x-2-charge*2,y+spec.girth+2),(x,y+spec.girth+4+charge*2),(x+2+charge*2,y+spec.girth+2)],g[4],1.2)

def construct(stage,spec,m,direction):
    coat,dark,pale=_ramps(spec); c=m['collapse']; y=max(5,spec.height*.47*(1-c*.7)); width=spec.girth
    for s in (-1,1):
        foot=(s*(width*.55+c*5),0); knee=(s*width*.5,y*.5); hip=(s*width*.4,y); stage.segment(hip,knee,3.4,2.8,dark[3]); stage.segment(knee,foot,2.8,2.3,dark[3])
    stage.poly([(-width,y-3),(-width*.85,y+5),(0,y+8),(width*.85,y+5),(width,y-3),(width*.55,y-7),(-width*.55,y-7)],coat[3]); head=(0,y+12*(1-c*.5)); stage.poly([(-spec.head,head[1]-spec.head),(0,head[1]+spec.head),(spec.head,head[1]-spec.head)],dark[3])
    for s in (-1,1):
        shoulder=(s*width*.9,y+4); hand=(s*(width+5+m['charge']*3),y-1+m['lunge']*.2); stage.segment(shoulder,hand,3.2,2.3,coat[2 if s<0 else 3])
    if spec.glow: stage.disc((0,y+2),2,pigment.ramp(spec.glow)[5],None)

def render_frame(definition,state,number,direction,spec):
    size=128 if definition.get('boss') else 64; stage=Stage(size); m=_motion(state,number); archetype=spec.archetype
    if archetype in ('quadruped','amphibian','aquatic','primate'): quadruped(stage,spec,m,direction)
    elif archetype in ('humanoid','plant'): humanoid(stage,spec,m,direction)
    elif archetype in ('bird','drake'): bird(stage,spec,m,direction)
    elif archetype in ('serpent','worm'): serpent(stage,spec,m,direction)
    elif archetype in ('insect','arachnid','crustacean'): insect(stage,spec,m,direction)
    elif archetype in ('spirit','elemental'): spirit(stage,spec,m,direction)
    elif archetype in ('construct','mineral','mimic'): construct(stage,spec,m,direction)
    else: quadruped(stage,spec,m,direction)
    if definition.get('elite') or definition.get('boss'):
        tone=pigment.ramp(spec.glow or '#d4aa5a'); stage.line([(-5,stage.size/stage.scale*.0+spec.height+5),(0,spec.height+8),(5,spec.height+5)],tone[4],1.4)
    if m['flash']:
        overlay=Image.new('RGBA',stage.image.size,(255,234,210,0)); overlay.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['flash']*.45))); stage.image=Image.alpha_composite(stage.image,overlay)
    if m['fade']<1: stage.image.putalpha(stage.image.getchannel('A').point(lambda a:round(a*m['fade'])))
    return stage.image
