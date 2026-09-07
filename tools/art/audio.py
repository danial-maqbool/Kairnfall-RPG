"""Original short synthesized cues and ambience. Not sampled third-party music."""
from __future__ import annotations
import math
from pathlib import Path
import random
import struct
import wave
from .common import seed

RATE=22050

def write(path: Path,samples):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(RATE)
        out.writeframes(b''.join(struct.pack('<h',round(max(-.95,min(.95,value))*32767)) for value in samples))

def tune(name: str):
    notes=[0,7,12,3,10,7,5,3,0,7,15,12,10,5,7,0]
    keys={'menu':146.83,'wayfarers_rest':164.81,'dawnreach':196,'emberhold':130.81,'thornhollow':174.61,'frostgate':146.83,'gloamport':155.56,'wilderness':164.81,'dungeon':110,'boss':130.81}
    root=keys.get(name,146.83); beat=.32 if name=='boss' else .55; length=16*beat
    for n in range(round(length*RATE)):
        t=n/RATE; phase=t%beat; ix=int(t/beat)%16; freq=root*2**(notes[ix]/12)
        attack=min(1,phase/.01); decay=math.exp(-phase*7)
        pluck=(math.sin(math.tau*freq*t)+.22*math.sin(math.tau*freq*2*t)+.07*math.sin(math.tau*freq*3*t))*.15*attack*decay
        pad=math.sin(math.tau*root*.5*t)*.025*min(1,t/.1,(length-t)/.1)
        yield pluck+pad

def build(root: Path,data: dict):
    music={'menu','wayfarers_rest','wilderness','dungeon','boss'}|{z['id'] for z in data['zones'] if z['kind']=='city'}
    for name in sorted(music): write(root/('music_'+name+'.wav'),tune(name))
    for name in ('forest','coast','cave','wind'):
        rng=random.Random(seed(name)); smooth=0; samples=[]; length=8
        for n in range(RATE*length):
            t=n/RATE; smooth=.985*smooth+.015*rng.uniform(-1,1); amplitude=.035*(.7+.3*math.sin(t*.8))
            value=smooth*amplitude
            if name=='forest' and t%2.5<.22: value+=math.sin(math.tau*(1600+math.sin(t*35)*160)*t)*.018*math.sin(t%2.5/.22*math.pi)
            if name=='coast': value+=smooth*.10*(.5+.5*math.sin(t*1.2))
            value*=min(1,t/.1,(length-t)/.1); samples.append(value)
        write(root/('ambient_'+name+'.wav'),samples)
    for name,freq in [('sword',230),('spell',680),('gather',180),('coins',1350),('hammer',150),('equip',370),('drink',450),('ui',800)]:
        rng=random.Random(seed(name)); values=[]
        for n in range(round(RATE*.28)):
            t=n/RATE; envelope=min(1,t/.005)*math.exp(-t*22)
            metallic=math.sin(math.tau*freq*t)+.3*math.sin(math.tau*freq*2.76*t)
            noise=rng.uniform(-1,1)*(.7 if name in {'sword','gather','hammer'} else .05)
            values.append((metallic*.12+noise*.10)*envelope)
        write(root/('effect_'+name+'.wav'),values)
