#!/usr/bin/env python3
"""Run real Godot character and retained visual fixtures on Linux or Windows."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='artifacts/character-acceptance')
    args=parser.parse_args();out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/'artifacts'):raise SystemExit('Native evidence must stay under artifacts/.')
    binary=os.environ.get('GODOT_BIN','')
    if not binary or not Path(binary).is_file():raise SystemExit('Run tools/get_godot.py first; GODOT_BIN must name the pinned executable.')
    logs=out/'logs';shots=out/'screenshots';logs.mkdir(parents=True,exist_ok=True);shots.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'KAIRNFALL_SCREENSHOTS':str(shots),'LIBGL_ALWAYS_SOFTWARE':'1'}
    results=[]
    def run(name,command,timeout,marker=None):
        start=time.monotonic();log=logs/(name+'.log')
        try:
            with log.open('wb') as stream:
                result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
            text=log.read_text(encoding='utf-8',errors='replace')
            failed=re.findall(r'(?m)(?:^|\s)(?:ERROR:|SCRIPT ERROR:|Unhandled exception)[^\n]*',text)
            ok=result.returncode==0 and not failed and (marker is None or marker in text)
            results.append({'name':name,'returncode':result.returncode,'seconds':round(time.monotonic()-start,2),'passed':ok,'marker':marker,'errors':failed[:30]})
            print(text[-16000:],flush=True)
            if not ok:raise RuntimeError('Native fixture failed: '+name)
        except subprocess.TimeoutExpired:
            results.append({'name':name,'passed':False,'timeout':timeout});raise
    try:
        run('import',[binary,'--headless','--editor','--path','client','--import'],900)
        prefix=[]
        if sys.platform!='win32':
            xvfb=shutil.which('xvfb-run')
            if not xvfb:raise RuntimeError('A graphical Xvfb display is required for Linux native acceptance.')
            prefix=[xvfb,'-a','-s','-screen 0 1920x1080x24']
        for name,scene,marker in (
            ('character-native','CharacterPresentationContract','CHARACTER_NATIVE_CONTRACT:'),
            ('retained-visual','VisualPresentationContract','VISUAL_PRESENTATION_CONTRACT:')):
            run(name,prefix+[binary,'--path','client','--rendering-method','gl_compatibility','--audio-driver','Dummy','res://Tests/'+scene+'.tscn'],480,marker)
        required=['character-remote-interaction.png','character-remote-corpse.png','character-state-7-frame-4.png',
                  'character-state-8-frame-3.png','02-player-walk.png','03-player-attack.png','04-player-cast.png',
                  'equipment-state-5-frame-7.png','mobs-state-5-frame-7.png']
        for name in required:
            if not (shots/name).is_file() or (shots/name).stat().st_size<100:raise RuntimeError('Missing native viewport evidence: '+name)
    finally:
        images={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(shots.glob('*.png'))}
        report={'revision':os.environ.get('GITHUB_SHA','local'),'platform':sys.platform,'fixtures':results,
                'rendered_viewports':len(images),'png_sha256':images,
                'passed':len(results)==3 and all(r['passed'] for r in results),
                'artistic_approval':False,'ordinary_account_gameplay':False,'release_approval':False}
        (out/'native-result.json').write_text(json.dumps(report,indent=2)+'\n')
    print('CHARACTER_NATIVE_SUITE:',json.dumps({k:v for k,v in report.items() if k!='png_sha256'}),flush=True)

if __name__=='__main__':main()
