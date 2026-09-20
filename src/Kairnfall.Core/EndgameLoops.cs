namespace Kairnfall.Core;

public readonly record struct ReputationAward(int Added,long BonusGold,string Rank);

public static class EndgameLoops
{
    public const int ContractsPerBoard=3;
    public static readonly string[] Kinds=["elite","gather","craft","dungeon","boss","event"];
    private static readonly (string Faction,string City)[] Boards=
    [
        ("crown","dawnreach"),
        ("forge_clans","emberhold"),
        ("circle","thornhollow"),
        ("wardens","frostgate"),
        ("league","gloamport")
    ];
    public static IReadOnlyList<string> Factions=>Boards.Select(x=>x.Faction).ToArray();
    public static bool IsFaction(string faction)=>Boards.Any(x=>x.Faction==faction);
    public static bool IsContractId(string id)=>id.StartsWith("endgame:",StringComparison.Ordinal);
    public static long RotationDay(double time)=>Math.Max(0,(long)Math.Floor(Math.Max(0,time)/WorldTime.DayLength));
    public static double SecondsUntilRotation(double time)
    {
        double within=Math.Max(0,time)%WorldTime.DayLength;
        return Math.Max(0,WorldTime.DayLength-within);
    }
    private static int FactionIndex(string faction)
    {
        for(int i=0;i<Boards.Length;i++)if(Boards[i].Faction==faction)return i;
        throw new RuleException("Unknown faction contract board.");
    }
    private static int Pick(long seed,int count)
    {
        if(count<=0)throw new InvalidDataException("Task 22 endgame pool is empty.");
        long value=seed%count;if(value<0)value+=count;return (int)value;
    }
    public static string FactionName(string faction)=>faction switch
    {
        "crown"=>"Crown",
        "forge_clans"=>"Forge Clans",
        "circle"=>"Circle",
        "wardens"=>"Wardens",
        "league"=>"League",
        "wayfarers"=>"Wayfarers",
        _=>string.Join(' ',faction.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]))
    };
    public static string RankName(int reputation)=>Math.Clamp(reputation,0,1000) switch
    {
        >=1000=>"Exalted",
        >=750=>"Revered",
        >=500=>"Honored",
        >=250=>"Trusted",
        _=>"Known"
    };
    public static int NextRankThreshold(int reputation)=>Math.Clamp(reputation,0,1000) switch
    {
        <250=>250,<500=>500,<750=>750,<1000=>1000,_=>0
    };
    public static long RankRewardGold(int threshold)=>threshold switch{250=>250,500=>600,750=>1000,1000=>1600,_=>0};
    public static ReputationAward GrantReputation(Character player,string faction,int amount)
    {
        if(string.IsNullOrWhiteSpace(faction)||amount<=0)return new(0,0,RankName(player.Reputation.GetValueOrDefault(faction)));
        int before=Math.Clamp(player.Reputation.GetValueOrDefault(faction),0,1000);
        int after=Math.Min(1000,before+amount);player.Reputation[faction]=after;
        long bonus=0;
        if(IsFaction(faction))
        {
            foreach(var row in new[]{(250,"trusted"),(500,"honored"),(750,"revered"),(1000,"exalted")})
            {
                if(after<row.Item1)continue;
                string achievement=$"faction_{faction}_{row.Item2}";
                if(!player.Achievements.Add(achievement))continue;
                long gold=RankRewardGold(row.Item1);Items.Grant(player,gold);bonus+=gold;
            }
        }
        return new(after-before,bonus,RankName(after));
    }
    public static NpcDef Registrar(Catalog data,string faction)
    {
        string city=Boards.FirstOrDefault(x=>x.Faction==faction).City??"";
        if(city=="")throw new RuleException("Unknown faction contract board.");
        return data.Npcs.FirstOrDefault(x=>x.Zone==city&&x.Faction==faction&&x.Role=="guild_registrar")
            ??throw new InvalidDataException($"Faction {faction} has no guild registrar in {city}.");
    }
    private static ZoneDef HomeRegion(Catalog data,string faction)
    {
        string cityId=Boards.First(x=>x.Faction==faction).City;var city=data.Zone(cityId);
        var linked=city.Exits.Select(x=>data.Zone(x.Target)).Where(x=>x.Kind=="wilderness"&&x.Layer=="Surface")
            .OrderBy(x=>Math.Abs(x.Level-city.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(linked.Length>0)return linked[0];
        return data.Zones.Where(x=>x.Kind=="wilderness"&&x.Layer=="Surface")
            .OrderBy(x=>Math.Abs(x.Level-city.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).First();
    }
    private static MobDef Elite(Catalog data,ZoneDef region,long day,int factionIndex)
    {
        var local=region.Species.Select(data.Mob).Where(x=>x.Elite&&!x.Boss).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        var pool=local.Length>0?local:data.Mobs.Where(x=>x.Elite&&!x.Boss).OrderBy(x=>Math.Abs(x.Level-region.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*7,pool.Length)];
    }
    private static ResourceDef Resource(Catalog data,ZoneDef region,long day,int factionIndex)
    {
        var pool=region.Resources.Where(id=>data.Resources.Any(r=>r.Id==id)).Select(data.Resource)
            .OrderByDescending(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(pool.Length==0)pool=data.Resources.OrderBy(x=>Math.Abs(x.Requirement-region.Level)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*11,pool.Length)];
    }
    private static RecipeDef Recipe(Catalog data,string faction,ZoneDef region,long day,int factionIndex)
    {
        string city=Boards[factionIndex].City;
        var stations=data.Npcs.Where(x=>x.Zone==city&&x.Station!="").Select(x=>x.Station).Append("hand").ToHashSet(StringComparer.Ordinal);
        int target=Math.Max(35,region.Level+10);
        var pool=data.Recipes.Where(x=>stations.Contains(x.Station)&&data.Items.Any(i=>i.Id==x.Output&&i.Type!="quest"&&i.Type!="structure"))
            .OrderBy(x=>Math.Abs(x.Requirement-target)).ThenByDescending(x=>x.Requirement).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        if(pool.Length==0)pool=data.Recipes.OrderBy(x=>Math.Abs(x.Requirement-target)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*13,pool.Length)];
    }
    private static ZoneDef Dungeon(Catalog data,ZoneDef region,long day,int factionIndex,int offset)
    {
        int target=Math.Max(35,region.Level+15);
        var pool=data.Zones.Where(x=>x.Kind=="dungeon"&&x.Boss!="")
            .OrderBy(x=>Math.Abs(x.Level-target)).ThenBy(x=>x.Id,StringComparer.Ordinal).ToArray();
        return pool[Pick(day+factionIndex*17+offset,pool.Length)];
    }
    private static QuestDef Build(Catalog data,long day,string faction,string kind)
    {
        if(day<0||!IsFaction(faction)||!Kinds.Contains(kind,StringComparer.Ordinal))throw new RuleException("Unknown faction contract.");
        int fi=FactionIndex(faction);var registrar=Registrar(data,faction);var region=HomeRegion(data,faction);
        string target;int minimum;int gold;List<ObjectiveDef> objectives;string name;string story;
        switch(kind)
        {
            case "elite":
            {
                var elite=Elite(data,region,day,fi);target=elite.Id;minimum=Math.Clamp(Math.Max(35,elite.Level-3),1,100);gold=180+minimum*7;
                name="Elite Hunt: "+elite.Name;story=$"{FactionName(faction)} scouts have marked a dangerous veteran threat on established roads near {region.Name}.";
                objectives=[new(){Action="kill",Target=elite.Id,Count=2,Description=$"Defeat 2 {elite.Name}."}];break;
            }
            case "gather":
            {
                var resource=Resource(data,region,day,fi);target=resource.Item;var item=data.Item(resource.Item);minimum=Math.Clamp(Math.Max(35,resource.Requirement),1,100);gold=150+minimum*6;
                name="Supply Muster: "+item.Name;story=$"{FactionName(faction)} needs traceable materials gathered from the existing routes around {region.Name}.";
                objectives=[new(){Action="gather",Target=item.Id,Count=8,Description=$"Gather 8 {item.Name}."}];break;
            }
            case "craft":
            {
                var recipe=Recipe(data,faction,region,day,fi);target=recipe.Output;var item=data.Item(recipe.Output);minimum=Math.Clamp(Math.Max(35,recipe.Requirement),1,100);gold=170+minimum*7;
                name="Guild Order: "+item.Name;story=$"The {FactionName(faction)} workshops are issuing a rotating order through their existing {recipe.Station.Replace('_',' ')} services.";
                objectives=[new(){Action="craft",Target=item.Id,Count=Math.Max(1,Math.Min(3,recipe.Quantity==1?2:recipe.Quantity)),Description=$"Craft {Math.Max(1,Math.Min(3,recipe.Quantity==1?2:recipe.Quantity))} {item.Name}."}];break;
            }
            case "dungeon":
            {
                var dungeon=Dungeon(data,region,day,fi,0);target=dungeon.Id;var boss=data.Mob(dungeon.Boss);minimum=Math.Clamp(Math.Max(35,dungeon.Level-5),1,100);gold=240+minimum*8;
                name="Expedition Circuit: "+dungeon.Name;story=$"{FactionName(faction)} is rotating veteran expeditions through established dungeons instead of opening new territory.";
                objectives=[new(){Action="explore",Target=dungeon.Id,Count=1,Description="Enter "+dungeon.Name+"."},new(){Action="boss",Target=boss.Id,Count=1,Description="Defeat "+boss.Name+"."}];break;
            }
            case "boss":
            {
                var dungeon=Dungeon(data,region,day,fi,5);var boss=data.Mob(dungeon.Boss);target=boss.Id;minimum=Math.Clamp(Math.Max(35,boss.Level-5),1,100);gold=260+minimum*9;
                name="Boss Writ: "+boss.Name;story=$"A {FactionName(faction)} writ calls experienced adventurers back to {dungeon.Name} to contain its known guardian.";
                objectives=[new(){Action="boss",Target=boss.Id,Count=1,Description="Defeat "+boss.Name+"."}];break;
            }
            case "event":
                target="public";minimum=Math.Clamp(Math.Max(35,region.Level+10),1,100);gold=220+minimum*7;
                name="Regional Response";story=$"{FactionName(faction)} is assigning veterans to complete one public event anywhere on the established world routes.";
                objectives=[new(){Action="event_complete",Target="*",Count=1,Description="Complete a public world event as an eligible contributor."}];break;
            default:throw new RuleException("Unknown faction contract kind.");
        }
        string id=$"endgame:{day}:{faction}:{kind}:{target}";
        int rep=kind switch{"elite"=>22,"gather"=>18,"craft"=>20,"dungeon"=>28,"boss"=>30,"event"=>24,_=>20};
        return new(){Id=id,Name=name,Giver=registrar.Id,Story=story,Category="endgame",Faction=faction,MinimumLevel=minimum,Objectives=objectives,Gold=gold+rep,Repeatable=true};
    }
    public static QuestDef ForDay(Catalog data,long day,string faction,string kind)=>Build(data,day,faction,kind);
    public static IReadOnlyList<QuestDef> Today(Catalog data,double time,string faction)
    {
        if(!IsFaction(faction))return [];
        long day=RotationDay(time);int start=Pick(day+FactionIndex(faction)*3,Kinds.Length);
        int[] slots=[start,(start+2)%Kinds.Length,(start+3)%Kinds.Length];
        return slots.Select(i=>Build(data,day,faction,Kinds[i])).ToArray();
    }
    public static IReadOnlyList<QuestDef> Today(Catalog data,double time)=>Factions.SelectMany(f=>Today(data,time,f)).ToArray();
    public static QuestDef ResolveQuest(Catalog data,string id)
    {
        if(!IsContractId(id))return data.Quest(id);
        var parts=id.Split(new[]{':'},5,StringSplitOptions.None);
        if(parts.Length!=5||parts[0]!="endgame"||!long.TryParse(parts[1],out long day))throw new RuleException("Unknown faction contract.");
        var expected=Build(data,day,parts[2],parts[3]);
        if(!string.Equals(expected.Id,id,StringComparison.Ordinal))throw new RuleException("Unknown faction contract.");
        return expected;
    }
    public static int ReputationReward(QuestDef quest)
    {
        if(!IsContractId(quest.Id))return 0;
        var parts=quest.Id.Split(new[]{':'},5,StringSplitOptions.None);
        return parts[3] switch{"elite"=>22,"gather"=>18,"craft"=>20,"dungeon"=>28,"boss"=>30,"event"=>24,_=>0};
    }
    public static string ContractKind(QuestDef quest)
    {
        if(!IsContractId(quest.Id))return "";
        var parts=quest.Id.Split(new[]{':'},5,StringSplitOptions.None);return parts.Length==5?parts[3]:"";
    }
    public static void Advance(QuestDef quest,QuestProgress progress,string action,string target,int amount=1)
    {
        if(amount<1)return;
        while(progress.Counts.Count<quest.Objectives.Count)progress.Counts.Add(0);
        for(int i=0;i<quest.Objectives.Count;i++)
        {
            var objective=quest.Objectives[i];
            if(objective.Action==action&&(objective.Target=="*"||objective.Target==target))progress.Counts[i]=Math.Min(objective.Count,progress.Counts[i]+amount);
        }
        progress.Complete=quest.Objectives.Select((objective,i)=>progress.Counts[i]>=objective.Count).All(x=>x);
    }
}
