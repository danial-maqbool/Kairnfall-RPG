import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "content" / "catalog.json"
COUNTS = ROOT / "content" / "counts.json"

CHAINS = {
    "heartwood_stand": ("old_boughs", "heartwood_burl", "season_heartwood", "heartwood_forester_axe"),
    "ghost_reed_patch": ("mosswater", "ghost_reed", "distill_ghost_reed", "ghost_reed_sickle"),
    "moonfin_pool": ("gull_isles", "moonfin", "press_moonfin_oil", "moonfin_rod"),
    "frostsilver_vein": ("glassmere", "frostsilver_ore", "smelt_frostsilver", "frostsilver_pickaxe"),
}


class Task19ProfessionDepth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.counts = json.loads(COUNTS.read_text(encoding="utf-8"))

    def test_world_footprint_and_sparse_regional_sources(self):
        surface = [z for z in self.data["zones"] if z["kind"] == "wilderness" and z["layer"] == "Surface"]
        self.assertEqual(20, len(surface))
        self.assertEqual(2_048_000, sum(z["width"] * z["height"] for z in surface))
        zones = {z["id"]: z for z in self.data["zones"]}
        resources = {r["id"]: r for r in self.data["resources"]}
        for resource_id, (zone_id, item_id, _, _) in CHAINS.items():
            self.assertIn(resource_id, resources)
            self.assertEqual(item_id, resources[resource_id]["item"])
            self.assertGreaterEqual(resources[resource_id]["respawn"], 300)
            self.assertEqual(1, zones[zone_id]["resources"].count(resource_id))
            self.assertEqual(1, sum(resource_id in z["resources"] for z in self.data["zones"]))

    def test_processing_and_specialty_routes_are_complete(self):
        items = {i["id"]: i for i in self.data["items"]}
        recipes = {r["id"]: r for r in self.data["recipes"]}
        for _, (_, gathered, process_recipe, tool_id) in CHAINS.items():
            process = recipes[process_recipe]
            self.assertIn(gathered, process["ingredients"])
            self.assertIn(process["output"], items)
            tool = items[tool_id]
            self.assertEqual("tool", tool["type"])
            self.assertIn("regional_specialty", tool["tags"])
            self.assertLessEqual(tool["stats"].get("tool_efficiency", 0), 15)
            self.assertLessEqual(tool["stats"].get("tool_yield", 0), 20)
            craft = next(r for r in self.data["recipes"] if r["output"] == tool_id)
            self.assertTrue(craft["ingredients"])
            self.assertGreaterEqual(craft["requirement"], process["requirement"])

    def test_generation_counts_expose_task19_content(self):
        self.assertEqual(4, self.counts["profession_rare_resources"])
        self.assertEqual(4, self.counts["profession_specialty_tools"])
        self.assertEqual(4, self.counts["profession_specialty_recipes"])


if __name__ == "__main__":
    unittest.main()
