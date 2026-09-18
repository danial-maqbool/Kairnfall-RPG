#!/usr/bin/env python3
"""Verify the combat-feel pass against source boundaries and exact-head Actions.

This contract proves repository-side combat input/presentation behavior only.
It never grants subjective combat-feel, artistic, publication, or release approval.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.request

from documentation_contract import (ROOT, REPOSITORY, RELEASE_STATUS, require, git,
                                    latest_implementation_commit, validate_remote_run)

WORKSTREAM = 'combat-feel-pass'
TITLE = 'Combat feel and encounter presentation'
PREVIOUS = 'docs/handoff/CHARACTER_EVIDENCE_2026-09-18.json'
PREVIOUS_BLOB = '290104e10b3f0562e26138c08946d2bb06599093'
STARTING_MAIN = '7658fdf0d505d886bc0058565eea5c7e9f907dc0'
BASIC_BUFFER = .25
ABILITY_BUFFER = .35
TARGET_GRACE = 1.75

REQUIRED_WORKFLOWS = frozenset({
    'Transaction security regression', 'Compile Windows client source',
    'Live progression breadth', 'Windows package acceptance',
    'Graphical multiplayer acceptance', 'Load acceptance', 'Build and verify',
    'Task 13 adversarial acceptance', 'Release operations acceptance',
    'Transaction integrity on Windows and Linux', 'New-player journey',
    'Character sprite acceptance', 'Visual acceptance matrix',
    'Windows display and input acceptance', 'Audio acceptance',
})
CURRENT_DOCS = ('HANDOFF.md', 'docs/SESSION_STATUS.md', 'docs/COMBAT_FEEL.md',
                'docs/handoff/COMBAT_FEEL_VERIFICATION.md')


def validate_metadata(e: dict) -> str:
    require(e.get('schema') == 1 and e.get('currentTask') == WORKSTREAM,
            'Current evidence does not describe the combat-feel pass.')
    baseline = e.get('implementationBaseline', '')
    require(isinstance(baseline, str) and re.fullmatch(r'[0-9a-f]{40}', baseline) is not None,
            'Expected an exact implementation SHA.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    for key in ('repositorySideCombatFeelImplemented', 'serverAuthoritative', 'oldSavesCompatible',
                'temporaryToolingRemoved'):
        require(e.get(key) is True, 'Required combat delivery boundary is missing: ' + key)
    for key in ('clientPredictsDamage', 'combatBalanceChanged', 'publicationReady',
                'releasePublished', 'deployed', 'humanCombatFeelApproval'):
        require(e.get(key) is False, 'Automated combat evidence cannot claim or change: ' + key)
    authorization = e.get('authorization', {})
    require(authorization.get('implementationAuthorized') is True, 'Implementation authorization is missing.')
    for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
        require(authorization.get(key) is False, 'Unauthorized release/infrastructure claim: ' + key)
    require(e.get('releaseStatus') == RELEASE_STATUS, 'Release status drifted.')
    require(e.get('historicalCharacterEvidence') == PREVIOUS, 'Historical character evidence reference drifted.')
    require(e.get('startingMain') == STARTING_MAIN, 'Combat-pass starting main changed.')
    require(type(e.get('basicAttackBufferSeconds')) in (int, float)
            and abs(e['basicAttackBufferSeconds'] - BASIC_BUFFER) < 1e-9,
            'Basic attack input buffer changed.')
    require(type(e.get('abilityBufferSeconds')) in (int, float)
            and abs(e['abilityBufferSeconds'] - ABILITY_BUFFER) < 1e-9,
            'Ability input buffer changed.')
    require(type(e.get('selectedTargetGrace')) in (int, float)
            and abs(e['selectedTargetGrace'] - TARGET_GRACE) < 1e-9,
            'Selected-target approach grace changed.')
    features = e.get('combatEvidence', {})
    for key in ('bufferedBasicAttack', 'lockedQueuedAbilityIntent', 'stickyExplicitTargets',
                'threatAwareAutoTarget', 'authoritativeTargetSummary', 'urgentTelegraphPresentation',
                'accurateDamageAttributionBoundary'):
        require(features.get(key) is True, 'Combat evidence feature is missing: ' + key)
    gates = e.get('humanOnlyGates')
    require(isinstance(gates, list) and gates and all(isinstance(g, str) and g.strip() for g in gates),
            'Human-only combat acceptance gates cannot be erased.')
    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list) and len(rows) == len(REQUIRED_WORKFLOWS)
            and all(isinstance(row, dict) for row in rows), 'Incomplete workflow evidence.')
    require({row.get('name') for row in rows} == REQUIRED_WORKFLOWS,
            'Required combat workflows are missing or duplicated.')
    require(all(type(row.get('runId')) is int and row['runId'] > 0
                and row.get('headSha') == baseline and row.get('conclusion') == 'success' for row in rows),
            'Every combat workflow must succeed on the exact implementation SHA.')
    require(len({row['runId'] for row in rows}) == len(rows), 'Combat workflow run IDs must be unique.')
    return baseline


def api(path: str, token: str) -> dict:
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{path}',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def source_contract() -> None:
    experience_rules = (ROOT / 'client/Scripts/ExperienceRules.cs').read_text(encoding='utf-8')
    experience = (ROOT / 'client/Scripts/GameRoot.Experience.cs').read_text(encoding='utf-8')
    game = (ROOT / 'client/Scripts/GameRoot.cs').read_text(encoding='utf-8')
    mob_controls = (ROOT / 'client/Scripts/GameRoot.MobControls.cs').read_text(encoding='utf-8')
    overlay = (ROOT / 'client/Scripts/CombatReadabilityOverlay.cs').read_text(encoding='utf-8')
    world = (ROOT / 'client/Scripts/WorldView.cs').read_text(encoding='utf-8')
    for token in ('BasicAttackBufferSeconds = .25', 'SelectedTargetGrace = 1.75',
                  'ChooseEngagementTarget', 'TargetProblem', 'creature.Target == self.Id'):
        require(token in experience_rules, 'Combat input/target source contract missing: ' + token)
    for token in ('BasicAttackBuffered', 'ReleaseBasicAttack', 'No short attack route'):
        require(token in experience, 'Basic attack responsiveness contract missing: ' + token)
    require('PlayWeaponImpact(current.Self' not in experience,
            'Selected-target health deltas falsely claim local weapon attribution.')
    for token in ('AbilityBufferSeconds = .35', 'queuedAbilityTargetKind', 'queuedAbilityAim',
                  'replayQueued', 'Selected target is no longer available.'):
        require(token in game, 'Queued ability intent contract missing: ' + token)
    require('QUEUED' in mob_controls, 'Queued basic attack feedback is missing.')
    for token in ('SelectedTargetSummary', 'TargetSummary', ' · NOW'):
        require(token in overlay, 'Combat overlay readability contract missing: ' + token)
    for token in ('TelegraphUrgency(effect, RealmTime)', 'SelectedTargetGrace'):
        require(token in world, 'World combat presentation contract missing: ' + token)


def validate(e: dict) -> int:
    baseline = validate_metadata(e)
    require(latest_implementation_commit() == baseline, 'Combat implementation evidence is stale.')
    git('merge-base', '--is-ancestor', STARTING_MAIN, baseline)
    git('merge-base', '--is-ancestor', baseline, 'HEAD')

    historical = (ROOT / PREVIOUS).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(historical)).encode('ascii') + b'\0' + historical).hexdigest()
    require(actual == PREVIOUS_BLOB, 'Historical character evidence changed instead of being archived verbatim.')

    authored = {p for p in git('diff', '--name-only', STARTING_MAIN, baseline, '--', 'content_src').splitlines() if p}
    require(not authored, 'Combat-feel pass changed authored content: ' + ', '.join(sorted(authored)))
    server = {p for p in git('diff', '--name-only', STARTING_MAIN, baseline, '--', 'src/Kairnfall.Server').splitlines() if p}
    require(not server, 'Combat-feel pass changed server implementation: ' + ', '.join(sorted(server)))
    core = {p for p in git('diff', '--name-only', STARTING_MAIN, baseline, '--', 'src/Kairnfall.Core').splitlines() if p}
    require(core == {'src/Kairnfall.Core/CombatReadability.cs'},
            'Combat-feel pass changed authoritative core outside read-only readability rules: ' + ', '.join(sorted(core)))
    source_contract()

    for relative in CURRENT_DOCS:
        text = (ROOT / relative).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS, TITLE, e.get('statusDate', '')):
            require(bool(marker) and marker in text, relative + ' omits a current combat-evidence marker.')
    verification = (ROOT / CURRENT_DOCS[-1]).read_text(encoding='utf-8')
    for row in e['implementationWorkflows']:
        require(str(row['runId']) in verification and row['name'] in verification,
                'Combat verification document omits a workflow.')

    mode = 'offline-structure-only; run CI for remote verification'
    if os.environ.get('CI', '').lower() == 'true':
        token = os.environ.get('GITHUB_TOKEN', '')
        require(bool(token), 'CI requires a read-only Actions token.')
        for row in e['implementationWorkflows']:
            actual_run = api(f'actions/runs/{row["runId"]}', token)
            validate_remote_run(row, actual_run, baseline)
        mode = 'live-actions-verified'

    print(f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; implementation={baseline}; '
          f'workflows={len(REQUIRED_WORKFLOWS)}; basic_buffer={BASIC_BUFFER}; '
          f'ability_buffer={ABILITY_BUFFER}; {mode}')
    return 0
