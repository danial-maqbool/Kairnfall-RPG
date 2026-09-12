namespace Kairnfall.Core;

public sealed record JourneySuggestion(string ZoneId,string ZoneName,int ThreatLevel,int EntryLevel,bool Locked,int LevelsNeeded);
public sealed record JourneyQuestLead(string QuestId,string QuestName,string GiverId,string GiverName,string ZoneId);

/// <summary>Shared authoritative rules for level-gated frontiers and next-step guidance.</summary>
public static class JourneyProgression
{
    public static int ThreatLevel(Catalog data,ZoneDef zone)
    {
        var levels=zone.Species
            .Select(id=>data.Mobs.FirstOrDefault(m=>m.Id==id))
            .Where(m=>m is not null&&!m.Boss&&!m.Elite)
            .Select(m=>m!.Level)
            .OrderBy(x=>x)
            .ToArray();
        if(levels.Length==0)return Math.Clamp(zone.Level,1,100);
        int middle=levels.Length/2;
        int median=levels.Length%2==1?levels[middle]:(levels[middle-1]+levels[middle]+1)/2;
        return Math.Clamp(median,1,100);
    }

    public static int EntryRequirement(Catalog data,ZoneDef zone,int authoredRequirement=1)
        =>Math.Clamp(Math.Max(Math.Max(1,authoredRequirement),ThreatLevel(data,zone)-5),1,Progression.PlayerCap);

    public static int ExitRequirement(Catalog data,ExitDef exit)
        =>EntryRequirement(data,data.Zone(exit.Target),exit.Requirement);

    public static bool CanEnter(Catalog data,Character player,ZoneDef zone,int authoredRequirement=1)
        =>Progression.PlayerLevel(player)>=EntryRequirement(data,zone,authoredRequirement);

    public static string LockMessage(ZoneDef zone,int playerLevel,int requirement)
    {
        int need=Math.Max(0,requirement-playerLevel);
        return need<=0?$"{zone.Name} is open.":$"{zone.Name} opens at character level {requirement}. You are level {playerLevel}; gain {need} more level{(need==1?"":"s")}.";
    }

    public static int QuestPriority(QuestDef quest)=>quest.Category switch
    {
        "main"=>0,"regional"=>1,"side"=>2,"class"=>3,"repeatable"=>4,_=>5
    };

    public static bool IsLandmark(ZoneDef zone,BuildingDef building)
        =>zone.Kind=="wilderness"&&building.Station==""&&building.Style is "ruin" or "shrine" or "camp";

    public static Point LandmarkPoint(BuildingDef building)
        =>new(building.X+building.Width/2+.5,building.Y+building.Height-.5);

    public static string ObjectiveGuidance(Catalog data,QuestDef quest,ObjectiveDef objective,Character? player=null)
    {
        ZoneDef? zone=null;string suffix="";
        if(objective.Action=="survey")
        {
            foreach(var candidate in data.Zones)
            {
                var landmark=candidate.Buildings.FirstOrDefault(x=>x.Id==objective.Target&&IsLandmark(candidate,x));
                if(landmark is null)continue;zone=candidate;suffix="Survey "+landmark.Name+" with Interact [E].";break;
            }
        }
        else if(objective.Action is "explore" or "chart") { zone=data.Zones.FirstOrDefault(x=>x.Id==objective.Target); suffix=objective.Action=="chart"?"Explore four map sectors, then use Record regional chart on Map [M].":"Use Map [M] to mark the route."; }
        else if(objective.Action=="talk"&&data.Npcs.FirstOrDefault(x=>x.Id==objective.Target) is { } npc) { zone=data.Zones.FirstOrDefault(x=>x.Id==npc.Zone); suffix="Look for the gold !/? and use Interact [E]."; }
        else if(objective.Action is "boss" or "kill"&&data.Mobs.FirstOrDefault(x=>x.Id==objective.Target) is { } mob)
        { zone=data.Zones.FirstOrDefault(x=>x.Boss==mob.Id||x.Species.Contains(mob.Id)); suffix=(mob.Boss?"Boss":"Rare/creature")+" targets show a health bar and tactic cue when selected."; }
        else if(objective.Action=="gather"&&data.Resources.FirstOrDefault(x=>x.Item==objective.Target) is { } resource)
        { zone=data.Zones.FirstOrDefault(x=>x.Resources.Contains(resource.Id)); suffix="Select the resource and use Interact [E]; required tools are shown in the action result."; }
        else if(objective.Action=="deliver"&&data.Npcs.FirstOrDefault(x=>x.Id==quest.Giver) is { } giver)
        { zone=data.Zones.FirstOrDefault(x=>x.Id==giver.Zone); suffix="Return to the quest giver with the item in your backpack."; }
        else if(objective.Action=="craft"&&data.Recipes.FirstOrDefault(x=>x.Output==objective.Target) is { } recipe)
        {
            var stationNpc=data.Npcs.FirstOrDefault(x=>x.Station==recipe.Station);
            zone=stationNpc is null?null:data.Zones.FirstOrDefault(x=>x.Id==stationNpc.Zone);
            suffix="Open Crafting [C] near the "+recipe.Station.Replace('_',' ')+"; the panel shows missing ingredients and skill requirements.";
        }
        else if(objective.Action=="socket") return "Open Backpack [I], select the equipped weapon, then insert the starter rune into its open socket.";
        else if(objective.Action=="plant") return "Use the Farming action on clear surface soil; return when the crop is ready to harvest.";
        if(zone is null)return suffix;
        string lead=player?.Zone==zone.Id?"Here in ":"Go to ";
        return lead+zone.Name+(suffix==""?".":" · "+suffix);
    }

