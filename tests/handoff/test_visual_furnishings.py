"""Furniture contracts. Image checks establish construction coverage, not visual approval."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'tools'))
from content_src import skills,items,abilities,mobs,world,quests,presentation
from art import room_art
from art.environment_pack import building as old_building

spec=importlib.util.spec_from_file_location('furnishing_content_builder',ROOT/'tools/build_content.py')
builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)


class FurnishingArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=builder.build()
        cls.zones={z['id']:z for z in cls.data['zones']}

    def test_assets_use_the_authoritative_floor_footprint_and_rise(self):
        for kind,(width,height,rise,solid,ground) in presentation.FURNITURE.items():
            with self.subTest(kind=kind):
                image=room_art.render(kind)
                self.assertEqual(image.size,(width*32,height*32+rise))
                self.assertEqual(image.mode,'RGBA')
                self.assertIsNotNone(image.getchannel('A').getbbox())
                self.assertFalse(solid and ground)
                self.assertGreater(len(set(image.getdata())),4)

    def test_all_interior_plans_are_furnished_and_ids_are_unique(self):
        for zone in self.data['zones']:
            if zone['kind']!='interior': continue
            furniture=zone['furnishings']
            self.assertGreaterEqual(len(furniture),10,zone['id'])
            self.assertEqual(len({f['id'] for f in furniture}),len(furniture))
            self.assertTrue(any(f['ground'] for f in furniture))
            for f in furniture:
                self.assertEqual((f['width'],f['height'],f['rise'],f['solid'],f['ground']),presentation.FURNITURE[f['kind']])

    def test_starter_rooms_have_role_specific_construction(self):
        expected=[{'bed','hearth','dining_table','bar_counter'},
                  {'forge','anvil','quench','weapon_rack','armor_stand'},
                  {'shelf_food','shelf_potions','shelf_goods','shop_counter'},
                  {'map_board','practice_dummy','practice_ring','weapon_rack'}]
        for index,required in enumerate(expected):
            zone=self.zones[f'starter_building_{index}_inside']
            self.assertTrue(required <= {f['kind'] for f in zone['furnishings']})

    def test_the_central_travel_cross_and_npc_positions_are_not_occupied(self):
        for zone in self.data['zones']:
            if zone['kind']!='interior': continue
            occupied={(x,y) for f in zone['furnishings'] if f['solid']
                      for y in range(f['y'],f['y']+f['height']) for x in range(f['x'],f['x']+f['width'])}
            cx,cy=int(zone['spawn']['x']),int(zone['spawn']['y'])
            self.assertFalse(any(abs(x-cx)<=2 or abs(y-cy)<=2 for x,y in occupied),zone['id'])
            for npc in self.data['npcs']:
                if npc['zone']!=zone['id']: continue
                self.assertNotIn((int(npc['position']['x']),int(npc['position']['y'])),occupied)

    def test_plan_does_not_change_catalog_identities_quests_or_exits(self):
        raw={key:[] for key in ['skills','classes','items','abilities','recipes','zones','mobs','resources','npcs','quests']}
        for module in (skills,items,abilities,mobs,world,quests): module.build(raw)
        before=copy.deepcopy(raw); presentation.build(raw)
        for key in ('skills','classes','items','abilities','recipes','mobs','resources','quests'):
            self.assertEqual(before[key],raw[key],key)
        for a,b in zip(before['zones'],raw['zones']):
            self.assertEqual(a['id'],b['id']); self.assertEqual(a['spawn'],b['spawn']); self.assertEqual(a['exits'],b['exits'])
        for a,b in zip(before['npcs'],raw['npcs']):
            expected=copy.deepcopy(a)
            if self.zones[a['zone']]['kind']=='interior': expected['position']=b['position']
            self.assertEqual(expected,b)

    def test_plans_and_art_are_deterministic_without_input_mutation(self):
        self.assertEqual(self.data,builder.build())
        z=self.zones['wayfarers_rest']; b=z['buildings'][0]; before=copy.deepcopy((z,b))
        first=room_art.building(z,b); second=room_art.building(z,b)
        self.assertEqual(first.tobytes(),second.tobytes())
        self.assertEqual((z,b),before)
        self.assertEqual(first.size,old_building(z,b).size)

    def test_invalid_and_overlapping_plans_are_rejected(self):
        zone=copy.deepcopy(self.zones['starter_building_0_inside'])
        with self.assertRaises(ValueError): presentation.place(zone,[('bed',0,0)])
        with self.assertRaises(ValueError): presentation.place(zone,[('bed',5,5),('bed',5,5)])
        with self.assertRaises(ValueError): room_art.render('../bad')

    def test_terrain_edges_keep_native_pixel_dimensions(self):
        for mask in range(1,16):
            image=room_art.edge(mask)
            self.assertEqual(image.size,(32,32))
            self.assertIsNotNone(image.getchannel('A').getbbox())
            self.assertEqual(image.getpixel((16,16))[3],0)


if __name__=='__main__': unittest.main()
