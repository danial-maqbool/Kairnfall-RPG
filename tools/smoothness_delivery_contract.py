#!/usr/bin/env python3
"""Verify the smoothness/performance workstream against exact-head evidence.

Checkpoint 0 reconciles delivery evidence only. It preserves the already-landed
smoothness source and proves that the evidence tooling itself is tested at a new
implementation revision before documentation is synchronized.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

from documentation_contract import (
    ROOT, REPOSITORY, RELEASE_STATUS, git, latest_implementation_commit,
    require, validate_remote_run,
)

WORKSTREAM = 'smoothness-performance-polish'
TITLE = 'Measured smoothness, performance, camera and gameplay polish'
CHECKPOINT = 0
STARTING_MAIN = '1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e'
PREVIOUS = 'docs/handoff/COMBAT_EVIDENCE_2026-09-18.json'
PREVIOUS_BLOB = 'cf1a93b5cd2481dcc1de86ec10c72469d3828fc0'
PRESERVED_COMBAT_BASELINE = '06776f6b0de7dbe02cab30a9e236e730c377de2e'
PRESERVED_COMBAT_DELIVERY = 'bc9561846cd480c1e899190cb9b6f2df75a30176'

REQUIRED_WORKFLOWS = frozenset({
    'Transaction security regression', 'Compile Windows client source',
    'Live progression breadth', 'Windows package acceptance',
    'Graphical multiplayer acceptance', 'Load acceptance', 'Build and verify',
    'Task 13 adversarial acceptance', 'Release operations acceptance',
    'Transaction integrity on Windows and Linux', 'New-player journey',
    'Character sprite acceptance', 'Visual acceptance matrix',
    'Windows display and input acceptance', 'Audio acceptance',
})
CURRENT_DOCS = (
    'HANDOFF.md',
    'docs/SESSION_STATUS.md',
    'docs/handoff/SMOOTHNESS_VERIFICATION.md',
)
CHECKPOINT0_ALLOWED_PATHS = frozenset({
    'tools/documentation_contract.py',
    'tools/smoothness_delivery_contract.py',
    'tests/handoff/test_smoothness_evidence.py',
    PREVIOUS,
})
PRESERVED_SMOOTHNESS_PATHS = frozenset({
    'client/Scripts/WorldView.CharacterMotion.cs',
    'client/Scripts/WorldView.cs',
    'client/Tests/CharacterPresentationContract.cs',
})


def validate_native_jobs(jobs: list[dict]) -> None:
    require(isinstance(jobs, list), 'Native job evidence must be a list.')
    required = {
        'verify (ubuntu-latest, linux)',
        'verify (windows-latest, windows)',
    }
    names = [job.get('name') for job in jobs]
    require(set(names) == required and len(names) == len(required),
            'Character native acceptance must contain exactly Linux and Windows jobs.')
    require(all(job.get('status') == 'completed' and job.get('conclusion') == 'success'
                for job in jobs),
            'Every character native platform job must complete successfully.')


def validate_metadata(e: dict) -> str:
    require(e.get('schema') == 1 and e.get('currentTask') == WORKSTREAM,
            'Current evidence does not describe the smoothness/performance workstream.')
    require(e.get('checkpoint') == CHECKPOINT,
            'Current smoothness evidence does not describe checkpoint 0.')
    baseline = e.get('implementationBaseline', '')
    require(isinstance(baseline, str) and re.fullmatch(r'[0-9a-f]{40}', baseline) is not None,
            'Expected an exact checkpoint implementation SHA.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    require(e.get('startingMain') == STARTING_MAIN,
            'Checkpoint 0 starting main changed.')
    require(e.get('preservedCombatBaseline') == PRESERVED_COMBAT_BASELINE and
            e.get('preservedCombatDelivery') == PRESERVED_COMBAT_DELIVERY,
            'Preserved combat revision references drifted.')
    require(e.get('historicalCombatEvidence') == PREVIOUS,
            'Historical combat evidence reference drifted.')
    for key in ('repositorySideCheckpoint0Complete', 'serverAuthoritative',
                'oldSavesCompatible', 'temporaryToolingRemoved'):
        require(e.get(key) is True, 'Required checkpoint boundary is missing: ' + key)
    for key in ('gameplaySourceChangedInCheckpoint0', 'combatBalanceChanged',
                'movementSpeedChanged', 'tickFrequencyChanged', 'publicationReady',
                'releasePublished', 'deployed', 'performanceTargetClaimed'):
        require(e.get(key) is False, 'Checkpoint 0 cannot claim or change: ' + key)
    authorization = e.get('authorization', {})
    require(authorization.get('implementationAuthorized') is True,
            'Implementation authorization is missing.')
    for key in ('publicationAuthorized', 'deploymentAuthorized',
                'productionInfrastructureChanged'):
        require(authorization.get(key) is False,
                'Unauthorized publication/deployment/infrastructure claim: ' + key)
    require(e.get('releaseStatus') == RELEASE_STATUS,
            'Release status drifted.')
    gates = e.get('humanOnlyGates')
    require(isinstance(gates, list) and gates and
            all(isinstance(item, str) and item.strip() for item in gates),
            'Human-only acceptance gates cannot be erased.')
    require(e.get('nativeAcceptancePlatforms') == ['linux', 'windows'],
            'Native character platform coverage must remain Linux and Windows.')

    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list) and len(rows) == len(REQUIRED_WORKFLOWS) and
            all(isinstance(row, dict) for row in rows),
            'Incomplete checkpoint workflow evidence.')
    require({row.get('name') for row in rows} == REQUIRED_WORKFLOWS,
            'Required checkpoint workflows are missing or duplicated.')
    require(all(type(row.get('runId')) is int and row['runId'] > 0 and
                row.get('headSha') == baseline and
                row.get('conclusion') == 'success' for row in rows),
            'Every checkpoint workflow must succeed on the exact implementation SHA.')
    require(len({row['runId'] for row in rows}) == len(rows),
            'Checkpoint workflow run IDs must be unique.')
    return baseline


def api(path: str, token: str):
    request = urllib.request.Request(
        f'https://api.github.com/repos/{REPOSITORY}/{path}',
        headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def validate(e: dict) -> int:
    baseline = validate_metadata(e)
    require(latest_implementation_commit() == baseline,
            'Smoothness checkpoint implementation evidence is stale.')
    git('merge-base', '--is-ancestor', STARTING_MAIN, baseline)
    git('merge-base', '--is-ancestor', baseline, 'HEAD')

    historical = (ROOT / PREVIOUS).read_bytes()
    actual_blob = hashlib.sha1(
        b'blob ' + str(len(historical)).encode('ascii') + b'\0' + historical
    ).hexdigest()
    require(actual_blob == PREVIOUS_BLOB,
            'Historical combat evidence changed instead of being archived byte-for-byte.')

    inherited = {
        path for path in git(
            'diff', '--name-only', PRESERVED_COMBAT_DELIVERY, STARTING_MAIN,
            '--', 'client'
        ).splitlines() if path
    }
    require(inherited == PRESERVED_SMOOTHNESS_PATHS,
            'Inherited smoothness footprint differs from the verified three-file delta: ' +
            ', '.join(sorted(inherited)))

    checkpoint_paths = {
        path for path in git('diff', '--name-only', STARTING_MAIN, baseline).splitlines()
        if path
    }
    require(checkpoint_paths == CHECKPOINT0_ALLOWED_PATHS,
            'Checkpoint 0 changed paths outside evidence reconciliation: ' +
            ', '.join(sorted(checkpoint_paths ^ CHECKPOINT0_ALLOWED_PATHS)))

    for protected in ('content_src', 'src/Kairnfall.Server', 'src/Kairnfall.Core'):
        changed = {
            path for path in git(
                'diff', '--name-only', STARTING_MAIN, baseline, '--', protected
            ).splitlines() if path
        }
        require(not changed,
                'Checkpoint 0 changed protected gameplay source: ' + ', '.join(sorted(changed)))

    for relative in CURRENT_DOCS:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS,
                       TITLE, e.get('statusDate', '')):
            require(bool(marker) and marker in text,
                    relative + ' omits a current smoothness-evidence marker.')

    verification = (ROOT / CURRENT_DOCS[-1]).read_text(encoding='utf-8')
    for row in rows_from(e):
        require(str(row['runId']) in verification and row['name'] in verification,
                'Smoothness verification document omits a workflow.')

    mode = 'offline-structure-only; run CI for live Actions verification'
    if os.environ.get('CI', '').lower() == 'true':
        token = os.environ.get('GITHUB_TOKEN', '')
        require(bool(token), 'CI requires a read-only Actions token.')
        native_jobs = None
        for row in rows_from(e):
            actual = api(f'actions/runs/{row["runId"]}', token)
            validate_remote_run(row, actual, baseline)
            if row['name'] == 'Character sprite acceptance':
                native_jobs = api(f'actions/runs/{row["runId"]}/jobs?per_page=100', token).get('jobs', [])
        require(native_jobs is not None,
                'Character sprite acceptance run is missing from live evidence.')
        validate_native_jobs(native_jobs)
        mode = 'live-actions-verified'

    print(
        f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; checkpoint={CHECKPOINT}; '
        f'implementation={baseline}; workflows={len(REQUIRED_WORKFLOWS)}; {mode}'
    )
    return 0


def rows_from(e: dict) -> list[dict]:
    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list), 'Implementation workflows must be a list.')
    return rows
