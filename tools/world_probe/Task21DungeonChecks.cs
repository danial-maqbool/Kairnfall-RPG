using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task21DungeonChecks
{
    [ModuleInitializer]
    internal static void VerifyTask21Dungeons()
    {
        const string path="content/catalog.json";
        if(!File.Exists(path))throw new InvalidDataException("Task 21 checks require content/catalog.json.");
        var data=Catalog.Load(path);var failures=new List<string>();int passed=0;
        void Need(bool value,string message){if(!value)throw new InvalidOperationException(message);}
        void Check(string name,Action body){try{body();passed++;Console.WriteLine("PASS TASK21 DUNGEONS: "+name);}catch(Exception e){failures.Add(name+": "+e.Message);Console.WriteLine("FAIL TASK21 DUNGEONS: "+name+": "+e.Message);}}
        string[] selected=["broken_mill","silken_tollhouse","sunken_foundry","glasswing_grotto"];

        Check("compact encounter wings deepen existing entrances without overworld growth",()=>
        {
            var surface=data.Zones.Where(z=>z.Kind=="wilderness"&&z.Layer=="Surface").ToArray();
            Need(surface.Length==20&&surface.Sum(z=>(long)z.Width*z.Height)==2_048_000,"Task 21 changed the overworld footprint.");
            foreach(string id in selected)
            {
                var boss=data.Zone(id);var threshold=data.Zone(id+"_threshold");var gauntlet=data.Zone(id+"_gauntlet");
                Need(boss.Boss!=""&&data.Mob(boss.Boss).Boss,"Canonical boss identity changed for "+id);
                Need(threshold.Kind=="dungeon"&&gauntlet.Kind=="dungeon"&&threshold.Width==64&&threshold.Height==64&&gauntlet.Width==64&&gauntlet.Height==64,"Compact room dimensions/kind drifted for "+id);
                Need(threshold.Boss==""&&gauntlet.Boss=="","Pre-boss rooms must not duplicate the major boss.");
                Need(gauntlet.Species.Select(data.Mob).Any(m=>m.Elite),"Elite encounter beat missing for "+id);
                Need(threshold.Exits.Any(e=>e.Target==gauntlet.Id)&&gauntlet.Exits.Any(e=>e.Target==boss.Id)&&boss.Exits.Any(e=>e.Target==gauntlet.Id),"Boss is not the final room in the compact chain for "+id);
                Need(data.Zones.Where(z=>z.Exits.Any(e=>e.Target==threshold.Id)).Any(z=>z.Id!=gauntlet.Id),"Existing world entrance no longer reaches compact chain for "+id);
            }
        });

        Check("abandoned and leashed boss encounters clear transient combat state",()=>
        {
            var realm=new RealmEngine(data);var p=realm.CreateCharacter("task21-abandon","Dungeon Reset Tester","vanguard",new());realm.Active.Add(p.Id);
            var zone=data.Zone("silken_tollhouse");var boss=realm.State.Creatures[zone.Id+"/boss"];var def=data.Mob(boss.Template);
            boss.Health=def.Health*.4;boss.Phase=1;boss.AttackStep=2;boss.Target=p.Id;boss.Threat[p.Id]=50;
            string addId=boss.Id+"/add/check";realm.State.Creatures[addId]=new(){Id=addId,Template=zone.Species[0],Zone=zone.Id,Position=boss.Home,Home=boss.Home,Health=10,Target=p.Id};
            realm.State.Telegraphs.Add(new(){Zone=zone.Id,Source=boss.Id,Position=boss.Home,Shape="circle",Radius=2,Power=10,Resolves=realm.State.Time+5});
            p.Zone="kingsmeadow";p.Position=data.Zone("kingsmeadow").Spawn;realm.Tick(.1);realm.Tick(.1);
            Need(boss.Health==def.Health&&boss.Position==boss.Home&&boss.Phase==0&&boss.AttackStep==0&&boss.Threat.Count==0&&boss.Target=="","Abandoned boss did not reset atomically.");
            Need(!realm.State.Creatures.ContainsKey(addId)&&!realm.State.Telegraphs.Any(t=>t.Source==boss.Id),"Abandoned boss left adds or telegraphs behind.");

            p.Zone=zone.Id;p.Position=boss.Home;boss.Health=def.Health*.5;boss.Phase=1;boss.AttackStep=1;boss.Threat[p.Id]=5;boss.Position=new(boss.Home.X+30,boss.Home.Y);
            realm.Tick(.1);realm.Tick(.1);
            Need(boss.Health==def.Health&&boss.Position==boss.Home&&boss.Phase==0&&boss.AttackStep==0&&boss.Threat.Count==0,"Leashed boss did not use the clean reset path.");
        });

        Check("multiplayer boss kill removes adds and remains exactly-once",()=>
        {
            var realm=new RealmEngine(data);var a=realm.CreateCharacter("task21-a","Boss Tester A","vanguard",new());var b=realm.CreateCharacter("task21-b","Boss Tester B","vanguard",new());
            var zone=data.Zone("broken_mill");var boss=realm.State.Creatures[zone.Id+"/boss"];string addId=boss.Id+"/add/check";
            a.Zone=zone.Id;b.Zone=zone.Id;a.Position=boss.Home;b.Position=boss.Home;realm.Active.Add(a.Id);realm.Active.Add(b.Id);boss.Health=1;boss.Position=boss.Home;boss.Threat[b.Id]=1;
            realm.State.Creatures[addId]=new(){Id=addId,Template=zone.Species[0],Zone=zone.Id,Position=boss.Home,Home=boss.Home,Health=10,Target=a.Id};
            int generation=boss.Generation,piles=realm.Loot.Count,aKills=a.Bestiary.GetValueOrDefault(boss.Template),bKills=b.Bestiary.GetValueOrDefault(boss.Template);
            var command=new GameCommand{Kind="attack",Target=boss.Id,Sequence=a.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};var result=realm.Execute(a.Id,command);Need(result.Ok,result.Message);
            Need(boss.Health==0&&boss.Generation==generation+1,"Boss death did not advance exactly one generation.");
            Need(!realm.State.Creatures.ContainsKey(addId),"Boss death left summoned adds alive.");
            Need(realm.Loot.Count==piles+1,"Boss death did not create exactly one authoritative loot pile.");
            Need(a.Bestiary.GetValueOrDefault(boss.Template)==aKills+1&&b.Bestiary.GetValueOrDefault(boss.Template)==bKills+1,"Both nearby contributors did not receive boss credit.");
            var replay=realm.Execute(a.Id,command);Need(replay.Ok,"Idempotent boss-kill replay lost its receipt.");
            Need(realm.Loot.Count==piles+1&&boss.Generation==generation+1,"Replayed boss kill duplicated loot or completion.");
        });

        Console.WriteLine($"TASK21 DUNGEON DEPTH: {passed} checks passed; {failures.Count} failed.");
        if(failures.Count>0)throw new InvalidDataException("Task 21 dungeon regression failed: "+string.Join(" | ",failures));
    }
}
