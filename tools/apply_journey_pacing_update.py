#!/usr/bin/env python3
from pathlib import Path


def replace(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Patch anchor missing in {path}: {old[:120]!r}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")


replace(
    "src/Kairnfall.Core/Mechanics.cs",
    '''    public static double PlayerLevelValue(Character p)\n    {\n        // Character XP is simply the sum of awarded skill XP. Skill challenge rules\n        // already reduce weak/trivial actions, so do not apply a second hidden filter.\n        long total=Total(p);\n        double equivalent=BeginnerProgression.OverallEquivalentXp(total);\n        double ratio=Math.Clamp(equivalent/(60.0*Threshold(SkillCap)),0,1);\n        double trained=1+199*Math.Pow(ratio,0.30);\n        // Late mastery still approaches the cap continuously.\n        double mastery=Math.Clamp(total/(60.0*Threshold(SkillCap)),0,1);\n        double mastered=1+199*Math.Pow(mastery,1.5);\n        return Math.Clamp(Math.Max(trained,mastered),1,PlayerCap);\n    }\n''',
    '''    public static long PlayerLevelCost(int level)\n    {\n        int current=Math.Clamp(level,1,PlayerCap);\n        if(current>=PlayerCap)return 0;\n        return current switch\n        {\n            <20 => 100L+20L*(current-1),\n            <30 => 550L+75L*(current-20),\n            <40 => 1350L+150L*(current-30),\n            <50 => 3000L+300L*(current-40),\n            <60 => 6500L+600L*(current-50),\n            <80 => 13000L+1000L*(current-60),\n            <100 => 35000L+2500L*(current-80),\n            <125 => 90000L+6000L*(current-100),\n            <150 => 250000L+15000L*(current-125),\n            <175 => 650000L+35000L*(current-150),\n            _ => 1600000L+100000L*(current-175)\n        };\n    }\n    public static long PlayerThreshold(int level)\n    {\n        int target=Math.Clamp(level,1,PlayerCap);\n        long total=0;\n        for(int current=1;current<target;current++)total=checked(total+PlayerLevelCost(current));\n        return total;\n    }\n    public static double PlayerLevelValue(Character p)\n    {\n        // Character XP remains the exact sum of awarded skill XP. The visible level\n        // curve is intentionally easy through 20, then each ten-level band asks for\n        // gradually more practice instead of hiding a single late-game grind wall.\n        long total=Total(p);int low=1,high=PlayerCap;\n        while(low<high){int mid=(low+high+1)/2;if(PlayerThreshold(mid)<=total)low=mid;else high=mid-1;}\n        if(low>=PlayerCap)return PlayerCap;\n        long floor=PlayerThreshold(low),ceiling=PlayerThreshold(low+1);\n        return low+Math.Clamp((total-floor)/(double)Math.Max(1,ceiling-floor),0,1);\n    }\n''')

replace(
    "src/Kairnfall.Core/RealmEconomy.cs",
    '''        Need(Progression.PlayerLevel(p)>=exit.Requirement,"Your overall level is too low for this passage.");\n        CancelTradesFor(p.Id); inputs.Remove(p.Id);\n        p.Zone=exit.Target; p.Position=WorldMap.FindFree(Data.Zone(exit.Target),exit.Arrival);\n''',
    '''        var target=Data.Zone(exit.Target);int currentLevel=Progression.PlayerLevel(p);\n        int required=JourneyProgression.ExitRequirement(Data,exit);\n        Need(currentLevel>=required,JourneyProgression.LockMessage(target,currentLevel,required));\n        CancelTradesFor(p.Id); inputs.Remove(p.Id);\n        p.Zone=target.Id; p.Position=WorldMap.FindFree(target,exit.Arrival);\n''')
replace(
    "src/Kairnfall.Core/RealmEconomy.cs",
    '''        Need(source.Kind is "city" or "settlement","Fast travel starts at a settlement waystone.");\n        Near(p,p.Zone,source.Spawn,3);\n''',
    '''        Need(source.Kind is "city" or "settlement","Fast travel starts at a settlement waystone.");\n        int currentLevel=Progression.PlayerLevel(p),required=JourneyProgression.EntryRequirement(Data,dest);\n        Need(currentLevel>=required,JourneyProgression.LockMessage(dest,currentLevel,required));\n        Near(p,p.Zone,source.Spawn,3);\n''')

replace(
    "client/Scripts/Maps.cs",
    '''            var at = positions[zone.Id]; Color color = zone.Id == Selected ? Ui.Text : zone.Kind == "city" ? Ui.Gold : new Color("91ae91");\n''',
    '''            var at = positions[zone.Id];int gate=JourneyProgression.EntryRequirement(Data,zone);\n            bool locked=player is not null&&Progression.PlayerLevel(player)<gate;\n            Color color = zone.Id == Selected ? Ui.Text : locked ? Ui.Danger : zone.Kind == "city" ? Ui.Gold : new Color("91ae91");\n''')
replace(
    "client/Scripts/Maps.cs",
    '''            detail.AddChild(Ui.Label(zone.Name + " · " + Ui.Words(zone.Biome) + " · Suggested skill level " + zone.Level, 19, Ui.Gold)); detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));\n            var actions = Ui.Row(detail); actions.AddChild(Ui.Button("Mark route", () => MarkDestination(zone.Id, zone.Spawn)));\n            bool canTravel = Snapshot.Self.Waypoints.Contains(zone.Id) && zone.Id != Snapshot.Self.Zone;\n            actions.AddChild(Ui.Button("Waystone travel · 20 gold", () => Send("travel", zone.Id), !canTravel));\n            detail.AddChild(Ui.Label("Fast travel starts beside a discovered settlement waystone. Hidden regions remain absent until discovered.", 13, Ui.Muted, true));\n''',
    '''            int playerLevel=Progression.PlayerLevel(Snapshot.Self),threat=JourneyProgression.ThreatLevel(Data,zone),entryLevel=JourneyProgression.EntryRequirement(Data,zone);\n            bool locked=playerLevel<entryLevel;\n            detail.AddChild(Ui.Label(zone.Name + " · " + Ui.Words(zone.Biome) + $" · Threat {threat} · Entry {entryLevel}+", 19, locked?Ui.Danger:Ui.Gold));\n            detail.AddChild(Ui.Label(zone.Lore, 14, Ui.Muted, true));\n            if(locked)detail.AddChild(Ui.Label($"LOCKED · Reach character level {entryLevel} ({entryLevel-playerLevel} to go).",13,Ui.Danger,true));\n            var actions = Ui.Row(detail); actions.AddChild(Ui.Button("Mark route", () => MarkDestination(zone.Id, zone.Spawn)));\n            bool canTravel = Snapshot.Self.Waypoints.Contains(zone.Id) && zone.Id != Snapshot.Self.Zone && !locked;\n            actions.AddChild(Ui.Button("Waystone travel · 20 gold", () => Send("travel", zone.Id), !canTravel));\n            detail.AddChild(Ui.Label("Frontiers open five character levels below the area's ordinary-mob threat. Fast travel still requires a discovered settlement waystone.", 13, Ui.Muted, true));\n''')
replace(
    "client/Scripts/Maps.cs",
    '''                if (exit.Requirement > Progression.PlayerLevel(self) || !visited.Add(exit.Target)) continue;\n''',
    '''                if (JourneyProgression.ExitRequirement(Data,exit) > Progression.PlayerLevel(self) || !visited.Add(exit.Target)) continue;\n''')

replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''    private Label overview=null!,details=null!,directions=null!;\n''',
    '''    private Label overview=null!,journey=null!,details=null!,directions=null!;\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''    private string region="";\n    private HuntingPlan plan=null!;\n''',
    '''    private string region="";\n    private int shownLevel=-1;\n    private HuntingPlan plan=null!;\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''        overview=Ui.Label("",15,Ui.Gold,true);AddChild(overview);\n        var body=Ui.Row(this);body.SizeFlagsVertical=SizeFlags.ExpandFill;\n''',
    '''        overview=Ui.Label("",15,Ui.Gold,true);AddChild(overview);\n        journey=Ui.Label("",13,Ui.Text,true);journey.Name="JourneySuggestion";AddChild(journey);\n        var body=Ui.Row(this);body.SizeFlagsVertical=SizeFlags.ExpandFill;\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Square: exit\\nTravel on foot. Q dashes; Tab changes target. Hidden caches are not exposed by this map.",12,Ui.Muted,true));\n''',
    '''        right.AddChild(Ui.Label("Circle: hunting patch · Diamond: boss · Gold square: open exit · Red square: locked frontier\\nTravel on foot. Q dashes; Tab changes target. Hidden caches are not exposed by this map.",12,Ui.Muted,true));\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''        var zone=Data.Zone(self.Zone);\n        if(region!=zone.Id)\n        {\n            region=zone.Id;plan=HuntingGrounds.For(Data,zone);sites.Clear();Ui.Clear(list);\n            overview.Text=zone.Name+" · "+plan.Specialty+"\\n"+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" separate patches";\n''',
    '''        var zone=Data.Zone(self.Zone);int playerLevel=Progression.PlayerLevel(self);\n        if(region!=zone.Id||shownLevel!=playerLevel)\n        {\n            region=zone.Id;shownLevel=playerLevel;plan=HuntingGrounds.For(Data,zone);sites.Clear();Ui.Clear(list);\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''            foreach(var exit in zone.Exits)\n            {\n                var target=Data.Zone(exit.Target);string id=exit.Id;\n                sites[id]=("Exit: "+target.Name,exit.Position,$"{target.Name} · {target.Layer} · Suggested level {target.Level}\\n{target.Lore}");\n                var button=Ui.Button("To "+target.Name,()=>SelectSite(id));button.Name="HuntExit_"+id;button.ClipText=true;list.AddChild(button);\n            }\n            SelectedSite=sites.Keys.FirstOrDefault()??"";map.Zone=zone;map.Plan=plan;\n        }\n        if(sites.TryGetValue(SelectedSite,out var selected))\n''',
    '''            foreach(var exit in zone.Exits)\n            {\n                var target=Data.Zone(exit.Target);string id=exit.Id;int threat=JourneyProgression.ThreatLevel(Data,target);int gate=JourneyProgression.ExitRequirement(Data,exit);bool locked=playerLevel<gate;\n                string status=locked?$"LOCKED · Level {gate}+ · {gate-playerLevel} to go":$"OPEN · Level {gate}+";\n                sites[id]=("Exit: "+target.Name,exit.Position,$"{target.Name} · {target.Layer} · Threat {threat} · {status}\\n{target.Lore}");\n                var button=Ui.Button((locked?"LOCKED · ":"")+"To "+target.Name+" · Lv "+gate+"+",()=>SelectSite(id));button.Name="HuntExit_"+id;button.ClipText=true;button.TooltipText=sites[id].Description;list.AddChild(button);\n            }\n            SelectedSite=sites.Keys.FirstOrDefault()??"";map.Zone=zone;map.Plan=plan;\n        }\n        overview.Text=zone.Name+" · "+plan.Specialty+$"\\nCharacter {playerLevel} · Threat {JourneyProgression.ThreatLevel(Data,zone)} · "+plan.OrdinaryCount+" ordinary spawn slots · "+plan.Patches.Count+" patches";\n        var lead=JourneyProgression.LocalQuest(Data,self);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n        journey.Text=lead is not null?$"NEXT LEAD · {lead.QuestName}\\nTalk to {lead.GiverName} in {zone.Name}."\n            :next is not null?(next.Locked?$"NEXT FRONTIER · {next.ZoneName} · LOCKED at {next.EntryLevel}+ ({next.LevelsNeeded} to go)\\nTrain skills, craft, gather or finish local quests while you prepare."\n                :$"NEXT FRONTIER · {next.ZoneName} · Threat {next.ThreatLevel} · Entry {next.EntryLevel}+ · READY\\nSelect its exit below and follow the route marker.")\n            :activity is not null?$"CHANGE OF PACE · {activity.Name} level {Progression.BaseLevel(self,activity.Id)}\\n{activity.Action}":"Explore, quest, craft and hunt to build your character.";\n        if(sites.TryGetValue(SelectedSite,out var selected))\n''')
