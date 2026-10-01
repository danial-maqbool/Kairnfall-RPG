using Kairnfall.Core;

public static class ChestLootCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        (RealmEngine Realm, Character Player, Chest Chest) Fixture()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("chest-test", "Chest Tester", "vanguard", new());
            var chest = realm.State.Chests.Values.First(x => x.Zone == player.Zone && x.Kind == "weathered");
            player.Position = chest.Position;
            return (realm, player, chest);
        }
        test("Ordinary chest pools preserve boss journey and regional reward identities", () =>
        {
            var special = data.Items.Where(x => x.Tags.Any(t => t is "boss_unique" or "opening_reward" or "exploration_unique")).ToArray();
            Check(special.Any(x => x.Tags.Contains("boss_unique")) && special.Any(x => x.Tags.Contains("opening_reward"))
                && special.Any(x => x.Tags.Contains("exploration_unique")), "Restricted reward fixture is incomplete.");
            for (int requirement = 1; requirement <= 100; requirement++)
            {
                var actual = ChestRewardRules.EquipmentCandidates(data, requirement).Select(x => x.Id).ToHashSet();
                var ordinary = data.Items.Where(x => x.Slot != "" && x.Type != "tool"
                    && x.Requirement >= Math.Max(1, requirement - 20) && x.Requirement <= Math.Min(100, requirement + 10)
                    && !special.Any(s => s.Id == x.Id)).Select(x => x.Id).ToHashSet();
                Check(actual.SetEquals(ordinary) && actual.Count > 0, "Ordinary reward coverage changed at requirement " + requirement);
                Check(!special.Any(x => actual.Contains(x.Id)), "Restricted reward entered ordinary chest pool.");
            }
        });
        test("Chest reports actual rewards and replay preserves the same result and possessions", () =>
        {
            var (realm, player, chest) = Fixture(); var before = player.Inventory.Select(x => x.Id).ToHashSet(); long gold = player.Gold;
            var command = new GameCommand { Kind = "chest", Target = chest.Id, Sequence = player.LastAction + 1 };
            var result = realm.Execute(player.Id, command); Check(result.Ok, result.Message);
            var awarded = player.Inventory.Where(x => !before.Contains(x.Id)).ToArray();
            Check(awarded.Length == 1 && ChestRewardRules.EquipmentCandidates(data, chest.Requirement).Any(x => x.Id == awarded[0].Template), "Chest did not grant one ordinary equipment reward.");
            Check(result.Message.Contains(awarded[0].Rarity + " " + data.Item(awarded[0].Template).Name)
                && result.Message.Contains((player.Gold - gold) + " gold"), "Reward feedback disagreed with inventory/currency.");
            string possessions = System.Text.Json.JsonSerializer.Serialize(player.Inventory, Wire.Json); long after = player.Gold;
            var replay = realm.Execute(player.Id, command);
            Check(replay.Ok && replay.Message == result.Message && player.Gold == after
                && System.Text.Json.JsonSerializer.Serialize(player.Inventory, Wire.Json) == possessions, "Chest replay changed rewards or feedback.");
        });
        test("Full backpack rejects locked chest without spending its key gold or cooldown", () =>
        {
            var (realm, player, chest) = Fixture(); chest.Kind = "locked"; chest.Requirement = 1;
            // Leave a key in its occupied slot after unlocking; consuming the last
            // key legitimately creates room and should allow a full-bag opening.
            Items.Add(player.Inventory, Items.Create(data, "lockpick"), data);
            int keys = Items.Count(player, "lockpick");
            while (player.Inventory.Count < Items.InventoryCapacity) Items.Add(player.Inventory, Items.Create(data, data.Class(player.Class).Weapon), data);
            long gold = player.Gold; long sequence = player.LastAction; double ready = chest.ReadyAt;
            var result = realm.Execute(player.Id, new() { Kind = "chest", Target = chest.Id, Sequence = sequence + 1 });
            Check(!result.Ok, "Full backpack accepted chest contents."); player = realm.Player(player.Id);
            Check(player.Gold == gold && Items.Count(player, "lockpick") == keys && player.LastAction == sequence
                && realm.State.Chests[chest.Id].ReadyAt == ready && !player.Cooldowns.ContainsKey("chest"), "Failed chest lost keys/gold or consumed reward readiness.");
        });
        test("Runic chest rolls back its first reward when the second reward cannot fit", () =>
        {
            var (realm, player, chest) = Fixture(); chest.Kind = "runic"; chest.Requirement = 1;
            player.Inventory.RemoveAll(x => data.Item(x.Template).Type == "rune");
            while (player.Inventory.Count < Items.InventoryCapacity - 1) Items.Add(player.Inventory, Items.Create(data, data.Class(player.Class).Weapon), data);
            string inventory = System.Text.Json.JsonSerializer.Serialize(player.Inventory, Wire.Json);
            string skills = System.Text.Json.JsonSerializer.Serialize(player.SkillXp, Wire.Json);
            long gold = player.Gold; long sequence = player.LastAction;
            var result = realm.Execute(player.Id, new() { Kind = "chest", Target = chest.Id, Sequence = sequence + 1 });
            Check(!result.Ok, "Runic chest discarded a rune or accepted contents without room for both rewards."); player = realm.Player(player.Id);
            Check(player.Gold == gold && player.LastAction == sequence && realm.State.Chests[chest.Id].ReadyAt == 0
                && !player.Cooldowns.ContainsKey("chest") && System.Text.Json.JsonSerializer.Serialize(player.Inventory, Wire.Json) == inventory
                && System.Text.Json.JsonSerializer.Serialize(player.SkillXp, Wire.Json) == skills, "Rejected second reward left a partial equipment grant, training or spent readiness.");
            player.Inventory.RemoveAt(player.Inventory.Count - 1);
            Check(realm.Execute(player.Id, new() { Kind = "chest", Target = chest.Id, Sequence = sequence + 1 }).Ok
                && player.Inventory.Count == Items.InventoryCapacity && player.Inventory.Any(x => data.Item(x.Template).Type == "rune"), "Making space did not recover both runic rewards.");
        });
        test("Expired ground loot is rejected before any cleanup tick", () =>
        {
            foreach (double expires in new[] { 0d, -1d })
            {
                var (realm, player, _) = Fixture();
                var item = Items.Create(data, "river_trout", 2);
                var pile = new LootPile { Zone = player.Zone, Position = player.Position, Owner = player.Id, Items = [item], Gold = 31, Expires = expires };
                realm.Loot[pile.Id] = pile; long gold = player.Gold; int fish = Items.Count(player, item.Template); long sequence = player.LastAction;
                var result = realm.Execute(player.Id, new() { Kind = "loot", Target = pile.Id, Sequence = sequence + 1 });
                Check(!result.Ok, "Expired/nonfinite loot was collected before sweep."); player = realm.Player(player.Id);
                Check(player.Gold == gold && Items.Count(player, item.Template) == fish && player.LastAction == sequence, "Rejected loot changed possessions or action sequence.");
            }
            var (freshRealm, freshPlayer, _) = Fixture();
            var fresh = new LootPile { Zone = freshPlayer.Zone, Position = freshPlayer.Position, Owner = freshPlayer.Id, Gold = 31, Expires = .01 };
            freshRealm.Loot[fresh.Id] = fresh; long startingGold = freshPlayer.Gold;
            Check(freshRealm.Execute(freshPlayer.Id, new() { Kind = "loot", Target = fresh.Id, Sequence = freshPlayer.LastAction + 1 }).Ok
                && freshPlayer.Gold == startingGold + 31 && !freshRealm.Loot.ContainsKey(fresh.Id), "Fresh owner loot was lost or not removed after collection.");
        });
    }
}
