#!/usr/bin/env python3
"""Publish a passing source/art candidate; workflow edits use the authorized integration separately."""
from pathlib import Path
import json
import os
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def run(*command,capture=False):
    return subprocess.run(command,cwd=ROOT,check=True,text=True,capture_output=capture).stdout


def main():
    parent=os.environ['GITHUB_SHA'];repository=os.environ['GITHUB_REPOSITORY']
    current=run('gh','api',f'repos/{repository}/git/ref/heads/main','--jq','.object.sha',capture=True).strip()
    if current!=parent:raise RuntimeError('main moved; refusing to publish a stale character candidate.')
    report=json.loads((ROOT/'artifacts/test-results/character-assets.json').read_text())
    native=json.loads((ROOT/'artifacts/character-candidate/native-result.json').read_text())
    source=json.loads((ROOT/'artifacts/test-results/character-source.json').read_text())
    if not all(v.get('passed') is True for v in (report,native,source)):raise RuntimeError('Candidate evidence is not passing.')
    if run('git','diff','--name-only','--','content_src',capture=True).strip():raise RuntimeError('Character work cannot rewrite the game catalogue.')
    report.update(candidate_parent=parent,candidate_run_id=int(os.environ['GITHUB_RUN_ID']),
                  native_viewports=native['rendered_viewports'],delivery_head_ci='pending exact-head verification',
                  workflow_integration='pending authorized connector commit')
    docs=ROOT/'docs/art/character-rebuild'
    (docs/'integration-report.json').write_text(json.dumps(report,indent=2)+'\n')
    (docs/'native-candidate.json').write_text(json.dumps(native,indent=2)+'\n')
    stage=docs/'stage-report.json';value=json.loads(stage.read_text());value['runtimeIntegrated']=True
    stage.write_text(json.dumps(value,indent=2)+'\n')
    shots=ROOT/'artifacts/character-candidate/screenshots';retained=docs/'native'
    retained.mkdir(parents=True,exist_ok=True)
    samples=['character-remote-interaction.png','character-remote-corpse.png',
             'character-state-0-frame-0.png','character-state-1-frame-3.png',
             'character-state-2-frame-4.png','character-state-3-frame-4.png',
             'character-state-5-frame-7.png','character-state-6-frame-3.png',
             'character-state-7-frame-4.png','character-state-8-frame-3.png',
             'equipment-state-5-frame-7.png','mobs-state-5-frame-7.png']
    for name in samples:
        if not (shots/name).is_file():raise RuntimeError('Required retained native viewport is absent: '+name)
        shutil.copyfile(shots/name,retained/name)
    (ROOT/'docs/CHARACTER_REBUILD.md').write_text(
        '# Wayfarer character replacement\n\n'
        'The new character and creature source, complete runtime atlases, additional action sheets, authority cues and native rendering tests are integrated. '
        'Prior actor PNGs and authored masters are deleted from the working tree; Git history and saves are retained.\n\n'
        'The accepted candidate is recorded in `docs/art/character-rebuild/integration-report.json`. Native viewport samples are retained in `docs/art/character-rebuild/native/`. '
        'Permanent workflow installation and Linux/Windows delivery-head verification remain pending. '
        'Compilation and structural checks do not establish independent artistic approval, ordinary-account play quality or release readiness.\n\n'
        'Rebuild with `python tools/build_content.py`, `python tools/check_character_source.py`, `python tools/build_game_assets.py`, '
        '`python tools/complete_skill_icons.py`, `python tools/validate_character_assets.py`, and `python tools/build_wayfarer_pack.py`. '
        'The pack command compares committed pixels; its `--write` option is an explicit source-authoring operation, not validation.\n')
    for name in ('HANDOFF.md','docs/SESSION_STATUS.md'):
        path=ROOT/name
        path.write_text('## Active workstream: Wayfarer character replacement\n\nCharacter replacement source is integrated; workflow cleanup and delivery-head verification are in progress. '
                       'Read `docs/CHARACTER_REBUILD.md` and `docs/art/character-rebuild/integration-report.json`. '
                       'The previous first-hour evidence below is historical and does not certify the new character implementation.\n\n---\n\n'+path.read_text())
    # GITHUB_TOKEN has contents:write, not workflows:write. Preserve the desired
    # workflow diff as evidence, but never include workflow edits in this commit.
    evidence=ROOT/'artifacts/character-candidate'
    (evidence/'workflow-integration.patch').write_text(run('git','diff','--','.github/workflows',capture=True))
    desired=ROOT/'.github/workflows/character-acceptance.yml'
    if desired.is_file():shutil.copyfile(desired,evidence/'character-acceptance.yml')
    temporary=ROOT/'tools/character_rebuild_stage.py'
    if temporary.exists():temporary.unlink()
    shutil.rmtree(ROOT/'tools/character_rebuild')
    run('git','diff','--check')
    run('git','config','user.name','github-actions[bot]')
    run('git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    allowed=['tools/art','tools/check_character_source.py','tools/build_game_assets.py',
             'tools/integrate_atelier.py','tools/validate_game_assets.py','tools/validate_grounded_actor_assets.py',
             'tools/validate_character_assets.py','tools/build_wayfarer_pack.py','tools/run_character_native.py',
             'tools/character_probe','tools/character_rebuild','tools/character_rebuild_stage.py',
             'client/Scripts/PixelAssets.cs','client/Scripts/SpritePoseRules.cs','client/Scripts/WorldView.cs',
             'client/Scripts/WorldView.CharacterMotion.cs','client/Scripts/WorldView.CharacterMotion.cs.uid',
             'client/Scripts/GameRoot.cs','client/Scripts/PixelPresentation.cs',
             'client/Tests/CharacterPresentationContract.cs','client/Tests/CharacterPresentationContract.cs.uid',
             'client/Tests/CharacterPresentationContract.tscn','src/Kairnfall.Core/ActorPresentation.cs',
             'src/Kairnfall.Core/Models.cs','src/Kairnfall.Core/RealmEngine.cs','src/Kairnfall.Core/ReconnectRecovery.cs',
             'Kairnfall.slnx','art/wayfarer','atelier/Assets','atelier/authored','atelier/build.py',
             'atelier/coverage.json','atelier/README.md','foundry','docs/art/character-rebuild',
             'docs/CHARACTER_REBUILD.md','docs/ART_DIRECTION.md','docs/SESSION_STATUS.md','HANDOFF.md']
    paths=[name for name in allowed if (ROOT/name).exists() or run('git','ls-files','--',name,capture=True).strip()]
    if not paths:raise RuntimeError('No candidate paths to stage.')
    run('git','add','--all','--',*paths)
    changed=run('git','diff','--cached','--name-only',capture=True).splitlines()
    if not any(name.startswith('art/wayfarer/Assets/people/') for name in changed):raise RuntimeError('Runtime actor PNGs were not staged.')
    if not any(name.startswith('atelier/Assets/people/') for name in changed):raise RuntimeError('Old actor removal was not staged.')
    if any(name.startswith(('.github/','.local/','artifacts/','content_src/')) for name in changed):raise RuntimeError('An unauthorized path entered the source-only candidate commit.')
    run('git','diff','--cached','--check')
    run('git','commit','-m','feat(characters): replace legacy sprites, rebuild motions and synchronize public actions')
    revision=run('git','rev-parse','HEAD',capture=True).strip()
    (evidence/'candidate-revision.txt').write_text(revision+'\n')
    run('gh','auth','setup-git')
    run('git','push','origin','HEAD:main')
    (evidence/'published-revision.txt').write_text(revision+'\n')
    print('CHARACTER_RUNTIME_PUBLISHED:',revision,'files:',len(changed),flush=True)

if __name__=='__main__':main()
