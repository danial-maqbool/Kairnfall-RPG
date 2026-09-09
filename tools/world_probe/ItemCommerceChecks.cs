using System.Text.Json;
using Kairnfall.Core;

internal static class ItemCommerceChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Test(string name, Action test)
        {
            try { test(); passed++; Console.WriteLine("PASS ITEM COMMERCE: " + name); }
            catch (Exception error) { failures.Add("ITEM COMMERCE: " + name); Console.WriteLine("FAIL ITEM COMMERCE: " + name + ": " + error); }
        }
        Test("Locked and banked equipment retains independent positive negative and unchanged stat deltas", () =>
        {
            var self = new Character(); var old = Items.Create(data, "copper_sword");
            old.Affixes = [new() { Stat = "vitality", Value = 6 }, new() { Stat = "luck", Value = 2 }];
            self.Inventory.Add(old); self.Equipment["weapon"] = old.Id;
            var item = Items.Create(data, "iron_sword", 1, Rarity.Rare);
            item.Affixes = [new() { Stat = "vitality", Value = 1 }, new() { Stat = "luck", Value = 2 }]; self.Bank.Add(item);
            string original = Json(self); var result = EquipmentComparison.Inspect(self, item, data);
            Need(result.Blockers.Any(x => x.StartsWith("Requires")) && result.Blockers.Any(x => x.Contains("backpack")), "Actual skill and storage blockers must be exposed.");
            Need(result.Stats.Single(x => x.Key == "vitality").Difference == -5, "Lost vitality was hidden or aggregated with another stat.");
            Need(result.Stats.Single(x => x.Key == "luck").Improvement == 0, "Equal stat acquired a comparison color.");
            Need(result.Stats.Single(x => x.Key == "item_power").Improvement > 0, "Better locked weapon power is not compared.");
            Need(Json(self) == original, "Inspection mutated the authoritative character.");
        });
        Test("Affixes runes missing stats and lower-is-better attack intervals are represented", () =>
        {
            Need(new ItemStatComparison("attack_interval", .6, -.2, true).Improvement == 1, "Faster interval is not an improvement.");
            Need(new ItemStatComparison("attack_interval", 1.2, .2, true).Improvement == -1, "Slower interval was presented as better.");
            var item = Items.Create(data, "copper_sword");
            var rune = data.Items.First(x => x.Type == "rune" && x.Stats.Count > 0);
            item.Runes.Add(new() { Template = rune.Id });
            var plain = EquipmentComparison.Values(Items.Create(data, "copper_sword"), data);
            var actual = EquipmentComparison.Values(item, data);
            foreach (var stat in rune.Stats) Need(Math.Abs(actual.GetValueOrDefault(stat.Key) - plain.GetValueOrDefault(stat.Key) - stat.Value) < .0001, "Rune bonus omitted.");
            var self = new Character(); var old = Items.Create(data, "copper_sword"); old.Affixes.Add(new() { Stat = "luck", Value = 8 });
            self.Inventory.Add(old); self.Equipment["weapon"] = old.Id;
            Need(EquipmentComparison.Inspect(self, item, data, false).Stats.Any(x => x.Key == "luck" && x.Difference == -8), "Missing new-item stat hides a loss.");
        });
        Test("Two-handed comparisons include removed shields and every simultaneous blocker", () =>
        {
            var self = new Character(); var weapon = Items.Create(data, "copper_sword");
            var shield = Items.Create(data, data.Items.First(x => x.Tags.Contains("shield") && x.Armor > 0).Id);
            self.Inventory.AddRange([weapon, shield]); self.Equipment["weapon"] = weapon.Id; self.Equipment["offhand"] = shield.Id;
            var two = Items.Create(data, data.Items.First(x => x.Slot == "weapon" && x.Tags.Contains("two_handed")).Id);
            var comparison = EquipmentComparison.Inspect(self, two, data, false);
            Need(comparison.Notices.Any(x => x.Contains(data.Item(shield.Template).Name)), "Removed shield is not named.");
            Need(comparison.Stats.Any(x => x.Key == "item_armor" && x.Difference < 0), "Shield armor loss was omitted.");
            self.Health = 0; two.Durability = 0;
            Need(EquipmentComparison.Inspect(self,two,data).Blockers.Count >= 3, "One blocker conceals other failures.");
        });
        // Bulk coverage changes only a copied fixture catalog; production stack and bag limits stay unchanged.
        data = Wire.Copy(data); data.Item("copper_ore").StackMax = 999;
        var realm = new RealmEngine(data);
        string id = realm.CreateCharacter("sale-fixture", "Sale Tester", "vanguard", new()).Id;
        var merchant = data.Npcs.First(x => x.Role == "provisioner" && x.Stock.Length > 0);
        var stackDef = data.Items.First(x => x.StackMax >= 150 && x.Value > 0 && x.Type != "quest");
        Character Reset()
        {
            var p = realm.Player(id); p.Inventory.Clear(); p.Bank.Clear(); p.Equipment.Clear();
            p.Zone = merchant.Zone; p.Position = merchant.Position; p.Health = 100; p.Gold = 20;
            return p;
        }
        GameCommand Sale(string item, int count, string? target = null) => new() { Kind = "sell", Item = item, Target = target ?? merchant.Id, Amount = count, Sequence = realm.Player(id).LastAction + 1 };
        void Rejected(GameCommand cmd)
        {
            string before = Json(realm.State); Need(!realm.Execute(id, cmd).Ok, "Invalid sale accepted.");
            Need(Json(realm.State) == before, "Rejected sale changed state.");
        }
        Test("Partial and full-stack sales use exact totals and replay cannot sell twice", () =>
        {
            var p = Reset(); var item = Items.Create(data, stackDef.Id, 150); p.Inventory.Add(item);
            long quote = MerchantSales.Quote(p,merchant,item,7,data), beforeGold = p.Gold;
            var partial = Sale(item.Id,7); Need(realm.Execute(id,partial).Ok,"Partial sale failed.");
            p = realm.Player(id); Need(p.Gold == beforeGold + quote && Items.Owned(p,item.Id).Quantity == 143,"Partial sale amount or gold incorrect.");
            string after = Json(realm.State); Need(realm.Execute(id,partial).Ok && Json(realm.State) == after,"Replay duplicated partial sale.");
            var all = Sale(item.Id,143); Need(realm.Execute(id,all).Ok,"Full stack above 99 was not supported.");
            Need(!realm.Player(id).Inventory.Any(x=>x.Id==item.Id),"Sell all left a hidden remainder.");
            Need(realm.Player(id).Gold == beforeGold + MerchantSales.UnitPrice(stackDef) * 150,"Sell-all total incorrect.");
            after = Json(realm.State); Need(realm.Execute(id,all).Ok && Json(realm.State)==after,"Full-stack replay duplicated gold.");
            Need(Items.Validate(realm.State,data).Count==0,"Sale broke inventory invariants.");
        });
        Test("Zero negative excessive equipped banked foreign and remote sales fail without mutations", () =>
        {
            var p = Reset(); var item = Items.Create(data,stackDef.Id,5); p.Inventory.Add(item);
            foreach(int count in new[]{0,-1,6,1000,int.MaxValue}) Rejected(Sale(item.Id,count));
            p = realm.Player(id); var weapon=Items.Create(data,"copper_sword");p.Inventory.Add(weapon);p.Equipment["weapon"]=weapon.Id;Rejected(Sale(weapon.Id,1));
            p=realm.Player(id);var banked=Items.Create(data,stackDef.Id);p.Bank.Add(banked);Rejected(Sale(banked.Id,1));
            Rejected(Sale(Guid.NewGuid().ToString("N"),1));
            p=realm.Player(id);p.Position=new Point(1,1);Rejected(Sale(item.Id,1));
        });
        Test("Merchant acceptance quest-item restrictions and the gold cap share the displayed validation", () =>
        {
            var p=Reset();var item=Items.Create(data,stackDef.Id,5);p.Inventory.Add(item);
            var other=data.Npcs.First(x=>x.Stock.Length>0&&x.Role!="provisioner"&&!x.Stock.Any(t=>data.Item(t).Type==stackDef.Type));
            p.Zone=other.Zone;p.Position=other.Position;Rejected(Sale(item.Id,1,other.Id));
            p=realm.Player(id);p.Zone=merchant.Zone;p.Position=merchant.Position;p.Gold=Items.GoldCap;Rejected(Sale(item.Id,1));
            p=Reset();var quest=data.Items.FirstOrDefault(x=>x.Type=="quest"||x.Value<=0);
            if(quest is not null) {var restricted=Items.Create(data,quest.Id);p.Inventory.Add(restricted);Rejected(Sale(restricted.Id,1));}
        });
        Console.WriteLine($"ITEM COMMERCE: {passed} groups passed; total failures {failures.Count}.");
    }
}
