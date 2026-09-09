import copy
import importlib.util
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('hunting_routes_content',ROOT/'tools/build_content.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
from content_src import hunting_routes

class HuntingRoutesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=builder.build();cls.zones={z['id']:z for z in cls.data['zones']};cls.mobs={m['id']:m for m in cls.data['mobs']}
    def test_two_new_hunting_dungeons_have_real_bosses_and_population(self):
        for ident,level,layer,boss in [('wayfarer_burrows',5,'Deepways','millbreaker'),('silkroot_den',15,'Umbral Depths','mother_of_silk')]:
            z=self.zones[ident];self.assertEqual(z['level'],level);self.assertEqual(z['layer'],layer)
            self.assertEqual(z['kind'],'dungeon');self.assertEqual(z['boss'],boss);self.assertTrue(self.mobs[boss]['boss'])
            self.assertGreaterEqual(len(z['species']),2);self.assertTrue(z['exits'])
    def test_all_new_links_are_reciprocal_and_preserve_matching_arrivals(self):
        for origin,target in [('wayfarers_rest','wayfarer_burrows'),('thistle_woods','silkroot_den'),('silkroot_den','dawnreach_deepway')]:
            a=next(e for e in self.zones[origin]['exits'] if e['target']==target)
            b=next(e for e in self.zones[target]['exits'] if e['target']==origin)
            self.assertEqual(a['position'],b['arrival']);self.assertEqual(a['arrival'],b['position'])
            self.assertEqual(a['kind'],'stairs');self.assertEqual(b['requirement'],1)
    def test_ordinary_dungeon_creatures_fit_the_advertised_level_band(self):
        for z in self.data['zones']:
            if z['kind']!='dungeon':continue
            self.assertGreaterEqual(len(z['species']),2)
            for species in z['species']:
                self.assertLessEqual(self.mobs[species]['level'],z['level']+8,(z['id'],species))
                self.assertFalse(self.mobs[species]['boss'])
        self.assertNotIn('stone_guardian',self.zones['broken_mill']['species'])
    def test_extension_is_deterministic_and_cannot_be_applied_twice(self):
        self.assertEqual(self.data,builder.build())
        with self.assertRaises(ValueError):hunting_routes.build(copy.deepcopy(self.data))

if __name__=='__main__':unittest.main()
