from __future__ import annotations

import hashlib
import unittest

from content_src import mobs
from tools.art.creatures import DIRECTIONS, STATES, creature_frame, frame_size


def mob_catalog() -> list[dict]:
    data = {"mobs": []}
    mobs.build(data)
    return data["mobs"]


def digest(image) -> str:
    return hashlib.sha256(image.tobytes()).hexdigest()


class CreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mobs = mob_catalog()

    def test_expected_mob_counts(self):
        normal = sum(1 for mob in self.mobs if not mob["boss"] and not mob["elite"])
        elite = sum(1 for mob in self.mobs if mob["elite"])
        bosses = sum(1 for mob in self.mobs if mob["boss"])
        self.assertEqual((normal, elite, bosses), (100, 25, 20))

    def test_frame_size_contract(self):
        for mob in self.mobs:
            expected = 128 if mob["boss"] else 64
            self.assertEqual(frame_size(mob), expected, mob["id"])

    def test_all_states_directions_and_frames_render(self):
        for mob in self.mobs:
            size = frame_size(mob)
            for state in STATES:
                for direction in DIRECTIONS.values():
                    for frame in range(8):
                        image = creature_frame(mob, state, frame, direction)
                        self.assertEqual(image.mode, "RGBA", (mob["id"], state, direction, frame))
                        self.assertEqual(image.size, (size, size), (mob["id"], state, direction, frame))
                        alpha = image.getchannel("A")
                        box = alpha.getbbox()
                        self.assertIsNotNone(box, (mob["id"], state, direction, frame))
                        self.assertGreater(box[2] - box[0], 0, (mob["id"], state, direction, frame))

    def test_deterministic_output(self):
        for mob in self.mobs:
            for state in ("idle", "walk", "attack", "cast", "death"):
                for direction in (0, 2, 3):
                    first = creature_frame(mob, state, 3, direction)
                    second = creature_frame(mob, state, 3, direction)
                    self.assertEqual(digest(first), digest(second), (mob["id"], state, direction))

    def test_pose_and_direction_differences(self):
        for mob in self.mobs:
            idle_south = creature_frame(mob, "idle", 0, 0)
            walk_south = creature_frame(mob, "walk", 2, 0)
            attack_south = creature_frame(mob, "attack", 4, 0)
            hit_south = creature_frame(mob, "hit", 2, 0)
            death_south = creature_frame(mob, "death", 7, 0)
            idle_north = creature_frame(mob, "idle", 0, 3)

            self.assertNotEqual(digest(idle_south), digest(walk_south), mob["id"])
            self.assertNotEqual(digest(idle_south), digest(attack_south), mob["id"])
            self.assertNotEqual(digest(idle_south), digest(hit_south), mob["id"])
            self.assertNotEqual(digest(idle_south), digest(death_south), mob["id"])
            self.assertNotEqual(digest(idle_south), digest(idle_north), mob["id"])


if __name__ == "__main__":
    unittest.main()
