#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def edit(path, old, new):
    p=ROOT/path
    text=p.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:100]!r}')
    p.write_text(text.replace(old,new,1),encoding='utf-8')

# Shared landmark rules, quest priority, and objective navigation hints.
edit(Path('src/Kairnfall.Core/JourneyProgression.cs'),
'''    public static JourneyQuestLead? LocalQuest(Catalog data,Character player)\n    {\n''',
'''    public static int QuestPriority(QuestDef quest)=>quest.Category switch\n    {\n        "main"=>0,"regional"=>1,"side"=>2,"class"=>3,"repeatable"=>4,_=>5\n    };\n\n    public static bool IsLandmark(ZoneDef zone,BuildingDef building)\n        =>zone.Kind=="wilderness"&&building.Station==""&&building.Style is "ruin" or "shrine" or "camp";\n\n    public static Point LandmarkPoint(BuildingDef building)\n        =>new(building.X+building.Width/2+.5,building.Y+building.Height-.5);\n\n    public static string ObjectiveGuidance(Catalog data,QuestDef quest,ObjectiveDef objective)\n    {\n        ZoneDef? zone=null;string suffix="";\n        if(objective.Action=="survey")\n        {\n            foreach(var candidate in data.Zones)\n            {\n                var landmark=candidate.Buildings.FirstOrDefault(x=>x.Id==objective.Target&&IsLandmark(candidate,x));\n                if(landmark is null)continue;zone=candidate;suffix="Survey "+landmark.Name+" with Interact [E].";break;\n            }\n        }\n        else if(objective.Action is "explore" or "chart") zone=data.Zones.FirstOrDefault(x=>x.Id==objective.Target);\n        else if(objective.Action=="talk"&&data.Npcs.FirstOrDefault(x=>x.Id==objective.Target) is { } npc) zone=data.Zones.FirstOrDefault(x=>x.Id==npc.Zone);\n        else if(objective.Action is "boss" or "kill"&&data.Mobs.FirstOrDefault(x=>x.Id==objective.Target) is { } mob)\n            zone=data.Zones.FirstOrDefault(x=>x.Boss==mob.Id||x.Species.Contains(mob.Id));\n        else if(objective.Action=="gather"&&data.Resources.FirstOrDefault(x=>x.Item==objective.Target) is { } resource)\n            zone=data.Zones.FirstOrDefault(x=>x.Resources.Contains(resource.Id));\n        else if(objective.Action=="deliver"&&data.Npcs.FirstOrDefault(x=>x.Id==quest.Giver) is { } giver)\n            zone=data.Zones.FirstOrDefault(x=>x.Id==giver.Zone);\n        if(zone is null)return "";\n        return "Go to "+zone.Name+(suffix==""?".":" · "+suffix);\n    }\n\n    public static JourneyQuestLead? LocalQuest(Catalog data,Character player)\n    {\n''')
edit(Path('src/Kairnfall.Core/JourneyProgression.cs'),
'''            .OrderBy(q=>q.Category=="main"?0:q.Category=="side"?1:2)\n''',
'''            .OrderBy(QuestPriority)\n''')

# Server-authoritative landmark survey action.
edit(Path('src/Kairnfall.Core/RealmEconomy.cs'),
'''    private string Transition(Character p,string exitId)\n    {\n''',
'''    private string InspectLandmark(Character p,string id)\n    {\n        var zone=Data.Zone(p.Zone);\n        var landmark=zone.Buildings.FirstOrDefault(x=>x.Id==id&&JourneyProgression.IsLandmark(zone,x))??throw new RuleException("Landmark not found.");\n        Near(p,p.Zone,JourneyProgression.LandmarkPoint(landmark),2.5);\n        bool first=p.Discoveries.Add(zone.Id+":landmark:"+landmark.Id);\n        if(first)Progression.Train(p,"exploration",50,Math.Clamp(zone.Level,1,100),Data);\n        Progress(p,"survey",landmark.Id);\n        return first?$"Surveyed {landmark.Name} in {zone.Name}.":$"Reviewed {landmark.Name} in {zone.Name}.";\n    }\n    private string Transition(Character p,string exitId)\n    {\n''')
edit(Path('src/Kairnfall.Core/RealmEngine.cs'),
'''            case "talk": return Talk(p,c.Target);\n            case "accept_quest": return AcceptQuest(p,c.Item);\n''',
'''            case "talk": return Talk(p,c.Target);\n            case "inspect": return InspectLandmark(p,c.Target);\n            case "accept_quest": return AcceptQuest(p,c.Item);\n''')

