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
