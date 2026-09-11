using Kairnfall.Core;

internal static class LivingWorldEventChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        void Test(string name, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS LIVING WORLD: " + name); }
            catch (Exception error) { failures.Add("Living world: " + name); Console.WriteLine("FAIL LIVING WORLD: " + name + ": " + error.Message); }
        }
        RealmEngine Realm(double time = 20) => new(data, new RealmState { Time = time });
        Character Hero(RealmEngine realm, string suffix = "A")
        {
            var player = realm.CreateCharacter("living-world-" + suffix, "Event Hero " + suffix, "vanguard", new());
            realm.Active.Add(player.Id); return player;
        }
        ZoneDef ZoneFor(string kind) => data.Zones.First(x => WorldEventRules.EligibleZone(kind, x));
        CommandResult Act(RealmEngine realm, Character player, string kind, string target = "")
            => realm.Execute(player.Id, new GameCommand { Kind = kind, Target = target, Sequence = player.LastAction + 1 });

        Test("eight event families expose staged objectives and eligible regions", () =>
        {
            Need(WorldEventRules.Kinds.Length == 8 && WorldEventRules.Kinds.Distinct(StringComparer.Ordinal).Count() == 8, "Public-event taxonomy is incomplete.");
            foreach (string kind in WorldEventRules.Kinds)
            {
                Need(data.Zones.Any(x => WorldEventRules.EligibleZone(kind, x)), kind + " has no eligible region.");
                Need(WorldEventRules.Name(kind) != "Public Event", kind + " has no identity.");
                Need(WorldEventRules.StageCount(kind) is >= 1 and <= 2, kind + " has an invalid stage count.");
                Need(!string.IsNullOrWhiteSpace(WorldEventRules.StageLabel(kind, 0)), kind + " has no stage objective.");
                Need(!string.IsNullOrWhiteSpace(WorldEventRules.EffectLabel(WorldEventRules.SuccessEffect(kind))), kind + " has no aftermath.");
            }
        });

        Test("rift interaction chains into a champion and resolves with exact cleanup", () =>
        {
            var realm = Realm(); var player = Hero(realm); var zone = ZoneFor("arcane_rift"); player.Zone = zone.Id; player.Position = zone.Spawn;
            var value = new WorldEvent { Id = "event/check-rift", Kind = "arcane_rift", Name = WorldEventRules.Name("arcane_rift"), Zone = zone.Id, Position = player.Position, Status = "active", Stage = 0, Goal = 2, Difficulty = 1, Started = realm.State.Time, StageStarted = realm.State.Time, StageEnds = realm.State.Time + 100, Ends = realm.State.Time + 100 };
            realm.State.Events.Add(value);
            Need(Act(realm, player, "event", value.Id).Ok, "First rift stabilization failed."); realm.State.Time += 3;
            Need(Act(realm, player, "event", value.Id).Ok, "Second rift stabilization failed.");
            realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Stage == 1 && value.Status == "active", "Rift did not advance to its champion stage.");
            var champion = realm.State.Creatures.Values.Single(x => WorldEventRules.Owns(value, x.Id)); champion.Health = .1; player.Position = champion.Position; player.Stamina = 100;
            Need(Act(realm, player, "attack", champion.Id).Ok, "Champion attack failed."); realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "success" && value.Effect == "arcane_clarity", "Rift did not resolve into its regional aftermath.");
            Need(!realm.State.Creatures.Keys.Any(x => WorldEventRules.Owns(value, x)), "Event-owned champion survived stage cleanup.");
        });

        Test("timeouts fail into unrest and event-owned objects are removed", () =>
        {
            var realm = Realm(); var zone = ZoneFor("meteor");
            var value = new WorldEvent { Id = "event/check-timeout", Kind = "meteor", Name = "Timeout", Zone = zone.Id, Position = zone.Spawn, Status = "active", Goal = 4, StageEnds = realm.State.Time + .05, Ends = realm.State.Time + .05 };
            realm.State.Events.Add(value); realm.State.Nodes[value.Id + "/node/0"] = new() { Id = value.Id + "/node/0", Template = "meteor_ore", Zone = zone.Id, Position = zone.Spawn };
            realm.Tick(.1); value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "failure" && value.Effect == "regional_unrest" && value.EffectEnds > realm.State.Time, "Timeout did not produce regional unrest.");
            Need(!realm.State.Nodes.Keys.Any(x => WorldEventRules.Owns(value, x)), "Timed-out event object was not cleaned.");
        });

        Test("contribution tiers reward once and survive save roundtrip", () =>
        {
            var realm = Realm(); var a = Hero(realm, "RewardA"); var b = Hero(realm, "RewardB"); var zone = ZoneFor("world_boss");
            a.Zone = b.Zone = zone.Id; a.Position = b.Position = zone.Spawn;
            var value = new WorldEvent { Id = "event/check-reward", Kind = "world_boss", Name = "Reward", Zone = zone.Id, Position = zone.Spawn, Status = "active", Goal = 1, StageEnds = realm.State.Time + 100, Ends = realm.State.Time + 100, Contributions = new() { [a.Id] = 100, [b.Id] = 40 } };
            realm.State.Events.Add(value); var def = data.Mob("field_rat"); string mobId = value.Id + "/mob/0/0";
            realm.State.Creatures[mobId] = new() { Id = mobId, Template = def.Id, Zone = zone.Id, Position = zone.Spawn, Home = zone.Spawn, Health = .1 };
            long goldA = a.Gold, goldB = b.Gold; a.Stamina = 100;
            Need(Act(realm, a, "attack", mobId).Ok, "Event boss fixture could not be defeated."); realm.Tick(.1);
            value = realm.State.Events.Single(x => x.Id == value.Id);
            Need(value.Status == "success" && a.PublicEventsCompleted == 1 && b.PublicEventsCompleted == 1, "Meaningful contributors were not rewarded.");
            Need(a.Gold - goldA > b.Gold - goldB, "Contribution tiers did not differentiate rewards.");
            long after = a.Gold; realm.Tick(.1); Need(a.Gold == after && value.Rewarded.Count == 2, "Event rewards were granted twice.");
            var copy = Wire.Copy(realm.State); var saved = copy.Events.Single(x => x.Id == value.Id);
            Need(saved.Rewarded.SetEquals(value.Rewarded) && saved.Contributions.Count == 2 && copy.Characters[a.Id].PublicEventsCompleted == 1, "Event/reward state did not survive serialization.");
        });

        Test("participant scaling and caravan escort react to nearby players", () =>
        {
            Need(WorldEventRules.ScaledGoal("undead", 0, 4) > WorldEventRules.ScaledGoal("undead", 0, 1), "Combat events do not scale with participants.");
            var realm = Realm(); var a = Hero(realm, "EscortA"); var b = Hero(realm, "EscortB"); var c = Hero(realm, "EscortC"); var zone = ZoneFor("caravan");
            foreach (var p in new[] { a, b, c }) { p.Zone = zone.Id; p.Position = zone.Spawn; }
            var destination = WorldMap.FindFree(zone, new(zone.Spawn.X + 10, zone.Spawn.Y));
            var value = new WorldEvent { Id = "event/check-caravan", Kind = "caravan", Name = "Escort", Zone = zone.Id, Position = zone.Spawn, Destination = destination, Status = "active", Goal = WorldEventRules.BaseGoal("caravan", 0), Difficulty = 1, StageEnds = realm.State.Time + 200, Ends = realm.State.Time + 200 };
            realm.State.Events.Add(value); var before = value.Position; realm.Tick(.1);
            Need(value.Difficulty == 3 && value.Goal == WorldEventRules.ScaledGoal("caravan", 0, 3), "Nearby players did not scale the escort.");
            Need(value.Progress > 0 && value.Position.Distance(before) > 0 && value.Contributions.Count == 3, "Caravan did not move or credit its escort group.");
        });

        Test("aftermath modifiers are real gameplay hooks rather than UI-only text", () =>
        {
            var state = new RealmState { Time = 50 }; string zone = ZoneFor("caravan").Id;
            state.Events.Add(new() { Id = "event/effect", Kind = "caravan", Zone = zone, Status = "success", Effect = "safe_roads", EffectEnds = 200, Ends = 200 });
            Need(WorldEventRules.MovementMultiplier(state, zone, 50) > 1 && WorldEventRules.StaminaRegenBonus(state, zone, 50) > 0, "Safe-road aftermath has no gameplay effect.");
            state.Events[0].Effect = "regional_unrest";
            Need(WorldEventRules.MovementMultiplier(state, zone, 50) < 1 && WorldEventRules.EnemyPowerMultiplier(state, zone, 50) > 1, "Failure aftermath has no pressure tradeoff.");
            string engine = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmEngine.cs"));
            string economy = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmEconomy.cs"));
            string combat = File.ReadAllText(Path.Combine(Directory.GetCurrentDirectory(), "src/Kairnfall.Core/RealmCombat.cs"));
            Need(engine.Contains("WorldEventRules.MovementMultiplier", StringComparison.Ordinal) && engine.Contains("WorldEventRules.HealthRegenBonus", StringComparison.Ordinal), "Movement/regeneration are not wired to aftermath.");
            Need(economy.Contains("WorldEventRules.GatherYieldBonus", StringComparison.Ordinal) && economy.Contains("WorldEventRules.TreasureGoldMultiplier", StringComparison.Ordinal), "Gathering/treasure are not wired to aftermath.");
            Need(combat.Contains("WorldEventRules.EnemyPowerMultiplier", StringComparison.Ordinal), "Enemy pressure is not wired to failed events.");
        });

        Test("legacy events upgrade safely and clients expose the living world globally", () =>
        {
            var zone = ZoneFor("arcane_rift"); var state = new RealmState { Time = 40 };
            state.Events.Add(new() { Id = "event/legacy", Kind = "arcane_storm", Name = "Old storm", Zone = zone.Id, Position = zone.Spawn, Ends = 140 });
            state.Nodes["event/legacy/old"] = new() { Id = "event/legacy/old", Template = "meteor_ore", Zone = zone.Id, Position = zone.Spawn };
            var realm = new RealmEngine(data, state); realm.Tick(.1); var upgraded = realm.State.Events.Single(x => x.Id == "event/legacy");
            Need(upgraded.Kind == "arcane_rift" && upgraded.StageEnds > realm.State.Time && !realm.State.Nodes.ContainsKey("event/legacy/old"), "Historical arcane-storm event did not upgrade safely.");
            var player = Hero(realm, "Snapshot"); var otherZone = data.Zones.First(x => x.Id != player.Zone && x.Layer == "Surface");
            realm.State.Events.Add(new() { Id = "event/remote", Kind = "meteor", Name = "Remote", Zone = otherZone.Id, Position = otherZone.Spawn, Status = "active", Goal = 1, StageEnds = 100, Ends = 100 });
            Need(realm.Snapshot(player.Id).Events.Any(x => x.Id == "event/remote"), "Snapshot hides remote public events from the atlas.");
            string root = Directory.GetCurrentDirectory();
            string experience = File.ReadAllText(Path.Combine(root, "client/Scripts/GameRoot.Experience.cs"));
            string world = File.ReadAllText(Path.Combine(root, "client/Scripts/WorldView.cs"));
            string maps = File.ReadAllText(Path.Combine(root, "client/Scripts/Maps.cs"));
            string hunting = File.ReadAllText(Path.Combine(root, "client/Scripts/HuntingGuidePanel.cs"));
            Need(experience.Contains("PublicEventHud", StringComparison.Ordinal), "Combat HUD has no public-event state.");
            Need(world.Contains("\"event\"", StringComparison.Ordinal) && world.Contains("StageLabel", StringComparison.Ordinal), "World view has no event marker/identity.");
            Need(maps.Contains("Snapshot.Events", StringComparison.Ordinal) && maps.Contains("Events = () => Snapshot?.Events", StringComparison.Ordinal), "Minimap/atlas do not expose public events.");
            Need(hunting.Contains("ReadEvents", StringComparison.Ordinal) && hunting.Contains("PUBLIC EVENT", StringComparison.Ordinal), "Hunting Guide does not prioritize live events.");
        });

        Console.WriteLine($"LIVING WORLD EVENTS: {passed} groups passed; total failures {failures.Count}.");
    }
}
