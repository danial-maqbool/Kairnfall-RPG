"""Authored anatomy for common fauna. All poses use a fixed 64px canvas.

Separate frontal, rear, and side constructions preserve the direction of heads,
feet, shells, and tails. Unsupported species keep their existing authored renderer.
"""
from __future__ import annotations
import math
from .common import Pixel, canvas, palette, shade, INK
from .creature_pack import body_colour
from .species_refinement import frame as previous_frame
from .humanoid import limb, finish

# body half-length, body half-height, head size, muzzle length, leg height, tail length
PROFILES={
    'rat':(12,7,5,5,5,20),'mouse':(9,7,4,3,4,17),
    'hare':(10,11,5,3,6,3),'weasel':(16,6,4,5,4,12),
    'fox':(14,9,5,7,9,19),'arctic_fox':(13,11,5,5,8,18),
    'wolf':(17,10,6,7,11,16),'hound':(17,9,5,7,12,14),
    'boar':(17,12,7,6,6,5),'bear':(18,14,7,4,8,3),
    'polar_bear':(18,13,6,8,9,3),'badger':(15,9,5,5,5,6),
    'wolverine':(15,11,6,4,7,8)}
SUPPORTED=frozenset(PROFILES)|{'spider','quartz_spider','turtle','tortoise'}


def polygon_oval(p,box,base):
    x0,y0,x1,y1=box; c=palette(base); w=x1-x0; h=y1-y0
    p.poly([(x0+w*.2,y0),(x0+w*.7,y0),(x1,y0+h*.27),(x1-1,y0+h*.72),
            (x0+w*.73,y1),(x0+w*.25,y1),(x0,y0+h*.7),(x0,y0+h*.28)],c[2])
    p.poly([(x0+w*.2,y0+1),(x0+w*.65,y0+1),(x0+w*.8,y0+h*.45),
            (x0+w*.64,y0+h*.65),(x0+w*.16,y0+h*.63),(x0+1,y0+h*.32)],c[3],None)
    p.line([(x0+w*.2,y0+2),(x0+w*.46,y0+1),(x0+w*.65,y0+2)],c[4])


def foot(p,x,y,width,c,hoof=False):
    p.poly([(x-width,y-2),(x+width-1,y-2),(x+width+1,y),(x+width,y+1),(x-width,y+1)],c[1] if hoof else c[2])
    p.line([(x-width+1,y-1),(x+width-1,y-1)],c[4])
    if hoof: p.line([(x,y-1),(x,y+1)],c[0])
    elif width>=3:
        for dx in (-1,1): p.dot(x+dx,y+1,c[0])


