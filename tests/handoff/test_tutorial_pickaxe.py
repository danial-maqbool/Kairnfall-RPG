"""Optional held-tool rig and incremental scope checks; not artistic approval."""
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
from art.character_motion import STATES, EXTRA_STATES, DIRECTIONS, rig
from art.characters import armour_frame, body_frame, hair_frame, npc_frame, _weapon_kind
from art.common import palette, WOODS
from art.optional_equipment import equipment_definitions, optional_equipment
import refresh_tutorial_pickaxe as refresh
import validate_character_assets as strict
import integrate_atelier as integration_audit


class TutorialPickaxeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_bytes = (ROOT / 'content/catalog.json').read_bytes()
        cls.catalog = json.loads(cls.catalog_bytes)

    def fixture(self, root):
        (root / 'content').mkdir()
        (root / 'content/catalog.json').write_bytes(self.catalog_bytes)
        for name in refresh.SOURCES:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        entries = []
        for directory in refresh.ASSET_ROOTS:
            base = root / directory
            base.mkdir(parents=True)
            (base / 'catalog.json').write_bytes(self.catalog_bytes)
            (base / 'unrelated.bin').write_bytes(b'accepted nonactor and icon bytes\x00\xff')
            actor = base / 'equipment/copper_sword.png'
            actor.parent.mkdir()
            actor.write_bytes(b'accepted ordinary actor bytes')
        entry = {'key': 'equipment/copper_sword', 'width': 512, 'height': 1536,
                 'animated': True, 'state_count': 6, 'sha256': refresh.digest(b'accepted ordinary actor bytes'),
                 'pixel_sha256': 'accepted-pixels', 'extra_metadata': {'retain': 7}}
        base_keys, extra_keys = strict.expected(self.catalog)
        for key in sorted((base_keys | extra_keys) - set(refresh.TARGET_KEYS)):
            entries.append(dict(deepcopy(entry), key=key,
                                height=256 if key.startswith('motions/') else 1536,
                                state_count=1 if key.startswith('motions/') else 6))
        pack = {'schema': 1, 'library': 'wayfarer', 'actor_size': 64, 'boss_size': 128,
                'foot_anchor': [32, 55], 'boss_anchor': [64, 110], 'artistic_approval': False,
                'states': list(STATES), 'motion_states': list(EXTRA_STATES),
                'directions': list(DIRECTIONS), 'frames': 8,
                'source_sha256': {name: refresh.digest((root / name).read_bytes())
                                  for name in refresh.SOURCES if name != refresh.NEW_SOURCE},
                'provenance': {'must_remain': True}, 'assets': deepcopy(entries)}
        runtime = {'schema': 1, 'artistic_review': 'not_approved', 'frame_order': list(STATES),
                   'motion_order': list(EXTRA_STATES), 'directions': list(DIRECTIONS), 'frames_per_row': 8,
                   'atelier_assets': 1857, 'skill_icon_sources': ['retained'],
                   'assets': deepcopy(entries) + [{'key': 'items/copper_pickaxe', 'sha256': 'unchanged'}]}
        for name, metadata in zip(refresh.MANIFESTS, (pack, runtime)):
            (root / name).write_bytes(refresh.json_bytes(metadata))
        integration = {'schema': 3, 'actor_runtime_source': 'Wayfarer original joint construction',
                       'actor_historical_fallbacks': 0, 'historical_actor_bytes_active': False,
                       'catalog_ids_changed': False, 'independent_gear_ladder_imported': False,
                       'coverage': integration_audit.runtime_coverage(
                           [item['key'] for item in runtime['assets']], self.catalog, require_optional=False)[0],
                       'skipped': [{'key': 'equipment/copper_sword', 'reason': 'retained'}],
                       'assets': [{'key': 'items/copper_pickaxe', 'sha256': 'unchanged'}],
                       'source_manifest_sha256': 'retained-nonactor-library', 'integrated': 1,
                       'visual_approval': 'not_granted_by_integrity_checks'}
        (root / refresh.MANIFESTS[2]).write_bytes(refresh.json_bytes(integration))
        return root

    def force_selected_difference(self, root):
        for directory in refresh.ASSET_ROOTS:
            name = directory + '/equipment/' + refresh.ITEM_ID + '.png'
            path = root / name
            with Image.open(path) as source:
                image = source.copy()
            alpha = image.getchannel('A')
            at = next((x, y) for y in range(image.height) for x in range(image.width)
                      if alpha.getpixel((x, y)))
            image.putpixel(at, (27, 31, 37, 255))
            encoded = refresh.png_bytes(image)
            path.write_bytes(encoded)
            manifest = root / directory / 'manifest.json'
            metadata = json.loads(manifest.read_bytes())
            entry = next(entry for entry in metadata['assets'] if entry['key'] == refresh.BASE_KEY)
            entry['sha256'] = refresh.digest(encoded)
            entry['pixel_sha256'] = refresh.digest(image.tobytes())
            manifest.write_bytes(refresh.json_bytes(metadata))

    def test_descriptor_is_art_only_fresh_and_catalog_is_untouched(self):
        before = deepcopy(self.catalog)
        equipped = equipment_definitions(self.catalog)
        normal = [item for item in self.catalog['items'] if item.get('slot')]
        self.assertEqual(equipped[:-1], normal)
        self.assertEqual(equipped[-1], optional_equipment()[0])
        self.assertEqual(len(equipped), len(normal) + 1)
        equipped[-1]['tags'].append('mutated')
        self.assertEqual(optional_equipment()[0]['tags'], ['pickaxe'])
        self.assertEqual(self.catalog, before)
        self.assertTrue({'power', 'rewards', 'stats', 'value'}.isdisjoint(optional_equipment()[0]))
        collision = deepcopy(self.catalog)
        collision['items'].append(optional_equipment()[0])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            equipment_definitions(collision)

    def test_pickaxe_precedes_axe_and_no_ordinary_equipment_family_changes(self):
        self.assertEqual(_weapon_kind(optional_equipment()[0]), 'pickaxe')
        self.assertEqual(_weapon_kind({'id': 'copper_pickaxe', 'tags': []}), 'pickaxe')
        self.assertEqual(_weapon_kind({'id': 'work_tool', 'tags': ['pickaxe', 'axe']}), 'pickaxe')
        for item in self.catalog['items']:
            if not item.get('slot'):
                continue
            old = next((kind for kind in ('crossbow', 'bow', 'spear', 'staff', 'wand', 'dagger', 'axe', 'mace', 'sword')
                        if kind in item.get('tags', []) or kind in item['id']), 'sword')
            self.assertEqual(_weapon_kind(item), old, item['id'])

    def test_every_action_direction_cell_is_deterministic_inside_bounds_and_grips_hand(self):
        item = optional_equipment()[0]
        before = deepcopy(item)
        cells = 0
        for state in STATES + EXTRA_STATES:
            for direction in range(4):
                for number in range(8):
                    with self.subTest(state=state, direction=direction, frame=number):
                        image = armour_frame(item, state, number, direction)
                        self.assertEqual(image.tobytes(), armour_frame(item, state, number, direction).tobytes())
                        self.assertEqual((image.mode, image.size), ('RGBA', (64, 64)))
                        box = image.getchannel('A').getbbox()
                        self.assertIsNotNone(box)
                        self.assertTrue(0 < box[0] < box[2] < 64 and 0 < box[1] < box[3] < 64, box)
                        joints = rig(state, number, direction)
                        if joints['collapse'] <= .6:
                            x, y = joints['hand_r']
                            self.assertGreater(image.getchannel('A').getpixel((x, y)), 0)
                        cells += 1
        self.assertEqual(cells, 352)
        self.assertEqual(item, before)

    def test_collapsed_tool_is_low_grounded_stable_and_not_rotated_standing_art(self):
        item = optional_equipment()[0]
        for direction in range(4):
            idle = armour_frame(item, 'idle', 0, direction)
            dead = armour_frame(item, 'death', 7, direction)
            alpha = dead.getchannel('A')
            # A visible transverse head spans the ground plane. Preserve the
            # low released attachment while testing the newly authored points.
            self.assertTrue(48 <= alpha.getbbox()[1] < 55 < alpha.getbbox()[3] <= 62)
            self.assertGreater(sum(alpha.getpixel((x, 55)) > 0 for x in range(64)), 15)
            self.assertEqual(dead.tobytes(), armour_frame(item, 'death', 6, direction).tobytes())
            for angle in (90, 180, 270):
                self.assertNotEqual(dead.tobytes(), idle.rotate(angle).tobytes())

    def test_raised_working_head_remains_visible_outside_all_authored_hair(self):
        item = optional_equipment()[0]
        stone = set(palette('7d8175'))
        for state in ('interact', 'craft'):
            for direction in range(4):
                for number in (2, 3):
                    tool = armour_frame(item, state, number, direction)
                    for style in range(6):
                        hair = hair_frame(style, 1, state, number, direction)
                        occluded = sum(pixel in stone and bool(hair_pixel[3])
                                       for pixel, hair_pixel in zip(tool.getdata(), hair.getdata()))
                        self.assertEqual(occluded, 0, (state, direction, number, style))

    def test_contact_preserves_a_visible_wooden_haft_in_each_direction(self):
        item = optional_equipment()[0]
        wood = {palette(WOODS['oak'])[index] for index in (1, 3, 4)}
        for direction in range(4):
            for number in (3, 4, 5):
                image = armour_frame(item, 'attack', number, direction)
                # Count actual material pixels, rather than mirroring the
                # angle/length algorithm. The previous contact lost the haft.
                self.assertGreaterEqual(sum(pixel in wood for pixel in image.getdata()), 48,
                                        (direction, number))

    def test_released_head_retains_transverse_points_at_original_size(self):
        item = optional_equipment()[0]
        stone = set(palette('7d8175'))
        for direction in range(4):
            image = armour_frame(item, 'death', 7, direction)
            ys = [y for y in range(64) for x in range(64) if image.getpixel((x, y)) in stone]
            self.assertGreaterEqual(max(ys) - min(ys), 10)
            self.assertLess(min(ys), 55)
            self.assertGreater(max(ys), 55)

    def test_strict_expected_coverage_requires_exactly_six_optional_sheets(self):
        base, extra = strict.expected(self.catalog)
        self.assertEqual(len(base | extra), 6751)
        self.assertIn(refresh.BASE_KEY, base)
        self.assertTrue(set(refresh.TARGET_KEYS[1:]).issubset(extra))
        self.assertEqual(len([key for key in base | extra if key.endswith('/' + refresh.ITEM_ID)]), 6)
        candidates = refresh.render_candidates()
        self.assertEqual(set(candidates), set(refresh.TARGET_KEYS))
        self.assertEqual(candidates[refresh.BASE_KEY].size, (512, 1536))
        self.assertTrue(all(candidates[key].size == (512, 256) for key in refresh.TARGET_KEYS[1:]))

    def test_ordinary_drawings_still_match_retained_wayfarer_pixels(self):
        # Compare actual retained cells, not screenshots or generated uniqueness.
        representatives = {}
        for item in self.catalog['items']:
            if item.get('slot') == 'weapon':
                representatives.setdefault((_weapon_kind(item), item.get('material')), item)
        draws = [('equipment/' + item['id'], lambda state, number, direction, item=item:
                  armour_frame(item, state, number, direction)) for item in representatives.values()]
        draws += [('people/body_0_2', lambda state, number, direction: body_frame(0, 2, state, number, direction)),
                  ('people/hair_4_3', lambda state, number, direction: hair_frame(4, 3, state, number, direction))]
        draws += [('npcs/' + role, lambda state, number, direction, role=role:
                   npc_frame(role, state, number, direction))
                  for role in sorted({npc['role'] for npc in self.catalog['npcs']})]
        for key, draw in draws:
            for state in STATES + EXTRA_STATES:
                path = ROOT / 'art/wayfarer/Assets' / (
                    'motions/' + state + '/' + key + '.png' if state in EXTRA_STATES else key + '.png')
                with Image.open(path) as source:
                    for direction in range(4):
                        row = direction if state in EXTRA_STATES else STATES.index(state) * 4 + direction
                        for number in (0, 3, 7):
                            actual = source.crop((number * 64, row * 64, (number + 1) * 64, (row + 1) * 64))
                            self.assertEqual(actual.tobytes(), draw(state, number, direction).tobytes(),
                                             f'{key}/{state}/{direction}/{number}')

    def test_default_check_writes_nothing_and_proposes_only_selected_sheets_and_manifests(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            before = refresh.fingerprints(root)
            plan = refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)
            self.assertFalse((root / 'artifacts').exists())
            allowed = set(refresh.MANIFESTS) | {directory + '/' + key + '.png'
                       for directory in refresh.ASSET_ROOTS for key in refresh.TARGET_KEYS}
            self.assertEqual(set(plan.writes), allowed)
            self.assertEqual(len(plan.writes), 15)
            self.assertEqual(plan.report['visual_acceptance'], 'not_approved')
            self.assertEqual(plan.report['native_rendering'], 'not_performed')

    def test_apply_backs_up_merges_preserves_catalog_unrelated_assets_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            plan = refresh.make_plan(root)
            old = [json.loads((root / name).read_bytes()) for name in refresh.MANIFESTS]
            report = refresh.apply_plan(plan)
            self.assertTrue(report['unrelated_hashes_preserved'])
            self.assertEqual((root / 'content/catalog.json').read_bytes(), self.catalog_bytes)
            after = refresh.fingerprints(root)
            self.assertEqual({key: value for key, value in after.items() if key not in plan.writes},
                             {key: value for key, value in plan.before.items() if key not in plan.writes})
            for name, previous in zip(refresh.MANIFESTS[:2], old[:2]):
                current = json.loads((root / name).read_bytes())
                retained = {entry['key']: entry for entry in current['assets']
                            if entry['key'] not in refresh.TARGET_KEYS}
                self.assertEqual(retained, {entry['key']: entry for entry in previous['assets']})
                for key, value in previous.items():
                    if key not in ('assets', 'source_sha256'):
                        self.assertEqual(current[key], value)
                self.assertEqual(len(current['assets']), len(previous['assets']) + 6)
                self.assertEqual((root / report['backup'] / 'originals' / name).read_bytes(), plan.originals[name])
            current = json.loads((root / refresh.MANIFESTS[2]).read_bytes())
            self.assertEqual(current['coverage'], old[2]['coverage'])
            self.assertEqual(current['coverage']['equipment'], len([item for item in self.catalog['items'] if item.get('slot')]))
            self.assertEqual(current['optional_actor_equipment'], [refresh.ITEM_ID])
            self.assertEqual(current['assets'], old[2]['assets'])
            for key, value in old[2].items():
                if key not in ('coverage', 'skipped', 'optional_actor_equipment'):
                    self.assertEqual(current[key], value)
            self.assertEqual([entry for entry in current['skipped'] if entry['key'] != refresh.BASE_KEY], old[2]['skipped'])
            self.assertEqual(len(json.loads((root / report['backup'] / 'previously-absent-files.json').read_bytes())), 12)
            self.assertEqual(refresh.make_plan(root).writes, {})

    def test_all_changes_after_preflight_are_refused_without_asset_mutation(self):
        for source in (False, True):
            with tempfile.TemporaryDirectory() as temp:
                root = self.fixture(Path(temp))
                plan = refresh.make_plan(root)
                path = root / (refresh.CHANGED_RENDERER if source else 'client/Assets/unrelated.bin')
                path.write_bytes(b'accepted concurrent work')
                before = refresh.fingerprints(root)
                with self.assertRaisesRegex(ValueError, 'changed after preflight'):
                    refresh.apply_plan(plan)
                self.assertEqual(refresh.fingerprints(root), before)

    def test_writer_lease_is_exclusive_and_another_writers_lease_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            plan = refresh.make_plan(root)
            lease = root / 'artifacts/tutorial-pickaxe-refresh/.refresh-owner.lock'
            lease.parent.mkdir(parents=True)
            lease.write_bytes(b'another writer')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'write lease'):
                refresh.apply_plan(plan)
            self.assertEqual(refresh.fingerprints(root), before)
            self.assertEqual(lease.read_bytes(), b'another writer')

    def test_concurrently_created_target_is_not_overwritten_and_our_added_sheets_roll_back(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            plan = refresh.make_plan(root)
            first, second = list(plan.writes)[:2]
            link = refresh.os.link
            calls = []

            def add_other_writer(source, destination):
                calls.append(str(destination))
                if len(calls) == 2:
                    Path(destination).write_bytes(b'another new accepted sheet')
                link(source, destination)

            with patch.object(refresh.os, 'link', side_effect=add_other_writer):
                with self.assertRaises(refresh.RefreshApplyError) as raised:
                    refresh.apply_plan(plan)
            self.assertFalse((root / first).exists())
            self.assertEqual((root / second).read_bytes(), b'another new accepted sheet')
            self.assertEqual(raised.exception.report['remaining_changed_files'], [second])
            self.assertTrue(raised.exception.report['partial_state'])

    def test_existing_targets_are_checked_per_replace_and_rollback_uses_atomic_replace(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            self.force_selected_difference(root)
            plan = refresh.make_plan(root)
            first, second = list(plan.writes)[:2]
            replace = refresh.os.replace
            calls = []

            def edit_next(source, destination):
                calls.append((Path(source), Path(destination)))
                replace(source, destination)
                if len(calls) == 1:
                    (root / second).write_bytes(b'accepted edit during refresh')

            with patch.object(refresh.os, 'replace', side_effect=edit_next):
                with self.assertRaisesRegex(refresh.RefreshApplyError, 'changed before replacement') as raised:
                    refresh.apply_plan(plan)
            self.assertEqual((root / first).read_bytes(), plan.originals[first])
            self.assertEqual((root / second).read_bytes(), b'accepted edit during refresh')
            self.assertEqual(len(calls), 2)
            self.assertIn('rollback', calls[-1][0].parts)
            self.assertEqual(raised.exception.report['remaining_changed_files'], [second])

    def test_partial_tool_sets_bad_checksums_and_unrelated_renderer_drift_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            plan = refresh.make_plan(root)
            runtime = root / refresh.MANIFESTS[1]
            metadata = json.loads(runtime.read_bytes())
            metadata['assets'].append(plan.report['assets'][0])
            runtime.write_bytes(refresh.json_bytes(metadata))
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'incomplete'):
                refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            (root / 'client/Assets/equipment/classic_stone_pickaxe.png').write_bytes(b'corrupt')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'checksum'):
                refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            (root / 'tools/art/character_motion.py').write_bytes(b'new unrelated rig')
            with self.assertRaisesRegex(ValueError, 'Unrelated renderer'):
                refresh.make_plan(root)

    def test_catalog_mismatch_duplicate_manifest_keys_and_path_escape_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            (root / 'client/Assets/catalog.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'catalogs differ'):
                refresh.make_plan(root)
            for name in ('../outside', '/absolute', 'C:/outside', 'client\\Assets', 'client/../Assets'):
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    refresh.checked_path(root, name)
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            runtime = root / refresh.MANIFESTS[1]
            metadata = json.loads(runtime.read_bytes())
            metadata['assets'].append(deepcopy(metadata['assets'][0]))
            runtime.write_bytes(refresh.json_bytes(metadata))
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                refresh.make_plan(root)

    def test_loaded_source_guard_refuses_new_unloaded_descriptor_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            (root / refresh.NEW_SOURCE).write_bytes(b'new descriptor not loaded by this process')
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'loaded drawing code'):
                refresh.make_plan(root)
            self.assertEqual(refresh.fingerprints(root), before)

    def test_copied_historical_actors_or_stale_integration_coverage_are_refused(self):
        for corrupt in ('copy', 'coverage'):
            with tempfile.TemporaryDirectory() as temp:
                root = self.fixture(Path(temp))
                path = root / refresh.MANIFESTS[2]
                metadata = json.loads(path.read_bytes())
                if corrupt == 'copy':
                    metadata['assets'].append({'key': 'equipment/retired_pickaxe', 'sha256': 'rejected'})
                else:
                    metadata['coverage']['equipment'] += 1
                path.write_bytes(refresh.json_bytes(metadata))
                before = refresh.fingerprints(root)
                with self.assertRaisesRegex(ValueError, 'Historical actor bytes|coverage'):
                    refresh.make_plan(root)
                self.assertEqual(refresh.fingerprints(root), before)

    def test_optional_metadata_absent_malformed_wrong_or_duplicated_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            path = root / refresh.MANIFESTS[2]
            original = json.loads(path.read_bytes())
            for value in ('absent', None, [], {}, refresh.ITEM_ID, ['unknown_tool'],
                          [refresh.ITEM_ID, refresh.ITEM_ID], [refresh.ITEM_ID, 'unknown_tool']):
                with self.subTest(value=value):
                    metadata = deepcopy(original)
                    if value == 'absent':
                        metadata.pop('optional_actor_equipment')
                    else:
                        metadata['optional_actor_equipment'] = value
                    path.write_bytes(refresh.json_bytes(metadata))
                    before = refresh.fingerprints(root)
                    with self.assertRaisesRegex(ValueError, 'Optional actor equipment metadata'):
                        refresh.make_plan(root)
                    with self.assertRaisesRegex(ValueError, 'supported aggregate'):
                        refresh.make_plan(root, migrate_aggregate_coverage=True)
                    self.assertEqual(refresh.fingerprints(root), before)

    def test_explicit_aggregate_migration_changes_only_audit_and_retains_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            path = root / refresh.MANIFESTS[2]
            aggregate = json.loads(path.read_bytes())
            aggregate.pop('optional_actor_equipment')
            aggregate['coverage']['equipment'] += 1
            path.write_bytes(refresh.json_bytes(aggregate))
            original = path.read_bytes()
            before = refresh.fingerprints(root)
            with self.assertRaisesRegex(ValueError, 'coverage'):
                refresh.make_plan(root)
            plan = refresh.make_plan(root, migrate_aggregate_coverage=True)
            self.assertEqual(set(plan.writes), {refresh.MANIFESTS[2]})
            self.assertTrue(plan.report['aggregate_coverage_migrated'])
            self.assertEqual(refresh.fingerprints(root), before)
            report = refresh.apply_plan(plan)
            current = json.loads(path.read_bytes())
            self.assertEqual(current['optional_actor_equipment'], [refresh.ITEM_ID])
            self.assertEqual(current['coverage']['equipment'], aggregate['coverage']['equipment'] - 1)
            self.assertEqual(current['assets'], aggregate['assets'])
            self.assertEqual(current['skipped'], aggregate['skipped'])
            self.assertEqual((root / report['backup'] / 'originals' / refresh.MANIFESTS[2]).read_bytes(), original)
            after = refresh.fingerprints(root)
            self.assertEqual({key: digest for key, digest in after.items() if key != refresh.MANIFESTS[2]},
                             {key: digest for key, digest in before.items() if key != refresh.MANIFESTS[2]})
            self.assertEqual((root / 'content/catalog.json').read_bytes(), self.catalog_bytes)
            self.assertEqual(refresh.make_plan(root).writes, {})
            with self.assertRaisesRegex(ValueError, 'supported aggregate'):
                refresh.make_plan(root, migrate_aggregate_coverage=True)

    def test_aggregate_migration_refuses_stale_sources_wrong_counts_or_bad_ownership(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            path = root / refresh.MANIFESTS[2]
            pack_path = root / refresh.MANIFESTS[0]
            aggregate = json.loads(path.read_bytes())
            aggregate.pop('optional_actor_equipment')
            aggregate['coverage']['equipment'] += 1
            pack = json.loads(pack_path.read_bytes())
            for corrupt in ('count', 'reason', 'source', 'bool'):
                with self.subTest(corrupt=corrupt):
                    metadata = deepcopy(aggregate)
                    pack_metadata = deepcopy(pack)
                    if corrupt == 'count':
                        metadata['coverage']['equipment'] += 1
                    elif corrupt == 'reason':
                        next(entry for entry in metadata['skipped'] if entry['key'] == refresh.BASE_KEY)['reason'] = 'unknown owner'
                    elif corrupt == 'source':
                        pack_metadata['source_sha256'][refresh.CHANGED_RENDERER] = 'stale'
                    else:
                        metadata['coverage']['items'] = True
                    path.write_bytes(refresh.json_bytes(metadata))
                    pack_path.write_bytes(refresh.json_bytes(pack_metadata))
                    before = refresh.fingerprints(root)
                    with self.assertRaisesRegex(ValueError, 'supported aggregate|ownership skip'):
                        refresh.make_plan(root, migrate_aggregate_coverage=True)
                    self.assertEqual(refresh.fingerprints(root), before)

    def test_full_actor_contract_refuses_ordinary_omissions_and_arbitrary_extras(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            originals = [json.loads((root / name).read_bytes()) for name in refresh.MANIFESTS[:2]]
            for corrupt in ('ordinary_missing', 'equipment/unknown_tool',
                            'motions/craft/equipment/unknown_tool', 'npcs/unknown_role'):
                with self.subTest(corrupt=corrupt):
                    for name, original in zip(refresh.MANIFESTS[:2], originals):
                        metadata = deepcopy(original)
                        if corrupt == 'ordinary_missing':
                            metadata['assets'] = [entry for entry in metadata['assets']
                                                  if entry['key'] != 'motions/craft/equipment/copper_sword']
                        else:
                            metadata['assets'].append(dict(metadata['assets'][0], key=corrupt))
                        (root / name).write_bytes(refresh.json_bytes(metadata))
                    before = refresh.fingerprints(root)
                    with self.assertRaisesRegex(ValueError, 'Actor manifest differs'):
                        refresh.make_plan(root)
                    self.assertEqual(refresh.fingerprints(root), before)

    def test_metadata_only_migration_failure_preserves_all_assets_and_catalog(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.fixture(Path(temp))
            refresh.apply_plan(refresh.make_plan(root))
            path = root / refresh.MANIFESTS[2]
            aggregate = json.loads(path.read_bytes())
            aggregate.pop('optional_actor_equipment')
            aggregate['coverage']['equipment'] += 1
            path.write_bytes(refresh.json_bytes(aggregate))
            plan = refresh.make_plan(root, migrate_aggregate_coverage=True)
            before = refresh.fingerprints(root)
            with patch.object(refresh.os, 'replace', side_effect=OSError('simulated audit replace failure')):
                with self.assertRaises(refresh.RefreshApplyError) as raised:
                    refresh.apply_plan(plan)
            self.assertFalse(raised.exception.report['partial_state'])
            self.assertEqual(refresh.fingerprints(root), before)
            self.assertEqual((root / 'content/catalog.json').read_bytes(), self.catalog_bytes)
            self.assertEqual((root / raised.exception.report['backup'] / 'originals' / refresh.MANIFESTS[2]).read_bytes(),
                             plan.originals[refresh.MANIFESTS[2]])


if __name__ == '__main__':
    unittest.main()
