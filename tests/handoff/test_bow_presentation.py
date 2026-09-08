"""Bow geometry regressions. These checks do not grant visual approval."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from art import bow_pose, humanoid
from art.common import STATES


class BowPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
        cls.bows = [item for item in data['items'] if item.get('slot') == 'weapon' and 'bow' in item.get('tags', [])]

    def test_every_side_frame_keeps_the_grip_on_the_hand(self):
        self.assertTrue(self.bows)
        for state in STATES:
            for direction in (1, 2):
                for frame in range(8):
                    j = humanoid.rig(state, frame, direction)
                    geometry = bow_pose.geometry(j)
                    self.assertEqual(geometry['grip'], j['hand_r'])
                    self.assertIn(j['hand_r'], geometry['curve'])
                    for item in self.bows:
                        image = humanoid.equipment_frame(item, state, frame, direction)
                        x, y = j['hand_r']
                        self.assertIsNotNone(image.getchannel('A').crop((x-1,y-1,x+2,y+2)).getbbox())

    def test_draw_release_and_reload_have_explicit_states(self):
        for direction in (1, 2):
            for frame in range(8):
                j = humanoid.rig('attack', frame, direction)
                geometry = bow_pose.geometry(j)
                self.assertEqual(geometry['drawing'], frame in (1, 2))
                if frame in (1, 2):
                    self.assertEqual(geometry['nock'], j['hand_l'])
                    self.assertNotEqual(geometry['nock'], geometry['grip'])
                if frame in (4, 5):
                    self.assertIsNone(geometry['arrow'])
                else:
                    start, end = geometry['arrow']
                    self.assertGreater((end[0]-start[0])*geometry['direction'], 0)

    def test_side_bow_never_clips_the_fixed_canvas(self):
        for state in STATES:
            for direction in (1, 2):
                for frame in range(8):
                    image = humanoid.equipment_frame(self.bows[0], state, frame, direction)
                    self.assertEqual(image.size, (64,64))
                    box = image.getchannel('A').getbbox()
                    self.assertIsNotNone(box)
                    self.assertGreater(box[0], 0)
                    self.assertGreater(box[1], 0)
                    self.assertLess(box[2], 64)
                    self.assertLess(box[3], 64)

    def test_west_and_east_keep_mirrored_grips_and_shoot_outwards(self):
        for state in ('idle','walk','attack','cast','death'):
            for frame in range(8):
                east = bow_pose.geometry(humanoid.rig(state, frame, 2))
                west = bow_pose.geometry(humanoid.rig(state, frame, 1))
                self.assertEqual(west['grip'], (64-east['grip'][0], east['grip'][1]))
                for a,b in zip(east['curve'], west['curve']):
                    self.assertEqual(b, (64-a[0],a[1]))

    def test_presentation_does_not_mutate_rig_or_item(self):
        j = humanoid.rig('attack',2,2)
        before = copy.deepcopy(j)
        bow_pose.geometry(j)
        self.assertEqual(j,before)
        for item in self.bows:
            before_item = copy.deepcopy(item)
            humanoid.equipment_frame(item,'attack',2,2)
            self.assertEqual(item,before_item)


if __name__ == '__main__':
    unittest.main()
