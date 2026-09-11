using Kairnfall.Core;

internal static class MeaningfulObjectiveChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Test(string name,Action check){try{check();passed++;Console.WriteLine("PASS MEANINGFUL OBJECTIVES: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL MEANINGFUL OBJECTIVES: "+name+": "+e.Message);}}
        var regions=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").OrderBy(z=>z.Id,StringComparer.Ordinal).ToArray();

        Test("Every wilderness region has a non-combat landmark survey chain",()=>
        {
            Need(regions.Length==20,"Expected 20 authored wilderness regions.");
            foreach(var zone in regions)
            {
                var quest=data.Quests.SingleOrDefault(q=>q.Id=="survey_"+zone.Id);Need(quest is not null,"Missing regional survey quest for "+zone.Id);
                Need(quest!.Category=="regional"&&!quest.Repeatable,"Regional survey must be a one-time regional objective.");
                Need(quest.Objectives.Any(o=>o.Action=="explore"&&o.Target==zone.Id),"Survey chain does not require entering "+zone.Id);
                var landmarks=zone.Buildings.Where(b=>JourneyProgression.IsLandmark(zone,b)).ToArray();Need(landmarks.Length==4,"Expected four landmarks in "+zone.Id);
                foreach(var landmark in landmarks)Need(quest.Objectives.Any(o=>o.Action=="survey"&&o.Target==landmark.Id),"Quest omits landmark "+landmark.Id);
                Need(quest.Objectives.All(o=>o.Action is not "kill" and not "boss"),"Regional survey fell back to combat in "+zone.Id);
            }
        });

        Test("Repeatable field reports rotate exploration survey and gathering without kills",()=>
        {
            var reports=data.Quests.Where(q=>q.Id.StartsWith("field_",StringComparison.Ordinal)).ToArray();Need(reports.Length==regions.Length,"Field report count no longer matches regions.");
            foreach(var quest in reports)
            {
                Need(quest.Repeatable&&quest.Category=="repeatable","Field report lost repeatable contract semantics.");
                Need(quest.Objectives.Any(o=>o.Action=="explore"),quest.Id+" lacks exploration.");
                Need(quest.Objectives.Any(o=>o.Action=="survey"),quest.Id+" lacks landmark observation.");
                Need(quest.Objectives.Any(o=>o.Action=="gather"),quest.Id+" lacks local gathering.");
                Need(quest.Objectives.All(o=>o.Action is not "kill" and not "boss"),quest.Id+" still forces mob farming.");
            }
        });

        Test("Landmark interaction points are reachable and guidance names their region",()=>
        {
            foreach(var zone in regions)foreach(var landmark in zone.Buildings.Where(b=>JourneyProgression.IsLandmark(zone,b)))
            {
                var at=JourneyProgression.LandmarkPoint(landmark);Need(WorldMap.Fits(zone,at),$"Blocked landmark interaction {zone.Id}/{landmark.Id}");
                var quest=data.Quest("survey_"+zone.Id);var objective=quest.Objectives.First(o=>o.Action=="survey"&&o.Target==landmark.Id);
                string guidance=JourneyProgression.ObjectiveGuidance(data,quest,objective);Need(guidance.Contains(zone.Name,StringComparison.Ordinal)&&guidance.Contains(landmark.Name,StringComparison.Ordinal),"Guidance does not identify landmark destination.");
            }
        });

        Test("Real server survey grants first-discovery XP and always advances accepted survey work",()=>
        {
            var zone=regions.OrderBy(z=>z.Level).First();var landmark=zone.Buildings.First(b=>JourneyProgression.IsLandmark(zone,b));var quest=data.Quest("survey_"+zone.Id);
            int index=quest.Objectives.FindIndex(o=>o.Action=="survey"&&o.Target==landmark.Id);Need(index>=0,"Survey objective missing.");
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("meaningful-objectives","Waymark Tester","vanguard",new());
            p.Zone=zone.Id;p.Position=JourneyProgression.LandmarkPoint(landmark);p.Quests[quest.Id]=new(){Counts=Enumerable.Repeat(0,quest.Objectives.Count).ToList()};
            long before=p.SkillXp["exploration"];
            var first=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=landmark.Id,Sequence=p.LastAction+1});
            Need(first.Ok,"Landmark survey rejected: "+first.Message);Need(p.Quests[quest.Id].Counts[index]==1,"Survey did not advance quest.");
            Need(p.Discoveries.Contains(zone.Id+":landmark:"+landmark.Id),"Landmark discovery was not persisted.");Need(p.SkillXp["exploration"]>before,"First survey granted no Exploration XP.");
            long after=p.SkillXp["exploration"];p.Quests[quest.Id].Counts[index]=0;p.Quests[quest.Id].Complete=false;
            var revisit=realm.Execute(p.Id,new GameCommand{Kind="inspect",Target=landmark.Id,Sequence=p.LastAction+1});
            Need(revisit.Ok&&p.Quests[quest.Id].Counts[index]==1,"Revisit cannot satisfy later/repeatable survey work.");Need(p.SkillXp["exploration"]==after,"Repeated survey farmed first-discovery XP.");
        });

        Test("Regional quests outrank generic side work in journey guidance",()=>
        {
            var ordered=data.Quests.Where(q=>q.Category is "main" or "regional" or "side" or "repeatable").OrderBy(JourneyProgression.QuestPriority).Select(q=>q.Category).Distinct().ToArray();
            Need(Array.IndexOf(ordered,"main")<Array.IndexOf(ordered,"regional"),"Main quests must remain first.");
            Need(Array.IndexOf(ordered,"regional")<Array.IndexOf(ordered,"side"),"Regional direction should precede generic side contracts.");
        });
        Console.WriteLine($"MEANINGFUL OBJECTIVES: {passed} groups passed; total failures {failures.Count}.");
    }
}
