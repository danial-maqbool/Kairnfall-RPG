namespace Kairnfall.Core;

public sealed class LootPile
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Zone { get; set; } = "";
    public Point Position { get; set; }
    public string Owner { get; set; } = "";
    public string Party { get; set; } = "";
    public List<Item> Items { get; set; } = [];
    public long Gold { get; set; }
    public double PublicAt { get; set; }
    public double Expires { get; set; }
}

public static class WorldTime
{
    public const double DayLength=1800;
    public static double DayFraction(double time)=>(time%DayLength)/DayLength;
    public static string Weather(ZoneDef zone,double time)
    {
        if(zone.Layer!="Surface") return "underground";
        var n=WorldMap.Hash((int)(time/300),0,zone.Seed)%6;
        if(n<3) return "clear";
        return zone.Biome switch
        {
            "tundra" or "glacier" => n==5?"blizzard":"snow",
            "volcanic" => "ash",
            "swamp" or "wetlands" => n==5?"rain":"fog",
            "badlands" => "dust",
            _ => n==5?"storm":"rain"
        };
    }
}
