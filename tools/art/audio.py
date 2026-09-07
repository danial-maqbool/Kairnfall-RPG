"""Original synthesized music, ambience, and effects. No sampled recordings."""
from __future__ import annotations
import hashlib
import math
import wave
from pathlib import Path
import numpy as np

RATE = 22050
MUSIC = {
    'menu': (76, 50, [0,3,7,10,7,5,3,2,0,5,7,12,10,7,5,3], [0,5,3,7], 'lute'),
    'wayfarers_rest': (88, 55, [0,2,4,7,9,7,4,2,0,4,5,9,7,5,4,2], [0,5,7,0], 'lute'),
    'dawnreach': (84, 53, [0,4,7,12,11,9,7,4,5,9,12,14,12,9,7,4], [0,5,9,7], 'bell'),
    'emberhold': (78, 50, [0,0,7,5,3,2,0,-2,0,3,5,7,10,7,5,3], [0,3,5,7], 'metal'),
    'thornhollow': (72, 57, [0,3,5,7,10,7,5,3,2,5,9,12,10,9,7,5], [0,5,7,3], 'flute'),
    'frostgate': (64, 52, [0,7,10,12,10,7,3,2,0,3,7,5,3,2,-2,0], [0,3,5,0], 'bowed'),
    'gloamport': (94, 48, [0,4,7,10,7,4,2,5,9,7,5,2,0,4,2,0], [0,5,7,5], 'lute'),
    'wilderness': (82, 52, [0,3,7,5,9,7,3,2,0,5,7,10,9,7,5,2], [0,5,3,7], 'flute'),
    'dungeon': (58, 48, [0,7,3,2,0,-2,3,7,5,3,2,0,-2,0,2,3], [0,3,1,0], 'bowed'),
    'boss': (116, 50, [0,0,7,10,7,5,3,2,0,3,7,12,10,7,5,2], [0,3,5,7], 'metal')
}
AMBIENCE = ('forest', 'coast', 'cave', 'wind')
EFFECTS = ('sword','spell','gather','coins','hammer','equip','drink','ui','step_grass','step_stone','step_wood','step_snow')


def rng(name):
    value=int.from_bytes(hashlib.sha256(name.encode()).digest()[:8],'little')
    return np.random.Generator(np.random.PCG64(value))


def lowpass(signal, width):
    width=max(1,int(width)); sums=np.cumsum(np.pad(signal,(width,0)))
    return (sums[width:]-sums[:-width])/width


def note(midi, seconds, instrument='lute'):
    n=max(1,round(seconds*RATE)); t=np.arange(n,dtype=np.float64)/RATE; f=440*2**((midi-69)/12)
    phase=math.tau*f*t
    if instrument=='flute':
        wave=np.sin(phase+.022*np.sin(math.tau*5*t))+.12*np.sin(phase*2)+.035*np.sin(phase*3)
        envelope=np.minimum(1,t/.07)*np.minimum(1,(seconds-t)/.15)
    elif instrument=='bowed':
        wave=np.sin(phase)+.16*np.sin(phase*2)+.09*np.sin(phase*3)+.035*np.sin(phase*5)
        envelope=np.minimum(1,t/.22)*np.minimum(1,(seconds-t)/.28)
    elif instrument in {'bell','metal'}:
        wave=np.sin(phase)*np.exp(-t*2.2)+.34*np.sin(phase*2.01)*np.exp(-t*4)+.15*np.sin(phase*3.97)*np.exp(-t*6)
        envelope=np.minimum(1,t/.004)*np.minimum(1,(seconds-t)/.06)
    else:
        wave=np.sin(phase)+.32*np.sin(phase*2)*np.exp(-t*4)+.14*np.sin(phase*3)*np.exp(-t*6)+.05*np.sin(phase*5)*np.exp(-t*9)
        envelope=(1-np.exp(-t*220))*np.exp(-t*3.1)*np.minimum(1,(seconds-t)/.04)
    return wave*np.clip(envelope,0,1)


def add(buffer, sound, start, volume=.2, pan=0):
    offset=round(start*RATE); first=max(0,offset); end=min(len(buffer),offset+len(sound))
    if first>=end:return
    source=sound[first-offset:end-offset]
    pan=float(np.clip(pan,-1,1));buffer[first:end,0]+=source*volume*math.sqrt((1-pan)/2);buffer[first:end,1]+=source*volume*math.sqrt((1+pan)/2)


def drum(seconds=.22, seed_name='drum'):
    t=np.arange(round(seconds*RATE))/RATE
    noise=rng(seed_name).normal(0,1,len(t));body=np.sin(math.tau*(95*t-45*t*t))*np.exp(-t*20)
    return body+.19*lowpass(noise,5)*np.exp(-t*35)


def music(name):
    bpm,root,melody,chords,instrument=MUSIC[name]; beat=60/bpm;duration=32*beat
    result=np.zeros((round(duration*RATE),2),dtype=np.float64)
    minor=name not in {'wayfarers_rest','dawnreach','gloamport'};third=3 if minor else 4
    for bar in range(8):
        chord=root+chords[bar%len(chords)]
        add(result,note(chord-12,beat*3.9,'bowed'),bar*4*beat,.12,-.08)
        for step in range(8):
            degree=(0,7,12,third+12,7,12,third+12,7)[step]
            add(result,note(chord+degree,beat*.95,'lute'),(bar*4+step*.5)*beat,.14,(-.45 if step%2 else .4))
        for step in range(2):
            pitch=root+12+melody[(bar*2+step)%len(melody)]
            add(result,note(pitch,beat*1.8,instrument),(bar*4+step*2)*beat,.18,.15)
        if name not in {'dungeon','frostgate'}:
            for step in (0,2):add(result,drum(seed_name=name+str(bar)+str(step)),(bar*4+step)*beat,.1 if name!='boss' else .2,-.2)
        if name in {'boss','emberhold','gloamport'}:
            for step in (1,3):
                hit=rng(name+'shaker'+str(bar)+str(step)).normal(0,.3,round(RATE*.09))*np.exp(-np.arange(round(RATE*.09))/RATE*35)
                add(result,hit,(bar*4+step)*beat,.07,.5)
    dry=result.copy()
    for delay,gain in ((.17,.12),(.31,.08),(.47,.045)):
        shift=round(delay*RATE);result+=np.roll(dry,shift,axis=0)*gain
    return finish(result,.66)


