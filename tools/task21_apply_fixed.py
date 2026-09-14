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

root = Path(__file__).resolve().parents[1]

# Preserve the canonical dungeon-side arrival, not the surface-side return arrival.
# The latter is outside a 96x96 boss room and correctly fails Catalog.Validate().
dungeon_depth = root / 'content_src' / 'dungeon_depth.py'
text = dungeon_depth.read_text(encoding='utf-8')
old = "        original_dungeon_arrival = dict(dungeon_exit['arrival'])"
new = "        original_dungeon_arrival = dict(source_exit['arrival'])"
if text.count(old) != 1:
    raise RuntimeError('Task 21 dungeon arrival patch anchor drifted.')
text = text.replace(old, new, 1)

# Walk-through transitions are exact reciprocal pairs: the destination arrival
# of one direction must equal the return trigger position and vice versa.
coordinate_patches = [
    ("        source_exit['arrival'] = point(32.5, 58.5)", "        source_exit['arrival'] = point(32.5, 62.5)"),
    ("        dungeon_exit['arrival'] = point(32.5, 5.5)", "        dungeon_exit['arrival'] = point(32.5, 2.5)"),
    ("exit_row(threshold_id + '_to_' + gauntlet_id, gauntlet_id, point(32.5, 2.5), point(32.5, 58.5), 'door', 1)", "exit_row(threshold_id + '_to_' + gauntlet_id, gauntlet_id, point(32.5, 2.5), point(32.5, 62.5), 'door', 1)"),
    ("exit_row(gauntlet_id + '_to_' + threshold_id, threshold_id, point(32.5, 62.5), point(32.5, 5.5), 'door', 1)", "exit_row(gauntlet_id + '_to_' + threshold_id, threshold_id, point(32.5, 62.5), point(32.5, 2.5), 'door', 1)"),
]
for before, after in coordinate_patches:
    if text.count(before) != 1:
        raise RuntimeError('Task 21 reciprocal coordinate patch anchor drifted: ' + before)
    text = text.replace(before, after, 1)
dungeon_depth.write_text(text, encoding='utf-8')

# Bosses must reset even when they have already moved beyond the nearby-player
# scan. The generic loop used to return on nearby.Count==0 before reaching its
# leash branch, leaving an abandoned displaced boss stuck until someone walked
# within 28 units of that displaced position.
combat = root / 'src' / 'Kairnfall.Core' / 'RealmCombat.cs'
text = combat.read_text(encoding='utf-8')
old = '''            var nearby=live.Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=28).ToList();
            if(nearby.Count==0) continue;
'''
new = '''            var nearby=live.Where(x=>x.Zone==mob.Zone&&x.Position.Distance(mob.Position)<=28).ToList();
            if(def.Boss&&mob.Position.Distance(mob.Home)>25) { ResetBossEncounter(mob,def); continue; }
            if(nearby.Count==0) continue;
'''
if text.count(old) != 1:
    raise RuntimeError('Task 21 early boss leash patch anchor drifted.')
combat.write_text(text.replace(old, new, 1), encoding='utf-8')
