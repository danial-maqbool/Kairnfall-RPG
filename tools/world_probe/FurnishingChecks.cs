using System.Text.Json;
using Kairnfall.Core;

internal static class FurnishingChecks
{
    public static int Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS FURNISHING: " + name); }
            catch (Exception error) { failures.Add(name); Console.WriteLine("FAIL FURNISHING: " + name + ": " + error.Message); }
        }
        var rooms = data.Zones.Where(z => z.Kind == "interior").ToArray();
        Test("Every service interior has furniture and an open travel cross", () =>
        {
            Need(rooms.Length >= 4, "Missing service rooms.");
            foreach (var zone in rooms)
            {
                Need(zone.Furnishings.Count >= 10, "Sparse authored plan: " + zone.Id);
                int walkable = 0;
                for (int y = 3; y < zone.Height - 3; y++) for (int x = 3; x < zone.Width - 3; x++)
                {
                    var point = new Point(x + .5, y + .5);
                    if (WorldMap.Fits(zone, point)) walkable++;
                    if (Math.Abs(x - (int)zone.Spawn.X) <= 2 || Math.Abs(y - (int)zone.Spawn.Y) <= 2)
                        Need(WorldMap.Fits(zone, point), "Central circulation lane blocked: " + zone.Id);
                }
                Need(walkable >= (zone.Width - 6) * (zone.Height - 6) * .72, "Room is overfilled: " + zone.Id);
            }
        });
        Test("Furniture blocks its footprint while rugs preserve the original floor", () =>
        {
            foreach (var zone in data.Zones.Where(z => z.Furnishings.Count > 0))
                for (int y = 0; y < zone.Height; y++) for (int x = 0; x < zone.Width; x++)
                {
                    bool solid = zone.Furnishings.Any(f => f.Solid && f.Covers(x,y));
                    Terrain ground = WorldMap.GroundTileAt(zone,x,y), actual = WorldMap.TileAt(zone,x,y);
                    Need(solid ? actual == Terrain.Wall : actual == ground, "Unexpected collision change: " + zone.Id);
                    if (solid) Need(!WorldMap.IsSolid(ground), "Furniture hides pre-existing solid terrain.");
                }
        });
        Test("Movement and line of sight cannot pass through furniture", () =>
        {
            int approaches = 0;
            foreach (var zone in rooms)
                foreach (var f in zone.Furnishings.Where(f => f.Solid))
                {
                    var target = new Point(f.X + .5, f.Y + .5);
                    Need(!WorldMap.Fits(zone,target), "Furniture center is walkable.");
                    foreach (var step in new[] { new Point(-1,0),new Point(1,0),new Point(0,-1),new Point(0,1) })
                    {
                        var start = target.Add(step);
                        if (!WorldMap.Fits(zone,start)) continue;
                        approaches++;
                        var result = WorldMap.Move(zone,start,step.Scale(-1.25));
                        Need(WorldMap.Fits(zone,result), "Movement entered the furniture footprint.");
                        Need(!WorldMap.LineOfSight(zone,start,target), "Line of sight crosses furniture.");
                    }
                }
            Need(approaches > 50, "Movement fixture did not test enough approaches.");
        });
        Test("Saved occupants recover locally without losing any progress or identity", () =>
        {
            var realm = new RealmEngine(data);
            foreach (var zone in rooms)
            {
                var f = zone.Furnishings.First(f => f.Solid);
                var p = realm.CreateCharacter("furnishing-recovery-" + zone.Id, "Room" + realm.State.Characters.Count, "vanguard", new());
                p.Zone = zone.Id; p.Position = new Point(f.X + .5,f.Y + .5);
                p.Gold = 12345; p.SkillXp["mining"] = 500;
                p.Statuses.Add(new StatusEffect { Kind = "poison", Power = 3, Until = 120, Source = "fixture" });
                p.Quests["retained-progress"] = new QuestProgress { Counts = [2,7] };
            }
            var before = Wire.Copy(realm.State);
            var loaded = new RealmEngine(data,Wire.Copy(realm.State));
            foreach (var p in loaded.State.Characters.Values)
            {
                var old = before.Characters[p.Id];
                Need(WorldMap.Fits(data.Zone(p.Zone),p.Position), "Occupant remains blocked.");
                Need(old.Position.Distance(p.Position) <= 6, "Recovery moved the occupant too far.");
                old.Position = p.Position;
            }
            Need(Json(before) == Json(loaded.State), "Recovery altered non-position state.");
            Need(loaded.EconomicDirty, "Recovery must be persisted.");
            var again = new RealmEngine(data,Wire.Copy(loaded.State));
            Need(Json(again.State) == Json(loaded.State) && !again.EconomicDirty, "Recovery is not idempotent.");
        });
        Test("Loot on a newly furnished floor retains ownership rewards and timers", () =>
        {
            var realm = new RealmEngine(data);
            foreach (var zone in rooms)
            {
                var f = zone.Furnishings.First(f => f.Solid);
                realm.Loot[zone.Id] = new LootPile { Id = zone.Id, Zone = zone.Id,
                    Position = new Point(f.X+.5,f.Y+.5), Owner = "fixture-owner", Party = "fixture-party",
                    Gold = 321, PublicAt = 60, Expires = 300, Items = [Items.Create(data,"healing_potion",2)] };
            }
            var before = Wire.Copy(realm.Loot);
            realm.RecoverLegacyLootPositions();
            foreach (var pile in realm.Loot.Values)
            {
                Need(WorldMap.Fits(data.Zone(pile.Zone),pile.Position), "Loot remains under furniture.");
                before[pile.Id].Position = pile.Position;
            }
            Need(Json(before) == Json(realm.Loot), "Loot identity or rewards changed.");
        });
        Test("Ordinary walls and invalid coordinates still fail closed", () =>
        {
            var zone = rooms[0];
            foreach (var point in new[] { new Point(-1,8),new Point(1.5,1.5),new Point(999,999),new Point(double.NaN,8) })
                Need(!WorldMap.TryRecoverLegacyRoadPosition(zone,point,out _), "Corrupt coordinate was recovered: " + point);
        });
        Test("Malformed and overlapping furniture is rejected by catalog validation", () =>
        {
            foreach (string mode in new[] { "path", "width", "overlap", "ground", "concealed-wall" })
            {
                var copy = Wire.Copy(data); var zone = copy.Zones.First(z => z.Kind == "interior");
                var f = zone.Furnishings.First(f => f.Solid);
                if (mode == "path") f.Kind = "../secret";
                if (mode == "width") f.Width = int.MaxValue;
                if (mode == "overlap") { var other=Wire.Copy(f); other.Id += "-copy"; zone.Furnishings.Add(other); }
                if (mode == "ground") f.Ground = true;
                if (mode == "concealed-wall") { f.Solid = false; f.Ground = true; f.X = 1; f.Y = 1; }
                Need(copy.Validate().Any(x => x.Contains("furnish",StringComparison.OrdinalIgnoreCase)), "Invalid furnishing accepted: " + mode);
            }
        });
        Console.WriteLine($"FURNISHING CONTRACT: {passed} passed; total probe failures {failures.Count}.");
        return passed;
    }
}