replace(
    "client/Scripts/HuntingGuidePanel.cs",
    '''        foreach(var exit in zone.Exits)DrawRect(new Rect2(At(exit.Position)-new Vector2(2,2),new Vector2(5,5)),Ui.Gold);\n''',
    '''        foreach(var exit in zone.Exits)\n        {\n            bool locked=ReadCharacter() is { } self&&Progression.PlayerLevel(self)<JourneyProgression.ExitRequirement(Data,exit);\n            DrawRect(new Rect2(At(exit.Position)-new Vector2(2,2),new Vector2(5,5)),locked?Ui.Danger:Ui.Gold);\n        }\n''')

replace(
    "client/Scripts/GameRoot.Hud.cs",
    '''        foreach (var entry in new[] { ("Bag [I]", "Inventory"), ("Gear [C]", "Character"), ("Skills [K]", "Skills"), ("Arts [B]", "Abilities"), ("Quest [J]", "Quests"), ("Craft [F]", "Crafting"), ("Social [P]", "Social"), ("Menu", "Settings") })\n''',
    '''        foreach (var entry in new[] { ("Bag [I]", "Inventory"), ("Gear [C]", "Character"), ("Skills [K]", "Skills"), ("Arts [B]", "Abilities"), ("Quest [J]", "Quests"), ("Hunt [H]", "Hunting"), ("Craft [F]", "Crafting"), ("Social [P]", "Social"), ("Menu", "Settings") })\n''')
