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

    public static JourneyQuestLead? LocalQuest(Catalog data,Character player)
    {
        foreach(var quest in data.Quests
            .Where(q=>!player.Quests.ContainsKey(q.Id)&&!player.CompletedQuests.Contains(q.Id)
                &&(q.Prerequisite==""||player.CompletedQuests.Contains(q.Prerequisite)))
            .OrderBy(q=>q.Category=="main"?0:q.Category=="side"?1:2)
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
