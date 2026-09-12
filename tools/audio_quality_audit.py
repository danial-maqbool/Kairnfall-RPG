#!/usr/bin/env python3
"""Measure shipped WAV files. Automated checks never approve perceived mix, composition, transitions, or artistic quality."""
from __future__ import annotations
import argparse,array,hashlib,json,math,sys,wave
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MUSIC=('menu','dawnreach','emberhold','thornhollow','frostgate','gloamport','wayfarers_rest','wilderness','dungeon','boss','combat','interior')
AMBIENT=('meadow','forest','ancient_forest','coast','wind','cave','city','forge','harbor','tundra','swamp','interior','ruins','arcane')
STEP=tuple(f'{surface}_{n}' for surface in ('grass','dirt','stone','wood','water','snow') for n in range(1,4))
IMPACT=tuple(f'{kind}_{n}' for kind in ('blade','blunt','bow','magic') for n in range(1,4))
VOCAL=tuple(f'{family}_{state}' for family in ('beast','humanoid','undead','construct','spirit','monster') for state in ('hurt','death'))
CLASS=('vanguard','berserker','ranger','rogue','arcanist','warden','templar','spellblade')
EFFECT=('gather','coins','hammer','equip','drink','ui','click','error','loot','quest_accept','quest_complete','skill_up','level_up','transition','chest','social','event_start','event_complete','heal','swing')
GROUPS={'music':MUSIC,'ambient':AMBIENT,'step':STEP,'impact':IMPACT,'vocal':VOCAL,'class':CLASS,'effect':EFFECT}
EXPECTED=tuple(f'{prefix}_{key}' for prefix,keys in GROUPS.items() for key in keys)
RANGES={'music':(15,20),'ambient':(10,14),'step':(.12,.35),'impact':(.16,.45),'vocal':(.25,.70),'class':(.25,.70),'effect':(.15,.60)}

def read_pcm(path:Path):
    with wave.open(str(path),'rb') as stream:
        channels=stream.getnchannels();width=stream.getsampwidth();rate=stream.getframerate();frames=stream.getnframes();compression=stream.getcomptype();raw=stream.readframes(frames)
    if width!=2:return channels,width,rate,frames,compression,[]
    values=array.array('h');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    return channels,width,rate,frames,compression,[value/32768.0 for value in values]

def metrics(path:Path):
    channels,width,rate,frames,compression,samples=read_pcm(path);row={'file':path.name,'channels':channels,'sample_width':width,'sample_rate':rate,'frames':frames,'compression':compression,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    if not samples:return row
    peak=max(abs(value) for value in samples);rms=math.sqrt(sum(value*value for value in samples)/len(samples));dc=sum(samples)/len(samples);clipped=sum(1 for value in samples if abs(value)>=32767/32768)/len(samples);edge=min(max(1,rate//20),len(samples)//2);seam=sum(abs(samples[index]-samples[-edge+index]) for index in range(edge))/edge
    row.update(duration_seconds=frames/rate if rate else 0,peak=peak,rms=rms,dc_offset=dc,clipped_fraction=clipped,loop_edge_mean_difference=seam);return row

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--audio-root',type=Path,default=ROOT/'client/Assets/audio');parser.add_argument('--output',type=Path,default=ROOT/'artifacts/audio/audio-quality.json');args=parser.parse_args();root=args.audio_root.resolve();output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    errors=[];rows=[];found={path.stem for path in root.glob('*.wav')};missing=sorted(set(EXPECTED)-found);unexpected=sorted(found-set(EXPECTED))
    if missing:errors.append('Missing audio: '+', '.join(missing))
    if unexpected:errors.append('Unexpected audio: '+', '.join(unexpected))
    for key in EXPECTED:
        path=root/(key+'.wav')
        if not path.exists():continue
        row=metrics(path);rows.append(row);prefix=key.split('_',1)[0]
        if row.get('channels')!=1:errors.append(key+': expected mono PCM')
        if row.get('sample_width')!=2:errors.append(key+': expected 16-bit PCM')
        if row.get('sample_rate')!=22050:errors.append(key+': expected 22050 Hz')
        if row.get('compression')!='NONE':errors.append(key+': compressed WAV is not supported')
        if 'rms' not in row:continue
        lo,hi=RANGES[prefix];duration=row['duration_seconds']
        if not lo<=duration<=hi:errors.append(f'{key}: duration {duration:.3f}s outside {lo}-{hi}s')
        if not .03<=row['peak']<=.95:errors.append(f'{key}: peak {row["peak"]:.4f} is out of range')
        if not .002<=row['rms']<=.50:errors.append(f'{key}: RMS {row["rms"]:.5f} is out of range')
        if abs(row['dc_offset'])>.03:errors.append(f'{key}: DC offset {row["dc_offset"]:.5f} is too large')
        if row['clipped_fraction']>.0005:errors.append(f'{key}: clipped fraction {row["clipped_fraction"]:.6f} is too large')
        if prefix in {'music','ambient'} and row['loop_edge_mean_difference']>.20:errors.append(f'{key}: loop boundary mean difference {row["loop_edge_mean_difference"]:.4f} is too large')
    dupes=[digest for digest,count in Counter(row['sha256'] for row in rows).items() if count>1]
    if dupes:errors.append('Duplicate WAV payloads detected: '+str(len(dupes)))
    counts={prefix:sum(1 for row in rows if row['file'].startswith(prefix+'_')) for prefix in GROUPS}
    for prefix,keys in GROUPS.items():
        if counts[prefix]!=len(keys):errors.append(f'{prefix}: expected {len(keys)} files, measured {counts[prefix]}')
    report={'expected_files':len(EXPECTED),'measured_files':len(rows),'category_counts':counts,'unique_payloads':len({row['sha256'] for row in rows}),'human_listening_approved':False,'checks':rows,'errors':errors};output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if rows:print(f'AUDIO_QUALITY: measured {len(rows)} WAV files in {len(GROUPS)} categories; unique {report["unique_payloads"]}; technical errors {len(errors)}.')
    print('AUDIO_QUALITY: automated format, level, clipping, uniqueness and loop checks do not approve perceived mix, transitions, composition, or artistic quality.')
    if errors:
        for error in errors:print('AUDIO ERROR:',error)
        raise SystemExit(1)
if __name__=='__main__':main()
