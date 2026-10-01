#!/usr/bin/env python3
"""Exact-source delivery evidence for the authorized broad game experience pass.

This is a separate workstream. It never widens a historical checkpoint's
footprint or turns automated acceptance into human or whole-game approval.
Offline validation checks structure/history; only CI checks real Actions proof.
"""
from __future__ import annotations

from datetime import date
import hashlib
import json
import os
from pathlib import PurePosixPath
import re
import urllib.request

from documentation_contract import (
    ROOT, REPOSITORY, RELEASE_STATUS, TEMPORARY_PATHS, git,
    latest_implementation_commit, require,
)

WORKSTREAM = 'game-experience-improvement'
STARTING_MAIN = '55b504254620d1a0d9197512265907103b271d22'
CHECKPOINT3_ARCHIVE = 'docs/handoff/SMOOTHNESS_CHECKPOINT3_EVIDENCE_2026-09-21.json'
# Git blob identities pin exact original bytes, including formatting/newlines.
HISTORICAL_BLOBS = {
    'docs/handoff/TASK20_EVIDENCE.json': 'd106a1ecee3d5204faf4d47f99f7f3a323882d63',
    'docs/handoff/TASK21_EVIDENCE.json': '249c0e3310f31b8fea43c4e9664cc0629a3a0b28',
    'docs/handoff/TASK22_EVIDENCE.json': 'f6623a46db658f3f8c9ef3656a74722583380233',
    'docs/handoff/COMBAT_EVIDENCE_2026-09-18.json': 'cf1a93b5cd2481dcc1de86ec10c72469d3828fc0',
    'docs/handoff/SMOOTHNESS_CHECKPOINT0_EVIDENCE_2026-09-20.json': '79779ce75560c5dd98132827181e8f56f35e1f70',
    'docs/handoff/SMOOTHNESS_CHECKPOINT1_EVIDENCE_2026-09-20.json': '10654d5d0d4605c7f9708faccb8b7cfd13257efb',
    'docs/handoff/SMOOTHNESS_CHECKPOINT2_EVIDENCE_2026-09-20.json': '43df0bc5281a8f969268d38f32c57c943c70c412',
    CHECKPOINT3_ARCHIVE: '2ee3b9a519379b3e7c534372b6f9f962c5a8605a',
}
WORKFLOWS = {
    'Transaction security regression': ('.github/workflows/security.yml', ()),
    'Compile Windows client source': ('.github/workflows/client.yml', ('client-source-',)),
    'Live progression breadth': ('.github/workflows/live-progression-breadth.yml', ('live-progression-',)),
    'Windows package acceptance': ('.github/workflows/windows-package.yml', ('windows-package-',)),
    'Graphical multiplayer acceptance': ('.github/workflows/graphical-multiplayer.yml', ('graphical-multiplayer-',)),
    'Load acceptance': ('.github/workflows/load-acceptance.yml', ('load-acceptance-',)),
    'Build and verify': ('.github/workflows/ci.yml', ('source-and-test-evidence-', 'windows-core-evidence-')),
    'Task 13 adversarial acceptance': ('.github/workflows/independent-qa.yml', ('task13-adversarial-evidence-',)),
    'Release operations acceptance': ('.github/workflows/release-operations.yml', ('release-operations-',)),
    'Transaction integrity on Windows and Linux': ('.github/workflows/transaction-security.yml',
        ('transaction-integrity-ubuntu-latest-', 'transaction-integrity-windows-latest-')),
    'New-player journey': ('.github/workflows/new-player-journey.yml', ('new-player-journey-',)),
    'Character sprite acceptance': ('.github/workflows/grounded-actor-acceptance.yml',
        ('character-sprites-ubuntu-latest-', 'character-sprites-windows-latest-')),
    'Visual acceptance matrix': ('.github/workflows/visual-acceptance-matrix.yml', ('visual-acceptance-',)),
    'Windows display and input acceptance': ('.github/workflows/windows-display-input.yml', ('windows-display-input-',)),
    'Audio acceptance': ('.github/workflows/audio-acceptance.yml', ('audio-acceptance-',)),
    'Client performance and motion diagnostics': ('.github/workflows/performance-diagnostics.yml',
        ('performance-diagnostics-ubuntu-latest-', 'performance-diagnostics-windows-latest-')),
}
NATIVE_JOBS = {
    'Character sprite acceptance': {'verify (ubuntu-latest, linux)', 'verify (windows-latest, windows)'},
    'Client performance and motion diagnostics': {
        'diagnostics (ubuntu-latest, linux)', 'diagnostics (windows-latest, windows)'},
}
ALLOWED_SCOPES = ('client/', 'src/', 'tests/', 'tools/', 'content_src/', 'content/', 'art/', 'atelier/', 'docs/')
ALLOWED_ROOT_FILES = frozenset({
    'HANDOFF.md', 'README.md', 'AGENTS.md', '.gitignore', '.env.example',
    'Directory.Build.props', 'Directory.Packages.props', 'global.json',
    'Kairnfall.slnx', 'NuGet.Config', 'NuGet.config', 'docker-compose.yml',
    'Bootstrap-Kairnfall.ps1', 'Run-Kairnfall-Dev.ps1', 'Run-Kairnfall.ps1', 'Test-Kairnfall.ps1',
})
ALLOWED_WORKFLOW_PATHS = frozenset(path for path, _ in WORKFLOWS.values()) | {
    '.github/workflows/documentation-contract.yml', '.github/workflows/local-handoff.yml',
}
CURRENT_DOCS = ('HANDOFF.md', 'docs/SESSION_STATUS.md', 'docs/handoff/IMPROVEMENT_VERIFICATION.md')


