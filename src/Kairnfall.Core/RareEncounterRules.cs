namespace Kairnfall.Core;

/// <summary>Deterministic rank, cadence and visibility rules for optional regional elite encounters.</summary>
public static class RareEncounterRules
{
    public const double LegacyEliteRespawnCeiling = 91;
    private static readonly Dictionary<string,string> ChampionSignatures = new(StringComparer.Ordinal)
    {
        ["rare_pine_wolf"]="root",
        ["rare_kobold_slinger"]="charge",
        ["rare_fire_beetle"]="field",
        ["rare_ice_elemental"]="ring",
        ["rare_gilded_scarab"]="summon",
        ["rare_arcane_sentinel"]="interruptible",
    };

    public static IReadOnlyCollection<string> Champions => ChampionSignatures.Keys;
    public static bool IsChampion(MobDef definition)=>definition.Elite&&ChampionSignatures.ContainsKey(definition.Id);
    public static string SignatureAttack(MobDef definition)=>ChampionSignatures.GetValueOrDefault(definition.Id)??"";
    public static string RankLabel(MobDef definition)=>definition.Boss?"Boss":IsChampion(definition)?"Champion":definition.Elite?"Rare":"Common";
    public static string HuntingPattern(MobDef definition)
    {
        if(!definition.Elite)return "";
        string prefix=IsChampion(definition)?"champion_":"rare_";
        return prefix+(definition.Ai=="ambusher"?"ambush":"patrol");
    }
    public static double InitialSpawnDelay(ZoneDef zone,MobDef definition)
    {
        if(!definition.Elite||definition.Id=="rare_hay_golem")return 0;
        int hash=StableHash(zone.Id+"|"+definition.Id+"|initial|"+zone.Seed);
        return IsChampion(definition)?120+hash%181:45+hash%136;
    }
    public static double RespawnDelay(ZoneDef zone,MobDef definition,int generation)
    {
        if(definition.Boss)return 300;
        if(!definition.Elite)return 25;
        if(definition.Id=="rare_hay_golem")return 90;
        int hash=StableHash(zone.Id+"|"+definition.Id+"|"+generation+"|"+zone.Seed);
        return IsChampion(definition)?600+hash%301:360+hash%181;
    }
    public static double RespawnClearRadius(MobDef definition)=>definition.Boss?12:IsChampion(definition)?14:definition.Elite?10:7;
    public static (double Minimum,double Maximum) RespawnWindow(MobDef definition)
        =>definition.Id=="rare_hay_golem"?(90,90):IsChampion(definition)?(600,900):definition.Elite?(360,540):definition.Boss?(300,300):(25,25);

    private static int StableHash(string value)
    {
        unchecked
        {
            uint hash=2166136261;
            foreach(char c in value){hash^=c;hash*=16777619;}
            return (int)(hash&0x7fffffff);
        }
    }
}
