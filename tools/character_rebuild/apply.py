#!/usr/bin/env python3
"""Temporary guarded character migration. A failed candidate is never pushed."""
from pathlib import Path
import hashlib, json, os, subprocess, sys
from runtime_upgrade import ROOT,HERE,replace,install


def retire():
    groups={'people','equipment','npcs','mobs','gear_worn'}
    baseline=json.loads((ROOT/'artifacts/character-baseline-assets/manifest.json').read_text())
    historical=json.loads((ROOT/'atelier/Assets/manifest.json').read_text())
    older={e['key']:e for e in historical['assets'] if e['key'].split('/')[0] in groups}
    records=[]
    for entry in baseline['assets']:
        if entry['key'].split('/')[0] not in groups:continue
        records.append({'key':entry['key'],'grounded_sha256':entry['sha256'],
                        'atelier_sha256':older.get(entry['key'],{}).get('sha256')})
    roots=[ROOT/'atelier/Assets'/group for group in groups]
    roots.extend((ROOT/'atelier/authored/humanoid',ROOT/'atelier/authored/humanoid_preview'))
    removed=[]
    for directory in roots:
        if directory.is_symlink():raise RuntimeError('Refusing to retire a symlink: '+str(directory))
        for path in sorted(directory.rglob('*')):
            if path.is_file():
                relative=path.relative_to(ROOT).as_posix()
                tracked=subprocess.run(['git','ls-files','--error-unmatch','--',relative],cwd=ROOT,capture_output=True).returncode==0
                if tracked:removed.append(relative)
                path.unlink()
    target=ROOT/'art/wayfarer';target.mkdir(parents=True,exist_ok=True)
    (target/'retired-actors.json').write_text(json.dumps({'schema':1,
        'prior_runtime':'Grounded-2026','prior_library':'Atelier','baseline_revision':os.environ.get('GITHUB_SHA',''),
        'history_rewritten':False,'save_data_modified':False,'assets':sorted(records,key=lambda e:e['key']),
        'removed_files':sorted(removed)},indent=2)+'\n')
    builder='atelier/build.py'
    replace(builder,"GROUPS = ('terrain', 'props', 'buildings', 'resources', 'chests', 'items', 'structures',\n          'abilities', 'skills', 'people', 'equipment', 'npcs', 'mobs', 'gear',\n          'gear_worn', 'audio')", "GROUPS = ('terrain', 'props', 'buildings', 'resources', 'chests', 'items', 'structures',\n          'abilities', 'skills', 'gear', 'audio')\nRETIRED_ACTOR_GROUPS = frozenset(('people','equipment','npcs','mobs','gear_worn'))")
    replace(builder,'    # Terrain and indexing are independent of game content.',"    if set(groups) & RETIRED_ACTOR_GROUPS:\n        raise ValueError('Atelier actor generation is retired. Use tools/build_game_assets.py and art/wayfarer instead.')\n    # Terrain and indexing are independent of game content.")
    replace(builder,"    group, key, payload = task\n    path = OUT", "    group, key, payload = task\n    if group in RETIRED_ACTOR_GROUPS: raise ValueError('Retired actor renderer: '+group)\n    path = OUT")
    replace(builder,"        group = key.split('/', 1)[0]\n        with Image.open(path) as image:","        group = key.split('/', 1)[0]\n        if group in RETIRED_ACTOR_GROUPS: raise ValueError('Retired actor raster reappeared: '+key)\n        with Image.open(path) as image:")
    replace(builder,'Kairnfall Atelier art library.','Kairnfall Atelier non-actor art library.\n\nActor sprites and authored masters were retired by the Wayfarer migration.\nThey are not generated, indexed, copied or available as a runtime fallback.\nThe original historical source remains recoverable in Git history.\n')
    (ROOT/'.github/workflows/2d-humanoid-assets.yml').unlink()
    for name in ('tools/art/render_2d_humanoid.py','tools/art/assemble_blender_humanoid.py','tools/art/blender_humanoid_batch.py','tools/art/blender_humanoid_workbench.py'):
        path=ROOT/name
        if path.exists():
            path.write_text('#!/usr/bin/env python3\n"""Retired prototype entry point. Do not recreate rejected actor masters."""\nraise SystemExit("This actor prototype is retired. Run python tools/build_game_assets.py for the current Wayfarer source.")\n')
    for name in ('tools/integrate_atelier.py','client/Scripts/PixelPresentation.cs'):
        path=ROOT/name;text=path.read_text();text=text.replace('Grounded-2026','Wayfarer')
        text=text.replace('The Atelier art pack uses the existing item identities and animation grid. Independent gear/gear_worn records do not replace your saved equipment.',
                          'Wayfarer characters preserve your saved appearance and equipment identities. Compatible Atelier world artwork remains separate; retired character sprites are not loaded.')
        path.write_text(text)
    for name in ('docs/ART_DIRECTION.md','atelier/README.md'):
        path=ROOT/name;text=path.read_text()
        prefix='# Current character source: Wayfarer\n\nPlayer bodies, hair, equipment overlays, NPCs and creatures now come only from the new Wayfarer construction in `tools/art/characters.py`, `character_motion.py`, and `wildlife.py`. Committed runtime atlases and source hashes are in `art/wayfarer/Assets`. The earlier actor implementation and counts below are historical, not the active renderer.\n\nBase compatibility remains 64-pixel actors, 128-pixel bosses, four directions and eight frames for six states. Separate one-action atlases add interaction, crafting, running, bow draw/release and crossbow handling. The client keeps legs grounded during upper-body actions. Accepted server cues synchronize public actions without changing rewards, saves or combat authority.\n\nThe rejected actor PNGs and authored masters are deleted from the working tree. Legacy actor publishing is disabled. Git history is retained. Structural and native rendering results are not independent artistic acceptance or release approval.\n\n---\n\n'
        path.write_text(prefix+text)
    print('Retired',len(removed),'tracked actor/master files; retained',len(records),'old runtime hashes for regression checks.',flush=True)


