using Kairnfall.Core;

public static class ItemDropCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        (RealmEngine Realm, Character Player, Item Item) Fixture()
        {
            var realm = new RealmEngine(data); var player = realm.CreateCharacter("drop-account", "Drop Fixture", "vanguard", new());
            realm.Active.Add(player.Id); var item = Items.Create(data, "river_trout", 3);
            Items.Add(player.Inventory, item, data); return (realm, player, player.Inventory.First(x => x.Template == "river_trout"));
        }
        CommandResult Send(RealmEngine realm, Character player, string kind, string item = "", int amount = 1, string target = "")
            => realm.Execute(player.Id, new() { Kind = kind, Item = item, Amount = amount, Target = target, Sequence = realm.Player(player.Id).LastAction + 1 });
        test("Whole item drop preserves identity ownership and metadata", () =>
        {
            var (realm, player, item) = Fixture(); item.Durability = 81; item.Element = Element.Frost;
            item.Affixes.Add(new() { Name = "Saved affix", Stat = "health", Value = 2 });
            var expected = Wire.Copy(item); long gold = player.Gold;
            Check(Send(realm, player, "drop", item.Id, item.Quantity).Ok, "Whole drop rejected.");
            var pile = realm.Loot.Values.Single();
            Check(!player.Inventory.Any(x => x.Id == item.Id) && pile.Items.Single().Id == item.Id, "Whole drop duplicated or replaced the item ID.");
            Check(System.Text.Json.JsonSerializer.Serialize(pile.Items.Single(), Wire.Json) == System.Text.Json.JsonSerializer.Serialize(expected, Wire.Json), "Dropping changed item metadata.");
            Check(pile.Owner == player.Id && pile.Position == player.Position && pile.Zone == player.Zone && pile.Gold == 0 && player.Gold == gold, "Dropping changed ownership, position or gold.");
            Check(pile.PublicAt == realm.State.Time + 60 && pile.Expires == realm.State.Time + LootPile.LifetimeSeconds, "Dropping bypassed normal owned-loot timers.");
        });
        test("Partial item drop splits one quantity and leaves the original stack ID", () =>
        {
            var (realm, player, item) = Fixture();
            Check(Send(realm, player, "drop", item.Id, 1).Ok, "Partial drop rejected.");
            var split = realm.Loot.Values.Single().Items.Single();
            Check(Items.Owned(player, item.Id).Quantity == 2 && split.Quantity == 1 && split.Id != item.Id, "Partial drop did not conserve quantity with a unique split ID.");
            Check(Send(realm, player, "loot", target: realm.Loot.Keys.Single()).Ok && Items.Count(player, item.Template) == 3, "Pickup did not restore the quantity.");
        });
        test("Invalid and equipped item drops roll back without losing possessions", () =>
        {
            var (realm, player, item) = Fixture();
            foreach (int quantity in new[] { -1, 0, 4, int.MaxValue })
            {
                Check(!Send(realm, player, "drop", item.Id, quantity).Ok, "Invalid drop accepted."); player = realm.Player(player.Id);
                Check(Items.Owned(player, item.Id).Quantity == 3 && realm.Loot.Count == 0, "Rejected drop changed possessions.");
            }
            string weapon = player.Equipment["weapon"];
            Check(!Send(realm, player, "drop", weapon).Ok, "Equipped item was dropped."); player = realm.Player(player.Id);
            Check(player.Equipment["weapon"] == weapon && player.Inventory.Any(x => x.Id == weapon) && realm.Loot.Count == 0, "Rejected equipment drop changed ownership.");
        });
        test("Replayed drop cannot duplicate ground items or consume another quantity", () =>
        {
            var (realm, player, item) = Fixture();
            var request = new GameCommand { Kind = "drop", Item = item.Id, Amount = 1, Sequence = player.LastAction + 1 };
            Check(realm.Execute(player.Id, request).Ok && realm.Execute(player.Id, request).Ok, "A confirmed drop receipt was not replayable.");
            Check(realm.Loot.Count == 1 && Items.Owned(player, item.Id).Quantity == 2, "Replay duplicated a drop.");
        });
        test("Dropped loot remains reserved and survives the existing saved-realm boundary", () =>
        {
            var (realm, player, item) = Fixture(); Check(Send(realm, player, "drop", item.Id, 3).Ok, "Drop rejected.");
            var other = realm.CreateCharacter("drop-other", "Other Drop Hero", "vanguard", new());
            Check(!Send(realm, other, "loot", target: realm.Loot.Keys.Single()).Ok, "Foreign player took reserved dropped loot.");
            var loaded = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            var pile = loaded.Loot.Values.Single();
            Check(pile.Items.Single().Id == item.Id && pile.Owner == player.Id && pile.PublicAt == realm.Loot.Values.Single().PublicAt && pile.Expires == realm.Loot.Values.Single().Expires, "Save boundary changed drop identity or timers.");
            Check(Send(loaded, loaded.Player(player.Id), "loot", target: pile.Id).Ok, "Owner could not recover saved dropped loot.");
            Check(loaded.Player(player.Id).Inventory.Any(x => x.Id == item.Id && x.Quantity == 3), "Recovery changed the whole stack identity.");
        });
    }
}