def ambience(name):
    duration=24;count=duration*RATE;t=np.arange(count)/RATE;random=rng('ambient_'+name)
    noise=random.normal(0,1,count);soft=lowpass(noise,100);soft/=max(.001,float(np.std(soft)))
    result=np.zeros((count,2),dtype=np.float64)
    if name=='coast':
        swell=.22+.3*(.5+.5*np.sin(math.tau*.105*t))**2
        base=soft*swell+lowpass(noise,8)*(.04+.08*(.5+.5*np.sin(math.tau*.105*t+.8)))
    elif name=='cave':base=soft*.12+np.sin(math.tau*63*t)*.025
    elif name=='forest':base=soft*(.1+.035*np.sin(math.tau*.08*t))
    else:base=soft*(.16+.08*np.sin(math.tau*.055*t))
    result[:,0]=base;result[:,1]=np.roll(base,127)*.94
    if name=='forest':
        for i,start in enumerate((1.7,4.8,8.2,13.1,17.3,20.8)):
            seconds=.38;tt=np.arange(round(seconds*RATE))/RATE
            call=np.sin(math.tau*(1100*tt+550*tt*tt)+.7*np.sin(math.tau*12*tt))*np.sin(math.pi*tt/seconds)**2
            add(result,call,start,.045,(i%3-1)*.6)
    if name=='cave':
        for i,start in enumerate((2.4,6.3,11.7,16.2,21.2)):
            sound=note(82+i%3, .6, 'bell');add(result,sound,start,.045,(i%3-1)*.5);add(result,sound,start+.21,.014,0)
    return finish(result,.38)


def effect(name):
    duration={'sword':.38,'spell':.85,'gather':.30,'coins':.6,'hammer':.45,'equip':.3,'drink':.6,'ui':.16}.get(name,.2)
    count=round(duration*RATE);t=np.arange(count)/RATE;random=rng('effect_'+name);noise=random.normal(0,1,count);mono=np.zeros(count)
    if name=='sword':
        mono=lowpass(noise,4)*np.sin(math.pi*np.minimum(t/.19,1))**2*.5
        at=t-.14;mask=at>=0;mono[mask]+=(np.sin(math.tau*1510*at[mask])+.3*np.sin(math.tau*2300*at[mask]))*np.exp(-at[mask]*30)*.2
    elif name=='spell':mono=np.sin(math.tau*(380*t+450*t*t))*np.sin(math.pi*t/duration)**2*.4+lowpass(noise,12)*np.exp(-t*3)*.15
    elif name=='coins':
        for start,pitch in ((0,106),(.13,111),(.29,103)):
            sound=note(pitch,duration-start,'metal');offset=round(start*RATE);mono[offset:offset+min(len(sound),count-offset)]+=sound[:count-offset]*.3
    elif name in {'gather','hammer'}:
        mono=np.sin(math.tau*(130*t-60*t*t))*np.exp(-t*24)+lowpass(noise,4)*np.exp(-t*42)*.35
        if name=='hammer':mono+=np.sin(math.tau*1350*t)*np.exp(-t*15)*.18
    elif name=='equip':mono=lowpass(noise,9)*np.exp(-t*17)*.6+np.sin(math.tau*1900*t)*np.exp(-t*36)*.09
    elif name=='drink':
        for start in (0,.13,.29):
            at=t-start;mask=(at>=0)&(at<.17);mono[mask]+=np.sin(math.tau*(360*at[mask]+1000*at[mask]**2))*np.exp(-at[mask]*24)*.35
    elif name=='ui':mono=note(81,duration,'lute')*.4
    else:
        width={'step_grass':6,'step_stone':2,'step_wood':14,'step_snow':5}.get(name,8)
        mono=lowpass(noise,width)*np.exp(-t*32)*.65+np.sin(math.tau*105*t)*np.exp(-t*36)*.2
    result=np.column_stack((mono,mono*.97));return finish(result,.65)


def finish(signal, peak):
    if not np.isfinite(signal).all():raise ValueError('Nonfinite audio sample.')
    maximum=float(np.max(np.abs(signal)))
    if maximum>0:signal=signal*(peak/maximum)
    count=min(round(.012*RATE),len(signal)//2)
    if count:
        ramp=np.linspace(0,1,count);signal[:count]*=ramp[:,None];signal[-count:]*=ramp[::-1,None]
    return np.clip(signal,-.95,.95)


def write_wav(path:Path, signal):
    path.parent.mkdir(parents=True,exist_ok=True)
    pcm=np.rint(signal*32767).astype('<i2')
    with wave.open(str(path),'wb') as output:
        output.setnchannels(2);output.setsampwidth(2);output.setframerate(RATE);output.writeframes(pcm.tobytes())


def build_audio(output:Path):
    written=[]
    for name in MUSIC:
        path=output/('music_'+name+'.wav');write_wav(path,music(name));written.append(path)
    for name in AMBIENCE:
        path=output/('ambient_'+name+'.wav');write_wav(path,ambience(name));written.append(path)
    for name in EFFECTS:
        path=output/('effect_'+name+'.wav');write_wav(path,effect(name));written.append(path)
    return written