# Client interaction support for field landmarks.
edit(Path('client/Scripts/ExperienceRules.cs'),
'''        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot")\n''',
'''        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot" or "landmark")\n''')
edit(Path('client/Scripts/ExperienceRules.cs'),
'''        "npc" => "Talk to", "exit" => "Enter", "node" => "Gather",\n        "chest" => "Open", "loot" => "Pick up", _ => "Use"\n''',
'''        "npc" => "Talk to", "exit" => "Enter", "node" => "Gather",\n        "chest" => "Open", "loot" => "Pick up", "landmark" => "Survey", _ => "Use"\n''')
edit(Path('client/Scripts/GameRoot.cs'),
'''        else if (target.Kind == "exit") Send("transition", target.Id);\n        else if (target.Kind == "chest") Send("chest", target.Id);\n''',
'''        else if (target.Kind == "exit") Send("transition", target.Id);\n        else if (target.Kind == "landmark") Send("inspect", target.Id);\n        else if (target.Kind == "chest") Send("chest", target.Id);\n''')
edit(Path('client/Scripts/WorldView.cs'),
'''        foreach (var building in zone.Buildings)\n        {\n            var at = new Point(building.X + building.Width / 2.0, building.Y + building.Height);\n            if (IsWithinCameraBounds(at, building.Width + building.Height)) visuals.Add(new Visual((float)at.Y, "building", building.Id, at, building));\n        }\n''',
'''        foreach (var building in zone.Buildings)\n        {\n            var at = new Point(building.X + building.Width / 2.0, building.Y + building.Height);\n            if (IsWithinCameraBounds(at, building.Width + building.Height))\n            {\n                visuals.Add(new Visual((float)at.Y, "building", building.Id, at, building));\n                if(JourneyProgression.IsLandmark(zone,building))\n                    interactions.Add(new WorldTarget("landmark",building.Id,building.Name,JourneyProgression.LandmarkPoint(building)));\n            }\n        }\n''')

# Track the most purposeful accepted quest first and show concrete destination hints.
edit(Path('client/Scripts/GameRoot.Hud.cs'),
'''        var tracked = self.Quests.OrderByDescending(x => Data.Quest(x.Key).Category == "main").FirstOrDefault();\n''',
'''        var tracked = self.Quests.OrderBy(x=>JourneyProgression.QuestPriority(Data.Quest(x.Key))).ThenBy(x=>x.Key,StringComparer.Ordinal).FirstOrDefault();\n''')
edit(Path('client/Scripts/GameRoot.Hud.cs'),
'''            objectiveText.Text = quest.Name + "\\n" + (next < 0 ? "Return to " + Data.Npcs.First(x => x.Id == quest.Giver).Name + " to claim the reward."\n                : quest.Objectives[next].Description + "\\n" + tracked.Value.Counts.ElementAtOrDefault(next) + " / " + quest.Objectives[next].Count);\n''',
'''            string guidance=next<0?"":JourneyProgression.ObjectiveGuidance(Data,quest,quest.Objectives[next]);\n            objectiveText.Text = quest.Name + "\\n" + (next < 0 ? "Return to " + Data.Npcs.First(x => x.Id == quest.Giver).Name + " to claim the reward."\n                : quest.Objectives[next].Description + "\\n" + tracked.Value.Counts.ElementAtOrDefault(next) + " / " + quest.Objectives[next].Count + (guidance==""?"":" · "+guidance));\n''')

