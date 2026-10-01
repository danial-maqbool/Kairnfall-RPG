using System.Text.Json;
using Kairnfall.Core;

public static class RareRespawnPersistenceCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        string Rewards(RealmEngine realm, string player) => Json(new { Character = realm.Player(player), realm.Loot });
        RealmEngine Reload(RealmEngine realm)
        {
            var state = JsonSerializer.Deserialize<RealmState>(Json(realm.State), Wire.Json)!;
            var loot = JsonSerializer.Deserialize<Dictionary<string, LootPile>>(Json(realm.Loot), Wire.Json)!;
            return new RealmEngine(data, state) { Loot = loot };
        }
        (RealmEngine Realm, Character Player, Creature Mob, MobDef Def) Kill(string template = "rare_pine_wolf")
        {
            var realm = new RealmEngine(data); var player = realm.CreateCharacter("rare-timer", "Rare Timer", "vanguard", new());
            var definition = data.Mob(template);
            var zone = data.Zones.Where(x => x.Kind == "wilderness" && x.Species.Contains(template, StringComparer.Ordinal))
                .OrderBy(x => x.Id, StringComparer.Ordinal).First();
            var mob = realm.State.Creatures[zone.Id + "/" + template];
            // Like the retained champion transaction fixture: a final legitimate
            // attack owns the death, generation, rewards and timing transition.
            realm.State.Time = 100; mob.Health = 1; mob.RespawnAt = 0; mob.Position = mob.Home;
            player.Zone = zone.Id; player.Position = mob.Home; realm.Active.Add(player.Id);
            var command = new GameCommand { Kind = "attack", Target = mob.Id, Sequence = player.LastAction + 1 };
            var result = realm.Execute(player.Id, command); Check(result.Ok, "Actual rare kill failed: " + result.Message);
            Check(mob.Health == 0 && mob.Generation == 1 && player.Bestiary.GetValueOrDefault(template) == 1 && realm.Loot.Count == 1,
                "The death fixture did not produce exactly one real kill/generation/reward.");
            return (realm, player, mob, definition);
        }
        void Decide(RealmEngine realm) { realm.Tick(.1); realm.Tick(.1); }

        test("An elite death saves its accepted cadence before any AI tick and never schedules it twice", () =>
        {
            foreach (string template in new[] { "rare_pine_wolf", "rare_hay_golem" })
            {
                var (realm, player, mob, definition) = Kill(template);
                double delay = RareEncounterRules.RespawnDelay(data.Zone(mob.Zone), definition, mob.Generation);
                double deadline = realm.State.Time + delay; string rewards = Rewards(realm, player.Id);
                Check(mob.RespawnAt == deadline, "The authoritative death saved a legacy timer instead of its accepted cadence.");
                var loaded = Reload(realm);
                Check(loaded.State.Creatures[mob.Id].RespawnAt == deadline && Rewards(loaded, player.Id) == rewards,
                    "Immediate save/reload changed the deadline or replayed kill rewards.");
                // The real constructor rebuilds all pending hunt slots. Position
                // the observer away from this home so an AI pass is legitimate.
                realm.Player(player.Id).Position = data.Zone(mob.Zone).Spawn;
                loaded.Player(player.Id).Position = data.Zone(mob.Zone).Spawn; loaded.Active.Add(player.Id);
                Decide(realm); Decide(loaded);
                Check(realm.State.Creatures[mob.Id].RespawnAt == deadline && loaded.State.Creatures[mob.Id].RespawnAt == deadline,
                    "A later AI decision extended an already scheduled generation.");
                Check(realm.Loot.Count == 1 && loaded.Loot.Count == 1 && realm.Player(player.Id).Bestiary[template] == 1
                    && loaded.Player(player.Id).Bestiary[template] == 1, "AI scheduling duplicated loot or kill credit.");
            }
        });

        test("Current-revision rare saves retain near-deadline and overdue timers and all rewards", () =>
        {
            var (realm, player, mob, _) = Kill(); double deadline = mob.RespawnAt;
            Check(realm.State.HuntingRevision == HuntingGrounds.Revision, "Fixture is not a current hunting revision.");
            foreach (double remaining in new[] { 91.001, 91, 60, 0, -1 })
            {
                // A detached reading-delay clock isolates persistence boundaries;
                // it is not a human pacing or elapsed offline-time measurement.
                realm.State.Time = deadline - remaining; string rewards = Rewards(realm, player.Id);
                var loaded = Reload(realm); var saved = loaded.State.Creatures[mob.Id];
                Check(saved.RespawnAt == deadline && saved.Health == 0 && saved.Generation == mob.Generation && saved.Home == mob.Home,
                    "Reload extended or reset a current pending rare with " + remaining + " seconds remaining.");
                Check(Rewards(loaded, player.Id) == rewards, "Pending deadline reload changed possessions or kill/drop credit.");
                var twice = Reload(loaded);
                Check(twice.State.Creatures[mob.Id].RespawnAt == deadline && Rewards(twice, player.Id) == rewards,
                    "A second restart changed the retained timer or rewards.");
            }
        });

        test("Historical short elite timers still upgrade once and pristine delayed appearances stay intact", () =>
        {
            var (realm, player, mob, definition) = Kill();
            realm.State.HuntingRevision = 0; mob.RespawnAt = realm.State.Time + 90;
            string rewards = Rewards(realm, player.Id); double expected = realm.State.Time + RareEncounterRules.RespawnDelay(data.Zone(mob.Zone), definition, mob.Generation);
            var loaded = Reload(realm);
            Check(loaded.State.HuntingRevision == HuntingGrounds.Revision && loaded.State.Creatures[mob.Id].RespawnAt == expected
                && loaded.State.Creatures[mob.Id].Health == 0 && loaded.State.Creatures[mob.Id].Generation == mob.Generation,
                "Legacy short elite migration lost its accepted cadence/death state.");
            Check(Rewards(loaded, player.Id) == rewards && Reload(loaded).State.Creatures[mob.Id].RespawnAt == expected,
                "Legacy migration changed rewards or scheduled the same death again.");
            var pristine = new RealmEngine(data);
            var initial = pristine.State.Creatures[mob.Id]; double initialDelay = RareEncounterRules.InitialSpawnDelay(data.Zone(initial.Zone), definition);
            Check(initial.Health == 0 && initial.Generation == 0 && initial.RespawnAt == initialDelay,
                "The pristine champion fixture lost its deferred first appearance.");
            pristine.State.Time = initial.RespawnAt - 1;
            var pristineLoaded = Reload(pristine);
            Check(pristineLoaded.State.Creatures[initial.Id].Health == 0 && pristineLoaded.State.Creatures[initial.Id].Generation == 0
                && pristineLoaded.State.Creatures[initial.Id].RespawnAt == initial.RespawnAt,
                "Reload converted a pristine first appearance into an elite death cadence.");
        });
    }
}
