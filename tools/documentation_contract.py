#!/usr/bin/env python3
"""Validate current Task 22 evidence while retaining Task 21 provenance."""
from __future__ import annotations
import json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs'/'handoff'/'CURRENT_EVIDENCE.json'
TASK21_EVIDENCE=ROOT/'docs'/'handoff'/'TASK21_EVIDENCE.json'
CURRENT_DOCS=[ROOT/'HANDOFF.md',ROOT/'docs'/'SESSION_STATUS.md',ROOT/'docs'/'handoff'/'TASK22_CURRENT.md',ROOT/'docs'/'handoff'/'TASK22_VERIFICATION.md']
RELEASE_STATUS='NOT APPROVED — human acceptance remains.'
IMPLEMENTATION='d83aa0f9d09a081cd5ebe7f43fe2e2ed9c34baec'
TASK21='9e493a02a0b371d3d0d6cd08e283c7d95000d9ce'
EXPECTED={
'Transaction security regression':34885269493,
'Compile Windows client source':34885269419,
'Live progression breadth':34885269509,
'Windows package acceptance':34885269513,
'Graphical multiplayer acceptance':34885269398,
'Load acceptance':34885269448,
'Build and verify':34885269413,
'Task 13 adversarial acceptance':34885269459,
'Release operations acceptance':34885269453,
'Transaction integrity on Windows and Linux':34885269575}

def fail(m): raise RuntimeError(m)
def latest_implementation_commit():
    cmd=['git','log','-1','--format=%H','HEAD','--','.',':(exclude)docs/**',':(exclude)HANDOFF.md',':(exclude)tools/documentation_contract.py',':(exclude).ci/experience-candidate.json',':(exclude).github/workflows/**']
    v=subprocess.run(cmd,cwd=ROOT,check=True,text=True,capture_output=True).stdout.strip()
    if len(v)!=40: fail('Could not resolve latest implementation commit.')
    return v

def main():
    e=json.loads(EVIDENCE.read_text(encoding='utf-8'))
    if e.get('schema')!=1 or e.get('currentTask')!=22: fail('Current evidence must identify schema 1 / Task 22.')
    if e.get('implementationBaseline')!=IMPLEMENTATION or latest_implementation_commit()!=IMPLEMENTATION: fail('Task 22 implementation baseline is stale.')
    if e.get('repositorySideTask22Implemented') is not True: fail('Task 22 repository implementation state must be explicit.')
    a=e.get('task22Authorization',{})
    if a.get('authorized') is not True or a.get('publicationAuthorized') is not False or a.get('deploymentAuthorized') is not False: fail('Task 22 authorization boundary drifted.')
    if e.get('releaseStatus')!=RELEASE_STATUS or e.get('publicationReady') is not False or e.get('releasePublished') is not False: fail('Release boundary drifted.')
    if not isinstance(e.get('humanOnlyGates'),list) or not e['humanOnlyGates']: fail('Human-only release gates must remain explicit and non-empty.')
    rows=e.get('task22ImplementationWorkflows',[])
    if {r.get('name'):r.get('runId') for r in rows}!=EXPECTED: fail('Task 22 workflow set/run IDs drifted.')
    if any(r.get('conclusion')!='success' or r.get('headSha')!=IMPLEMENTATION for r in rows): fail('Task 22 workflows must be successful exact-head evidence.')
    expected_content={'factions':5,'contractsPerFactionPerDay':3,'contractsPerDay':15,'contractKinds':['elite','gather','craft','dungeon','boss','event'],'reputationCap':1000,'rankThresholds':[250,500,750,1000],'newOverworldRegions':0,'serverAuthoritative':True,'persistenceCovered':True,'replayProtectionCovered':True,'exactOnceRewards':True,'rankMilestoneRewards':True}
    if e.get('task22Content')!=expected_content: fail('Task 22 content evidence drifted.')
    s=e.get('task22DocumentationSync',{})
    if s.get('preSyncRunId')!=34885269511 or s.get('preSyncHeadSha')!=IMPLEMENTATION or s.get('preSyncConclusion')!='failure': fail('Task 22 pre-sync documentation failure drifted.')
    repair=e.get('task22ClientCompileRepair',{})
    if repair.get('originalFailureRunId')!=34884785169 or repair.get('repairedExactHeadRunId')!=34885269419 or repair.get('publicationAuthorizationChanged') is not False: fail('Task 22 client repair provenance drifted.')
    if e.get('historicalTask21Evidence')!='docs/handoff/TASK21_EVIDENCE.json': fail('Task 21 evidence pointer drifted.')
    h=json.loads(TASK21_EVIDENCE.read_text(encoding='utf-8'))
    if h.get('currentTask')!=21 or h.get('implementationBaseline')!=TASK21: fail('Historical Task 21 evidence drifted.')
    if not isinstance(h.get('humanOnlyGates'),list) or not h['humanOnlyGates']: fail('Historical Task 21 release gates must remain explicit.')
    for p in CURRENT_DOCS:
        text=p.read_text(encoding='utf-8')
        for marker in ('2026-09-15',IMPLEMENTATION,'CURRENT_EVIDENCE.json',RELEASE_STATUS,'Task 22'):
            if marker not in text: fail(f'{p.relative_to(ROOT)} missing {marker}')
    v=CURRENT_DOCS[-1].read_text(encoding='utf-8')
    for marker in (str(34885269513),str(34885269511),'TASK21_EVIDENCE.json',str(34885269419)):
        if marker not in v: fail('TASK22_VERIFICATION.md missing '+marker)
    print(f'DOCUMENTATION_CONTRACT: task=22; implementation={IMPLEMENTATION}; windows_run=34885269513; task21_history={TASK21}')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(f'DOCUMENTATION_CONTRACT_FAIL: {error}',file=__import__('sys').stderr); raise SystemExit(1)
