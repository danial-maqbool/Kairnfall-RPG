"""Regression checks for reviewed art. These checks are not visual approval."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'atelier'), str(ROOT / 'foundry')]
from forge import brush, lands, pigment
from kit import face, ground


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


preview = load('foundry_preview_checks', ROOT / 'foundry/preview.py')
atelier_build = load('atelier_build_checks', ROOT / 'atelier/build.py')


class CliffChecks(unittest.TestCase):
    def test_existing_keys_and_new_feet_are_exported_in_all_variants(self):
        keys = {key for key, _ in ground.plan()}
        for shape in ground.CLIFF_PIECES:
            for variant in range(4):
                key = 'ground/cliff_' + shape + ('_' + str(variant) if variant else '')
                self.assertIn(key, keys)
                image = ground.cliff(shape, variant)
                self.assertEqual(image.size, (32, 32))
                self.assertEqual(image.mode, 'RGBA')
                self.assertIsNotNone(image.getchannel('A').getbbox())

    def test_horizontal_sockets_all_variant_pairs(self):
        joins = [('top', 'top'), ('face', 'face'), ('corner_left', 'top'),
                 ('top', 'corner_right'), ('left', 'face'), ('face', 'right'),
                 ('top', 'inner_right'), ('inner_left', 'top'),
                 ('inner_right', 'face'), ('face', 'inner_left'),
                 ('foot_left', 'foot'), ('foot', 'foot'), ('foot', 'foot_right')]
        for first, second in joins:
            for a in range(4):
                for b in range(4):
                    with self.subTest(first=first, second=second, a=a, b=b):
                        left, right = ground.cliff(first, a), ground.cliff(second, b)
                        self.assertEqual(left.crop((31, 0, 32, 32)).tobytes(),
                                         right.crop((0, 0, 1, 32)).tobytes())

    def test_vertical_sockets_and_inner_turns(self):
        joins = [('top', 'face', 0, 32), ('face', 'face', 0, 32),
                 ('corner_left', 'left', 0, 32), ('corner_right', 'right', 0, 32),
                 ('left', 'foot_left', 0, 32), ('right', 'foot_right', 0, 32),
                 ('face', 'foot', 0, 32), ('inner_right', 'face', 0, 32),
                 ('inner_left', 'face', 0, 32),
                 # Only the rock-side span connects at a concave turn. The
                 # exterior span is turf, not continuation of transparent air.
                 ('left', 'inner_right', 5, 32), ('right', 'inner_left', 0, 27)]
        for first, second, x0, x1 in joins:
            for a in range(4):
                for b in range(4):
                    with self.subTest(first=first, second=second, a=a, b=b):
                        top, bottom = ground.cliff(first, a), ground.cliff(second, b)
                        self.assertEqual(top.crop((x0, 31, x1, 32)).tobytes(),
                                         bottom.crop((x0, 0, x1, 1)).tobytes())

    def test_complete_face_below_cap_and_grounded_foot(self):
        for name in ('top', 'face', 'inner_left', 'inner_right'):
            self.assertEqual(ground.cliff(name).getchannel('A').getextrema(), (255, 255))
        for variant in range(4):
            foot = ground.cliff('foot', variant)
            self.assertEqual(foot.getchannel('A').crop((0, 0, 32, 20)).getextrema(), (255, 255))
            self.assertLess(foot.getpixel((16, 31))[3], 255)
        for layout in preview.CLIFF_LAYOUTS.values():
            self.assertTrue(all(len(row) == len(layout[0]) for row in layout))
        with self.assertRaises(ValueError):
            ground.cliff('unknown')


class TerrainChecks(unittest.TestCase):
    kinds = ('grass', 'moss', 'marsh', 'dirt', 'sand', 'ash', 'snow')

    def test_terrain_does_not_use_ordered_dither(self):
        with patch.object(brush.Piece, 'dither', side_effect=AssertionError('ordered dither in ground')):
            for kind in self.kinds:
                for variant in range(4):
                    image = lands.tile(kind, variant)
                    self.assertEqual(image.size, (32, 32))
                    self.assertEqual(image.getchannel('A').getextrema(), (255, 255))

    def test_primary_vegetation_edges_join_for_every_variant_pair(self):
        for kind in ('grass', 'moss', 'marsh'):
            for a in range(4):
                for b in range(4):
                    first, second = lands.tile(kind, a), lands.tile(kind, b)
                    self.assertEqual(first.crop((31, 0, 32, 32)).tobytes(), second.crop((0, 0, 1, 32)).tobytes())
                    self.assertEqual(first.crop((0, 31, 32, 32)).tobytes(), second.crop((0, 0, 32, 1)).tobytes())

    def test_no_strong_four_pixel_phase_pattern(self):
        # A regression alarm for the old 4x4 checker, not an artistic score.
        for kind in self.kinds:
            buckets = [[] for _ in range(16)]
            for variant in range(4):
                image = lands.tile(kind, variant)
                for y in range(32):
                    for x in range(32):
                        buckets[(y % 4) * 4 + x % 4].append(sum(image.getpixel((x, y))[:3]) / 3)
            means = [sum(bucket) / len(bucket) for bucket in buckets]
            self.assertLess(max(means) - min(means), 3.0, kind)

    def test_partial_terrain_build_does_not_need_game_catalog(self):
        with patch.object(atelier_build, 'catalog', side_effect=AssertionError('unexpected catalogue read')):
            tasks = atelier_build.plan({'terrain'})
        self.assertEqual(len(tasks), 52)


class PanelChecks(unittest.TestCase):
    def test_nine_slice_contract_and_fixed_corners(self):
        self.assertEqual((face.SLICE, face.CORNER), (48, 16))
        for name in face.PANELS:
            source = face.panel(name)
            self.assertEqual(source.size, (48, 48))
            self.assertEqual(source.mode, 'RGBA')
            center = source.crop((16, 16, 32, 32))
            self.assertEqual(len({center.getpixel((x, y)) for y in range(16) for x in range(16)}), 1, 'stretchable center cannot contain grain bars')
            for width, height in ((48, 48), (132, 96), (202, 104), (320, 180)):
                stretched = preview.nine_slice(source, width, height)
                for sx, sy, tx, ty in ((0, 0, 0, 0), (32, 0, width-16, 0),
                                      (0, 32, 0, height-16), (32, 32, width-16, height-16)):
                    self.assertEqual(source.crop((sx, sy, sx+16, sy+16)).tobytes(),
                                     stretched.crop((tx, ty, tx+16, ty+16)).tobytes())

    def test_tooltip_and_inset_are_readable_not_near_black(self):
        for name in ('tooltip', 'inset'):
            source = face.panel(name)
            center = source.getpixel((24, 24))
            self.assertGreater(min(center[:3]), 60)
            # Top/bottom bevels keep contrasting lighting, including sunken inset.
            self.assertNotEqual(source.getpixel((24, 2)), source.getpixel((24, 45)))
            self.assertNotEqual(source.getpixel((24, 2)), center)
        self.assertEqual(pigment.rgb(face.PARCHMENT), (201, 184, 138, 255))

    def test_repeat_rendering_is_identical(self):
        makers = [lambda: face.panel('tooltip'), lambda: ground.cliff('inner_left', 3),
                  lambda: lands.tile('grass', 3)]
        for maker in makers:
            self.assertEqual(hashlib.sha256(maker().tobytes()).digest(),
                             hashlib.sha256(maker().tobytes()).digest())


if __name__ == '__main__':
    unittest.main()
