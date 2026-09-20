using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

internal static class HuntingGroundChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0; var census=new List<object>();
        void Need(bool condition,string message) { if(!condition) throw new InvalidOperationException(message); }
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        void Test(string name,Action action)
        {
            try { action();passed++;Console.WriteLine("PASS HUNTING: "+name); }
            catch(Exception error) { failures.Add("HUNTING: "+name);Console.WriteLine("FAIL HUNTING: "+name+": "+error); }
        }
        var watch=Stopwatch.StartNew(); var realm=new RealmEngine(data); watch.Stop(); double cachedInitialization=watch.Elapsed.TotalMilliseconds;
        Test("Every hunting region has exact ordinary multipliers, unique positions, and bounded separated patches",()=>
        {
            var ids=new HashSet<string>(StringComparer.Ordinal);
            foreach(var zone in data.Zones)
            {
                var plan=HuntingGrounds.For(data,zone); var reachable=HuntingGrounds.ReachableFloor(zone);
                var templates=HuntingGrounds.Species(data,zone);
                foreach(string species in templates)
                {
                    var def=data.Mob(species); int expected=def.Boss||def.Elite?1:HuntingGrounds.Multiplier(zone.Level);
                    var placed=plan.Spawns.Where(s=>s.Template==species).ToArray();
                    Need(placed.Length==expected,$"{zone.Id}/{species}: {placed.Length} instead of {expected}");
                    Need(placed.All(s=>realm.State.Creatures.ContainsKey(s.Id)),"A planned creature is absent from the authoritative realm.");
                }
                foreach(var spawn in plan.Spawns)
                {
                    Need(ids.Add(spawn.Id),"Repeated spawn identity: "+spawn.Id);
                    Need(WorldMap.Fits(zone,spawn.Position)&&reachable[(int)spawn.Position.Y*zone.Width+(int)spawn.Position.X],"Unreachable or blocked hunting spawn: "+spawn.Id);
                    Need(!HuntingGrounds.Protected(zone,spawn.Position,data),"Hunting occupies a protected service or entry area: "+spawn.Id);
                    Need(plan.Membership.ContainsKey(spawn.Id),"Spawn has no patch membership.");
                }
                for(int i=0;i<plan.Spawns.Count;i++) for(int j=i+1;j<plan.Spawns.Count;j++)
                    Need(plan.Spawns[i].Position.Distance(plan.Spawns[j].Position)>1.05,"Spawn overlap in "+zone.Id);
                foreach(var patch in plan.Patches)
                {
                    var members=plan.Spawns.Where(s=>s.Patch==patch.Id).ToArray();
                    Need(members.Length==patch.Count&&patch.Count is >=1 and <=5,"Unbounded or empty hunting patch.");
                    Need(members.All(s=>s.Position.Distance(patch.Position)<=patch.Radius),"Member is outside its hunting patch.");
                }
                if(plan.BaselineOrdinary>0) Need(plan.Patches.Count>1,"Only one hunting pile exists in "+zone.Id);
                if(zone.Kind=="interior") Need(plan.Spawns.Count==0&&plan.FieldBoss=="","An interior became a hostile hunting area.");
                census.Add(new {zone=zone.Id,level=zone.Level,kind=zone.Kind,baseline=plan.BaselineOrdinary,multiplier=plan.Multiplier,
                    ordinary=plan.OrdinaryCount,spawnSlots=plan.Spawns.Count,patches=plan.Patches.Count,fieldBoss=plan.FieldBoss,specialty=plan.Specialty});
            }
        });
        Test("Field domains and underground objectives retain one real boss and reachable rewards",()=>
        {
            foreach(var zone in data.Zones)
            {
                var plan=HuntingGrounds.For(data,zone);
                if(plan.FieldBoss!="")
                {
                    var boss=realm.State.Creatures[zone.Id+"/field-boss"];
                    Need(data.Mob(boss.Template).Boss&&boss.Template==plan.FieldBoss,"A field marker has no actual boss.");
                    Need(WorldMap.Fits(zone,boss.Home)&&WorldMap.FindPath(zone,zone.Spawn,boss.Home,zone.Width*zone.Height).Count>0,"Field boss is unreachable.");
                    Need(boss.Home.Distance(zone.Spawn)>20,"Field boss occupies a beginner arrival point.");
                }
                if(zone.Boss!="") Need(realm.State.Creatures[zone.Id+"/boss"].Template==zone.Boss,"Existing dungeon boss changed.");
                if(plan.Patches.Count>0 && zone.Kind is "wilderness" or "tunnel")
                {
                    var chest=realm.State.Chests[zone.Id+"/chest/2"];
                    Need(WorldMap.Fits(zone,chest.Position),"Hunting reward chest is blocked.");
                    Need(chest.Position.Distance(plan.CachePosition)<.01,"Cache marker differs from actual reward position.");
                }
            }
        });
        Test("Hunting plans are deterministic and reload does not duplicate or reset saved creatures",()=>
        {
            foreach(string id in new[]{"wayfarers_rest","kingsmeadow","broken_mill"})
            {
                var copy=Wire.Copy(data);
                Need(Json(HuntingGrounds.For(data,data.Zone(id)))==Json(HuntingGrounds.For(copy,copy.Zone(id))),"Hunting plan is not deterministic: "+id);
            }
            var victim=realm.State.Creatures.Values.First(m=>m.Id.Contains("/hunt/",StringComparison.Ordinal));
            victim.Health=0; victim.Generation=7; victim.RespawnAt=realm.State.Time+900;
            string before=Json(realm.State); var reload=new RealmEngine(data,Wire.Copy(realm.State));
            Need(Json(reload.State)==before,"Reload changes hunting position, death state, or rewards.");
            Need(!reload.EconomicDirty,"An unchanged hunting plan dirties every save.");
            Need(Items.Validate(reload.State,data).Count==0,"Hunting reload broke item ownership.");
        });
        Test("Legacy migration retains primary creature identities health and timers without multiplying owned pets",()=>
        {
            var state=Wire.Copy(realm.State); state.HuntingRevision=0;
            foreach(var id in state.Creatures.Keys.Where(id=>id.Contains("/hunt/",StringComparison.Ordinal)||id.EndsWith("/field-boss",StringComparison.Ordinal)).ToArray()) state.Creatures.Remove(id);
            var primary=state.Creatures["wayfarers_rest/field_rat"]; primary.Health=0;primary.RespawnAt=999;primary.Generation=11;
            var owned=state.Creatures["wayfarers_rest/wild_hare"];owned.Owner="retained-pet-fixture";var oldPet=Json(owned);
            var engine=new RealmEngine(data,state);
            var retained=engine.State.Creatures[primary.Id];
            Need(retained.Health==0&&retained.RespawnAt==999&&retained.Generation==11,"Migration reset a killed primary creature.");
            Need(Json(engine.State.Creatures[owned.Id])==oldPet,"Migration moved or reset a captured creature.");
            Need(engine.State.HuntingRevision==HuntingGrounds.Revision&&engine.EconomicDirty,"Migration is not persisted.");
            string before=Json(engine.State); var again=new RealmEngine(data,Wire.Copy(engine.State));
            Need(Json(again.State)==before,"Migration is not idempotent.");
        });
        Test("Dungeon population correction retires obsolete wild slots but preserves owned animals and boss state",()=>
        {
            var state=Wire.Copy(realm.State);state.HuntingRevision=1;
            var zone=data.Zone("broken_mill");
            Need(!zone.Species.Contains("stone_guardian"),"Beginner dungeon still contains the level-65 guardian.");
            var old=new Creature { Id=zone.Id+"/stone_guardian",Template="stone_guardian",Zone=zone.Id,Home=zone.Spawn,Position=zone.Spawn,Health=33,Generation=8 };
            state.Creatures[old.Id]=old;
            var pet=Wire.Copy(old);pet.Id=zone.Id+"/hunt/stone_guardian/01";pet.Owner="retained-pet";state.Creatures[pet.Id]=pet;
            string savedPet=Json(pet),savedBoss=Json(state.Creatures[zone.Id+"/boss"]);
            var loaded=new RealmEngine(data,state);
            Need(!loaded.State.Creatures.ContainsKey(old.Id),"Obsolete over-level spawn remained in the dungeon.");
            Need(Json(loaded.State.Creatures[pet.Id])==savedPet,"Owned dungeon animal changed during population correction.");
            Need(Json(loaded.State.Creatures[zone.Id+"/boss"])==savedBoss,"Population correction reset the dungeon boss.");
        });
        Test("Camped hunting slots wait before respawn then recover after the player leaves",()=>
        {
            var engine=new RealmEngine(data); var p=engine.CreateCharacter("hunt-respawn","Hunt Respawn","vanguard",new());
            var plan=HuntingGrounds.For(data,data.Zone(p.Zone)); var spawn=plan.Spawns.First(s=>s.Template=="field_rat");
            var mob=engine.State.Creatures[spawn.Id]; mob.Health=0;mob.RespawnAt=0;
            p.Position=mob.Home;engine.Active.Add(p.Id);
            for(int i=0;i<3;i++)engine.Tick(.1);
            Need(mob.Health==0,"A hunting animal respawned under the player.");
            p.Position=data.Zone(p.Zone).Spawn;
            for(int i=0;i<6;i++)engine.Tick(.1);
            Need(mob.Health>0&&WorldMap.Fits(data.Zone(mob.Zone),mob.Position),"A clear hunting slot did not respawn.");
        });
        Test("Dense hunting motion stays bounded and the server exposes measured tick and snapshot costs",()=>
        {
            var engine=new RealmEngine(data); var p=engine.CreateCharacter("hunt-profile","Hunt Profile","vanguard",new());
            var zone=data.Zone("thistle_woods");var plan=HuntingGrounds.For(data,zone);p.Zone=zone.Id;p.Position=plan.Patches[0].Position;
            p.Statuses.Add(new StatusEffect{Kind="stealth",Power=1,Until=10000});engine.Active.Add(p.Id);
            var subjects=engine.State.Creatures.Values.Where(m=>m.Zone==zone.Id&&!data.Mob(m.Template).Boss&&m.Position.Distance(p.Position)<24).ToArray();
            var distances=subjects.ToDictionary(m=>m.Id,_=>0.0);var moving=subjects.ToDictionary(m=>m.Id,_=>0);var timings=new List<double>();
            for(int i=0;i<1200;i++)
            {
                var before=subjects.ToDictionary(m=>m.Id,m=>m.Position);
                var timer=Stopwatch.StartNew();engine.Tick(.1);timer.Stop();timings.Add(timer.Elapsed.TotalMilliseconds);
                foreach(var mob in subjects)
                {
                    double distance=before[mob.Id].Distance(mob.Position);distances[mob.Id]+=distance;
                    if(distance>.01)moving[mob.Id]++;
                    Need(WorldMap.Fits(zone,mob.Position),"Creature moved into an obstacle: "+mob.Id);
                    Need(distance<=data.Mob(mob.Template).Speed*.2*1.31+.01,"Movement exceeded the simulated cadence: "+mob.Id);
                }
            }
            Need(subjects.Length>=6,"Profile area does not contain a visible hunting population.");
            Need(distances.Count(x=>x.Value>2)>=Math.Max(2,subjects.Length/3),"Most sampled creatures never wandered.");
            int bytes=JsonSerializer.SerializeToUtf8Bytes(engine.Snapshot(p.Id),Wire.Json).Length;
            Need(bytes<2_000_000,"Dense snapshot exceeds the client's existing packet limit.");
            timings.Sort(); double p95=timings[(int)(timings.Count*.95)];
            var report=new { cachedPlanInitializationMs=cachedInitialization,creatures=engine.State.Creatures.Count,observed=subjects.Length,
                simulatedSeconds=120,meanTickMs=timings.Average(),p95TickMs=p95,maxTickMs=timings[^1],snapshotBytes=bytes,
                averageTravelTiles=distances.Values.Average(),movingSamples=moving.Values.Sum(),samples=subjects.Length*1200 };
            Directory.CreateDirectory("artifacts/experience/hunting");
            File.WriteAllText("artifacts/experience/hunting/performance.json",Json(report));
            Console.WriteLine("HUNTING_PROFILE "+Json(report));
        });
        Directory.CreateDirectory("artifacts/experience/hunting");
        File.WriteAllText("artifacts/experience/hunting/census.json",Json(census));
        Console.WriteLine($"HUNTING CONTRACT: {passed} groups passed; {realm.State.Creatures.Count} total creatures; {census.Count} regions counted; total failures {failures.Count}.");
    }
}
