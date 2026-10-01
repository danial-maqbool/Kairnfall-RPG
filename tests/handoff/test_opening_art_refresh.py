"""Opening-art scope and anchor regressions; these do not approve artwork."""
from copy import deepcopy
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import refresh_opening_art as refresh
from atelier.forge import lands, smith
from atelier.forge.brush import Sketch
from atelier.forge.pigment import ramp


class OpeningArtRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_bytes = (ROOT / 'content/catalog.json').read_bytes()
        cls.catalog = json.loads(cls.catalog_bytes)
        cls.zone = next(zone for zone in cls.catalog['zones'] if zone['id'] == 'wayfarers_rest')

    def fixture(self, root):
        (root / 'content').mkdir()
        (root / 'content/catalog.json').write_bytes(self.catalog_bytes)
        source_entries, runtime_entries, integrated_entries = [], [], []
        for directory in refresh.ASSET_ROOTS:
            (root / directory).mkdir(parents=True)
            (root / directory / 'catalog.json').write_bytes(self.catalog_bytes)
            (root / directory / 'unrelated.bin').write_bytes(b'preserve unrelated accepted bytes\x00\xff')
        for key in refresh.TARGET_KEYS:
            original = (ROOT / 'atelier/Assets' / (key + '.png')).read_bytes()
            with Image.open(BytesIO(original)) as image:
                width, height = image.size
            entry = {'key': key, 'width': width, 'height': height,
                     'sha256': refresh.digest(original), 'animated': False}
            source_entries.append(dict(entry, group=key.split('/')[0]))
            runtime_entries.append(entry)
            integrated_entries.append({'key': key, 'sha256': entry['sha256']})
            for directory in refresh.ASSET_ROOTS:
                path = root / directory / (key + '.png')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
        # An untouched actor and its extra metadata must survive the partial
        # update even though this tool never regenerates or approves actors.
        key = 'people/body_0_0'
        actor = root / 'client/Assets' / (key + '.png')
        actor.parent.mkdir()
        actor.write_bytes(b'untouched actor fixture')
        runtime_entries.append({'key': key, 'width': 512, 'height': 1536, 'animated': True,
                                'sha256': refresh.digest(actor.read_bytes()), 'pixel_sha256': 'preserved'})
        untouched_key = 'terrain/grass_0'
        untouched = refresh.png_bytes(Image.new('RGBA', (32, 32), (43, 62, 41, 255)))
        for directory in refresh.ASSET_ROOTS:
            path = root / directory / (untouched_key + '.png')
            path.parent.mkdir(parents=True)
            path.write_bytes(untouched)
        untouched_entry = {'key': untouched_key, 'width': 32, 'height': 32, 'animated': False,
                           'sha256': refresh.digest(untouched), 'provenance': {'source': 'unrelated', 'revision': 7}}
        source_entries.append(dict(untouched_entry, group='terrain'))
        runtime_entries.append(deepcopy(untouched_entry))
        integrated_entries.append({'key': untouched_key, 'sha256': refresh.digest(untouched)})
        source = {'schema': 1, 'library': 'atelier', 'artistic_review': 'pending',
                  'foot_baseline': 55, 'assets': source_entries}
        runtime = {'schema': 1, 'artistic_review': 'not_approved', 'atelier_assets': 9,
                   'frame_order': ['idle', 'walk', 'attack', 'cast', 'hit', 'death'], 'assets': runtime_entries}
        (root / refresh.MANIFESTS[0]).write_bytes(refresh.json_bytes(source))
        (root / refresh.MANIFESTS[1]).write_bytes(refresh.json_bytes(runtime))
        integration = {'schema': 3, 'source': 'atelier/Assets',
                       'source_manifest_sha256': refresh.digest(refresh.json_bytes(source)),
                       'integrated': 9, 'groups': {'buildings': 4, 'items': 5},
                       'coverage': {'people': 1, 'buildings': 4, 'items': 5},
                       'skipped': [{'key': key, 'reason': 'Wayfarer actor source'}],
                       'actor_runtime_source': 'Wayfarer original joint construction',
                       'actor_historical_fallbacks': 0, 'historical_actor_bytes_active': False,
                       'visual_approval': 'not_granted_by_integrity_checks', 'assets': integrated_entries}
        (root / refresh.MANIFESTS[2]).write_bytes(refresh.json_bytes(integration))
        return root

    def force_candidate_difference(self, root):
        """A selected PNG really changes even after real assets are refreshed."""
        key = refresh.RUNE_KEYS[-1]
        path = root / 'atelier/Assets' / (key + '.png')
        with Image.open(path) as image:
            image = image.copy()
        r, g, b, a = image.getpixel((16, 16))
        image.putpixel((16, 16), ((r + 17) % 255, g, b, a))
        data = refresh.png_bytes(image)
        checksum = refresh.digest(data)
        for directory, manifest in zip(refresh.ASSET_ROOTS, refresh.MANIFESTS[:2]):
            (root / directory / (key + '.png')).write_bytes(data)
            metadata = json.loads((root / manifest).read_bytes())
            next(entry for entry in metadata['assets'] if entry['key'] == key)['sha256'] = checksum
            (root / manifest).write_bytes(refresh.json_bytes(metadata))
        path = root / refresh.MANIFESTS[2]
        metadata = json.loads(path.read_bytes())
        next(entry for entry in metadata['assets'] if entry['key'] == key)['sha256'] = checksum
        metadata['source_manifest_sha256'] = refresh.digest((root / refresh.MANIFESTS[0]).read_bytes())
        path.write_bytes(refresh.json_bytes(metadata))

    def test_opening_facades_preserve_shipped_alpha_door_and_catalog_definitions(self):
        seen = set()
        for definition in self.zone['buildings']:
            if definition['id'] not in lands.OPENING_FACADE_ROLES:
                continue
            before = deepcopy(definition)
            image = lands.building(self.zone, definition)
            with Image.open(ROOT / 'atelier/Assets/buildings/wayfarers_rest' / (definition['id'] + '.png')) as old:
                self.assertEqual(image.size, (224, 224))
                self.assertEqual(image.getchannel('A').tobytes(), old.getchannel('A').tobytes())
                box = lands.opening_door_box(image.size)
                self.assertEqual(image.crop(box).tobytes(), old.crop(box).tobytes())
            self.assertEqual(definition, before)
            self.assertEqual(image.tobytes(), lands.building(self.zone, definition).tobytes())
            seen.add(image.tobytes())
        self.assertEqual(len(seen), 4)

    def test_other_buildings_keep_the_existing_renderer(self):
        definition = deepcopy(self.zone['buildings'][0])
        definition['id'] = 'other-inn'
        self.assertEqual(lands.building(self.zone, definition).tobytes(),
                         lands._building_shell(self.zone, definition).tobytes())
        definition['id'] = 'starter_building_0'
        other_zone = dict(self.zone, id='different-zone')
        self.assertEqual(lands.building(other_zone, definition).tobytes(),
                         lands._building_shell(other_zone, definition).tobytes())

    def test_early_rune_glyphs_differ_in_shape_without_changing_item_geometry(self):
        masks = []
        for ident in sorted(smith.OPENING_RUNE_GLYPHS):
            item = next(item for item in self.catalog['items'] if item['id'] == ident)
            before = deepcopy(item)
            image = smith.icon(item)
            with Image.open(ROOT / 'atelier/Assets/items' / (ident + '.png')) as old:
                self.assertEqual(image.size, (32, 32))
                self.assertEqual(image.getchannel('A').tobytes(), old.getchannel('A').tobytes())
            self.assertEqual(item, before)
            sketch = Sketch(32)
            mark = sketch.piece(ramp('#eeeeee'))
            smith._opening_rune_glyph(mark, ident)
            masks.append(mark.image.getchannel('A').tobytes())
        # Readability still needs actual pixel inspection. This catches a
        # palette-only replacement or a shared glyph under distinct IDs.
        for left in range(len(masks)):
            for right in range(left + 1, len(masks)):
                self.assertGreater(sum(a != b for a, b in zip(masks[left], masks[right])), 30)

    def test_check_writes_nothing_and_only_proposes_selected_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            before = refresh.fingerprints(root)
            plan = refresh.make_plan(root)
            self.assertEqual(before, refresh.fingerprints(root))
            self.assertFalse((root / 'artifacts').exists())
            allowed = set(refresh.MANIFESTS) | {directory + '/' + key + '.png'
                       for directory in refresh.ASSET_ROOTS for key in refresh.TARGET_KEYS}
            self.assertLessEqual(set(plan.writes), allowed)
            self.assertEqual(plan.report['visual_acceptance'], 'not_approved')
            self.assertFalse(plan.report['actor_assets_changed'])

    def test_apply_merges_metadata_and_preserves_all_unrelated_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            self.force_candidate_difference(root)
            before = refresh.fingerprints(root)
            metadata_before = [json.loads((root / relative).read_bytes()) for relative in refresh.MANIFESTS]
            plan = refresh.make_plan(root)
            report = refresh.apply_plan(plan)
            after = refresh.fingerprints(root)
            for relative, checksum in before.items():
                if relative not in plan.writes:
                    self.assertEqual(after[relative], checksum, relative)
            for relative, contents in plan.writes.items():
                self.assertEqual((root / relative).read_bytes(), contents)
            for relative, original in zip(refresh.MANIFESTS, metadata_before):
                merged = json.loads((root / relative).read_bytes())
                for key, value in original.items():
                    if key not in ('assets', 'source_manifest_sha256'):
                        self.assertEqual(merged[key], value, (relative, key))
                self.assertEqual(len(merged['assets']), len(original['assets']))
                for old, new in zip(original['assets'], merged['assets']):
                    self.assertEqual(old['key'], new['key'])
                    if old['key'] not in refresh.TARGET_KEYS:
                        self.assertEqual(old, new)
                    self.assertEqual({k: v for k, v in old.items() if k != 'sha256'},
                                     {k: v for k, v in new.items() if k != 'sha256'})
            if plan.writes:
                backup = root / report['backup']
                for relative in plan.writes:
                    self.assertEqual((backup / 'originals' / relative).read_bytes(), plan.originals[relative])
                self.assertEqual(json.loads((backup / 'hash-inventory-before.json').read_bytes()), before)
            again = refresh.make_plan(root)
            self.assertEqual(again.writes, {})
            self.assertTrue(report['unrelated_hashes_preserved'])

    def test_failed_replacement_restores_original_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            self.force_candidate_difference(root)
            plan = refresh.make_plan(root)
            self.assertGreaterEqual(len(plan.writes), 2)
            before = refresh.fingerprints(root)
            replace = refresh.os.replace
            calls = 0

            def fail_second(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected replacement failure')
                replace(source, destination)

            with patch.object(refresh.os, 'replace', side_effect=fail_second):
                with self.assertRaisesRegex(refresh.RefreshApplyError, 'injected') as raised:
                    refresh.apply_plan(plan)
            self.assertEqual(refresh.fingerprints(root), before)
            self.assertFalse(raised.exception.report['partial_state'])
            self.assertEqual(raised.exception.report['concurrent_files_preserved'], [])

    def test_rollback_preserves_selected_file_changed_by_a_later_writer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            self.force_candidate_difference(root)
            plan = refresh.make_plan(root)
            first = next(iter(plan.writes))
            self.assertTrue(first.endswith('.png'))
            later_bytes = b'concurrent writer bytes must survive rollback'
            replace = refresh.os.replace
            calls = 0

            def concurrent_then_fail(source, destination):
                nonlocal calls
                calls += 1
                if calls == 2:
                    (root / first).write_bytes(later_bytes)
                    raise OSError('injected failure after another writer changed the first replacement')
                replace(source, destination)

            with patch.object(refresh.os, 'replace', side_effect=concurrent_then_fail):
                with self.assertRaises(refresh.RefreshApplyError) as raised:
                    refresh.apply_plan(plan)
            self.assertEqual((root / first).read_bytes(), later_bytes)
            report = raised.exception.report
            self.assertTrue(report['partial_state'])
            self.assertEqual(report['concurrent_files_preserved'], [first])
            self.assertEqual(report['remaining_changed_files'], [first])
            backup = root / report['backup']
            self.assertEqual((backup / 'originals' / first).read_bytes(), plan.originals[first])
            self.assertEqual(json.loads((backup / 'refresh-failure.json').read_bytes()), report)

    def test_stale_preflight_refuses_to_overwrite_new_unrelated_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            plan = refresh.make_plan(root)
            path = root / 'client/Assets/unrelated.bin'
            path.write_bytes(b'new accepted work')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'changed after preflight'):
                refresh.apply_plan(plan)
            self.assertEqual(refresh.fingerprints(root), before)

    def test_pending_selected_edit_is_preserved_and_previous_replace_rolls_back_atomically(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            self.force_candidate_difference(root)
            plan = refresh.make_plan(root)
            first, second = list(plan.writes)[:2]
            later = b'accepted edit arriving after the first replacement'
            replace = refresh.os.replace
            replacements = []

            def edit_next(source, destination):
                replacements.append((Path(source), Path(destination)))
                replace(source, destination)
                if len(replacements) == 1:
                    (root / second).write_bytes(later)

            with patch.object(refresh.os, 'replace', side_effect=edit_next):
                with self.assertRaisesRegex(refresh.RefreshApplyError, 'changed before replacement') as raised:
                    refresh.apply_plan(plan)
            self.assertEqual((root / second).read_bytes(), later)
            self.assertEqual((root / first).read_bytes(), plan.originals[first])
            self.assertEqual(len(replacements), 2)
            self.assertIn('rollback', replacements[-1][0].parts)
            self.assertEqual(raised.exception.report['remaining_changed_files'], [second])
            self.assertTrue(raised.exception.report['partial_state'])
            self.assertFalse((root / 'artifacts/opening-art-refresh/.refresh-owner.lock').exists())

    def test_existing_write_lease_refuses_all_asset_mutation_and_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            self.force_candidate_difference(root)
            plan = refresh.make_plan(root)
            lease = root / 'artifacts/opening-art-refresh/.refresh-owner.lock'
            lease.parent.mkdir(parents=True)
            lease.write_bytes(b'another active writer')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'write lease'):
                refresh.apply_plan(plan)
            self.assertEqual(refresh.fingerprints(root), before)
            self.assertEqual(lease.read_bytes(), b'another active writer')

    def test_corrupt_checksum_and_duplicate_entries_refuse_all_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            image = root / 'client/Assets' / (refresh.TARGET_KEYS[-1] + '.png')
            image.write_bytes(b'corrupt')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            path = root / refresh.MANIFESTS[1]
            manifest = json.loads(path.read_bytes())
            manifest['assets'].append(deepcopy(manifest['assets'][0]))
            path.write_bytes(refresh.json_bytes(manifest))
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)

    def test_authoritative_catalog_mismatch_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            (root / 'client/Assets/catalog.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'catalogs differ'):
                refresh.make_plan(root)
            with self.assertRaisesRegex(ValueError, 'escapes'):
                refresh.checked_path(root, '../outside')


if __name__ == '__main__':
    unittest.main()