def mammal(p,m,state,n,direction):
    family=m['family']; length,height,head,muzzle,legs,tail=PROFILES[family]
    base=body_colour(m); c=palette(base); side=direction in (1,2); s=-1 if direction==1 else 1
    walk=math.sin(n*math.tau/8) if state=='walk' else 0
    attack=(0,-1,-2,3,4,2,0,0)[n] if state=='attack' else 0
    collapse=(0,0,1,3,5,7,8,8)[n] if state=='death' else 0
    cy=53-legs-height//2+collapse*.35
    if side:
        cx=29; length=min(length,17); rear=cx-length; front=cx+length-2
        def xy(x,y): return (64-x,y) if s<0 else (x,y)
        # All left/right coordinates are authored before projection, not image-rotated.
        class View:
            def poly(self,pts,color,outline=INK): p.poly([xy(x,y) for x,y in pts],color,outline)
            def line(self,pts,color,width=1): p.line([xy(x,y) for x,y in pts],color,width)
            def dot(self,x,y,color): p.dot(*xy(x,y),color)
        q=View()
        if tail>5:
            curve=[(rear+2,cy+2),(max(2,rear-tail*.4),cy+4),(max(2,rear-tail*.8),cy+1),(max(2,rear-tail),cy-4)]
            q.line(curve,c[0],3 if family in ('rat','mouse') else 7)
            q.line(curve,'b09085' if family in ('rat','mouse') else c[2],1 if family in ('rat','mouse') else 5)
            if family=='fox': q.line(curve[-2:],'d4c9ad',3)
        else: q.poly([(rear+1,cy),(rear-4,cy-3),(rear-4,cy+2),(rear+1,cy+4)],c[3])
        for far in (True,False):
            for fore in (False,True):
                x=(front-4 if fore else rear+5)+(1 if far else -1)
                swing=round(walk*(2 if legs<7 else 3))*(-1 if fore==far else 1)
                knee=(x+swing*.4,cy+height*.6+legs*.35)
                end=(x+swing,54-(max(0,swing) if state=='walk' else 0))
                if collapse: knee=(x+(-4 if fore else 4),53); end=(x+(4 if fore else -4),55)
                limb(p,xy(x,cy+height*.35),xy(*knee),4 if family in ('bear','polar_bear','boar') else 3,c[1] if far else base)
                limb(p,xy(*knee),xy(*end),3,c[1] if far else base)
                foot(p,*xy(*end),3 if family in ('bear','polar_bear') else 2,c,family=='boar')
            if far:
                # Low shoulders and narrower waist produce animal-specific silhouettes.
                pts=[(rear,cy-2),(rear+3,cy-height*.65),(cx,cy-height),(front-1,cy-height*.8),
                     (front+2,cy-2),(front,cy+height*.6),(cx+3,cy+height*.65),(cx-4,cy+height*.4),(rear+1,cy+height*.55)]
                q.poly(pts,c[2]); q.poly([(rear+3,cy-2),(cx-3,cy-height*.7),(front-3,cy-height*.6),(front-4,cy+height*.2),(cx-4,cy+height*.15)],c[3],None)
                q.line([(rear+4,cy-height*.4),(cx-2,cy-height*.75),(front-5,cy-height*.65)],c[4])
        hx=front+2+attack; hy=cy-height*.55+collapse*.4
        if family=='polar_bear':
            q.poly([(front-7,cy-height*.6),(hx+3,hy-2),(hx+2,hy+6),(front-4,cy+4)],c[3])
        q.poly([(hx-head,hy-head*.5),(hx-2,hy-head),(hx+head-1,hy-head*.5),(hx+head,hy+3),(hx+1,hy+head),(hx-head,hy+3)],c[3])
        q.poly([(hx+2,hy),(min(62,hx+head+muzzle),hy+2),(min(61,hx+head+muzzle),hy+5),(hx+2,hy+5)],c[2])
        q.dot(min(61,hx+head+muzzle),hy+2,c[0]); q.dot(hx+2,hy-1,INK); q.dot(hx+1,hy-2,c[4])
        q.line([(hx+3,hy+5),(min(61,hx+head+muzzle-1),hy+5)],c[1])
        if family in ('wolf','fox','arctic_fox'):
            q.poly([(hx-head+1,hy-3),(hx-head+1,hy-12),(hx+1,hy-5)],c[2]); q.line([(hx-head+2,hy-8),(hx-head+3,hy-4)],c[4])
        elif family=='hare':
            for dx in (-3,2): q.poly([(hx+dx-2,hy-3),(hx+dx-4,hy-18),(hx+dx-1,hy-20),(hx+dx+2,hy-4)],c[3]); q.line([(hx+dx-2,hy-15),(hx+dx,hy-6)],'ae8e85')
            # Folded haunch, visibly larger than a rat's hind leg.
            q.poly([(rear+4,cy),(rear+10,cy-1),(rear+13,cy+7),(rear+8,cy+11),(rear+2,cy+8)],c[2]); q.line([(rear+5,cy+2),(rear+9,cy+4),(rear+9,cy+7)],c[4])
        else:
            ear=4 if family in ('rat','mouse') else 3
            q.poly([(hx-head,hy-3),(hx-head-1,hy-ear-5),(hx-head+3,hy-ear-6),(hx-head+5,hy-3)],c[2])
            if family in ('rat','mouse'): q.line([(hx-head+1,hy-6),(hx-head+3,hy-4)],'bf9f96',2)
        if family=='boar':
            q.poly([(hx+head,hy+5),(hx+head+3,hy+6),(hx+head+4,hy+1),(hx+head+2,hy+3)],'ddcbae')
            for x in range(round(cx-6),round(front-2),3): q.line([(x,cy-height+2),(x-1,cy-height-2)],c[0])
        if family=='badger': q.line([(hx-2,hy-head+1),(hx+3,hy+2)],'d2cbb9',3)
        if family=='wolverine': q.line([(rear+5,cy-1),(cx,cy+3),(front-5,cy+2)],'b29b78',2)
    else:
        back=direction==3; x=32; width=min(14,round(length*.65)); by=36+collapse*.5
        # Face south: head overlaps chest. Face north: rump overlaps neck.
        head_y=by+7 if not back else by-12
        for sign in (-1,1):
            for fore in (False,True):
                px=x+sign*(width-3); py=48 if fore else 52
                sway=round(walk*2)*(sign if fore else -sign)
                foot(p,px+sway,py+min(3,collapse),3 if family in ('bear','polar_bear') else 2,c,family=='boar')
        polygon_oval(p,(x-width,by-12,x+width,by+14),base)
        if tail>5:
            ty=by+14 if back else by-11; end=ty+(10 if back else -10)
            p.line([(x,ty),(x+3,end),(x+7,end+1)],c[1],2 if family in ('rat','mouse') else 5)
        elif family=='hare': p.ellipse((x-3,by+10,x+3,by+16),c[4],INK)
        hy=head_y+attack*(1 if not back else -1)
        polygon_oval(p,(x-head-1,hy-head,x+head+1,hy+head),base)
        if not back:
            p.poly([(x-3,hy+2),(x+3,hy+2),(x+3,hy+muzzle),(x,hy+muzzle+2),(x-3,hy+muzzle)],c[3]); p.line([(x-1,hy+muzzle),(x+1,hy+muzzle)],c[0])
            for dx in (-3,3): p.dot(x+dx,hy,INK); p.dot(x+dx-1,hy-1,c[4])
        for sign in (-1,1):
            ex=x+sign*(head-1)
            if family=='hare': p.poly([(ex-2,hy-4),(ex-2,hy-19),(ex+1,hy-21),(ex+2,hy-4)],c[2]); p.line([(ex,hy-17),(ex,hy-7)],'b69b8f')
            elif family in ('wolf','fox','arctic_fox'): p.poly([(ex-3,hy-3),(ex,hy-12),(ex+3,hy-3)],c[2])
            else: p.ellipse((ex-3,hy-8,ex+3,hy-3),c[2],INK)
        if family=='boar' and not back:
            for sign in (-1,1): p.poly([(x+sign*5,hy+6),(x+sign*7,hy+5),(x+sign*6,hy+1)],'ddcbae')
        if family=='badger' and not back:
            for sign in (-1,1): p.line([(x+sign*2,hy-5),(x+sign*3,hy-1)],'e0d6bd',2)


