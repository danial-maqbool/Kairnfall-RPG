"""Technical tests. These do not constitute visual approval."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from art import common,environment,people,icons,audio
from art.items import icon
import build_assets

class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'content'/'catalog.json').read_text(encoding='utf-8'))
    def test_all_item_icons_have_physical_pixels(self):
        for item in self.data['items']:
            with self.subTest(item=item['id']):
                image=icon(item)
                self.assertEqual(image.size,(32,32));self.assertEqual(image.mode,'RGBA');self.assertIsNotNone(image.getchannel('A').getbbox())
                self.assertGreaterEqual(len({p for p in image.getdata() if p[3]>0}),4)
    def test_skill_and_ability_icons(self):
        for skill in self.data['skills']:
            self.assertIsNotNone(icons.skill_icon(skill,self.data['items']).getchannel('A').getbbox(),skill['id'])
        for ability in self.data['abilities']:
            self.assertIsNotNone(icons.ability_icon(ability).getchannel('A').getbbox(),ability['id'])
    def test_all_terrain_and_prop_forms(self):
        for kind in environment.GROUND:
            for variant in range(4):
                image=environment.terrain(kind,variant);self.assertEqual(image.size,(32,32));self.assertEqual(image.getchannel('A').getextrema(),(255,255))
        for prop in build_assets.PROPS:
            self.assertIsNotNone(environment.prop(prop).getchannel('A').getbbox(),prop)
    def test_building_native_dimensions(self):
        for zone in self.data['zones']:
            for building in zone.get('buildings',[]):
                definition=dict(building);definition.setdefault('width',5);definition.setdefault('height',4)
                image=environment.building(zone,definition)
                self.assertEqual(image.size,(definition['width']*32,(definition['height']+2)*32));self.assertIsNotNone(image.getchannel('A').getbbox())
    def test_humanoid_state_direction_frame_contract(self):
        for state in common.STATES:
            for direction in range(4):
                for frame in range(8):
                    image=people.body_frame(0,2,state,frame,direction)
                    self.assertEqual(image.size,(64,64));self.assertIsNotNone(image.getchannel('A').getbbox())
        south=people.body_frame(0,2,'idle',0,0).tobytes();north=people.body_frame(0,2,'idle',0,3).tobytes()
        self.assertNotEqual(south,north)
    def test_equipment_uses_same_frame_dimensions(self):
        selected=[]
        for slot in build_assets.VISIBLE_SLOTS:
            found=next((item for item in self.data['items'] if item.get('slot')==slot),None)
            if found:selected.append(found)
        for item in selected:
            for direction in range(4):
                for state in common.STATES:
                    image=people.equipment_frame(item,state,3,direction)
                    self.assertEqual(image.size,(64,64));self.assertIsNotNone(image.getchannel('A').getbbox(),(item['id'],state,direction))
    def test_deterministic_art(self):
        for kind in ('oak','rock','crate','waystone'):
            self.assertEqual(environment.prop(kind).tobytes(),environment.prop(kind).tobytes())
        for item in self.data['items'][::31]:self.assertEqual(icon(item).tobytes(),icon(item).tobytes())
    def test_job_paths_are_unique_and_safe(self):
        jobs=build_assets.jobs_for(self.data);paths=[job['key'] for job in jobs]
        self.assertEqual(len(paths),len(set(paths)))
        for path in paths:self.assertNotIn('..',path);self.assertFalse(path.startswith('/'))
        for invalid in ('../secret','a/b','a\\b','','a\x00b'):
            with self.assertRaises(ValueError):build_assets.safe_id(invalid)
    def test_wave_format_and_bounded_samples(self):
        signal=audio.effect('sword');self.assertTrue(np.isfinite(signal).all());self.assertLessEqual(float(np.max(np.abs(signal))),.95)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'sword.wav';audio.write_wav(path,signal)
            with wave.open(str(path),'rb') as stream:
                self.assertEqual(stream.getnchannels(),2);self.assertEqual(stream.getsampwidth(),2);self.assertEqual(stream.getframerate(),22050);self.assertGreater(stream.getnframes(),100)
        self.assertTrue(np.array_equal(audio.effect('coins'),audio.effect('coins')))
    def test_pack_install_preserves_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);stage=base/'stage';target=base/'target';stage.mkdir();target.mkdir()
            (target/'user-note.txt').write_text('preserve',encoding='utf-8');(stage/'new.txt').write_text('generated',encoding='utf-8')
            manifest={'assets':[{'path':'new.txt'}]};build_assets.install_pack(stage,target,manifest)
            self.assertEqual((target/'user-note.txt').read_text(),'preserve');self.assertEqual((target/'new.txt').read_text(),'generated');self.assertTrue((target/'manifest.json').is_file())

if __name__=='__main__':unittest.main()
