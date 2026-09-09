from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

from PIL import Image

HERE = Path(__file__).resolve().parent
ATELIER = HERE.parent
ROOT = ATELIER.parent
sys.path.insert(0, str(ATELIER))

from forge import beasts, folk, rig, smith  # noqa: E402
from forge.brush import canvas, refine_sprite  # noqa: E402


class SpriteRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = ROOT / 'content' / 'catalog.json'
        if not catalog.is_file():
            raise unittest.SkipTest('content/catalog.json is required; run tools/build_content.py')
        cls.data = json.loads(catalog.read_text(encoding='utf-8'))

    def test_refinement_preserves_canvas_and_alpha_mask(self):
        source = canvas((24, 24))
        pixels = source.load()
        for y in range(4, 20):
            for x in range(5, 19):
                pixels[x, y] = (112, 94, 78, 255)
        before_alpha = source.getchannel('A').tobytes()
        refined = refine_sprite(source, 0.14)
        self.assertEqual(refined.size, source.size)
        self.assertEqual(refined.getchannel('A').tobytes(), before_alpha)
        self.assertNotEqual(refined.convert('RGB').tobytes(), source.convert('RGB').tobytes())

    def test_people_keep_fixed_rig_frame_and_are_deterministic(self):
        first = folk.body_frame(0, 2, 'idle', 0, 0)
        second = folk.body_frame(0, 2, 'idle', 0, 0)
        self.assertEqual(first.size, (64, 64))
        self.assertEqual(first.mode, 'RGBA')
        self.assertIsNotNone(first.getchannel('A').getbbox())
        self.assertEqual(first.tobytes(), second.tobytes())

    def test_humanoid_proportions_are_less_chibi_and_equipment_keeps_shared_rig(self):
        for build in rig.BUILDS:
            standing_height = rig.GROUND - (build.head_y - build.head)
            self.assertLess((build.head * 2) / standing_height, 0.24)
            self.assertGreater(build.femur + build.shin, 19)
        body = folk.body_frame(0, 2, 'idle', 0, 0)
        chest = next(i for i in self.data['items'] if i.get('slot') == 'chest')
        worn = folk.armour_frame(chest, 'idle', 0, 0)
        body_alpha = body.getchannel('A')
        worn_alpha = worn.getchannel('A')
        overlap = sum(1 for a, b in zip(body_alpha.getdata(), worn_alpha.getdata()) if a and b)
        self.assertGreater(overlap, 30)
        self.assertEqual(worn.size, body.size)

    def test_representative_creature_keeps_fixed_frame_and_detail(self):
        mob = next(m for m in self.data['mobs'] if not m.get('boss') and m.get('family') in {'bear', 'polar_bear', 'wolf'})
        first = beasts.frame(mob, 'idle', 0, 0)
        second = beasts.frame(mob, 'idle', 0, 0)
        self.assertEqual(first.size, (64, 64))
        self.assertEqual(first.mode, 'RGBA')
        self.assertIsNotNone(first.getchannel('A').getbbox())
        self.assertEqual(first.tobytes(), second.tobytes())
        pixels = first.load()
        opaque = [pixels[x, y][:3] for y in range(first.height) for x in range(first.width) if pixels[x, y][3] >= 220]
        self.assertGreater(len(set(opaque)), 8)

    def test_inventory_icon_keeps_32px_contract_and_is_deterministic(self):
        item = next(i for i in self.data['items'] if i.get('id') == 'copper_sword')
        first = smith.icon(item)
        second = smith.icon(item)
        self.assertEqual(first.size, (32, 32))
        self.assertEqual(first.mode, 'RGBA')
        self.assertEqual(first.getchannel('A').tobytes(), second.getchannel('A').tobytes())
        self.assertEqual(first.tobytes(), second.tobytes())
        pixels = first.load()
        self.assertGreater(len(set(pixels[x, y][:3] for y in range(first.height) for x in range(first.width) if pixels[x, y][3] >= 220)), 8)


if __name__ == '__main__':
    unittest.main()
