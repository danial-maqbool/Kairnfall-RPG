using Kairnfall.Core;
using System.Text.Json;

var catalog = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(args.Length > 0 ? args[0] : "content/catalog.json"), Wire.Json)!;
var failures = new List<string>();
int walls = 0, destinations = 0;
foreach (var zone in catalog.Zones)
{
    foreach (var building in zone.Buildings)
        for (int y = building.Y + 1; y < building.Y + building.Height; y++)
            for (int x = building.X; x < building.X + building.Width; x++)
            {
                if (x == building.X + building.Width / 2 && y == building.Y + building.Height - 1) continue;
                walls++;
                if (WorldMap.Walkable(zone, new Point(x + .5, y + .5))) failures.Add($"Walkable masonry {zone.Id}/{building.Id} ({x},{y})");
            }
    // Flood actual actor-fitting tile centers; graph edges alone cannot prove accessibility.
    var reached = new HashSet<(int X, int Y)>();
    var queue = new Queue<(int X, int Y)>();
    queue.Enqueue(((int)zone.Spawn.X, (int)zone.Spawn.Y));
    while (queue.TryDequeue(out var tile))
    {
        if (tile.X < 1 || tile.Y < 1 || tile.X >= zone.Width - 1 || tile.Y >= zone.Height - 1 || reached.Contains(tile)) continue;
        if (!WorldMap.Fits(zone, new Point(tile.X + .5, tile.Y + .5))) continue;
        reached.Add(tile);
        queue.Enqueue((tile.X + 1, tile.Y)); queue.Enqueue((tile.X - 1, tile.Y));
        queue.Enqueue((tile.X, tile.Y + 1)); queue.Enqueue((tile.X, tile.Y - 1));
    }
    void Require(Point at, string label)
    {
        destinations++;
        if (!WorldMap.Fits(zone, at) || !reached.Contains(((int)at.X, (int)at.Y))) failures.Add($"Unreachable {zone.Id}/{label} ({at.X},{at.Y})");
    }
    Require(zone.Spawn, "spawn");
    foreach (var exit in zone.Exits) Require(exit.Position, "exit " + exit.Id);
    foreach (var source in catalog.Zones)
        foreach (var exit in source.Exits.Where(e => e.Target == zone.Id)) Require(exit.Arrival, "arrival " + exit.Id);
    foreach (var building in zone.Buildings) Require(new Point(building.X + building.Width / 2 + .5, building.Y + building.Height - .5), "door " + building.Id);
    foreach (var npc in catalog.Npcs.Where(n => n.Zone == zone.Id)) Require(npc.Position, "service " + npc.Id);
}
foreach (var failure in failures) Console.WriteLine("FAIL " + failure);
Console.WriteLine($"WORLD PROBE: {catalog.Zones.Count} zones; {walls} masonry tiles; {destinations} destinations; {failures.Count} failures.");
int saveTests = 0;
void SaveTest(string name, Action check)
{
    try { check(); saveTests++; Console.WriteLine("PASS " + name); }
    catch (Exception error) { failures.Add(name); Console.WriteLine("FAIL " + name + ": " + error.Message); }
}
void Assert(bool condition, string message) { if (!condition) throw new Exception(message); }
string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
SaveTest("Legacy character recovery preserves progress and is idempotent after save roundtrip", () =>
{
    var realm = new RealmEngine(catalog);
    var player = realm.CreateCharacter("migration-fixture", "Migration Hero", "vanguard", new());
    player.Zone = "thornhollow"; player.Position = new(64.5, 88.5);
    player.Gold = 12345; player.SkillXp["mining"] = 500;
    player.Quests["fixture-progress"] = new() { Counts = [2, 7] };
    player.CompletedQuests.Add("fixture-completed"); player.Reputation["circle"] = 23;
    var valid = realm.CreateCharacter("migration-fixture", "Unchanged Hero", "vanguard", new());
    var unchanged = Json(valid);
    var before = Wire.Copy(player);
    var loaded = new RealmEngine(catalog, Wire.Copy(realm.State));
    var recovered = loaded.Player(player.Id);
    Assert(WorldMap.Fits(catalog.Zone(recovered.Zone), recovered.Position), "Recovered character is still blocked.");
    Assert(recovered.Position != before.Position && loaded.EconomicDirty, "Recovery was not recorded for persistence.");
    before.Position = recovered.Position;
    Assert(Json(before) == Json(recovered), "Recovery changed character progress, possessions, or identity.");
    Assert(Json(loaded.Player(valid.Id)) == unchanged, "Valid character changed.");
    var saved = Json(loaded.State);
    var reloaded = new RealmEngine(catalog, Wire.Copy(loaded.State));
    Assert(saved == Json(reloaded.State) && !reloaded.EconomicDirty, "Reload was not idempotent.");
});
SaveTest("Corrupt character positions fail closed without partial migration", () =>
{
    foreach (var invalid in new[] { new Point(-1, 4), new Point(999999, 4), new Point(double.MaxValue, 4), new Point(59.5, 85.5), new Point(double.NaN, 3) })
    {
        var state = new RealmState();
        state.Characters["recoverable"] = new() { Id = "recoverable", Zone = "thornhollow", Position = new(64.5, 88.5) };
        state.Characters["corrupt"] = new() { Id = "corrupt", Zone = "dawnreach", Position = invalid };
        bool rejected = false;
        try { _ = new RealmEngine(catalog, state); } catch (InvalidDataException) { rejected = true; }
        Assert(rejected, "Corrupt character accepted: " + invalid);
        Assert(state.Characters["recoverable"].Position == new Point(64.5, 88.5), "Failed load partly migrated supplied state.");
    }
});
SaveTest("Persisted world entity recovery preserves identity, timers, and ownership", () =>
{
    var state = new RealmEngine(catalog).State;
    state.Creatures["migration-creature"] = new() { Id = "migration-creature", Template = "field_rat", Zone = "thornhollow", Position = new(64.5, 88.5), Home = new(64.5, 88.5), Health = 7, RespawnAt = 123, Owner = "fixture-owner" };
    state.Nodes["migration-node"] = new() { Id = "migration-node", Template = "copper_vein", Zone = "thornhollow", Position = new(64.5, 88.5), ReadyAt = 321, Owner = "fixture-owner" };
    state.Chests["migration-chest"] = new() { Id = "migration-chest", Zone = "thornhollow", Position = new(64.5, 88.5), ReadyAt = 456, Hidden = true };
    var before = Wire.Copy(state);
    var loaded = new RealmEngine(catalog, Wire.Copy(state)).State;
    var creature = loaded.Creatures["migration-creature"];
    Assert(WorldMap.Fits(catalog.Zone(creature.Zone), creature.Position) && WorldMap.Fits(catalog.Zone(creature.Zone), creature.Home), "Creature/home not recovered.");
    before.Creatures[creature.Id].Position = creature.Position; before.Creatures[creature.Id].Home = creature.Home;
    before.Nodes["migration-node"].Position = loaded.Nodes["migration-node"].Position;
    before.Chests["migration-chest"].Position = loaded.Chests["migration-chest"].Position;
    Assert(Json(before) == Json(loaded), "Migration changed non-position saved world data.");
});
SaveTest("Full legacy seeded world survives recovery and roundtrip", () =>
{
    // Reconstruct SeedWorld's unchanged placement rules with the historical tile policy.
    var legacyTile = typeof(WorldMap).GetMethod("TileAt", System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static,
        [typeof(ZoneDef), typeof(int), typeof(int), typeof(bool)])!.CreateDelegate<Func<ZoneDef, int, int, bool, Terrain>>();
    bool OldFits(ZoneDef zone, Point point) => new[] { -.24, .24 }.All(dx => new[] { -.24, .24 }.All(dy =>
        !WorldMap.IsSolid(legacyTile(zone, (int)Math.Floor(point.X + dx), (int)Math.Floor(point.Y + dy), true))));
    Point OldFree(ZoneDef zone, Point near)
    {
        for (int r = 0; r < 24; r++) for (int dy = -r; dy <= r; dy++) for (int dx = -r; dx <= r; dx++)
        {
            var point = new Point(Math.Floor(near.X) + dx + .5, Math.Floor(near.Y) + dy + .5);
            if (OldFits(zone, point)) return point;
        }
        return zone.Spawn;
    }
    var state = new RealmEngine(catalog).State;
    foreach (var zone in catalog.Zones)
    {
        int n = 0;
        foreach (var species in zone.Species)
        {
            double angle = n * 2.399;
            var point = OldFree(zone, new Point(zone.Spawn.X + Math.Cos(angle) * (zone.Kind == "city" ? 30 : 15), zone.Spawn.Y + Math.Sin(angle) * (zone.Kind == "city" ? 30 : 15)));
            var creature = state.Creatures[zone.Id + "/" + species]; creature.Position = creature.Home = point; n++;
        }
        if (zone.Boss != "") { var boss = state.Creatures[zone.Id + "/boss"]; boss.Position = boss.Home = OldFree(zone, new(zone.Spawn.X + 6, zone.Spawn.Y + 3)); }
        for (int i = 0; i < zone.Resources.Length; i++) for (int j = 0; j < 3; j++)
            state.Nodes[$"{zone.Id}/node/{i}/{j}"].Position = OldFree(zone, new(zone.Spawn.X - 12 + i * 3, zone.Spawn.Y + 7 + j * 4));
        for (int i = 0; i < 3; i++) state.Chests[$"{zone.Id}/chest/{i}"].Position = OldFree(zone, new(zone.Spawn.X + 10 + i * 6, zone.Spawn.Y - 8 - i * 3));
    }
    int creatures = state.Creatures.Values.Count(c => !WorldMap.Fits(catalog.Zone(c.Zone), c.Position));
    int homes = state.Creatures.Values.Count(c => !WorldMap.Fits(catalog.Zone(c.Zone), c.Home));
    int nodes = state.Nodes.Values.Count(c => !WorldMap.Fits(catalog.Zone(c.Zone), c.Position));
    int chests = state.Chests.Values.Count(c => !WorldMap.Fits(catalog.Zone(c.Zone), c.Position));
    var loaded = new RealmEngine(catalog, Wire.Copy(state));
    Assert(loaded.State.Creatures.Values.All(c => WorldMap.Fits(catalog.Zone(c.Zone), c.Position) && WorldMap.Fits(catalog.Zone(c.Zone), c.Home)), "Legacy seeded creature remains blocked.");
    Assert(loaded.State.Nodes.Values.All(c => WorldMap.Fits(catalog.Zone(c.Zone), c.Position)), "Legacy seeded node remains blocked.");
    Assert(loaded.State.Chests.Values.All(c => WorldMap.Fits(catalog.Zone(c.Zone), c.Position)), "Legacy seeded chest remains blocked.");
    var again = new RealmEngine(catalog, Wire.Copy(loaded.State));
    Assert(Json(loaded.State) == Json(again.State) && !again.EconomicDirty, "Full-world migration is not idempotent.");
    Console.WriteLine($"LEGACY SEEDED IMPACT: {creatures}/{state.Creatures.Count} creature positions, {homes} homes, {nodes}/{state.Nodes.Count} nodes, {chests}/{state.Chests.Count} chests recovered.");
});
SaveTest("Separately loaded loot preserves items, gold, ownership, and valid positions", () =>
{
    var realm = new RealmEngine(catalog);
    realm.Loot["legacy-loot"] = new() { Id = "legacy-loot", Zone = "thornhollow", Position = new(64.5, 88.5), Owner = "fixture-owner", Party = "fixture-party", Gold = 987, PublicAt = 321, Expires = 999, Items = [Items.Create(catalog, "healing_potion", 2)] };
    realm.Loot["valid-loot"] = new() { Id = "valid-loot", Zone = "wayfarers_rest", Position = catalog.Zone("wayfarers_rest").Spawn, Gold = 42 };
    var before = Wire.Copy(realm.Loot);
    realm.RecoverLegacyLootPositions();
    Assert(WorldMap.Fits(catalog.Zone("thornhollow"), realm.Loot["legacy-loot"].Position), "Loot remains blocked.");
    before["legacy-loot"].Position = realm.Loot["legacy-loot"].Position;
    Assert(Json(before) == Json(realm.Loot) && realm.EconomicDirty, "Loot recovery changed non-position data.");
    var reload = new RealmEngine(catalog, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
    reload.RecoverLegacyLootPositions();
    Assert(Json(realm.Loot) == Json(reload.Loot) && !reload.EconomicDirty, "Loot recovery is not idempotent.");
});
Console.WriteLine($"SAVE MIGRATION: {saveTests} passed; total probe failures {failures.Count}.");
FurnishingChecks.Run(catalog, failures);
GearProgressionChecks.Run(catalog,failures);
CraftStationChecks.Run(catalog,failures);
EquipmentMaintenanceChecks.Run(catalog,failures);
JourneyControlChecks.Run(catalog,failures);
HuntingGroundChecks.Run(catalog,failures);
return failures.Count == 0 ? 0 : 1;
