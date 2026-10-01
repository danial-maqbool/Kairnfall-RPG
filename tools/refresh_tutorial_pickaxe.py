#!/usr/bin/env python3
"""Check one optional Wayfarer tool in memory; --apply refreshes its six sheets.

Only the shared optional descriptor's base and five extra-action sheets are
merged into the runtime and committed actor libraries. Original bytes and hash
inventories are retained before any mutation. This never regenerates ordinary
actors, imports Godot textures, changes a catalog, or grants artistic approval.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import sys
import uuid

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_wayfarer_pack import SOURCES

# A CLI invocation captures source bytes before loading the drawing modules.
# Refuse to fingerprint newly edited files as if already loaded code used them.
_LOADED_SOURCES = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCES}
from art.character_motion import STATES, EXTRA_STATES, DIRECTIONS
from art.characters import equipment_frame
from art.common import canvas, sheet
from art.optional_equipment import optional_equipment
from integrate_atelier import ACTOR_SKIP_REASON, runtime_coverage, validate_runtime_provenance
from validate_character_assets import expected as expected_actor_keys

ASSET_ROOTS = ('art/wayfarer/Assets', 'client/Assets')
MANIFESTS = tuple(directory + '/manifest.json' for directory in ASSET_ROOTS)
MANIFESTS += ('client/Assets/atelier-integration.json',)
ITEM_ID = optional_equipment()[0]['id']
BASE_KEY = 'equipment/' + ITEM_ID
TARGET_KEYS = (BASE_KEY,) + tuple('motions/' + state + '/' + BASE_KEY for state in EXTRA_STATES)
NEW_SOURCE = 'tools/art/optional_equipment.py'
CHANGED_RENDERER = 'tools/art/characters.py'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def checked_path(root, relative):
    if not isinstance(relative, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*', relative) \
            or any(part in ('.', '..') for part in relative.split('/')):
        raise ValueError('Unsafe refresh path: ' + str(relative))
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Refresh path escapes the repository: ' + relative)
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError('Refresh refuses symlink paths: ' + relative)
        current = current.parent
    return path


def fingerprints(root):
    inventory = {}
    for directory in ASSET_ROOTS:
        for path in sorted(checked_path(root, directory).rglob('*')):
            relative = path.relative_to(root).as_posix()
            checked_path(root, relative)
            if path.is_file():
                inventory[relative] = digest(path.read_bytes())
    return inventory


def source_fingerprints(root):
    return {name: digest(checked_path(root, name).read_bytes()) for name in SOURCES}


def entry_index(metadata, label):
    entries = metadata.get('assets')
    if not isinstance(entries, list):
        raise ValueError('Missing assets in ' + label)
    result = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Malformed entry in ' + label)
        key = entry.get('key')
        if not isinstance(key, str) or not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*', key):
            raise ValueError('Unsafe asset key in ' + label)
        if key in result:
            raise ValueError('Duplicate asset key in ' + label + ': ' + key)
        result[key] = entry
    return result


def png_bytes(image):
    stream = BytesIO()
    image.save(stream, format='PNG', optimize=True, compress_level=9)
    return stream.getvalue()


def render_candidates():
    items = optional_equipment()
    if len(items) != 1 or items[0]['id'] != ITEM_ID or items[0]['slot'] != 'weapon':
        raise ValueError('This incremental refresh supports exactly one optional held tool')
    item = items[0]
    images = {BASE_KEY: sheet(lambda state, number, direction:
                             equipment_frame(item, state, number, direction))}
    for state in EXTRA_STATES:
        image = canvas((512, 256))
        for direction in range(4):
            for number in range(8):
                image.alpha_composite(equipment_frame(item, state, number, direction),
                                      (number * 64, direction * 64))
        images['motions/' + state + '/' + BASE_KEY] = image
    return images


def validate_candidate(key, image):
    count = 1 if key.startswith('motions/') else len(STATES)
    if image.mode != 'RGBA' or image.size != (512, 256 * count):
        raise ValueError('Invalid candidate pose grid: ' + key)
    alpha = image.getchannel('A')
    for row in range(4 * count):
        for number in range(8):
            box = alpha.crop((number * 64, row * 64, (number + 1) * 64, (row + 1) * 64)).getbbox()
            if box is None or not (box[0] > 0 and box[1] > 0 and box[2] < 64 and box[3] < 64):
                raise ValueError(f'Blank or clipped candidate: {key}/{row}/{number}')


@dataclass
class RefreshPlan:
    root: Path
    writes: dict[str, bytes]
    originals: dict[str, bytes | None]
    before: dict[str, str]
    catalog_hash: str
    sources: dict[str, str]
    report: dict


class RefreshApplyError(RuntimeError):
    def __init__(self, report):
        self.report = report
        super().__init__('Tutorial pickaxe refresh failed: ' + report['failure']
                         + '; retained backup: ' + report['backup'])


def make_plan(root=ROOT, *, migrate_aggregate_coverage=False):
    root = Path(root).absolute()
    catalog = checked_path(root, 'content/catalog.json').read_bytes()
    if checked_path(root, 'client/Assets/catalog.json').read_bytes() != catalog:
        raise ValueError('Client and authoritative catalogs differ; refresh never changes catalogs')
    catalog_data = json.loads(catalog)
    originals = {name: checked_path(root, name).read_bytes() for name in MANIFESTS}
    pack, runtime, integration = (json.loads(originals[name]) for name in MANIFESTS)
    if pack.get('schema') != 1 or pack.get('library') != 'wayfarer' \
            or pack.get('artistic_approval') is not False or pack.get('actor_size') != 64 \
            or pack.get('foot_anchor') != [32, 55] or pack.get('frames') != 8 \
            or pack.get('states') != list(STATES) or pack.get('motion_states') != list(EXTRA_STATES) \
            or pack.get('directions') != list(DIRECTIONS):
        raise ValueError('Unsupported Wayfarer pack identity, anchors, poses or approval')
    if runtime.get('schema') != 1 or runtime.get('artistic_review') != 'not_approved' \
            or runtime.get('frame_order') != list(STATES) or runtime.get('motion_order') != list(EXTRA_STATES) \
            or runtime.get('directions') != list(DIRECTIONS) or runtime.get('frames_per_row') != 8:
        raise ValueError('Unsupported runtime manifest identity, poses or approval')
    if integration.get('schema') != 3 \
            or integration.get('actor_runtime_source') != 'Wayfarer original joint construction' \
            or integration.get('actor_historical_fallbacks') != 0 \
            or integration.get('historical_actor_bytes_active') is not False \
            or integration.get('catalog_ids_changed') is not False \
            or integration.get('independent_gear_ladder_imported') is not False:
        raise ValueError('Unsupported non-actor integration ownership contract')
    copied = entry_index(integration, MANIFESTS[2])
    if any(key.split('/')[0] in {'people', 'equipment', 'npcs', 'mobs', 'motions'} for key in copied):
        raise ValueError('Historical actor bytes are present in the non-actor copy report')
    sources = source_fingerprints(root)
    recorded = pack.get('source_sha256')
    if not isinstance(recorded, dict) or set(recorded) not in (set(SOURCES), set(SOURCES) - {NEW_SOURCE}):
        raise ValueError('Wayfarer source fingerprint coverage differs')
    for name in set(SOURCES) - {NEW_SOURCE, CHANGED_RENDERER}:
        if recorded.get(name) != sources[name]:
            raise ValueError('Unrelated renderer source changed: ' + name)
    if sources != _LOADED_SOURCES:
        raise ValueError('Renderer source differs from loaded drawing code; start a fresh check')
    indexes = [entry_index(metadata, label) for metadata, label in zip((pack, runtime), MANIFESTS[:2])]
    present = [set(index) & set(TARGET_KEYS) for index in indexes]
    if present[0] != present[1] or present[0] not in (set(), set(TARGET_KEYS)):
        raise ValueError('Selected tool sheets are incomplete or differ between libraries')
    base, extra = expected_actor_keys(catalog_data)
    expected_actors = (base | extra) - (set() if present[0] else set(TARGET_KEYS))
    for index in indexes:
        actual = {key for key in index if key.split('/')[0] in {'people', 'equipment', 'npcs', 'mobs', 'motions'}}
        if actual != expected_actors:
            raise ValueError('Actor manifest differs from the exact ordinary and optional cohorts')
    coverage, optional = runtime_coverage(list(indexes[1]), catalog_data, require_optional=bool(present[0]))
    skipped = integration.get('skipped')
    if not isinstance(skipped, list) \
            or any(not isinstance(entry, dict) or not isinstance(entry.get('key'), str) for entry in skipped):
        raise ValueError('Non-actor integration skips differ from runtime actors')
    tool_skips = [entry for entry in skipped if entry['key'] == BASE_KEY]
    if len(tool_skips) != (1 if present[0] else 0) \
            or any(entry.get('reason') != ACTOR_SKIP_REASON for entry in tool_skips):
        raise ValueError('Optional tool ownership skip differs from runtime actors')
    aggregate_migrated = False
    checked_integration = deepcopy(integration)
    if migrate_aggregate_coverage:
        aggregate = dict(coverage, equipment=coverage['equipment'] + 1)
        if not present[0] or 'optional_actor_equipment' in integration \
                or integration.get('coverage') != aggregate \
                or any(type(count) is not int for count in integration['coverage'].values()) \
                or recorded != sources:
            raise ValueError('No exact supported aggregate optional-equipment audit to migrate')
        checked_integration['coverage'] = coverage
        checked_integration['optional_actor_equipment'] = optional
        aggregate_migrated = True
    elif not present[0] and 'optional_actor_equipment' not in integration:
        # The retained pre-tool audit predates optional art. It may be upgraded
        # only while both libraries have no selected sheets and ordinary counts match.
        checked_integration['optional_actor_equipment'] = []
    validate_runtime_provenance(checked_integration, list(indexes[1]), catalog_data,
                                require_optional=bool(present[0]))
    before = fingerprints(root)
    candidates, repeated = render_candidates(), render_candidates()
    merged = [deepcopy(pack), deepcopy(runtime)]
    merged_indexes = [entry_index(metadata, label) for metadata, label in zip(merged, MANIFESTS)]
    writes, changes = {}, []
    for key in TARGET_KEYS:
        image = candidates[key]
        validate_candidate(key, image)
        if image.tobytes() != repeated[key].tobytes():
            raise ValueError('Nondeterministic pickaxe candidate: ' + key)
        encoded = png_bytes(image)
        entry = {'key': key, 'width': image.width, 'height': image.height,
                 'sha256': digest(encoded), 'pixel_sha256': digest(image.tobytes()),
                 'animated': True, 'state_count': 1 if key.startswith('motions/') else 6}
        for directory, index, merged_index, metadata in zip(ASSET_ROOTS, indexes, merged_indexes, merged):
            relative = directory + '/' + key + '.png'
            path = checked_path(root, relative)
            original = path.read_bytes() if path.is_file() else None
            originals[relative] = original
            if (original is not None) != (key in index):
                raise ValueError('Tool file and manifest presence differ: ' + relative)
            if original is not None:
                if digest(original) != index[key].get('sha256'):
                    raise ValueError('Selected tool checksum differs: ' + relative)
                if any(index[key].get(field) != entry[field]
                       for field in ('width', 'height', 'animated', 'state_count')):
                    raise ValueError('Selected tool pose metadata differs: ' + relative)
                with Image.open(BytesIO(original)) as old:
                    if old.mode != 'RGBA' or old.size != image.size \
                            or digest(old.tobytes()) != index[key].get('pixel_sha256'):
                        raise ValueError('Selected tool pixels or pose geometry differ: ' + relative)
            if key in merged_index:
                merged_index[key].update(entry)
            else:
                metadata['assets'].append(deepcopy(entry))
            writes[relative] = encoded
        changes.append(entry)
    merged[0]['source_sha256'] = sources
    for name, metadata in zip(MANIFESTS[:2], merged):
        metadata['assets'].sort(key=lambda entry: entry['key'])
        writes[name] = json_bytes(metadata)
    merged_integration = deepcopy(integration)
    merged_integration['coverage'] = coverage
    merged_integration['optional_actor_equipment'] = sorted(item['id'] for item in optional_equipment())
    if not present[0]:
        merged_integration['skipped'].append({
            'key': BASE_KEY, 'reason': ACTOR_SKIP_REASON})
        merged_integration['skipped'].sort(key=lambda entry: entry['key'])
    validate_runtime_provenance(merged_integration,
                                [entry['key'] for entry in merged[1]['assets']], catalog_data)
    writes[MANIFESTS[2]] = json_bytes(merged_integration)
    for relative, original in originals.items():
        if (digest(original) if original is not None else None) != before.get(relative):
            raise ValueError('Selected bytes changed during preflight: ' + relative)
    writes = {name: data for name, data in writes.items() if originals[name] != data}
    report = {'schema': 1, 'mode': 'check', 'selected_keys': list(TARGET_KEYS),
              'assets': changes, 'changed_files': sorted(writes), 'catalog_sha256': digest(catalog),
              'source_sha256': sources, 'asset_files_in_inventory': len(before),
              'ordinary_equipment_count': coverage['equipment'],
              'optional_actor_equipment': merged_integration['optional_actor_equipment'],
              'aggregate_coverage_migrated': aggregate_migrated,
              'actor_runtime_source': 'Wayfarer original joint construction',
              'visual_review': 'not_performed', 'visual_acceptance': 'not_approved',
              'native_rendering': 'not_performed', 'catalog_changed': False}
    return RefreshPlan(root, writes, originals, before, digest(catalog), sources, report)


def assert_unchanged(plan):
    if fingerprints(plan.root) != plan.before:
        raise ValueError('Asset bytes changed after preflight; nothing was refreshed')
    if digest(checked_path(plan.root, 'content/catalog.json').read_bytes()) != plan.catalog_hash \
            or source_fingerprints(plan.root) != plan.sources:
        raise ValueError('Catalog or renderer changed after preflight; nothing was refreshed')


def target_unchanged(plan, relative):
    path = checked_path(plan.root, relative)
    original = plan.originals[relative]
    return path.is_file() and path.read_bytes() == original if original is not None else not path.exists()


def apply_plan(plan):
    lease = checked_path(plan.root, 'artifacts/tutorial-pickaxe-refresh/.refresh-owner.lock')
    lease.parent.mkdir(parents=True, exist_ok=True)
    marker = uuid.uuid4().hex.encode('ascii')
    try:
        descriptor = os.open(lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError('Another pickaxe refresh owns the write lease; nothing was refreshed') from error
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(marker)
        return _apply_plan(plan)
    finally:
        if lease.is_file() and lease.read_bytes() == marker:
            lease.unlink()


def _apply_plan(plan):
    assert_unchanged(plan)
    if not plan.writes:
        return dict(plan.report, mode='apply', changed_files=[], unrelated_hashes_preserved=True)
    suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    backup_relative = 'artifacts/tutorial-pickaxe-refresh/' + suffix
    backup = checked_path(plan.root, backup_relative)
    backup.mkdir(parents=True, exist_ok=False)
    absent = []
    for relative, data in plan.writes.items():
        if plan.originals[relative] is None:
            absent.append(relative)
        else:
            original = backup / 'originals' / relative
            original.parent.mkdir(parents=True, exist_ok=True)
            original.write_bytes(plan.originals[relative])
        staged = backup / 'staged' / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(data)
    (backup / 'previously-absent-files.json').write_bytes(json_bytes(absent))
    (backup / 'hash-inventory-before.json').write_bytes(json_bytes(plan.before))
    (backup / 'refresh-plan.json').write_bytes(json_bytes(plan.report))
    replaced = []
    try:
        assert_unchanged(plan)
        for relative in plan.writes:
            target = checked_path(plan.root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target_unchanged(plan, relative):
                raise ValueError('Selected asset changed before replacement: ' + relative)
            staged = backup / 'staged' / relative
            if plan.originals[relative] is None:
                # A hard link attaches already complete bytes atomically and
                # refuses to overwrite a concurrently created new target.
                os.link(staged, target)
            else:
                os.replace(staged, target)
            replaced.append(relative)
        after = fingerprints(plan.root)
        expected = dict(plan.before)
        expected.update({name: digest(data) for name, data in plan.writes.items()})
        if after != expected:
            raise ValueError('Refresh did not preserve every unrelated asset hash')
        if source_fingerprints(plan.root) != plan.sources \
                or digest(checked_path(plan.root, 'content/catalog.json').read_bytes()) != plan.catalog_hash:
            raise ValueError('Catalog or renderer changed during refresh')
    except BaseException as error:
        restored, concurrent, rollback_errors = [], [], []
        for relative in reversed(replaced):
            try:
                path = checked_path(plan.root, relative)
                if not path.is_file() or path.read_bytes() != plan.writes[relative]:
                    concurrent.append(relative)
                    continue
                original = plan.originals[relative]
                if original is None:
                    if path.read_bytes() != plan.writes[relative]:
                        concurrent.append(relative)
                        continue
                    path.unlink()
                else:
                    rollback = backup / 'rollback' / relative
                    rollback.parent.mkdir(parents=True, exist_ok=True)
                    rollback.write_bytes(original)
                    if not path.is_file() or path.read_bytes() != plan.writes[relative]:
                        concurrent.append(relative)
                        continue
                    os.replace(rollback, path)
                restored.append(relative)
            except (OSError, ValueError) as rollback_error:
                rollback_errors.append({'path': relative, 'error': str(rollback_error)})
        failure = dict(plan.report, mode='apply_failed', backup=backup_relative, failure=str(error),
                       replaced_files=replaced, restored_files=restored,
                       concurrent_files_preserved=concurrent, rollback_errors=rollback_errors)
        try:
            remaining = fingerprints(plan.root)
            failure['remaining_changed_files'] = sorted(name for name in set(remaining) | set(plan.before)
                                                        if remaining.get(name) != plan.before.get(name))
            (backup / 'hash-inventory-failed.json').write_bytes(json_bytes(remaining))
        except (OSError, ValueError) as inventory_error:
            failure['remaining_changed_files'] = None
            failure['inventory_error'] = str(inventory_error)
        failure['partial_state'] = bool(failure['remaining_changed_files'] or rollback_errors
                                       or failure.get('inventory_error'))
        (backup / 'refresh-failure.json').write_bytes(json_bytes(failure))
        raise RefreshApplyError(failure) from error
    report = dict(plan.report, mode='apply', backup=backup_relative, unrelated_hashes_preserved=True)
    (backup / 'hash-inventory-after.json').write_bytes(json_bytes(after))
    (backup / 'refresh-result.json').write_bytes(json_bytes(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument('--check', action='store_true', help='render in memory and write nothing (default)')
    operation.add_argument('--apply', action='store_true', help='back up and merge only the six optional tool sheets')
    parser.add_argument('--migrate-aggregate-coverage', action='store_true',
                        help='explicitly repair the complete tool audit that counted optional art as ordinary catalog equipment')
    args = parser.parse_args()
    plan = make_plan(migrate_aggregate_coverage=args.migrate_aggregate_coverage)
    print(json.dumps(apply_plan(plan) if args.apply else plan.report, indent=2))


if __name__ == '__main__':
    main()