# Replace kill-centric field reports and add one landmark-driven regional chain per wilderness region.
p=ROOT/'content_src/quests.py'
text=p.read_text(encoding='utf-8')
start=text.index('    # Regional field contracts tie repeatable play to local ecology.\n')
end=text.index('    for i,(dungeon_id,name,parent,layer,biome,boss_id) in enumerate(DUNGEONS[:10]):\n',start)
replacement='''    # Regional waymark chains make every wilderness region a place to learn, not merely a place to farm mobs.\n    settlement_for={parent:ident for ident,name,parent in __import__('content_src.world',fromlist=['SETTLEMENTS']).SETTLEMENTS}\n    landmark_rows=[('watch','Old Watch Post'),('shrine','Roadside Shrine'),('camp','Abandoned Camp'),('mill','Broken Storehouse')]\n    for i,(region_id,region_name,biome,level,lore) in enumerate(REGIONS):\n        home=settlement_for.get(region_id,CITIES[i%len(CITIES)][0])\n        giver=home+'_traveler'\n        objectives=[objective('explore',region_id,1,'Reach '+region_name+'.')]\n        objectives += [objective('survey',region_id+'_'+suffix,1,'Survey '+label+' in '+region_name+'.') for suffix,label in landmark_rows]\n        add(data,'survey_'+region_id,'Waymarks of '+region_name,giver,\n            'The road ledger has names but no reliable landmarks. Walk the region, inspect its four surviving waymarks, and return with a route another traveler could actually follow. '+lore,\n            objectives,'regional',reward='parchment',gold=70+level*4)\n\n    # Repeatable field work now rotates exploration, observation, and gathering instead of defaulting to mob kills.\n    for i,(region_id,region_name,biome,level,lore) in enumerate(REGIONS):\n        home=settlement_for.get(region_id,CITIES[i%len(CITIES)][0])\n        giver=home+'_traveler'\n        zone=next(z for z in data['zones'] if z['id']==region_id)\n        resource_id=next(r for r in zone['resources'] if r not in {'buried_pottery','relic_deposit'})\n        resource=next(r for r in data['resources'] if r['id']==resource_id)\n        suffix,label=landmark_rows[i%len(landmark_rows)]\n        add(data,'field_'+region_id,'Field Report: '+region_name,giver,\n            'Revisit '+region_name+' as a working surveyor: confirm one landmark, collect a local material sample, and update the route without turning the assignment into another extermination order. '+lore,\n            [objective('explore',region_id),objective('survey',region_id+'_'+suffix,1,'Recheck '+label+' in '+region_name+'.'),objective('gather',resource['item'],2,'Gather 2 '+resource['item'].replace('_',' ')+' in '+region_name+'.')],\n            'repeatable',gold=50+level*3,repeatable=True)\n'''
p.write_text(text[:start]+replacement+text[end:],encoding='utf-8')

# Add authoritative regression fixture.
checks=ROOT/'tools/world_probe/MeaningfulObjectiveChecks.cs'
checks.write_text(r'''using Kairnfall.Core;

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
''',encoding='utf-8')

edit(Path('tools/world_probe/Program.cs'),
'''JourneyPacingChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''',
'''JourneyPacingChecks.Run(catalog,failures);\nMeaningfulObjectiveChecks.Run(catalog,failures);\nChallengeProgressionChecks.Run(catalog,failures);\n''')

# Current design record.
(ROOT/'docs/MEANINGFUL_OBJECTIVES.md').write_text('''# Meaningful regional objectives\n\nStatus: implemented as an Area 2 anti-repetition pass.\n\n- Every one of the 20 surface wilderness regions has a one-time `Waymarks` survey chain.\n- Each chain requires reaching the region and surveying its four authored landmarks; it contains no kill/boss objective.\n- Regional landmarks are authoritative world interactions: approach them and press **E** to survey. First discovery grants Exploration XP; later inspections still satisfy accepted repeatable work without farming discovery XP.\n- Repeatable field reports now require **exploration + landmark survey + local gathering** instead of `explore + kill 3 mobs`.\n- Active quest tracking prioritizes main story, then regional direction, then generic side/repeatable work.\n- The HUD resolves objective destinations where possible and names the region/landmark for survey objectives.\n\nThis pass deliberately leaves dedicated dungeon delves and class/combat quests intact: combat remains a supported activity, but regional progression no longer defaults to blind mob farming.\n''',encoding='utf-8')

print('meaningful objectives patch applied')
