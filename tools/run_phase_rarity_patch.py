#!/usr/bin/env python3
from pathlib import Path
import runpy

patch = Path('tools/phase_rarity_elements_patch.py')
text = patch.read_text(encoding='utf-8')
old = '''def replace(path: str, old: str, new: str) -> None:\n    file = Path(path)\n    text = file.read_text(encoding='utf-8')\n    count = text.count(old)\n    if count != 1:\n        raise SystemExit(f'{path}: expected one replacement, found {count}')\n    file.write_text(text.replace(old, new, 1), encoding='utf-8')\n'''
new = '''def replace(path: str, old: str, new: str) -> None:\n    file = Path(path)\n    text = file.read_text(encoding='utf-8')\n    count = text.count(old)\n    if count != 1:\n        # The inventory refresh edit follows earlier edits in this same patch.\n        # Match only its stable assignment line so unrelated surrounding UI text stays guarded.\n        if path == 'client/Scripts/GameRoot.Inventory.cs' and old.startswith('                slot.Item = item; slot.Selected = item.Id == selectedItem;'):\n            needle = '                slot.Item = item; slot.Selected = item.Id == selectedItem; slot.Equipped = Items.Equipped(self, item.Id);\\n'\n            replacement = needle + '                slot.Element = Items.ElementOf(item,Data.Item(item.Template));\\n'\n            if text.count(needle) != 1:\n                raise SystemExit(f'{path}: inventory refresh assignment guard failed')\n            file.write_text(text.replace(needle, replacement, 1), encoding='utf-8')\n            return\n        raise SystemExit(f'{path}: expected one replacement, found {count}')\n    file.write_text(text.replace(old, new, 1), encoding='utf-8')\n'''
if text.count(old) != 1:
    raise SystemExit('phase patch replace-function guard failed')
patch.write_text(text.replace(old, new, 1), encoding='utf-8')
runpy.run_path(str(patch), run_name='__main__')
runpy.run_path('tools/phase_rarity_elements_patch_followup.py', run_name='__main__')
print('rarity/element/boss-unique patch sequence complete')