    public static JourneyQuestLead? LocalQuest(Catalog data,Character player,double now=0)
    {
        int level=Progression.PlayerLevel(player);
        foreach(var quest in data.Quests
            .Where(q=>!player.Quests.ContainsKey(q.Id)
                &&(q.Repeatable||!player.CompletedQuests.Contains(q.Id))
                &&level>=q.MinimumLevel
                &&(q.Prerequisite==""||player.CompletedQuests.Contains(q.Prerequisite))
                &&(!q.Repeatable||player.Cooldowns.GetValueOrDefault("quest:"+q.Id)<=now))
            .OrderBy(QuestPriority)
            .ThenBy(q=>q.MinimumLevel)
            .ThenBy(q=>q.Id,StringComparer.Ordinal))
        {
            var giver=data.Npc(quest.Giver);
            if(giver.Zone==player.Zone)return new(quest.Id,quest.Name,giver.Id,giver.Name,giver.Zone);
        }
        return null;
    }

    public static SkillDef? SuggestedActivity(Catalog data,Character player)
    {
        string[] variety=["mining","woodcutting","fishing","herbalism","cooking","woodworking","smithing","exploration","farming","hunting"];
        return variety.Where(id=>data.Skills.Any(s=>s.Id==id)).Select(data.Skill)
            .OrderBy(s=>Progression.BaseLevel(player,s.Id))
            .ThenBy(s=>s.Id,StringComparer.Ordinal)
            .FirstOrDefault();
    }

    public static JourneySuggestion? Suggest(Catalog data,Character player)
    {
        var source=data.Zone(player.Zone);int level=Progression.PlayerLevel(player);
        var all=source.Exits.Select(exit=>(Exit:exit,Zone:data.Zone(exit.Target),Gate:ExitRequirement(data,exit)))
            .GroupBy(x=>x.Zone.Id,StringComparer.Ordinal)
            .Select(g=>g.OrderBy(x=>x.Gate).First())
            .ToArray();
        if(all.Length==0)return null;
        var candidates=all.Where(x=>x.Zone.Kind!="interior").ToArray();
        if(candidates.Length==0)candidates=all;
        var ready=candidates.Where(x=>x.Gate<=level&&ThreatLevel(data,x.Zone)>=Math.Max(1,ThreatLevel(data,source)-2))
            .OrderBy(x=>player.Discoveries.Contains(x.Zone.Id)?1:0)
            .ThenBy(x=>Math.Abs(ThreatLevel(data,x.Zone)-(level+5)))
            .ThenByDescending(x=>ThreatLevel(data,x.Zone))
            .FirstOrDefault();
        if(ready.Zone is not null)return new(ready.Zone.Id,ready.Zone.Name,ThreatLevel(data,ready.Zone),ready.Gate,false,0);
        var locked=candidates.Where(x=>x.Gate>level)
            .OrderBy(x=>x.Gate-level)
            .ThenBy(x=>ThreatLevel(data,x.Zone))
            .FirstOrDefault();
        if(locked.Zone is not null)return new(locked.Zone.Id,locked.Zone.Name,ThreatLevel(data,locked.Zone),locked.Gate,true,locked.Gate-level);
        var fallback=candidates.Where(x=>x.Gate<=level)
            .OrderBy(x=>player.Discoveries.Contains(x.Zone.Id)?1:0)
            .ThenBy(x=>Math.Abs(ThreatLevel(data,x.Zone)-level))
            .FirstOrDefault();
        return fallback.Zone is null?null:new(fallback.Zone.Id,fallback.Zone.Name,ThreatLevel(data,fallback.Zone),fallback.Gate,false,0);
    }
}
