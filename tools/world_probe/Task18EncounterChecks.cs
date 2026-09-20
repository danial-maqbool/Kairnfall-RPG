using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task18EncounterChecks
{
    [ModuleInitializer]
    internal static void VerifyTask18Encounters()
    {
        const string catalogPath="content/catalog.json";
        if(!File.Exists(catalogPath))throw new InvalidDataException("Task 18 checks require content/catalog.json.");
        var data=Catalog.Load(catalogPath);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK18 ENCOUNTERS: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK18 ENCOUNTERS: "+name+": "+e.Message);}}

        Check("regional rare slots stay sparse reachable and tied to existing landmarks",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 18 changed the established overworld footprint.");
            foreach(var zone in surface)
            {
                var elites=zone.Species.Select(data.Mob).Where(m=>m.Elite).ToArray();
                Need(elites.Length==1,zone.Id+" must expose exactly one regional elite template.");
                var plan=HuntingGrounds.For(data,zone);var spawn=plan.Spawns.Single(s=>s.Template==elites[0].Id);var patch=plan.Membership[spawn.Id];
                Need(WorldMap.Fits(zone,spawn.Position)&&!HuntingGrounds.Protected(zone,spawn.Position,data),zone.Id+" elite spawn is blocked or protected.");
                Need(patch.Count==1&&patch.Pattern is "rare_patrol" or "rare_ambush" or "champion_patrol" or "champion_ambush",zone.Id+" elite does not have a controlled rare/champion encounter pattern.");
                Need(patch.Name.StartsWith(RareEncounterRules.RankLabel(elites[0])+": ",StringComparison.Ordinal),zone.Id+" elite rank is not readable in hunting guidance.");
                if(zone.Buildings.Count>0)
                {
                    double nearest=zone.Buildings.Min(b=>JourneyProgression.LandmarkPoint(b).Distance(spawn.Position));
                    Need(nearest<=12,zone.Id+" elite does not reuse an existing landmark area.");
                }
            }
        });

        Check("six regional champions add actual mechanics without multiplying elite templates",()=>
        {
            var elites=data.Mobs.Where(m=>m.Elite).ToArray();Need(elites.Length==25,"Existing 25-elite catalogue changed.");
            var champions=elites.Where(RareEncounterRules.IsChampion).ToArray();Need(champions.Length==6,"Expected six champion mini-boss variants.");
            Need(champions.Select(m=>m.Biome).Distinct(StringComparer.Ordinal).Count()==6,"Champions do not span six regional identities.");
            Need(champions.Min(m=>m.Level)<=10&&champions.Max(m=>m.Level)>=70,"Champions do not span early through late progression.");
            foreach(var champion in champions)
            {
                string signature=RareEncounterRules.SignatureAttack(champion);
                Need(signature!=""&&EnemyCombatRules.IsKnownAttack(signature)&&champion.Attacks.Contains(signature,StringComparer.Ordinal),champion.Id+" lacks a real signature mechanic.");
                var creature=new Creature{Template=champion.Id,Health=champion.Health};
                var sequence=Enumerable.Range(0,Math.Max(6,(champion.Attacks.Length+1)*2)).Select(_=>EnemyCombatRules.NextStandardAttack(champion,creature)).ToArray();
                Need(sequence.Contains(signature,StringComparer.Ordinal),champion.Id+" signature mechanic never enters its attack sequence.");
                Need(champion.Name.StartsWith("Champion ",StringComparison.Ordinal),champion.Id+" is not visibly distinguished by name.");
            }
            var traits=elites.Select(EnemyCombatRules.EliteTrait).ToArray();
            Need(traits.All(t=>EnemyCombatRules.EliteTraits.Contains(t,StringComparer.Ordinal)),"An elite lost its established mechanical trait.");
            Need(EnemyCombatRules.EliteTraits.All(t=>traits.Contains(t,StringComparer.Ordinal)),"Task 18 lost an established elite trait family.");
        });

        Check("rare cadence is deterministic controlled and preserves the introductory rare",()=>
        {
            var realm=new RealmEngine(data);
            var starter=realm.State.Creatures["kingsmeadow/rare_hay_golem"];
            Need(starter.Health>0,"The first-hour rare must remain immediately available for required starter progression.");
            foreach(var zone in data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface"))
            {
                var elite=zone.Species.Select(data.Mob).Single(m=>m.Elite);var creature=realm.State.Creatures[zone.Id+"/"+elite.Id];
                if(elite.Id=="rare_hay_golem")continue;
                Need(creature.Health==0&&creature.RespawnAt>realm.State.Time,zone.Id+" optional rare is permanently seeded instead of using a controlled first appearance.");
                double initial=creature.RespawnAt-realm.State.Time;
                Need(initial==RareEncounterRules.InitialSpawnDelay(zone,elite),zone.Id+" first appearance is not deterministic.");
                var window=RareEncounterRules.RespawnWindow(elite);
                Need(window.Minimum>=360,zone.Id+" elite respawn window is still an obvious short farm loop.");
                if(RareEncounterRules.IsChampion(elite))Need(window.Minimum>=600&&RareEncounterRules.RespawnClearRadius(elite)>=14,elite.Id+" champion cadence/reset space is too permissive.");
            }
        });

        Check("multiplayer champion rewards are once per kill and restart safe",()=>
        {
            const string championId="rare_pine_wolf";var definition=data.Mob(championId);
            var zone=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Species.Contains(championId,StringComparer.Ordinal)).OrderBy(z=>z.Id,StringComparer.Ordinal).First();
            var realm=new RealmEngine(data);var first=realm.CreateCharacter("task18-a","Champion Tester A","vanguard",new());var second=realm.CreateCharacter("task18-b","Champion Tester B","vanguard",new());
            var mob=realm.State.Creatures[zone.Id+"/"+championId];mob.Health=1;mob.RespawnAt=0;mob.Position=mob.Home;
            first.Zone=zone.Id;second.Zone=zone.Id;first.Position=mob.Home;second.Position=mob.Home;realm.Active.Add(first.Id);realm.Active.Add(second.Id);mob.Threat[second.Id]=1;
            int generation=mob.Generation,piles=realm.Loot.Count,firstKills=first.Bestiary.GetValueOrDefault(championId),secondKills=second.Bestiary.GetValueOrDefault(championId);
            var command=new GameCommand{Kind="attack",Target=mob.Id,Sequence=first.LastAction+1};var result=realm.Execute(first.Id,command);
            Need(result.Ok,"Authoritative champion attack failed: "+result.Message);first=realm.Player(first.Id);second=realm.Player(second.Id);
            Need(mob.Health==0&&mob.Generation==generation+1,"Champion death did not advance exactly one generation.");
            Need(first.Bestiary.GetValueOrDefault(championId)==firstKills+1&&second.Bestiary.GetValueOrDefault(championId)==secondKills+1,"Both active contributors did not receive authoritative kill credit.");
            Need(realm.Loot.Count==piles+1,"Champion kill did not create exactly one loot pile.");
            var reward=realm.Loot.Values.OrderByDescending(x=>x.Expires).First();Need(reward.Gold>=definition.Gold,"Champion loot does not retain its controlled enhanced gold floor.");
            var replay=realm.Execute(first.Id,command);Need(replay.Ok,"Idempotent kill-command replay did not return its receipt.");
            Need(realm.Loot.Count==piles+1&&mob.Generation==generation+1,"Replayed champion kill duplicated reward or generation.");
            var duplicate=realm.Execute(first.Id,new GameCommand{Kind="attack",Target=mob.Id,Sequence=first.LastAction+1});Need(!duplicate.Ok,"Fresh attack against a dead champion was accepted.");
            Need(realm.Loot.Count==piles+1&&mob.Generation==generation+1,"Rejected duplicate champion attack changed rewards.");

            var savedLoot=Wire.Copy(realm.Loot);realm=new RealmEngine(data,Wire.Copy(realm.State)){Loot=savedLoot};realm.RecoverLegacyLootPositions();first=realm.Player(first.Id);second=realm.Player(second.Id);mob=realm.State.Creatures[mob.Id];
            double expected=RareEncounterRules.RespawnDelay(zone,definition,mob.Generation);
            Need(mob.Health==0&&Math.Abs((mob.RespawnAt-realm.State.Time)-expected)<.001,"Immediate restart did not upgrade the legacy 90-second elite cooldown to the deterministic champion cadence.");
            Need(realm.Loot.Count==piles+1&&first.Bestiary.GetValueOrDefault(championId)==firstKills+1&&second.Bestiary.GetValueOrDefault(championId)==secondKills+1,"Restart changed champion reward/credit state.");
            first.Position=zone.Spawn;second.Position=zone.Spawn;realm.Active.Add(first.Id);realm.Active.Add(second.Id);
            Need(mob.Home.Distance(zone.Spawn)>RareEncounterRules.RespawnClearRadius(definition),"Champion landmark home is too close to the region arrival for safe reset testing.");
            realm.State.Time=mob.RespawnAt+.1;realm.Tick(.1);realm.Tick(.1);
            Need(mob.Health==definition.Health&&mob.Position==mob.Home&&mob.Phase==0&&mob.AttackStep==0&&mob.Threat.Count==0&&mob.Statuses.Count==0,"Champion did not reset cleanly after its persisted cooldown.");
        });

        Console.WriteLine($"TASK18 ENCOUNTER VARIETY: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 18 encounter regression failed: "+string.Join(" | ",failures));
    }
}