def exact_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None


def positive_id(value: object) -> bool:
    return type(value) is int and value > 0


def validate_path(path: object) -> None:
    require(isinstance(path, str) and bool(path) and '\\' not in path and ':' not in path
            and not path.startswith('/') and PurePosixPath(path).as_posix() == path
            and not any(ord(char) < 32 or ord(char) == 127 for char in path)
            and all(part not in ('', '.', '..') for part in path.split('/')),
            'Changed path is not a normalized repository-relative path: ' + str(path))
    parts = {part.lower() for part in path.split('/')}
    require(not parts.intersection({'.git', '.godot', '.tools', '.venv', 'bin', 'obj',
            '__pycache__', 'artifacts', 'deliverables', 'saves', 'backups', 'credentials'})
            and not any(part.startswith('.env') and part != '.env.example' for part in parts),
            'Generated, private or local state cannot enter the implementation inventory: ' + path)
    require(path.startswith(ALLOWED_SCOPES) or path in ALLOWED_ROOT_FILES
            or path in ALLOWED_WORKFLOW_PATHS,
            'Changed path exceeds the authorized repository scopes: ' + path)


def validate_jobs(row: dict, jobs: object, baseline: str) -> None:
    require(isinstance(jobs, list) and bool(jobs) and all(isinstance(job, dict) for job in jobs),
            'Every workflow requires its complete job inventory.')
    names, ids = [], []
    for job in jobs:
        require(positive_id(job.get('id')) and isinstance(job.get('name'), str) and bool(job['name']),
                'Job identity is malformed.')
        require(job.get('runId') == row['runId'] and job.get('runAttempt') == row['runAttempt']
                and job.get('headSha') == baseline,
                'Job evidence was replayed from a different run, attempt or source.')
        require(job.get('status') == 'completed' and job.get('conclusion') == 'success',
                'Skipped, pending or failed jobs cannot approve a workflow.')
        names.append(job['name'])
        ids.append(job['id'])
    require(len(set(ids)) == len(ids) and len(set(names)) == len(names), 'Job inventory contains duplicates.')
    if row['name'] in NATIVE_JOBS:
        require(set(names) == NATIVE_JOBS[row['name']], 'Native Linux/Windows job coverage is incomplete.')


