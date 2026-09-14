#!/usr/bin/env python3
from pathlib import Path
import runpy
import textwrap

real_dedent = textwrap.dedent


def task21_dedent(text: str) -> str:
    if text.startswith("\\\nusing System;"):
        return text[2:]
    stripped = text.lstrip()
    csharp_prefixes = (
        'private void ClearBossEncounterArtifacts',
        'var zones=live.Select',
        'if(mob.Position.Distance(mob.Home)>25)',
    )
    if stripped.startswith(csharp_prefixes):
        return text
    return real_dedent(text)


textwrap.dedent = task21_dedent
runpy.run_path(str(Path(__file__).with_name('task21_apply.py')), run_name='__main__')

# Preserve the canonical dungeon-side arrival, not the surface-side return arrival.
# The latter is outside a 96x96 boss room and correctly fails Catalog.Validate().
dungeon_depth = Path(__file__).resolve().parents[1] / 'content_src' / 'dungeon_depth.py'
text = dungeon_depth.read_text(encoding='utf-8')
old = "        original_dungeon_arrival = dict(dungeon_exit['arrival'])"
new = "        original_dungeon_arrival = dict(source_exit['arrival'])"
if text.count(old) != 1:
    raise RuntimeError('Task 21 dungeon arrival patch anchor drifted.')
dungeon_depth.write_text(text.replace(old, new, 1), encoding='utf-8')
