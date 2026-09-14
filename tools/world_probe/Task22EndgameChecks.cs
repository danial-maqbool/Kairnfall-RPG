using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task22EndgameChecks
{
    [ModuleInitializer]
    internal static void VerifyTask22Endgame()
    {
        const string path="content/catalog.json";
        if(!File.Exists(path))throw new InvalidDataException("Task 22 checks require content/catalog.json.");
        var data=Catalog.Load(path);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK22 ENDGAME: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK22 ENDGAME: "+name+": "+e.Message);}}
        void MaxLevel(Character p){p.SkillXp["exploration"]=Progression.PlayerThreshold(100);}
        GameCommand Command(Character p,string kind,string target,string? request=null)=>new(){Kind=kind,Target=target,Sequence=p.LastAction+1,RequestId=request??Guid.NewGuid().ToString("N")};

        Check("canonical faction boards rotate all six loop families without expanding the world",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 22 changed the overworld footprint.");
            Need(EndgameLoops.Factions.SequenceEqual(new[]{"crown","forge_clans","circle","wardens","league"}),"Faction boards no longer match the five authored city factions.");
            foreach(string faction in EndgameLoops.Factions)
            {
                var registrar=EndgameLoops.Registrar(data,faction);Need(registrar.Faction==faction&&registrar.Role=="guild_registrar","Faction board is not anchored to its existing registrar.");
                var kinds=new HashSet<string>();
                for(int day=0;day<6;day++)
                {
                    var today=EndgameLoops.Today(data,day*WorldTime.DayLength+1,faction);Need(today.Count==3&&today.Select(q=>q.Id).Distinct().Count()==3,"Daily board must contain exactly three unique contracts.");
                    foreach(var q in today){kinds.Add(EndgameLoops.ContractKind(q));Need(q.Faction==faction&&q.Giver==registrar.Id&&q.MinimumLevel>=35,"Generated contract escaped its faction/endgame gate.");Need(EndgameLoops.ResolveQuest(data,q.Id).Id==q.Id,"Generated contract cannot be deterministically resolved.");}
                }
                Need(kinds.SetEquals(EndgameLoops.Kinds),"Six-day rotation does not cover elite/gather/craft/dungeon/boss/event loops for "+faction);
            }
        });

        Check("all contract objective families use the shared authoritative quest progress semantics",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-families","Loop Auditor","vanguard",new());MaxLevel(p);
            foreach(string kind in EndgameLoops.Kinds)
            {
                var quest=EndgameLoops.ForDay(data,0,"crown",kind);var progress=new QuestProgress{Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};p.Quests[quest.Id]=progress;
                foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);
                Need(progress.Complete,"Contract family did not complete through authoritative objective progress: "+kind);p.Quests.Remove(quest.Id);
            }
        });

        Check("accept and claim are proximity/level gated and replay-safe",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-authority","Faction Auditor","vanguard",new());MaxLevel(p);string faction="crown";var registrar=EndgameLoops.Registrar(data,faction);var quest=EndgameLoops.Today(data,realm.State.Time,faction)[0];
            var accept=Command(p,"endgame_accept",quest.Id);var far=realm.Execute(p.Id,accept);Need(!far.Ok,"Remote faction contract acceptance bypassed registrar proximity.");
            p=realm.Player(p.Id);p.Zone=registrar.Zone;p.Position=registrar.Position;accept=Command(p,"endgame_accept",quest.Id);var accepted=realm.Execute(p.Id,accept);Need(accepted.Ok,accepted.Message);Need(p.Quests.ContainsKey(quest.Id),"Accepted faction contract was not persisted in quest state.");
            var early=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(!early.Ok,"Incomplete faction contract was claimable.");
            p=realm.Player(p.Id);var progress=p.Quests[quest.Id];foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);Need(progress.Complete,"Fixture contract did not complete.");
            long gold=p.Gold;int reputation=p.Reputation.GetValueOrDefault(faction);string request=Guid.NewGuid().ToString("N");var claim=Command(p,"endgame_claim",quest.Id,request);var claimed=realm.Execute(p.Id,claim);Need(claimed.Ok,claimed.Message);
            Need(p.Gold==gold+quest.Gold&&p.Reputation.GetValueOrDefault(faction)==reputation+EndgameLoops.ReputationReward(quest),"Faction claim reward was not exact.");Need(!p.Quests.ContainsKey(quest.Id)&&p.CompletedQuests.Contains(quest.Id),"Faction claim did not atomically retire the active contract.");
            long after=p.Gold;int repAfter=p.Reputation.GetValueOrDefault(faction);var replay=realm.Execute(p.Id,claim);Need(replay.Ok&&p.Gold==after&&p.Reputation.GetValueOrDefault(faction)==repAfter,"Request replay duplicated faction rewards.");
            var second=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(!second.Ok&&p.Gold==after&&p.Reputation.GetValueOrDefault(faction)==repAfter,"Second claim duplicated faction rewards.");
        });

        Check("active contract progress survives save roundtrip and remains resolvable after rotation",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-persist","Persistent Veteran","vanguard",new());MaxLevel(p);var registrar=EndgameLoops.Registrar(data,"circle");p.Zone=registrar.Zone;p.Position=registrar.Position;var quest=EndgameLoops.Today(data,realm.State.Time,"circle")[0];
            Need(realm.Execute(p.Id,Command(p,"endgame_accept",quest.Id)).Ok,"Could not accept persistence fixture contract.");var progress=p.Quests[quest.Id];var first=quest.Objectives[0];EndgameLoops.Advance(quest,progress,first.Action,first.Target=="*"?"fixture":first.Target,Math.Max(1,first.Count-1));
            var loaded=new RealmEngine(data,Wire.Copy(realm.State));var restored=loaded.Player(p.Id);Need(restored.Quests.ContainsKey(quest.Id),"Active faction contract was lost on save roundtrip.");Need(restored.Quests[quest.Id].Counts.SequenceEqual(progress.Counts),"Faction contract progress changed on save roundtrip.");
            loaded.State.Time+=WorldTime.DayLength*2;Need(EndgameLoops.ResolveQuest(data,quest.Id).Id==quest.Id,"Accepted contract became unresolvable after rotation rollover.");loaded.Tick(.1);
        });

        Check("reputation rank milestone gold is idempotent and persisted through the same claim",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task22-rank","Trusted Candidate","vanguard",new());MaxLevel(p);string faction="league";p.Reputation[faction]=240;var registrar=EndgameLoops.Registrar(data,faction);p.Zone=registrar.Zone;p.Position=registrar.Position;
            var quest=EndgameLoops.Today(data,realm.State.Time,faction).First(q=>EndgameLoops.ReputationReward(q)>=18);Need(realm.Execute(p.Id,Command(p,"endgame_accept",quest.Id)).Ok,"Could not accept rank fixture.");var progress=p.Quests[quest.Id];foreach(var objective in quest.Objectives)EndgameLoops.Advance(quest,progress,objective.Action,objective.Target=="*"?"fixture":objective.Target,objective.Count);
            long before=p.Gold;var result=realm.Execute(p.Id,Command(p,"endgame_claim",quest.Id));Need(result.Ok,result.Message);Need(p.Reputation[faction]>=250&&p.Achievements.Contains("faction_league_trusted"),"Trusted rank milestone was not recorded.");Need(p.Gold==before+quest.Gold+EndgameLoops.RankRewardGold(250),"Trusted rank milestone gold was not exact.");
            long after=p.Gold;var award=EndgameLoops.GrantReputation(p,faction,1);Need(award.BonusGold==0&&p.Gold==after,"Reputation update duplicated an already-earned rank reward.");
            var copy=Wire.Copy(realm.State);Need(copy.Characters[p.Id].Achievements.Contains("faction_league_trusted")&&copy.Characters[p.Id].Reputation[faction]==p.Reputation[faction],"Rank milestone did not persist in realm state.");
        });

        Console.WriteLine($"TASK22 ENDGAME LOOPS: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 22 endgame regression failed: "+string.Join(" | ",failures));
    }
}
