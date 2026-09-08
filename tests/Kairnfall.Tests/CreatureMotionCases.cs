using Kairnfall.Core;

public static class CreatureMotionCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value,string message) { if(!value) throw new InvalidOperationException(message); }
        (RealmEngine Realm,Character Player,Creature Mob) Fixture()
        {
            var realm=new RealmEngine(data); var player=realm.CreateCharacter("motion-account","Motion Fixture","vanguard",new());
            realm.Active.Add(player.Id); realm.State.Creatures.Clear();
            var definition=data.Mob("field_rat"); var zone=data.Zone(player.Zone);
            var home=WorldMap.FindFree(zone,new Point(player.Position.X+8,player.Position.Y));
            var mob=new Creature { Id="motion/field_rat",Template=definition.Id,Zone=zone.Id,Home=home,Position=home,Health=definition.Health };
            realm.State.Creatures.Add(mob.Id,mob); return (realm,player,mob);
        }
        test("Idle animals walk pause and retain valid world positions",()=>
        {
            var (realm,player,mob)=Fixture(); var home=mob.Home; int walked=0,paused=0;
            for(int step=0;step<500;step++)
            {
                var before=mob.Position; realm.Tick(.05); double distance=before.Distance(mob.Position);
                if(distance>.001) walked++; else paused++;
                Check(WorldMap.Fits(data.Zone(mob.Zone),mob.Position),"Idle wandering crossed solid terrain.");
                Check(mob.Position.Distance(home)<=6.5,"Idle wandering exceeded its home range.");
                // The engine runs creature decisions at 0.2-second intervals, not each player tick.
                Check(distance<=data.Mob(mob.Template).Speed*.2+.001,"Idle movement exceeded authoritative speed.");
            }
            Check(walked>10&&paused>10,"Animals must both move and pause.");
        });
        test("A wounded starter animal retreats to cover instead of fleeing forever",()=>
        {
            var (realm,player,mob)=Fixture(); var start=mob.Position;
            player.Position=new Point(start.X-1,start.Y); mob.Health=data.Mob(mob.Template).Health*.25; mob.Threat[player.Id]=1;
            for(int step=0;step<60;step++) realm.Tick(.05);
            Check(mob.Position.Distance(start)>.1,"The retreat did not move.");
            Check(mob.Position.Distance(start)<=1.3,"The starter retreat exceeded its cover distance.");
            var resting=mob.Position; for(int step=0;step<10;step++) realm.Tick(.05);
            Check(mob.Position.Distance(resting)<.01,"The animal did not pause after reaching cover.");
        });
        test("Rooted and stunned animals cannot wander",()=>
        {
            foreach(string kind in new[]{"root","stun"})
            {
                var (realm,player,mob)=Fixture(); var start=mob.Position;
                mob.Statuses.Add(new StatusEffect {Kind=kind,Power=1,Until=realm.State.Time+20});
                for(int step=0;step<120;step++) realm.Tick(.05);
                Check(mob.Position==start,kind+" failed to stop wandering.");
            }
        });
        test("Wandering never changes saved identity home or inventory",()=>
        {
            var (realm,player,mob)=Fixture(); string id=mob.Id; var home=mob.Home; var items=player.Inventory.Select(x=>x.Id).ToArray();
            for(int step=0;step<160;step++) realm.Tick(.05);
            var loaded=new RealmEngine(data,Wire.Copy(realm.State));
            Check(loaded.State.Creatures[id].Home==home,"Wandering rewrote the respawn home.");
            Check(loaded.Player(player.Id).Inventory.Select(x=>x.Id).SequenceEqual(items),"Wandering altered owned items.");
            Check(WorldMap.Fits(data.Zone(mob.Zone),loaded.State.Creatures[id].Position),"Save restored an invalid wander position.");
        });
    }
}