def validate_artifacts(row: dict, artifacts: object, baseline: str) -> None:
    require(isinstance(artifacts, list) and all(isinstance(item, dict) for item in artifacts),
            'Artifacts must be an explicit inventory, including an empty list where none are produced.')
    require(all(isinstance(item.get('name'), str) for item in artifacts), 'Artifact name is malformed.')
    expected = {prefix + baseline for prefix in WORKFLOWS[row['name']][1]}
    require(len(artifacts) == len(expected) and {item.get('name') for item in artifacts} == expected,
            'Artifact names/source inventory differs from the retained workflow contract.')
    ids = []
    for item in artifacts:
        require(positive_id(item.get('id')) and type(item.get('sizeBytes')) is int and item['sizeBytes'] > 0,
                'Artifact ID or byte count is malformed.')
        require(item.get('runId') == row['runId'] and item.get('headSha') == baseline
                and item.get('headBranch') == 'main' and item.get('expired') is False,
                'Artifact is expired or belongs to a different run/source.')
        require(isinstance(item.get('digest'), str) and
                re.fullmatch(r'sha256:[0-9a-f]{64}', item['digest']) is not None,
                'Artifact SHA-256 digest must be recorded exactly as returned by Actions.')
        ids.append(item['id'])
    require(len(set(ids)) == len(ids), 'Artifact inventory contains duplicate identities.')


