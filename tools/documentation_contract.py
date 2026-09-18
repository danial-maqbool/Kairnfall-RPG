#!/usr/bin/env python3
"""Validate synchronized evidence against Git history and real Actions runs."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'danial-maqbool/Kairnfall-RPG'
# Retain the previous workstream's validator and regression API. The entry point
# routes the character replacement to its stricter pack/platform contract below.
WORKSTREAM = 'new-player-experience'
RELEASE_STATUS = 'NOT APPROVED — human acceptance remains.'
TASK22_BLOB = 'f6623a46db658f3f8c9ef3656a74722583380233'
REQUIRED_WORKFLOWS = frozenset({
    'Transaction security regression', 'Compile Windows client source',
    'Live progression breadth', 'Windows package acceptance',
    'Graphical multiplayer acceptance', 'Load acceptance', 'Build and verify',
    'Task 13 adversarial acceptance', 'Release operations acceptance',
    'Transaction integrity on Windows and Linux', 'New-player journey',
    'Grounded actor acceptance', 'Visual acceptance matrix',
    'Windows display and input acceptance',
})
CURRENT_DOCS = ('HANDOFF.md', 'docs/SESSION_STATUS.md',
                'docs/handoff/NEW_PLAYER_CURRENT.md', 'docs/handoff/NEW_PLAYER_VERIFICATION.md')
TEMPORARY_PATHS = (
    '.ci/client-edit-request.json', '.ci/experience-candidate.json', '.ci/source-overlay.json',
    '.github/workflows/experience-candidate.yml', '.github/workflows/experience-log-diagnostic.yml',
    '.github/workflows/prepare-client-edit.yml', '.github/workflows/source-overlay.yml',
    '.github/workflows/first-hour-baseline.yml', '.github/workflows/grounded-motion-repair.yml',
    '.github/workflows/grounded-spirit-repair.yml', '.github/workflows/opening-integration-repair.yml',
    '.github/workflows/opening-integration.yml', '.github/workflows/opening-native-diagnostic.yml',
    '.github/workflows/opening-native-log-diagnostic.yml',
)
EXPECTED_UI_MATRIX = ['1024x720', '1280x720', '1920x1080', '2560x1440']
ASSET_MANIFEST = 'docs/ASSET_MIGRATION_FIRST_HOUR_UI.md'
ALLOWED_AUTHORED_CONTENT = {'content_src/opening_journey.py'}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_metadata(e: dict) -> str:
    require(e.get('schema') == 1 and e.get('currentTask') == WORKSTREAM,
            'Current evidence has not been synchronized to the verified new-player implementation.')
    baseline = e.get('implementationBaseline', '')
    require(isinstance(baseline, str) and re.fullmatch(r'[0-9a-f]{40}', baseline) is not None,
            'Expected an exact implementation SHA.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    require(e.get('repositorySideNewPlayerExperienceImplemented') is True,
            'Repository-side completion must be explicit.')
    authorization = e.get('authorization', {})
    require(authorization.get('implementationAuthorized') is True and
            authorization.get('publicationAuthorized') is False and
            authorization.get('deploymentAuthorized') is False and
            authorization.get('productionInfrastructureChanged') is False,
            'Implementation authorization must not authorize publication, deployment or infrastructure changes.')
    require(e.get('releaseStatus') == RELEASE_STATUS and e.get('publicationReady') is False and
            e.get('releasePublished') is False and e.get('deployed') is False,
            'Release boundary drifted.')
    require(isinstance(e.get('humanOnlyGates'), list) and bool(e['humanOnlyGates']) and
            all(isinstance(item, str) and item for item in e['humanOnlyGates']),
            'Human-only release gates must remain explicit.')
    require(e.get('historicalTask22Evidence') == 'docs/handoff/TASK22_EVIDENCE.json',
            'Historical Task 22 evidence must be preserved.')
    require(e.get('temporaryToolingRemoved') is True and e.get('newOverworldRegions') == 0 and
            type(e.get('tutorialRewardsAdded')) is int and e.get('tutorialRewardsAdded') == 8 and
            e.get('serverAuthoritative') is True,
            'Cleanup, footprint, tutorial reward count or reward-authority boundary drifted.')
    require(e.get('actorRuntimeSource') == 'Grounded-2026 procedural construction' and
            e.get('actorHistoricalFallbacks') == 0,
            'Active actor source or zero-fallback migration boundary drifted.')
    require(e.get('uiResolutionMatrix') == EXPECTED_UI_MATRIX,
            'UI acceptance resolution matrix is incomplete or reordered.')
    require(e.get('assetMigrationManifest') == ASSET_MANIFEST,
            'Asset migration manifest is missing from current evidence.')
    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list) and len(rows) == len(REQUIRED_WORKFLOWS) and
            all(isinstance(row, dict) for row in rows), 'Incomplete implementation workflow set.')
    require({row.get('name') for row in rows} == REQUIRED_WORKFLOWS, 'Required workflows are missing or duplicated.')
    require(all(type(row.get('runId')) is int and row['runId'] > 0 and
                row.get('conclusion') == 'success' and row.get('headSha') == baseline for row in rows),
            'Every implementation workflow must be successful at the exact baseline.')
    require(len({row['runId'] for row in rows}) == len(rows), 'Workflow run IDs must be unique.')
    return baseline


def validate_remote_run(row: dict, actual: dict, baseline: str) -> None:
    require(actual.get('id') == row['runId'] and actual.get('name') == row['name'],
            'Actions run identity does not match recorded evidence: ' + row['name'])
    require(actual.get('head_sha') == baseline and actual.get('head_branch') == 'main',
            'Actions run is not the exact main implementation: ' + row['name'])
    require(actual.get('status') == 'completed' and actual.get('conclusion') == 'success',
            'Actions run has not completed successfully: ' + row['name'])
    require(actual.get('event') in ('push', 'workflow_dispatch') and
            actual.get('repository', {}).get('full_name') == REPOSITORY,
            'Actions evidence belongs to an unexpected repository or trigger.')


def git(*arguments: str) -> str:
    return subprocess.run(['git', *arguments], cwd=ROOT, check=True, text=True,
                          capture_output=True).stdout.strip()


def latest_implementation_commit() -> str:
    # Workflow, guard, tooling and test edits all invalidate the baseline. Only handoff
    # documentation is excluded, avoiding a self-referential documentation commit SHA.
    return git('log', '-1', '--format=%H', 'HEAD', '--', '.',
               ':(exclude)docs/**', ':(exclude)HANDOFF.md')


def main() -> int:
    evidence = json.loads((ROOT / 'docs/handoff/CURRENT_EVIDENCE.json').read_text(encoding='utf-8'))
    if evidence.get('currentTask') == 'combat-feel-pass':
        from combat_delivery_contract import validate
        return validate(evidence)
    if evidence.get('currentTask') == 'character-rebuild':
        from character_delivery_contract import validate
        return validate(evidence)
    baseline = validate_metadata(evidence)
    require(latest_implementation_commit() == baseline, 'Implementation evidence is stale.')
    git('merge-base', '--is-ancestor', baseline, 'HEAD')
    historical = (ROOT / evidence['historicalTask22Evidence']).read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(historical)).encode('ascii') + b'\0' + historical).hexdigest()
    require(digest == TASK22_BLOB, 'Historical Task 22 evidence was changed instead of archived verbatim.')
    for path in TEMPORARY_PATHS:
        require(not (ROOT / path).exists(), 'Temporary tooling remains: ' + path)
    require((ROOT / ASSET_MANIFEST).is_file(), 'Asset migration manifest is absent from the repository.')
    origin = evidence.get('startingMain', '')
    require(isinstance(origin, str) and re.fullmatch(r'[0-9a-f]{40}', origin) is not None,
            'An exact starting-main SHA is required for the footprint audit.')
    git('merge-base', '--is-ancestor', origin, baseline)
    authored = {path for path in git('diff', '--name-only', origin, baseline, '--', 'content_src').splitlines() if path}
    require(authored == ALLOWED_AUTHORED_CONTENT,
            'Authored content footprint differs from the single approved opening module: ' + ', '.join(sorted(authored)))
    for relative in CURRENT_DOCS:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS,
                       'New-player experience', evidence.get('statusDate', '')):
            require(bool(marker) and marker in text, relative + ' is missing a current-evidence marker.')
    verification = (ROOT / CURRENT_DOCS[-1]).read_text(encoding='utf-8')
    for row in evidence['implementationWorkflows']:
        require(str(row['runId']) in verification and row['name'] in verification,
                'Verification documentation omits an implementation run.')
    if os.environ.get('CI', '').lower() == 'true':
        token = os.environ.get('GITHUB_TOKEN', '')
        require(bool(token), 'CI requires its read-only Actions token to verify real run results.')
        for row in evidence['implementationWorkflows']:
            request = urllib.request.Request(
                f'https://api.github.com/repos/{REPOSITORY}/actions/runs/{row["runId"]}',
                headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                         'X-GitHub-Api-Version': '2022-11-28'})
            with urllib.request.urlopen(request, timeout=30) as response:
                validate_remote_run(row, json.load(response), baseline)
        mode = 'live-actions-verified'
    else:
        mode = 'offline-structure-only; run CI for remote verification'
    print(f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; implementation={baseline}; '
          f'workflows={len(REQUIRED_WORKFLOWS)}; {mode}')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f'DOCUMENTATION_CONTRACT_FAIL: {error}', file=__import__('sys').stderr)
        raise SystemExit(1)
