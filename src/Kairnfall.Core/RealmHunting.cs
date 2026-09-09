namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private readonly Dictionary<string,HuntPatch> huntMembership = new(StringComparer.Ordinal);
    private readonly Dictionary<string,HuntingPlan> huntPlans = new(StringComparer.Ordinal);
    private Dictionary<(string Zone,int X,int Y),List<Creature>> creatureCells = [];
    private static (string,int,int) CreatureCell(string zone,Point at) => (zone,(int)Math.Floor(at.X/4),(int)Math.Floor(at.Y/4));

    private void SeedHuntingWorld()
    {
        bool migrate=State.HuntingRevision<HuntingGrounds.Revision;
        bool changed=false;
        foreach(var zone in Data.Zones)
        {
            var plan=HuntingGrounds.For(Data,zone); huntPlans[zone.Id]=plan;
            foreach(var spawn in plan.Spawns)
            {
                huntMembership[spawn.Id]=plan.Membership[spawn.Id];
                var def=Data.Mob(spawn.Template);
                if(State.Creatures.TryGetValue(spawn.Id,out var existing))
                {
                    if(existing.Owner!=""||existing.Template!=spawn.Template||existing.Zone!=zone.Id) continue;
                    if(migrate)
                    {
                        var oldHome=existing.Home; existing.Home=spawn.Position;
                        if(HuntingGrounds.Protected(zone,existing.Position,Data)||(!existing.Threat.Any()&&existing.Target==""&&existing.Position.Distance(oldHome)<1))
                            existing.Position=spawn.Position;
                        changed=true;
                    }
                    continue;
                }
                bool occupied=State.Characters.Values.Any(p=>p.Zone==zone.Id&&p.Health>0&&p.Position.Distance(spawn.Position)<8);
                State.Creatures.Add(spawn.Id,new Creature { Id=spawn.Id,Template=spawn.Template,Zone=zone.Id,
                    Home=spawn.Position,Position=spawn.Position,Health=occupied?0:def.Health,RespawnAt=occupied?State.Time+1:0 });
                changed=true;
            }
            if(plan.FieldBoss!="")
            {
                string id=zone.Id+"/field-boss";
                if(!State.Creatures.ContainsKey(id))
                {
                    var def=Data.Mob(plan.FieldBoss);
                    bool occupied=State.Characters.Values.Any(p=>p.Zone==zone.Id&&p.Health>0&&p.Position.Distance(plan.FieldBossPosition)<12);
                    State.Creatures.Add(id,new Creature { Id=id,Template=def.Id,Zone=zone.Id,Home=plan.FieldBossPosition,
                        Position=plan.FieldBossPosition,Health=occupied?0:def.Health,RespawnAt=occupied?State.Time+3:0 });
                    changed=true;
                }
            }
            // Reuse the existing hidden cache. Do not create another chest per hunting patch.
            if(migrate && plan.Patches.Count>0 && zone.Kind is "wilderness" or "tunnel"
                && State.Chests.TryGetValue(zone.Id+"/chest/2",out var cache))
            {
                cache.Position=plan.CachePosition; changed=true;
            }
        }
        if(migrate) { State.HuntingRevision=HuntingGrounds.Revision; changed=true; }
        if(changed) EconomicDirty=true;
    }

    private bool CanHuntRespawn(Creature mob,IReadOnlyList<Character> live)
    {
        if(!huntMembership.ContainsKey(mob.Id)&&!mob.Id.EndsWith("/field-boss",StringComparison.Ordinal)) return true;
        double distance=Data.Mob(mob.Template).Boss?12:7;
        return !live.Any(p=>p.Zone==mob.Zone&&p.Position.Distance(mob.Home)<distance)
            && !NearCreatures(mob.Zone,mob.Home).Any(other=>other.Id!=mob.Id&&other.Health>0&&other.Position.Distance(mob.Home)<.8);
    }
    private void IndexCreatures(IEnumerable<Creature> creatures)
    {
        creatureCells.Clear();
        foreach(var mob in creatures.Where(m=>m.Health>0))
        {
            var cell=CreatureCell(mob.Zone,mob.Position);
            if(!creatureCells.TryGetValue(cell,out var rows)) creatureCells[cell]=rows=[];
            rows.Add(mob);
        }
    }
    private IEnumerable<Creature> NearCreatures(string zone,Point at)
    {
        var (_,x,y)=CreatureCell(zone,at);
        for(int dy=-1;dy<=1;dy++) for(int dx=-1;dx<=1;dx++)
            if(creatureCells.TryGetValue((zone,x+dx,y+dy),out var rows))
                foreach(var mob in rows) yield return mob;
    }
    private Point SeparatedMove(Creature mob,Point direction,double distance)
    {
        var zone=Data.Zone(mob.Zone); var from=mob.Position;
        bool Clear(Point point) => !NearCreatures(mob.Zone,point).Any(other=>other.Id!=mob.Id&&other.Health>0&&other.Position.Distance(point)<.66);
        Point chosen=WorldMap.Move(zone,from,direction.Scale(distance));
        if(!Clear(chosen))
        {
            double sign=(MotionSeed(mob.Id)&1)==0?1:-1;
            var side=new Point(-direction.Y*sign,direction.X*sign);
            var candidates=new[]{direction.Add(side.Scale(.75)),direction.Scale(.35),side.Scale(.6)};
            chosen=from;
            foreach(var next in candidates)
            {
                double length=next.Distance(new Point(0,0));
                var bounded=length>1?next.Scale(1/length):next;
                var point=WorldMap.Move(zone,from,bounded.Scale(distance));
                if(point.Distance(from)<.03||!Clear(point)) continue;
                chosen=point; break;
            }
        }
        var oldCell=CreatureCell(mob.Zone,from); var newCell=CreatureCell(mob.Zone,chosen);
        if(oldCell!=newCell)
        {
            if(creatureCells.TryGetValue(oldCell,out var old)) old.Remove(mob);
            if(!creatureCells.TryGetValue(newCell,out var rows)) creatureCells[newCell]=rows=[];
            rows.Add(mob);
        }
        return chosen;
    }
    private bool PatrolHuntingCreature(Creature mob,MobDef definition,double dt)
    {
        if(!huntMembership.TryGetValue(mob.Id,out var patch)||patch.Pattern!="patrol") return false;
        if(!creatureMotion.TryGetValue(mob.Id,out var plan)||plan.Threat!="")
            creatureMotion[mob.Id]=plan=new CreatureMotionPlan { Goal=mob.Position,NextDecision=State.Time+1 };
        if(mob.Position.Distance(mob.Home)>7)
        {
            MoveCreature(mob,mob.Home,dt,definition.Speed*.7); return true;
        }
        if(mob.Position.Distance(plan.Goal)>.2)
        {
            MoveCreature(mob,plan.Goal,dt,definition.Speed*.55);
            if(State.Time>plan.NextDecision+6) { plan.Goal=mob.Position; plan.NextDecision=State.Time+1; }
            return true;
        }
        if(State.Time<plan.NextDecision) return true;
        Point[] route=[new(2.5,0),new(0,2.5),new(-2.5,0),new(0,-2.5)];
        int offset=(int)(MotionSeed(mob.Id)%4);
        for(int attempt=0;attempt<4;attempt++)
        {
            var goal=mob.Home.Add(route[(++plan.Cycle+offset)%4]);
            if(!WorldMap.Fits(Data.Zone(mob.Zone),goal)||!WorldMap.LineOfSight(Data.Zone(mob.Zone),mob.Position,goal)) continue;
            plan.Goal=goal; plan.NextDecision=State.Time+2+mob.Position.Distance(goal)/Math.Max(.1,definition.Speed*.55);
            return true;
        }
        plan.NextDecision=State.Time+1.5; return true;
    }
}
