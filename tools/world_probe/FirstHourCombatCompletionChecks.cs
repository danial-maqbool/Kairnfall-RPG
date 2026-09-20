using System.Runtime.CompilerServices;
using System.Text.Json;
using Kairnfall.Core;

/// <summary>
/// Regression checks for authoritative first-fight completion. Placement and clocks are
/// isolated fixtures; attacks, casts, damage, kill credit and receipt replay use the real
/// realm API. This is not a UI playthrough, a pacing measurement or human acceptance.
/// </summary>
internal static class FirstHourCombatCompletionChecks
{
    [ModuleInitializer]
    internal static void Run()
    {
        // Match world_probe's optional catalog argument instead of silently skipping
        // these checks when it is invoked outside the repository working directory.
        var arguments = Environment.GetCommandLineArgs();
        string path = arguments.Length > 1 ? arguments[1] : "content/catalog.json";
        var data = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path), Wire.Json)
            ?? throw new InvalidDataException("Empty first-fight regression catalog.");
        var combat = FirstHourExperience.Steps.Single(x => x.Id == "combat");
        var failures = new List<string>();
        int passed = 0, nonlethalClasses = 0, victoriousClasses = 0, supportCasts = 0;

        void Need(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException(message);
        }
        void Test(string name, Action check)
        {
            try { check(); passed++; Console.WriteLine("PASS FIRST FIGHT: " + name); }
            catch (Exception error)
            {
                failures.Add(name + ": " + error.Message);
                Console.WriteLine("FAIL FIRST FIGHT: " + name + ": " + error.Message);
            }
        }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        GameCommand Command(RealmEngine realm, string id, string kind, string target = "", string item = "")
            => new() { Kind = kind, Target = target, Item = item,
                Sequence = realm.Player(id).LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
        void Act(RealmEngine realm, string id, GameCommand command)
        {
            var result = realm.Execute(id, command);
            Need(result.Ok, command.Kind + " unexpectedly failed: " + result.Message);
        }
        void Advance(RealmEngine realm, double seconds)
        {
            double until = realm.State.Time + seconds;
            while (realm.State.Time + .0001 < until) realm.Tick(.1);
        }

        Test("nonlethal attack is not a first victory for any starting class", () =>
        {
            foreach (var cls in data.Classes)
            {
                var realm = new RealmEngine(data);
                var player = realm.CreateCharacter("first-fight-nonlethal", "Nonlethal Hero", cls.Id, new());
                // Deliberately use a healthy, much stronger authored target so a random
                // critical hit cannot accidentally turn this negative fixture into a kill.
                // No health, damage, bestiary count or tutorial state is injected.
                double minimumHealth = CombatMath.Stats(player, data).Physical * 20;
                var target = realm.State.Creatures.Values.Where(x => x.Owner == "" && x.Health > minimumHealth)
                    .OrderByDescending(x => x.Health).ThenBy(x => x.Id, StringComparer.Ordinal).First();
                player.Zone = target.Zone; player.Position = target.Position;
                Need(WorldMap.Fits(data.Zone(player.Zone), player.Position), "Nonlethal fixture is not actor-fit.");
                var command = Command(realm, player.Id, "attack", target.Id);
                Act(realm, player.Id, command);
                player = realm.Player(player.Id);
                Need(target.Health > 0 && !player.Bestiary.Values.Any(count => count > 0),
                    cls.Id + ": the negative fixture unexpectedly killed a creature.");
                Need(!FirstHourExperience.Completed(data, player, combat),
                    "FIRST_HOUR_COMBAT_NONLETHAL: " + cls.Id + " was credited with a victory before any kill.");
                Need(!FirstHourExperience.Marked(player, "combat"), cls.Id + ": attack still writes a victory marker.");
                string beforeReplay = Json(player);
                Act(realm, player.Id, command);
                Need(beforeReplay == Json(realm.Player(player.Id)), "Replayed nonlethal attack changed character state.");
                nonlethalClasses++;
            }
            Need(nonlethalClasses == data.Classes.Count && nonlethalClasses > 0, "Starting-class coverage is incomplete.");
        });

        Test("successful support casts do not complete a fight", () =>
        {
            foreach (var cls in data.Classes)
            {
                var realm = new RealmEngine(data);
                var player = realm.CreateCharacter("first-fight-support", "Support Hero", cls.Id, new());
                var ability = data.Abilities.Where(x => (x.Class == "" || x.Class == cls.Id)
                    && x.Requirement <= Progression.Level(player, x.Skill)
                    && x.Mana <= player.Mana && x.Stamina <= player.Stamina
                    && x.Kind is "shield" or "buff" or "stealth" or "summon")
                    .OrderBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                if (ability is null) continue; // Some classes have no starting support spell.
                Act(realm, player.Id, Command(realm, player.Id, "cast", item: ability.Id));
                player = realm.Player(player.Id);
                Need(!player.Bestiary.Values.Any(count => count > 0), "Support fixture unexpectedly killed a creature.");
                Need(!FirstHourExperience.Completed(data, player, combat),
                    "FIRST_HOUR_COMBAT_SUPPORT: " + ability.Id + " was credited as a won fight.");
                Need(!FirstHourExperience.Marked(player, "combat"), "Support cast still writes a victory marker.");
                supportCasts++;
            }
            Need(supportCasts > 0, "No real starting support cast was exercised.");
        });

        Test("real starter kills complete immediately and survive replay and restart for every class", () =>
        {
            foreach (var cls in data.Classes)
            {
                var realm = new RealmEngine(data);
                string id = realm.CreateCharacter("first-fight-victory", "Victorious Hero", cls.Id, new()).Id;
                realm.Active.Add(id);
                var target = realm.State.Creatures.Values.Where(x => x.Zone == "wayfarers_rest"
                    && x.Template == "field_rat" && x.Owner == "" && x.Health > 0)
                    .OrderBy(x => x.Id, StringComparer.Ordinal).First();
                Need(!FirstHourExperience.Completed(data, realm.Player(id), combat), "Fresh character already has combat completion.");
                GameCommand? lastAttack = null;
                for (int strike = 0; target.Health > 0 && strike < 80; strike++)
                {
                    var player = realm.Player(id);
                    Need(player.Health > 0, cls.Id + ": starter combat fixture died.");
                    Need(WorldMap.Fits(data.Zone(player.Zone), target.Position), "Retreating starter target is not actor-fit.");
                    // Re-establish reachable melee proximity to the real retreating rat.
                    // Keep normal AI, cooldowns, stamina costs and projectile resolution.
                    Need(player.Position.Distance(target.Position) < 1
                        || WorldMap.FindPath(data.Zone(player.Zone), player.Position, target.Position,
                            data.Zone(player.Zone).Width * data.Zone(player.Zone).Height * 2).Count > 0,
                        "Starter target is not reachable from the preceding fixture position.");
                    player.Position = target.Position;
                    lastAttack = Command(realm, id, "attack", target.Id);
                    Act(realm, id, lastAttack);
                    Advance(realm, 2);
                }
                var winner = realm.Player(id);
                Need(target.Health <= 0 && winner.Bestiary.GetValueOrDefault("field_rat") == 1,
                    cls.Id + ": real starter kill was not credited exactly once.");
                Need(FirstHourExperience.Completed(data, winner, combat),
                    cls.Id + ": real kill needs an unrelated later command to complete the milestone.");
                string beforeRead = Json(winner);
                for (int i = 0; i < 10; i++) FirstHourExperience.Completed(data, winner, combat);
                Need(beforeRead == Json(winner), "Reading victory completion mutated character state or granted a reward.");
                var replay = lastAttack ?? throw new InvalidOperationException("No real attack was exercised.");
                string lootBeforeReplay = Json(realm.Loot);
                Act(realm, id, replay);
                Need(beforeRead == Json(realm.Player(id)) && lootBeforeReplay == Json(realm.Loot),
                    "Replaying the killing attack duplicated credit, damage or loot.");
                var restored = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
                Need(beforeRead == Json(restored.Player(id)), "Restart changed character identity, progress or equipment.");
                Need(FirstHourExperience.Completed(data, restored.Player(id), combat), "Victory was lost after restart.");
                Act(restored, id, replay);
                Need(beforeRead == Json(restored.Player(id)) && lootBeforeReplay == Json(restored.Loot),
                    "Replaying the persisted killing receipt changed rewards or completion.");
                Need(Items.Validate(restored.State, data).Count == 0, "Combat/restart fixture violated inventory invariants.");
                victoriousClasses++;
            }
            Need(victoriousClasses == data.Classes.Count && victoriousClasses > 0, "Victory coverage missed a starting class.");
        });

        Test("failed commands and zero kill counts do not imply victory; historical markers remain compatible", () =>
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("first-fight-invalid", "Invalid Hero", "vanguard", new());
            var command = Command(realm, player.Id, "attack", "missing-creature");
            string before = Json(player);
            Need(!realm.Execute(player.Id, command).Ok, "Missing hostile unexpectedly accepted an attack.");
            player = realm.Player(player.Id);
            Need(before == Json(player) && !FirstHourExperience.Completed(data, player, combat),
                "A rejected attack mutated the character or completed combat.");
            // Boundary/save-compatibility fixtures, not simulated gameplay or kill credit.
            var empty = new Character(); empty.Bestiary["field_rat"] = 0;
            Need(!FirstHourExperience.Completed(data, empty, combat), "An empty bestiary entry counts as a kill.");
            var historical = new Character(); historical.Discoveries.Add(FirstHourExperience.Key("combat"));
            string historicalBefore = Json(historical);
            Need(FirstHourExperience.Completed(data, historical, combat), "Existing character's completion was forcibly reset.");
            Need(historicalBefore == Json(historical), "Historical completion was rewritten during inspection.");
        });

        Console.WriteLine($"FIRST_HOUR_COMBAT_COMPLETION: {passed}/{passed + failures.Count} groups; nonlethal_classes={nonlethalClasses}/{data.Classes.Count}; victorious_classes={victoriousClasses}/{data.Classes.Count}; support_casts={supportCasts}. Isolated API fixtures, not a first-time human playthrough.");
        if (failures.Count > 0) throw new InvalidOperationException("First-fight regression failures: " + string.Join(" | ", failures));
    }
}
