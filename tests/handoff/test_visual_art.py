"""Structural/anchor regressions. Passing these tests is not visual approval."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from art import humanoid, fauna
from art.common import STATES


class VisualArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'content/catalog.json').read_text(encoding='utf-8'))
        cls.equipment=[item for item in cls.data['items'] if item.get('slot')]

    def test_actor_canvas_and_ground_anchor(self):
        for body in range(2):
            for state in STATES:
                for direction in range(4):
                    for n in range(8):
                        with self.subTest(body=body,state=state,direction=direction,frame=n):
                            j=humanoid.rig(state,n,direction,body)
                            self.assertEqual(max(j['foot_l'][1],j['foot_r'][1]),55)
                            image=humanoid.body_frame(body,2,state,n,direction)
                            self.assertEqual(image.size,(64,64))
                            self.assertIsNotNone(image.getchannel('A').getbbox())
                            self.assertLessEqual(image.getchannel('A').getbbox()[3],57)

    def test_body_variants_share_equipment_anchors(self):
        for state in STATES:
            for direction in range(4):
                for n in range(8):
                    a=humanoid.rig(state,n,direction,0); b=humanoid.rig(state,n,direction,1)
                    for key in ('head','neck','hip','hand_l','hand_r','foot_l','foot_r'):
                        self.assertEqual(a[key],b[key])

    def test_head_and_pelvis_stay_stable_during_walk(self):
        for direction in range(4):
            first=humanoid.rig('walk',0,direction)
            for n in range(8):
                value=humanoid.rig('walk',n,direction)
                self.assertEqual(value['head'],first['head'])
                self.assertEqual(value['hip'],first['hip'])

    def test_west_and_east_share_mirrored_joint_contract(self):
        for n in range(8):
            east=humanoid.rig('walk',n,2); west=humanoid.rig('walk',n,1)
            for key in ('head','hip','hand_l','hand_r','foot_l','foot_r'):
                self.assertEqual(west[key],(64-east[key][0],east[key][1]))

    def test_death_is_joint_collapse_not_rotated_standing_pose(self):
        for direction in range(4):
            start=humanoid.rig('death',0,direction); end=humanoid.rig('death',7,direction)
            self.assertGreater(end['head'][1],start['head'][1]+20)
            self.assertEqual(end['foot_l'][1],55)
            self.assertEqual(end['foot_r'][1],55)
        for module in (humanoid,fauna):
            self.assertNotIn('.rotate(',Path(module.__file__).read_text())

    def test_weapon_grips_intersect_the_real_hand(self):
        for item in self.equipment:
            if item['slot']!='weapon': continue
            for direction in range(4):
                for state,n in [('idle',0),('walk',3),('attack',4),('cast',3),('death',7)]:
                    j=humanoid.rig(state,n,direction); x,y=j['hand_r']
                    image=humanoid.equipment_frame(item,state,n,direction)
                    with self.subTest(item=item['id'],state=state,direction=direction):
                        self.assertIsNotNone(image.getchannel('A').crop((x-3,y-3,x+4,y+4)).getbbox())
                        self.assertEqual(image.size,(64,64))

    def test_all_equipment_slots_have_visible_layers(self):
        for item in self.equipment:
            for direction in range(4):
                with self.subTest(item=item['id'],direction=direction):
                    self.assertIsNotNone(humanoid.equipment_frame(item,'idle',0,direction).getchannel('A').getbbox())

    def test_directional_occlusion_contract(self):
        for direction in range(4):
            order=humanoid.layer_order(direction,{})
            self.assertEqual(len(order),len(set(order)))
            self.assertIn('ring',order)
            self.assertLess(order.index('body'),order.index('helmet'))
        north=humanoid.layer_order(3,{})
        self.assertGreater(north.index('cloak'),north.index('chest'))
        self.assertLess(north.index('weapon'),north.index('body'))
        west=humanoid.layer_order(1,{})
        self.assertLess(west.index('weapon'),west.index('body'))
        self.assertGreater(west.index('offhand'),west.index('body'))

    def test_supported_species_have_every_required_frame(self):
        for mob in self.data['mobs']:
            if mob['family'] not in fauna.SUPPORTED or mob['boss']: continue
            for state in STATES:
                for direction in range(4):
                    for n in range(8):
                        with self.subTest(species=mob['id'],state=state,direction=direction,frame=n):
                            image=fauna.frame(mob,state,n,direction)
                            self.assertEqual(image.size,(64,64))
                            self.assertEqual(image.mode,'RGBA')
                            self.assertIsNotNone(image.getchannel('A').getbbox())

    def test_turtle_and_polar_bear_have_distinct_direction_views(self):
        for ident in ('sea_turtle','polar_bear','field_rat','wild_hare'):
            mob=next(x for x in self.data['mobs'] if x['id']==ident)
            views=[fauna.frame(mob,'idle',0,d).tobytes() for d in range(4)]
            self.assertEqual(len(set(views)),4,ident)

    def test_drawers_do_not_change_catalog_or_equipment(self):
        item=copy.deepcopy(next(x for x in self.equipment if x['slot']=='weapon'))
        before=copy.deepcopy(item); humanoid.equipment_frame(item,'attack',4,2)
        self.assertEqual(item,before)
        mob=copy.deepcopy(next(x for x in self.data['mobs'] if x['id']=='sea_turtle'))
        before=copy.deepcopy(mob); fauna.frame(mob,'walk',3,2)
        self.assertEqual(mob,before)

    def test_every_npc_role_uses_nonempty_art(self):
        for role in sorted({npc['role'] for npc in self.data['npcs']}):
            for direction in range(4):
                image=humanoid.npc_frame(role,'idle',0,direction)
                self.assertIsNotNone(image.getchannel('A').getbbox(),role)


if __name__=='__main__': unittest.main()
