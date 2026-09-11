using Kairnfall.Core;

internal static class JourneyPacingChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool value,string text){if(!value)throw new InvalidOperationException(text);}
        void Test(string name,Action action){try{action();passed++;Console.WriteLine("PASS JOURNEY PACING: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL JOURNEY PACING: "+name+": "+e.Message);}}
        Character AtLevel(int target)
        {
            var p=new Character{Class="vanguard"};long remaining=Progression.PlayerThreshold(target);
            foreach(var skill in data.Skills)
            {
                long chunk=Math.Min(remaining,Progression.Threshold(Progression.SkillCap));p.SkillXp[skill.Id]=chunk;remaining-=chunk;
            }
            Need(remaining==0,"Could not seed character XP for level "+target);
            Need(Progression.PlayerLevel(p)==target,"Seeded level mismatch for "+target+": "+Progression.PlayerLevel(p));return p;
        }
        Test("Character XP is easy early and grows every level without a cliff",()=>
        {
            Need(Progression.PlayerThreshold(1)==0,"Level one should start at zero character XP.");
            long previous=0;
            for(int level=1;level<Progression.PlayerCap;level++)
            {
                long cost=Progression.PlayerLevelCost(level);Need(cost>0,"Non-positive level cost at "+level);
                Need(cost>=previous,"Level costs became easier at "+level);previous=cost;
            }
            Need(Progression.PlayerThreshold(20)<=6000,"Levels 1-20 are still too grindy.");
            long early=Progression.PlayerThreshold(20),mid=Progression.PlayerThreshold(30)-early;
            Need(mid>early&&mid<early*3,"The 20-30 band should be a modest step up, not a grind wall.");
            foreach(int level in new[]{1,10,20,30,50,80,100,150,200})_ = AtLevel(level);
        });
        Test("Every frontier gate is exactly five below ordinary-mob threat unless authored stricter",()=>
        {
            int checkedExits=0;
            foreach(var source in data.Zones)foreach(var exit in source.Exits)
            {
                var target=data.Zone(exit.Target);int threat=JourneyProgression.ThreatLevel(data,target);
                int expected=Math.Clamp(Math.Max(exit.Requirement,Math.Max(1,threat-5)),1,Progression.PlayerCap);
                Need(JourneyProgression.ExitRequirement(data,exit)==expected,$"Gate mismatch {source.Id}/{exit.Id}: threat {threat}, expected {expected}");checkedExits++;
            }
            Need(checkedExits>100,"Too few frontiers checked.");
        });
        Test("A real server transition rejects below-level entry and accepts the exact gate",()=>
        {
            var candidate=(from source in data.Zones from exit in source.Exits let gate=JourneyProgression.ExitRequirement(data,exit)
                           where gate>1&&source.Kind!="interior" orderby gate select (source,exit,gate)).First();
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("journey-gate","Gate Walker","vanguard",new());
            p.Zone=candidate.source.Id;p.Position=candidate.exit.Position;
            var low=AtLevel(candidate.gate-1);p.SkillXp=new(low.SkillXp);
            var denied=realm.Execute(p.Id,new GameCommand{Kind="transition",Target=candidate.exit.Id,Sequence=p.LastAction+1});
            Need(!denied.Ok&&p.Zone==candidate.source.Id,"Below-level player crossed a gated frontier.");
            Need(denied.Message.Contains(candidate.gate.ToString(),StringComparison.Ordinal),"Gate failure did not explain the required level.");
            p=realm.Player(p.Id);
            var ready=AtLevel(candidate.gate);p.SkillXp=new(ready.SkillXp);p.Position=candidate.exit.Position;
            var accepted=realm.Execute(p.Id,new GameCommand{Kind="transition",Target=candidate.exit.Id,Sequence=p.LastAction+1});
            Need(accepted.Ok&&p.Zone==candidate.exit.Target,"Exact-level player could not cross the frontier: "+accepted.Message);
        });
        Test("Journey guidance offers a quest, frontier or undertrained activity",()=>
        {
            var p=AtLevel(12);p.Zone="wayfarers_rest";
            var activity=JourneyProgression.SuggestedActivity(data,p);Need(activity is not null&&activity.Action!="","No change-of-pace skill guidance.");
            var lead=JourneyProgression.LocalQuest(data,p);var suggestion=JourneyProgression.Suggest(data,p);
            Need(lead is not null||suggestion is not null||activity is not null,"No next-step guidance exists.");
            if(suggestion is not null)
            {
                Need(data.Zones.Any(z=>z.Id==suggestion.ZoneId),"Suggested frontier does not exist.");
                Need(suggestion.ThreatLevel==JourneyProgression.ThreatLevel(data,data.Zone(suggestion.ZoneId)),"Suggested threat is stale.");
            }
        });
        Console.WriteLine($"JOURNEY PACING: {passed} groups passed; total failures {failures.Count}.");
    }
}
