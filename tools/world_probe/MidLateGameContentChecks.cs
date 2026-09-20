using Kairnfall.Core;

internal static class MidLateGameContentChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check)
        {
            try{check();passed++;Console.WriteLine("PASS MID/LATE CONTENT: "+name);}
            catch(Exception error){failures.Add(name);Console.WriteLine("FAIL MID/LATE CONTENT: "+name+": "+error.Message);}
        }

        // The hunting-route pass also creates two beginner dungeon-kind zones that deliberately reuse
        // existing bosses. Canonical authored boss dungeons are the boss-lore arenas created from DUNGEONS.
        var dungeons=data.Zones.Where(z=>z.Kind=="dungeon"&&z.Boss!=""
            &&string.Equals(z.Lore,data.Mob(z.Boss).Lore,StringComparison.Ordinal))
            .OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();
        var regions=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").OrderBy(z=>z.Level).ThenBy(z=>z.Id,StringComparer.Ordinal).ToArray();

        Test("every authored dungeon has a level-gated repeatable expedition",()=>
        {
            Need(dungeons.Length==20,"Expected exactly 20 authored dungeons.");
            int veteran=0;
            foreach(var zone in dungeons)
            {
                var boss=data.Mob(zone.Boss);
                var quest=data.Quests.SingleOrDefault(q=>q.Id=="delve_"+zone.Id);
                Need(quest is not null,"Missing repeatable expedition for "+zone.Id);
                Need(quest!.Repeatable&&quest.Category=="repeatable",quest.Id+" lost repeatable semantics.");
                Need(quest.MinimumLevel==Math.Max(1,boss.Level-5),quest.Id+" has the wrong character-level gate.");
                Need(quest.Objectives.Any(o=>o.Action=="explore"&&o.Target==zone.Id),quest.Id+" does not require entering the dungeon.");
                Need(quest.Objectives.Any(o=>o.Action=="boss"&&o.Target==boss.Id),quest.Id+" does not require its authored boss.");
                Need(quest.Gold>=100&&quest.Gold<=800,quest.Id+" reward is outside the bounded daily range.");
                if(boss.Level>=50)
                {
                    veteran++;
                    Need(quest.Prerequisite!="",quest.Id+" veteran expedition has no story gate.");
                    Need(quest.Objectives.Any(o=>o.Action=="gather"&&o.Target=="relic_shard"),quest.Id+" lacks the veteran relic-sample objective.");
                }
            }
            Console.WriteLine($"MID/LATE CONTENT METRIC dungeons={dungeons.Length} veteran_expeditions={veteran}");
            Need(veteran>=10,"Too few veteran expeditions.");
        });

        Test("optional dungeon circuits give every dungeon a one-time narrative hook",()=>
        {
            string[] deepways={"drowned_cistern","glasswing_grotto"};
            string[] umbral={"regents_tomb","rime_abbey","cinder_barracks","reef_sanctum"};
            var deep=data.Quest("veteran_deepways_circuit");
            var umb=data.Quest("veteran_umbral_circuit");
            Need(!deep.Repeatable&&deep.Category=="regional"&&deep.MinimumLevel==40&&deep.Prerequisite=="main_18","Deepways circuit gate changed.");
            Need(!umb.Repeatable&&umb.Category=="regional"&&umb.MinimumLevel==50&&umb.Prerequisite=="main_20","Umbral circuit gate changed.");
            foreach(var id in deepways)
            {
                var zone=data.Zone(id);
                Need(deep.Objectives.Any(o=>o.Action=="explore"&&o.Target==id),"Deepways circuit omits "+id);
                Need(deep.Objectives.Any(o=>o.Action=="boss"&&o.Target==zone.Boss),"Deepways circuit omits boss "+zone.Boss);
            }
            foreach(var id in umbral)
            {
                var zone=data.Zone(id);
                Need(umb.Objectives.Any(o=>o.Action=="explore"&&o.Target==id),"Umbral circuit omits "+id);
                Need(umb.Objectives.Any(o=>o.Action=="boss"&&o.Target==zone.Boss),"Umbral circuit omits boss "+zone.Boss);
            }
            var oneTimeDungeonTargets=data.Quests.Where(q=>!q.Repeatable)
                .SelectMany(q=>q.Objectives.Where(o=>o.Action=="explore").Select(o=>o.Target))
                .ToHashSet(StringComparer.Ordinal);
            foreach(var zone in dungeons)Need(oneTimeDungeonTargets.Contains(zone.Id),"Dungeon has no one-time narrative objective: "+zone.Id);
        });

        Test("regional and field work unlock at the same frontier band as their region",()=>
        {
            Need(regions.Length==20,"Expected 20 surface wilderness regions.");
            foreach(var zone in regions)
            {
                int expected=Math.Max(1,zone.Level-5);
                Need(data.Quest("survey_"+zone.Id).MinimumLevel==expected,"Survey level gate mismatch for "+zone.Id);
                Need(data.Quest("field_"+zone.Id).MinimumLevel==expected,"Field-report level gate mismatch for "+zone.Id);
            }
        });

        Test("server enforces expedition level story and daily cooldown gates",()=>
        {
            var quest=data.Quest("delve_prism_observatory");
            var giver=data.Npc(quest.Giver);
            var realm=new RealmEngine(data);
            var p=realm.CreateCharacter("mid-late-content","Expedition Tester","vanguard",new());
            p.Zone=giver.Zone;p.Position=giver.Position;
            var low=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(!low.Ok&&low.Message.Contains("character level",StringComparison.OrdinalIgnoreCase),"Under-level expedition was not rejected by level.");
            // Rejected commands restore RealmState from a deep copy; reacquire the authoritative character before fixture seeding.
            p=realm.Player(p.Id);
            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);
            Need(Progression.PlayerLevel(p)>=quest.MinimumLevel,"Fixture did not reach the expedition level gate.");
            p.CompletedQuests.Add(quest.Prerequisite);
            var accepted=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(accepted.Ok&&p.Quests.ContainsKey(quest.Id),"Eligible expedition could not be accepted: "+accepted.Message);
            var progress=p.Quests[quest.Id];
            progress.Counts=quest.Objectives.Select(o=>o.Count).ToList();progress.Complete=true;
            long before=p.Gold;
            var claimed=realm.Execute(p.Id,new GameCommand{Kind="claim_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(claimed.Ok&&p.Gold==before+quest.Gold,"Expedition reward was not claimed exactly.");
            double ready=p.Cooldowns.GetValueOrDefault("quest:"+quest.Id);
            Need(ready>realm.State.Time,"Repeatable expedition did not set a daily cooldown.");
            var early=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(!early.Ok,"Expedition could be immediately repeated.");
            realm.State.Time=ready+.01;
            var again=realm.Execute(p.Id,new GameCommand{Kind="accept_quest",Item=quest.Id,Sequence=p.LastAction+1});
            Need(again.Ok,"Expedition did not reopen after its cooldown: "+again.Message);
        });

        Test("journey guidance can surface ready repeatables after one-time work is exhausted",()=>
        {
            var quest=data.Quest("delve_prism_observatory");
            var giver=data.Npc(quest.Giver);
            var p=new Character{Id="guidance",Name="Guidance",Class="vanguard",Zone=giver.Zone};
            p.SkillXp["exploration"]=Progression.PlayerThreshold(quest.MinimumLevel);
            foreach(var oneTime in data.Quests.Where(q=>!q.Repeatable))p.CompletedQuests.Add(oneTime.Id);
            p.CompletedQuests.Add(quest.Id);
            p.Cooldowns["quest:"+quest.Id]=100;
            Need(JourneyProgression.LocalQuest(data,p,50)?.QuestId!=quest.Id,"Guidance ignored the repeatable cooldown.");
            var lead=JourneyProgression.LocalQuest(data,p,101);
            Need(lead is not null,"No ready repeatable was surfaced after one-time work.");
            Need(data.Quest(lead!.QuestId).Repeatable,"Guidance surfaced non-repeatable work after all one-time quests were completed.");
        });

        Console.WriteLine($"MID_LATE_GAME_CONTENT: {passed} groups passed; failures {failures.Count}. Human long-session variety and reward feel remain separate.");
    }
}