replace(
    "client/Scripts/GameRoot.Hud.cs",
    '''        int overallLevel = Progression.PlayerLevel(self);\n        double overallProgress=Progression.PlayerLevelProgress(self);\n        experiencePacing.Text = overallLevel>=Progression.PlayerCap ? "Character XP · Level 200" : $"Character XP · Level {overallLevel} → {overallLevel+1}";\n        experiencePacing.TooltipText = "Every awarded skill XP point contributes directly to character level.";\n''',
    '''        int overallLevel = Progression.PlayerLevel(self);\n        double overallProgress=Progression.PlayerLevelProgress(self);long characterXp=Progression.Total(self);\n        long nextCharacterXp=overallLevel>=Progression.PlayerCap?characterXp:Progression.PlayerThreshold(overallLevel+1);\n        long remainingCharacterXp=Math.Max(0,nextCharacterXp-characterXp);\n        experiencePacing.Text = overallLevel>=Progression.PlayerCap ? "Character XP · Level 200" : $"Character XP · Level {overallLevel} → {overallLevel+1} · {remainingCharacterXp:N0} XP";\n        experiencePacing.TooltipText = "Every awarded skill XP point contributes directly to character level. Levels 1-20 are deliberately quick; later bands require progressively more XP.";\n''')
replace(
    "client/Scripts/GameRoot.Hud.cs",
    '''        if (tracked.Value is null)\n            objectiveText.Text = zone.Kind == "interior"\n                ? "Speak to the village innkeeper.\\nOutside the Lantern Hearth\\nUse the marked exit to return."\n                : "Speak to the village innkeeper.\\nBy the inn, northwest of the square\\nMove: WASD / arrows · Talk: E";\n        else\n''',
    '''        if (tracked.Value is null)\n        {\n            var lead=JourneyProgression.LocalQuest(Data,self);var next=JourneyProgression.Suggest(Data,self);var activity=JourneyProgression.SuggestedActivity(Data,self);\n            if(lead is not null)objectiveText.Text=$"NEW LEAD · {lead.QuestName}\\nTalk to {lead.GiverName} here.\\nOpen Quest [J] or Hunt [H] for direction.";\n            else if(zone.Kind=="interior"&&zone.Exits.FirstOrDefault() is { } wayOut)\n                objectiveText.Text=$"Return outside\\nExit toward {Data.Zone(wayOut.Target).Name}\\nInteract: E";\n            else if(next is not null&&next.Locked)\n                objectiveText.Text=$"NEXT FRONTIER · {next.ZoneName}\\nUnlocks at Level {next.EntryLevel} · {next.LevelsNeeded} to go\\nTrain {activity?.Name??"skills"}, craft, gather or quest · Hunt [H]";\n            else if(next is not null)\n                objectiveText.Text=$"NEXT FRONTIER · {next.ZoneName}\\nThreat {next.ThreatLevel} · Entry {next.EntryLevel}+ · READY\\nOpen Hunt [H] and select the exit.";\n            else objectiveText.Text=activity is null?"Explore, quest, craft and hunt to advance.":$"BUILD {activity.Name.ToUpperInvariant()} · Level {Progression.BaseLevel(self,activity.Id)}\\n{activity.Action}\\nHunt [H] shows local routes.";\n        }\n        else\n''')

Path("tools/world_probe/JourneyPacingChecks.cs").write_text(r'''using Kairnfall.Core;

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
''',encoding="utf-8")

replace(
    "tools/world_probe/Program.cs",
    '''HuntingDistributionChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''',
    '''HuntingDistributionChecks.Run(catalog,failures);\nJourneyPacingChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''')

print("Journey/pacing patch applied.")
