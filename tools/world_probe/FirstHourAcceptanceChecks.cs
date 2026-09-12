using System.Runtime.CompilerServices;
using System.Text.Json;
using Kairnfall.Core;

/// <summary>
/// Task 6 automated acceptance support for the fresh-character first hour.
/// This verifies objective reachability/state contracts only; subjective normal-play approval remains manual.
/// </summary>
internal static class FirstHourAcceptanceChecks
{
    [ModuleInitializer]
    internal static void Run()
    {
        string root=Directory.GetCurrentDirectory();
        string catalogPath=File.Exists(Path.Combine(root,"content","catalog.json"))
            ?Path.Combine(root,"content","catalog.json")
            :Path.Combine(root,"client","Data","catalog.json");
        if(!File.Exists(catalogPath)) return;
        var data=JsonSerializer.Deserialize<Catalog>(File.ReadAllText(catalogPath),Wire.Json)
            ?? throw new InvalidDataException("Empty first-hour acceptance catalog.");
        var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action body)
        {
            try{body();passed++;Console.WriteLine("PASS FIRST HOUR ACCEPTANCE: "+name);}
            catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL FIRST HOUR ACCEPTANCE: "+name+": "+e.Message);}
        }

        HashSet<(int X,int Y)> Reachable(ZoneDef zone)
        {
            var reached=new HashSet<(int,int)>();var queue=new Queue<(int,int)>();
            queue.Enqueue(((int)zone.Spawn.X,(int)zone.Spawn.Y));
            while(queue.TryDequeue(out var tile))
            {
                if(tile.Item1<1||tile.Item2<1||tile.Item1>=zone.Width-1||tile.Item2>=zone.Height-1||reached.Contains(tile))continue;
                if(!WorldMap.Fits(zone,new Point(tile.Item1+.5,tile.Item2+.5)))continue;
                reached.Add(tile);
                queue.Enqueue((tile.Item1+1,tile.Item2));queue.Enqueue((tile.Item1-1,tile.Item2));
                queue.Enqueue((tile.Item1,tile.Item2+1));queue.Enqueue((tile.Item1,tile.Item2-1));
            }
            return reached;
        }
        void Reach(ZoneDef zone,HashSet<(int X,int Y)> reached,Point point,string label)
        {
            Need(WorldMap.Fits(zone,point),label+" is not actor-fit walkable.");
            Need(reached.Contains(((int)point.X,(int)point.Y)),label+" is not reachable from "+zone.Name+" spawn.");
        }

        Test("first skill level can precede first character level",()=>
        {
            Need(Progression.Threshold(2)<Progression.PlayerThreshold(2),
                "Skill level 2 must occur before character level 2 or the authored skill -> level guide step is skipped.");
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task6-order","Order Hero","vanguard",new());
            foreach(string id in new[]{"movement","npc","gather","craft","combat"})FirstHourExperience.Mark(p,id);
            string skill=data.Skills.First().Id;p.SkillXp[skill]=Progression.Threshold(2);
            Need(Progression.BaseLevel(p,skill)==2,"Prepared first skill level did not reach level 2.");
            Need(Progression.PlayerLevel(p)==1,"Character level advanced before the first skill-level milestone.");
            Need(FirstHourExperience.Current(data,p)?.Id=="level","Guide did not advance from skill to character level.");
            p.SkillXp[skill]+=Progression.PlayerThreshold(2)-Progression.Total(p);
            Need(Progression.PlayerLevel(p)==2,"First character level is not reachable immediately after the skill milestone.");
            Need(FirstHourExperience.Current(data,p)?.Id=="equipment","Guide did not advance from character level to equipment.");
        });

        Test("starter quest recipe chain is resource-closed and station-satisfiable",()=>
        {
            var quest=data.Quest("main_01");
            var gather=quest.Objectives.Single(x=>x.Action=="gather"&&x.Target=="oak_log");
            var craft=quest.Objectives.Single(x=>x.Action=="craft"&&x.Target=="wooden_handle");
            var plank=data.Recipes.Single(x=>x.Output=="oak_plank"&&x.Requirement==1);
            var handle=data.Recipes.Single(x=>x.Output==craft.Target&&x.Requirement==1);
            int logsPerBatch=plank.Ingredients.GetValueOrDefault("oak_log");
            Need(logsPerBatch>0&&logsPerBatch<=gather.Count,"Starter quest does not gather enough logs for its board conversion.");
            int plankYield=(gather.Count/logsPerBatch)*plank.Quantity;
            Need(plankYield>=handle.Ingredients.GetValueOrDefault("oak_plank"),"Starter log grant cannot satisfy the handle recipe.");
            Need(plank.Station=="sawbench"&&handle.Station=="sawbench","Starter woodworking chain unexpectedly requires multiple stations.");
            Need(data.Npcs.Any(x=>x.Zone=="wayfarers_rest"&&x.Station=="sawbench"),"Wayfarer's Rest has no usable sawbench service.");
            Need(FirstHourExperience.Steps.Single(x=>x.Id=="craft").Guidance.Contains("plank",StringComparison.OrdinalIgnoreCase),
                "First-hour crafting guidance hides the required log-to-plank intermediate step.");
        });

