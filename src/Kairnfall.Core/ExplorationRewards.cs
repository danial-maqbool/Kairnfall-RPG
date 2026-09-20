namespace Kairnfall.Core;

public static class ExplorationRewards
{
    public const int CacheClueLandmarks=2;
    public const int RequiredChartSectors=4;
    public const double CacheClueRevealRadius=12;

    public static bool Eligible(ZoneDef zone)=>zone.Kind=="wilderness"&&zone.Layer=="Surface";
    public static IReadOnlyList<BuildingDef> Landmarks(ZoneDef zone)=>zone.Buildings
        .Where(x=>JourneyProgression.IsLandmark(zone,x)).OrderBy(x=>x.Id,StringComparer.Ordinal).ToArray();
    public static string LandmarkKey(ZoneDef zone,BuildingDef landmark)=>zone.Id+":landmark:"+landmark.Id;
    public static string ClueKey(ZoneDef zone)=>"cache_clue:"+zone.Id;
    public static string CacheId(ZoneDef zone)=>zone.Id+"/chest/2";
    public static string CacheOpenedKey(ZoneDef zone)=>"cache_opened:"+zone.Id;
    public static string RewardKey(ZoneDef zone)=>"region_reward:"+zone.Id;
    public static string RewardItemId(ZoneDef zone)=>"keepsake_"+zone.Id;

    public static int LandmarkCount(Character player,ZoneDef zone)=>Landmarks(zone).Count(x=>player.Discoveries.Contains(LandmarkKey(zone,x)));
    public static int SectorCount(Character player,ZoneDef zone)
    {
        int total=0;
        foreach(string discovery in player.Discoveries)
        {
            var parts=discovery.Split(':');
            if(parts.Length==3&&parts[0]==zone.Id&&int.TryParse(parts[1],out _)&&int.TryParse(parts[2],out _)) total++;
        }
        return total;
    }
    public static bool HasClue(Character player,ZoneDef zone)=>player.Discoveries.Contains(ClueKey(zone));
    public static bool CacheDiscovered(Character player,ZoneDef zone)=>player.Discoveries.Contains("secret:"+CacheId(zone));
    public static bool CacheOpened(Character player,ZoneDef zone)=>player.Discoveries.Contains(CacheOpenedKey(zone));
    public static bool Charted(Character player,ZoneDef zone)=>player.Discoveries.Contains("charted:"+zone.Id);
    public static bool Rewarded(Character player,ZoneDef zone)=>player.Discoveries.Contains(RewardKey(zone));
    public static bool MasteryReady(Character player,ZoneDef zone)
        =>Eligible(zone)&&LandmarkCount(player,zone)>=Landmarks(zone).Count&&Charted(player,zone)&&CacheOpened(player,zone);

    public static bool VisibleChest(Character player,Chest chest,Catalog data)
    {
        if(!chest.Hidden)return true;
        if(player.Discoveries.Contains("secret:"+chest.Id))return true;
        var zone=data.Zone(chest.Zone);
        return Eligible(zone)&&chest.Id==CacheId(zone)&&HasClue(player,zone)&&chest.Position.Distance(player.Position)<=CacheClueRevealRadius;
    }

    public static string TryRevealCacheClue(Character player,ZoneDef zone,Catalog data)
    {
        if(!Eligible(zone)||LandmarkCount(player,zone)<CacheClueLandmarks||!player.Discoveries.Add(ClueKey(zone)))return "";
        Progression.Train(player,"treasure_hunting",25,Math.Clamp(zone.Level,1,100),data);
        player.Achievements.Add("trail:"+zone.Id);
        return $"\nCACHE CLUE · Two waymarks align. Search away from the road; the hidden cache becomes visible within {CacheClueRevealRadius:0} tiles.";
    }

    public static string TryGrantRegionalReward(Character player,ZoneDef zone,Catalog data)
    {
        if(!MasteryReady(player,zone)||Rewarded(player,zone))return "";
        var reward=data.Items.FirstOrDefault(x=>x.Id==RewardItemId(zone));
        if(reward is null)return "\nRegional mastery reward is unavailable because its catalog item is missing.";
        bool banked=false;
        if(player.Inventory.Count<Items.InventoryCapacity)
            Items.Add(player.Inventory,Items.Create(data,reward.Id),data);
        else if(player.Bank.Count<Items.BankCapacity)
        {
            Items.Add(player.Bank,Items.Create(data,reward.Id),data,Items.BankCapacity);banked=true;
        }
        else return "\nREGIONAL MASTERY READY · Free one backpack or bank slot, then inspect any waymark again to claim the keepsake.";

        player.Discoveries.Add(RewardKey(zone));
        Progression.Train(player,"exploration",200,Math.Clamp(zone.Level,1,100),data);
        Progression.Train(player,"treasure_hunting",120,Math.Clamp(zone.Level,1,100),data);
        long gold=Math.Min(Items.GoldCap-player.Gold,50L+zone.Level*4L);if(gold>0)Items.Grant(player,gold);
        player.Achievements.Add("explorer:"+zone.Id);
        int mastered=player.Discoveries.Count(x=>x.StartsWith("region_reward:",StringComparison.Ordinal));
        if(mastered>=5)player.Achievements.Add("pathfinder");
        if(mastered>=10)player.Achievements.Add("trailblazer");
        if(mastered>=20)player.Achievements.Add("worldwalker");
        return $"\nREGIONAL MASTERY · {reward.Name} earned{(banked?" and sent to your bank":"")}, plus {gold} gold and bonus Exploration/Treasure Hunting XP.";
    }

    public static string ProgressSummary(Character player,ZoneDef zone)
    {
        if(!Eligible(zone))return "Exploration rewards are tracked in surface wilderness regions.";
        int landmarks=LandmarkCount(player,zone),total=Landmarks(zone).Count,sectors=SectorCount(player,zone);
        string chart=Charted(player,zone)?"charted":$"chart {Math.Min(sectors,RequiredChartSectors)}/{RequiredChartSectors} sectors";
        string cache=CacheOpened(player,zone)?"cache opened":CacheDiscovered(player,zone)?"cache found":HasClue(player,zone)?"cache clue active":"cache unknown";
        string reward=Rewarded(player,zone)?"mastery claimed":MasteryReady(player,zone)?"mastery ready":"mastery pending";
        return $"Exploration · Waymarks {landmarks}/{total} · {chart} · {cache} · {reward}";
    }

    public static string LandmarkLore(ZoneDef zone,BuildingDef landmark)
    {
        string structure=landmark.Style.Replace('_',' ');
        return $"{landmark.Name} · {UiWords(zone.Biome)} {structure}. {zone.Lore}";
    }

    private static string UiWords(string value)=>string.Join(' ',value.Split('_',StringSplitOptions.RemoveEmptyEntries).Select(x=>char.ToUpperInvariant(x[0])+x[1..]));
}
