"""Task 18 deterministic encounter-variety content regressions."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'tools'))
from content_src import encounter_variety
spec=importlib.util.spec_from_file_location('task18_builder',ROOT/'tools/build_content.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)


class Task18EncounterContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=builder.build()
        cls.mobs={m['id']:m for m in cls.data['mobs']}

    def test_task18_generation_is_deterministic_without_world_growth(self):
        self.assertEqual(self.data,builder.build())
        surface=[z for z in self.data['zones'] if z['kind']=='wilderness' and z['layer']=='Surface']
        self.assertEqual(len(surface),20)
        self.assertEqual(sum(z['width']*z['height'] for z in surface),2_048_000)
        self.assertEqual(sum(not m['boss'] and not m['elite'] for m in self.data['mobs']),100)
        self.assertEqual(sum(m['elite'] for m in self.data['mobs']),25)
        self.assertEqual(sum(m['boss'] for m in self.data['mobs']),20)
        self.assertTrue(all(sum(self.mobs[i]['elite'] for i in z['species'])==1 for z in surface))

    def test_champions_have_distinct_regions_and_real_mechanics(self):
        known={'strike','lunge','slam','brace','frenzy','ambush','projectile','circle','charge','cone','stomp','line','ring','interruptible','poison_field','summon','root','field','tempest'}
        self.assertEqual(len(encounter_variety.CHAMPIONS),6)
        biomes=[]
        for ident,(name,signature,_) in encounter_variety.CHAMPIONS.items():
            mob=self.mobs[ident]
            self.assertTrue(mob['elite'])
            self.assertFalse(mob['boss'])
            self.assertEqual(mob['name'],name)
            self.assertTrue(name.startswith('Champion '))
            self.assertIn(signature,known)
            self.assertIn(signature,mob['attacks'])
            self.assertIn('champion',mob['anatomy'])
            biomes.append(mob['biome'])
        self.assertEqual(len(set(biomes)),6)

if __name__=='__main__':unittest.main()
