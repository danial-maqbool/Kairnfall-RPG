from __future__ import annotations

from pathlib import Path
import hashlib
import sys
import unittest

HERE = Path(__file__).resolve().parent
ATELIER = HERE.parent
sys.path.insert(0, str(ATELIER))

from forge import blender_body, folk, rig  # noqa: E402


class RefinedBodyBatchTests(unittest.TestCase):
    def test_folk_uses_authored_renderer(self):
        self.assertIs(folk.body_frame, blender_body.body_frame)

    def test_all_base_frames_are_valid_and_deterministic(self):
        for build in range(2):
            for skin in range(6):
                first = folk.body_frame(build, skin, 'idle', 0, 0)
                second = folk.body_frame(build, skin, 'idle', 0, 0)
                self.assertEqual(first.mode, 'RGBA')
                self.assertEqual(first.size, (64, 64))
                self.assertIsNotNone(first.getchannel('A').getbbox())
                self.assertEqual(first.tobytes(), second.tobytes())

    def test_complete_sheet_contract_and_animation_variation(self):
        sheet = rig.sheet(lambda state, frame, direction: folk.body_frame(0, 2, state, frame, direction))
        self.assertEqual(sheet.mode, 'RGBA')
        self.assertEqual(sheet.size, (512, 1536))
        hashes = set()
        for row in range(24):
            for column in range(8):
                frame = sheet.crop((column * 64, row * 64, (column + 1) * 64, (row + 1) * 64))
                self.assertIsNotNone(frame.getchannel('A').getbbox())
                hashes.add(hashlib.sha256(frame.tobytes()).digest())
        self.assertGreater(len(hashes), 80)

    def test_front_side_and_back_silhouettes_are_distinct(self):
        images = [folk.body_frame(0, 2, 'idle', 0, direction) for direction in (0, 2, 3)]
        hashes = {hashlib.sha256(image.tobytes()).hexdigest() for image in images}
        self.assertEqual(len(hashes), 3)

    def test_authored_batch_is_complete_when_present(self):
        root = ATELIER / 'authored' / 'humanoid'
        if not root.exists():
            self.skipTest('Blender-authored sheets have not been generated yet')
        files = sorted(root.glob('body_*.png'))
        self.assertEqual(len(files), 12)


if __name__ == '__main__':
    unittest.main()
