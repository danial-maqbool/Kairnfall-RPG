#!/usr/bin/env python3
"""Validate current Task 20 evidence while retaining Task 19 provenance."""
from __future__ import annotations
import json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs'/'handoff'/'CURRENT_EVIDENCE.json'
TASK19_EVIDENCE=ROOT/'docs'/'handoff'/'TASK19_EVIDENCE.json'
CURRENT_DOCS=[ROOT/'HANDOFF.md',ROOT/'docs'/'SESSION_STATUS.md',ROOT/'docs'/'handoff'/'TASK20_CURRENT.md',ROOT/'docs'/'handoff'/'TASK20_VERIFICATION.md']
RELEASE_STATUS='NOT APPROVED — human acceptance remains.'
IMPLEMENTATION='5167d6323ac4264250fc4b64072450c0f6d69ead'
CANDIDATE='abc141dcaf82420c8289ebd47f8a7942aec6ee04'
TRIGGER='210ef038928d2400b34c4de42103bef085200931'
RUN=34860458864
ARTIFACT=10356070613
DIGEST='sha256:8e185ca82e9a264bc38001c001224015a489893fdbf63865ece5e99046f56a5c'
TASK19='dbec66155142caa96dd6612eea97a164a050bcd7'
EXPECTED={
'Build and verify':34862412834,'Load acceptance':34862412704,'Transaction security regression':34862413032,
'Transaction integrity on Windows and Linux':34862412868,'Compile Windows client source':34862412724,
'Task 13 adversarial acceptance':34862412800,'Live progression breadth':34862412792,
'Windows package acceptance':34862412854,'Graphical multiplayer acceptance':34862412720,
'Release operations acceptance':34862412821}

def fail(m): raise RuntimeError(m)
def latest_implementation_commit():
    cmd=['git','log','-1','--format=%H','HEAD','--','.',':(exclude)docs/**',':(exclude)HANDOFF.md',':(exclude)tools/documentation_contract.py',':(exclude).ci/experience-candidate.json',':(exclude).github/workflows/documentation-contract.yml']
    v=subprocess.run(cmd,cwd=ROOT,check=True,text=True,capture_output=True).stdout.strip()
    if len(v)!=40: fail('Could not resolve latest implementation commit.')
    return v

def main():
    e=json.loads(EVIDENCE.read_text(encoding='utf-8'))
    if e.get('schema')!=1 or e.get('currentTask')!=20: fail('Current evidence must identify schema 1 / Task 20.')
    if e.get('implementationBaseline')!=IMPLEMENTATION or latest_implementation_commit()!=IMPLEMENTATION: fail('Task 20 implementation baseline is stale.')
    if e.get('repositorySideTask20Implemented') is not True: fail('Task 20 repository implementation state must be explicit.')
    a=e.get('task20Authorization',{})
    if a.get('authorized') is not True or a.get('publicationAuthorized') is not False or a.get('deploymentAuthorized') is not False: fail('Task 20 authorization boundary drifted.')
    if e.get('releaseStatus')!=RELEASE_STATUS or e.get('publicationReady') is not False or e.get('releasePublished') is not False: fail('Release boundary drifted.')
    c=e.get('task20CandidateVerification',{})
    expected={'workflowRunId':RUN,'triggerHeadSha':TRIGGER,'verifiedRevision':CANDIDATE,'conclusion':'success','actionsArtifactId':ARTIFACT,'actionsArtifactDigest':DIGEST}
    if e.get('task20CandidateBaseline')!=CANDIDATE: fail('Task 20 candidate baseline drifted.')
    for k,v in expected.items():
        if c.get(k)!=v: fail('Task 20 candidate provenance drifted: '+k)
    rows=e.get('task20ImplementationWorkflows',[])
    if {r.get('name'):r.get('runId') for r in rows}!=EXPECTED: fail('Task 20 workflow set/run IDs drifted.')
    if any(r.get('conclusion')!='success' or r.get('headSha')!=IMPLEMENTATION for r in rows): fail('Task 20 workflows must be successful exact-head evidence.')
    if e.get('task20Content')!={'surfaceWildernessRegions':20,'surfaceWildernessTiles':2048000,'newOverworldRegions':0,'eventFamilies':8,'globalActiveEventCap':3,'rewardContributionFloor':4}: fail('Task 20 content evidence drifted.')
    s=e.get('task20DocumentationSync',{})
    if s.get('preSyncRunId')!=34862412700 or s.get('preSyncHeadSha')!=IMPLEMENTATION or s.get('preSyncConclusion')!='failure': fail('Task 20 pre-sync documentation failure drifted.')
    if e.get('historicalTask19Evidence')!='docs/handoff/TASK19_EVIDENCE.json': fail('Task 19 evidence pointer drifted.')
    h=json.loads(TASK19_EVIDENCE.read_text(encoding='utf-8'))
    if h.get('currentTask')!=19 or h.get('implementationBaseline')!=TASK19: fail('Historical Task 19 evidence drifted.')
    for p in CURRENT_DOCS:
        text=p.read_text(encoding='utf-8')
        for marker in ('2026-09-14',IMPLEMENTATION,'CURRENT_EVIDENCE.json',RELEASE_STATUS,'Task 20'):
            if marker not in text: fail(f'{p.relative_to(ROOT)} missing {marker}')
    v=CURRENT_DOCS[-1].read_text(encoding='utf-8')
    for marker in (CANDIDATE,str(RUN),str(ARTIFACT),DIGEST,'TASK19_EVIDENCE.json'):
        if marker not in v: fail('TASK20_VERIFICATION.md missing '+marker)
    print(f'DOCUMENTATION_CONTRACT: task=20; implementation={IMPLEMENTATION}; exact_run={RUN}; artifact={ARTIFACT}; task19_history={TASK19}')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except Exception as error:
        print(f'DOCUMENTATION_CONTRACT_FAIL: {error}',file=__import__('sys').stderr); raise SystemExit(1)
