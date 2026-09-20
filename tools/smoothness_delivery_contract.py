#!/usr/bin/env python3
"""Verify exact-head smoothness/performance checkpoint evidence.

Checkpoint 0 reconciles inherited smoothness delivery evidence.
Checkpoint 1 adds bounded measurement tooling only; it does not approve a
Windows 60 FPS target or claim a performance improvement.
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
CHECKPOINT1 = 1
CHECKPOINT2 = 2
CHECKPOINT3 = 3
STARTING_MAIN = '1a4704fee2194bf3b9c51eb28b6e7408a7c1e72e'
CHECKPOINT1_STARTING_MAIN = '6e76af928af21c8ed7e1d14fd9fe59093174d228'
CHECKPOINT2_STARTING_MAIN = 'efd418c4233802e91f5e0dd861b73119addb850d'
CHECKPOINT3_STARTING_MAIN = '192c8b50ce6ecac11e6327189af6208dd26c7944'
PREVIOUS = 'docs/handoff/COMBAT_EVIDENCE_2026-09-18.json'
PREVIOUS_BLOB = 'cf1a93b5cd2481dcc1de86ec10c72469d3828fc0'
CHECKPOINT0_ARCHIVE = 'docs/handoff/SMOOTHNESS_CHECKPOINT0_EVIDENCE_2026-09-20.json'
CHECKPOINT0_ARCHIVE_BLOB = '79779ce75560c5dd98132827181e8f56f35e1f70'
CHECKPOINT1_ARCHIVE = 'docs/handoff/SMOOTHNESS_CHECKPOINT1_EVIDENCE_2026-09-20.json'
CHECKPOINT1_ARCHIVE_BLOB = '10654d5d0d4605c7f9708faccb8b7cfd13257efb'
CHECKPOINT2_ARCHIVE = 'docs/handoff/SMOOTHNESS_CHECKPOINT2_EVIDENCE_2026-09-20.json'
CHECKPOINT2_ARCHIVE_BLOB = '43df0bc5281a8f969268d38f32c57c943c70c412'
PRESERVED_COMBAT_BASELINE = '06776f6b0de7dbe02cab30a9e236e730c377de2e'
PRESERVED_COMBAT_DELIVERY = 'bc9561846cd480c1e899190cb9b6f2df75a30176'
PERFORMANCE_WORKFLOW = 'Client performance and motion diagnostics'

REQUIRED_WORKFLOWS = frozenset({
    'Transaction security regression', 'Compile Windows client source',
    'Live progression breadth', 'Windows package acceptance',
    'Graphical multiplayer acceptance', 'Load acceptance', 'Build and verify',
    'Task 13 adversarial acceptance', 'Release operations acceptance',
    'Transaction integrity on Windows and Linux', 'New-player journey',
    'Character sprite acceptance', 'Visual acceptance matrix',
    'Windows display and input acceptance', 'Audio acceptance',
})
CHECKPOINT0_DOCS = (
    'HANDOFF.md',
    'docs/SESSION_STATUS.md',
    'docs/handoff/SMOOTHNESS_VERIFICATION.md',
)
CHECKPOINT1_DOCS = (
    'HANDOFF.md',
    'docs/SESSION_STATUS.md',
    'docs/handoff/PERFORMANCE_DIAGNOSTICS_VERIFICATION.md',
)
CHECKPOINT2_DOCS = (
    'HANDOFF.md',
    'docs/SESSION_STATUS.md',
    'docs/handoff/PERFORMANCE_OPTIMIZATION_VERIFICATION.md',
)
CHECKPOINT3_DOCS = (
    'HANDOFF.md',
    'docs/SESSION_STATUS.md',
    'docs/handoff/MOVEMENT_RANGED_BASIC_VERIFICATION.md',
)
CHECKPOINT0_ALLOWED_PATHS = frozenset({
    'tools/documentation_contract.py',
    'tools/smoothness_delivery_contract.py',
    'tests/handoff/test_smoothness_evidence.py',
    PREVIOUS,
})
CHECKPOINT1_ALLOWED_PATHS = frozenset({
    '.github/workflows/performance-diagnostics.yml',
    'client/Scripts/ClientPerformanceDiagnostics.cs',
    'client/Scripts/GameRoot.cs',
    'client/Scripts/PixelAssets.cs',
    'client/Scripts/WorldView.Presentation.cs',
    'client/Scripts/WorldView.cs',
    'client/Tests/PerformanceMotionDiagnosticsContract.cs',
    'client/Tests/PerformanceMotionDiagnosticsContract.tscn',
    'tools/smoothness_delivery_contract.py',
    'tests/handoff/test_smoothness_evidence.py',
    CHECKPOINT0_ARCHIVE,
})
CHECKPOINT2_ALLOWED_PATHS = frozenset({
    'client/Scripts/GameRoot.cs',
    'client/Scripts/PixelAssets.cs',
    'client/Scripts/WorldView.cs',
    'client/Tests/InventoryRefreshChecks.cs',
    'client/Tests/PerformanceMotionDiagnosticsContract.cs',
    'tools/smoothness_delivery_contract.py',
    'tests/handoff/test_smoothness_evidence.py',
    CHECKPOINT1_ARCHIVE,
})
CHECKPOINT3_ALLOWED_PATHS = frozenset({
    '.github/workflows/acceptance-dispatch.yml',
    '.github/workflows/performance-diagnostics.yml',
    'client/Scripts/ClientPerformanceDiagnostics.cs',
    'client/Scripts/CombatReadabilityOverlay.cs',
    'client/Scripts/ExperienceRules.cs',
    'client/Scripts/GameRoot.cs',
    'client/Scripts/GameRoot.Experience.cs',
    'client/Scripts/GameRoot.Hud.cs',
    'client/Scripts/GameRoot.MobControls.cs',
    'client/Scripts/WorldView.CharacterMotion.cs',
    'client/Scripts/WorldView.cs',
    'client/Tests/CharacterPresentationContract.cs',
    'client/Tests/ControlRulesContract.cs',
    'client/Tests/LiveExperienceContract.cs',
    'client/Tests/PresentationChecks.cs',
    'client/Tests/PerformanceMotionDiagnosticsContract.cs',
    'client/Tests/PlayerExperienceContract.cs',
    'src/Kairnfall.Core/BasicAttackRules.cs',
    'src/Kairnfall.Core/Models.cs',
    'src/Kairnfall.Core/RealmCombat.cs',
    'tests/Kairnfall.Tests/Program.cs',
    'tools/smoothness_delivery_contract.py',
    'tests/handoff/test_smoothness_evidence.py',
})
PRESERVED_SMOOTHNESS_PATHS = frozenset({
    'client/Scripts/WorldView.CharacterMotion.cs',
    'client/Scripts/WorldView.cs',
    'client/Tests/CharacterPresentationContract.cs',
})


def sha1_blob(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(
        b'blob ' + str(len(data)).encode('ascii') + b'\0' + data
    ).hexdigest()


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


def validate_performance_jobs(jobs: list[dict]) -> None:
    require(isinstance(jobs, list), 'Performance native job evidence must be a list.')
    required = {
        'diagnostics (ubuntu-latest, linux)',
        'diagnostics (windows-latest, windows)',
    }
    names = [job.get('name') for job in jobs]
    require(set(names) == required and len(names) == len(required),
            'Performance diagnostics must contain exactly Linux and Windows jobs.')
    require(all(job.get('status') == 'completed' and job.get('conclusion') == 'success'
                for job in jobs),
            'Every performance diagnostic platform job must complete successfully.')


def validate_common(e: dict) -> str:
    require(e.get('schema') == 1 and e.get('currentTask') == WORKSTREAM,
            'Current evidence does not describe the smoothness/performance workstream.')
    baseline = e.get('implementationBaseline', '')
    require(isinstance(baseline, str) and re.fullmatch(r'[0-9a-f]{40}', baseline) is not None,
            'Expected an exact checkpoint implementation SHA.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    require(e.get('preservedCombatBaseline') == PRESERVED_COMBAT_BASELINE and
            e.get('preservedCombatDelivery') == PRESERVED_COMBAT_DELIVERY,
            'Preserved combat revision references drifted.')
    require(e.get('historicalCombatEvidence') == PREVIOUS,
            'Historical combat evidence reference drifted.')
    require(e.get('serverAuthoritative') is True and e.get('oldSavesCompatible') is True
            and e.get('temporaryToolingRemoved') is True,
            'Authority, save compatibility or cleanup boundary drifted.')
    for key in ('combatBalanceChanged', 'movementSpeedChanged', 'tickFrequencyChanged',
                'publicationReady', 'releasePublished', 'deployed'):
        require(e.get(key) is False, 'Unauthorized checkpoint claim/change: ' + key)
    authorization = e.get('authorization', {})
    require(authorization.get('implementationAuthorized') is True,
            'Implementation authorization is missing.')
    for key in ('publicationAuthorized', 'deploymentAuthorized',
                'productionInfrastructureChanged'):
        require(authorization.get(key) is False,
                'Unauthorized publication/deployment/infrastructure claim: ' + key)
    require(e.get('releaseStatus') == RELEASE_STATUS, 'Release status drifted.')
    gates = e.get('humanOnlyGates')
    require(isinstance(gates, list) and gates and
            all(isinstance(item, str) and item.strip() for item in gates),
            'Human-only acceptance gates cannot be erased.')
    require(e.get('nativeAcceptancePlatforms') == ['linux', 'windows'],
            'Native character platform coverage must remain Linux and Windows.')

    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list) and len(rows) == len(REQUIRED_WORKFLOWS)
            and all(isinstance(row, dict) for row in rows),
            'Incomplete checkpoint workflow evidence.')
    require({row.get('name') for row in rows} == REQUIRED_WORKFLOWS,
            'Required checkpoint workflows are missing or duplicated.')
    require(all(type(row.get('runId')) is int and row['runId'] > 0
                and row.get('headSha') == baseline
                and row.get('conclusion') == 'success' for row in rows),
            'Every checkpoint workflow must succeed on the exact implementation SHA.')
    require(len({row['runId'] for row in rows}) == len(rows),
            'Checkpoint workflow run IDs must be unique.')
    return baseline


def validate_checkpoint0_metadata(e: dict) -> str:
    baseline = validate_common(e)
    require(e.get('checkpoint') == CHECKPOINT,
            'Current smoothness evidence does not describe checkpoint 0.')
    require(e.get('startingMain') == STARTING_MAIN, 'Checkpoint 0 starting main changed.')
    require(e.get('repositorySideCheckpoint0Complete') is True,
            'Checkpoint 0 completion is not explicit.')
    require(e.get('gameplaySourceChangedInCheckpoint0') is False,
            'Checkpoint 0 cannot change gameplay source.')
    require(e.get('performanceTargetClaimed') is False,
            'Checkpoint 0 cannot claim the performance target.')
    return baseline


def validate_checkpoint1_metadata(e: dict) -> str:
    baseline = validate_common(e)
    require(e.get('checkpoint') == CHECKPOINT1,
            'Current smoothness evidence does not describe checkpoint 1.')
    require(e.get('startingMain') == STARTING_MAIN,
            'Overall smoothness starting main changed.')
    require(e.get('checkpointStartingMain') == CHECKPOINT1_STARTING_MAIN,
            'Checkpoint 1 starting main changed.')
    require(e.get('historicalCheckpoint0Evidence') == CHECKPOINT0_ARCHIVE,
            'Checkpoint 0 archive reference drifted.')
    require(e.get('repositorySideCheckpoint1Complete') is True,
            'Checkpoint 1 completion is not explicit.')
    require(e.get('gameplayBehaviorChangedInCheckpoint1') is False,
            'Checkpoint 1 is diagnostics-only and cannot change gameplay behavior.')
    require(e.get('performanceImprovementClaimed') is False,
            'Checkpoint 1 cannot claim an optimization improvement.')
    require(e.get('performanceTargetClaimed') is False,
            'Checkpoint 1 cannot claim the 60 FPS target.')

    diagnostic = e.get('diagnosticsEvidence', {})
    require(diagnostic.get('optIn') is True and diagnostic.get('boundedHistory') == 4096,
            'Diagnostics must remain opt-in and bounded.')
    require(diagnostic.get('perFrameConsoleOutput') is False
            and diagnostic.get('synchronousPerFrameFileWrites') is False,
            'Diagnostics cannot add per-frame console or file I/O.')
    require(diagnostic.get('nativeScenarios') == 10
            and diagnostic.get('syntheticMotionSchedules') == 36
            and diagnostic.get('renderRatesFps') == [30, 60, 120, 144],
            'Checkpoint 1 scenario/rate matrix is incomplete.')
    require(diagnostic.get('windowsLocalGpuMeasured') is True,
            'Checkpoint 1 must record the connected Windows GPU fixture.')
    require(diagnostic.get('windowsGpuPerformanceApproved') is False
            and diagnostic.get('sixtyFpsApproved') is False,
            'Diagnostics cannot promote a fixture into 60 FPS approval.')

    validate_performance_workflow(e, baseline)
    return baseline


def validate_performance_workflow(e: dict, baseline: str) -> None:
    perf = e.get('performanceWorkflow', {})
    require(perf.get('name') == PERFORMANCE_WORKFLOW,
            'Performance workflow identity drifted.')
    require(type(perf.get('runId')) is int and perf['runId'] > 0
            and perf.get('headSha') == baseline
            and perf.get('conclusion') == 'success',
            'Performance workflow must succeed on the exact implementation SHA.')
    require(perf['runId'] not in {row['runId'] for row in e['implementationWorkflows']},
            'Performance workflow run ID must not duplicate another acceptance run.')
    require(perf.get('nativePlatforms') == ['linux', 'windows'],
            'Performance workflow must retain Linux and Windows coverage.')
    artifact_ids = perf.get('artifactIds')
    require(isinstance(artifact_ids, list) and len(artifact_ids) == 2
            and len(set(artifact_ids)) == 2
            and all(type(value) is int and value > 0 for value in artifact_ids),
            'Performance workflow must record two unique native artifacts.')


def validate_checkpoint2_metadata(e: dict) -> str:
    baseline = validate_common(e)
    require(e.get('checkpoint') == CHECKPOINT2,
            'Current smoothness evidence does not describe checkpoint 2.')
    require(e.get('startingMain') == STARTING_MAIN,
            'Overall smoothness starting main changed.')
    require(e.get('checkpointStartingMain') == CHECKPOINT2_STARTING_MAIN,
            'Checkpoint 2 starting main changed.')
    require(e.get('historicalCheckpoint1Evidence') == CHECKPOINT1_ARCHIVE,
            'Checkpoint 1 archive reference drifted.')
    require(e.get('repositorySideCheckpoint2Complete') is True,
            'Checkpoint 2 completion is not explicit.')
    require(e.get('gameplayBehaviorChangedInCheckpoint2') is False,
            'Checkpoint 2 cannot change gameplay behavior.')
    require(e.get('performanceImprovementClaimed') is True,
            'Checkpoint 2 must record its measured targeted improvement.')
    require(e.get('performanceTargetClaimed') is False,
            'Checkpoint 2 cannot promote a targeted win into 60 FPS approval.')

    optimization = e.get('optimizationEvidence', {})
    require(optimization.get('metric') == 'inventory-panel-stamp'
            and optimization.get('comparisonKind') == 'same-process legacy-vs-candidate',
            'Checkpoint 2 must retain its like-for-like Inventory stamp comparison.')
    require(type(optimization.get('iterations')) is int and optimization['iterations'] >= 1000,
            'Checkpoint 2 benchmark sample count is insufficient.')
    legacy_us = optimization.get('legacyMicrosecondsPerCall')
    candidate_us = optimization.get('candidateMicrosecondsPerCall')
    legacy_bytes = optimization.get('legacyAllocatedBytesPerCall')
    candidate_bytes = optimization.get('candidateAllocatedBytesPerCall')
    require(all(isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in (legacy_us, candidate_us, legacy_bytes, candidate_bytes)),
            'Checkpoint 2 benchmark values must be numeric.')
    require(legacy_us > candidate_us > 0,
            'Checkpoint 2 must demonstrate a faster Inventory stamp.')
    require(legacy_bytes > candidate_bytes >= 0,
            'Checkpoint 2 must demonstrate lower Inventory stamp allocation.')
    require(optimization.get('broadFramePercentageClaimed') is False,
            'No broad frame-performance percentage may be inferred from the noisy native runs.')
    require(optimization.get('coldLoadOptimizationDeferred') is True,
            'Cold-load work must remain explicitly deferred when it was not optimized.')
    validate_performance_workflow(e, baseline)
    return baseline


def validate_checkpoint3_metadata(e: dict) -> str:
    baseline = validate_common(e)
    require(e.get('checkpoint') == CHECKPOINT3,
            'Current smoothness evidence does not describe checkpoint 3.')
    require(e.get('startingMain') == STARTING_MAIN,
            'Overall smoothness starting main changed.')
    require(e.get('checkpointStartingMain') == CHECKPOINT3_STARTING_MAIN,
            'Checkpoint 3 starting main changed.')
    require(e.get('historicalCheckpoint2Evidence') == CHECKPOINT2_ARCHIVE,
            'Checkpoint 2 archive reference drifted.')
    require(e.get('repositorySideCheckpoint3Complete') is True,
            'Checkpoint 3 completion is not explicit.')
    require(e.get('gameplayBehaviorChangedInCheckpoint3') is True,
            'Checkpoint 3 must explicitly record its authorized gameplay behavior changes.')
    require(e.get('performanceImprovementClaimed') is False
            and e.get('performanceTargetClaimed') is False,
            'Checkpoint 3 cannot turn motion continuity into a broad frame-performance claim.')
    require(e.get('movementContinuityImprovementClaimed') is True,
            'Checkpoint 3 must record the measured movement continuity improvement.')

    motion = e.get('movementEvidence', {})
    require(motion.get('comparisonKind') == 'same-process legacy-vs-candidate'
            and motion.get('renderRatesFps') == [30, 60, 120, 144]
            and motion.get('syntheticMotionSchedules') == 48
            and motion.get('nativeScenarios') == 11,
            'Checkpoint 3 movement matrix is incomplete.')
    legacy_stops = motion.get('legacyFalseStopFramesByFps')
    candidate_stops = motion.get('candidateFalseStopFramesByFps')
    legacy_longest = motion.get('legacyLongestFalseStopMsByFps')
    candidate_longest = motion.get('candidateLongestFalseStopMsByFps')
    for values in (legacy_stops, candidate_stops, legacy_longest, candidate_longest):
        require(isinstance(values, list) and len(values) == 4
                and all(isinstance(value, (int, float)) and not isinstance(value, bool)
                        and value >= 0 for value in values),
                'Checkpoint 3 false-stop evidence must contain four numeric render-rate samples.')
    require(sum(candidate_stops) < sum(legacy_stops),
            'Checkpoint 3 must reduce interstitial false-stop frames versus the retained legacy rules.')
    require(max(candidate_longest) <= 50,
            'Checkpoint 3 candidate contains a sustained false-stop interval.')
    require(isinstance(motion.get('candidateP95ErrorTiles144'), (int, float))
            and motion['candidateP95ErrorTiles144'] >= 0
            and isinstance(motion.get('candidateMaxErrorTiles144'), (int, float))
            and motion['candidateMaxErrorTiles144'] <= 0.5
            and isinstance(motion.get('candidateMaxForwardLeadTiles144'), (int, float))
            and motion['candidateMaxForwardLeadTiles144'] <= 0.47
            and isinstance(motion.get('candidateFinalErrorTiles144'), (int, float))
            and motion['candidateFinalErrorTiles144'] <= 0.03,
            'Checkpoint 3 position/convergence evidence is missing or exceeds the accepted bounds.')
    require(type(motion.get('nativeFalseStopFramesWindows')) is int
            and motion['nativeFalseStopFramesWindows'] >= 0
            and isinstance(motion.get('nativeLongestFalseStopMsWindows'), (int, float))
            and motion['nativeLongestFalseStopMsWindows'] <= 50,
            'Checkpoint 3 Windows native continuity evidence is invalid.')

    ranged = e.get('rangedBasicAttackEvidence', {})
    require(ranged.get('classes') == ['arcanist', 'templar']
            and ranged.get('rangeTiles') == 6.0
            and ranged.get('serverAuthoritative') is True
            and ranged.get('targetedProjectile') is True
            and ranged.get('meleeClassesRemainMelee') is True
            and ranged.get('basicDamageFormulaChanged') is False
            and ranged.get('attackCooldownFormulaChanged') is False
            and ranged.get('visualElements') == {'arcanist': 'Arcane', 'templar': 'Radiant'},
            'Checkpoint 3 ranged-basic attack evidence is incomplete or changes unauthorized combat rules.')
    validate_performance_workflow(e, baseline)
    return baseline


def validate_metadata(e: dict) -> str:
    checkpoint = e.get('checkpoint')
    if checkpoint == CHECKPOINT:
        return validate_checkpoint0_metadata(e)
    if checkpoint == CHECKPOINT1:
        return validate_checkpoint1_metadata(e)
    if checkpoint == CHECKPOINT2:
        return validate_checkpoint2_metadata(e)
    if checkpoint == CHECKPOINT3:
        return validate_checkpoint3_metadata(e)
    raise RuntimeError('Unsupported smoothness checkpoint evidence.')


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


def validate_source_boundary(e: dict, baseline: str) -> None:
    checkpoint = e['checkpoint']
    if checkpoint == CHECKPOINT:
        checkpoint_start = STARTING_MAIN
        allowed = CHECKPOINT0_ALLOWED_PATHS
    elif checkpoint == CHECKPOINT1:
        checkpoint_start = CHECKPOINT1_STARTING_MAIN
        allowed = CHECKPOINT1_ALLOWED_PATHS
    elif checkpoint == CHECKPOINT2:
        checkpoint_start = CHECKPOINT2_STARTING_MAIN
        allowed = CHECKPOINT2_ALLOWED_PATHS
    else:
        checkpoint_start = CHECKPOINT3_STARTING_MAIN
        allowed = CHECKPOINT3_ALLOWED_PATHS
    git('merge-base', '--is-ancestor', checkpoint_start, baseline)
    paths = {
        path for path in git('diff', '--name-only', checkpoint_start, baseline).splitlines()
        if path
    }
    require(paths == allowed,
            f'Checkpoint {checkpoint} changed paths outside its accepted footprint: ' +
            ', '.join(sorted(paths ^ allowed)))
    protected_roots = ('content_src', 'src/Kairnfall.Server') if checkpoint == CHECKPOINT3 else (
        'content_src', 'src/Kairnfall.Server', 'src/Kairnfall.Core')
    for protected in protected_roots:
        changed = {
            path for path in git(
                'diff', '--name-only', checkpoint_start, baseline, '--', protected
            ).splitlines() if path
        }
        require(not changed,
                f'Checkpoint {checkpoint} changed protected gameplay source: ' +
                ', '.join(sorted(changed)))


def validate_archives(e: dict) -> None:
    require(sha1_blob(ROOT / PREVIOUS) == PREVIOUS_BLOB,
            'Historical combat evidence changed instead of being archived byte-for-byte.')
    if e['checkpoint'] >= CHECKPOINT1:
        require(sha1_blob(ROOT / CHECKPOINT0_ARCHIVE) == CHECKPOINT0_ARCHIVE_BLOB,
                'Checkpoint 0 evidence changed instead of being archived byte-for-byte.')
    if e['checkpoint'] >= CHECKPOINT2:
        require(sha1_blob(ROOT / CHECKPOINT1_ARCHIVE) == CHECKPOINT1_ARCHIVE_BLOB,
                'Checkpoint 1 evidence changed instead of being archived byte-for-byte.')
    if e['checkpoint'] >= CHECKPOINT3:
        require(sha1_blob(ROOT / CHECKPOINT2_ARCHIVE) == CHECKPOINT2_ARCHIVE_BLOB,
                'Checkpoint 2 evidence changed instead of being archived byte-for-byte.')


def validate_inherited_smoothness() -> None:
    inherited = {
        path for path in git(
            'diff', '--name-only', PRESERVED_COMBAT_DELIVERY, STARTING_MAIN,
            '--', 'client'
        ).splitlines() if path
    }
    require(inherited == PRESERVED_SMOOTHNESS_PATHS,
            'Inherited smoothness footprint differs from the verified three-file delta: ' +
            ', '.join(sorted(inherited)))


def rows_from(e: dict) -> list[dict]:
    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list), 'Implementation workflows must be a list.')
    return rows


def validate_docs(e: dict, baseline: str) -> None:
    docs = (CHECKPOINT0_DOCS if e['checkpoint'] == CHECKPOINT
            else CHECKPOINT1_DOCS if e['checkpoint'] == CHECKPOINT1
            else CHECKPOINT2_DOCS if e['checkpoint'] == CHECKPOINT2
            else CHECKPOINT3_DOCS)
    for relative in docs:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS,
                       TITLE, e.get('statusDate', '')):
            require(bool(marker) and marker in text,
                    relative + ' omits a current smoothness-evidence marker.')
    verification = (ROOT / docs[-1]).read_text(encoding='utf-8')
    for row in rows_from(e):
        require(str(row['runId']) in verification and row['name'] in verification,
                'Smoothness verification document omits a workflow.')
    if e['checkpoint'] >= CHECKPOINT1:
        perf = e['performanceWorkflow']
        require(str(perf['runId']) in verification and perf['name'] in verification,
                'Performance verification document omits the diagnostic workflow.')


def validate_live(e: dict, baseline: str) -> str:
    if os.environ.get('CI', '').lower() != 'true':
        return 'offline-structure-only; run CI for live Actions verification'
    token = os.environ.get('GITHUB_TOKEN', '')
    require(bool(token), 'CI requires a read-only Actions token.')
    character_jobs = None
    for row in rows_from(e):
        actual = api(f'actions/runs/{row["runId"]}', token)
        validate_remote_run(row, actual, baseline)
        if row['name'] == 'Character sprite acceptance':
            character_jobs = api(
                f'actions/runs/{row["runId"]}/jobs?per_page=100', token
            ).get('jobs', [])
    require(character_jobs is not None,
            'Character sprite acceptance run is missing from live evidence.')
    validate_native_jobs(character_jobs)

    if e['checkpoint'] >= CHECKPOINT1:
        perf = e['performanceWorkflow']
        actual = api(f'actions/runs/{perf["runId"]}', token)
        validate_remote_run(perf, actual, baseline)
        perf_jobs = api(
            f'actions/runs/{perf["runId"]}/jobs?per_page=100', token
        ).get('jobs', [])
        validate_performance_jobs(perf_jobs)
        artifacts = api(f'actions/runs/{perf["runId"]}/artifacts?per_page=100', token)
        live_ids = {item.get('id') for item in artifacts.get('artifacts', [])}
        require(set(perf['artifactIds']) == live_ids,
                'Recorded performance artifact IDs do not match the exact workflow run.')
    return 'live-actions-verified'


def validate_checkpoint3_delivery_boundary(baseline: str) -> None:
    """After exact-head acceptance, permit only evidence sync and temporary-helper cleanup."""
    git('merge-base', '--is-ancestor', baseline, 'HEAD')
    helper = '.github/workflows/acceptance-dispatch.yml'
    allowed_non_docs = {helper, 'tools/smoothness_delivery_contract.py'}
    commits = [value for value in git('rev-list', '--reverse', f'{baseline}..HEAD').splitlines() if value]
    for commit in commits:
        paths = {
            path for path in git('diff-tree', '--no-commit-id', '--name-only', '-r', commit).splitlines()
            if path
        }
        unexpected = {
            path for path in paths
            if path != 'HANDOFF.md' and not path.startswith('docs/') and path not in allowed_non_docs
        }
        require(not unexpected,
                'Checkpoint 3 changed implementation source after exact-head acceptance: ' +
                ', '.join(sorted(unexpected)))
    require(not (ROOT / helper).exists(),
            'Temporary exact-head acceptance dispatcher remains in the delivery tree.')


def validate(e: dict) -> int:
    baseline = validate_metadata(e)
    if e['checkpoint'] == CHECKPOINT3:
        validate_checkpoint3_delivery_boundary(baseline)
    else:
        require(latest_implementation_commit() == baseline,
                'Smoothness checkpoint implementation evidence is stale.')
    git('merge-base', '--is-ancestor', STARTING_MAIN, baseline)
    git('merge-base', '--is-ancestor', baseline, 'HEAD')
    validate_archives(e)
    validate_inherited_smoothness()
    validate_source_boundary(e, baseline)
    validate_docs(e, baseline)
    mode = validate_live(e, baseline)
    print(
        f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; checkpoint={e["checkpoint"]}; '
        f'implementation={baseline}; workflows={len(REQUIRED_WORKFLOWS)}; {mode}'
    )
    return 0
