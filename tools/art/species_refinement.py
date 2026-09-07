"""Species anatomy refinements identified by the duplicate-sheet audit."""
from __future__ import annotations
import math
from PIL import Image
from .common import Pixel, canvas, palette, animation_pose, finish_frame, INK
from .environment_pack import crystal, stone
from .arcane_creatures import frame as existing_frame
from . import creature_pack as base

REFINED={'sentinel','elemental','wasp','spore_moth','pirate','fire_beetle','scarab','polar_bear','tick','wisp','geode','cuttle','wolf','harpy','skimmer','gull','vulture','djinn','phantom','stag','mouse','mudskipper','frog','crab','hermit_crab','worm','construct','turtle','fungus','leech','guardian','automaton'}


def eyes(p,x,y,c,back=False):
    if back: return
    for dx in (-3,3): p.dot(x+dx,y,INK); p.dot(x+dx-1,y-1,c[5])


def flipper(p,start,end,width,c):
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=max(1,math.hypot(dx,dy)); nx,ny=-dy/length*width,dx/length*width
    mid=((start[0]+end[0])*.5,(start[1]+end[1])*.5)
    p.poly([start,(mid[0]+nx,mid[1]+ny),end,(mid[0]-nx*.5,mid[1]-ny*.5)],c[2])
    p.line([start,mid,end],c[4])


