using System.Text.Json;
using Kairnfall.Core;

/// <summary>Disposable realm fixtures for crafting access. No production saves are loaded.</summary>
internal static class CraftStationChecks
{
    public static void Run(Catalog source, List<string> failures)
    {
        int passed = 0;
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS CRAFT ACCESS: " + name); }
            catch (Exception error) { failures.Add(name); Console.WriteLine("FAIL CRAFT ACCESS: " + name + ": " + error.Message); }
        }
        foreach (bool ownedStation in new[] { false, true })
        {
            Test((ownedStation ? "Owned workbench" : "NPC forge") + " requires a clear approach and retains materials on rejection", () =>
            {
                var data = Wire.Copy(source);
                var zone = data.Zones.First(z => z.Kind == "interior" && data.Npcs.Any(n => n.Zone == z.Id && n.Station == "forge"));
                string station = ownedStation ? "workbench" : "forge";
                var staff = data.Npcs.Where(n => n.Zone == zone.Id).ToArray();
                foreach (var npc in staff) npc.Station = "";
                if (!ownedStation) { staff[0].Station = station; staff[0].Position = new Point(16.5,16.5); }
                var barrier = new FurnishingDef { Id = zone.Id + "/craft-access-fixture", Kind = "barrel", X = 15, Y = 16,
                    Width = 1, Height = 1, Rise = 28, Solid = true };
                zone.Furnishings.Add(barrier);
                var realm = new RealmEngine(data);
                var player = realm.CreateCharacter("craft-access-fixture", "Station Tester", "vanguard", new());
                string id = player.Id;
                foreach (var skill in data.Skills) player.SkillXp[skill.Id] = Progression.Threshold(100);
                player.Zone = zone.Id; player.Position = new Point(14.5,16.5); player.Inventory.Clear(); player.Equipment.Clear();
                Need(WorldMap.Fits(zone,player.Position) && WorldMap.Fits(zone,new Point(16.5,16.5)), "Fixture endpoints must be valid floor.");
                Need(!WorldMap.LineOfSight(zone,player.Position,new Point(16.5,16.5)), "Fixture must obstruct the station.");
                var recipe = data.Recipes.First(r => r.Station == station && data.Item(r.Output).Type != "structure");
                foreach (var ingredient in recipe.Ingredients)
                    Items.Add(player.Inventory,Items.Create(data,ingredient.Key,ingredient.Value),data);
                if (ownedStation)
                {
                    Need(data.Items.Any(item => item.Id == "structure_" + station), "Owned station must have a real construction template.");
                    realm.State.Nodes["craft-access-station"] = new WorldNode { Id = "craft-access-station", Template = "structure_" + station,
                        Owner = id, Zone = zone.Id, Position = new Point(16.5,16.5) };
                }
                string before = Json(realm.State);
                var blocked = realm.Execute(id,new GameCommand { Kind = "craft", Item = recipe.Id, Sequence = player.LastAction + 1 });
                Need(!blocked.Ok && Json(realm.State) == before, "Blocked crafting must retain materials, sequence, cooldown and rewards.");
                zone.Furnishings.Remove(barrier);
                player = realm.Player(id);
                Need(WorldMap.LineOfSight(zone,player.Position,new Point(16.5,16.5)), "Removing the barrier must restore a clear approach.");
                if (ownedStation)
                {
                    realm.State.Nodes["craft-access-station"].Owner = "another-player";
                    before = Json(realm.State);
                    var foreign = realm.Execute(id,new GameCommand { Kind = "craft", Item = recipe.Id, Sequence = player.LastAction + 1 });
                    Need(!foreign.Ok && Json(realm.State) == before, "Another player's station must not grant crafting access.");
                    realm.State.Nodes["craft-access-station"].Owner = id; player = realm.Player(id);
                }
                var allowed = realm.Execute(id,new GameCommand { Kind = "craft", Item = recipe.Id, Sequence = player.LastAction + 1 });
                Need(allowed.Ok, "Clear eligible crafting failed: " + allowed.Message);
                Need(Items.Count(realm.Player(id),recipe.Output) == recipe.Quantity, "Clear crafting must produce its exact recipe output.");
                Need(Items.Validate(realm.State,data).Count == 0, "Crafting must retain item ownership invariants.");
            });
        }
        Console.WriteLine($"CRAFT ACCESS CONTRACT: {passed} groups passed; total probe failures {failures.Count}.");
    }
}
