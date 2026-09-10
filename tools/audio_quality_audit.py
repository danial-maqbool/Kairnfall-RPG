#!/usr/bin/env python3
"""Measure shipped WAV files. This does not approve perceived mix or music quality."""
from __future__ import annotations
import argparse
import array
import json
import math
from pathlib import Path
import sys
import wave

ROOT=Path(__file__).resolve().parents[1]
MUSIC=('menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss')
AMBIENT=('forest','coast','wind','cave')
EFFECT=('sword','spell','gather','coins','hammer','equip','drink','ui')
EXPECTED=tuple('music_'+x for x in MUSIC)+tuple('ambient_'+x for x in AMBIENT)+tuple('effect_'+x for x in EFFECT)


def read_pcm(path:Path):
    with wave.open(str(path),'rb') as stream:
        channels=stream.getnchannels(); width=stream.getsampwidth(); rate=stream.getframerate(); frames=stream.getnframes(); compression=stream.getcomptype()
        raw=stream.readframes(frames)
    if width!=2: return channels,width,rate,frames,compression,[]
    values=array.array('h'); values.frombytes(raw)
    if sys.byteorder!='little': values.byteswap()
    return channels,width,rate,frames,compression,[value/32768.0 for value in values]


def metrics(path:Path):
    channels,width,rate,frames,compression,samples=read_pcm(path)
    if not samples: return {'file':path.name,'channels':channels,'sample_width':width,'sample_rate':rate,'frames':frames,'compression':compression}
    peak=max(abs(value) for value in samples)
    rms=math.sqrt(sum(value*value for value in samples)/len(samples))
    dc=sum(samples)/len(samples)
    clipped=sum(1 for value in samples if abs(value)>=32767/32768)/len(samples)
    edge=min(max(1,rate//20),len(samples)//2)
    seam=sum(abs(samples[index]-samples[-edge+index]) for index in range(edge))/edge
    return {'file':path.name,'channels':channels,'sample_width':width,'sample_rate':rate,'frames':frames,'compression':compression,
        'duration_seconds':frames/rate if rate else 0,'peak':peak,'rms':rms,'dc_offset':dc,'clipped_fraction':clipped,'loop_edge_mean_difference':seam}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--audio-root',type=Path,default=ROOT/'client/Assets/audio'); parser.add_argument('--output',type=Path,default=ROOT/'artifacts/audio/audio-quality.json'); args=parser.parse_args()
    root=args.audio_root.resolve(); output=args.output.resolve(); output.parent.mkdir(parents=True,exist_ok=True)
    errors=[]; rows=[]
    found={path.stem for path in root.glob('*.wav')}
    missing=sorted(set(EXPECTED)-found); unexpected=sorted(found-set(EXPECTED))
    if missing: errors.append('Missing audio: '+', '.join(missing))
    if unexpected: errors.append('Unexpected audio: '+', '.join(unexpected))
    for key in EXPECTED:
        path=root/(key+'.wav')
        if not path.exists(): continue
        row=metrics(path); rows.append(row)
        if row.get('channels')!=1: errors.append(key+': expected mono PCM')
        if row.get('sample_width')!=2: errors.append(key+': expected 16-bit PCM')
        if row.get('sample_rate')!=22050: errors.append(key+': expected 22050 Hz')
        if row.get('compression')!='NONE': errors.append(key+': compressed WAV is not supported')
        if 'rms' not in row: continue
        duration=row['duration_seconds']; prefix=key.split('_',1)[0]
        lo,hi={'music':(15,30),'ambient':(10,20),'effect':(.15,.6)}[prefix]
        if not lo<=duration<=hi: errors.append(f'{key}: duration {duration:.3f}s outside {lo}-{hi}s')
        if not .03<=row['peak']<=.95: errors.append(f'{key}: peak {row["peak"]:.4f} is out of range')
        if not .002<=row['rms']<=.50: errors.append(f'{key}: RMS {row["rms"]:.5f} is out of range')
        if abs(row['dc_offset'])>.03: errors.append(f'{key}: DC offset {row["dc_offset"]:.5f} is too large')
        if row['clipped_fraction']>.0005: errors.append(f'{key}: clipped fraction {row["clipped_fraction"]:.6f} is too large')
        if prefix in {'music','ambient'} and row['loop_edge_mean_difference']>.20:
            errors.append(f'{key}: loop boundary mean difference {row["loop_edge_mean_difference"]:.4f} is too large')
    report={'expected_files':len(EXPECTED),'measured_files':len(rows),'human_listening_approved':False,'checks':rows,'errors':errors}
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if rows:
        print(f'AUDIO_QUALITY: measured {len(rows)} WAV files; peak {min(r["peak"] for r in rows if "peak" in r):.3f}-{max(r["peak"] for r in rows if "peak" in r):.3f}; technical errors {len(errors)}.')
    print('AUDIO_QUALITY: automated format, level, clipping and loop-boundary checks do not approve perceived mix, transitions, or artistic quality.')
    if errors:
        for error in errors: print('AUDIO ERROR:',error)
        raise SystemExit(1)

if __name__=='__main__': main()
