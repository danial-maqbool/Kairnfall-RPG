#!/usr/bin/env python3
"""Inspect a pinned public art source without executing upstream code."""
from __future__ import annotations
import csv
import io
import json
import os
from pathlib import Path
import urllib.request

REPO='LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator'
REVISION='d44ea7d6904891aab8627b80ff4de1560d63bdff'

def read(url: str) -> bytes:
    headers={'User-Agent':'Kairnfall-asset-import','Accept':'application/vnd.github+json'}
    token=os.environ.get('GH_TOKEN','')
    if token and url.startswith('https://api.github.com/'):
        headers['Authorization']='Bearer '+token
    with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=90) as response:
        return response.read()

def main() -> None:
    cache=Path('.cache/lpc'); cache.mkdir(parents=True,exist_ok=True)
    tree=json.loads(read(f'https://api.github.com/repos/{REPO}/git/trees/{REVISION}?recursive=1'))
    if tree.get('truncated'):
        raise RuntimeError('The upstream file tree was truncated. Use subtree traversal before importing.')
    (cache/'tree.json').write_text(json.dumps(tree),encoding='utf-8')
    paths=[row['path'] for row in tree['tree'] if row['type']=='blob']
    credits=read(f'https://raw.githubusercontent.com/{REPO}/{REVISION}/CREDITS.csv').decode('utf-8-sig')
    (cache/'CREDITS.csv').write_text(credits,encoding='utf-8')
    print('PIN',REVISION,'FILES',len(paths))
    print('CREDIT HEADER',credits.splitlines()[0])
    for prefix in ['spritesheets/body/bodies/male/','spritesheets/head/','spritesheets/hair/',
                   'spritesheets/torso/','spritesheets/legs/','spritesheets/feet/',
                   'spritesheets/weapon/','spritesheets/shield/','palette_definitions/']:
        candidates=[p for p in paths if p.startswith(prefix)]
        if prefix.startswith('spritesheets/'):
            selected=[p for p in candidates if p.endswith('/walk.png') or p.endswith('/slash.png') or p.endswith('/idle.png')]
            candidates=selected or candidates
        directories=sorted(set('/'.join(p.split('/')[:-1]) for p in candidates))
        print('\nPREFIX',prefix,'TOTAL',len(candidates))
        for p in directories[:90]: print(p)
    for needle in ['body.json','head_human','torso_armor','torso_clothes','legs_pants','feet_shoes','weapon_sword','hair_plain']:
        print('\nDEFINITIONS',needle)
        for p in [p for p in paths if p.startswith('sheet_definitions/') and needle in p][:16]: print(p)
    print('\nCREDIT EXAMPLES')
    rows=list(csv.reader(io.StringIO(credits)))
    for row in rows[:6]: print(json.dumps(row,ensure_ascii=False))

if __name__=='__main__': main()
