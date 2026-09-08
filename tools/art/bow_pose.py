"""Side-view bow construction tied to the existing two hand anchors.

The grip is on the bow, not on its string. Attack frames draw, release, and reload
an arrow. Geometry is mirrored before shading, so lighting stays upper-left.
"""
from __future__ import annotations
import math
from .common import INK, palette


def geometry(j: dict) -> dict:
    hx,hy=j['hand_r']; direction=j['sign']; state=j.get('state','idle'); frame=j.get('frame',0)
    collapse=j.get('collapse',0.0)
    angle=-math.pi*.5*collapse
    cs,sn=math.cos(angle),math.sin(angle)
    length=16-round(collapse*4)
    def point(u,v):
        return (round(hx+direction*(u*cs-v*sn)),round(hy+u*sn+v*cs))
    curve=[point(-4,-length),point(-2,-length*.75),point(0,-5),point(0,0),
           point(0,5),point(-2,length*.75),point(-4,length)]
    drawing=state=='attack' and frame in (1,2)
    nock=j['hand_l'] if drawing else point(-4,0)
    arrow=None
    if state not in ('death','cast') and not (state=='attack' and frame in (4,5)):
        tip=point(18,0)
        # A release frame shows the arrow ahead of the grip rather than on the string.
        start=point(5,0) if state=='attack' and frame==3 else nock
        arrow=(start,tip)
    return {'grip':(hx,hy),'curve':curve,'string':(curve[0],nock,curve[-1]),
            'nock':nock,'drawing':drawing,'arrow':arrow,'direction':direction}


def draw(p,j):
    g=geometry(j); wood=palette('96724f'); string='d4c7a5'; s=g['direction']
    p.line(g['curve'],INK,3)
    p.line(g['curve'],wood[3],2)
    # Highlight the lit surface in screen space, independently of the facing row.
    p.line([(x-1,y) for x,y in g['curve'][1:6]],wood[4])
    p.line(g['string'],string)
    for x,y in (g['curve'][0],g['curve'][-1]):
        p.line([(x-1,y),(x+1,y)],'bdb8a1')
    if g['arrow'] is not None:
        start,end=g['arrow']; ex,ey=end
        p.line([start,end],'ad9164')
        p.poly([(ex,ey),(ex-4*s,ey-2),(ex-3*s,ey+2)],'b5c3c1')
        sx,sy=start
        p.line([(sx+2*s,sy),(sx-1*s,sy-2)],'d6c9a6')
        p.line([(sx+3*s,sy),(sx,sy+2)],'acb4a8')
    hx,hy=g['grip']
    p.line([(hx,hy-3),(hx,hy+3)],INK,4)
    p.line([(hx,hy-2),(hx,hy+2)],'75513c',2)
    p.line([(hx-1,hy-2),(hx+1,hy-1)],'ba9161')
    p.line([(hx-1,hy+1),(hx+1,hy+2)],'4f3c31')
