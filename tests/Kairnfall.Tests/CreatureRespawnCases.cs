using System.Text.Json;
using Kairnfall.Core;

public static class CreatureRespawnCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Decide(RealmEngine realm) { realm.Tick(.1); realm.Tick(.1); }
        (RealmEngine Realm, Character Player, Creature Pending, Creature Neighbor, Point Watcher) Fixture()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("respawn-fixture", "Respawn Fixture", "vanguard", new());
            realm.Active.Add(player.Id);
            var zone = data.Zone(player.Zone);
            var plan = HuntingGrounds.For(data, zone);
            foreach (var spawn in plan.Spawns.Where(x => x.Template == "field_rat"))
            {
                var second = plan.Spawns.FirstOrDefault(x => x.Template == spawn.Template && x.Id != spawn.Id
                    && x.Position.Distance(spawn.Position) < 12);
                if (second is null) continue;
                for (int direction = 0; direction < 72; direction++)
                {
                    double angle = direction * Math.Tau / 72;
                    var vector = new Point(Math.Cos(angle), Math.Sin(angle));
                    var watcher = spawn.Position.Add(vector.Scale(8.2));
                    var approach = spawn.Position.Add(vector.Scale(-.9));
                    if (!WorldMap.Fits(zone, watcher) || !WorldMap.Fits(zone, approach)
                        || !WorldMap.LineOfSight(zone, approach, watcher)) continue;
                    player.Position = watcher;
                    var pending = realm.State.Creatures[spawn.Id]; var neighbor = realm.State.Creatures[second.Id];
                    pending.Health = 0; pending.Position = pending.Home; pending.Generation = 1; pending.RespawnAt = 100;
                    pending.Target = ""; pending.Threat.Clear(); pending.Statuses.Clear(); pending.NextAttack = 98;
                    neighbor.Health = data.Mob(neighbor.Template).Health; neighbor.Position = approach;
                    neighbor.Target = player.Id; neighbor.Threat.Clear(); neighbor.Threat[player.Id] = 1; neighbor.Statuses.Clear();
                    neighbor.NextAttack = double.MaxValue;
                    realm.State.Creatures.Clear(); realm.State.Creatures.Add(pending.Id, pending); realm.State.Creatures.Add(neighbor.Id, neighbor);
                    realm.State.Time = 100;
                    return (realm, player, pending, neighbor, watcher);
                }
            }
            throw new InvalidOperationException("No clear authored Field Rat respawn lane found.");
        }

        test("A revived hunting creature blocks later movement within the same AI decision", () =>
        {
            var (realm, player, pending, neighbor, _) = Fixture();
            Check(pending.Home.Distance(neighbor.Home) > 1.05 && neighbor.Position.Distance(pending.Home) > .8,
                "Fixture did not preserve authored homes and the existing respawn clearance.");
            var home = pending.Home; int generation = pending.Generation; double ready = pending.RespawnAt, attack = pending.NextAttack;
            string possessions = Json(player.Inventory); long gold = player.Gold, slayer = player.SkillXp["slayer"];
            Decide(realm);
            Check(pending.Health == data.Mob(pending.Template).Health && pending.Position == home, "An eligible respawn was blocked or misplaced.");
            Check(neighbor.Position.Distance(pending.Position) >= .66, "Later movement ignored the revived creature and violated ordinary separation.");
            Check(pending.Home == home && pending.Generation == generation && pending.RespawnAt == ready && pending.NextAttack == attack,
                "Respawn indexing changed identity, generation or authoritative timers.");
            Check(Json(player.Inventory) == possessions && player.Gold == gold && player.SkillXp["slayer"] == slayer && realm.Loot.Count == 0,
                "Respawn indexing granted possessions, kill training or loot.");
        });

        test("Saved pending creatures sharing a recovered home cannot revive on top of each other", () =>
        {
            var (realm, player, first, second, _) = Fixture();
            // Historical recovery resolves coordinates independently. The retained
            // save is valid even when two dead creatures have the same free home.
            second.Home = first.Home; second.Position = first.Home; second.Health = 0;
            second.Generation = 1; second.RespawnAt = first.RespawnAt; second.NextAttack = 98;
            second.Target = ""; second.Threat.Clear(); second.Statuses.Clear();
            var loaded = new RealmEngine(data, Wire.Copy(realm.State));
            var savedFirst = loaded.State.Creatures[first.Id]; var savedSecond = loaded.State.Creatures[second.Id];
            Check(savedFirst.Home == first.Home && savedSecond.Home == first.Home, "Reload relocated retained valid homes.");
            // Keep the two saved slots for this isolated collision check; their
            // normal hunting memberships were rebuilt by the real constructor.
            loaded.State.Creatures.Clear(); loaded.State.Creatures.Add(savedFirst.Id, savedFirst); loaded.State.Creatures.Add(savedSecond.Id, savedSecond);
            loaded.Active.Add(player.Id); string possessions = Json(loaded.Player(player.Id).Inventory);
            Decide(loaded);
            Check(new[] { savedFirst, savedSecond }.Count(x => x.Health > 0) == 1,
                "Two pending creatures revived at one occupied home in the same AI pass.");
            Check(savedFirst.Home == first.Home && savedSecond.Home == first.Home && savedFirst.Generation == 1 && savedSecond.Generation == 1
                && savedFirst.RespawnAt == first.RespawnAt && savedSecond.RespawnAt == second.RespawnAt,
                "Collision deferral changed saved homes, generations or respawn deadlines.");
            Check(Json(loaded.Player(player.Id).Inventory) == possessions && loaded.Loot.Count == 0,
                "Saved respawn deferral changed possessions or created rewards.");
        });

        test("Respawn retains its deadline and nearby-player deferral while clearing completed combat state", () =>
        {
            var (realm, player, pending, neighbor, watcher) = Fixture(); realm.State.Creatures.Remove(neighbor.Id);
            pending.RespawnAt = 101; pending.Target = player.Id; pending.Threat[player.Id] = 4;
            pending.Phase = 2; pending.AttackStep = 3;
            pending.Statuses.Add(new() { Kind = "poison", Source = player.Id, Until = 110, Power = 1 });
            Decide(realm); Check(pending.Health == 0, "Creature revived before its original deadline.");
            realm.State.Time = pending.RespawnAt; player.Position = pending.Home;
            Decide(realm); Check(pending.Health == 0 && pending.RespawnAt == 101, "Nearby player deferral was bypassed or extended its timer.");
            player.Position = watcher; Decide(realm);
            Check(pending.Health == data.Mob(pending.Template).Health && pending.Target == "" && pending.Threat.Count == 0
                && pending.Statuses.Count == 0 && pending.Phase == 0 && pending.AttackStep == 0,
                "Eligible respawn retained a stale target, threat, status or attack phase.");
            Check(pending.RespawnAt == 101 && pending.NextAttack == 98 && pending.Generation == 1,
                "Completed combat-state reset altered authoritative attack or respawn timing.");
        });
    }
}
