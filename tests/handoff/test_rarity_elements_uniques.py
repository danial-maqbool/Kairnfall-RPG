import hashlib
import unittest

from tools import build_content
from atelier.forge import smith


class RarityElementUniqueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_content.build()
        cls.items = {item['id']: item for item in cls.data['items']}
        cls.mobs = {mob['id']: mob for mob in cls.data['mobs']}
        cls.uniques = [item for item in cls.data['items'] if 'boss_unique' in item.get('tags', [])]

    def test_five_boss_uniques_per_class_at_requested_milestones(self):
        self.assertEqual(40, len(self.uniques))
        for entry in self.data['classes']:
            owned = [item for item in self.uniques if 'class:' + entry['id'] in item['tags']]
            self.assertEqual([25,45,65,85,100], sorted(item['requirement'] for item in owned), entry['id'])

    def test_uniques_are_stronger_and_boss_only(self):
        recipe_outputs = {recipe['output'] for recipe in self.data['recipes']}
        nonboss_drops = {drop for mob in self.data['mobs'] if not mob.get('boss') for drop in mob['drops']}
        boss_drops = {drop for mob in self.data['mobs'] if mob.get('boss') for drop in mob['drops']}
        for item in self.uniques:
            base_tag = next(tag for tag in item['tags'] if tag.startswith('base:'))
            base = self.items[base_tag.split(':',1)[1]]
            self.assertGreater(item['power'], base['power'], item['id'])
            self.assertNotIn(item['id'], recipe_outputs)
            self.assertNotIn(item['id'], nonboss_drops)
            self.assertIn(item['id'], boss_drops)
            self.assertNotEqual('Physical', item['element'])
        assigned = [mob for mob in self.data['mobs'] if mob.get('boss') and any(drop in {u['id'] for u in self.uniques} for drop in mob['drops'])]
        self.assertEqual(5, len(assigned))
        self.assertTrue(all(sum(drop in {u['id'] for u in self.uniques} for drop in mob['drops']) == 8 for mob in assigned))

    def test_unique_icons_are_distinct_pixel_art_with_aura(self):
        hashes = []
        for item in self.uniques:
            image = smith.icon(item)
            self.assertEqual((32,32), image.size)
            self.assertEqual('RGBA', image.mode)
            self.assertGreater(image.getchannel('A').getbbox()[2], 0)
            hashes.append(hashlib.sha256(image.tobytes()).hexdigest())
        self.assertEqual(40, len(set(hashes)))


if __name__ == '__main__':
    unittest.main()
