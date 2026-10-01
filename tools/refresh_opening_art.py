#!/usr/bin/env python3
"""Refresh nine original opening assets without rebuilding the actor library.

The default check renders candidates in memory. --apply retains original bytes
and hash inventories under artifacts/opening-art-refresh before replacing only
the selected PNGs and merging their existing manifest entries. This validates
scope and anchors; it does not grant visual or gameplay acceptance.
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
import sys
import uuid

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))
from atelier.forge import lands, smith
from integrate_atelier import safe_path

BUILDING_KEYS = tuple('buildings/wayfarers_rest/' + ident for ident in lands.OPENING_FACADE_ROLES)
RUNE_KEYS = tuple('items/' + ident for ident in sorted(smith.OPENING_RUNE_GLYPHS))
TARGET_KEYS = BUILDING_KEYS + RUNE_KEYS
ASSET_ROOTS = ('atelier/Assets', 'client/Assets')
MANIFESTS = ('atelier/Assets/manifest.json', 'client/Assets/manifest.json',
             'client/Assets/atelier-integration.json')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2) + '\n').encode('utf-8')


def checked_path(root, relative):
    """No symlink or resolved path may escape the selected repository root."""
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
        base = checked_path(root, directory)
        for path in sorted(base.rglob('*')):
            relative = path.relative_to(root).as_posix()
            checked_path(root, relative)
            if path.is_file():
                inventory[relative] = digest(path.read_bytes())
    return inventory


def entry_index(metadata, label):
    entries = metadata.get('assets')
    if not isinstance(entries, list):
        raise ValueError('Missing asset entries in ' + label)
    index = {}
    for entry in entries:
        key = entry.get('key')
        safe_path(ROOT, key)
        if key in index:
            raise ValueError('Duplicate asset key in ' + label + ': ' + key)
        index[key] = entry
    for key in TARGET_KEYS:
        if key not in index:
            raise ValueError('Selected opening key is absent in ' + label + ': ' + key)
    return index


def png_bytes(image):
    output = BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()


def render_candidates(catalog):
    zones = [zone for zone in catalog['zones'] if zone['id'] == 'wayfarers_rest']
    if len(zones) != 1:
        raise ValueError('Expected exactly one opening zone')
    zone = zones[0]
    images = {}
    for key in BUILDING_KEYS:
        ident = key.rsplit('/', 1)[1]
        definitions = [building for building in zone['buildings'] if building['id'] == ident]
        if len(definitions) != 1 or definitions[0].get('style') != lands.OPENING_FACADE_ROLES[ident]:
            raise ValueError('Opening facade identity or service changed: ' + ident)
        images[key] = lands.building(zone, deepcopy(definitions[0]))
    for key in RUNE_KEYS:
        ident = key.split('/', 1)[1]
        definitions = [item for item in catalog['items'] if item['id'] == ident]
        if len(definitions) != 1 or definitions[0].get('type') != 'rune':
            raise ValueError('Opening rune identity or type changed: ' + ident)
        images[key] = smith.icon(deepcopy(definitions[0]))
    return images


@dataclass
class RefreshPlan:
    root: Path
    writes: dict[str, bytes]
    originals: dict[str, bytes]
    before: dict[str, str]
    catalog_hash: str
    report: dict


class RefreshApplyError(RuntimeError):
    def __init__(self, report):
        self.report = report
        concurrent = report['concurrent_files_preserved']
        detail = '; concurrent files preserved: ' + ', '.join(concurrent) if concurrent else ''
        super().__init__('Opening art refresh failed: ' + report['failure'] + detail
                         + '; retained backup: ' + report['backup'])


def make_plan(root=ROOT):
    root = Path(root).absolute()
    catalog_bytes = checked_path(root, 'content/catalog.json').read_bytes()
    if checked_path(root, 'client/Assets/catalog.json').read_bytes() != catalog_bytes:
        raise ValueError('Client and authoritative catalogs differ; refresh does not rewrite catalogs')
    catalog = json.loads(catalog_bytes)
    originals = {relative: checked_path(root, relative).read_bytes() for relative in MANIFESTS}
    metadata = {relative: json.loads(data) for relative, data in originals.items()}
    source, runtime, integration = (metadata[relative] for relative in MANIFESTS)
    if source.get('schema') != 1 or source.get('library') != 'atelier':
        raise ValueError('Unsupported Atelier manifest')
    if runtime.get('schema') != 1 or runtime.get('artistic_review') != 'not_approved':
        raise ValueError('Unsupported runtime manifest or visual approval state')
    if integration.get('schema') != 3 or integration.get('actor_historical_fallbacks') != 0 \
            or integration.get('historical_actor_bytes_active') is not False:
        raise ValueError('Refresh requires the current non-actor integration contract')
    if integration.get('source_manifest_sha256') != digest(originals[MANIFESTS[0]]):
        raise ValueError('Atelier integration refers to a stale source manifest')
    indexes = [entry_index(meta, label) for meta, label in zip((source, runtime, integration), MANIFESTS)]
    before = fingerprints(root)
    candidates = render_candidates(catalog)
    repeated = render_candidates(catalog)
    changes = []
    merged = [deepcopy(meta) for meta in (source, runtime, integration)]
    merged_indexes = [entry_index(meta, label) for meta, label in zip(merged, MANIFESTS)]
    writes = {}
    for key in TARGET_KEYS:
        old_images = []
        for directory, index in zip(ASSET_ROOTS, indexes[:2]):
            relative = directory + '/' + key + '.png'
            path = checked_path(root, relative)
            original = path.read_bytes()
            originals[relative] = original
            if digest(original) != index[key]['sha256']:
                raise ValueError('Existing PNG checksum differs: ' + relative)
            with Image.open(BytesIO(original)) as image:
                if image.mode != 'RGBA' or image.size != (index[key]['width'], index[key]['height']):
                    raise ValueError('Existing PNG dimensions or mode differ: ' + relative)
                old_images.append(image.copy())
        if originals[ASSET_ROOTS[0] + '/' + key + '.png'] != originals[ASSET_ROOTS[1] + '/' + key + '.png']:
            raise ValueError('Source and runtime opening art differ; preserve and review before refresh: ' + key)
        if indexes[2][key].get('sha256') != indexes[0][key]['sha256']:
            raise ValueError('Integration checksum differs for ' + key)
        image = candidates[key]
        if image.mode != 'RGBA' or image.getchannel('A').getbbox() is None:
            raise ValueError('Candidate is blank or not RGBA: ' + key)
        if image.tobytes() != repeated[key].tobytes():
            raise ValueError('Candidate render is nondeterministic: ' + key)
        for old in old_images:
            if image.size != old.size or image.getchannel('A').tobytes() != old.getchannel('A').tobytes():
                raise ValueError('Candidate changes the established dimensions or alpha anchor: ' + key)
            if key in BUILDING_KEYS:
                box = lands.opening_door_box(old.size)
                if image.crop(box).tobytes() != old.crop(box).tobytes():
                    raise ValueError('Candidate changes the opening doorway: ' + key)
        encoded = png_bytes(image)
        checksum = digest(encoded)
        for directory in ASSET_ROOTS:
            writes[directory + '/' + key + '.png'] = encoded
        for index in merged_indexes:
            index[key]['sha256'] = checksum
        changes.append({'key': key, 'previous_sha256': indexes[0][key]['sha256'], 'sha256': checksum,
                        'dimensions': list(image.size), 'alpha_preserved': True,
                        'door_preserved': key in BUILDING_KEYS})
    writes[MANIFESTS[0]] = json_bytes(merged[0])
    merged[2]['source_manifest_sha256'] = digest(writes[MANIFESTS[0]])
    writes[MANIFESTS[1]] = json_bytes(merged[1])
    writes[MANIFESTS[2]] = json_bytes(merged[2])
    for relative, original in originals.items():
        if digest(original) != before.get(relative):
            raise ValueError('Asset bytes changed during preflight: ' + relative)
    writes = {relative: data for relative, data in writes.items() if data != originals[relative]}
    report = {'schema': 1, 'mode': 'check', 'selected_keys': list(TARGET_KEYS), 'assets': changes,
              'changed_files': sorted(writes), 'catalog_sha256': digest(catalog_bytes),
              'asset_files_in_inventory': len(before), 'visual_review': 'not_performed',
              'visual_acceptance': 'not_approved', 'actor_assets_changed': False}
    return RefreshPlan(root, writes, originals, before, digest(catalog_bytes), report)


def assert_unchanged(plan):
    if fingerprints(plan.root) != plan.before:
        raise ValueError('Asset bytes changed after preflight; nothing was refreshed')
    if digest(checked_path(plan.root, 'content/catalog.json').read_bytes()) != plan.catalog_hash:
        raise ValueError('Authoritative catalog changed after preflight; nothing was refreshed')


def apply_plan(plan):
    if not plan.writes:
        assert_unchanged(plan)
        return dict(plan.report, mode='apply', changed_files=[], unrelated_hashes_preserved=True)
    lease = checked_path(plan.root, 'artifacts/opening-art-refresh/.refresh-owner.lock')
    lease.parent.mkdir(parents=True, exist_ok=True)
    marker = uuid.uuid4().hex.encode('ascii')
    try:
        descriptor = os.open(lease, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError('Another opening art refresh owns the write lease; nothing was refreshed') from error
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(marker)
        return _apply_plan(plan)
    finally:
        # Never remove a lease replaced by another writer.
        if lease.is_file() and lease.read_bytes() == marker:
            lease.unlink()


def _apply_plan(plan):
    assert_unchanged(plan)
    if not plan.writes:
        return dict(plan.report, mode='apply', changed_files=[], unrelated_hashes_preserved=True)
    suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    backup_relative = 'artifacts/opening-art-refresh/' + suffix
    backup = checked_path(plan.root, backup_relative)
    backup.mkdir(parents=True, exist_ok=False)
    for relative in plan.writes:
        original = backup / 'originals' / relative
        original.parent.mkdir(parents=True, exist_ok=True)
        original.write_bytes(plan.originals[relative])
        staged = backup / 'staged' / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(plan.writes[relative])
    (backup / 'hash-inventory-before.json').write_bytes(json_bytes(plan.before))
    (backup / 'refresh-plan.json').write_bytes(json_bytes(plan.report))
    replaced = []
    try:
        assert_unchanged(plan)
        for relative in plan.writes:
            target = checked_path(plan.root, relative)
            if not target.is_file() or target.read_bytes() != plan.originals[relative]:
                raise ValueError('Selected asset changed before replacement: ' + relative)
            os.replace(backup / 'staged' / relative, target)
            replaced.append(relative)
        after = fingerprints(plan.root)
        expected = dict(plan.before)
        expected.update({relative: digest(data) for relative, data in plan.writes.items()})
        if after != expected:
            raise ValueError('Refresh did not preserve every unrelated asset hash')
        if digest(checked_path(plan.root, 'content/catalog.json').read_bytes()) != plan.catalog_hash:
            raise ValueError('Authoritative catalog changed during refresh')
    except BaseException as error:
        restored, concurrent, rollback_errors = [], [], []
        for relative in reversed(replaced):
            try:
                path = checked_path(plan.root, relative)
                # A later edit belongs to the other writer. Never erase it
                # merely because an earlier refresh replacement must roll back.
                if not path.is_file() or digest(path.read_bytes()) != digest(plan.writes[relative]):
                    concurrent.append(relative)
                    continue
                rollback = backup / 'rollback' / relative
                rollback.parent.mkdir(parents=True, exist_ok=True)
                rollback.write_bytes(plan.originals[relative])
                if not path.is_file() or digest(path.read_bytes()) != digest(plan.writes[relative]):
                    concurrent.append(relative)
                    continue
                os.replace(rollback, path)
                restored.append(relative)
            except OSError as rollback_error:
                rollback_errors.append({'path': relative, 'error': str(rollback_error)})
            except ValueError as rollback_error:
                concurrent.append(relative)
                rollback_errors.append({'path': relative, 'error': str(rollback_error)})
        failure = dict(plan.report, mode='apply_failed', backup=backup_relative, failure=str(error),
                       replaced_files=replaced, restored_files=restored,
                       concurrent_files_preserved=concurrent, rollback_errors=rollback_errors)
        try:
            remaining = fingerprints(plan.root)
            failure['remaining_changed_files'] = sorted(relative for relative in set(remaining) | set(plan.before)
                                                        if remaining.get(relative) != plan.before.get(relative))
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
    operation.add_argument('--check', action='store_true', help='render and validate in memory; write nothing (default)')
    operation.add_argument('--apply', action='store_true', help='retain backups, refresh the nine assets and merge manifests')
    args = parser.parse_args()
    plan = make_plan()
    print(json.dumps(apply_plan(plan) if args.apply else plan.report, indent=2))


if __name__ == '__main__':
    main()
