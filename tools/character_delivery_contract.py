#!/usr/bin/env python3
"""Verify Wayfarer delivery against committed bytes, history and exact-head Actions.

This is repository-side acceptance, never artistic, human usability or release approval.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import urllib.request

from documentation_contract import (ROOT, REPOSITORY, RELEASE_STATUS, TASK22_BLOB,
                                    EXPECTED_UI_MATRIX, require, git,
                                    latest_implementation_commit, validate_remote_run)

WORKSTREAM = 'character-rebuild'
TITLE = 'Wayfarer character replacement'
ACTOR_SOURCE = 'Wayfarer original joint construction'
PACK = 'art/wayfarer/Assets/manifest.json'
PREVIOUS = 'docs/handoff/NEW_PLAYER_EVIDENCE.json'
PREVIOUS_BLOB = 'c998c352e9a04c9d73d64266fb189fd29db233cd'
REQUIRED_WORKFLOWS = frozenset({
    'Transaction security regression', 'Compile Windows client source',
    'Live progression breadth', 'Windows package acceptance',
    'Graphical multiplayer acceptance', 'Load acceptance', 'Build and verify',
    'Task 13 adversarial acceptance', 'Release operations acceptance',
    'Transaction integrity on Windows and Linux', 'New-player journey',
    'Character sprite acceptance', 'Visual acceptance matrix',
    'Windows display and input acceptance', 'Audio acceptance',
})
CURRENT_DOCS = ('HANDOFF.md', 'docs/SESSION_STATUS.md', 'docs/CHARACTER_REBUILD.md',
                'docs/handoff/CHARACTER_VERIFICATION.md')
TEMPORARY_PATHS = (
    'tools/character_rebuild', 'tools/character_rebuild_stage.py',
    '.github/workflows/character-rebuild-stage.yml',
    '.github/workflows/character-rebuild-apply.yml',
    '.github/workflows/character-commit-diagnostic.yml',
    '.github/workflows/character-publish-diagnostic.yml',
    '.github/workflows/2d-humanoid-assets.yml',
)
SOURCES = {'tools/art/characters.py', 'tools/art/character_motion.py',
           'tools/art/wildlife.py', 'tools/art/creature_anatomy.py',
           'tools/art/common.py', 'atelier/forge/pigment.py'}
COUNTS = {'baseSheets': 1245, 'motionSheets': 5500, 'actorSheets': 6745,
          'frameCells': 415040, 'historicalHashesReplaced': 1245,
          'retiredFiles': 1877}


def validate_metadata(e: dict) -> str:
    require(e.get('schema') == 1 and e.get('currentTask') == WORKSTREAM,
            'Current evidence does not describe the character replacement.')
    baseline = e.get('implementationBaseline', '')
    require(isinstance(baseline, str) and re.fullmatch(r'[0-9a-f]{40}', baseline) is not None,
            'Expected an exact implementation SHA.')
    require(e.get('repository') == REPOSITORY and e.get('persistentBranches') == ['main'],
            'Repository or single-main policy drifted.')
    for key in ('repositorySideCharacterRebuildImplemented', 'repositorySideNewPlayerExperienceImplemented',
                'serverAuthoritative', 'oldSavesCompatible', 'temporaryToolingRemoved'):
        require(e.get(key) is True, 'Required delivery boundary is missing: ' + key)
    a = e.get('authorization', {})
    require(a.get('implementationAuthorized') is True, 'Implementation authorization is missing.')
    for key in ('publicationAuthorized', 'deploymentAuthorized', 'productionInfrastructureChanged'):
        require(a.get(key) is False, 'Unauthorized release/infrastructure claim: ' + key)
    require(e.get('releaseStatus') == RELEASE_STATUS, 'Release status drifted.')
    for key in ('publicationReady', 'releasePublished', 'deployed', 'humanArtApproval', 'humanUxApproval'):
        require(e.get(key) is False, 'Automated evidence cannot grant approval: ' + key)
    gates = e.get('humanOnlyGates')
    require(isinstance(gates, list) and gates and all(isinstance(g, str) and g.strip() for g in gates),
            'Human-only release gates cannot be erased.')
    require(type(e.get('newOverworldRegions')) is int and e['newOverworldRegions'] == 0 and
            type(e.get('tutorialRewardsAdded')) is int and e['tutorialRewardsAdded'] == 8,
            'Retained opening reward or world footprint changed.')
    require(e.get('actorRuntimeSource') == ACTOR_SOURCE and type(e.get('actorHistoricalFallbacks')) is int
            and e['actorHistoricalFallbacks'] == 0, 'Active actor source/fallback boundary drifted.')
    require(e.get('uiResolutionMatrix') == EXPECTED_UI_MATRIX, 'UI matrix is incomplete.')
    require(e.get('characterAssetManifest') == PACK and e.get('historicalNewPlayerEvidence') == PREVIOUS
            and e.get('historicalTask22Evidence') == 'docs/handoff/TASK22_EVIDENCE.json',
            'Pack or historical evidence references drifted.')
    actor = e.get('actorEvidence', {})
    for key, count in COUNTS.items():
        require(type(actor.get(key)) is int and actor[key] == count, 'Actor coverage drifted: ' + key)
    require(e.get('nativeAcceptancePlatforms') == ['linux', 'windows'],
            'Both native acceptance platforms must be recorded.')
    rows = e.get('implementationWorkflows', [])
    require(isinstance(rows, list) and len(rows) == len(REQUIRED_WORKFLOWS)
            and all(isinstance(r, dict) for r in rows), 'Incomplete workflow evidence.')
    require({r.get('name') for r in rows} == REQUIRED_WORKFLOWS, 'Missing or duplicated workflow.')
    require(all(type(r.get('runId')) is int and r['runId'] > 0 and r.get('headSha') == baseline
                and r.get('conclusion') == 'success' for r in rows),
            'Every workflow must succeed on the exact implementation SHA.')
    require(len({r['runId'] for r in rows}) == len(rows), 'Run IDs must be unique.')
    return baseline


def safe_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and re.fullmatch(r'[A-Za-z0-9_./-]+', relative) is not None
            and not relative.startswith('/') and all(p not in ('', '.', '..') for p in relative.split('/')),
            'Unsafe manifest path.')
    path = root / relative
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(),
            'Manifest path escapes its root.')
    return path


def validate_pack(e: dict) -> None:
    manifest = json.loads((ROOT / PACK).read_text(encoding='utf-8'))
    require(manifest.get('schema') == 1 and manifest.get('library') == 'wayfarer'
            and manifest.get('artistic_approval') is False, 'Invalid pack identity/approval.')
    require(manifest.get('states') == ['idle', 'walk', 'attack', 'cast', 'hit', 'death']
            and manifest.get('motion_states') == ['interact', 'craft', 'run', 'bow_attack', 'crossbow_attack']
            and manifest.get('frames') == 8 and len(manifest.get('directions', [])) == 4,
            'Animation layout drifted.')
    sources = manifest.get('source_sha256', {})
    require(set(sources) == SOURCES, 'Source fingerprint coverage is incomplete.')
    for relative, digest in sources.items():
        require(hashlib.sha256(safe_path(ROOT, relative).read_bytes()).hexdigest() == digest,
                'Committed renderer/source hash differs: ' + relative)
    entries = manifest.get('assets', [])
    require(len(entries) == COUNTS['actorSheets'], 'Committed sheet count differs.')
    expected = set(); frame_cells = base = motion = 0; pack = (ROOT / PACK).parent
    for entry in entries:
        key = entry['key']; relative = key + '.png'; path = safe_path(pack, relative)
        require(relative not in expected, 'Duplicate atlas key: ' + key); expected.add(relative)
        require(key.split('/')[0] in {'people', 'equipment', 'npcs', 'mobs', 'motions'}, 'Unexpected actor group.')
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == entry['sha256'], 'Atlas bytes differ: ' + key)
        require(data[:8] == b'\x89PNG\r\n\x1a\n' and len(data) > 24, 'Invalid PNG: ' + key)
        width, height = struct.unpack('>II', data[16:24]); states = 1 if key.startswith('motions/') else 6
        require((width, height) == (entry['width'], entry['height']) and width % 8 == 0
                and width // 8 in (64, 128) and height == (width // 8) * 4 * states,
                'Atlas geometry differs: ' + key)
        frame_cells += states * 4 * 8
        if states == 1: motion += 1
        else: base += 1
    require((base, motion, frame_cells) == (COUNTS['baseSheets'], COUNTS['motionSheets'], COUNTS['frameCells']),
            'Base/motion/frame coverage differs.')
    require({p.relative_to(pack).as_posix() for p in pack.rglob('*.png')} == expected,
            'Unexpected or missing committed actor PNGs.')
    retired = json.loads((ROOT / 'art/wayfarer/retired-actors.json').read_text(encoding='utf-8'))
    require(retired.get('history_rewritten') is False and retired.get('save_data_modified') is False,
            'Retirement cannot rewrite history or saves.')
    removed = retired.get('removed_files', [])
    require(len(removed) == COUNTS['retiredFiles'] and len(set(removed)) == len(removed), 'Retirement coverage differs.')
    for name in removed:
        require(name.startswith(('atelier/Assets/', 'atelier/authored/')), 'Unexpected retirement path.')
        require(not safe_path(ROOT, name).exists(), 'Retired actor file reappeared: ' + name)
    previous = retired.get('assets', []); current = {r['key']: r['sha256'] for r in entries}
    require(len(previous) == COUNTS['historicalHashesReplaced'], 'Historical hash coverage differs.')
    for row in previous:
        require(row['key'] in current and current[row['key']] != row['grounded_sha256'],
                'Historical runtime actor survived: ' + row['key'])


def validate_native_jobs(jobs: list[dict]) -> None:
    require(any('ubuntu' in j.get('name', '').lower() and j.get('conclusion') == 'success' for j in jobs)
            and any('windows' in j.get('name', '').lower() and j.get('conclusion') == 'success' for j in jobs),
            'Character acceptance must actually pass both native platform jobs.')
    require(all(j.get('status') == 'completed' and j.get('conclusion') == 'success' for j in jobs),
            'A character matrix job is pending, skipped or failing.')


def api(path: str, token: str) -> dict:
    request = urllib.request.Request(f'https://api.github.com/repos/{REPOSITORY}/{path}',
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def validate(e: dict) -> int:
    baseline = validate_metadata(e)
    require(latest_implementation_commit() == baseline, 'Implementation evidence is stale.')
    git('merge-base', '--is-ancestor', baseline, 'HEAD')
    for path, digest in ((PREVIOUS, PREVIOUS_BLOB), ('docs/handoff/TASK22_EVIDENCE.json', TASK22_BLOB)):
        data = (ROOT / path).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()
        require(actual == digest, 'Historical evidence changed instead of being retained verbatim: ' + path)
    from documentation_contract import TEMPORARY_PATHS as previous_temporary
    for path in (*previous_temporary, *TEMPORARY_PATHS):
        require(not (ROOT / path).exists(), 'Temporary or retired publishing tooling remains: ' + path)
    origin = e.get('startingMain', '')
    require(isinstance(origin, str) and re.fullmatch(r'[0-9a-f]{40}', origin) is not None, 'Missing starting-main SHA.')
    git('merge-base', '--is-ancestor', origin, baseline)
    changed = set(filter(None, git('diff', '--name-only', origin, baseline, '--', 'content_src').splitlines()))
    require(changed == {'content_src/opening_journey.py'}, 'Retained authored-content footprint drifted.')
    validate_pack(e)
    for path in CURRENT_DOCS:
        text = (ROOT / path).read_text(encoding='utf-8')
        for marker in (baseline, 'CURRENT_EVIDENCE.json', RELEASE_STATUS, TITLE, e.get('statusDate', '')):
            require(bool(marker) and marker in text, path + ' omits a current-evidence marker.')
    verification = (ROOT / CURRENT_DOCS[-1]).read_text(encoding='utf-8')
    for row in e['implementationWorkflows']:
        require(str(row['runId']) in verification and row['name'] in verification, 'Verification document omits a workflow.')
    mode = 'offline-structure-only; run CI for remote verification'
    if os.environ.get('CI', '').lower() == 'true':
        token = os.environ.get('GITHUB_TOKEN', '')
        require(bool(token), 'CI requires a read-only Actions token.')
        for row in e['implementationWorkflows']:
            actual = api(f'actions/runs/{row["runId"]}', token)
            validate_remote_run(row, actual, baseline)
            if row['name'] == 'Character sprite acceptance':
                value = api(f'actions/runs/{row["runId"]}/jobs?per_page=100', token)
                require(value.get('total_count') == len(value.get('jobs', [])), 'Truncated native job evidence.')
                validate_native_jobs(value['jobs'])
        mode = 'live-actions-verified'
    print(f'DOCUMENTATION_CONTRACT: task={WORKSTREAM}; implementation={baseline}; '
          f'workflows={len(REQUIRED_WORKFLOWS)}; sheets={COUNTS["actorSheets"]}; {mode}')
    return 0
