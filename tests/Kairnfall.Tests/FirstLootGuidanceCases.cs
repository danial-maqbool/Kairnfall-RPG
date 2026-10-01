using System.Text.Json;
using Kairnfall.Core;

public static class FirstLootGuidanceCases
{
    public static void Run(Action<string, Action> test, Catalog data)
    {
        void Check(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
        string Economy(Character player) => Json(new { player.Gold, player.Inventory, player.Bank, player.Equipment,
            player.SkillXp, player.Bestiary, player.Quests, player.CompletedQuests, player.Reputation,
            player.PracticeOnlyXp, player.OverallCreditRemainder });
        GameCommand Act(RealmEngine realm, Character player, string kind, string target = "", string item = "", string arg = "")
        {
            var command = new GameCommand { Kind = kind, Target = target, Item = item, Arg = arg,
                Sequence = player.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
            var result = realm.Execute(player.Id, command); Check(result.Ok, kind + " failed: " + result.Message); return command;
        }
        void Advance(RealmEngine realm, int ticks) { for (int n = 0; n < ticks; n++) realm.Tick(.1); }
        Creature NextRat(RealmEngine realm, Character player) => realm.State.Creatures.Values
            .Where(x => x.Zone == OpeningJourney.Home && x.Template == OpeningJourney.Foe && x.Owner == "" && x.Health > 0)
            .OrderBy(x => x.Position.Distance(player.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).First();
        void Kill(RealmEngine realm, Character player, Creature rat)
        {
            for (int strike = 0; rat.Health > 0 && strike < 20; strike++)
            {
                player.Position = rat.Position; Act(realm, player, "attack", rat.Id); Advance(realm, 20);
            }
            Check(rat.Health <= 0, "Authoritative starter attacks did not produce a kill.");
        }
        (RealmEngine Realm, Character Player, LootPile Pile) FirstKill()
        {
            var realm = new RealmEngine(data);
            var player = realm.CreateCharacter("first-loot", "First Loot", "vanguard", new()); realm.Active.Add(player.Id);
            var giver = OpeningJourney.Giver(data); player.Position = giver.Position;
            Act(realm, player, "talk", giver.Id); Act(realm, player, "accept_quest", item: OpeningJourney.FightQuest);
            Kill(realm, player, NextRat(realm, player));
            var pile = realm.Loot.Values.Single(x => x.Owner == player.Id);
            Check(OpeningJourney.Kills(player) == 1 && OpeningJourney.RewardId(player) == "", "Fixture skipped the real opening kill/reward order.");
            return (realm, player, pile);
        }
        void NearExpiry(RealmEngine realm, LootPile pile)
        {
            // Controlled reading-delay clock, not a human pacing measurement.
            // All kills, reward claims, pickups and acknowledgements remain real commands.
            realm.State.Time = pile.Expires - 30;
        }
        JourneyObjective Next(RealmEngine realm, Character player) => NewPlayerJourney.Recommend(data, realm.Snapshot(player.Id), realm.VisibleLoot(player.Id));

        test("Actual opening spoils gain a read-only warning only near their existing expiry", () =>
        {
            var (realm, player, pile) = FirstKill();
            Check(Next(realm, player).Stage == "combat", "Fresh loot displaced the ordinary opening fight.");
            double expiry = pile.Expires; NearExpiry(realm, pile);
            var snapshot = realm.Snapshot(player.Id); var visible = realm.VisibleLoot(player.Id);
            string beforeSnapshot = Json(snapshot), beforePlayer = Json(player), beforeLoot = Json(realm.Loot);
            for (int read = 0; read < 8; read++)
            {
                var objective = NewPlayerJourney.Recommend(data, snapshot, visible);
                Check(objective.Stage == "loot" && objective.TargetKind == "loot" && objective.TargetId == pile.Id
                    && objective.Title.StartsWith("Optional", StringComparison.Ordinal)
                    && objective.Objective.Contains("30s left", StringComparison.Ordinal) && objective.Why.Contains("30 seconds", StringComparison.Ordinal),
                    "Owned local spoils were suppressed by the mandatory fight near expiry.");
                Check(NewPlayerJourney.NextHint(data, snapshot, objective)?.Id == "loot",
                    "Got it would acknowledge another hint instead of dismissing the urgent reminder.");
            }
            Check(Json(snapshot) == beforeSnapshot && Json(player) == beforePlayer && Json(realm.Loot) == beforeLoot && pile.Expires == expiry,
                "Reading loot guidance changed a snapshot, character, rewards or expiry.");
        });

        test("Urgent-loot dismissal is only the accepted hint acknowledgement and persists across reload", () =>
        {
            var (realm, player, pile) = FirstKill(); NearExpiry(realm, pile);
            string economy = Economy(player), loot = Json(realm.Loot); int kills = OpeningJourney.Kills(player);
            var beforeDiscoveries = player.Discoveries.ToHashSet(StringComparer.Ordinal);
            var command = Act(realm, player, "guide_ack", arg: "loot");
            Check(Economy(player) == economy && Json(realm.Loot) == loot && OpeningJourney.Kills(player) == kills
                && OpeningJourney.RewardId(player) == "" && !player.Discoveries.Contains(NewPlayerJourney.MilestoneKey("loot"))
                && player.Discoveries.Except(beforeDiscoveries).SequenceEqual(new[] { NewPlayerJourney.HintKey("loot") }),
                "Dismissal granted gameplay credit, rewards or changed the existing loot.");
            Check(Next(realm, player).Stage == "combat", "Dismissal did not restore the ordinary opening objective.");
            var replay = realm.Execute(player.Id, command); Check(replay.Ok && Economy(player) == economy && Json(realm.Loot) == loot,
                "Replaying hint dismissal changed gameplay rewards.");
            var loaded = new RealmEngine(data, Wire.Copy(realm.State)) { Loot = Wire.Copy(realm.Loot) };
            Check(NewPlayerJourney.Seen(loaded.Player(player.Id), "loot") && Next(loaded, loaded.Player(player.Id)).Stage == "combat"
                && Economy(loaded.Player(player.Id)) == economy && Json(loaded.Loot) == loot,
                "Reload lost presentation dismissal or changed rewards/opening progress.");
        });

        test("A real first pickup grants its existing contents once and restores the opening", () =>
        {
            var (realm, player, pile) = FirstKill(); NearExpiry(realm, pile); player.Position = pile.Position;
            long gold = player.Gold, payout = pile.Gold; int kills = OpeningJourney.Kills(player); string quests = Json(player.Quests);
            var contents = pile.Items.GroupBy(x => x.Template).ToDictionary(x => x.Key, x => x.Sum(i => i.Quantity));
            var beforeCounts = contents.Keys.ToDictionary(x => x, x => Items.Count(player, x));
            var command = Act(realm, player, "loot", pile.Id);
            Check(!realm.Loot.ContainsKey(pile.Id) && player.Gold == gold + payout
                && contents.All(x => Items.Count(player, x.Key) == beforeCounts[x.Key] + x.Value)
                && player.Discoveries.Contains(NewPlayerJourney.MilestoneKey("loot")), "Real pickup changed or omitted the existing reward contents.");
            Check(Next(realm, player).Stage == "combat" && OpeningJourney.Kills(player) == kills && Json(player.Quests) == quests,
                "First pickup skipped the remaining opening fight or changed quest progress.");
            string economy = Economy(player); Check(realm.Execute(player.Id, command).Ok && Economy(player) == economy,
                "Replayed pickup duplicated rewards.");
        });

        test("Urgency respects ownership, local visibility, finite lifetimes, recovery and its exact time window", () =>
        {
            var (realm, player, pile) = FirstKill(); NearExpiry(realm, pile); var snapshot = realm.Snapshot(player.Id);
            JourneyObjective For(LootPile candidate) => NewPlayerJourney.Recommend(data, snapshot, new[] { candidate });
            var boundary = Wire.Copy(pile); boundary.Expires = snapshot.Time + 45;
            Check(For(boundary).Stage == "loot", "The last 45 seconds did not show urgent first-loot guidance.");
            boundary.Expires = snapshot.Time + 45.001; Check(For(boundary).Stage == "combat", "Nonurgent loot displaced the opening.");
            foreach (double expiry in new[] { snapshot.Time, snapshot.Time - 1, double.NaN, double.PositiveInfinity, double.NegativeInfinity })
            {
                var candidate = Wire.Copy(pile); candidate.Expires = expiry;
                Check(For(candidate).Stage == "combat", "Expired or nonfinite loot received urgency.");
            }
            var foreign = Wire.Copy(pile); foreign.Owner = "someone-else"; foreign.PublicAt = 0; foreign.Party = player.Party;
            Check(For(foreign).Stage == "combat", "Other players' public/party loot received first-owner urgency.");
            foreign.Owner = ""; Check(For(foreign).Stage == "combat", "Ownerless loot received first-owner urgency.");
            var far = Wire.Copy(pile); far.Position = player.Position.Add(new Point(30, 0));
            Check(For(far).Stage == "loot", "Visible loot at the local range boundary lost its reminder.");
            far.Position = player.Position.Add(new Point(30.001, 0));
            Check(For(far).Stage == "combat", "Invisible distant loot displaced the local opening.");
            far.Position = new(double.NaN, player.Position.Y); Check(For(far).Stage == "combat", "Nonfinite loot position received urgency.");
            var remote = Wire.Copy(pile); remote.Zone = "kingsmeadow"; Check(For(remote).Stage == "combat", "Another region's loot received urgency.");
            var empty = Wire.Copy(pile); empty.Gold = 0; empty.Items.Clear();
            Check(For(empty).Stage == "combat", "An empty pile displaced the opening with a pickup reminder.");
            empty.Gold = 1; Check(For(empty).Stage == "loot" && For(empty).Reward == "1 gold", "Legitimate gold-only loot lost its reminder or claimed nonexistent items.");
            var itemsOnly = Wire.Copy(pile); itemsOnly.Gold = 0;
            Check(itemsOnly.Items.Count > 0 && For(itemsOnly).Stage == "loot", "Legitimate item-only loot lost its reminder.");
            foreach (long gold in new[] { -1L, Items.GoldCap + 1 })
            {
                var candidate = Wire.Copy(pile); candidate.Gold = gold;
                Check(For(candidate).Stage == "combat", "Invalid loot gold received a pickup reminder.");
            }
            var invalid = Wire.Copy(pile); invalid.Id = "";
            Check(For(invalid).Stage == "combat", "Loot without an actionable pile identity received urgency.");
            invalid = Wire.Copy(pile); invalid.Items = null!;
            Check(For(invalid).Stage == "combat", "Missing loot contents received urgency or crashed the objective.");
            invalid = Wire.Copy(pile); invalid.Items[0].Id = "";
            Check(For(invalid).Stage == "combat", "An item without identity received a pickup reminder.");
            invalid = Wire.Copy(pile); invalid.Items[0].Template = "unknown-loot-template";
            Check(For(invalid).Stage == "combat", "Unknown loot metadata received urgency or crashed the objective.");
            foreach (int quantity in new[] { 0, data.Item(pile.Items[0].Template).StackMax + 1 })
            {
                invalid = Wire.Copy(pile); invalid.Items[0].Quantity = quantity;
                Check(For(invalid).Stage == "combat", "An invalid persisted item stack received urgency.");
            }
            Check(NewPlayerJourney.Recommend(data, snapshot, Array.Empty<LootPile>()).Stage == "combat", "Lost visibility did not restore the opening.");
            snapshot.Self.Health = 0; Check(For(pile).Stage == "recovery", "Urgent loot displaced death recovery.");
        });

        test("Urgent spoils wait through real combat and do not replace the guaranteed opening reward", () =>
        {
            var (realm, player, pile) = FirstKill(); NearExpiry(realm, pile);
            var rat = NextRat(realm, player); player.Position = rat.Position; Act(realm, player, "attack", rat.Id);
            Check(rat.Health > 0 && Next(realm, player).Stage == "combat", "Urgency interrupted an active real fight.");
            var snapshot = realm.Snapshot(player.Id); snapshot.Self.LastCombat = snapshot.Time - 9;
            Check(NewPlayerJourney.Recommend(data, snapshot, realm.VisibleLoot(player.Id)).Stage == "combat",
                "An active target/threat was ignored when the last-hit timestamp was older.");
            Advance(realm, 20); Kill(realm, player, rat); realm.State.Time += 9;
            Check(OpeningJourney.Kills(player) == OpeningJourney.KillGoal && Next(realm, player).TargetId == pile.Id,
                "The warning did not return safely after combat completed.");
            var giver = OpeningJourney.Giver(data); player.Position = giver.Position;
            Act(realm, player, "claim_quest", item: OpeningJourney.FightQuest);
            string reward = OpeningJourney.RewardId(player);
            Check(reward != "" && player.Inventory.Any(x => x.Id == reward) && Next(realm, player).Stage == "loot",
                "Urgency replaced the guaranteed opening reward or failed during the equip lesson.");
            Act(realm, player, "equip", item: reward); var recipe = data.Recipe(OpeningJourney.Recipe);
            player.Position = data.Npcs.First(x => x.Zone == OpeningJourney.Home && x.Station == recipe.Station).Position;
            Act(realm, player, "craft", item: recipe.Id); player.Position = giver.Position;
            Act(realm, player, "claim_quest", item: OpeningJourney.CraftQuest);
            Check(OpeningJourney.Finished(player) && Next(realm, player).Stage == "loot",
                "Urgent existing spoils were suppressed by the next quest offer after real opening completion.");
            Act(realm, player, "guide_ack", arg: "loot");
            Check(Next(realm, player).Stage == "quest_offer" && player.Inventory.Any(x => x.Id == reward)
                && Items.Count(player, "healing_potion") >= 7, "Dismissal did not restore the workshop handoff with the earned weapon/potions intact.");
        });
    }
}
