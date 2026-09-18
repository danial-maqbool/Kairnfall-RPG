#!/usr/bin/env python3
"""Build or verify the committed Wayfarer actor atlas pack.

Use --write only after reviewing a renderer change. The default is a read-only
comparison against independently regenerated client assets, never a baseline update.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GROUPS=frozenset(('people','equipment','npcs','mobs','motions'))
SOURCES=('tools/art/characters.py','tools/art/character_motion.py','tools/art/wildlife.py',
         'tools/art/creature_anatomy.py','tools/art/common.py','atelier/forge/pigment.py')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--assets',default='client/Assets')
    args=parser.parse_args()
    source=(ROOT/args.assets).resolve();pack=ROOT/'art/wayfarer/Assets'
    if not source.is_relative_to(ROOT):raise SystemExit('Asset source must be inside the repository.')
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    entries=sorted((dict(e) for e in manifest['assets'] if e['key'].split('/')[0] in GROUPS),key=lambda e:e['key'])
    if not entries:raise SystemExit('No regenerated actor assets found.')
    value={'schema':1,'library':'wayfarer','source':'Original project-authored character and creature construction',
           'actor_size':64,'boss_size':128,'foot_anchor':[32,55],'boss_anchor':[64,110],
           'states':manifest['frame_order'],'motion_states':manifest['motion_order'],
           'directions':manifest['directions'],'frames':8,
           'source_sha256':{name:sha(ROOT/name) for name in SOURCES},
           'artistic_approval':False,'assets':entries}
    expected={e['key']+'.png' for e in entries}
    if any(not isinstance(e.get('pixel_sha256'),str) or len(e['pixel_sha256'])!=64 for e in entries):
        raise SystemExit('Generated actor manifest is missing canonical pixel hashes.')
    problems=[];stored={}
    if args.write:
        pack.mkdir(parents=True,exist_ok=True)
        for old in pack.rglob('*.png'):
            if old.relative_to(pack).as_posix() not in expected:old.unlink()
    else:
        manifest_path=pack/'manifest.json'
        if not manifest_path.is_file():
            problems.append('Committed actor manifest is missing.')
        else:
            committed=json.loads(manifest_path.read_text(encoding='utf-8'))
            committed_meta=dict(committed);stored_entries=committed_meta.pop('assets',[])
            expected_meta=dict(value);expected_meta.pop('assets',None)
            if committed_meta!=expected_meta:problems.append('Committed actor manifest/source metadata differs.')
            if not isinstance(stored_entries,list):
                problems.append('Committed actor manifest has an invalid asset list.')
            else:
                for saved in stored_entries:
                    if not isinstance(saved,dict) or not isinstance(saved.get('key'),str) or saved['key'] in stored:
                        problems.append('Committed actor manifest has invalid or duplicate asset entries.');continue
                    stored[saved['key']]=saved
                if set(stored)!={e['key'] for e in entries}:problems.append('Committed actor manifest asset keys differ.')
    for entry in entries:
        relative=entry['key']+'.png';src=source/relative;dest=pack/relative
        if not src.is_file() or sha(src)!=entry['sha256']:raise SystemExit('Unverified generated input: '+relative)
        if args.write:
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
        else:
            saved=stored.get(entry['key'])
            if not dest.is_file():problems.append('Committed atlas is missing: '+relative);continue
            if saved is None:continue
            if any(saved.get(field)!=entry.get(field) for field in ('width','height','animated','state_count','pixel_sha256')):
                problems.append('Committed atlas pixels or geometry differ: '+relative);continue
            if sha(dest)!=saved.get('sha256'):problems.append('Committed atlas file checksum differs: '+relative)
    if args.write:
        (pack/'manifest.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        (pack/'CREDITS.txt').write_text('Kairnfall Wayfarer actor pack.\nOriginal project-generated artwork from the source paths recorded in manifest.json.\nNo prior actor raster or promotional concept sheet is sampled by the active renderers.\nExisting catalogue identities, shared colour primitives and species anatomy descriptions are retained as data.\nBase sheets: six states, four directions, eight frames. Motion sheets: one action, four directions, eight frames.\nPNG integrity and reproducibility are technical checks, not independent artistic or release approval.\n',encoding='utf-8')
    else:
        present={p.relative_to(pack).as_posix() for p in pack.rglob('*.png')}
        if present!=expected:problems.append('The committed pack contains missing or obsolete atlas files.')
    if problems:raise SystemExit('\n'.join(problems))
    print(json.dumps({'mode':'write' if args.write else 'verify','sheets':len(entries),
                      'base_sheets':sum(e['key'].split('/')[0]!='motions' for e in entries),
                      'motion_sheets':sum(e['key'].startswith('motions/') for e in entries),
                      'committed_bytes':sum((pack/(e['key']+'.png')).stat().st_size for e in entries),
                      'artistic_approval':False},indent=2))

if __name__=='__main__':main()
