#!/usr/bin/env python3
"""Temporary targeted anatomy corrections, applied before strict candidate validation."""
from runtime_upgrade import replace


DRAWING_SOURCE=r'''

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
'''


def main():
    path='tools/art/wildlife.py'
    replace(path,'\ndef frame(definition,state,number,direction):',DRAWING_SOURCE+'\n\ndef frame(definition,state,number,direction):')
    replace(path,"elif s.archetype=='aquatic':_aquatic(b,s,m)",
        "elif s.archetype=='aquatic':\n        if s.family_key=='manta':_manta(b,s,m)\n        elif s.family_key=='cuttle':_cuttle(b,s,m)\n        else:_aquatic(b,s,m)")
    replace(path,"elif s.archetype in ('arachnid','insect','crustacean'):_many_legs(b,s,m,8 if s.archetype=='arachnid' else 10 if s.archetype=='crustacean' else 6)",
        "elif s.family_key=='scorpion':_scorpion(b,s,m)\n    elif s.archetype in ('arachnid','insect','crustacean'):_many_legs(b,s,m,4 if s.shell else 8 if s.archetype in ('arachnid','crustacean') else 6)")
    replace(path,"for front in (False,True):leg(front,far_side,True)","for front in ((False,) if s.legs==2 and s.wings else (False,True)):leg(front,far_side,True)")
    replace(path,"for front in (False,True):leg(front,-far_side,False)","for front in ((False,) if s.legs==2 and s.wings else (False,True)):leg(front,-far_side,False)")
    replace(path,"if s.family_key=='myconid' or 'mushroom' in s.family_key:","if s.family_key in ('myconid','fungus') or 'mushroom' in s.family_key:")
    replace(path,"    b.ellipsoid((-3+m['drive'],0,z),s.length*.36,s.girth,s.girth*.65,s.coat)",
        """    b.ellipsoid((-3+m['drive'],0,z),s.length*.36,s.girth,s.girth*.65,s.coat)
    if s.shell:
        shell=s.accent or 'b49476';sx=-5+m['drive']*.35;sz=z+3-m['collapse']*2
        b.ellipsoid((sx,0,sz),6.5,6,6,shell)
        for side in (-1,1):
            points=[]
            for k in range(11):
                a=k*math.pi/3;r=max(.5,4-k*.30)
                points.append((sx+math.cos(a)*r,side*5.5,sz+math.sin(a)*r))
            b.line(points,shade(shell,.65),1.1)""")
    replace(path,"end=(hx+7+m['drive'],side*8,z+2)",
        "end=(hx+7+m['drive']+m['charge']*1.5,side*(8+m['charge']*2),z+2+m['charge']*4)")
    replace(path,"b.poly([end,(end[0]+4,end[1]-2,z+3),(end[0]+5,end[1],z+2),(end[0]+3,end[1]+3,z)],s.coat)",
        "b.poly([end,(end[0]+4,end[1]-2,end[2]+1),(end[0]+5,end[1],end[2]),(end[0]+3,end[1]+3,end[2]-2)],s.coat)")
    print('Explicit species anatomy; raised, visible casting pincers and bounded feeding-tentacle contact.',flush=True)

if __name__=='__main__':main()