def render_special(p,f,c,j,m):
    x,y=32,35+j['bob']; stride=round(j['stride']*3); phase=j['phase']; back=j['back']
    if f=='mouse':
        # A compact mouse has large ears and fine feet. The field rat retains its longer torso.
        for dx in (-8,7):
            p.limb((x+dx,y+3),(x+dx+stride,y+13),2,c[2]); p.line([(x+dx+stride,y+13),(x+dx+stride+4,y+14)],'c49c92')
        p.line([(x-10,y+3),(x-21,y+5),(x-25,y-1),(x-21,y-7)],'be9a91',2)
        p.sphere((x-12,y-9,x+11,y+9),c[3]); hx=x+8 if j['side'] else x; hy=y-8
        p.sphere((hx-7,hy-5,hx+8,hy+7),c[3])
        for dx in (-5,5):
            p.sphere((hx+dx-5,hy-12,hx+dx+5,hy-2),c[3]); p.ellipse((hx+dx-2,hy-9,hx+dx+2,hy-4),'bb9890')
        if not back:
            p.poly([(hx-3,hy+3),(hx+5,hy+3),(hx+10,hy+8),(hx+2,hy+9)],c[4]); p.dot(hx+8,hy+7,'75504b'); eyes(p,hx,hy,c)
            for dy in (-1,2): p.line([(hx+8,hy+7),(hx+16,hy+5+dy)],c[1])
    elif f=='tick':
        # Eight short legs originate near the mouth rather than across a spider-sized span.
        for sign in (-1,1):
            for n in range(4):
                yy=y-10+n*3
                p.line([(x+sign*7,yy),(x+sign*(12+n),yy-6+stride),(x+sign*(15+n),yy-2)],c[1],2)
        p.sphere((x-15,y-7,x+15,y+22),c[3]); p.poly([(x-7,y-13),(x+7,y-13),(x+8,y-3),(x-8,y-3)],c[1])
        p.sphere((x-4,y-19,x+4,y-11),c[3]); p.line([(x-1,y-18),(x-2,y-24)],c[4]); p.line([(x+1,y-18),(x+3,y-23)],c[2])
        p.line([(x-8,y+3),(x-10,y+12),(x-5,y+18)],c[4]); p.line([(x+10,y+1),(x+11,y+14)],c[1])
    elif f=='leech':
        # A leech has a flattened annulated body and terminal suckers. It has no snake head or tongue.
        points=[(10+n*5,y+math.sin(n*.6+phase)*5) for n in range(9)]
        for n,(xx,yy) in enumerate(points):
            width=3 if n in {0,8} else 5 if n in {1,7} else 7
            p.sphere((xx-4,yy-width,xx+5,yy+width),c[2]); p.line([(xx+2,yy-width+2),(xx+2,yy+width-2)],c[0])
            p.line([(xx-2,yy-width+2),(xx+1,yy-width+1)],c[4])
        for xx,yy in (points[0],points[-1]): p.ellipse((xx-4,yy-3,xx+4,yy+3),c[3],INK); p.ellipse((xx-2,yy-1,xx+2,yy+1),c[0])
    elif f=='mudskipper':
        # Pectoral fins support a tapered fish body. No frog hind legs are present.
        p.poly([(15,y+1),(5,y-6),(3,y+12),(17,y+8)],c[2]); p.line([(6,y-1),(14,y+5)],c[4])
        p.sphere((12,y-6,48,y+12),c[3]); p.sphere((38,y-12,57,y+9),c[3])
        for yy in (y-8,y-1): p.poly([(23,yy),(32,yy-10),(38,yy)],c[2]); p.line([(25,yy),(32,yy-7)],c[4])
        for xx in (30,41): flipper(p,(xx,y+5),(xx-7+stride,y+21),5,c)
        for xx in (44,52): p.sphere((xx-4,y-19,xx+4,y-9),c[4]); p.dot(xx+1,y-14,INK)
        p.line([(46,y+5),(56,y+4)],c[0]); p.line([(19,y+2),(34,y+2)],c[4])
    elif f=='turtle':
        # A sea turtle has a low oval shell and long front flippers rather than a tortoise's short feet.
        for sign in (-1,1):
            flipper(p,(x+sign*10,y-5),(x+sign*28,y+8+stride),5,c)
            flipper(p,(x+sign*8,y+12),(x+sign*15,y+24-stride),3,c)
        p.poly([(29,y+16),(35,y+16),(32,y+26)],c[3]); p.sphere((18,y-16,46,y+19),c[3])
        p.poly([(26,y-12),(37,y-12),(42,y),(37,y+13),(26,y+13),(22,y)],c[2]); p.line([(27,y-10),(36,y-10),(40,y),(35,y+10),(28,y+10)],c[4])
        p.line([(32,y-11),(32,y+12)],c[0]); p.line([(23,y),(41,y)],c[1])
        p.limb((32,y-12),(32,y-22),5,c[3]); p.sphere((27,y-28,37,y-18),c[3]); eyes(p,32,y-24,c,back)
    elif f=='fungus':
        # A rooted colony carries several luminous fruiting bodies. It is not a walking humanoid cap.
        for dx in (-11,-4,5,13): p.line([(x,55),(x+dx,58+abs(dx)%3),(x+dx+4,61)],c[2],3)
        for xx,yy,rr in [(23,49,13),(40,42,16),(26,26,14)]:
            p.limb((32,55),(xx,yy-2),5,'b2ad8a')
            p.sphere((xx-rr,yy-rr,xx+rr,yy+2),c[3]); p.ellipse((xx-rr+1,yy-1,xx+rr-1,yy+5),'c7d0a0',INK)
            for dx in range(-rr+3,rr-1,4): p.line([(xx+dx,yy+1),(xx,yy+7)],'92ae89')
            p.line([(xx-rr+4,yy-rr+6),(xx-3,yy-rr+3)],c[5]); p.dot(xx+5,yy-6,'dbd6b4')
    elif f=='construct':
        # The hay golem uses tied rectangular straw bundles and branch joints, not a coat and hat.
        straw=palette('bca36c'); rope=palette('847353')
        for sign in (-1,1):
            p.limb((x+sign*7,43),(x+sign*11+stride*sign,59),5,rope[2])
            p.plank((x+sign*11-6+stride*sign,51,x+sign*11+6+stride*sign,61),straw[3])
            p.limb((x+sign*10,27),(x+sign*25,38-round(j['attack']*12)),4,'81714f')
            p.poly([(x+sign*24-5,31),(x+sign*24+5,32),(x+sign*26+3,44),(x+sign*24-6,43)],straw[2])
        p.rect((19,21,45,47),straw[2],INK); p.rect((22,9,42,24),straw[3],INK)
        for xx in range(22,44,4): p.line([(xx,24),(xx-1,44)],straw[4]); p.line([(xx+1,26),(xx,40)],straw[1])
        for yy in (28,40): p.line([(20,yy),(44,yy)],rope[1],3); p.line([(21,yy-1),(43,yy-1)],rope[4])
        for xx in (25,39): p.line([(xx,10),(xx,24)],rope[2],2)
        eyes(p,32,17,straw,back)
    elif f=='wisp':
        # A hollow thorn cage surrounds a suspended seed. Branches leave visible gaps.
        core=palette('b5c092'); thorn=palette('85765f')
        for sign in (-1,1):
            points=[(32,10),(32+sign*16,18),(32+sign*21,34),(32+sign*11,48),(32,55)]
            p.line(points,thorn[1],4); p.line(points,thorn[4],1)
            for xx,yy in points[1:-1]: p.poly([(xx,yy),(xx+sign*7,yy-7),(xx+sign*3,yy+2)],thorn[2])
        p.poly([(32,23),(38,30),(37,39),(32,44),(26,38),(26,29)],core[3]); p.line([(31,26),(29,31),(30,36)],core[5],2)
        p.line([(16,31),(27,35)],thorn[2],2); p.line([(37,33),(49,27)],thorn[3],2)
    elif f=='geode':
        # Two broken rock halves expose crystalline faces around a smaller inner spirit.
        rock=palette('8f887f')
        for sign in (-1,1):
            p.poly([(32+sign*8,13),(32+sign*21,20),(32+sign*25,35),(32+sign*19,49),(32+sign*8,55),(32+sign*14,34)],rock[2])
            for yy in (23,33,43): p.poly([(32+sign*13,yy-3),(32+sign*4,yy),(32+sign*15,yy+4)],c[4])
        p.sphere((28,24,37,35),'bdc9c2'); p.poly([(31,33),(35,33),(39,44),(32,49),(27,43)],c[3]); p.line([(29,27),(33,26)],c[5])
    elif f=='cuttle':
        # A cuttlefish has a long mantle, lateral fins, eight short arms, and two feeding tentacles.
        p.poly([(21,11),(14,23),(14,37),(23,42),(28,28)],c[2]); p.poly([(43,11),(50,23),(50,37),(42,42),(37,28)],c[2])
        p.sphere((22,6,43,38),c[3]); p.line([(27,10),(25,24),(28,34)],c[4]); p.sphere((24,32,41,43),c[2])
        for n in range(8):
            xx=23+n*2.5; sway=math.sin(phase+n)*3
            p.line([(xx,40),(xx+sway,49),(xx+(n-3.5)*1.5,55)],c[3 if n%2 else 4],2)
        for sign in (-1,1):
            p.line([(32+sign*6,41),(32+sign*17,53),(32+sign*24,57),(32+sign*20,63)],c[3],3)
            p.sphere((32+sign*20-2,58,32+sign*20+2,63),c[4])
        eyes(p,32,37,c,back)
    elif f=='hermit_crab':
        # A raised spiral shell sits behind the small exposed head and claws.
        for sign in (-1,1):
            for n in range(3): p.line([(32+sign*7,46+n*2),(32+sign*(16+n*2),48+n*3+stride),(32+sign*(19+n*2),56+n)],c[2],2)
        shell=palette('b69877'); p.poly([(15,42),(13,29),(19,12),(31,5),(45,15),(50,32),(44,47),(29,51)],shell[2])
        p.sphere((19,14,44,41),shell[3]); points=[]
        for i in range(54):
            a=i*.22; radius=11*(1-i/60); points.append((32+math.cos(a)*radius,27+math.sin(a)*radius))
        p.line(points,shell[0],2); p.line([(22,16),(31,11),(39,17)],shell[5])
        p.sphere((25,39,40,51),c[3]);
        for dx in (-3,4): p.limb((32+dx,42),(32+dx,34),2,c[3]); p.dot(32+dx,33,INK)
        for sign in (-1,1): p.limb((32+sign*5,48),(32+sign*16,54),3,c[2]); p.poly([(32+sign*14,50),(32+sign*22,45),(32+sign*21,53),(32+sign*26,49),(32+sign*22,59),(32+sign*14,58)],c[3])
    elif f=='wasp':
        # Separate thorax and abdomen form a narrow waist; paired translucent wings replace moth wings.
        wing=palette('bcc8bf')
        for sign in (-1,1):
            for yy,hh in [(24,16),(34,11)]:
                p.poly([(32+sign*3,yy),(32+sign*20,yy-hh),(32+sign*26,yy-hh+5),(32+sign*20,yy+4),(32+sign*6,yy+7)],wing[2]); p.line([(32+sign*5,yy),(32+sign*22,yy-hh+4)],wing[5])
            for n in range(3): p.line([(32+sign*4,28+n*5),(32+sign*(10+n),32+n*6+stride),(32+sign*(16+n),42+n*4)],c[0],2)
        p.sphere((27,22,37,34),c[3]); p.limb((32,33),(32,40),2,c[0]); p.sphere((26,38,38,55),c[3])
        for yy in (42,48,53): p.line([(27,yy),(37,yy)],c[0],2)
        p.poly([(30,53),(34,53),(32,62)],INK); p.sphere((27,13,37,23),c[3]); eyes(p,32,18,c,back)
        for sign in (-1,1): p.line([(32+sign*3,15),(32+sign*7,6),(32+sign*12,5)],c[2],2)
    elif f in {'pirate','harpy','djinn','phantom'}:
        # These bodies differ structurally. They do not reuse the generic NPC's silhouette.
        skin=palette('b79a81'); shoulder=24+j['bob']; hip=43+j['bob']
        if f=='harpy':
            for sign in (-1,1):
                p.poly([(32+sign*6,shoulder),(32+sign*21,14-stride),(32+sign*30,20),(32+sign*27,31),(32+sign*18,41)],c[2])
                for n in range(4): p.line([(32+sign*(12+n*4),23),(32+sign*(16+n*4),37-n*3)],c[4])
                p.limb((32+sign*5,hip),(32+sign*8+stride,54),3,'afa074')
                for n in range(3): p.line([(32+sign*8+stride,54),(32+sign*8+stride+(n-1)*4,60)],'d2bb8b',2)
            p.sphere((25,shoulder-1,39,hip),skin[3]); p.poly([(25,37),(39,37),(43,46),(31,43),(22,46)],c[2])
        elif f=='djinn':
            for n in range(5):
                width=17-n*3; yy=43+n*4; dx=round(math.sin(phase+n*.6)*(6-n))
                p.poly([(32+dx-width,yy),(32+dx,yy-3),(32+dx+width,yy),(32+dx+width-3,yy+3),(32+dx-width+3,yy+3)],c[2 if n%2 else 3]); p.line([(32+dx-width+3,yy),(32+dx+width-3,yy)],c[4])
            p.sphere((23,shoulder-3,42,44),c[3])
        elif f=='phantom':
            for dx,dy in [(-6,0),(5,3),(-9,15),(6,18),(0,31)]:
                xx,yy=32+dx,shoulder+dy
                p.poly([(xx-5,yy-4),(xx+4,yy-7),(xx+6,yy+2),(xx,yy+6),(xx-6,yy+3)],c[2]); p.line([(xx-3,yy-3),(xx+2,yy-5),(xx+3,yy)],c[5])
        else:
            for sign in (-1,1): p.limb((32+sign*5,hip),(32+sign*7+stride*sign,57),4,'716b6b'); p.poly([(32+sign*7+stride*sign-3,55),(32+sign*7+stride*sign+6,55),(32+sign*7+stride*sign+6,60),(32+sign*7+stride*sign-4,60)],'66503c')
            p.poly([(23,shoulder),(41,shoulder),(42,47),(35,50),(32,43),(27,50),(21,46)],'786d79'); p.line([(26,shoulder+2),(29,42)],'c7a36e',2); p.line([(38,shoulder+2),(35,42)],'c7a36e',2); p.rect((22,39,41,42),'85603e',INK)
        if f!='harpy':
            for sign in (-1,1): p.limb((32+sign*9,shoulder+2),(32+sign*18,39-round(j['attack']*12)),4,c[3] if f!='pirate' else '786d79')
        p.sphere((26,8+j['bob'],39,23+j['bob']),skin[3] if f in {'pirate','harpy'} else c[3]); eyes(p,32,16+j['bob'],skin if f in {'pirate','harpy'} else c,back)
        if f=='pirate':
            p.poly([(24,12),(28,5),(40,6),(43,13),(39,16),(26,15)],'a38666'); p.line([(25,12),(42,12)],'c6a882'); p.line([(28,14),(37,20)],INK,2)
            p.line([(47,38),(51,30),(54,16)],'c5cbc4',3); p.line([(53,16),(51,9)],'e3dfbe',2); p.line([(44,37),(52,40)],'b59b62',2)
        elif f=='harpy': p.poly([(26,9),(22,2),(31,7),(34,1),(40,9)],c[2])
        elif f=='djinn': p.sphere((24,5,41,14),'b8a273'); p.line([(26,8),(39,8)],'e1d0a2',2); p.sphere((31,8,35,12),'9fbeb8')
        else: p.line([(30,10),(33,15),(30,20)],'e4e1d4'); p.poly([(23,8),(20,14),(18,7)],c[4])
    elif f=='automaton':
        metal=palette('a89568')
        for sign in (-1,1):
            for n in range(4):
                a=(32+sign*7,24+n*5); b=(32+sign*(18+n%2*4),17+n*7+stride); end=(32+sign*(24-n%2),30+n*7)
                p.limb(a,b,2,metal[2]); p.limb(b,end,2,metal[3]); p.sphere((b[0]-2,b[1]-2,b[0]+2,b[1]+2),metal[4]); p.dot(b[0],b[1],metal[0])
        p.poly([(25,18),(39,18),(45,30),(42,46),(23,46),(19,31)],metal[2]); p.line([(25,21),(38,21),(41,30)],metal[5]); p.rect((26,36,39,42),metal[0]); p.line([(28,38),(31,40),(36,37)],'c3d9c6')
        p.sphere((25,23,39,36),'789f9e'); p.sphere((29,26,36,33),'c6d9c5'); p.dot(32,29,INK)
    else:
        # Retain an appropriate base skeleton, then add the species' actual structural traits.
        if f in base.QUADRUPEDS: base.quadruped(p,f,c,j,m)
        elif f in base.INSECTS: base.insect(p,f,c,j,m)
        elif f in base.BIRDS: base.bird(p,f,c,j,m)
        elif f in base.STONES: base.construct(p,f,c,j,m)
        elif f in base.SHELLS: base.shell(p,f,c,j,m)
        elif f in base.TUBES: base.tube(p,f,c,j,m)
        elif f in base.AQUATICS: base.aquatic(p,f,c,j,m)
        else: raise ValueError('Missing refined skeleton for '+f)
        if f=='polar_bear':
            # Raised long neck and compact ears distinguish its profile from the black bear.
            p.limb((43,y-4),(51,y-20),10,c[3]); p.sphere((46,y-27,60,y-13),c[3]); p.poly([(55,y-19),(63,y-16),(61,y-12),(54,y-13)],c[3]); p.sphere((46,y-30,51,y-25),c[3]); p.dot(57,y-20,INK); p.dot(62,y-15,INK)
        elif f=='wolf':
            p.poly([(32,y-14),(38,y-22),(43,y-18),(48,y-22),(49,y-12),(45,y-4),(37,y-3)],c[3]); p.line([(39,y-17),(43,y-11),(39,y-8)],c[4]); p.line([(7,y-4),(5,y+5),(9,y+13)],c[2],5)
        elif f=='stag':
            hx,hy=(45,y-15) if j['side'] else (32,y-3 if not back else y-19)
            for sign in (-1,1):
                p.line([(hx+sign*7,hy-10),(hx+sign*16,hy-19),(hx+sign*18,hy-27)],'c4b28d',2)
                p.line([(hx+sign*14,hy-17),(hx+sign*8,hy-25)],'c4b28d',2)
                p.line([(hx+sign*14,hy-17),(hx+sign*22,hy-19)],'9d936f',2)
                p.line([(hx+sign*12,hy-17),(hx+sign*11,hy-6),(hx+sign*14,hy-3)],'7f9668',2)
        elif f=='spore_moth':
            for xx,yy in [(8,y-11),(15,y+17),(53,y-9),(47,y+17)]:
                p.rect((xx-1,yy-3,xx+1,yy+4),'b2aa89'); p.sphere((xx-5,yy-7,xx+5,yy-1),'aa8c91'); p.line([(xx-3,yy-1),(xx+3,yy-1)],'d0c89b')
        elif f in {'fire_beetle','scarab'}:
            if f=='fire_beetle':
                p.poly([(25,y+8),(21,y+21),(28,y+27),(36,y+27),(43,y+20),(38,y+7)],c[2]);
                for yy in (y+13,y+19,y+24): p.line([(27,yy),(37,yy)],'d9ae72',2)
            else:
                p.poly([(24,y-16),(19,y-26),(26,y-24),(29,y-30),(32,y-26),(35,y-30),(39,y-24),(45,y-26),(41,y-16)],c[3]); p.line([(24,y-23),(32,y-21),(41,y-23)],'d9c28c',2)
        elif f=='frog':
            for sign in (-1,1):
                xx=x+sign*17
                for n in range(3):
                    tx=xx+sign*(n*3); ty=y+18+n%2*3
                    p.line([(xx,y+12),(tx,ty)],c[4],2); p.sphere((tx-2,ty-2,tx+2,ty+2),'b8c78b')
            p.poly([(22,y-7),(19,y-15),(23,y-18),(28,y-7)],c[2])
        elif f in {'skimmer','gull','vulture'}:
            if f=='skimmer':
                p.poly([(35,y-15),(60,y-12),(40,y-9)],'c4a674'); p.poly([(35,y-10),(62,y-7),(37,y-6)],'9a7758'); p.poly([(27,y+13),(20,y+27),(32,y+19),(43,y+28),(37,y+12)],c[2])
            elif f=='gull':
                for sign in (-1,1): p.poly([(32+sign*19,y-11),(32+sign*30,y-19),(32+sign*27,y+2),(32+sign*20,y+11)],'747b7e'); p.line([(32+sign*21,y-9),(32+sign*27,y-14)],'dce0ca')
                p.poly([(27,y+19),(32,y+25),(38,y+18)],'d1d3bd')
            else:
                p.limb((32,y-8),(35,y-23),5,'b59a84'); p.sphere((30,y-30,42,y-19),'b89b87'); p.poly([(39,y-23),(48,y-20),(44,y-15),(39,y-18)],'a99469'); p.ellipse((24,y-15,41,y-5),'c5bca0',INK); p.dot(38,y-25,INK)
        elif f=='crab':
            crystal(p,32,y-8,22,'b7cdd3'); p.poly([(7,y-9),(1,y-22),(8,y-21),(11,y-15),(17,y-21),(17,y-10),(11,y-3)],c[3]); p.line([(5,y-19),(9,y-15)],c[5],2)
        elif f=='worm':
            for n in range(6):
                xx=16+n*5; yy=34+math.sin(n*.7+phase)*8
                for sign in (-1,1): p.poly([(xx-2,yy+sign*4),(xx,yy+sign*12),(xx+3,yy+sign*4)],'b4cdd3'); p.line([(xx,yy+sign*5),(xx,yy+sign*10)],'e0e5d1')
        elif f=='sentinel':
            for sign in (-1,1): p.poly([(32+sign*11,19),(32+sign*25,12),(32+sign*28,21),(32+sign*15,27)],'9ba8b7'); p.line([(32+sign*14,20),(32+sign*24,15)],'d4d7c3')
            p.d.ellipse((17,3,47,16),outline=(186,199,212,255),width=2); p.d.arc((7,25,57,46),10,165,fill=(171,185,210,255),width=2)
        elif f=='elemental':
            for xx,yy in [(12,35),(49,39),(25,10),(41,13)]: crystal(p,xx,yy,18,'b9d3d4')
            p.poly([(23,51),(18,62),(30,56),(37,61),(43,53)],'9ab9c8')
        elif f=='guardian':
            for sign in (-1,1):
                stone(p,32+sign*12,62,19,12,'a39e89')
                p.poly([(32+sign*10,20),(32+sign*23,17),(32+sign*25,28),(32+sign*12,29)],c[2]); p.line([(32+sign*12,23),(32+sign*22,22)],c[5])
            p.rect((27,3,37,10),c[2],INK); p.line([(29,5),(35,5)],c[4]); p.poly([(7,20),(10,20),(10,48),(7,56),(4,48),(4,20)],'b0aca0'); p.line([(3,39),(12,39)],c[1],2)


def frame(definition,state,number,direction):
    family=definition['family']
    if family not in REFINED: return existing_frame(definition,state,number,direction)
    image=canvas(); p=Pixel(image); pose=animation_pose(state,number,direction)
    pose.update(phase=number/8*math.tau,state=state,frame=number)
    colours=palette(base.body_colour(definition))
    render_special(p,family,colours,pose,definition)
    if definition.get('elite'):
        p.line([(23,27),(29,36)],'bdac8a',2); p.line([(24,27),(30,36)],colours[0])
    if direction==1: image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    image=finish_frame(image,state,number,direction)
    if definition.get('boss'):
        # Size is a rendering choice, not approval of a boss's unique design.
        image=image.resize((128,128),Image.Resampling.NEAREST)
    return image
