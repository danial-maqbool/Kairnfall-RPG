using System.Text.Json;
using Kairnfall.Core;

/// <summary>Repair requests use the real authoritative transaction path and disposable state.</summary>
internal static class EquipmentMaintenanceChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed=0, toolsChecked=0;
        void Need(bool value,string message) { if(!value) throw new InvalidOperationException(message); }
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        void Test(string name,Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS MAINTENANCE: "+name); }
            catch(Exception error) { failures.Add(name); Console.WriteLine("FAIL MAINTENANCE: "+name+": "+error.Message); }
        }
        var realm=new RealmEngine(data);
        string owner=realm.CreateCharacter("maintenance-fixture","Maintenance Tester","vanguard",new()).Id;
        var smith=data.Npcs.First(n=>n.Role=="blacksmith");
        Character Reset()
        {
            var p=realm.Player(owner); p.Inventory.Clear(); p.Bank.Clear(); p.Equipment.Clear();
            p.Zone=smith.Zone; p.Position=smith.Position; p.Health=100; p.Gold=1_000_000;
            return p;
        }
        GameCommand Command(string item)=>new(){Kind="repair",Item=item,Sequence=realm.Player(owner).LastAction+1};
        long Cost(ItemDef def,int durability)=>Math.Max(1,(long)Math.Ceiling((100-durability)*Math.Max(1,def.Value)/500.0));
        void Rejected(GameCommand command,string reason)
        {
            string before=Json(realm.State);
            var result=realm.Execute(owner,command);
            Need(!result.Ok,reason+" was accepted.");
            Need(Json(realm.State)==before,reason+" changed state despite rejection.");
        }
        Test("All seven tools in every grade can be repaired without changing their identity or bonuses",()=>
        {
            var ids=data.EquipmentTiers.SelectMany(t=>t.Entries.Where(e=>e.Key.StartsWith("tool/",StringComparison.Ordinal)).Select(e=>e.Value)).Distinct().ToArray();
            Need(ids.Length==147,"Expected seven tools across 21 grades.");
            foreach(string template in ids)
            {
                var p=Reset(); var item=Items.Create(data,template,1,Rarity.Rare); item.Durability=0; p.Inventory.Add(item);
                var def=data.Item(template); var before=Wire.Copy(item); long gold=p.Gold;
                var command=Command(item.Id); var result=realm.Execute(owner,command);
                Need(result.Ok,template+": "+result.Message);
                p=realm.Player(owner); var restored=Items.Owned(p,item.Id); before.Durability=100;
                Need(Json(before)==Json(restored),"Repair changed non-durability item data: "+template);
                Need(p.Gold==gold-Cost(def,0),"Repair charged the wrong price: "+template);
                string completed=Json(realm.State); var replay=realm.Execute(owner,command);
                Need(replay.Ok&&Json(realm.State)==completed,"Replaying a repair charged twice: "+template);
                Need(Items.Validate(realm.State,data).Count==0,"Repair broke item ownership: "+template);
                toolsChecked++;
            }
        });
        Test("Equipment and tools retain the same partial-durability price rule",()=>
        {
            foreach(string template in new[]{"copper_sword","copper_pickaxe","aetherium_tool_pickaxe"})
            foreach(int durability in new[]{0,34,99})
            {
                var p=Reset(); var item=Items.Create(data,template); item.Durability=durability; p.Inventory.Add(item);
                p.Gold=Cost(data.Item(template),durability);
                var result=realm.Execute(owner,Command(item.Id));
                Need(result.Ok,"An exactly funded repair failed: "+template);
                Need(realm.Player(owner).Gold==0&&Items.Owned(realm.Player(owner),item.Id).Durability==100,"Repair amount or durability differs.");
            }
        });
        Test("Banked foreign full-durability and non-equipment items cannot be repaired",()=>
        {
            var p=Reset(); var item=Items.Create(data,"copper_pickaxe"); item.Durability=20; p.Bank.Add(item);
            Rejected(Command(item.Id),"Banked tool");
            var other=realm.CreateCharacter("maintenance-other","Other Repairer","vanguard",new());
            var foreign=Items.Create(data,"copper_pickaxe"); foreign.Durability=20; other.Inventory.Add(foreign);
            Reset(); Rejected(Command(foreign.Id),"Foreign tool");
            p=Reset(); item=Items.Create(data,"copper_pickaxe"); p.Inventory.Add(item);
            Rejected(Command(item.Id),"Undamaged tool");
            p=Reset(); item=Items.Create(data,"healing_potion"); item.Durability=20; p.Inventory.Add(item);
            Rejected(Command(item.Id),"Consumable");
        });
        Test("Repair still requires a living owner enough gold and a nearby blacksmith",()=>
        {
            foreach(string condition in new[]{"dead","poor","distant"})
            {
                var p=Reset(); var item=Items.Create(data,"aetherium_tool_pickaxe"); item.Durability=20; p.Inventory.Add(item);
                if(condition=="dead") p.Health=0;
                if(condition=="poor") p.Gold=0;
                if(condition=="distant")
                {
                    var zone=data.Zones.First(z=>z.Kind=="wilderness"&&!data.Npcs.Any(n=>n.Zone==z.Id&&n.Role=="blacksmith"));
                    p.Zone=zone.Id; p.Position=zone.Spawn;
                }
                Rejected(Command(item.Id),condition+" repair");
            }
        });
        Console.WriteLine($"EQUIPMENT MAINTENANCE: {passed} groups passed; {toolsChecked} tier tools repaired and replay-checked; total failures {failures.Count}.");
    }
}
