using System.Text.Json;
using Kairnfall.Core;

public static class WildlifeHostilityCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Advance(RealmEngine realm, int ticks) { for (int n = 0; n < ticks; n++) realm.Tick(.1); }
        void Act(RealmEngine realm, Character player, string kind, string target = "", string arg = "")
        {
            var result = realm.Execute(player.Id, new GameCommand { Kind = kind, Target = target, Arg = arg,
                Sequence = player.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") });
            Check(result.Ok, kind + " failed: " + result.Message);
        }
        Point ClearApproach(RealmEngine realm, Creature mob)
        {
            var zone = data.Zone(mob.Zone);
            for (int direction = 0; direction < 32; direction++)
            {
                double angle = direction * Math.Tau / 32;
                var vector = new Point(Math.Cos(angle), Math.Sin(angle));
                var approach = mob.Position.Add(vector.Scale(.8));
                var retreat = WorldMap.Move(zone, mob.Position, vector.Scale(-1.25));
                if (WorldMap.Fits(zone, approach) && WorldMap.LineOfSight(zone, mob.Position, approach)
                    && retreat.Distance(mob.Position) > .8
                    && realm.State.Creatures.Values.Where(x => x.Id != mob.Id && x.Zone == mob.Zone && x.Health > 0)
                        .All(x => x.Position.Distance(retreat) >= .66)) return approach;
            }
            throw new InvalidOperationException("No clear wildlife engagement lane for " + mob.Id);
        }

        test("Unprovoked wildlife on the real opening path never acquires or damages a traveler", () =>
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("wildlife-path", "Wildlife Path", "vanguard", new());
            var zone = data.Zone(OpeningJourney.Home); var giver = OpeningJourney.Giver(data);
            var plan = HuntingGrounds.For(data, zone);
            var rat = plan.Spawns.Where(x => x.Template == OpeningJourney.Foe)
                .OrderBy(x => x.Position.Distance(giver.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).First();
            var path = WorldMap.FindPath(zone, giver.Position, rat.Position, zone.Width * zone.Height * 2);
            var wildlife = realm.State.Creatures.Values.Where(x => x.Zone == zone.Id && x.Owner == ""
                && data.Mob(x.Template).Ai is "passive" or "fleeing").ToArray();
            int NearbyHares(Point at) => wildlife.Count(x => x.Template == "wild_hare"
                && x.Position.Distance(at) <= data.Mob(x.Template).Aggro && WorldMap.LineOfSight(zone, x.Position, at));
            Check(path.Count > 0, "The actual Bren-to-rat route is unreachable.");
            player.Position = path.OrderByDescending(NearbyHares).First();
            Check(NearbyHares(player.Position) >= 2, "The opening-path fixture lacks the original nearby wildlife hazard.");
            string inventory = Json(player.Inventory); long gold = player.Gold;
            double initialCombat = player.LastCombat, initialHealth = player.Health;
            var identities = wildlife.ToDictionary(x => x.Id, x => (x.Home, x.Health, x.Generation, x.RespawnAt, x.NextAttack));
            realm.Active.Add(player.Id); Advance(realm, 100);
            Check(wildlife.All(x => x.Target != player.Id && !x.Threat.ContainsKey(player.Id)),
                "Unprovoked passive or fleeing wildlife acquired the player.");
            int wildlifeTelegraphs = realm.State.Telegraphs.Count(x => wildlife.Any(m => m.Id == x.Source));
            double maxHealth = CombatMath.Stats(player, data).Health;
            Check(wildlifeTelegraphs == 0 && player.LastCombat == initialCombat && player.Health >= initialHealth && player.Health == maxHealth,
                $"Unprovoked wildlife attacked or damaged the traveler: telegraphs={wildlifeTelegraphs}, LastCombat={initialCombat}->{player.LastCombat}, health={initialHealth}->{player.Health}/{maxHealth}.");
            Check(wildlife.All(x => identities[x.Id] == (x.Home, x.Health, x.Generation, x.RespawnAt, x.NextAttack)),
                "Peaceful behavior changed wildlife homes, health, generations or combat timers.");
            Check(player.LastAction == 0 && player.Bestiary.Count == 0 && realm.Loot.Count == 0
                && Json(player.Inventory) == inventory && player.Gold == gold,
                "The peaceful route changed possessions, commands, kills or rewards.");
        });

        test("Ordinary aggressive species still acquire and damage an unprovoking player", () =>
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("wildlife-control", "Wildlife Control", "vanguard", new());
            var fox = realm.State.Creatures.Values.First(x => x.Zone == "kingsmeadow" && x.Template == "brush_fox" && x.Health > 0);
            Check(data.Mob(fox.Template).Ai == "territorial", "Aggressor control is no longer an authored hostile species.");
            // Retain one real authored creature to isolate aggression from group pressure.
            realm.State.Creatures.Clear(); realm.State.Creatures.Add(fox.Id, fox);
            player.Zone = fox.Zone; player.Position = ClearApproach(realm, fox);
            realm.Active.Add(player.Id);
            for (int tick = 0; tick < 120 && !(player.LastCombat > 0 && player.Health < CombatMath.Stats(player, data).Health); tick++)
                Advance(realm, 1);
            Check(fox.Target == player.Id && player.LastCombat > 0 && player.Health < CombatMath.Stats(player, data).Health,
                "The peaceful-wildlife rule disabled natural hostile acquisition or damage.");
            Check(player.LastAction == 0 && player.Health > 0 && player.Bestiary.Count == 0 && realm.Loot.Count == 0,
                "Aggression control required provocation or introduced a death/kill reward.");
        });

        test("Provoked passive and fleeing wildlife retain threat and wounded retreat through reload", () =>
        {
            foreach (string template in new[] { "field_rat", "wild_hare" })
            {
                var realm = new RealmEngine(data);
                var player = realm.CreateCharacter("wildlife-provoked", "Wildlife Provoked", "arcanist", new());
                var mob = realm.State.Creatures.Values.First(x => x.Zone == OpeningJourney.Home && x.Template == template && x.Health > 0);
                var definition = data.Mob(template); var home = mob.Home; int generation = mob.Generation; double respawn = mob.RespawnAt;
                // Three ordinary unarmed hits put the authored animal below half
                // health without killing it, even if all three hits are critical.
                Act(realm, player, "unequip", arg: "weapon"); realm.Active.Add(player.Id);
                for (int strike = 0; strike < 3; strike++)
                {
                    player.Position = mob.Position; Act(realm, player, "attack", mob.Id);
                    Advance(realm, 1); // Resolve the Arcanist's ordinary projectile through the real tick.
                    Check(mob.Health > 0 && mob.Threat.ContainsKey(player.Id), "Legitimate provocation failed or killed the retreat fixture.");
                    if (strike < 2) Advance(realm, 8);
                }
                Check(mob.Health < definition.Health * .5 && mob.Target == player.Id, "Real attacks did not establish wounded, provoked wildlife.");
                player.Position = ClearApproach(realm, mob);
                double distance = player.Position.Distance(mob.Position), health = mob.Health, threat = mob.Threat[player.Id];
                string inventory = Json(player.Inventory); long gold = player.Gold;
                var loaded = new RealmEngine(data, Wire.Copy(realm.State)); loaded.Active.Add(player.Id);
                var retained = loaded.State.Creatures[mob.Id]; var savedPlayer = loaded.Player(player.Id);
                Check(retained.Health == health && retained.Threat.GetValueOrDefault(player.Id) == threat,
                    "Reload discarded legitimate wildlife combat state.");
                Advance(loaded, 2);
                Check(retained.Target == player.Id && retained.Threat.ContainsKey(player.Id)
                    && retained.Position.Distance(savedPlayer.Position) > distance + .05,
                    "Provoked wildlife lost its target or stopped the existing wounded retreat after reload.");
                Check(retained.Home == home && retained.Generation == generation && retained.RespawnAt == respawn && retained.Health == health
                    && savedPlayer.Bestiary.Count == 0 && loaded.Loot.Count == 0
                    && Json(savedPlayer.Inventory) == inventory && savedPlayer.Gold == gold,
                    "Wildlife behavior reset identity, health, respawn timing or rewards.");
            }
        });
    }
}
