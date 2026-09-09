using Kairnfall.Core;
using System.Text.Json;

/// <summary>Disposable support-training fixtures. Healing effects stay unchanged; only reward attribution changes.</summary>
internal static class SupportTrainingChecks
{
    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Need(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        void Test(string name, Action action)
        {
            try { action(); passed++; Console.WriteLine("PASS SUPPORT XP: " + name); }
            catch (Exception error) { failures.Add(name); Console.WriteLine("FAIL SUPPORT XP: " + name + ": " + error); }
        }
        Test("Encounter attribution expires, follows the latest enemy and survives serialization", () =>
        {
            var p = new Character { Class = "vanguard", Zone = "wayfarers_rest", Health = 100 };
            Need(SupportTraining.EncounterLevel(p, 0) == 0, "A legacy or new character invented a hostile source.");
            SupportTraining.Record(p, 40, 100);
            Need(SupportTraining.EncounterLevel(p, 114.99) == 40, "Recent actual contact was lost.");
            Need(SupportTraining.EncounterLevel(p, 115) == 0, "Expired contact retained support rewards.");
            Need(SupportTraining.EncounterLevel(p, 99) == 0, "A future timestamp supplied rewards.");
            SupportTraining.Record(p, 1, 101);
            Need(SupportTraining.EncounterLevel(p, 102) == 1, "A weaker later enemy inherited an old stronger difficulty.");
            var copy = Wire.Copy(p);
            Need(Json(copy) == Json(p) && SupportTraining.EncounterLevel(copy, 102) == 1, "Reconnect changed the encounter difficulty.");
            copy.Zone = "other-region";
            Need(SupportTraining.EncounterLevel(copy, 102) == 0, "Changing region retained foreign encounter credit.");
            p.Health = 0;
            Need(SupportTraining.EncounterLevel(p, 102) == 0, "A dead recipient generated support rewards.");
        });
        Test("Invalid encounter input fails before mutation and corrupt metadata fails closed", () =>
        {
            var p = new Character();
            foreach (var (level, at) in new[] { (0, 0d), (101, 0d), (1, double.NaN), (1, double.PositiveInfinity) })
            {
                string before = Json(p); bool rejected = false;
                try { SupportTraining.Record(p, level, at); } catch (RuleException) { rejected = true; }
                Need(rejected && Json(p) == before, "Invalid contact changed state.");
            }
            p.RecentLearningEncounter = new LearningEncounter { EnemyLevel = 1, Zone = p.Zone, At = double.NaN };
            Need(SupportTraining.EncounterLevel(p, 100) == 0, "Non-finite timestamp granted experience.");
            SupportTraining.Record(p, 1, 100);
            foreach (double time in new[] { double.NaN, double.PositiveInfinity, double.NegativeInfinity })
                Need(SupportTraining.EncounterLevel(p, time) == 0, "Non-finite current time granted experience.");
        });
        Test("Real healing uses the contacted enemy rather than a high-level zone and replay cannot duplicate credit", () =>
        {
            var heal = data.Abilities.First(a => a.Kind == "heal" && a.Class != "");
            var engine = new RealmEngine(data);
            var p = engine.CreateCharacter("support-xp", "Support XP", heal.Class, new());
            string id = p.Id;
            foreach (var skill in data.Skills) p.SkillXp[skill.Id] = 50000;
            p.SkillXp[heal.Skill] = Progression.Threshold(Math.Min(100, heal.Requirement));
            var zone = data.Zones.First(z => z.Kind == "wilderness" && z.Level >= 60);
            p.Zone = zone.Id; p.Position = zone.Spawn; p.Inventory.Clear(); p.Equipment.Clear();
            p.Health = 20; p.Mana = 1000; p.Stamina = 1000;
            var rat = engine.State.Creatures.Values.First(m => m.Template == "field_rat" && m.Owner == "");
            rat.Zone = zone.Id; rat.Position = p.Position; rat.Health = 10000;
            var hit = engine.Execute(id, new GameCommand { Kind = "attack", Target = rat.Id,
                Sequence = p.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") });
            Need(hit.Ok, "Fixture attack failed: " + hit.Message);
            p = engine.Player(id);
            Need(SupportTraining.EncounterLevel(p, engine.State.Time) == data.Mob(rat.Template).Level,
                "Actual damage did not record its hostile difficulty.");
            var expected = Wire.Copy(p);
            var stats = CombatMath.Stats(expected, data);
            double power = (heal.Element == Element.Physical ? stats.Physical : stats.Spell) * heal.Power
                * CombatTrainingCurve.Spell(Progression.Level(expected, heal.Skill));
            double amount = Math.Min(stats.Health - expected.Health, power * stats.Healing);
            ChallengeProgression.TrainCombat(expected, heal.Skill, Math.Max(1, (int)amount / 2), data.Mob(rat.Template).Level, data);
            var cast = new GameCommand { Kind = "cast", Item = heal.Id, Sequence = p.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
            var healed = engine.Execute(id, cast); Need(healed.Ok, "Healing failed: " + healed.Message);
            p = engine.Player(id);
            Need(p.Health > 20, "Valid healing stopped restoring health.");
            Need(Json(p.SkillXp) == Json(expected.SkillXp) && Json(p.CombatPracticeRemainders) == Json(expected.CombatPracticeRemainders)
                && p.PracticeOnlyXp == expected.PracticeOnlyXp && p.OverallCreditRemainder == expected.OverallCreditRemainder,
                "Support rewards used region level or bypassed challenge fractions.");
            string complete = Json(engine.State); var replay = engine.Execute(id, cast);
            Need(replay.Ok && Json(engine.State) == complete, "Replayed healing changed health, mana or XP twice.");
        });
        Test("No hostile contact, expired contact and cross-region contact permit healing but not experience", () =>
        {
            var heal = data.Abilities.First(a => a.Kind == "heal" && a.Class != "");
            foreach (string invalid in new[] { "missing", "expired", "foreign" })
            {
                var engine = new RealmEngine(data);
                var p = engine.CreateCharacter("support-no-xp-" + invalid, "Support " + invalid, heal.Class, new());
                p.SkillXp[heal.Skill] = Progression.Threshold(heal.Requirement);
                p.Health = 10; p.Mana = 1000; p.LastCombat = engine.State.Time;
                if (invalid != "missing") SupportTraining.Record(p, 80, invalid == "expired" ? engine.State.Time - 16 : engine.State.Time);
                if (invalid == "foreign") p.RecentLearningEncounter!.Zone = "another-region";
                string skills = Json(p.SkillXp); string practice = Json(p.CombatPracticeRemainders);
                long overall = p.PracticeOnlyXp;
                var result = engine.Execute(p.Id, new GameCommand { Kind = "cast", Item = heal.Id,
                    Sequence = p.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") });
                Need(result.Ok && engine.Player(p.Id).Health > 10, invalid + " contact incorrectly blocked healing: " + result.Message);
                var after = engine.Player(p.Id);
                Need(Json(after.SkillXp) == skills && Json(after.CombatPracticeRemainders) == practice && after.PracticeOnlyXp == overall,
                    invalid + " contact manufactured support experience.");
            }
        });
        Console.WriteLine($"SUPPORT XP: {passed} groups passed; total failures {failures.Count}.");
    }
}
