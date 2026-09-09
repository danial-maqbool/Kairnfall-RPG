using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

namespace Kairnfall.Core;

/// <summary>Immutable, deterministic hunting layout. Counts are actual spawn slots, not a visual multiplier.</summary>
public sealed record HuntSpawn(string Id, string Template, Point Position, string Patch);
public sealed record HuntPatch(string Id, string Name, string Template, string Pattern, Point Position, int Count, double Radius);
public sealed class HuntingPlan
{
    public IReadOnlyList<HuntSpawn> Spawns { get; init; } = Array.Empty<HuntSpawn>();
    public IReadOnlyList<HuntPatch> Patches { get; init; } = Array.Empty<HuntPatch>();
    public IReadOnlyDictionary<string,HuntPatch> Membership { get; init; } = new ReadOnlyDictionary<string,HuntPatch>(new Dictionary<string,HuntPatch>());
    public string Specialty { get; init; } = "";
    public string FieldBoss { get; init; } = "";
    public Point FieldBossPosition { get; init; }
    public Point CachePosition { get; init; }
    public int Multiplier { get; init; }
    public int BaselineOrdinary { get; init; }
    public int OrdinaryCount => BaselineOrdinary * Multiplier;
}

public static class HuntingGrounds
{
    public const int Revision = 1;
    public const int PackSize = 5;
    private sealed class Cache { public readonly Dictionary<string,(int Stamp,HuntingPlan Plan)> Plans = []; }
    private static readonly ConditionalWeakTable<Catalog,Cache> Caches = new();
    public static int Multiplier(int level) => level <= 20 ? 30 : level <= 40 ? 20 : level <= 60 ? 15 : level <= 80 ? 10 : 5;
    public static bool IsTown(ZoneDef zone) => zone.Kind is "city" or "settlement";
    public static string Specialty(ZoneDef zone) => zone.Biome switch
    {
        "plains" => "Meadow herds and burrow colonies",
        "farmland" => "Field pests and boar runs",
        "forest" => "Woodland packs and webbed ambush sites",
        "pine_forest" => "Pinewood patrols and predator dens",
        "ancient_forest" => "Root guardians and old-growth hunting grounds",
        "swamp" or "wetlands" => "Causeway ambushes and reed-bank colonies",
        "coast" or "archipelago" => "Shoreline packs and stranded-camp sentries",
        "tundra" or "glacier" => "Sheltered snowfields and ice predators",
        "mountains" or "highlands" => "Ridge patrols and stony hunting terraces",
        "volcanic" => "Ash-basin packs and furnace sentries",
        "badlands" => "Caravan ambushes and burrowing colonies",
        "fungal" => "Healer colonies and spore-chamber ambushes",
        "crystal" => "Crystal sentries and clustered cave predators",
        "wasteland" or "ruins" => "Ruined-road patrols and guarded burial caches",
        "arcane_anomaly" => "Rift patrols and spellcasting colonies",
        _ => "Regional hunting grounds"
    };
    public static string Pattern(MobDef mob) => mob.Ai switch
    {
        "pack_hunter" => "pack", "guard" or "ranged_kiter" => "patrol",
        "ambusher" => "ambush", "healer" or "summoner" or "caster" => "colony",
        "passive" or "fleeing" => "graze", _ => "territory"
    };
    public static bool Protected(ZoneDef zone, Point point, Catalog data)
    {
        if (zone.Kind == "interior") return true;
        double dx = Math.Abs(point.X-zone.Spawn.X), dy = Math.Abs(point.Y-zone.Spawn.Y);
        if (IsTown(zone) ? dx < 25 && dy < 25 : point.Distance(zone.Spawn) < 9) return true;
        if (zone.Exits.Any(exit => exit.Position.Distance(point) < 5)) return true;
        return data.Npcs.Any(npc => npc.Zone == zone.Id && npc.Position.Distance(point) < 4);
    }
    public static IReadOnlyList<string> Species(Catalog data, ZoneDef zone)
    {
        if (zone.Kind == "interior") return Array.Empty<string>();
        if (zone.Species.Length > 0) return zone.Species.Distinct(StringComparer.Ordinal).ToArray();
        if (!IsTown(zone)) return Array.Empty<string>();
        // Formerly empty settlements gain wildlife outside their protected service core.
        var nearby = data.Mobs.Where(m => !m.Boss && !m.Elite && m.Biome == zone.Biome && m.Level <= Math.Max(5,zone.Level+5))
            .OrderBy(m=>m.Level).ThenBy(m=>m.Id,StringComparer.Ordinal).Take(2).Select(m=>m.Id).ToArray();
        return nearby.Length>0 ? nearby : data.Mobs.Where(m=>m.Id is "field_rat" or "wild_hare").Select(m=>m.Id).ToArray();
    }
    public static HuntingPlan For(Catalog data, ZoneDef zone)
    {
        var cache = Caches.GetOrCreateValue(data);
        // Tests may change furniture in a copied catalog. Do not reuse stale walkability.
        var stamp = new HashCode(); stamp.Add(zone.Seed); stamp.Add(zone.Width); stamp.Add(zone.Height); stamp.Add(zone.Spawn);
        stamp.Add(zone.Kind); stamp.Add(zone.Biome); stamp.Add(zone.Level); stamp.Add(zone.Boss);
        foreach(var id in zone.Species) stamp.Add(id);
        foreach(var b in zone.Buildings) { stamp.Add(b.X); stamp.Add(b.Y); stamp.Add(b.Width); stamp.Add(b.Height); }
        foreach(var f in zone.Furnishings) { stamp.Add(f.X); stamp.Add(f.Y); stamp.Add(f.Width); stamp.Add(f.Height); stamp.Add(f.Solid); }
        foreach(var e in zone.Exits) stamp.Add(e.Position);
        foreach(var npc in data.Npcs.Where(n=>n.Zone==zone.Id)) stamp.Add(npc.Position);
        int value=stamp.ToHashCode();
        lock(cache.Plans)
        {
            if(cache.Plans.TryGetValue(zone.Id,out var found) && found.Stamp==value) return found.Plan;
            var plan=Build(data,zone); cache.Plans[zone.Id]=(value,plan); return plan;
        }
    }
    private static HuntingPlan Build(Catalog data, ZoneDef zone)
    {
        var species=Species(data,zone).Select(data.Mob).ToArray();
        if(species.Length==0) return new HuntingPlan { Specialty=zone.Kind=="interior"?"Safe service interior":Specialty(zone) };
        var surface=ReachableFloor(zone);
        bool Reach(Point p) { int x=(int)p.X,y=(int)p.Y; return x>0&&y>0&&x<zone.Width&&y<zone.Height&&surface[y*zone.Width+x]; }
        var anchors=new List<Point>();
        for(int y=3;y<zone.Height-3;y+=2)
        for(int x=3;x<zone.Width-3;x+=2)
        {
            var point=new Point(x+.5,y+.5);
            if(Reach(point)&&!Protected(zone,point,data)) anchors.Add(point);
        }
        if(anchors.Count==0) throw new InvalidDataException("No reachable hunting ground in "+zone.Id);
        var occupied=new List<Point>(); var centers=new List<Point>(); var spawns=new List<HuntSpawn>(); var patches=new List<HuntPatch>();
        var membership=new Dictionary<string,HuntPatch>(StringComparer.Ordinal);
        int multiplier=Multiplier(zone.Level), ordinary=species.Count(m=>!m.Boss&&!m.Elite), sequence=0;
        var assigned=species.ToDictionary(m=>m.Id,_=>0,StringComparer.Ordinal);
        var dungeonBoss=zone.Boss==""?zone.Spawn:WorldMap.FindFree(zone,new(zone.Spawn.X+6,zone.Spawn.Y+3));
        bool Legal(Point point) => Reach(point)&&!Protected(zone,point,data)
            && (zone.Boss==""||point.Distance(dungeonBoss)>=7)
            && occupied.All(other=>other.Distance(point)>1.05);
        for(int batch=0;batch<(multiplier+PackSize-1)/PackSize;batch++)
        foreach(var mob in species)
        {
            int total=mob.Boss||mob.Elite?1:multiplier, remaining=total-assigned[mob.Id];
            if(remaining<=0) continue;
            int requested=Math.Min(PackSize,remaining);
            double angle=(sequence++*2.399963+zone.Seed*.01)%Math.Tau;
            double radius=IsTown(zone)?29+batch%2*5:zone.Layer=="Surface"?19+batch*8:12+batch*4;
            var desired=new Point(zone.Spawn.X+Math.Cos(angle)*radius,zone.Spawn.Y+Math.Sin(angle)*radius);
            Point centre=default; List<Point>? positions=null;
            // Relax centre separation, never actor separation or reachability, in narrow tunnels.
            foreach(double separation in new[]{6.0,3.0,0.0})
            {
                foreach(var candidate in anchors.Where(p=>centers.All(c=>c.Distance(p)>=separation))
                    .OrderBy(p=>p.Distance(desired)).ThenBy(p=>WorldMap.Hash((int)p.X,(int)p.Y,zone.Seed)))
                {
                    var local=new List<Point>();
                    foreach(var point in LocalCells(candidate,zone.Seed+sequence))
                    {
                        if(!Legal(point)||local.Any(p=>p.Distance(point)<=1.05)) continue;
                        local.Add(point); if(local.Count==requested) break;
                    }
                    if(local.Count!=requested) continue;
                    centre=candidate; positions=local; break;
                }
                if(positions is not null) break;
            }
            if(positions is null) throw new InvalidDataException($"Cannot place {requested} separated hunting creatures in {zone.Id}/{mob.Id}. No density was silently discarded.");
            string patchId=$"{zone.Id}/hunt-site/{mob.Id}/{batch}";
            string pattern=Pattern(mob);
            string name=mob.Name+" "+(pattern switch {"pack"=>"den","patrol"=>"patrol","ambush"=>"ambush","colony"=>"colony","graze"=>"grounds",_=>"territory"});
            var patch=new HuntPatch(patchId,name,mob.Id,pattern,centre,requested,5);
            centers.Add(centre); patches.Add(patch);
            foreach(var point in positions)
            {
                int index=assigned[mob.Id]++;
                string id=index==0?zone.Id+"/"+mob.Id:$"{zone.Id}/hunt/{mob.Id}/{index:D2}";
                var spawn=new HuntSpawn(id,mob.Id,point,patchId); spawns.Add(spawn); occupied.Add(point); membership.Add(id,patch);
            }
        }
        string boss=""; Point bossPosition=default;
        if(zone.Kind=="wilderness" && zone.Boss=="")
        {
            var candidate=data.Mobs.Where(m=>m.Boss&&m.Level<=zone.Level+14)
                .OrderBy(m=>m.Biome==zone.Biome?0:1).ThenBy(m=>Math.Abs(m.Level-(zone.Level+6))).ThenBy(m=>m.Id,StringComparer.Ordinal).FirstOrDefault();
            if(candidate is not null)
            {
                boss=candidate.Id;
                double radius=Math.Min(zone.Width*.28,65);
                var desired=new Point(zone.Spawn.X-radius,zone.Spawn.Y+radius*.7);
                bossPosition=anchors.Where(p=>Legal(p)&&p.Distance(zone.Spawn)>20).OrderBy(p=>p.Distance(desired)).FirstOrDefault();
                if(bossPosition==default) throw new InvalidDataException("No field-boss domain in "+zone.Id);
            }
        }
        var cacheAnchor=patches.OrderByDescending(p=>p.Position.Distance(zone.Spawn)).First().Position;
        Point cachePosition=LocalCells(cacheAnchor,zone.Seed+719).FirstOrDefault(p=>Legal(p));
        if(cachePosition==default) cachePosition=cacheAnchor;
        return new HuntingPlan
        {
            Spawns=Array.AsReadOnly(spawns.ToArray()),Patches=Array.AsReadOnly(patches.ToArray()),
            Membership=new ReadOnlyDictionary<string,HuntPatch>(membership),Multiplier=multiplier,BaselineOrdinary=ordinary,
            Specialty=Specialty(zone),FieldBoss=boss,FieldBossPosition=bossPosition,CachePosition=cachePosition
        };
    }
    private static IEnumerable<Point> LocalCells(Point centre,int seed)
        => Enumerable.Range(-4,9).SelectMany(y=>Enumerable.Range(-4,9).Select(x=>new Point(centre.X+x,centre.Y+y)))
            .Where(p=>p.Distance(centre)<=4.4).OrderBy(p=>p.Distance(centre))
            .ThenBy(p=>WorldMap.Hash((int)p.X,(int)p.Y,seed));
    public static bool[] ReachableFloor(ZoneDef zone)
    {
        var open=new bool[checked(zone.Width*zone.Height)];
        for(int y=1;y<zone.Height-1;y++) for(int x=1;x<zone.Width-1;x++)
            open[y*zone.Width+x]=!WorldMap.IsSolid(WorldMap.TileAt(zone,x,y));
        int start=(int)zone.Spawn.Y*zone.Width+(int)zone.Spawn.X;
        var seen=new bool[open.Length]; if(start<0||start>=open.Length||!open[start]) return seen;
        var queue=new Queue<int>(); queue.Enqueue(start); seen[start]=true;
        while(queue.TryDequeue(out int cell))
        {
            int x=cell%zone.Width,y=cell/zone.Width;
            foreach(var (dx,dy) in new[]{(1,0),(-1,0),(0,1),(0,-1)})
            {
                int nx=x+dx,ny=y+dy; if(nx<1||ny<1||nx>=zone.Width-1||ny>=zone.Height-1) continue;
                int next=ny*zone.Width+nx; if(!open[next]||seen[next]) continue;
                seen[next]=true; queue.Enqueue(next);
            }
        }
        return seen;
    }
}
