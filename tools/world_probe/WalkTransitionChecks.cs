using Kairnfall.Core;

internal static class WalkTransitionChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string text) { if (!value) throw new InvalidOperationException(text); }
        void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS WALK TRANSITIONS: " + name); }
            catch (Exception error) { failures.Add("walk transition: " + name); Console.WriteLine("FAIL WALK TRANSITIONS: " + name + ": " + error.Message); }
        }
        Character AtLevel(int target)
        {
            var seeded = new Character { Class = "vanguard" };
            long remaining = Progression.PlayerThreshold(target);
            foreach (var skill in data.Skills)
            {
                long chunk = Math.Min(remaining, Progression.Threshold(Progression.SkillCap));
                seeded.SkillXp[skill.Id] = chunk; remaining -= chunk;
            }
            Need(remaining == 0 && Progression.PlayerLevel(seeded) == target, "Could not seed level " + target);
            return seeded;
        }
        Point Approach(ZoneDef zone, ExitDef exit)
        {
            var outward = MapTransitionRules.BorderOutward(zone, exit);
            var guess = outward.Distance(new Point(0, 0)) > 0.01
                ? exit.Position.Add(outward.Scale(-1.15))
                : exit.Position.Add(exit.Position.Direction(zone.Spawn).Scale(1.15));
            return WorldMap.FindFree(zone, guess);
        }
        Point Direction(ZoneDef zone, ExitDef exit, Point from)
        {
            var outward = MapTransitionRules.BorderOutward(zone, exit);
            return outward.Distance(new Point(0, 0)) > 0.01 ? outward : from.Direction(exit.Position);
        }
        bool WalkThrough(RealmEngine realm, Character player, ZoneDef source, ExitDef exit, int ticks = 80)
        {
            realm.Active.Add(player.Id);
            for (int i = 0; i < ticks && player.Zone == source.Id; i++)
            {
                if (i % 3 == 0)
                {
                    var dir = Direction(source, exit, player.Position);
                    var result = realm.Execute(player.Id, new GameCommand { Kind = "move", X = dir.X, Y = dir.Y });
                    Need(result.Ok, "Movement intent rejected: " + result.Message);
                }
                realm.Tick(0.05);
            }
            return player.Zone == exit.Target;
        }

        Test("authored exits are reciprocal and have typed walk-through visuals", () =>
        {
            int exits = 0, borders = 0, caves = 0;
            var allowed = new HashSet<string> { "entrance_road", "entrance_door", "entrance_gate", "entrance_cave", "entrance_tunnel", "entrance_lift", "entrance_portal", "entrance_stairs" };
            foreach (var source in data.Zones) foreach (var exit in source.Exits)
            {
                var target = data.Zone(exit.Target);
                var reciprocal = target.Exits.FirstOrDefault(x => x.Target == source.Id && x.Position.Distance(exit.Arrival) < 0.01 && x.Arrival.Distance(exit.Position) < 0.01);
                Need(reciprocal is not null, "Missing reciprocal exit for " + source.Id + "/" + exit.Id);
                string visual = MapTransitionRules.EntranceVisualKey(source, exit, target);
                Need(allowed.Contains(visual), "Unknown entrance visual " + visual + " for " + exit.Id);
                if (MapTransitionRules.IsBorderExit(source, exit)) borders++;
                if (source.Kind == "wilderness" && source.Layer == "Surface" && target.Layer != "Surface" && exit.Kind == "stairs")
                {
                    Need(visual == "entrance_cave", "Underground wilderness entrance is not cave-like: " + exit.Id);
                    caves++;
                }
                exits++;
            }
            Need(exits > 100, "Too few authored exits were checked.");
            Need(borders > 50, "Surface border network is unexpectedly sparse.");
            Need(caves >= 10, "Too few wilderness cave entrances were classified.");
        });

        Test("walking through a building door changes maps without an interact command", () =>
        {
            var pair = (from source in data.Zones
                        from exit in source.Exits
                        let target = data.Zone(exit.Target)
                        where exit.Kind == "door" && source.Kind != "interior" && target.Kind == "interior"
                        select (source, exit, target)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-door", "Door Walker", "vanguard", new());
            player.Zone = pair.source.Id; player.Position = Approach(pair.source, pair.exit);
            Need(WalkThrough(realm, player, pair.source, pair.exit), "Walking onto the door did not enter the interior.");
            Need(WorldMap.Fits(pair.target, player.Position), "Door arrival is blocked.");
            Need(player.Position.Distance(pair.exit.Arrival) >= MapTransitionRules.ArrivalClearance - 0.25, "Door arrival remained on the reciprocal trigger.");
            string entered = player.Zone;
            var held = Direction(pair.source, pair.exit, pair.exit.Position);
            for (int i = 0; i < 12; i++)
            {
                if (i % 3 == 0) realm.Execute(player.Id, new GameCommand { Kind = "move", X = held.X, Y = held.Y });
                realm.Tick(0.05);
            }
            Need(player.Zone == entered, "Door arrival immediately bounced back to the previous map.");
        });

        Test("walking outward at a connected wilderness border enters the adjacent map", () =>
        {
            var pair = (from source in data.Zones
                        from exit in source.Exits
                        let target = data.Zone(exit.Target)
                        where source.Kind == "wilderness" && target.Kind == "wilderness" && MapTransitionRules.IsBorderExit(source, exit)
                        orderby JourneyProgression.ExitRequirement(data, exit)
                        select (source, exit, target)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-border", "Border Walker", "vanguard", new());
            var level = AtLevel(Math.Max(1, JourneyProgression.ExitRequirement(data, pair.exit)));
            player.SkillXp = new(level.SkillXp); player.Zone = pair.source.Id; player.Position = Approach(pair.source, pair.exit);
            Need(WalkThrough(realm, player, pair.source, pair.exit), "Outward movement did not cross the authored border.");
            Need(player.Zone == pair.target.Id && WorldMap.Fits(pair.target, player.Position), "Border arrival is invalid.");
        });

        Test("level gates remain server-authoritative for automatic entrances", () =>
        {
            var candidate = (from source in data.Zones
                             from exit in source.Exits
                             let gate = JourneyProgression.ExitRequirement(data, exit)
                             where gate > 1 && source.Kind != "interior"
                             orderby gate
                             select (source, exit, gate)).First();
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-gate", "Gate Walker Auto", "vanguard", new());
            var low = AtLevel(candidate.gate - 1); player.SkillXp = new(low.SkillXp);
            player.Zone = candidate.source.Id; player.Position = Approach(candidate.source, candidate.exit);
            Need(!WalkThrough(realm, player, candidate.source, candidate.exit, 50) && player.Zone == candidate.source.Id, "Below-level player crossed an automatic gate.");
            var ready = AtLevel(candidate.gate); player.SkillXp = new(ready.SkillXp); player.Position = Approach(candidate.source, candidate.exit);
            Need(WalkThrough(realm, player, candidate.source, candidate.exit), "Exact-level player could not walk through the gate.");
        });

        Test("a border with no authored exit stays solid", () =>
        {
            var zone = data.Zones.First(z => z.Kind == "wilderness" && z.WorldX == data.Zones.Where(x => x.Kind == "wilderness").Min(x => x.WorldX));
            Need(!zone.Exits.Any(e => MapTransitionRules.BorderOutward(zone, e).X < -0.5), "Fixture unexpectedly has a left-edge exit.");
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("walk-wall", "Edge Walker", "vanguard", new());
            player.Zone = zone.Id; player.Position = WorldMap.FindFree(zone, new Point(1.5, zone.Spawn.Y)); realm.Active.Add(player.Id);
            for (int i = 0; i < 30; i++)
            {
                if (i % 3 == 0) realm.Execute(player.Id, new GameCommand { Kind = "move", X = -1, Y = 0 });
                realm.Tick(0.05);
            }
            Need(player.Zone == zone.Id, "A non-connected border changed maps.");
            Need(WorldMap.Fits(zone, player.Position), "Solid border pushed the player into invalid terrain.");
        });

        Test("client exits are visual walk-throughs and are no longer E interactions", () =>
        {
            string world = File.ReadAllText("client/Scripts/WorldView.cs");
            string root = File.ReadAllText("client/Scripts/GameRoot.cs");
            string rules = File.ReadAllText("client/Scripts/ExperienceRules.cs");
            Need(!world.Contains("new WorldTarget(\"exit\"", StringComparison.Ordinal), "WorldView still registers exits as interaction targets.");
            Need(!root.Contains("target.Kind == \"exit\"", StringComparison.Ordinal), "GameRoot still sends transition commands from exit interactions.");
            Need(!rules.Contains("\"exit\" => \"Enter\"", StringComparison.Ordinal), "Interaction verb still advertises E-to-enter.");
            foreach (string key in new[] { "entrance_road", "entrance_door", "entrance_gate", "entrance_cave", "entrance_tunnel", "entrance_lift", "entrance_portal", "entrance_stairs" })
                Need(world.Contains("EntranceVisualKey", StringComparison.Ordinal), "WorldView is not using typed entrance visuals: " + key);
        });

        Console.WriteLine($"WALK TRANSITIONS: {passed} groups passed; total failures {failures.Count}.");
    }
}
