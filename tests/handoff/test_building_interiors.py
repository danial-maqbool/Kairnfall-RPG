"""Authored door/service contracts. These do not substitute for graphical playtesting."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('building_catalog_fixture', ROOT / 'tools/build_content.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class BuildingInteriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = builder.build()
        cls.zones = {zone['id']: zone for zone in cls.data['zones']}

    def test_starter_buildings_have_reciprocal_doors(self):
        starter = self.zones['wayfarers_rest']
        self.assertEqual(len(starter['buildings']), 4)
        for building in starter['buildings']:
            with self.subTest(building=building['id']):
                inside = self.zones[building['id'] + '_inside']
                self.assertEqual(inside['kind'], 'interior')
                entry = [exit for exit in starter['exits'] if exit['target'] == inside['id']]
                back = [exit for exit in inside['exits'] if exit['target'] == starter['id']]
                self.assertEqual(len(entry), 1)
                self.assertEqual(len(back), 1)
                self.assertEqual(entry[0]['kind'], 'door')
                self.assertEqual(entry[0]['position'], {'x': building['x'] + building['width']//2 + .5, 'y': building['y'] + building['height'] - .5})
                self.assertEqual(entry[0]['arrival'], back[0]['position'])
                self.assertEqual(back[0]['arrival'], entry[0]['position'])
                self.assertEqual(entry[0]['requirement'], 1)
                self.assertEqual(back[0]['requirement'], 1)

    def test_starter_services_exist_inside(self):
        for i, role in enumerate(('innkeeper', 'blacksmith', 'provisioner', 'trainer')):
            zone = 'starter_building_' + str(i) + '_inside'
            staff = [npc for npc in self.data['npcs'] if npc['zone'] == zone and npc['role'] == role]
            self.assertEqual(len(staff), 1, role)
            self.assertGreater(staff[0]['position']['y'], 3)
            self.assertLess(staff[0]['position']['y'], 25)
            if role in ('blacksmith', 'provisioner'):
                self.assertTrue(staff[0]['stock'])
            if role == 'blacksmith':
                self.assertEqual(staff[0]['station'], 'forge')

    def test_capital_interiors_are_not_empty_service_shells(self):
        capitals = [zone for zone in self.data['zones'] if zone['kind'] == 'city']
        self.assertEqual(len(capitals), 5)
        for capital in capitals:
            for building in capital['buildings']:
                inside = building['id'] + '_inside'
                self.assertIn(inside, self.zones)
                self.assertTrue(any(npc['zone'] == inside for npc in self.data['npcs']), inside)

    def test_original_starter_quest_givers_retain_identity_in_service_forecourts(self):
        expected = {'innkeeper': (30.5,34.5), 'blacksmith':(47.5,34.5), 'provisioner':(30.5,54.5), 'trainer':(49.5,55.5)}
        for role, point in expected.items():
            npc = next(npc for npc in self.data['npcs'] if npc['id'] == 'wayfarers_rest_' + role)
            self.assertEqual(npc['zone'], 'wayfarers_rest')
            self.assertEqual(npc['position'], {'x': point[0], 'y': point[1]})

    def test_starter_services_leave_the_square_and_door_thresholds_clear(self):
        staff = [npc for npc in self.data['npcs'] if npc['zone'] == 'wayfarers_rest']
        self.assertEqual(len(staff), 10)
        positions = [(npc['position']['x'],npc['position']['y']) for npc in staff]
        self.assertEqual(len(set(positions)),len(positions))
        self.assertGreater(len(set(x for x,y in positions)),5)
        for x,y in positions:
            self.assertGreater(abs(x-40.5),3, 'Keep the main north/south route clear')
            for other_x,other_y in positions:
                if (x,y) != (other_x,other_y):
                    self.assertGreaterEqual((x-other_x)**2+(y-other_y)**2,4)
            for building in self.zones['wayfarers_rest']['buildings']:
                door_x=building['x']+building['width']//2+.5
                door_y=building['y']+building['height']-.5
                self.assertGreater((x-door_x)**2+(y-door_y)**2,2)

    def test_all_quest_givers_still_resolve(self):
        identities = {npc['id'] for npc in self.data['npcs']}
        self.assertTrue(all(quest['giver'] in identities for quest in self.data['quests']))

    def test_existing_capital_and_world_connections_remain(self):
        starter = self.zones['wayfarers_rest']
        self.assertEqual(sum(exit['target'] == 'kingsmeadow' for exit in starter['exits']), 1)
        visited = set()
        pending = ['wayfarers_rest']
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            visited.add(current)
            pending.extend(exit['target'] for exit in self.zones[current]['exits'])
        self.assertEqual(visited, set(self.zones))

    def test_catalog_build_is_deterministic(self):
        self.assertEqual(self.data, builder.build())

if __name__ == '__main__':
    unittest.main()
