#!/usr/bin/env python3
"""Build the Atelier asset library.

Reads content/catalog.json (read only) and writes an independent, complete art
pack to atelier/Assets. It never touches client/Assets or any other existing
directory.

    python atelier/build.py                 # everything
    python atelier/build.py --only items abilities
    python atelier/build.py --jobs 8        # parallel render
    python atelier/build.py --list          # show groups and counts
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from PIL import Image  # noqa: E402

from forge import beasts, folk, gear, lands, rig, sigils, smith, score  # noqa: E402

OUT = HERE / 'Assets'
CATALOG = ROOT / 'content' / 'catalog.json'

GROUPS = ('terrain', 'props', 'buildings', 'resources', 'chests', 'items', 'structures',
          'abilities', 'skills', 'people', 'equipment', 'npcs', 'mobs', 'gear',
          'gear_worn', 'audio')

_DATA = None


def catalog():
    global _DATA
    if _DATA is None:
        if not CATALOG.is_file():
            raise SystemExit('content/catalog.json is missing; run the project content build first.')
        _DATA = json.loads(CATALOG.read_text(encoding='utf-8'))
    return _DATA


# ------------------------------------------------------------------ tasks --

def plan(groups):
    """Every asset this library owns, as (group, key, payload) tuples."""
    # Terrain and indexing are independent of game content. Avoid requiring a
    # generated catalogue for these self-contained library operations.
    dependent = {'buildings', 'resources', 'items', 'structures', 'abilities',
                 'skills', 'equipment', 'npcs', 'mobs'}
    data = catalog() if set(groups) & dependent else {
        key: [] for key in ('zones', 'resources', 'items', 'abilities', 'skills', 'npcs', 'mobs')}

    tasks = []

    def add(group, key, payload=None):
        if group in groups:
            tasks.append((group, key, payload))

    for kind in lands.TERRAIN:
        for variant in range(4):
            add('terrain', 'terrain/%s_%d' % (kind, variant), {'kind': kind, 'variant': variant})
    for name in lands.PROPS:
        add('props', 'props/' + name, {'name': name})
    for zone in data['zones']:
        for definition in zone['buildings']:
            add('buildings', 'buildings/%s/%s' % (zone['id'], definition['id']),
                {'zone': {'id': zone['id'], 'biome': zone.get('biome', '')}, 'building': definition})
    seen_resources = set()
    for definition in data['resources']:
        seen_resources.add(definition['id'])
        add('resources', 'resources/' + definition['id'], definition)
    if 'crop_wheat' not in seen_resources:
        add('resources', 'resources/crop_wheat', {'id': 'crop_wheat', 'skill': 'farming'})
    for kind in lands.CHESTS:
        for opened in (False, True):
            add('chests', 'chests/%s_%s' % (kind, 'open' if opened else 'closed'),
                {'kind': kind, 'opened': opened})
    for item in data['items']:
        add('items', 'items/' + item['id'], item)
        if item.get('type') == 'structure':
            add('structures', 'structures/' + item['id'], item)
    for ability in data['abilities']:
        add('abilities', 'abilities/' + ability['id'], ability)
    for skill in data['skills']:
        add('skills', 'skills/' + skill['id'], skill)
    for build in range(2):
        for skin in range(6):
            add('people', 'people/body_%d_%d' % (build, skin), {'build': build, 'skin': skin})
    for style in range(6):
        for colour in range(8):
            add('people', 'people/hair_%d_%d' % (style, colour), {'style': style, 'colour': colour})
    for item in data['items']:
        if item.get('slot'):
            add('equipment', 'equipment/' + item['id'], item)
    for role in sorted({npc['role'] for npc in data['npcs']}):
        add('npcs', 'npcs/' + role, {'role': role})
    for mob in data['mobs']:
        add('mobs', 'mobs/' + mob['id'], mob)
    for item in gear.catalogue():
        add('gear', 'gear/' + item['id'], item)
        if item.get('slot'):
            add('gear_worn', 'gear_worn/' + item['id'], item)
    for key in score.TRACKS:
        add('audio', 'audio/' + key, {'key': key})
    return tasks


ANIMATED = {'people', 'equipment', 'npcs', 'mobs', 'gear_worn'}


def render(task):
    """Draw one asset and write it. Runs in a worker process."""
    group, key, payload = task
    path = OUT / (key + ('.wav' if group == 'audio' else '.png'))
    path.parent.mkdir(parents=True, exist_ok=True)
    if group == 'audio':
        score.write(payload['key'], path)
        return key, group
    if group == 'terrain':
        image = lands.tile(payload['kind'], payload['variant'])
    elif group == 'props':
        image = lands.prop(payload['name'])
    elif group == 'buildings':
        image = lands.building(payload['zone'], payload['building'])
    elif group == 'resources':
        image = lands.resource(payload)
    elif group == 'chests':
        image = lands.chest(payload['kind'], payload['opened'])
    elif group == 'items':
        image = smith.icon(payload)
    elif group == 'structures':
        image = lands.structure(payload['id'])
    elif group == 'abilities':
        image = sigils.ability_icon(payload)
    elif group == 'skills':
        image = sigils.skill_icon(payload['id'])
    elif group == 'people':
        if 'build' in payload:
            image = rig.sheet(lambda s, f, d: folk.body_frame(payload['build'], payload['skin'], s, f, d))
        else:
            image = rig.sheet(lambda s, f, d: folk.hair_frame(payload['style'], payload['colour'], s, f, d))
    elif group == 'equipment':
        image = rig.sheet(lambda s, f, d: folk.armour_frame(payload, s, f, d))
    elif group == 'npcs':
        image = rig.sheet(lambda s, f, d: folk.npc_frame(payload['role'], s, f, d))
    elif group == 'gear':
        image = smith.icon(payload)
    elif group == 'gear_worn':
        image = rig.sheet(lambda s, f, d: folk.armour_frame(payload, s, f, d))
    elif group == 'mobs':
        size = 128 if payload.get('boss') else 64
        image = rig.sheet(lambda s, f, d: beasts.frame(payload, s, f, d), size)
    else:
        raise ValueError('unknown group ' + group)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    image.save(path, optimize=True, compress_level=9)
    return key, group


# ---------------------------------------------------------------- driver ---

def manifest():
    """Index everything on disk, so a partial rebuild never truncates the list."""
    entries = []
    for path in sorted(OUT.rglob('*.png')):
        key = path.relative_to(OUT).with_suffix('').as_posix()
        group = key.split('/', 1)[0]
        with Image.open(path) as image:
            if image.mode != 'RGBA':
                raise ValueError('Not RGBA: ' + key)
            if image.getchannel('A').getbbox() is None:
                raise ValueError('Blank asset: ' + key)
            animated = group in ANIMATED
            if animated:
                size = image.width // rig.FRAMES
                if image.width % rig.FRAMES or image.height != size * len(rig.STATES) * len(rig.DIRECTIONS):
                    raise ValueError('Bad animation grid: ' + key)
            entries.append({
                'key': key, 'group': group, 'width': image.width, 'height': image.height,
                'animated': animated,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    return entries


CREDITS = """Kairnfall Atelier art library.

