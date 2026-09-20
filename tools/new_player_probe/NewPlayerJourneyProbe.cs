using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Nodes;
using Kairnfall.Core;

namespace Kairnfall.Probes;

/// <summary>
/// Bounded gameplay-API journey and adversarial fixtures. Proximity fixtures and controlled
/// clocks keep the check deterministic; no timing claim or human first-hour approval is implied.
/// Rewards, combat, quests, crafting, socketing, equipment, transitions and event participation
/// are executed through RealmEngine.Execute, not through tutorial state.
/// </summary>
public static class NewPlayerJourneyProbe
{
    private static void Need([DoesNotReturnIf(false)] bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }
    private static string Economy(Character player) => JsonSerializer.Serialize(new
    {
        player.Gold, player.Inventory, player.Bank, player.Equipment, player.SkillXp,
        player.PracticeOnlyXp, player.OverallCreditRemainder, player.Reputation,
        player.Quests, player.CompletedQuests, player.PublicEventsCompleted, player.Bestiary
    }, Wire.Json);

    private sealed class Fixture
    {
        public Catalog Data { get; }
        public RealmEngine Realm { get; set; }
        public string Id { get; }
        public Character Player => Realm.Player(Id);
        public Snapshot Snapshot => Realm.Snapshot(Id);
        public Fixture(Catalog data, string suffix)
        {
            Data = data; Realm = new(data);
            Id = Realm.CreateCharacter("new-player-" + suffix, "Journey " + suffix, "vanguard", new()).Id;
            Realm.Active.Add(Id);
        }
        public void CompleteOpening()
        {
            // Keep the existing workshop, rune, loot, settlement and public-event
            // assertions below. Reach them through the new opening, never by writing
            // completion flags or opting a fresh character out of the new journey.
            var giver = OpeningJourney.Giver(Data);
            Npc(giver.Id); Act("talk", giver.Id);
            Act("accept_quest", item: OpeningJourney.FightQuest);
            for (int victory = 0; victory < OpeningJourney.KillGoal; victory++)
            {
                var rat = Realm.State.Creatures.Values.Where(x => x.Zone == OpeningJourney.Home
                    && x.Template == OpeningJourney.Foe && x.Health > 0 && x.Owner == "")
                    .OrderBy(x => x.Position.Distance(Player.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
                Need(rat is not null, "The opening lacks a living reachable Field Rat without a respawn wait.");
                Place(rat.Position);
                var guidance = Next();
                Need(guidance.Stage == "combat" && guidance.TargetKind == "creature"
                    && Realm.State.Creatures[guidance.TargetId].Template == OpeningJourney.Foe,
                    "The actual opening objective did not identify a starter Field Rat.");
                for (int strike = 0; rat.Health > 0 && strike < 80; strike++)
                { Place(rat.Position); Act("attack", rat.Id); Advance(2); }
                Need(rat.Health <= 0 && OpeningJourney.Kills(Player) == victory + 1,
                    "The actual starter victory did not advance the authoritative opening exactly once.");
            }
            Npc(giver.Id); Act("claim_quest", item: OpeningJourney.FightQuest);
            string reward = OpeningJourney.RewardId(Player);
            Need(reward != "" && Player.Inventory.Any(x => x.Id == reward), "The guaranteed upgrade was not delivered.");
            var beforeEquip = Wire.Copy(Player); Act("equip", item: reward);
            Need(OpeningJourney.Equipped(Player) && ProgressionFeedback.PowerChanges(Data,beforeEquip,Player).Count > 0,
                "The real earned weapon did not produce a meaningful equipment improvement.");
            var recipe = Data.Recipe(OpeningJourney.Recipe);
            var station = Data.Npcs.First(x => x.Zone == OpeningJourney.Home && x.Station == recipe.Station);
            Npc(station.Id); int beforePotions = Items.Count(Player, "healing_potion");
            Act("craft", item: recipe.Id); Advance(3);
            Need(OpeningJourney.Crafted(Player) && Items.Count(Player,"healing_potion") == beforePotions + recipe.Quantity,
                "The real alchemy recipe did not deliver the useful opening output.");
            Npc(giver.Id); Act("claim_quest", item: OpeningJourney.CraftQuest);
            Need(OpeningJourney.Finished(Player) && OpeningJourney.Recommend(Data,Snapshot) is null,
                "Completed opening did not return control to the existing world journey.");
            string beforeRestart = Economy(Player);
            Realm = new RealmEngine(Data, Wire.Copy(Realm.State)) { Loot = Wire.Copy(Realm.Loot) }; Realm.Active.Add(Id);
            Need(OpeningJourney.Finished(Player) && beforeRestart == Economy(Player),
                "Restart lost opening progress or changed its reward identities.");
        }
        public JourneyObjective Next()
        {
            var next = NewPlayerJourney.Recommend(Data, Snapshot, Realm.VisibleLoot(Id));
            Need(next.Stage != "" && next.Title != "" && next.Objective != "" && next.Why != "", "A progression stage lost its meaningful objective.");
            Need(Data.Zones.Any(x => x.Id == next.Zone), "Recommendation names a nonexistent zone.");
            var navigation = NewPlayerJourney.Navigation(Data, Player, next);
            if (navigation.Position is { } position) Need(WorldMap.Fits(Data.Zone(Player.Zone), position), "Navigation points into blocked terrain.");
            return next;
        }
        public GameCommand Act(string kind, string target = "", string item = "", string arg = "", int amount = 1)
        {
            var command = new GameCommand { Kind = kind, Target = target, Item = item, Arg = arg, Amount = amount,
                Sequence = Player.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
            var result = Realm.Execute(Id, command);
            Need(result.Ok, kind + " failed: " + result.Message);
            Next(); return command;
        }
        public void Reject(GameCommand command)
        {
            command.Sequence = Player.LastAction + 1; command.RequestId = Guid.NewGuid().ToString("N");
            string before = JsonSerializer.Serialize(Player, Wire.Json);
            var result = Realm.Execute(Id, command);
            Need(!result.Ok, "Rejected command unexpectedly succeeded: " + command.Kind + "/" + command.Arg);
            Need(before == JsonSerializer.Serialize(Player, Wire.Json), "A rejected command mutated character state.");
            Next();
        }
        public void Place(Point position)
        {
            var zone = Data.Zone(Player.Zone);
            Need(WorldMap.Fits(zone, position), "Fixture interaction is not actor-fit.");
            Need(position.Distance(Player.Position) < 1 || WorldMap.FindPath(zone, Player.Position, position, zone.Width * zone.Height * 2).Count > 0,
                "The real interaction cannot be reached from the previous milestone.");
            Player.Position = position;
        }
        public void Advance(double seconds)
        {
            double until = Realm.State.Time + seconds;
            while (Realm.State.Time + .0001 < until) Realm.Tick(.1);
        }
        public void Npc(string id) { var npc = Data.Npc(id); Need(npc.Zone == Player.Zone, "NPC is in another region."); Place(npc.Position); }
        public void Travel(string destination)
        {
            for (int hop = 0; Player.Zone != destination && hop < 12; hop++)
            {
                var exit = NewPlayerJourney.FirstExit(Data, Player, destination);
                Need(exit is not null, "No legitimate entry-level route to " + destination);
                Place(exit.Position); Act("transition", exit.Id); Advance(2);
            }
            Need(Player.Zone == destination, "Route did not reach its real destination.");
        }
    }

    public static int Run(Catalog data)
    {
        int passed = 0; var failures = new List<string>(); Fixture? journey = null; bool journeyCompleted = false;
        string footprint = JsonSerializer.Serialize(data.Zones.Select(x => new { x.Id, x.Width, x.Height, x.WorldX, x.WorldY, x.Exits }), Wire.Json);
        void Test(string name, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS NEW PLAYER JOURNEY: " + name); }
            catch (Exception error) { failures.Add(name + ": " + error.Message); Console.WriteLine("FAIL NEW PLAYER JOURNEY: " + name + ": " + error); }
        }
        Test("fresh characters get a real introductory NPC, route, why and reward preview", () =>
        {
            var fixture = new Fixture(data, "Fresh"); var player = fixture.Player;
            var next = fixture.Next(); var first = data.Quest(OpeningJourney.FightQuest);
            Need(NewPlayerJourney.Active(player) && next.Stage == "quest_offer" && next.TargetId == first.Giver, "Fresh spawn did not recommend the actual introductory giver.");
            Need(NewPlayerJourney.Available(player, first, fixture.Realm.State.Time), "The first recommendation is not legitimately available.");
            Need(next.Reward.Contains(first.Gold.ToString(), StringComparison.Ordinal), "Quest preview lost its authored gold.");
            Need(NewPlayerJourney.NextHint(data, fixture.Snapshot, next)?.Id == "movement", "Initial guidance is not contextual movement guidance.");
            Need(fixture.Snapshot.Players.Count == 0, "Fresh objective incorrectly requires another player.");
            string unchanged = JsonSerializer.Serialize(fixture.Realm.State, Wire.Json);
            for (int i = 0; i < 20; i++) { fixture.Next(); ProgressionFeedback.FindUpgrade(data, player); }
            Need(unchanged == JsonSerializer.Serialize(fixture.Realm.State, Wire.Json), "Presentation evaluation mutated the world.");
        });
        Test("real journey: movement, combat, loot, rune, crafting, quest reward and first settlement", () =>
        {
            var fixture = new Fixture(data, "Road"); journey = fixture;
            var initial = Wire.Copy(fixture.Player); var initialPosition = fixture.Player.Position;
            for (int i = 0; i < 5; i++)
            {
                var movement = new GameCommand { Kind = "move", X = 1, Y = 0, RequestId = Guid.NewGuid().ToString("N") };
                Need(fixture.Realm.Execute(fixture.Id, movement).Ok, "Normal movement command failed."); fixture.Realm.Tick(.1);
            }
            Need(fixture.Player.Position.Distance(initialPosition) > .1 && FirstHourExperience.Marked(fixture.Player, "movement"), "Actual movement did not retire the movement hint.");
            Need(fixture.Realm.Execute(fixture.Id, new GameCommand { Kind = "move", X = 0, Y = 0 }).Ok, "Normal movement stop failed.");
            fixture.CompleteOpening();
            fixture.Npc(data.Quest("main_01").Giver); fixture.Act("talk", data.Quest("main_01").Giver); fixture.Act("accept_quest", item: "main_01");
            // Both actual opening kills leave ordinary owned loot. The mandatory
            // equip/craft chain stays prioritized until complete; then normal loot
            // guidance resumes instead of forcing another unrelated fight.
            var loot = fixture.Realm.VisibleLoot(fixture.Id).FirstOrDefault(x => x.Owner == fixture.Id);
            Need(loot is not null, "A real defeated starter foe left no owned loot.");
            fixture.Place(loot.Position); Need(fixture.Next().Stage == "loot", "The first real loot drop was not prioritized.");
            fixture.Act("loot", loot.Id);
            Need(fixture.Player.Discoveries.Contains(NewPlayerJourney.MilestoneKey("loot")), "Successful loot was not persisted as understood.");
            fixture.Npc(data.Quest("starter_rune").Giver); fixture.Act("accept_quest", item: "starter_rune");
            var beforeSocket = Wire.Copy(fixture.Player);
            string weapon = fixture.Player.Equipment["weapon"], rune = fixture.Player.Inventory.Single(x => x.Template == "rune_embers_1").Id;
            fixture.Act("socket", weapon, rune);
            Need(ProgressionFeedback.Between(data, beforeSocket, fixture.Player).Any(x => x.Kind == "equipment"), "The real rune improvement has no power-change feedback.");
            fixture.Act("claim_quest", item: "starter_rune");
            var nodes = fixture.Realm.State.Nodes.Values.Where(x => x.Zone == "wayfarers_rest" && data.Resources.Any(r => r.Id == x.Template && r.Item == "oak_log")).Take(3).ToArray();
            Need(nodes.Length == 3, "The opening resource chain no longer has three available authored nodes.");
            foreach (var node in nodes) { fixture.Place(node.Position); fixture.Act("gather", node.Id); fixture.Advance(2); }
            var plank = data.Recipes.First(x => x.Output == "oak_plank" && x.Requirement == 1);
            var handle = data.Recipes.First(x => x.Output == "wooden_handle" && x.Requirement == 1);
            fixture.Npc(data.Npcs.First(x => x.Zone == "wayfarers_rest" && x.Station == "sawbench").Id);
            Need(fixture.Next().TargetId == plank.Id, "Guidance skipped the necessary log-to-plank intermediate recipe.");
            fixture.Act("craft", item: plank.Id); fixture.Advance(3);
            Need(fixture.Next().TargetId == handle.Id, "Guidance did not advance from planks to the handle.");
            fixture.Act("craft", item: handle.Id); fixture.Advance(3);
            fixture.Npc("wayfarers_rest_blacksmith"); fixture.Act("talk", "wayfarers_rest_blacksmith");
            Need(fixture.Player.Quests["main_01"].Complete, "Real opening objectives did not become claimable.");
            fixture.Npc(data.Quest("main_01").Giver); long beforeGold = fixture.Player.Gold;
            var claim = fixture.Act("claim_quest", item: "main_01");
            Need(fixture.Player.Gold == beforeGold + data.Quest("main_01").Gold && Items.Count(fixture.Player, "sealed_letter") == 1, "Opening quest reward differs from the authored reward.");
            string afterClaim = Economy(fixture.Player);
            Need(fixture.Realm.Execute(fixture.Id, claim).Ok && Economy(fixture.Player) == afterClaim, "Immediate quest receipt replay duplicated a reward.");
            fixture.Realm = new RealmEngine(data, Wire.Copy(fixture.Realm.State)); fixture.Realm.Active.Add(fixture.Id);
            Need(fixture.Realm.Execute(fixture.Id, claim).Ok && Economy(fixture.Player) == afterClaim, "Quest reward duplicated across restart.");
            fixture.Reject(new GameCommand { Kind = "claim_quest", Item = "main_01" });
            int level = Progression.PlayerLevel(fixture.Player);
            Need(level >= 2 && ProgressionFeedback.Between(data, initial, fixture.Player).Any(x => x.Kind == "level" && x.Level == level), "First level feedback did not follow real earned progression.");
            fixture.Travel("kingsmeadow"); fixture.Next(); fixture.Travel("dawnreach");
            fixture.Npc(data.Quest("main_02").Giver); fixture.Act("accept_quest", item: "main_02");
            Need(fixture.Player.Zone == "dawnreach" && fixture.Player.Quests.ContainsKey("main_02"), "The earned letter did not lead to the first settlement quest.");
            Need(Items.Validate(fixture.Realm.State, data).Count == 0, "The opening journey violated inventory invariants.");
            journeyCompleted = true;
            Console.WriteLine($"NEW_PLAYER_JOURNEY_MILESTONES: medicine quest -> two kills -> guaranteed weapon -> equip -> potions -> return -> loot -> rune -> planks -> handle -> claim -> Dawnreach; level={level}; one-time server-owned opening reward");
        });
        Test("usable equipment upgrades are real stat improvements and equip stays authoritative", () =>
        {
            var fixture = new Fixture(data, "Equipment");
            Need(ProgressionFeedback.FindUpgrade(data, fixture.Player) is null, "An arbitrary starter supply was classified as an equipment upgrade.");
            var candidate = Wire.Copy(fixture.Player.Inventory.Single(x => x.Id == fixture.Player.Equipment["weapon"]));
            candidate.Id = Guid.NewGuid().ToString("N"); candidate.Rarity = (Rarity)1; candidate.Affixes.Clear(); candidate.Runes.Clear();
            var pile = new LootPile { Id = Guid.NewGuid().ToString("N"), Owner = fixture.Id, Zone = fixture.Player.Zone,
                Position = fixture.Player.Position, Expires = 1000, PublicAt = 1000, Gold = 3, Items = [candidate] };
            fixture.Realm.Loot[pile.Id] = pile; var before = Wire.Copy(fixture.Player);
            fixture.Act("loot", pile.Id);
            var upgrade = ProgressionFeedback.FindUpgrade(data, fixture.Player);
            Need(upgrade?.ItemId == candidate.Id, "A usable higher-power version of the same weapon was not identified.");
            Need(fixture.Player.Equipment["weapon"] == before.Equipment["weapon"], "Receiving an upgrade auto-equipped it.");
            Need(ProgressionFeedback.Between(data, before, fixture.Player).Any(x => x.Kind == "upgrade"), "Receiving an upgrade has no presentation marker.");
            string unchanged = Economy(fixture.Player); ProgressionFeedback.FindUpgrade(data, fixture.Player);
            Need(Economy(fixture.Player) == unchanged, "Upgrade inspection mutated equipment or progression.");
            var beforeEquip = Wire.Copy(fixture.Player); fixture.Act("equip", item: candidate.Id);
            Need(fixture.Player.Equipment["weapon"] == candidate.Id && ProgressionFeedback.PowerChanges(data, beforeEquip, fixture.Player).Count > 0, "The normal equip API did not apply the advertised gain.");
            Need(fixture.Player.Discoveries.Contains(NewPlayerJourney.MilestoneKey("equipment")), "A real successful equipment improvement was not recorded.");
            var broken = Wire.Copy(candidate); broken.Id = Guid.NewGuid().ToString("N"); broken.Rarity = (Rarity)3; broken.Durability = 0;
            fixture.Player.Inventory.Add(broken);
            Need(ProgressionFeedback.FindUpgrade(data, fixture.Player) is null, "A broken rare item was advertised as a usable upgrade.");
        });
        Test("hint flags persist and replay without changing gameplay progression", () =>
        {
            var fixture = new Fixture(data, "Hints"); string before = Economy(fixture.Player);
            var acknowledgement = fixture.Act("guide_ack", arg: "movement");
            Need(Economy(fixture.Player) == before && NewPlayerJourney.Seen(fixture.Player, "movement"), "A guidance acknowledgement changed gameplay state or was not saved.");
            fixture.Realm = new RealmEngine(data, Wire.Copy(fixture.Realm.State)); fixture.Realm.Active.Add(fixture.Id);
            Need(NewPlayerJourney.Seen(fixture.Player, "movement"), "Guidance completion vanished after reload.");
            long sequence = fixture.Player.LastAction;
            Need(fixture.Realm.Execute(fixture.Id, acknowledgement).Ok && fixture.Player.LastAction == sequence, "A persisted hint receipt did not replay idempotently.");
            fixture.Act("guide_ack", arg: "movement");
            Need(fixture.Player.Discoveries.Count(x => x == NewPlayerJourney.HintKey("movement")) == 1 && Economy(fixture.Player) == before,
                "A new request duplicated hint completion or granted a reward.");
        });
        Test("malicious guidance payloads cannot grant XP items gold reputation or event credit", () =>
        {
            var fixture = new Fixture(data, "Authority");
            foreach (string forged in new[] { "xp", "items", "gold", "reputation", "public_scheduled", "milestone:loot", "eligible", "quest:main_01", "../level" })
                fixture.Reject(new GameCommand { Kind = "guide_ack", Arg = forged });
            fixture.Reject(new GameCommand { Kind = "guide_ack", Arg = "level", Amount = int.MaxValue });
            fixture.Reject(new GameCommand { Kind = "guide_ack", Arg = "public", Target = "event/1", Item = "sealed_letter" });
            fixture.Reject(new GameCommand { Kind = "guide_ack", Arg = "movement", X = 5 });
            string before = Economy(fixture.Player); fixture.Act("guide_ack", arg: "level"); fixture.Act("guide_ack", arg: "public");
            Need(Economy(fixture.Player) == before && Progression.PlayerLevel(fixture.Player) == 1 && fixture.Player.PublicEventsCompleted == 0,
                "Claiming to understand a future hint conferred progression.");
            Need(!fixture.Player.Discoveries.Contains(NewPlayerJourney.PublicScheduledKey), "Client acknowledgement set a server scheduling milestone.");
        });
        Test("old saves are compatible and established characters are never forced through hints", () =>
        {
            var fixture = new Fixture(data, "Legacy"); fixture.Player.Discoveries.Remove(NewPlayerJourney.EligibleKey); fixture.Player.Discoveries.Remove(OpeningJourney.EligibleKey);
            FirstHourExperience.Mark(fixture.Player, "gather"); fixture.Player.Gold = 87;
            string before = Economy(fixture.Player);
            fixture.Realm = new RealmEngine(data, Wire.Copy(fixture.Realm.State)); fixture.Realm.Active.Add(fixture.Id);
            Need(Economy(fixture.Player) == before && FirstHourExperience.Marked(fixture.Player, "gather"), "Old progress or legacy markers were reset.");
            Need(!NewPlayerJourney.Active(fixture.Player) && NewPlayerJourney.NextHint(data, fixture.Snapshot, fixture.Next()) is null, "Old saves opted into a forced tutorial.");
            var json = JsonNode.Parse(JsonSerializer.Serialize(fixture.Player, Wire.Json))!.AsObject();
            string discoveryProperty = json.First(x => x.Key.Equals("discoveries", StringComparison.OrdinalIgnoreCase)).Key;
            json.Remove(discoveryProperty);
            var missing = JsonSerializer.Deserialize<Character>(json.ToJsonString(), Wire.Json)!;
            Need(missing.Discoveries is not null && !NewPlayerJourney.Active(missing), "Missing historical discovery fields have unsafe defaults.");
            var veteran = new Fixture(data, "Veteran"); veteran.Player.SkillXp[data.Skills[0].Id] = Progression.PlayerThreshold(20);
            Need(!NewPlayerJourney.Active(veteran.Player) && NewPlayerJourney.NextHint(data, veteran.Snapshot, veteran.Next()) is null,
                "Established progression was treated as a new character.");
        });
        Test("no-foe, stale-loot, death, and unavailable-prerequisite states retain legitimate goals", () =>
        {
            var fixture = new Fixture(data, "Fallback"); fixture.Npc(OpeningJourney.Giver(data).Id); fixture.Act("accept_quest", item: OpeningJourney.FightQuest);
            var snapshot = fixture.Snapshot; snapshot.Creatures.Clear(); snapshot.Events.Clear();
            var next = NewPlayerJourney.Recommend(data, snapshot);
            Need(next.Stage == "combat" && next.Zone == OpeningJourney.Home && next.TargetId == "" && next.Why.Contains("No living",StringComparison.Ordinal), "An empty nearby snapshot targeted a dead foe, skipped the mandatory fight or lost the recovery explanation.");
            snapshot.Self.Health = 0;
            Need(NewPlayerJourney.Recommend(data, snapshot).Stage == "recovery", "Death has no explicit recovery recommendation.");
            Need(!NewPlayerJourney.Available(fixture.Player, data.Quest("starter_hunt"), fixture.Realm.State.Time), "The introductory elite prerequisite was skipped.");
            var stale = new LootPile { Owner = fixture.Id, Zone = fixture.Player.Zone, Position = fixture.Player.Position, Expires = -1 };
            snapshot.Self.Health = fixture.Player.Health;
            Need(NewPlayerJourney.Recommend(data, snapshot, [stale]).Stage != "loot", "Expired loot stranded the objective tracker.");
        });
        Test("identical snapshots and character switches cannot fabricate level-up feedback", () =>
        {
            Need(journey is not null && journeyCompleted, "The real journey must complete before checking earned feedback.");
            var player = Wire.Copy(journey.Player);
            Need(ProgressionFeedback.Between(data, player, Wire.Copy(player)).Count == 0, "A repeated snapshot produced duplicate progression feedback.");
            var other = Wire.Copy(player); other.Id = Guid.NewGuid().ToString("N");
            Need(ProgressionFeedback.Between(data, player, other).Count == 0, "Switching characters fabricated progression.");
            var unchanged = Wire.Copy(player); unchanged.Discoveries.Add(NewPlayerJourney.HintKey("level"));
            Need(ProgressionFeedback.Between(data, player, unchanged).Count == 0, "A tutorial flag manufactured a level-up event.");
        });
        Test("a solo newcomer discovers and completes the existing scheduled public event", () =>
        {
            Need(journey is not null && journeyCompleted, "The real journey must complete before public discovery.");
            var fixture = journey; fixture.Travel("kingsmeadow");
            foreach (var old in fixture.Realm.State.Events.ToArray()) WorldEventLifecycle.CleanupOwned(fixture.Realm.State, old.Id);
            fixture.Realm.State.Events.Clear(); // Controlled empty event calendar, not a gameplay/reward shortcut.
            fixture.Realm.State.Time = WorldEventRules.SpawnCadence; fixture.Realm.Tick(.1);
            var activity = fixture.Realm.State.Events.SingleOrDefault(x => x.Zone == "kingsmeadow" && x.Status == "active");
            Need(activity is not null && activity.Kind == "treasure_surge", "The first road journey did not receive its bounded existing-event scheduling preference.");
            Need(activity.Id == "event/1" && activity.Goal == WorldEventRules.ScaledGoal("treasure_surge", 0, 1), "Introduction created a separate event architecture or changed standard scaling.");
            Need(fixture.Player.Discoveries.Contains(NewPlayerJourney.PublicScheduledKey) && fixture.Snapshot.Players.Count == 0, "Solo introduction depends on another human or lacks its persisted scheduling marker.");
            Need(NewPlayerJourney.NearbyEvent(data, fixture.Snapshot)?.Id == activity.Id && fixture.Next().Stage == "public", "The nearby introductory activity has no actionable discovery.");
            string beforeAck = Economy(fixture.Player); fixture.Act("guide_ack", arg: "public");
            Need(Economy(fixture.Player) == beforeAck && WorldEventRules.Contribution(activity, fixture.Id) == 0 && fixture.Next().Stage != "public",
                "Skipping a public introduction granted credit or stranded the main route.");
            var chests = fixture.Realm.State.Chests.Values.Where(x => WorldEventRules.Owns(activity, x.Id)).ToArray();
            Need(chests.Length == 4, "Solo activity does not have its standard four shared caches.");
            GameCommand? firstChest = null;
            foreach (var chest in chests)
            {
                fixture.Place(chest.Position); var command = fixture.Act("chest", chest.Id); firstChest ??= command;
                fixture.Advance(2);
            }
            Need(activity.Status == "success" && fixture.Player.PublicEventsCompleted == 1 && WorldEventRules.RewardEligible(activity, WorldEventRules.Contribution(activity, fixture.Id)),
                "Real solo contributions did not earn the existing authoritative event reward.");
            string rewarded = Economy(fixture.Player);
            Need(firstChest is not null && fixture.Realm.Execute(fixture.Id, firstChest).Ok && Economy(fixture.Player) == rewarded, "Replaying a cache command duplicated event or chest rewards.");
            fixture.Realm = new RealmEngine(data, Wire.Copy(fixture.Realm.State)); fixture.Realm.Active.Add(fixture.Id); fixture.Advance(2);
            Need(Economy(fixture.Player) == rewarded && fixture.Player.PublicEventsCompleted == 1 && fixture.Player.Discoveries.Contains(NewPlayerJourney.PublicScheduledKey),
                "Restart duplicated a public reward or lost the introduction marker.");
            fixture.Reject(new GameCommand { Kind = "chest", Target = chests[0].Id });
            fixture.Next();
        });
        Test("noncontributors cannot obtain event rewards through social or guidance actions", () =>
        {
            var fixture = new Fixture(data, "Contribution"); fixture.Player.CompletedQuests.Add("main_01");
            fixture.Player.Zone = "kingsmeadow"; fixture.Player.Position = data.Zone("kingsmeadow").Spawn;
            var observer = fixture.Realm.CreateCharacter("new-player-observer", "Quiet Observer", "vanguard", new());
            observer.Zone = fixture.Player.Zone; observer.Position = fixture.Player.Position; fixture.Realm.Active.Add(observer.Id);
            fixture.Realm.Tick(.1);
            var activity = fixture.Realm.State.Events.Single(x => x.Kind == "treasure_surge");
            var ack = new GameCommand { Kind = "guide_ack", Arg = "public", RequestId = Guid.NewGuid().ToString("N"), Sequence = observer.LastAction + 1 };
            Need(fixture.Realm.Execute(observer.Id, ack).Ok && WorldEventRules.Contribution(activity, observer.Id) == 0, "An observer earned contribution from a hint.");
            long gold = observer.Gold; string inventory = JsonSerializer.Serialize(observer.Inventory, Wire.Json);
            foreach (var chest in fixture.Realm.State.Chests.Values.Where(x => WorldEventRules.Owns(activity, x.Id)).ToArray())
            { fixture.Place(chest.Position); fixture.Act("chest", chest.Id); fixture.Advance(2); }
            Need(activity.Status == "success" && observer.PublicEventsCompleted == 0 && observer.Gold == gold && JsonSerializer.Serialize(observer.Inventory, Wire.Json) == inventory,
                "A noncontributing observer received event rewards.");
        });
        Test("public discovery suppresses distant, expired and inappropriate activities", () =>
        {
            var fixture = new Fixture(data, "Relevance"); var snapshot = fixture.Snapshot;
            var activity = new WorldEvent { Id = "relevance", Kind = "treasure_surge", Zone = fixture.Player.Zone, Position = fixture.Player.Position,
                Status = "active", StageEnds = 100, Ends = 100, Goal = 4 };
            snapshot.Events.Add(activity);
            Need(NewPlayerJourney.NearbyEvent(data, snapshot)?.Id == activity.Id, "An eligible local activity is undiscoverable.");
            activity.Position = new Point(1000, 1000);
            Need(NewPlayerJourney.NearbyEvent(data, snapshot) is null, "Distant events generated nearby activity guidance.");
            activity.Position = fixture.Player.Position; activity.Kind = "world_boss";
            Need(NewPlayerJourney.NearbyEvent(data, snapshot) is null, "A fresh player was advertised an inappropriate boss activity.");
            activity.Kind = "treasure_surge"; activity.Ends = -1;
            Need(NewPlayerJourney.NearbyEvent(data, snapshot) is null, "Expired activity remained actionable.");
        });
        Test("legacy event scheduling and the overworld footprint remain intact", () =>
        {
            var fixture = new Fixture(data, "Schedule"); fixture.Player.CompletedQuests.Add("main_01");
            fixture.Player.Zone = "kingsmeadow"; fixture.Player.Position = data.Zone("kingsmeadow").Spawn;
            fixture.Player.Discoveries.Remove(NewPlayerJourney.EligibleKey); fixture.Realm.Tick(.1);
            Need(fixture.Realm.State.Events.Single().Kind == WorldEventRules.Kinds[0] && !fixture.Player.Discoveries.Contains(NewPlayerJourney.PublicScheduledKey),
                "A historical character changed the existing scheduled event sequence.");
            Need(footprint == JsonSerializer.Serialize(data.Zones.Select(x => new { x.Id, x.Width, x.Height, x.WorldX, x.WorldY, x.Exits }), Wire.Json),
                "Onboarding altered the overworld footprint or exit graph.");
            Need(WorldEventRules.SpawnCadence == 240 && WorldEventRules.RewardContributionFloor == 4 && WorldEventRules.StageCount("treasure_surge") == 1,
                "Onboarding changed the existing public-event cadence, contribution floor or stages.");
        });
        Console.WriteLine($"NEW_PLAYER_JOURNEY: {passed}/{passed + failures.Count} groups passed. Bounded APIs and native contracts; human first-hour timing/retention remains unmeasured.");
        if (failures.Count > 0) throw new InvalidOperationException("New-player journey failures: " + string.Join(" | ", failures));
        return passed;
    }
}
