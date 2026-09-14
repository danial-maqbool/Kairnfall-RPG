#!/usr/bin/env python3
"""Validate current Task 19 evidence while retaining Task 18 provenance."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs'/'handoff'/'CURRENT_EVIDENCE.json'
TASK18_EVIDENCE=ROOT/'docs'/'handoff'/'TASK18_EVIDENCE.json'
CURRENT_DOCS=[
    ROOT/'HANDOFF.md',
    ROOT/'docs'/'SESSION_STATUS.md',
    ROOT/'docs'/'handoff'/'TASK19_CURRENT.md',
    ROOT/'docs'/'handoff'/'TASK19_VERIFICATION.md',
]
RELEASE_STATUS='NOT APPROVED — human acceptance remains.'
TASK19_IMPLEMENTATION='dbec66155142caa96dd6612eea97a164a050bcd7'
TASK19_TRIGGER='838dde6faffb0bc779eca1d9f504258a5f85bcc6'
TASK19_RUN=34844649467
TASK19_ARTIFACT=10347388189
TASK19_DIGEST='sha256:6ec245e07c024b330ce01d98937b7219d463e7cc6a5e94f30e8e7de2a2b7d172'
TASK19_DETACHED='bc09a4fd7501751db16641f17cd79f37047b1431'
TASK19_DETACHED_RUN=34842460308
TASK18_IMPLEMENTATION='f0aa878fcde727f73538fda7e7c85a439dd41b49'
TASK18_CANDIDATE='d8ad0d28d0ca60aac161064cbd739e20ba00983d'
TASK18_RUN=34794421856
TASK18_ARTIFACT=10329611278
TASK18_DIGEST='sha256:4237c998e88e612ba12bcccb3e55c7cc15c18b2c41171e5fab2b5e0bb13e5c16'


def fail(message:str)->None:
    raise RuntimeError(message)


def latest_implementation_commit()->str:
    command=[
        'git','log','-1','--format=%H','HEAD','--','.',
        ':(exclude)docs/**',
        ':(exclude)HANDOFF.md',
        ':(exclude)tools/documentation_contract.py',
        ':(exclude).ci/experience-candidate.json',
        ':(exclude).github/workflows/documentation-contract.yml',
        ':(exclude).github/workflows/task19-evidence-sync.yml',
        ':(exclude).github/workflows/task19-refresh-foundry-atelier-atlas.yml',
        ':(exclude)foundry/Assets/atlas_atelier/**',
        ':(exclude)foundry/.task19-art-verify-trigger',
    ]
    value=subprocess.run(command,cwd=ROOT,check=True,text=True,capture_output=True).stdout.strip()
    if len(value)!=40:
        fail('Could not resolve latest implementation commit.')
    return value


def main()->int:
    evidence=json.loads(EVIDENCE.read_text(encoding='utf-8'))
    if evidence.get('schema')!=1 or evidence.get('currentTask')!=19:
        fail('Current evidence must identify schema 1 / Task 19.')
    baseline=evidence.get('implementationBaseline','')
    actual=latest_implementation_commit()
    if baseline!=TASK19_IMPLEMENTATION or baseline!=actual:
        fail(f'Current Task 19 baseline is stale: {baseline!r} != {actual!r}.')
    if evidence.get('repositorySideTask19Implemented') is not True:
        fail('Task 19 repository implementation state must be explicit.')

    auth=evidence.get('task19Authorization',{})
    if auth.get('authorized') is not True or auth.get('publicationAuthorized') is not False or auth.get('deploymentAuthorized') is not False:
        fail('Task 19 authorization boundary drifted.')
    approval=evidence.get('releaseApproval',{})
    if evidence.get('releaseStatus')!=RELEASE_STATUS or approval.get('status')!=RELEASE_STATUS:
        fail('Release-status wording drifted.')
    if evidence.get('publicationReady') is not False or evidence.get('releasePublished') is not False:
        fail('Publication boundary drifted.')
    if any(approval.get(key) is not False for key in ('art','humanUx','scale','performance')):
        fail('Human release gates must remain false.')

    candidate=evidence.get('task19CandidateVerification',{})
    if evidence.get('task19CandidateBaseline')!=TASK19_IMPLEMENTATION:
        fail('Task 19 current candidate baseline drifted.')
    expected={
        'workflowRunId':TASK19_RUN,
        'triggerHeadSha':TASK19_TRIGGER,
        'verifiedRevision':TASK19_IMPLEMENTATION,
        'conclusion':'success',
        'actionsArtifactId':TASK19_ARTIFACT,
        'actionsArtifactDigest':TASK19_DIGEST,
    }
    for key,value in expected.items():
        if candidate.get(key)!=value:
            fail('Task 19 integrated provenance drifted: '+key)

    detached=evidence.get('task19DetachedCandidateVerification',{})
    if detached.get('candidateSha')!=TASK19_DETACHED or detached.get('workflowRunId')!=TASK19_DETACHED_RUN or detached.get('conclusion')!='success':
        fail('Task 19 detached candidate provenance drifted.')

    expected_content={
        'surfaceWildernessRegions':20,
        'surfaceWildernessTiles':2048000,
        'newOverworldRegions':0,
        'regionalProfessionChains':4,
        'professionRareResources':4,
        'professionSpecialtyTools':4,
        'professionSpecialtyRecipes':4,
    }
    if evidence.get('task19Content')!=expected_content:
        fail('Task 19 profession/content evidence drifted.')
    if evidence.get('historicalTask18Evidence')!='docs/handoff/TASK18_EVIDENCE.json':
        fail('Task 18 historical evidence pointer drifted.')

    historical=json.loads(TASK18_EVIDENCE.read_text(encoding='utf-8'))
    if historical.get('currentTask')!=18 or historical.get('implementationBaseline')!=TASK18_IMPLEMENTATION:
        fail('Historical Task 18 current-evidence snapshot drifted.')
    old=historical.get('task18CandidateVerification',{})
    if historical.get('task18CandidateBaseline')!=TASK18_CANDIDATE:
        fail('Historical Task 18 candidate baseline drifted.')
    if old.get('workflowRunId')!=TASK18_RUN or old.get('actionsArtifactId')!=TASK18_ARTIFACT or old.get('actionsArtifactDigest')!=TASK18_DIGEST:
        fail('Historical Task 18 candidate provenance drifted.')
    if historical.get('releaseStatus')!=RELEASE_STATUS:
        fail('Historical Task 18 release boundary drifted.')

    for path in CURRENT_DOCS:
        text=path.read_text(encoding='utf-8')
        for marker in (evidence['statusDate'],TASK19_IMPLEMENTATION,'CURRENT_EVIDENCE.json',RELEASE_STATUS,'Task 19',str(TASK19_RUN)):
            if marker not in text:
                fail(f'{path.relative_to(ROOT)} is missing current marker: {marker}')
    verification=CURRENT_DOCS[-1].read_text(encoding='utf-8')
    for marker in (str(TASK19_ARTIFACT),TASK19_DIGEST,TASK19_DETACHED,str(TASK19_DETACHED_RUN),'TASK18_EVIDENCE.json'):
        if marker not in verification:
            fail('TASK19_VERIFICATION.md is missing provenance marker: '+marker)
    for path in (ROOT/'docs'/'handoff'/'TASK18_CURRENT.md',ROOT/'docs'/'handoff'/'TASK18_VERIFICATION.md'):
        if not path.is_file():
            fail('Historical Task 18 document missing: '+str(path.relative_to(ROOT)))

    print(f'DOCUMENTATION_CONTRACT: task=19; implementation={baseline}; exact_run={TASK19_RUN}; artifact={TASK19_ARTIFACT}; task18_history={TASK18_IMPLEMENTATION}')
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'DOCUMENTATION_CONTRACT_FAIL: {error}',file=__import__('sys').stderr)
        raise SystemExit(1)
