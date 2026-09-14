#!/usr/bin/env python3
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{path}: expected exactly one patch anchor, found {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


build = ROOT / "tools/build_content.py"
replace_once(
    build,
    "from content_src import skills, items, abilities, mobs, encounter_variety, boss_uniques, world, profession_depth, exploration_rewards, quests, world_density, presentation, gear_progression, build_defining_loot",
    "from content_src import skills, items, abilities, mobs, encounter_variety, boss_uniques, world, dungeon_depth, profession_depth, exploration_rewards, quests, world_density, presentation, gear_progression, build_defining_loot",
)
replace_once(
    build,
    "for module in [skills,items,abilities,mobs,encounter_variety,boss_uniques,world,profession_depth,exploration_rewards,quests,world_density,presentation,gear_progression,build_defining_loot]: module.build(data)",
    "for module in [skills,items,abilities,mobs,encounter_variety,boss_uniques,world,dungeon_depth,profession_depth,exploration_rewards,quests,world_density,presentation,gear_progression,build_defining_loot]: module.build(data)",
)
replace_once(
    build,
    "    counts['dungeons']=sum(z['kind']=='dungeon' for z in data['zones'])\n",
    "    counts['dungeons']=sum(z['kind']=='dungeon' for z in data['zones'])\n    counts['task21_compact_rooms']=sum(z['id'] in dungeon_depth.ROOM_IDS for z in data['zones'])\n",
)

(ROOT / "content_src/dungeon_depth.py").write_text(dedent(r'''\
"""Task 21: reusable compact encounter wings attached to existing boss dungeons."""

PLANS = {
    'broken_mill': ('Millrace Foreworks', 'Gearhouse Gauntlet'),
    'silken_tollhouse': ('Webbed Toll Cells', 'Silkroot Gallery'),
    'sunken_foundry': ('Flooded Smelter', 'Kiln Access'),
    'glasswing_grotto': ('Shard Descent', 'Prismatic Gallery'),
}
ROOM_IDS = frozenset(name for dungeon in PLANS for name in (dungeon + '_threshold', dungeon + '_gauntlet'))


def point(x, y):
    return {'x': float(x), 'y': float(y)}


def room(ident, name, dungeon, seed, lore):
    return dict(
        id=ident, name=name, biome=dungeon['biome'], level=dungeon['level'], kind='dungeon', layer=dungeon['layer'],
        width=64, height=64, seed=seed, spawn=point(32.5, 32.5), worldX=dungeon['worldX'], worldY=dungeon['worldY'],
        lore=lore, exits=[], buildings=[], species=[], boss='', resources=[])


def exit_row(ident, target, position, arrival, kind='door', requirement=1):
    return dict(id=ident, target=target, position=position, arrival=arrival, kind=kind, requirement=requirement)


def build(data):
    zones = data['zones']
    by_id = {z['id']: z for z in zones}
    mobs = {m['id']: m for m in data['mobs']}
    if ROOM_IDS & set(by_id):
        raise ValueError('Task 21 compact dungeon rooms must be installed once.')

    for index, (dungeon_id, (threshold_name, gauntlet_name)) in enumerate(PLANS.items()):
        dungeon = by_id.get(dungeon_id)
        if dungeon is None or dungeon['kind'] != 'dungeon' or not dungeon['boss']:
            raise ValueError('Task 21 requires canonical boss dungeon ' + dungeon_id)
        incoming = [(z, e) for z in zones for e in z['exits'] if e['target'] == dungeon_id]
        if len(incoming) != 1:
            raise ValueError(f'Task 21 selected dungeon {dungeon_id} must have exactly one pre-existing entrance, found {len(incoming)}.')
        source, source_exit = incoming[0]
        reverse = [e for e in dungeon['exits'] if e['target'] == source['id']]
        if len(reverse) != 1:
            raise ValueError('Task 21 requires one reciprocal entrance for ' + dungeon_id)
        dungeon_exit = reverse[0]
        boss = mobs[dungeon['boss']]
        ordinary = [mobs[x] for x in dungeon['species'] if x in mobs and not mobs[x]['boss'] and not mobs[x]['elite']]
        if len(ordinary) < 2:
            raise ValueError('Task 21 dungeon lacks ordinary encounter templates: ' + dungeon_id)
        local_elites = [m for m in data['mobs'] if m.get('elite') and m['biome'] == dungeon['biome']]
        elite_pool = local_elites or [m for m in data['mobs'] if m.get('elite')]
        elite = min(elite_pool, key=lambda m: (abs(m['level'] - boss['level']), m['id']))

        threshold_id = dungeon_id + '_threshold'
        gauntlet_id = dungeon_id + '_gauntlet'
        threshold = room(
            threshold_id, threshold_name, dungeon, 8800 + index * 41,
            'A compact approach chamber reuses the existing entrance and establishes the dungeon threat before the deeper fight.')
        gauntlet = room(
            gauntlet_id, gauntlet_name, dungeon, 8900 + index * 41,
            'A short elite gauntlet concentrates traversal pressure immediately before the established boss chamber.')
        threshold['species'] = [ordinary[0]['id'], ordinary[1]['id']]
        gauntlet['species'] = [ordinary[-1]['id'], elite['id']]
        threshold['buildings'] = [dict(id=threshold_id + '_ward', name='Broken Threshold Ward', x=28, y=27, width=8, height=5, style='ruin', station='')]
        gauntlet['buildings'] = [dict(id=gauntlet_id + '_marker', name='Bossward Marker', x=28, y=27, width=8, height=5, style='shrine', station='')]

        original_dungeon_arrival = dict(dungeon_exit['arrival'])
        original_requirement = max(1, source_exit['requirement'])
        source_exit['target'] = threshold_id
        source_exit['arrival'] = point(32.5, 58.5)
        dungeon_exit['target'] = gauntlet_id
        dungeon_exit['arrival'] = point(32.5, 5.5)
        threshold['exits'] = [
            exit_row(threshold_id + '_to_' + source['id'], source['id'], point(32.5, 62.5), dict(source_exit['position']), source_exit['kind'], 1),
            exit_row(threshold_id + '_to_' + gauntlet_id, gauntlet_id, point(32.5, 2.5), point(32.5, 58.5), 'door', 1),
        ]
        gauntlet['exits'] = [
            exit_row(gauntlet_id + '_to_' + threshold_id, threshold_id, point(32.5, 62.5), point(32.5, 5.5), 'door', 1),
            exit_row(gauntlet_id + '_to_' + dungeon_id, dungeon_id, point(32.5, 2.5), original_dungeon_arrival, 'door', original_requirement),
        ]
        zones.extend([threshold, gauntlet])
        by_id[threshold_id] = threshold
        by_id[gauntlet_id] = gauntlet
'''), encoding="utf-8")

combat = ROOT / "src/Kairnfall.Core/RealmCombat.cs"
replace_once(
    combat,
    '        mob.Target=""; mob.Statuses.Clear(); State.Telegraphs.RemoveAll(x=>x.Source==mob.Id);\n',
    '        mob.Target=""; mob.Statuses.Clear(); State.Telegraphs.RemoveAll(x=>x.Source==mob.Id);\n        if(def.Boss) ClearBossEncounterArtifacts(mob);\n',
)
replace_once(
    combat,
    '    private void SummonEnemyAdds(Creature mob,MobDef definition,Character target)\n',
    dedent('''\
    private void ClearBossEncounterArtifacts(Creature mob)
    {
        string prefix=mob.Id+"/add/";
        foreach(var id in State.Creatures.Keys.Where(x=>x.StartsWith(prefix,StringComparison.Ordinal)).ToList())
        {
            State.Creatures.Remove(id); creatureMotion.Remove(id);
        }
        State.Telegraphs.RemoveAll(x=>x.Source==mob.Id||x.Source.StartsWith(prefix,StringComparison.Ordinal));
        creatureMotion.Remove(mob.Id);
    }
    private void ResetBossEncounter(Creature mob,MobDef definition)
    {
        ClearBossEncounterArtifacts(mob);
        mob.Health=definition.Health; mob.Position=mob.Home; mob.Target=""; mob.NextAttack=State.Time+.5;
        mob.Phase=0; mob.AttackStep=0; mob.Threat.Clear(); mob.Statuses.Clear(); EconomicDirty=true;
    }

    private void SummonEnemyAdds(Creature mob,MobDef definition,Character target)
'''),
)
replace_once(
    combat,
    '        var zones=live.Select(x=>x.Zone).ToHashSet();\n        var activeCreatures=State.Creatures.Values.Where(x=>zones.Contains(x.Zone)).ToArray();\n',
    dedent('''\
        var zones=live.Select(x=>x.Zone).ToHashSet();
        foreach(var boss in State.Creatures.Values.Where(x=>x.Owner==""&&x.Health>0&&!zones.Contains(x.Zone)&&Data.Mob(x.Template).Boss).ToList())
        {
            var definition=Data.Mob(boss.Template); string prefix=boss.Id+"/add/";
            bool engaged=boss.Health<definition.Health||boss.Target!=""||boss.Threat.Count>0||boss.Phase>0||boss.AttackStep>0
                ||State.Telegraphs.Any(x=>x.Source==boss.Id||x.Source.StartsWith(prefix,StringComparison.Ordinal))
                ||State.Creatures.Keys.Any(x=>x.StartsWith(prefix,StringComparison.Ordinal));
            if(engaged) ResetBossEncounter(boss,definition);
        }
        var activeCreatures=State.Creatures.Values.Where(x=>zones.Contains(x.Zone)).ToArray();
'''),
)
replace_once(
    combat,
    dedent('''\
            if(mob.Position.Distance(mob.Home)>25)
            {
                mob.Target=""; mob.Threat.Clear(); creatureMotion.Remove(mob.Id); MoveCreature(mob,mob.Home,dt,def.Speed*1.3);
                mob.Health=Math.Min(def.Health,mob.Health+def.Health*dt/4); continue;
            }
'''),
    dedent('''\
            if(mob.Position.Distance(mob.Home)>25)
            {
                if(def.Boss) { ResetBossEncounter(mob,def); continue; }
                mob.Target=""; mob.Threat.Clear(); creatureMotion.Remove(mob.Id); MoveCreature(mob,mob.Home,dt,def.Speed*1.3);
                mob.Health=Math.Min(def.Health,mob.Health+def.Health*dt/4); continue;
            }
'''),
)

(ROOT / "tools/world_probe/Task21DungeonChecks.cs").write_text(dedent(r'''\
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task21DungeonChecks
{
    [ModuleInitializer]
    internal static void VerifyTask21Dungeons()
    {
        const string path="content/catalog.json";
        if(!File.Exists(path))throw new InvalidDataException("Task 21 checks require content/catalog.json.");
        var data=Catalog.Load(path);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK21 DUNGEONS: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK21 DUNGEONS: "+name+": "+e.Message);}}
        string[] selected=["broken_mill","silken_tollhouse","sunken_foundry","glasswing_grotto"];

        Check("compact encounter wings deepen existing entrances without overworld growth",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 21 changed the overworld footprint.");
            foreach(string id in selected)
            {
                var boss=data.Zone(id);var threshold=data.Zone(id+"_threshold");var gauntlet=data.Zone(id+"_gauntlet");
                Need(boss.Boss!=""&&data.Mob(boss.Boss).Boss,"Canonical boss identity changed for "+id);
                Need(threshold.Kind=="dungeon"&&gauntlet.Kind=="dungeon"&&threshold.Width==64&&threshold.Height==64&&gauntlet.Width==64&&gauntlet.Height==64,"Compact room dimensions/kind drifted for "+id);
                Need(threshold.Boss==""&&gauntlet.Boss=="","Pre-boss rooms must not duplicate the major boss.");
                Need(gauntlet.Species.Select(data.Mob).Any(m=>m.Elite),"Elite encounter beat missing for "+id);
                Need(threshold.Exits.Any(e=>e.Target==gauntlet.Id)&&gauntlet.Exits.Any(e=>e.Target==boss.Id)&&boss.Exits.Any(e=>e.Target==gauntlet.Id),"Boss is not the final room in the compact chain for "+id);
                Need(data.Zones.Where(z=>z.Exits.Any(e=>e.Target==threshold.Id)).Any(z=>z.Id!=gauntlet.Id),"Existing world entrance no longer reaches compact chain for "+id);
            }
        });

        Check("abandoned and leashed boss encounters clear transient combat state",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task21-abandon","Dungeon Reset Tester","vanguard",new());realm.Active.Add(p.Id);
            var zone=data.Zone("silken_tollhouse");var boss=realm.State.Creatures[zone.Id+"/boss"];var def=data.Mob(boss.Template);
            boss.Health=def.Health*.4;boss.Phase=1;boss.AttackStep=2;boss.Target=p.Id;boss.Threat[p.Id]=50;
            string addId=boss.Id+"/add/check";realm.State.Creatures[addId]=new(){Id=addId,Template=zone.Species[0],Zone=zone.Id,Position=boss.Home,Home=boss.Home,Health=10,Target=p.Id};
            realm.State.Telegraphs.Add(new(){Zone=zone.Id,Source=boss.Id,Position=boss.Home,Shape="circle",Radius=2,Power=10,Resolves=realm.State.Time+5});
            p.Zone="kingsmeadow";p.Position=data.Zone("kingsmeadow").Spawn;realm.Tick(.1);realm.Tick(.1);
            Need(boss.Health==def.Health&&boss.Position==boss.Home&&boss.Phase==0&&boss.AttackStep==0&&boss.Threat.Count==0&&boss.Target=="","Abandoned boss did not reset atomically.");
            Need(!realm.State.Creatures.ContainsKey(addId)&&!realm.State.Telegraphs.Any(t=>t.Source==boss.Id),"Abandoned boss left adds or telegraphs behind.");

            p.Zone=zone.Id;p.Position=boss.Home;boss.Health=def.Health*.5;boss.Phase=1;boss.AttackStep=1;boss.Threat[p.Id]=5;boss.Position=new(boss.Home.X+30,boss.Home.Y);
            realm.Tick(.1);realm.Tick(.1);
            Need(boss.Health==def.Health&&boss.Position==boss.Home&&boss.Phase==0&&boss.AttackStep==0&&boss.Threat.Count==0,"Leashed boss did not use the clean reset path.");
        });

        Check("multiplayer boss kill removes adds and remains exactly-once",()=>
        {
            var realm=new RealmEngine(data);var a=realm.CreateCharacter("task21-a","Boss Tester A","vanguard",new());var b=realm.CreateCharacter("task21-b","Boss Tester B","vanguard",new());
            var zone=data.Zone("broken_mill");var boss=realm.State.Creatures[zone.Id+"/boss"];string addId=boss.Id+"/add/check";
            a.Zone=zone.Id;b.Zone=zone.Id;a.Position=boss.Home;b.Position=boss.Home;realm.Active.Add(a.Id);realm.Active.Add(b.Id);boss.Health=1;boss.Position=boss.Home;boss.Threat[b.Id]=1;
            realm.State.Creatures[addId]=new(){Id=addId,Template=zone.Species[0],Zone=zone.Id,Position=boss.Home,Home=boss.Home,Health=10,Target=a.Id};
            int generation=boss.Generation,piles=realm.Loot.Count,aKills=a.Bestiary.GetValueOrDefault(boss.Template),bKills=b.Bestiary.GetValueOrDefault(boss.Template);
            var command=new GameCommand{Kind="attack",Target=boss.Id,Sequence=a.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};var result=realm.Execute(a.Id,command);Need(result.Ok,result.Message);
            Need(boss.Health==0&&boss.Generation==generation+1,"Boss death did not advance exactly one generation.");
            Need(!realm.State.Creatures.ContainsKey(addId),"Boss death left summoned adds alive.");
            Need(realm.Loot.Count==piles+1,"Boss death did not create exactly one authoritative loot pile.");
            Need(a.Bestiary.GetValueOrDefault(boss.Template)==aKills+1&&b.Bestiary.GetValueOrDefault(boss.Template)==bKills+1,"Both nearby contributors did not receive boss credit.");
            var replay=realm.Execute(a.Id,command);Need(replay.Ok,"Idempotent boss-kill replay lost its receipt.");
            Need(realm.Loot.Count==piles+1&&boss.Generation==generation+1,"Replayed boss kill duplicated loot or completion.");
        });

        Console.WriteLine($"TASK21 DUNGEON DEPTH: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 21 dungeon regression failed: "+string.Join(" | ",failures));
    }
}
'''), encoding="utf-8")

(ROOT / "docs/TASK21_DUNGEON_DEPTH.md").write_text(dedent('''\
# Task 21 — compact dungeon depth

Task 21 deepens four established boss entrances without expanding the overworld. Each selected dungeon now routes through two reusable 64×64 encounter rooms before the unchanged canonical boss arena. The rooms provide ordinary pressure, an elite beat, and environmental landmarks while the original boss ID, quests, loot table, layer, and surface coordinates stay intact.

Selected demonstrations: Broken Mill, Silken Tollhouse, Sunken Foundry, and Glasswing Grotto. This spans early through late progression and proves the structured template can be applied to future dungeons without growing the overworld.

Boss lifecycle is also hardened: death, leash, and abandonment clear boss-owned summoned adds and telegraphs; abandonment/leash resets health, position, phase, attack step, threat, and statuses without generating loot. Normal death still creates exactly one server-authoritative loot pile and the existing request-receipt system prevents duplicate kill rewards.

The 20 established Surface wilderness regions and 2,048,000 Surface wilderness tiles are unchanged. No release, deployment, or publication authorization is implied.
'''), encoding="utf-8")

print("Task 21 source patch applied.")