def arachnid(p,m,state,n,direction):
    c=palette(body_colour(m)); step=math.sin(n*math.tau/8) if state=='walk' else 0
    folded=(0,0,.2,.4,.7,1,1,1)[n] if state=='death' else 0
    # Four attachment pairs. Projection changes the longitudinal body axis, not the bitmap.
    def xy(lateral,longitudinal):
        if direction==0: return (32+lateral,34+longitudinal)
        if direction==3: return (32-lateral,34-longitudinal)
        if direction==2: return (32+longitudinal,34+lateral*.7)
        return (32-longitudinal,34-lateral*.7)
    for sign in (-1,1):
        for i in range(4):
            attach=(-5+i*3); gait=round(step*2)*(1 if i%2 else -1)
            knee=sign*(18-folded*8); tip=sign*(27-folded*14)
            points=[xy(sign*5,attach),xy(knee,attach-8+i*4+gait),xy(tip,attach-13+i*7+gait)]
            p.line(points,c[0],3); p.line(points,c[3],1)
    abdomen=xy(0,-8); thorax=xy(0,5); head=xy(0,11)
    polygon_oval(p,(abdomen[0]-9,abdomen[1]-10,abdomen[0]+9,abdomen[1]+9),c[3])
    polygon_oval(p,(thorax[0]-6,thorax[1]-5,thorax[0]+6,thorax[1]+5),c[2])
    p.line([xy(-3,13),xy(-2,17)],c[4],2); p.line([xy(3,13),xy(2,17)],c[4],2)
    for side in (-1,1):
        for offset in (0,2): p.dot(*xy(side*(2+offset),10+offset//2),'d5bc88')
    if m['family']=='quartz_spider':
        p.poly([(abdomen[0],abdomen[1]-9),(abdomen[0]+5,abdomen[1]),(abdomen[0],abdomen[1]+6),(abdomen[0]-4,abdomen[1])],'b1cad2')
        p.line([(abdomen[0],abdomen[1]-7),(abdomen[0]-2,abdomen[1])],'e1e2ce')


def turtle(p,m,state,n,direction):
    sea=m['family']=='turtle'; c=palette('849871' if sea else '727c64')
    wave=math.sin(n*math.tau/8) if state in ('walk','idle') else 0
    tuck=(0,0,.2,.5,.8,1,1,1)[n] if state=='death' else 0
    def xy(lateral,longitudinal):
        if direction==0: return (32+lateral,33+longitudinal)
        if direction==3: return (32-lateral,33-longitudinal)
        if direction==2: return (32+longitudinal,35+lateral*.65)
        return (32-longitudinal,35-lateral*.65)
    for sign in (-1,1):
        for front in (True,False):
            start=9 if front else -9; reach=(27 if front and sea else 17 if sea else 15)*(1-.25*tuck)
            sway=round(wave*(3 if front else 2))*sign
            points=[xy(sign*8,start),xy(sign*reach,start-8+sway),xy(sign*(reach-2),start-12+sway),xy(sign*10,start-6)]
            p.poly(points,c[2]); p.line([xy(sign*10,start-2),xy(sign*(reach-3),start-9+sway)],c[4])
    head=xy(0,20-5*tuck)
    p.line([xy(0,12),head],c[1],7); p.line([xy(-1,13),(head[0]-1,head[1])],c[3],4)
    p.ellipse((head[0]-4,head[1]-4,head[0]+4,head[1]+4),c[3],INK)
    for sign in (-1,1): p.dot(*xy(sign*2,21-5*tuck),INK)
    p.poly([xy(-2,-14),xy(0,-22),xy(2,-14)],c[2])
    shell=palette('776c4d' if sea else '85806a')
    outline=[(-9,-15),(8,-15),(13,-9),(14,7),(8,14),(-8,14),(-14,7),(-13,-9)]
    p.poly([xy(a,b) for a,b in outline],shell[1]); p.poly([xy(a*.88,b*.88) for a,b in outline],shell[3])
    # Scutes follow the shell axis for all four directions.
    for y in (-9,0,8):
        p.poly([xy(-4,y-4),xy(3,y-4),xy(6,y),xy(3,y+4),xy(-4,y+4),xy(-6,y)],shell[2])
        p.line([xy(-3,y-3),xy(2,y-3),xy(4,y-1)],shell[4])
    for sign in (-1,1):
        for y in (-9,0,8): p.line([xy(sign*5,y),xy(sign*11,y-3)],shell[0])


def frame(definition,state,number,direction):
    family=definition['family']
    if family not in SUPPORTED or definition.get('boss'): return previous_frame(definition,state,number,direction)
    image=canvas(); p=Pixel(image)
    if family in PROFILES: mammal(p,definition,state,number,direction)
    elif family in ('spider','quartz_spider'): arachnid(p,definition,state,number,direction)
    else: turtle(p,definition,state,number,direction)
    if definition.get('elite'):
        # Scars are an explicit elite treatment, never used to fake normal-species uniqueness.
        p.line([(28,30),(32,34)],'b7a488',2)
    return finish(image,state,number)
