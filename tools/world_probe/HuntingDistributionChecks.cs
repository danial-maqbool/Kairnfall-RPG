using Kairnfall.Core;
using System.Text.Json;

internal static class HuntingDistributionChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Need(bool condition,string text){if(!condition)throw new InvalidOperationException(text);}
        void Test(string name,Action test){try{test();passed++;Console.WriteLine("PASS HUNT SPREAD: "+name);}catch(Exception e){failures.Add(name);Console.WriteLine("FAIL HUNT SPREAD: "+name+": "+e);}}
        Test("All level bands double the previous ordinary population without duplicating bosses",()=>
        {
            foreach(var (level,count) in new[]{(1,60),(20,60),(21,40),(40,40),(41,30),(60,30),(61,20),(80,20),(81,10),(100,10)})
                Need(HuntingGrounds.Multiplier(level)==count,"Incorrect density at "+level);
            foreach(var zone in data.Zones)
            {
                var plan=HuntingGrounds.For(data,zone);
                foreach(var mob in HuntingGrounds.Species(data,zone).Select(data.Mob))
                    Need(plan.Spawns.Count(s=>s.Template==mob.Id)==(mob.Boss||mob.Elite?1:HuntingGrounds.Multiplier(zone.Level)),"Spawn count differs in "+zone.Id);
            }
        });
        Test("Large wilderness hunting patches cover the reachable map rather than one arrival ring",()=>
        {
            var report=new List<object>(); int examined=0;
            foreach(var zone in data.Zones.Where(z=>z.Kind=="wilderness"))
            {
                var plan=HuntingGrounds.For(data,zone); if(plan.Patches.Count<16)continue;
                var floor=HuntingGrounds.ReachableFloor(zone); var possible=new List<Point>();
                for(int y=3;y<zone.Height-3;y+=2)for(int x=3;x<zone.Width-3;x+=2)
                {
                    var p=new Point(x+.5,y+.5);
                    if(floor[y*zone.Width+x]&&!HuntingGrounds.Protected(zone,p,data))possible.Add(p);
                }
                if(possible.Count<64)continue;
                double minX=possible.Min(p=>p.X),maxX=possible.Max(p=>p.X),minY=possible.Min(p=>p.Y),maxY=possible.Max(p=>p.Y);
                double xCoverage=(plan.Patches.Max(p=>p.Position.X)-plan.Patches.Min(p=>p.Position.X))/Math.Max(1,maxX-minX);
                double yCoverage=(plan.Patches.Max(p=>p.Position.Y)-plan.Patches.Min(p=>p.Position.Y))/Math.Max(1,maxY-minY);
                Need(xCoverage>=.60&&yCoverage>=.60,"Hunting remains confined in "+zone.Id+": "+xCoverage+","+yCoverage);
                Need(plan.Patches.Any(p=>p.Position.Distance(zone.Spawn)<35),"No nearby arrival hunting route in "+zone.Id);
                examined++; report.Add(new{zone=zone.Id,patches=plan.Patches.Count,ordinary=plan.OrdinaryCount,xCoverage,yCoverage});
            }
            Need(examined>=5,"Too few complete wilderness maps were inspected.");
            Directory.CreateDirectory("artifacts/experience/hunting");
            File.WriteAllText("artifacts/experience/hunting/distribution.json",JsonSerializer.Serialize(report,Wire.Json));
            Console.WriteLine("HUNT_DISTRIBUTION_MAPS="+examined);
        });
        Console.WriteLine($"HUNT SPREAD: {passed} groups passed; total failures {failures.Count}.");
    }
}