Every image and sound in this directory is generated from the source in
atelier/forge by the build script atelier/build.py. There is no third party
artwork here, and nothing is copied from or shared with any other art pack in
this repository; this library is a separate, self contained alternative set.

Sprite sheets are laid out eight frames across, with the six animation states
(idle, walk, attack, cast, hit, death) each occupying four rows, one per facing
(south, west, east, north). Actor frames are 64x64 with the ground contact at
y=55; boss frames are 128x128 with the same proportions.

Structural checks confirm that files exist, are the right shape and are not
blank. They are not an artistic sign off; the art still has to be looked at.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--only', nargs='+', choices=GROUPS, default=list(GROUPS),
                        help='render just these groups')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) - 1),
                        help='worker processes (1 disables the pool)')
    parser.add_argument('--list', action='store_true', help='count assets and exit')
    parser.add_argument('--manifest', action='store_true',
                        help='reindex what is already on disk without rendering')
    parser.add_argument('--out', default=None, help='output directory (default atelier/Assets)')
    args = parser.parse_args()

    global OUT
    if args.out:
        OUT = Path(args.out).resolve()
        if not str(OUT).startswith(str(HERE)) and not str(OUT).startswith(str(ROOT / 'artifacts')):
            raise SystemExit('Refusing to write outside atelier/ or artifacts/.')

    groups = set(args.only)
    tasks = [] if args.manifest else plan(groups)
    counts = {}
    for group, _, _ in tasks:
        counts[group] = counts.get(group, 0) + 1
    if args.list:
        for group in GROUPS:
            if group in counts:
                print('%-12s %5d' % (group, counts[group]))
        print('%-12s %5d' % ('total', len(tasks)))
        return

    OUT.mkdir(parents=True, exist_ok=True)
    start = time.time()
    done = []
    if args.manifest:
        tasks = []
        print('ATELIER: reindexing %s' % OUT, flush=True)
    else:
        print('ATELIER: %d assets across %d groups -> %s' % (len(tasks), len(counts), OUT), flush=True)
    if not tasks:
        pass
    elif args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as pool:
            for index, result in enumerate(pool.map(render, tasks, chunksize=4), 1):
                done.append(result)
                if index % 100 == 0 or index == len(tasks):
                    print('  %5d / %d  (%.0fs)' % (index, len(tasks), time.time() - start), flush=True)
    else:
        for index, task in enumerate(tasks, 1):
            done.append(render(task))
            if index % 100 == 0 or index == len(tasks):
                print('  %5d / %d  (%.0fs)' % (index, len(tasks), time.time() - start), flush=True)

    entries = manifest()
    (OUT / 'manifest.json').write_text(json.dumps({
        'schema': 1,
        'library': 'atelier',
        'source': 'Original procedural artwork generated by atelier/forge.',
        'artistic_review': 'pending',
        'frame_order': list(rig.STATES),
        'directions': list(rig.DIRECTIONS),
        'frames_per_row': rig.FRAMES,
        'actor_size': 64,
        'boss_size': 128,
        'foot_baseline': int(rig.GROUND),
        'assets': entries,
    }, indent=2) + '\n', encoding='utf-8')
    (OUT / 'CREDITS.txt').write_text(CREDITS, encoding='utf-8')
    (HERE / 'gear.json').write_text(json.dumps({
        'schema': 1,
        'tiers': [{'index': tier.index + 1, 'level': tier.level, 'key': tier.key,
                   'metal': tier.metal_name, 'cloth': tier.cloth_name,
                   'leather': tier.leather_name, 'style': tier.style,
                   'glow': bool(tier.glow)} for tier in gear.TIERS],
        'items': gear.catalogue(),
    }, indent=2) + '\n', encoding='utf-8')
    audio = sorted(OUT.glob('audio/*.wav'))
    tally = {}
    for entry in entries:
        tally[entry['group']] = tally.get(entry['group'], 0) + 1
    report = {
        'groups': tally,
        'png_files': len(entries),
        'animation_sheets': sum(1 for e in entries if e['animated']),
        'audio_files': len(audio),
        'artistic_review': 'pending',
    }
    (HERE / 'coverage.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('ATELIER RESULT: %d images (%d animation sheets), %d audio files in %.0fs. '
          'Structural checks passed; visual review is still required.'
          % (len(entries), report['animation_sheets'], len(audio), time.time() - start), flush=True)


if __name__ == '__main__':
    main()
