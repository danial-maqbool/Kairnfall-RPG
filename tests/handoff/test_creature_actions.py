"""Species action geometry checks; not visual or gameplay acceptance."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from art import fauna
from art.creature_actions import ActionPose, pose, STATES


class CreatureActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT / 'content/catalog.json').read_text(encoding='utf-8'))
        cls.creatures = [m for m in catalog['mobs']
                         if m['family'] in ('spider', 'quartz_spider', 'turtle', 'tortoise')
                         and not m['boss'] and not m['elite']]

    def test_attack_has_anticipation_strike_and_recovery(self):
        for family in ('spider', 'quartz_spider', 'turtle', 'tortoise'):
            with self.subTest(family=family):
                before = pose(family, 'attack', 2)
                strike = pose(family, 'attack', 3)
                self.assertLess(before.advance + before.neck, 0)
                self.assertGreater(strike.advance + strike.neck, 0)
                self.assertEqual(pose(family, 'attack', 0), ActionPose())
                self.assertEqual(pose(family, 'attack', 7), ActionPose())

    def test_hit_is_a_recoil_not_an_attack_or_death(self):
        for family in ('spider', 'quartz_spider', 'turtle', 'tortoise'):
            values = [pose(family, 'hit', n) for n in range(8)]
            self.assertTrue(any(v.advance + v.neck < 0 for v in values))
            self.assertTrue(all(v.advance + v.neck <= 0 for v in values))
            self.assertEqual(values[-1], ActionPose())
            self.assertNotEqual(values, [pose(family, 'attack', n) for n in range(8)])

    def test_idle_walk_cast_and_death_keep_the_existing_pose_contract(self):
        for family in ('spider', 'quartz_spider', 'turtle', 'tortoise', 'wolf'):
            for state in ('idle', 'walk', 'cast', 'death'):
                for n in range(8):
                    self.assertEqual(pose(family, state, n), ActionPose())

    def test_every_rendered_action_stays_within_the_native_canvas(self):
        self.assertTrue(self.creatures)
        for creature in self.creatures:
            for direction in range(4):
                for state in ('attack', 'hit'):
                    for frame in range(8):
                        with self.subTest(creature=creature['id'], direction=direction,
                                          state=state, frame=frame):
                            image = fauna.frame(creature, state, frame, direction)
                            self.assertEqual(image.size, (64, 64))
                            bounds = image.getchannel('A').getbbox()
                            self.assertIsNotNone(bounds)
                            self.assertGreater(bounds[0], 0)
                            self.assertGreater(bounds[1], 0)
                            self.assertLess(bounds[2], 64)
                            self.assertLess(bounds[3], 64)

    def test_action_changes_geometry_not_only_the_hit_flash(self):
        for creature in self.creatures:
            for direction in range(4):
                # Frame 3 is outside the shared hit-flash frame.
                idle = fauna.frame(creature, 'idle', 3, direction).getchannel('A')
                attack = fauna.frame(creature, 'attack', 3, direction).getchannel('A')
                hit = fauna.frame(creature, 'hit', 3, direction).getchannel('A')
                with self.subTest(creature=creature['id'], direction=direction):
                    self.assertNotEqual(idle.tobytes(), attack.tobytes())
                    self.assertNotEqual(idle.tobytes(), hit.tobytes())
                    self.assertNotEqual(attack.tobytes(), hit.tobytes())

    def test_rendering_does_not_mutate_creature_definitions(self):
        for creature in self.creatures:
            original = copy.deepcopy(creature)
            first = fauna.frame(creature, 'attack', 3, 2)
            second = fauna.frame(creature, 'attack', 3, 2)
            self.assertEqual(first.tobytes(), second.tobytes())
            self.assertEqual(creature, original)

    def test_invalid_frame_addresses_are_rejected(self):
        for frame in (-1, 8, 1.5):
            with self.assertRaises(ValueError):
                pose('spider', 'attack', frame)
        with self.assertRaises(ValueError):
            pose('turtle', 'unknown', 0)


if __name__ == '__main__':
    unittest.main()
