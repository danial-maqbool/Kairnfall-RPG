from __future__ import annotations
import hashlib
import math
from pathlib import Path
from PIL import Image, ImageDraw

INK=(25,24,32,255)
STATES=('idle','walk','attack','cast','hit','death')
DIRECTIONS=('south','west','east','north')
FRAMES=8


def rgba(value):
    if isinstance(value,str):
        text=value.lstrip('#')
        return tuple(int(text[i:i+2],16) for i in (0,2,4))+(255,)
    return tuple(value)+(255,) if len(value)==3 else tuple(value)


def shade(color,factor=1.0,offset=0):
    c=rgba(color)
    return tuple(max(0,min(255,round(v*factor+offset))) for v in c[:3])+(c[3],)


def mix(a,b,t):
    a,b=rgba(a),rgba(b)
    return tuple(round(a[i]*(1-t)+b[i]*t) for i in range(4))


def seed(text): return int.from_bytes(hashlib.sha256(text.encode()).digest()[:4],'little')


def palette(base): return [shade(base,.42),shade(base,.63),shade(base,.82),rgba(base),shade(base,1.12,8),shade(base,1.25,14)]


class Pixel:
    def __init__(self,image): self.image=image; self.d=ImageDraw.Draw(image)
    @staticmethod
    def p(points): return [(round(x),round(y)) for x,y in points]
    @staticmethod
    def box(box):
        x0,y0,x1,y1=map(round,box)
        return min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)
    def rect(self,box,color,outline=None,width=1): self.d.rectangle(self.box(box),fill=rgba(color),outline=rgba(outline) if outline else None,width=width)
    def ellipse(self,box,color,outline=None,width=1): self.d.ellipse(self.box(box),fill=rgba(color),outline=rgba(outline) if outline else None,width=width)
    def poly(self,points,color,outline=INK): self.d.polygon(self.p(points),fill=rgba(color),outline=rgba(outline) if outline else None)
    def line(self,points,color,width=1): self.d.line(self.p(points),fill=rgba(color),width=width,joint='curve')
    def dot(self,x,y,color): self.d.point((round(x),round(y)),fill=rgba(color))
    def sphere(self,box,base):
        x0,y0,x1,y1=box; w=x1-x0; h=y1-y0; colors=palette(base)
        self.ellipse(box,colors[1],INK)
        self.ellipse((x0+1,y0+1,x1-1,y1-2),colors[2])
        self.ellipse((x0+1,y0+1,x0+w*.82,y0+h*.76),colors[3])
        self.ellipse((x0+w*.15,y0+h*.12,x0+w*.6,y0+h*.38),colors[4])
        if w>=10: self.line([(x0+w*.2,y0+h*.16),(x0+w*.42,y0+h*.12)],colors[5])
    def limb(self,a,b,width,base):
        colors=palette(base)
        self.line([a,b],INK,width+2)
        self.line([a,b],colors[1],width)
        self.line([(a[0]-1,a[1]),(b[0]-1,b[1])],colors[3],max(1,width-2))
        if width>=5: self.line([(a[0]-2,a[1]),(b[0]-2,b[1])],colors[4],1)
    def plank(self,box,base):
        x0,y0,x1,y1=box; colors=palette(base)
        self.rect(box,colors[2],colors[0]); self.line([(x0+1,y0+1),(x1-1,y0+1)],colors[4]); self.line([(x0+2,y1-1),(x1-1,y1-1)],colors[1])
        for y in range(round(y0)+3,round(y1),4): self.line([(x0+3,y),(x1-3,y-1)],colors[1])
        self.dot(x0+2,y0+2,colors[5]); self.dot(x1-2,y1-2,colors[0])


def canvas(size=(64,64)): return Image.new('RGBA',size,(0,0,0,0))


def animation_pose(state,frame,direction):
    t=frame/FRAMES*math.tau
    stride=math.sin(t) if state=='walk' else 0
    bob=round(abs(math.sin(t))*1.2) if state=='walk' else (1 if state=='idle' and frame>=4 else 0)
    attack=math.sin(frame/(FRAMES-1)*math.pi) if state=='attack' else 0
    cast=math.sin(frame/(FRAMES-1)*math.pi) if state=='cast' else 0
    return dict(stride=stride,bob=bob,attack=attack,cast=cast,side=direction in (1,2),back=direction==3,left=direction==1)


def finish_frame(image,state,frame,direction):
    if state=='hit' and frame in (1,2):
        overlay=Image.new('RGBA',image.size,(245,224,194,0)); overlay.putalpha(image.getchannel('A').point(lambda a:round(a*.42)))
        image=Image.alpha_composite(image,overlay)
    if state=='death':
        angle=min(90,frame*15)
        image=image.rotate(-angle,resample=Image.Resampling.NEAREST,center=(image.width/2,image.height*.64))
        if frame>5:
            image.putalpha(image.getchannel('A').point(lambda a:round(a*(1-(frame-5)*.15))))
    return image


def sheet(draw_frame,size=64):
    result=canvas((size*FRAMES,size*len(STATES)*len(DIRECTIONS)))
    for state_index,state in enumerate(STATES):
        for direction in range(4):
            for frame in range(FRAMES):
                image=draw_frame(state,frame,direction)
                if image.size!=(size,size): raise ValueError('Sprite frame has the wrong dimensions.')
                result.alpha_composite(image,(frame*size,(state_index*4+direction)*size))
    return result


def save(image,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,optimize=True,compress_level=9)


METALS={
 'copper':'b87543','iron':'87919b','steel':'b1c1c8','silver':'d1d9dc','cobalt':'6b94b0','mithril':'97c6c1','obsidian':'746b85','aetherium':'b9c3e0',
 'gold':'c9a557','bronze':'a48a57','metal':'a6b1bb','wood_metal':'9ca8ad'}
WOODS={'oak':'97704a','ash':'b08a56','yew':'8f6048','ironwood':'635d50','blackwood':'504b55','elderwood':'ae9867','emberwood':'955546','starwood':'a4a7bb','wood':'96724f'}
ELEMENT_COLORS={'Physical':'c3b6a2','Fire':'dc8053','Frost':'92c9d1','Lightning':'e0ca65','Nature':'83a768','Poison':'abc56b','Arcane':'ae9ccf','Radiant':'e7d6a0','Shadow':'8a78aa'}
