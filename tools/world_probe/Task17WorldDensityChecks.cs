using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using Kairnfall.Core;

internal static class Task17WorldDensityChecks
{
    [ModuleInitializer]
    internal static void VerifyTask17WorldDensity()
    {
        const string catalogPath = "content/catalog.json";
        if (!File.Exists(catalogPath))
            throw new InvalidDataException("Task 17 checks require content/catalog.json.");

        var data = Catalog.Load(catalogPath);
        var failures = new List<string>();
        int passed = 0;
        void Need(bool condition, string message)
        {
            if (!condition) throw new InvalidOperationException(message);
        }
        void Check(string name, Action body)
        {
            try
            {
                body();
                passed++;
                Console.WriteLine("PASS TASK17 DENSITY: " + name);
            }
            catch (Exception error)
            {
                failures.Add(name + ": " + error.Message);
                Console.WriteLine("FAIL TASK17 DENSITY: " + name + ": " + error.Message);
            }
        }

        (string Id, string Parent, string Specialist, string? Dungeon)[] settlements =
        [
            ("reedhaven", "mosswater", "alchemist", "chorus_caverns"),
            ("millcross", "westfarms", "carpenter", "broken_mill"),
            ("pinewatch", "pinewatch_reach", "woodworker", "watchers_nest"),
            ("brambleford", "thistle_woods", "tailor", null),
            ("stonebridge", "silver_run", "fletcher", "silken_tollhouse"),
            ("copperstead", "ember_marches", "blacksmith", "sunken_foundry"),
            ("whitepost", "northern_moor", "tanner", "winterhorn_pass"),
            ("saltmere", "saltwind", "fisher", "unmoored_vault"),
            ("gullhaven", "gull_isles", "woodworker", "reef_sanctum"),
            ("dustwell", "dry_reach", "scholar", "regents_tomb"),
        ];

        Check("overworld footprint is unchanged", () =>
        {
            var surface = data.Zones.Where(z => z.Kind == "wilderness" && z.Layer == "Surface").ToArray();
            Need(surface.Length == 20, "Task 17 must retain exactly the 20 established surface wilderness regions.");
            Need(surface.Sum(z => (long)z.Width * z.Height) == 2_048_000,
                "Task 17 changed the established surface-wilderness tile footprint.");
        });

        Check("all minor settlements gain purposeful resident density", () =>
        {
            foreach (var row in settlements)
            {
                var residents = data.Npcs.Where(n => n.Zone == row.Id).ToArray();
                Need(residents.Length >= 6, row.Id + " has fewer than six purposeful residents.");
                Need(residents.Any(n => n.Id == row.Id + "_traveler"), row.Id + " lost its traveler.");
                Need(residents.Any(n => n.Id == row.Id + "_innkeeper"), row.Id + " lost its innkeeper.");
                Need(residents.Any(n => n.Id == row.Id + "_provisioner"), row.Id + " lost its provisioner.");
                Need(residents.Any(n => n.Id == row.Id + "_guard"), row.Id + " has no local guard.");
                Need(residents.Any(n => n.Id == row.Id + "_scribe"), row.Id + " has no local scribe.");
                Need(residents.Any(n => n.Id == row.Id + "_" + row.Specialist), row.Id + " has no local specialist.");
            }
        });

        Check("ten authored three-stage settlement chains reuse existing geography", () =>
        {
            var local = data.Quests.Where(q => q.Id.StartsWith("local_", StringComparison.Ordinal)).ToArray();
            Need(local.Length == 30, "Expected exactly 30 Task 17 settlement-chain quests.");
            Need(local.Select(q => q.Name).Distinct(StringComparer.Ordinal).Count() == local.Length,
                "Task 17 quest titles are not individually authored.");

            foreach (var row in settlements)
            {
                var first = data.Quest("local_" + row.Id + "_01");
                var second = data.Quest("local_" + row.Id + "_02");
                var third = data.Quest("local_" + row.Id + "_03");
                Need(first.Category == "regional" && second.Category == "regional" && third.Category == "regional",
                    row.Id + " chain lost regional classification.");
                Need(!first.Repeatable && !second.Repeatable && !third.Repeatable,
                    row.Id + " story chain must not become a repeatable reward farm.");
                Need(first.Prerequisite == "" && second.Prerequisite == first.Id && third.Prerequisite == second.Id,
                    row.Id + " chain prerequisite order is broken.");
                Need(first.Giver == row.Id + "_traveler", row.Id + " discovery stage no longer starts with its traveler.");
                Need(first.Objectives.Any(o => o.Action == "explore" && o.Target == row.Parent),
                    row.Id + " discovery stage does not reuse its parent region.");
                Need(first.Objectives.Count(o => o.Action == "survey" && o.Target.StartsWith(row.Parent + "_", StringComparison.Ordinal)) == 2,
                    row.Id + " discovery stage must investigate exactly two local waymarks.");
                Need(first.Objectives.Any(o => o.Action == "talk" && o.Target == row.Id + "_" + row.Specialist),
                    row.Id + " discovery stage does not consult its local specialist.");
                Need(second.Giver == row.Id + "_" + row.Specialist,
                    row.Id + " escalation stage is not owned by its local specialist.");
                Need(second.Objectives.Any(o => o.Action == "talk" && o.Target == row.Id + "_guard"),
                    row.Id + " escalation stage does not involve the local watch.");
                Need(third.Giver == row.Id + "_guard" && third.Objectives.Any(o => o.Action == "talk" && o.Target == row.Id + "_scribe"),
                    row.Id + " resolution stage does not close through guard/scribe settlement roles.");

                if (row.Dungeon is not null)
                {
                    var dungeon = data.Zone(row.Dungeon!);
                    Need(third.Objectives.Any(o => o.Action == "explore" && o.Target == dungeon.Id),
                        row.Id + " resolution does not reuse its existing dungeon.");
                    Need(third.Objectives.Any(o => o.Action == "boss" && o.Target == dungeon.Boss),
                        row.Id + " resolution does not use the authored dungeon guardian.");
                }
                else
                {
                    Need(third.Objectives.Any(o => o.Action == "kill") && third.Objectives.Count(o => o.Action == "survey") >= 2,
                        row.Id + " non-dungeon resolution lacks a substantial local road challenge.");
                }

                var actions = first.Objectives.Concat(second.Objectives).Concat(third.Objectives)
                    .Select(o => o.Action).Distinct(StringComparer.Ordinal).ToArray();
                Need(actions.Length >= 6, row.Id + " chain does not vary objective types enough.");
                foreach (var quest in new[] { first, second, third })
                foreach (var objective in quest.Objectives)
                    Need(JourneyProgression.ObjectiveGuidance(data, quest, objective).Length >= 12,
                        quest.Id + " has an objective without actionable navigation guidance: " + objective.Action + ":" + objective.Target);
            }
        });

        Check("normal investigation reveals optional cache clues without gating the chain", () =>
        {
            Need(ExplorationRewards.CacheClueLandmarks == 2, "The settlement discovery design assumes two waymarks reveal the existing cache clue.");
            foreach (var row in settlements)
            {
                var parent = data.Zone(row.Parent);
                Need(ExplorationRewards.Eligible(parent), row.Parent + " is no longer eligible for regional exploration rewards.");
                var first = data.Quest("local_" + row.Id + "_01");
                var surveyed = first.Objectives.Where(o => o.Action == "survey").Select(o => o.Target).ToHashSet(StringComparer.Ordinal);
                Need(ExplorationRewards.Landmarks(parent).Count(l => surveyed.Contains(l.Id)) == 2,
                    row.Id + " discovery stage no longer points at two real regional waymarks.");
                Need(!first.Objectives.Any(o => o.Action == "chest"),
                    row.Id + " incorrectly makes hidden-cache opening mandatory.");
            }
        });

        Check("new quest progress survives restart and rewards are exactly-once", () =>
        {
            var quest = data.Quest("local_millcross_01");
            RealmEngine realm = new(data);
            Character player = realm.CreateCharacter("task17-density", "Density Tester", "vanguard", new());
            string playerId = player.Id;
            int entry = JourneyProgression.EntryRequirement(data, data.Zone("westfarms"));
            player.SkillXp["exploration"] = Progression.PlayerThreshold(Math.Max(entry, quest.MinimumLevel));

            CommandResult Act(string kind, string target = "", string item = "", int amount = 1)
            {
                var command = new GameCommand { Kind = kind, Target = target, Item = item, Amount = amount, Sequence = player.LastAction + 1 };
                var result = realm.Execute(playerId, command);
                player = realm.Player(playerId);
                Need(result.Ok, kind + " failed: " + result.Message);
                return result;
            }

            var giver = data.Npc(quest.Giver);
            player.Zone = giver.Zone;
            player.Position = giver.Position;
            Act("accept_quest", item: quest.Id);
            Need(player.Quests.ContainsKey(quest.Id), "New settlement quest was not accepted authoritatively.");

            var settlement = data.Zone("millcross");
            var exit = settlement.Exits.Single(e => e.Target == "westfarms");
            player.Position = exit.Position;
            Act("transition", target: exit.Id);
            Need(player.Quests[quest.Id].Counts[0] == 1, "Authoritative transition did not advance the exploration objective.");

            var parent = data.Zone("westfarms");
            var surveys = quest.Objectives.Where(o => o.Action == "survey").ToArray();
            var firstLandmark = parent.Buildings.Single(b => b.Id == surveys[0].Target);
            player.Position = JourneyProgression.LandmarkPoint(firstLandmark);
            Act("inspect", target: firstLandmark.Id);
            Need(!ExplorationRewards.HasClue(player, parent), "Cache clue appeared before the authored two-waymark investigation.");

            var retainedCounts = player.Quests[quest.Id].Counts.ToArray();
            realm = new RealmEngine(data, Wire.Copy(realm.State));
            player = realm.Player(playerId);
            Need(retainedCounts.SequenceEqual(player.Quests[quest.Id].Counts),
                "Settlement quest progress changed across authoritative realm-state restart.");

            var secondLandmark = parent.Buildings.Single(b => b.Id == surveys[1].Target);
            player.Zone = parent.Id;
            player.Position = JourneyProgression.LandmarkPoint(secondLandmark);
            Act("inspect", target: secondLandmark.Id);
            Need(ExplorationRewards.HasClue(player, parent), "Two investigated waymarks did not reveal the existing optional cache clue.");
            Need(!ExplorationRewards.CacheOpened(player, parent), "The hidden cache was opened implicitly instead of remaining optional.");

            var specialistId = quest.Objectives.Single(o => o.Action == "talk").Target;
            var specialist = data.Npc(specialistId);
            player.Zone = specialist.Zone;
            player.Position = specialist.Position;
            Act("talk", target: specialist.Id);
            Need(player.Quests[quest.Id].Complete, "Settlement discovery stage did not complete after all authoritative objectives.");

            player.Zone = giver.Zone;
            player.Position = giver.Position;
            long goldBefore = player.Gold;
            int rewardBefore = Items.Count(player, quest.Reward);
            var claim = new GameCommand { Kind = "claim_quest", Item = quest.Id, Sequence = player.LastAction + 1 };
            var claimed = realm.Execute(playerId, claim);
            player = realm.Player(playerId);
            Need(claimed.Ok, "Settlement quest claim failed: " + claimed.Message);
            long goldAfter = player.Gold;
            int rewardAfter = Items.Count(player, quest.Reward);
            Need(goldAfter == goldBefore + quest.Gold, "Settlement quest gold reward was not authoritative.");
            Need(rewardAfter == rewardBefore + 1, "Settlement quest item reward was not granted exactly once.");
            Need(player.CompletedQuests.Contains(quest.Id) && !player.Quests.ContainsKey(quest.Id),
                "Claim did not atomically move the quest to completed state.");

            var replay = realm.Execute(playerId, claim);
            player = realm.Player(playerId);
            Need(replay.Ok, "Idempotent replay did not return the prior successful receipt.");
            Need(player.Gold == goldAfter && Items.Count(player, quest.Reward) == rewardAfter,
                "Replayed claim duplicated a settlement quest reward.");

            var duplicate = realm.Execute(playerId, new GameCommand
            {
                Kind = "claim_quest", Item = quest.Id, Sequence = player.LastAction + 1
            });
            player = realm.Player(playerId);
            Need(!duplicate.Ok, "Fresh duplicate claim was accepted.");
            Need(player.Gold == goldAfter && Items.Count(player, quest.Reward) == rewardAfter,
                "Rejected duplicate claim changed authoritative rewards.");

            realm = new RealmEngine(data, Wire.Copy(realm.State));
            player = realm.Player(playerId);
            Need(player.CompletedQuests.Contains(quest.Id) && !player.Quests.ContainsKey(quest.Id),
                "Completed settlement quest did not persist across restart.");
            Need(player.Gold == goldAfter && Items.Count(player, quest.Reward) == rewardAfter,
                "Restart changed the claimed settlement reward.");
        });

        Console.WriteLine($"TASK17 WORLD DENSITY: {passed} checks passed; {failures.Count} failed.");
        if (failures.Count > 0)
            throw new InvalidDataException("Task 17 world-density regression failed: " + string.Join(" | ", failures));
    }
}
