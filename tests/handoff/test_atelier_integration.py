import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import integrate_atelier as module

class AtelierIntegrationTests(unittest.TestCase):
    def fixture(self,base):
        source=base/'atelier';output=base/'output';source.mkdir();output.mkdir()
        keys=['people/body_0_0','equipment/copper_sword','npcs/guard','items/copper_sword','terrain/grass_0']
        entries=[]
        for key in keys:
            animated=key.split('/')[0] in module.RIG
            size=(512,1536) if animated else (32,32)
            image=Image.new('RGBA',size,(0,0,0,0));draw=ImageDraw.Draw(image)
            if animated:
                for row in range(24):
                    for col in range(8):draw.rectangle((col*64+25,row*64+15,col*64+35,row*64+55),fill=(146,129,90,255))
            else:draw.rectangle((4,4,27,27),fill=(146,129,90,255))
            p=module.safe_path(source,key);p.parent.mkdir(parents=True,exist_ok=True);image.save(p)
            q=module.safe_path(output,key);q.parent.mkdir(parents=True,exist_ok=True)
            image.putpixel((0,0),(1,2,3,255));image.save(q)
            entries.append(dict(key=key,width=size[0],height=size[1],sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        meta=dict(schema=1,library='atelier',frame_order=list(module.STATES),directions=list(module.DIRECTIONS),
                  actor_size=64,boss_size=128,foot_baseline=55,frames_per_row=8,assets=entries)
        (source/'manifest.json').write_text(json.dumps(meta));(source/'CREDITS.txt').write_text('Original fixture art.')
        return source,output,keys
    def test_coherent_rig_and_catalog_keys_are_copied_without_modifying_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys=self.fixture(Path(temp));before={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            report=module.integrate(source,output,keys)
            self.assertEqual(report['integrated'],5);self.assertFalse(report['catalog_ids_changed']);self.assertFalse(report['independent_gear_ladder_imported'])
            for key in keys:self.assertEqual(module.safe_path(source,key).read_bytes(),module.safe_path(output,key).read_bytes())
            self.assertEqual(before,{str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()})
            again=module.integrate(source,output,keys);self.assertEqual(report,again)
    def test_corrupt_member_rejects_entire_copy_before_output_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys=self.fixture(Path(temp));before={str(p):p.read_bytes() for p in output.rglob('*.png')}
            module.safe_path(source,'equipment/copper_sword').write_bytes(b'broken')
            with self.assertRaisesRegex(ValueError,'checksum'):module.integrate(source,output,keys)
            self.assertEqual(before,{str(p):p.read_bytes() for p in output.rglob('*.png')})
    def test_incomplete_rig_is_not_mixed_with_old_equipment(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys=self.fixture(Path(temp));module.safe_path(source,'people/body_0_0').unlink()
            with self.assertRaisesRegex(ValueError,'Incomplete'):module.integrate(source,output,keys)
    def test_incompatible_environment_uses_existing_art_with_recorded_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys=self.fixture(Path(temp));p=module.safe_path(output,'terrain/grass_0');Image.new('RGBA',(64,64),(20,30,40,255)).save(p);before=p.read_bytes()
            report=module.integrate(source,output,keys);self.assertEqual(report['integrated'],4)
            self.assertEqual(report['skipped'][0]['key'],'terrain/grass_0');self.assertEqual(before,p.read_bytes())
    def test_unsafe_keys_duplicate_keys_and_source_output_overlap_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source,output,keys=self.fixture(base)
            for key in ('../secret','/etc/passwd','items/../../secret','items\\wrong','items/name.png'):
                with self.assertRaises(ValueError):module.safe_path(source,key)
            with self.assertRaises(ValueError):module.plan(source,output,keys+keys[:1])
            with self.assertRaises(ValueError):module.integrate(source,source,keys)
    def test_animation_order_and_foot_baseline_cannot_silently_change(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys=self.fixture(Path(temp));path=source/'manifest.json';metadata=json.loads(path.read_text())
            metadata['directions'].reverse();path.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError,'direction'):module.plan(source,output,keys)
    def test_checked_in_library_covers_current_catalog_items_and_the_entire_humanoid_rig(self):
        source=ROOT/'atelier/Assets';metadata=json.loads((source/'manifest.json').read_text())
        data=json.loads((ROOT/'content/catalog.json').read_text())
        keys={entry['key'] for entry in metadata['assets']}
        expected={'items/'+item['id'] for item in data['items']}
        expected|={'equipment/'+item['id'] for item in data['items'] if item.get('slot')}
        expected|={f'people/body_{body}_{skin}' for body in range(2) for skin in range(6)}
        expected|={f'people/hair_{style}_{color}' for style in range(6) for color in range(8)}
        expected|={'npcs/'+npc['role'] for npc in data['npcs']}
        self.assertFalse(expected-keys,sorted(expected-keys))
        for key in expected:self.assertTrue(module.safe_path(source,key).is_file(),key)
        self.assertEqual(metadata['foot_baseline'],55)

if __name__=='__main__':unittest.main()
