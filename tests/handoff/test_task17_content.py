import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import build_content


class Task17WorldDensityContentTests(unittest.TestCase):
    def test_task17_generation_is_deterministic_without_overworld_growth(self):
        first = build_content.build()
        second = build_content.build()
        canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self.assertEqual(canonical(first), canonical(second))

        surface = [z for z in first["zones"] if z["kind"] == "wilderness" and z["layer"] == "Surface"]
        self.assertEqual(20, len(surface))
        self.assertEqual(2_048_000, sum(z["width"] * z["height"] for z in surface))

        local = [q for q in first["quests"] if q["id"].startswith("local_")]
        self.assertEqual(30, len(local))
        self.assertEqual(30, len({q["name"] for q in local}))
        self.assertTrue(all(q["category"] == "regional" and not q["repeatable"] for q in local))

    def test_every_minor_settlement_has_a_three_stage_chain_and_six_residents(self):
        data = build_content.build()
        settlements = [
            ("reedhaven", "mosswater", "alchemist"),
            ("millcross", "westfarms", "carpenter"),
            ("pinewatch", "pinewatch_reach", "woodworker"),
            ("brambleford", "thistle_woods", "tailor"),
            ("stonebridge", "silver_run", "fletcher"),
            ("copperstead", "ember_marches", "blacksmith"),
            ("whitepost", "northern_moor", "tanner"),
            ("saltmere", "saltwind", "fisher"),
            ("gullhaven", "gull_isles", "woodworker"),
            ("dustwell", "dry_reach", "scholar"),
        ]
        quests = {q["id"]: q for q in data["quests"]}
        npcs = data["npcs"]

        for settlement, parent, specialist in settlements:
            residents = [n for n in npcs if n["zone"] == settlement]
            self.assertGreaterEqual(len(residents), 6, settlement)
            ids = {n["id"] for n in residents}
            self.assertTrue({
                settlement + "_innkeeper",
                settlement + "_provisioner",
                settlement + "_traveler",
                settlement + "_guard",
                settlement + "_scribe",
                settlement + "_" + specialist,
            }.issubset(ids), settlement)

            first = quests["local_" + settlement + "_01"]
            second = quests["local_" + settlement + "_02"]
            third = quests["local_" + settlement + "_03"]
            self.assertEqual("", first["prerequisite"])
            self.assertEqual(first["id"], second["prerequisite"])
            self.assertEqual(second["id"], third["prerequisite"])
            self.assertTrue(any(o["action"] == "explore" and o["target"] == parent for o in first["objectives"]))
            self.assertEqual(2, sum(o["action"] == "survey" for o in first["objectives"]))
            self.assertFalse(any(o["action"] == "chest" for o in first["objectives"]))


if __name__ == "__main__":
    unittest.main()
