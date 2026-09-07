#!/usr/bin/env python3
"""Record exact source and compiled files for a game acceptance run."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def git(*args: str) -> str:
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()

def main() -> None:
    names = ['client/Scripts/Ui.cs', 'client/Scripts/ActionButton.cs',
             'client/Scripts/GameRoot.cs', 'client/Tests/ClientAcceptance.cs',
             'client/Tests/SignalContract.cs', 'src/Kairnfall.Core/RealmTransactions.cs',
             'src/Kairnfall.Core/RealmEngine.cs', 'src/Kairnfall.Core/RealmSocial.cs']
    entries = []
    for name in names:
        path = ROOT / name
        raw = path.read_bytes()
        entries.append({'path': name, 'sha256': hashlib.sha256(raw).hexdigest(),
                        'git_blob': git('rev-parse', 'HEAD:' + name)})
    binaries = []
    for base in [ROOT/'client/.godot/mono/temp/bin/Debug', ROOT/'src/Kairnfall.Server/bin/Release/net10.0']:
        for path in sorted(base.glob('Kairnfall*.dll')):
            binaries.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    value = {'commit': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
             'tracked_changes': git('diff', '--name-only'), 'source': entries, 'binaries': binaries}
    if value['tracked_changes']:
        raise RuntimeError('Acceptance must not run against uncommitted source changes.')
    output = ROOT/'artifacts/provenance.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(value, indent=2))

if __name__ == '__main__': main()
