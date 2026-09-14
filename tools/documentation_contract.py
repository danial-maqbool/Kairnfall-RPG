#!/usr/bin/env python3
"""Validate current Task 21 evidence while retaining Task 20 provenance."""
from __future__ import annotations
import json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs'/'handoff'/'CURRENT_EVIDENCE.json'
TASK20_EVIDENCE=ROOT/'docs'/'handoff'/'TASK20_EVIDENCE.json'
CURRENT_DOCS=[ROOT/'HANDOFF.md',ROOT/'docs'/'SESSION_STATUS.md',ROOT/'docs'/'handoff'/'TASK21_CURRENT.md',ROOT/'docs'/'handoff'/'TASK21_VERIFICATION.md']
RELEASE_STATUS='NOT APPROVED — human acceptance remains.'
IMPLEMENTATION='9e493a02a0b371d3d0d6cd08e283c7d95000d9ce'
TASK20='5167d6323ac4264250fc4b64072450c0f6d69ead'
EXPECTED={
'Visual acceptance matrix':34880619970,'Load acceptance':34880620089,
'Windows display and input acceptance':34880619953,'Live progression breadth':34880619995,
'Review exact visual candidate':34880620028,'Graphical multiplayer acceptance':34880620094,
'Windows package acceptance':34880619996,'Build and verify':34880620064,
'Task 13 adversarial acceptance':34880620003,'Release operations acceptance':34880620037,
'Compile Windows client source':34880620067}

def fail(m): raise RuntimeError(m)
def latest_implementation_commit():
    cmd=['git','log','-1','--format=%H','HEAD','--','.',':(exclude)docs/**',':(exclude)HANDOFF.md',':(exclude)tools/documentation_contract.py',':(exclude).ci/experience-candidate.json',':(exclude).github/workflows/documentation-contract.yml']
    v=subprocess.run(cmd,cwd=ROOT,check=True,text=True,capture_output=True).stdout.strip()
    if len(v)!=40: fail('Could not resolve latest implementation commit.')
    return v

def main():
    e=json.loads(EVIDENCE.read_text(encoding='utf-8'))
    if e.get('schema')!=1 or e.get('currentTask')!=21: fail('Current evidence must identify schema 1 / Task 21.')
    if e.get('implementationBaseline')!=IMPLEMENTATION or latest_implementation_commit()!=IMPLEMENTATION: fail('Task 21 implementation baseline is stale.')
    if e.get('repositorySideTask21Implemented') is not True: fail('Task 21 repository implementation state must be explicit.')
    a=e.get('task21Authorization',{})
    if a.get('authorized') is not True or a.get('publicationAuthorized') is not False or a.get('deploymentAuthorized') is not False: fail('Task 21 authorization boundary drifted.')
    if e.get('releaseStatus')!=RELEASE_STATUS or e.get('publicationReady') is not False or e.get('releasePublished') is not False: fail('Release boundary drifted.')
    if not isinstance(e.get('humanOnlyGates'),list) or not e['humanOnlyGates']: fail('Human-only release gates must remain explicit and non-empty.')
    rows=e.get('task21ImplementationWorkflows',[])
    if {r.get('name'):r.get('runId') for r in rows}!=EXPECTED: fail('Task 21 workflow set/run IDs drifted.')
    if any(r.get('conclusion')!='success' or r.get('headSha')!=IMPLEMENTATION for r in rows): fail('Task 21 workflows must be successful exact-head evidence.')
    expected_content={'surfaceWildernessRegions':20,'surfaceWildernessTiles':2048000,'newOverworldRegions':0,'selectedBossDungeons':4,'compactDungeonRooms':8,'compactRoomSize':64,'bossLifecycleResetHardened':True,'exactOnceBossRewards':True}
    if e.get('task21Content')!=expected_content: fail('Task 21 content evidence drifted.')
    s=e.get('task21DocumentationSync',{})
    if s.get('preSyncRunId')!=34880619999 or s.get('preSyncHeadSha')!=IMPLEMENTATION or s.get('preSyncConclusion')!='failure': fail('Task 21 pre-sync documentation failure drifted.')
    repair=e.get('task21WindowsPackageRepair',{})
    if repair.get('originalFailureRunId')!=34875631596 or repair.get('repairedExactHeadRunId')!=34880619996 or repair.get('publicationAuthorizationChanged') is not False: fail('Task 21 package repair provenance drifted.')
    if e.get('historicalTask20Evidence')!='docs/handoff/TASK20_EVIDENCE.json': fail('Task 20 evidence pointer drifted.')
    h=json.loads(TASK20_EVIDENCE.read_text(encoding='utf-8'))
    if h.get('currentTask')!=20 or h.get('implementationBaseline')!=TASK20: fail('Historical Task 20 evidence drifted.')
    if not isinstance(h.get('humanOnlyGates'),list) or not h['humanOnlyGates']: fail('Historical Task 20 release gates must remain explicit.')
    for p in CURRENT_DOCS:
        text=p.read_text(encoding='utf-8')
        for marker in ('2026-09-14',IMPLEMENTATION,'CURRENT_EVIDENCE.json',RELEASE_STATUS,'Task 21'):
            if marker not in text: fail(f'{p.relative_to(ROOT)} missing {marker}')
    v=CURRENT_DOCS[-1].read_text(encoding='utf-8')
    for marker in (str(34880619996),str(34880619999),'TASK20_EVIDENCE.json'):
        if marker not in v: fail('TASK21_VERIFICATION.md missing '+marker)
    print(f'DOCUMENTATION_CONTRACT: task=21; implementation={IMPLEMENTATION}; windows_run=34880619996; task20_history={TASK20}')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(f'DOCUMENTATION_CONTRACT_FAIL: {error}',file=__import__('sys').stderr); raise SystemExit(1)
