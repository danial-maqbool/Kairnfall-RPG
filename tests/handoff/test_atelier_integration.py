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
        before_output={}
        for key in keys:
            actor=key.split('/')[0] in module.ACTOR_GROUPS
            size=(512,1536) if actor else (32,32)
            image=Image.new('RGBA',size,(0,0,0,0));draw=ImageDraw.Draw(image)
            if actor:
                for row in range(24):
                    for col in range(8):draw.rectangle((col*64+25,row*64+15,col*64+35,row*64+55),fill=(146,129,90,255))
            else:draw.rectangle((4,4,27,27),fill=(146,129,90,255))
            p=module.safe_path(source,key);p.parent.mkdir(parents=True,exist_ok=True);image.save(p)
            q=module.safe_path(output,key);q.parent.mkdir(parents=True,exist_ok=True)
            image.putpixel((0,0),(1,2,3,255));image.save(q);before_output[key]=q.read_bytes()
            entries.append(dict(key=key,width=size[0],height=size[1],sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        meta=dict(schema=1,library='atelier',frame_order=list(module.STATES),directions=list(module.DIRECTIONS),
                  actor_size=64,boss_size=128,foot_baseline=55,frames_per_row=8,assets=entries)
        (source/'manifest.json').write_text(json.dumps(meta));(source/'CREDITS.txt').write_text('Original fixture art.')
        return source,output,keys,before_output

    def test_grounded_actor_runtime_is_never_replaced_by_historical_atelier_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys,before_output=self.fixture(Path(temp));before_source={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            report=module.integrate(source,output,keys)
            self.assertEqual(report['integrated'],2)
            self.assertEqual(report['actor_runtime_source'],'Grounded-2026 procedural construction')
            self.assertEqual(report['actor_historical_fallbacks'],0)
            self.assertFalse(report['historical_actor_bytes_active'])
            for key in keys:
                group=key.split('/')[0]
                if group in module.ACTOR_GROUPS:
                    self.assertEqual(module.safe_path(output,key).read_bytes(),before_output[key],key)
                    self.assertNotEqual(module.safe_path(source,key).read_bytes(),module.safe_path(output,key).read_bytes(),key)
                else:
                    self.assertEqual(module.safe_path(source,key).read_bytes(),module.safe_path(output,key).read_bytes(),key)
            self.assertEqual(before_source,{str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()})
            again=module.integrate(source,output,keys);self.assertEqual(report,again)

    def test_corrupt_nonactor_member_rejects_entire_copy_before_output_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys,_=self.fixture(Path(temp));before={str(p):p.read_bytes() for p in output.rglob('*.png')}
            module.safe_path(source,'items/copper_sword').write_bytes(b'broken')
            with self.assertRaisesRegex(ValueError,'checksum'):module.integrate(source,output,keys)
            self.assertEqual(before,{str(p):p.read_bytes() for p in output.rglob('*.png')})

    def test_invalid_grounded_actor_output_is_rejected_before_nonactor_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys,_=self.fixture(Path(temp));p=module.safe_path(output,'equipment/copper_sword');Image.new('RGBA',(512,1536),(0,0,0,0)).save(p)
            before={str(path):path.read_bytes() for path in output.rglob('*.png')}
            with self.assertRaisesRegex(ValueError,'Grounded-2026 actor output is empty'):module.integrate(source,output,keys)
            self.assertEqual(before,{str(path):path.read_bytes() for path in output.rglob('*.png')})

    def test_incompatible_environment_uses_existing_art_with_recorded_reason(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys,_=self.fixture(Path(temp));p=module.safe_path(output,'terrain/grass_0');Image.new('RGBA',(64,64),(20,30,40,255)).save(p);before=p.read_bytes()
            report=module.integrate(source,output,keys);self.assertEqual(report['integrated'],1)
            terrain=next(entry for entry in report['skipped'] if entry['key']=='terrain/grass_0')
            self.assertIn('Different dimensions',terrain['reason']);self.assertEqual(before,p.read_bytes())

    def test_unsafe_keys_duplicate_keys_and_source_output_overlap_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);source,output,keys,_=self.fixture(base)
            for key in ('../secret','/etc/passwd','items/../../secret','items\\wrong','items/name.png'):
                with self.assertRaises(ValueError):module.safe_path(source,key)
            with self.assertRaises(ValueError):module.plan(source,output,keys+keys[:1])
            with self.assertRaises(ValueError):module.integrate(source,source,keys)

    def test_animation_order_and_foot_baseline_cannot_silently_change(self):
        with tempfile.TemporaryDirectory() as temp:
            source,output,keys,_=self.fixture(Path(temp));path=source/'manifest.json';metadata=json.loads(path.read_text())
            metadata['directions'].reverse();path.write_text(json.dumps(metadata))
            with self.assertRaisesRegex(ValueError,'direction'):module.plan(source,output,keys)

    def test_checked_in_library_covers_nonactor_catalog_except_versioned_generated_opening_icons(self):
        source=ROOT/'atelier/Assets';metadata=json.loads((source/'manifest.json').read_text())
        data=json.loads((ROOT/'content/catalog.json').read_text())
        keys={entry['key'] for entry in metadata['assets']}
        expected_items={'items/'+item['id'] for item in data['items']}
        missing=expected_items-keys
        generated_opening={'items/'+item['id'] for item in data['items'] if 'opening_reward' in item.get('tags',[])}
        self.assertEqual(len(generated_opening),8)
        self.assertEqual(missing,generated_opening,sorted(missing^generated_opening))
        for key in expected_items-missing:self.assertTrue(module.safe_path(source,key).is_file(),key)
        self.assertEqual(metadata['foot_baseline'],55)
        self.assertEqual(module.ACTOR_GROUPS,frozenset({'people','equipment','npcs','mobs'}))

if __name__=='__main__':unittest.main()
