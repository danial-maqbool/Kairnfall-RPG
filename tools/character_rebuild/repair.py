#!/usr/bin/env python3
"""Temporary guarded repairs for the tested character candidate; removed on integration."""
from runtime_upgrade import ROOT,replace


def main():
    path=ROOT/'tools/art/character_motion.py'
    text=path.read_text()
    start=text.index("    elif state == 'run':")
    stop=text.index("    elif state == 'interact':",start)
    block=text[start:stop]
    if block.count("for side, sign in (('l',1),('r',-1)):")!=1:
        raise RuntimeError('Running-rig repair no longer matches the inspected source.')
    repaired=block.replace("for side, sign in (('l',1),('r',-1)):","for limb, limb_sign in (('l',1),('r',-1)):")
    for name in ('foot','elbow','hand'):
        repaired=repaired.replace("'"+name+"_'+side","'"+name+"_'+limb")
    repaired=repaired.replace('sign*stride','limb_sign*stride')
    path.write_text(text[:start]+repaired+text[stop:])
    replace('tools/run_character_native.py','    try:\n        run(\'import\'',"    succeeded=False\n    try:\n        run('import'")
    replace('tools/run_character_native.py','    finally:\n        images=', '        succeeded=True\n    finally:\n        images=')
    replace('tools/run_character_native.py',"'passed':len(results)==3 and all(r['passed'] for r in results)","'passed':succeeded and len(results)==3 and all(r['passed'] for r in results)")
    replace('.github/workflows/grounded-actor-acceptance.yml',"      - 'tools/run_character_native.py'","      - 'tools/run_character_native.py'\n      - 'tools/check_character_source.py'")
    replace('.github/workflows/grounded-actor-acceptance.yml','          dotnet build client/Kairnfall.Client.csproj', '          python tools/check_character_source.py 2>&1 | tee artifacts/character-acceptance/logs/source-preflight.log\n          dotnet build client/Kairnfall.Client.csproj')
    print('Fixed running direction shadowing; retained exact native success accounting and source preflight.',flush=True)

if __name__=='__main__':main()
