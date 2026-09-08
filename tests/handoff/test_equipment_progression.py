"""Equipment progression, acquisition, balance and artwork construction regressions.

These tests do not approve artwork, human playability, or a release package.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'tools'))
from content_src import skills,items,abilities,mobs,world,quests,presentation,gear_progression
from art import items as item_art, humanoid
from art.common import STATES
spec=importlib.util.spec_from_file_location('equipment_progression_builder',ROOT/'tools/build_content.py')
builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)


def original():
    data={key:[] for key in ('skills','classes','items','abilities','recipes','zones','mobs','resources','npcs','quests')}
    for module in (skills,items,abilities,mobs,world,quests,presentation): module.build(data)
    return data


class EquipmentProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=builder.build(); cls.base=original()
        cls.lookup={i['id']:i for i in cls.data['items']}
        cls.old={i['id']:i for i in cls.base['items']}
        cls.new=set(cls.lookup)-set(cls.old)
        cls.tiers=cls.data['equipmentTiers']
        cls.recipes={r['output']:r for r in cls.data['recipes']}

    def test_requested_skill_levels_have_every_existing_equipment_family(self):
        expected={5,10,15,20,27,35,45,50,55,60,65,70,75,80,85,90,95,100}
        self.assertTrue(expected <= {t['level'] for t in self.tiers})
        families={f'weapon/{f[0]}' for f in items.WEAPONS}
        families|={f'armor/{w}/{s[0]}' for w in ('light','medium','heavy') for s in items.SLOTS}
        families|={f'offhand/{f[0]}' for f in gear_progression.OFFHANDS}
        families|={f'accessory/{f[0]}' for f in gear_progression.ACCESSORIES}
        families|={f'tool/{f[0]}' for f in gear_progression.TOOLS}
        self.assertEqual(len(families),51)
        for tier in self.tiers:
            self.assertEqual(set(tier['entries']),families,tier['name'])
            for family,ident in tier['entries'].items():
                item=self.lookup[ident]
                self.assertEqual(item['requirement'],tier['level'],ident)
                self.assertEqual(item['stackMax'],1,ident)
                self.assertIn(ident,self.recipes)
                self.assertEqual(item['type'],family.split('/')[0])

    def test_original_saved_templates_recipes_and_starter_loadouts_are_unchanged(self):
        for ident,item in self.old.items(): self.assertEqual(item,self.lookup[ident],ident)
        recipes={r['id']:r for r in self.data['recipes']}
        for r in self.base['recipes']: self.assertEqual(r,recipes[r['id']],r['id'])
        for key in ('skills','classes','abilities','mobs','resources','quests','zones'):
            self.assertEqual(self.base[key],self.data[key],key)

    def test_npc_identity_position_and_old_stock_are_preserved(self):
        now={n['id']:n for n in self.data['npcs']}
        for npc in self.base['npcs']:
            value=copy.deepcopy(now[npc['id']])
            self.assertTrue(set(npc['stock']) <= set(value['stock']))
            value['stock']=npc['stock']; value['name']=npc['name'] # builder resolves duplicate display names
            self.assertEqual(npc,value,npc['id'])

    def test_all_new_items_are_obtainable_from_real_sources_and_recipes(self):
        reachable={r['item'] for r in self.data['resources']}
        reachable|={i for npc in self.data['npcs'] for i in npc['stock']}
        reachable|={i for mob in self.data['mobs'] for i in mob['drops']}
        reachable|={q['reward'] for q in self.data['quests'] if q['reward']}
        for _ in range(len(self.data['recipes'])):
            expanded={r['output'] for r in self.data['recipes'] if set(r['ingredients'])<=reachable}
            if expanded<=reachable: break
            reachable|=expanded
        self.assertFalse(self.new-reachable,sorted(self.new-reachable))

    def test_added_recipes_have_no_forward_skill_gate_or_recipe_cycle(self):
        new_recipes=[r for r in self.data['recipes'] if r['output'] in self.new]
        for recipe in new_recipes:
            self.assertLessEqual(recipe['requirement'],100)
            for ident,quantity in recipe['ingredients'].items():
                self.assertGreater(quantity,0)
                self.assertLessEqual(self.lookup[ident]['requirement'],recipe['requirement'],recipe['id']+'/'+ident)
        graph={r['output']:set(r['ingredients'])&self.new for r in new_recipes}
        active=set(); complete=set()
        def visit(key):
            self.assertNotIn(key,active,'Crafting cycle: '+key)
            if key in complete: return
            active.add(key)
            for child in graph.get(key,()): visit(child)
            active.remove(key); complete.add(key)
        for key in graph: visit(key)

    def test_each_weapon_retains_family_timing_range_and_two_hand_rules(self):
        for tier in self.tiers:
            for family,_,_,_,speed,reach,two_handed in items.WEAPONS:
                item=self.lookup[tier['entries']['weapon/'+family]]
                self.assertEqual(item['speed'],speed)
                self.assertEqual(item['range'],reach)
                self.assertEqual('two_handed' in item['tags'],two_handed)

    def test_same_family_base_power_and_defense_never_decrease(self):
        for family in self.tiers[0]['entries']:
            previous=-1
            for tier in self.tiers:
                item=self.lookup[tier['entries'][family]]
                score=item['power'] if family.startswith('weapon/') else item['armor'] if family.startswith('armor/') else sum(item['stats'].values())
                self.assertGreaterEqual(score,previous-.0001,family+'/'+tier['name'])
                previous=score

    def test_new_crafting_outputs_cannot_be_sold_for_more_than_minimum_input_purchase(self):
        for recipe in self.data['recipes']:
            if recipe['output'] not in self.new: continue
            sale=max(1,int(self.lookup[recipe['output']]['value']*.30))*recipe['quantity']
            minimum_purchase=sum(max(1,__import__('math').ceil(self.lookup[k]['value']*1.05))*v for k,v in recipe['ingredients'].items())
            self.assertLess(sale,minimum_purchase,recipe['id'])

    def test_tool_upgrades_have_bounded_mechanical_bonuses(self):
        for tier in self.tiers:
            for tag,_,skill,_ in gear_progression.TOOLS:
                item=self.lookup[tier['entries']['tool/'+tag]]
                self.assertEqual(item['slot'],'')
                self.assertEqual(item['skill'],skill)
                self.assertIn(tag,item['tags'])
                if tier['level']>1:
                    self.assertGreater(item['stats']['tool_efficiency'],0)
                    self.assertLessEqual(item['stats']['tool_efficiency'],15)
                    if tag!='hammer': self.assertGreater(item['stats']['tool_yield'],0); self.assertLessEqual(item['stats']['tool_yield'],20)

    def test_each_added_item_has_a_physical_icon_and_equipment_layer(self):
        checked=0
        for ident in sorted(self.new):
            item=self.lookup[ident]; before=copy.deepcopy(item)
            image=item_art.icon(item)
            self.assertEqual(image.size,(32,32),ident)
            self.assertIsNotNone(image.getchannel('A').getbbox(),ident)
            self.assertGreater(len(set(image.getdata())),4,ident)
            if item['slot']:
                for direction in range(4):
                    layer=humanoid.equipment_frame(item,'idle',0,direction)
                    self.assertEqual(layer.size,(64,64),ident)
                    self.assertIsNotNone(layer.getchannel('A').getbbox(),ident)
            self.assertEqual(item,before,ident); checked+=1
        report=dict(levels=[t['level'] for t in self.tiers],families=51,
                    tracked_entries=sum(len(t['entries']) for t in self.tiers),new_items=len(self.new),
                    original_items_retained=len(self.old),icons_checked=checked,
                    visual_approval='not_granted_by_structural_tests')
        target=ROOT/'artifacts/test-results/equipment-progression.json'
        target.parent.mkdir(parents=True,exist_ok=True); target.write_text(json.dumps(report,indent=2)+'\n')
        print('EQUIPMENT_PROGRESSION:',json.dumps(report,sort_keys=True))

    def test_representative_full_equipment_actions_keep_the_shared_anchor(self):
        for level in (5,27,55,75,100):
            tier=next(t for t in self.tiers if t['level']==level)
            for family in ('weapon/sword','weapon/bow','weapon/wand','offhand/shield','armor/heavy/helmet','armor/light/chest','armor/medium/boots'):
                item=self.lookup[tier['entries'][family]]
                for state in STATES:
                    for direction in range(4):
                        for number in range(8):
                            image=humanoid.equipment_frame(item,state,number,direction)
                            self.assertEqual(image.size,(64,64)); self.assertIsNotNone(image.getchannel('A').getbbox(),item['id'])

    def test_new_alloys_textiles_and_hides_have_actual_recipe_uses(self):
        consumed={ident for recipe in self.data['recipes'] for ident in recipe['ingredients']}
        for ident in self.new:
            if self.lookup[ident]['type'] in ('material','ore'):
                self.assertIn(ident,consumed,'Unusable material: '+ident)

    def test_deterministic_build_and_duplicate_extension_rejected(self):
        self.assertEqual(self.data,builder.build())
        with self.assertRaises(ValueError): gear_progression.build(copy.deepcopy(self.data))

if __name__=='__main__': unittest.main()
