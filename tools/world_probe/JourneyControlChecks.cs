using System.Text.Json;
using Kairnfall.Core;

internal static class JourneyControlChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool ok,string message) { if(!ok) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value,Wire.Json);
        void Test(string name,Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS JOURNEY: "+name); }
            catch(Exception error) { failures.Add(name); Console.WriteLine("FAIL JOURNEY: "+name+": "+error); }
        }
        (RealmEngine Engine,string Id,Point Start) Fixture()
        {
            var realm = new RealmEngine(data);
            var p = realm.CreateCharacter("dash-fixture", "Dash Fixture", "vanguard", new());
            var zone = data.Zones.First(z=>z.Kind=="interior");
            for(int y=4;y<zone.Height-5;y++) for(int x=4;x<zone.Width-6;x++)
            {
                var at=new Point(x+.5,y+.5);
                if(!WorldMap.Fits(zone,at) || Math.Abs(WorldMap.Move(zone,at,new Point(DashRules.Distance,0)).Distance(at)-DashRules.Distance)>.001) continue;
                p.Zone=zone.Id; p.Position=at; p.Facing=new Point(1,0); p.Mana=16;
                return (realm,p.Id,at);
            }
            throw new InvalidOperationException("No clear dash fixture corridor.");
        }
        GameCommand Dash(RealmEngine realm,string id,double x=1,double y=0) => new() { Kind="dash", X=x,Y=y,Sequence=realm.Player(id).LastAction+1 };
        Test("Dash costs four mana, obeys distance and cooldown, and replay does not repeat movement",()=>
        {
            var (realm,id,start)=Fixture(); var p=realm.Player(id); double mana=p.Mana;
            var command=Dash(realm,id); var result=realm.Execute(id,command);
            Need(result.Ok,result.Message); p=realm.Player(id);
            Need(Math.Abs(p.Position.Distance(start)-2.5)<.001,"Dash distance differs.");
            Need(Math.Abs(p.Mana-(mana-4))<.001,"Dash mana cost differs.");
            Need(Math.Abs(p.Cooldowns["dash"]-realm.State.Time-.65)<.00001,"Dash cooldown differs.");
            string saved=Json(realm.State); Need(realm.Execute(id,command).Ok,"Replay receipt disappeared.");
            Need(Json(realm.State)==saved,"Replay repeated a dash or charged mana twice.");
            var next=realm.Execute(id,Dash(realm,id,-1));
            Need(!next.Ok && Json(realm.State)==saved,"Cooldown bypass changed state.");
            realm.State.Time+=.65; Need(realm.Execute(id,Dash(realm,id,-1)).Ok,"Dash is not reusable at the exact cooldown boundary.");
            Need(realm.Player(id).Position.Distance(start)<.001,"Reverse dash missed its start.");
        });
        Test("Dash rejects death, roots, stun, silence, insufficient mana and invalid direction without state changes",()=>
        {
            foreach(string reason in new[]{"dead","root","stun","silence","mana","direction"})
            {
                var (realm,id,_)=Fixture(); var p=realm.Player(id);
                if(reason=="dead") p.Health=0;
                else if(reason=="mana") p.Mana=3.99;
                else if(reason!="direction") p.Statuses.Add(new StatusEffect{Kind=reason,Until=realm.State.Time+3,Power=1,Source=id});
                string before=Json(realm.State);
                var result=realm.Execute(id,Dash(realm,id,reason=="direction"?99:1));
                Need(!result.Ok && Json(realm.State)==before,"Invalid "+reason+" dash mutated state.");
            }
            foreach(double value in new[]{double.NaN,double.PositiveInfinity,double.NegativeInfinity})
            {
                var (realm,id,_)=Fixture(); string before=Json(realm.State);
                Need(!realm.Execute(id,Dash(realm,id,value)).Ok && Json(realm.State)==before,"Non-finite dash direction was accepted.");
            }
        });
        Test("Dash sweeps solid furniture and never crosses the obstacle or grants invulnerability",()=>
        {
            var copy=Wire.Copy(data); var realm=new RealmEngine(copy);
            var p=realm.CreateCharacter("wall-dash","Wall Dash","vanguard",new());
            var zone=copy.Zones.First(z=>z.Kind=="interior"); p.Zone=zone.Id; p.Position=new Point(15.5,16.5); p.Mana=30;
            zone.Furnishings.Clear();
            zone.Furnishings.Add(new FurnishingDef{Id="dash-wall",Kind="barrel",X=17,Y=16,Width=1,Height=1,Rise=28,Solid=true});
            Need(WorldMap.Fits(zone,p.Position),"Dash fixture starts inside a wall.");
            var result=realm.Execute(p.Id,Dash(realm,p.Id)); Need(result.Ok,result.Message); p=realm.Player(p.Id);
            Need(p.Position.X<17-WorldMap.ActorRadius && WorldMap.Fits(zone,p.Position),"Dash crossed solid furniture.");
            Need(!p.Statuses.Any(s=>s.Kind.Contains("invulner")),"Dash granted an invulnerability effect.");
            realm.State.Time+=1; p.Position=new Point(16.749,16.5);
            string before=Json(realm.State);
            Need(!realm.Execute(p.Id,Dash(realm,p.Id)).Ok && Json(realm.State)==before,"A fully blocked dash consumed mana or state.");
        });
        Test("Repeated dashes can exhaust mana despite ordinary regeneration and survive save roundtrip",()=>
        {
            var (realm,id,start)=Fixture(); realm.Active.Add(id); int count=0;
            for(int attempt=0;attempt<30;attempt++)
            {
                var p=realm.Player(id);
                var result=realm.Execute(id,Dash(realm,id,count%2==0?1:-1));
                if(!result.Ok) { Need(result.Message.Contains("mana"),result.Message); break; }
                count++;
                for(int tick=0;tick<14;tick++) realm.Tick(.05);
            }
            Need(count>=2&&count<20,"Repeated dashes did not consume a finite mana reserve.");
            var current=realm.Player(id); var saved=Wire.Copy(current);
            Need(Json(saved)==Json(current),"Dash position, mana or cooldown changed on roundtrip.");
            Need(current.Position.Distance(start)<=2.51,"Repeated alternating dashes accumulated excess travel.");
        });
        Test("Early grades have lower use gates, while level twenty and all recipes remain unchanged",()=>
        {
            foreach(var tier in data.EquipmentTiers)
            foreach(string id in tier.Entries.Values)
            {
                var item=data.Item(id); int gate=BeginnerProgression.EquipmentRequirement(item);
                int expected=tier.Level switch {1=>1,5=>3,10=>6,15=>10,_=>tier.Level};
                Need(gate==expected,"Unexpected use gate: "+id);
                Need(item.Requirement==tier.Level,"The saved item grade was rewritten.");
            }
            Need(BeginnerProgression.EquipmentRequirement(data.Item("tin_bar"))==data.Item("tin_bar").Requirement,"Material requirements changed.");
        });
        Test("Overall early growth is monotone, preserves raw XP and never lowers an existing level",()=>
        {
            var p=new Character(); int previous=1;
            long cap=60*Progression.Threshold(100);
            foreach(long xp in new long[]{0,1,20,100,500,1000,5000,10000,20000,100000,500000,1000000,10000000,100000000,cap})
            {
                p.SkillXp.Clear(); long left=xp;
                foreach(var skill in data.Skills) { long share=Math.Min(left,Progression.Threshold(100)); p.SkillXp[skill.Id]=share;left-=share; }
                string before=Json(p.SkillXp); int level=Progression.PlayerLevel(p);
                int legacy=Math.Clamp(1+(int)Math.Floor(199*Math.Pow(xp/(double)cap,.30)),1,200);
                Need(level>=previous&&level>=legacy&&level<=200,"Overall growth decreases or exceeds its cap.");
                Need(Json(p.SkillXp)==before,"Computing a level changed saved XP."); previous=level;
                if(xp==10000) Need(level>=20,"Early overall level twenty still needs the old half-million XP.");
            }
            Need(previous==200,"Maximum skill progress no longer reaches the player cap.");
        });
        Console.WriteLine($"JOURNEY CONTROLS: {passed} groups passed; total failures {failures.Count}.");
    }
}