def tighten_runtime():
    replace('src/Kairnfall.Core/ActorPresentation.cs','        if (state < 0 || player.Health <= 0 || !Active.Contains(player.Id)) return;', '''        if (state < 0 || player.Health <= 0 || !Active.Contains(player.Id)) return;
        if (command.Kind == "attack") duration = Math.Clamp(player.Cooldowns.GetValueOrDefault("attack") - State.Time, .25, .95);
        if (command.Kind == "cast" && Data.Abilities.FirstOrDefault(a => a.Id == command.Item) is { } ability)
        {
            if (ability.Kind is "strike" or "interrupt" or "execute" or "charge") { state = 2; duration = .55; }
            else if (ability.Kind == "dash") { state = 8; duration = .3; }
        }''')
    replace('src/Kairnfall.Core/RealmEngine.cs','Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id);','Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id); presentationCues.Remove(id);')
    replace('src/Kairnfall.Core/ReconnectRecovery.cs','        playerTargets.Clear();','        playerTargets.Clear();\n        presentationCues.Clear();')
    # The source validator's catalogue loop calls the record entry, not e.
    replace('tools/validate_game_assets.py','image.height==4*e.get("state_count",6)*size','image.height==4*entry.get("state_count",6)*size')


def main():
    import runtime_upgrade
    runtime_upgrade.apply()
    # Correct the guarded data-only extraction anchor to the inspected describe() call.
    path=HERE/'art_upgrade.py';lines=path.read_text().splitlines();matches=0
    for index,line in enumerate(lines):
        if line.startswith("    replace('tools/art/creature_anatomy.py','    spec = _vary"):
            lines[index]="    replace('tools/art/creature_anatomy.py','    _vary(spec, mob)',\"    _vary(spec, mob)\\n    if not mob.get('boss'):\\n        spec.horn = FAMILIES[mob['family']].horn\")"
            matches+=1
    if matches!=1:raise RuntimeError('The inspected anatomy migration anchor changed.')
    path.write_text('\n'.join(lines)+'\n')
    import art_upgrade
    art_upgrade.apply()
    tighten_runtime()
    retire()
    install('character-acceptance.yml','.github/workflows/grounded-actor-acceptance.yml')
    subprocess.run([sys.executable,'atelier/build.py','--manifest'],cwd=ROOT,check=True)
    print('CHARACTER CANDIDATE APPLIED: no game source has been published by this command.',flush=True)

if __name__=='__main__':main()