        Test("required starter interactions doors and regional exit are reachable",()=>
        {
            var starter=data.Zone("wayfarers_rest");var reached=Reachable(starter);
            var main=data.Quest("main_01");
            foreach(string npcId in new[]{main.Giver,"wayfarers_rest_blacksmith"})
            {
                var npc=data.Npc(npcId);Reach(starter,reached,npc.Position,"starter NPC "+npc.Id);
            }
            var station=data.Npcs.First(x=>x.Zone==starter.Id&&x.Station=="sawbench");Reach(starter,reached,station.Position,"starter sawbench");
            var interior=starter.Exits.First(x=>data.Zone(x.Target).Kind=="interior");Reach(starter,reached,interior.Position,"first building door");
            var road=starter.Exits.Single(x=>x.Target=="kingsmeadow");Reach(starter,reached,road.Position,"Kingsmeadow road exit");
            Need(JourneyProgression.ExitRequirement(data,road)<=2,"First regional transition is gated above the first-hour level target.");
            var meadow=data.Zone("kingsmeadow");Reach(meadow,Reachable(meadow),road.Arrival,"Kingsmeadow arrival");
        });

        Test("starter rune provides an achievable first equipment improvement",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task6-gear","Gear Hero","vanguard",new());
            string weaponId=p.Equipment["weapon"];
            var weapon=p.Inventory.Single(x=>x.Id==weaponId);var rune=p.Inventory.Single(x=>x.Template=="rune_embers_1");
            Need(weapon.Sockets>weapon.Runes.Count,"Starter weapon no longer has an empty socket.");
            Items.Socket(p,weapon.Id,rune.Id,data);
            Need(weapon.Runes.Count==1&&weapon.Runes[0].Template=="rune_embers_1","Starter rune did not produce a persistent equipment improvement.");
            Need(FirstHourExperience.Completed(data,p,FirstHourExperience.Steps.Single(x=>x.Id=="equipment")),"First-hour equipment milestone does not recognize the socket upgrade.");
        });

        Test("social exposure has a persistent actionable completion path",()=>
        {
            var p=new RealmEngine(data).CreateCharacter("task6-social","Social Hero","vanguard",new());
            FirstHourExperience.ObserveCommand(p,new GameCommand{Kind="party_create"});
            Need(FirstHourExperience.Completed(data,p,FirstHourExperience.Steps.Single(x=>x.Id=="social")),"Party action does not satisfy first-hour social exposure.");
            string panel=File.ReadAllText(Path.Combine(root,"client","Scripts","GameRoot.Social.cs"));
            foreach(string token in new[]{"Party","LFG","Friend"})Need(panel.Contains(token,StringComparison.OrdinalIgnoreCase),"Social panel lost "+token+" access.");
        });

        Test("first rare is reachable in Kingsmeadow and intentionally gated",()=>
        {
            var meadow=data.Zone("kingsmeadow");var mob=data.Mob("rare_hay_golem");var quest=data.Quest("starter_hunt");
            Need(mob.Elite&&!mob.Boss,"First rare is no longer a non-boss elite mini-boss.");
            Need(meadow.Species.Contains(mob.Id),"Kingsmeadow no longer authors the first rare spawn.");
            Need(quest.MinimumLevel==2&&quest.Prerequisite=="main_02","First rare hunt lost its level-2/main-road gate.");
            Need(quest.Objectives.Any(x=>x.Action=="kill"&&x.Target==mob.Id),"First rare hunt does not target the authored mini-boss.");
            var realm=new RealmEngine(data);
            Need(realm.State.Creatures.TryGetValue("kingsmeadow/"+mob.Id,out var rare),"First rare was not seeded into the authoritative world.");
            Reach(meadow,Reachable(meadow),rare!.Position,"first rare spawn");
        });

        Test("restart preserves first-hour progression quest gear and guide position",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task6-save","Restart Hero","vanguard",new());
            foreach(string id in new[]{"movement","npc","gather","craft","combat"})FirstHourExperience.Mark(p,id);
            string skill=data.Skills.First().Id;p.SkillXp[skill]=Progression.PlayerThreshold(2);
            p.Quests["main_01"]=new QuestProgress{Counts=[3,1,0]};
            string weaponId=p.Equipment["weapon"];var rune=p.Inventory.Single(x=>x.Template=="rune_embers_1");Items.Socket(p,weaponId,rune.Id,data);
            var beforeStep=FirstHourExperience.Current(data,p)?.Id;
            string socketedRuneId=p.Inventory.Single(x=>x.Id==weaponId).Runes.Single().Id;
            var loaded=new RealmEngine(data,Wire.Copy(realm.State));var restored=loaded.Player(p.Id);
            Need(restored.Id==p.Id&&restored.Account==p.Account&&restored.Name==p.Name,"Character identity changed across restart.");
            Need(restored.SkillXp[skill]==p.SkillXp[skill]&&Progression.PlayerLevel(restored)==Progression.PlayerLevel(p),"First-hour XP/level changed across restart.");
            Need(restored.Quests["main_01"].Counts.SequenceEqual(new[]{3,1,0}),"Starter quest progress changed across restart.");
            Need(restored.Equipment["weapon"]==weaponId,"Equipped starter weapon identity changed across restart.");
            var restoredWeapon=restored.Inventory.Single(x=>x.Id==weaponId);
            Need(restoredWeapon.Runes.Count==1&&restoredWeapon.Runes[0].Id==socketedRuneId,"Socketed rune identity changed across restart.");
            Need(FirstHourExperience.Current(data,restored)?.Id==beforeStep,"First-hour guidance position changed across restart.");
            Need(restored.Discoveries.SetEquals(p.Discoveries),"First-hour persistent markers changed across restart.");
            Need(Items.Validate(loaded.State,data).Count==0,"Restart produced invalid inventory/equipment state.");
        });

        Console.WriteLine($"FIRST_HOUR_ACCEPTANCE: {passed}/{passed+failures.Count} groups passed. Human normal-play approval remains separate.");
        if(failures.Count>0)throw new InvalidOperationException("First-hour acceptance failures: "+string.Join(" | ",failures));
    }
}