def validate_metadata(e: dict) -> str:
    require(isinstance(e, dict) and type(e.get('schema')) is int and e.get('schema') == 1
            and e.get('currentTask') == WORKSTREAM,
            'Expected the separate game-experience-improvement evidence contract.')
    baseline = e.get('implementationBaseline')
    require(exact_sha(baseline) and e.get('startingMain') == STARTING_MAIN,
            'An exact implementation SHA and the approved starting-main SHA are required.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    try:
        require(isinstance(e.get('statusDate'), str) and date.fromisoformat(e['statusDate']).isoformat()
                == e['statusDate'], 'Status date must be an ISO calendar date.')
    except (ValueError, TypeError):
        raise RuntimeError('Status date must be an ISO calendar date.') from None
    for key in ('repositorySideBatchComplete', 'serverAuthoritative', 'oldSavesCompatible', 'temporaryToolingRemoved'):
        require(e.get(key) is True, 'Required bounded acceptance boundary is absent: ' + key)
    for key in ('wholeGameComplete', 'publicationReady', 'releasePublished', 'deployed',
                'performanceTargetClaimed', 'windowsGpuPerformanceApproved', 'sixtyFpsApproved'):
        require(e.get(key) is False, 'Automated evidence cannot approve this claim: ' + key)
    authorization = e.get('authorization')
    require(isinstance(authorization, dict) and authorization.get('implementationAuthorized') is True
            and all(authorization.get(key) is False for key in (
                'publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged')),
            'The broad implementation authorization must preserve release/infrastructure boundaries.')
    require(e.get('releaseStatus') == RELEASE_STATUS and e.get('humanAcceptance') == 'not-run'
            and isinstance(e.get('humanOnlyGates'), list) and bool(e['humanOnlyGates'])
            and all(isinstance(gate, str) and gate.strip() for gate in e['humanOnlyGates']),
            'Unrun human acceptance and human-only release gates must remain explicit.')
    require(e.get('nativeAcceptancePlatforms') == ['linux', 'windows'], 'Native platform coverage is incomplete.')
    require(e.get('historicalEvidenceBlobs') == HISTORICAL_BLOBS,
            'The historical checkpoints and Task 20/21/22 byte identities must remain pinned.')
    paths = e.get('changedPaths')
    require(isinstance(paths, list) and bool(paths) and all(isinstance(path, str) for path in paths)
            and paths == sorted(set(paths)), 'Changed paths must be a nonempty sorted unique inventory.')
    for path in paths:
        validate_path(path)
    rows = e.get('implementationWorkflows')
    require(isinstance(rows, list) and len(rows) == len(WORKFLOWS)
            and all(isinstance(row, dict) and isinstance(row.get('name'), str) for row in rows)
            and {row['name'] for row in rows} == set(WORKFLOWS),
            'All 15 retained functional workflows and performance diagnostics are required exactly once.')
    for row in rows:
        require(row.get('workflowPath') == WORKFLOWS[row['name']][0]
                and all(positive_id(row.get(key)) for key in ('workflowId', 'runId', 'runAttempt')),
                'Workflow path or immutable run/attempt identity is malformed.')
        require(row.get('repository') == REPOSITORY and row.get('headBranch') == 'main'
                and row.get('headSha') == baseline and row.get('status') == 'completed'
                and row.get('conclusion') == 'success' and row.get('event') in ('push', 'workflow_dispatch'),
                'Every workflow must complete successfully on the exact main implementation.')
        validate_jobs(row, row.get('jobs'), baseline)
        validate_artifacts(row, row.get('artifacts'), baseline)
    for key in ('workflowId', 'runId'):
        require(len({row[key] for row in rows}) == len(rows), 'Workflow identities cannot be replayed: ' + key)
    for collection in ('jobs', 'artifacts'):
        ids = [item['id'] for row in rows for item in row[collection]]
        require(len(ids) == len(set(ids)), 'Cross-workflow evidence identity was replayed: ' + collection)
    return baseline


def validate_archive_blobs(blobs: dict) -> None:
    require(blobs == HISTORICAL_BLOBS, 'Historical evidence changed instead of being archived byte for byte.')


def blob_identity(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def validate_history(e: dict, baseline: str) -> None:
    require(latest_implementation_commit() == baseline, 'Implementation evidence is stale.')
    git('merge-base', '--is-ancestor', STARTING_MAIN, baseline)
    git('merge-base', '--is-ancestor', baseline, 'HEAD')
    actual = sorted(filter(None, git('diff', '--name-only', '-z', STARTING_MAIN, baseline).split('\0')))
    require(actual == e['changedPaths'], 'Recorded changed paths do not match the exact implementation diff.')
    dirty = list(filter(None, git('diff', '--name-only', '-z', 'HEAD').split('\0')))
    dirty += list(filter(None, git('ls-files', '--others', '--exclude-standard', '-z').split('\0')))
    require(all(path == 'HANDOFF.md' or path.startswith('docs/') for path in dirty),
            'Uncommitted implementation changes are not covered by exact-head evidence.')
    # Per-commit auditing prevents an implementation edit/revert from masquerading
    # as a documentation-only delivery with a clean final tree.
    for commit in git('rev-list', baseline + '..HEAD').splitlines():
        paths = list(filter(None, git('diff-tree', '--no-commit-id', '--name-only', '-z', '-r', '--root', '-m', commit).split('\0')))
        require(all(path == 'HANDOFF.md' or path.startswith('docs/') for path in paths),
                'Delivery after the verified implementation contains non-documentation changes: ' + commit)


def validate_remote_run(row: dict, actual: dict, workflow: dict, baseline: str) -> None:
    require(actual.get('id') == row['runId'] and actual.get('name') == row['name']
            and actual.get('workflow_id') == row['workflowId'] and actual.get('path') == row['workflowPath']
            and actual.get('run_attempt') == row['runAttempt'], 'Actions run identity/path/attempt does not match evidence.')
    require(actual.get('repository', {}).get('full_name') == REPOSITORY
            and actual.get('head_sha') == baseline and actual.get('head_branch') == 'main'
            and actual.get('event') == row['event'] and actual.get('status') == 'completed'
            and actual.get('conclusion') == 'success', 'Actions run is not successful at the exact main source.')
    require(workflow.get('id') == row['workflowId'] and workflow.get('name') == row['name']
            and workflow.get('path') == row['workflowPath'] and workflow.get('state') == 'active',
            'Actions workflow identity is absent, renamed, disabled or points to a different path.')


def validate_remote_jobs(row: dict, jobs: list[dict], baseline: str) -> None:
    require(isinstance(jobs, list) and all(isinstance(job, dict) for job in jobs),
            'Malformed real Actions job inventory.')
    normalized = [{
        'id': job.get('id'), 'name': job.get('name'), 'runId': job.get('run_id'),
        'runAttempt': job.get('run_attempt'), 'headSha': job.get('head_sha'),
        'status': job.get('status'), 'conclusion': job.get('conclusion'),
    } for job in jobs]
    validate_jobs(row, normalized, baseline)
    require(sorted(normalized, key=lambda item: item['id']) == sorted(row['jobs'], key=lambda item: item['id']),
            'Recorded jobs differ from the complete real Actions attempt inventory.')
    # OS-specific steps may legitimately be skipped; a skipped job never is.


def validate_remote_artifacts(row: dict, artifacts: list[dict], baseline: str) -> None:
    require(isinstance(artifacts, list) and all(isinstance(item, dict) for item in artifacts),
            'Malformed real Actions artifact inventory.')
    normalized = [{
        'id': item.get('id'), 'name': item.get('name'), 'sizeBytes': item.get('size_in_bytes'),
        'digest': item.get('digest'), 'expired': item.get('expired'),
        'runId': item.get('workflow_run', {}).get('id'),
        'headSha': item.get('workflow_run', {}).get('head_sha'),
        'headBranch': item.get('workflow_run', {}).get('head_branch'),
    } for item in artifacts]
    validate_artifacts(row, normalized, baseline)
    require(sorted(normalized, key=lambda item: item['id']) == sorted(row['artifacts'], key=lambda item: item['id']),
            'Recorded artifacts differ from the complete live Actions inventory.')


def api_get(path: str, token: str) -> dict:
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{path}', headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        value = json.load(response)
    require(isinstance(value, dict), 'Malformed Actions API response.')
    return value


def api_inventory(path: str, key: str, token: str) -> list[dict]:
    rows, total = [], None
    # Finite pagination; this battery has only a few jobs/artifacts per run.
    for page in range(1, 101):
        value = api_get(f'{path}?per_page=100&page={page}', token)
        count, items = value.get('total_count'), value.get(key)
        require(type(count) is int and count >= 0 and isinstance(items, list)
                and all(isinstance(item, dict) for item in items), 'Malformed Actions inventory.')
        if total is None:
            total = count
        require(total == count, 'Actions inventory changed during verification; retry after it is stable.')
        rows.extend(items)
        if len(rows) == total:
            return rows
        require(bool(items) and len(rows) < total, 'Actions inventory is truncated or inconsistent.')
    raise RuntimeError('Actions inventory exceeded the finite pagination limit.')


def validate(e: dict) -> int:
    baseline = validate_metadata(e)
    validate_history(e, baseline)
    validate_archive_blobs({path: blob_identity((ROOT / path).read_bytes()) for path in HISTORICAL_BLOBS})
    for path in (*TEMPORARY_PATHS, '.github/workflows/acceptance-dispatch.yml'):
        require(not (ROOT / path).exists(), 'Removed temporary dispatcher/tooling reappeared: ' + path)
    for relative in CURRENT_DOCS:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS, WORKSTREAM, e['statusDate']):
            require(marker in text, relative + ' omits a current-evidence marker: ' + marker)
    verification = (ROOT / CURRENT_DOCS[-1]).read_text(encoding='utf-8')
    for row in e['implementationWorkflows']:
        require(str(row['runId']) in verification and row['name'] in verification
                and row['workflowPath'] in verification, 'Verification documentation omits workflow identity.')
    if os.environ.get('CI', '').lower() == 'true':
        token = os.environ.get('GITHUB_TOKEN', '')
        require(bool(token), 'CI requires its read-only Actions token; offline fixtures are not live acceptance.')
        for row in e['implementationWorkflows']:
            base = f'actions/runs/{row["runId"]}'
            validate_remote_run(row, api_get(base, token),
                                api_get(f'actions/workflows/{row["workflowId"]}', token), baseline)
            validate_remote_jobs(row, api_inventory(
                f'{base}/attempts/{row["runAttempt"]}/jobs', 'jobs', token), baseline)
            validate_remote_artifacts(row, api_inventory(f'{base}/artifacts', 'artifacts', token), baseline)
        mode = 'live-actions-verified'
    else:
        mode = 'offline-structure-only; run CI for remote verification'
    print(f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; implementation={baseline}; '
          f'workflows={len(WORKFLOWS)}; {mode}; whole-game-complete=false; human-acceptance=not-run')
    return 0
