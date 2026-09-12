using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

internal static class ConcurrencyStressChecks
{
    private sealed record Attempt(string PlayerId, CommandResult Result);
    private sealed record TradeFixture(string A, string B, string ItemId, string TradeId, int Revision);

    public static void Run(Catalog data, List<string> failures)
    {
        int passed = 0;
        void Test(string name, Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS CONCURRENCY · " + name); }
            catch (Exception error)
            {
                failures.Add("Concurrency stress · " + name + ": " + error.Message);
                Console.WriteLine("FAIL CONCURRENCY · " + name + ": " + error.Message);
            }
        }
        void Need(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        double Percentile(List<double> values, double q)
        {
            var sorted = values.Order().ToArray();
            return sorted.Length == 0 ? 0 : sorted[Math.Min(sorted.Length - 1, Math.Max(0, (int)Math.Ceiling(sorted.Length * q) - 1))];
        }

        var realm = new RealmEngine(data);
        var classes = data.Classes.Select(x => x.Id).ToArray();
        var ids = Enumerable.Range(0, 50).Select(i =>
        {
            var player = realm.CreateCharacter("concurrency-account-" + i, $"Stress {i:00}", classes[i % classes.Length], new());
            realm.Active.Add(player.Id);
            return player.Id;
        }).ToArray();
        var spawn = data.Zone("wayfarers_rest").Spawn;
        Character P(string id) => realm.Player(id);
        GameCommand Command(string playerId, string kind, string target = "", string item = "", int amount = 1, string arg = "")
        {
            var player = P(playerId);
            return new() { Kind = kind, Target = target, Item = item, Amount = amount, Arg = arg, Sequence = player.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
        }
        CommandResult Act(string playerId, string kind, string target = "", string item = "", int amount = 1, string arg = "")
            => realm.Execute(playerId, Command(playerId, kind, target, item, amount, arg));
        List<Attempt> Race(IEnumerable<(string PlayerId, GameCommand Command)> operations)
        {
            // RealmHost serializes every authoritative mutation behind one gate. Contending
            // worker tasks here model simultaneous arrivals while preserving that exact
            // serializable state-mutation contract. The live load probe separately exercises
            // the real RealmHost gate through WebSockets and PostgreSQL.
            object gate = new();
            var tasks = operations.Select(operation => Task.Run(() =>
            {
                lock (gate) return new Attempt(operation.PlayerId, realm.Execute(operation.PlayerId, operation.Command));
            })).ToArray();
            Task.WaitAll(tasks);
            return tasks.Select(task => task.Result).ToList();
        }
        void Place(IEnumerable<string> playerIds, string zone, Point position)
        {
            foreach (var id in playerIds) { var player = P(id); player.Zone = zone; player.Position = position; }
        }
        foreach (var id in ids) { P(id).Zone = "wayfarers_rest"; P(id).Position = spawn; }

        var partyIds = new string[10];
        Test("50 active characters form ten authoritative parties and survive concurrent leave/rejoin", () =>
        {
            for (int groupIndex = 0; groupIndex < 10; groupIndex++)
            {
                var memberIds = ids.Skip(groupIndex * 5).Take(5).ToArray();
                Need(Act(memberIds[0], "party_create").Ok, "Party creation failed.");
                partyIds[groupIndex] = P(memberIds[0]).Party;
                foreach (var memberId in memberIds.Skip(1)) Need(Act(memberIds[0], "party_invite", memberId).Ok, "Party invite failed.");
                foreach (var memberId in memberIds.Skip(1)) Need(Act(memberId, "party_join", partyIds[groupIndex]).Ok, "Party join failed.");
                Need(realm.State.Parties[partyIds[groupIndex]].Members.Count == 5, "Party did not reach five members.");
            }
            var leavers = Enumerable.Range(0, 10).Select(i => ids[i * 5 + 4]).ToArray();
            var leaves = Race(leavers.Select(id => (id, Command(id, "party_leave"))));
            Need(leaves.All(x => x.Result.Ok), "A concurrent party leave failed.");
            Need(partyIds.All(id => realm.State.Parties[id].Members.Count == 4), "Concurrent party leaves corrupted membership.");
            var invites = Race(Enumerable.Range(0, 10).Select(i =>
            {
                string leader = ids[i * 5]; return (leader, Command(leader, "party_invite", leavers[i]));
            }));
            Need(invites.All(x => x.Result.Ok), "A concurrent party reinvite failed.");
            var rejoins = Race(Enumerable.Range(0, 10).Select(i => (leavers[i], Command(leavers[i], "party_join", partyIds[i]))));
            Need(rejoins.All(x => x.Result.Ok) && partyIds.All(id => realm.State.Parties[id].Members.Count == 5), "Concurrent party rejoins were not atomic.");
        });

        Test("shared kills award active party support credit and rotate contested loot ownership", () =>
        {
            var partyPlayers = ids.Take(5).ToArray(); string outsiderId = ids[5];
            Place(partyPlayers.Append(outsiderId), "wayfarers_rest", spawn);
            var def = data.Mobs.First(x => !x.Boss && !x.Elite && x.Ai != "passive" && x.Gold > 0);
            var zone = data.Zone("wayfarers_rest");
            var position = WorldMap.FindFree(zone, new Point(spawn.X + 1, spawn.Y));
            var before = partyPlayers.ToDictionary(id => id, id => P(id).Bestiary.GetValueOrDefault(def.Id));
            int outsiderBefore = P(outsiderId).Bestiary.GetValueOrDefault(def.Id);
            var pileIds = new List<string>();
            for (int kill = 0; kill < 2; kill++)
            {
                foreach (var supporterId in partyPlayers.Skip(1)) P(supporterId).LastCombat = realm.State.Time;
                var mob = new Creature { Id = "concurrency/loot/" + kill, Template = def.Id, Zone = zone.Id, Position = position, Home = position, Health = 1 };
                realm.State.Creatures[mob.Id] = mob; P(partyPlayers[0]).Cooldowns["attack"] = 0;
                Need(Act(partyPlayers[0], "attack", mob.Id).Ok, "Shared kill attack failed.");
                var newest = realm.Loot.Values.Where(x => x.Party == partyIds[0] && !pileIds.Contains(x.Id)).OrderByDescending(x => x.Expires).FirstOrDefault();
                Need(newest is not null, "Party kill did not produce authoritative loot."); pileIds.Add(newest!.Id);
            }
            foreach (var id in partyPlayers) Need(P(id).Bestiary.GetValueOrDefault(def.Id) >= before[id] + 2, "Active party supporter missed shared kill credit.");
            Need(P(outsiderId).Bestiary.GetValueOrDefault(def.Id) == outsiderBefore, "Nearby non-party player received shared kill credit.");
            string firstOwner = realm.Loot[pileIds[0]].Owner, secondOwner = realm.Loot[pileIds[1]].Owner;
            Need(firstOwner != secondOwner, "Round-robin loot owner did not rotate.");

            Place(partyPlayers, realm.Loot[pileIds[0]].Zone, realm.Loot[pileIds[0]].Position);
            var reserved = Race(partyPlayers.Select(id => (id, Command(id, "loot", pileIds[0]))));
            var reservedSuccess = reserved.Where(x => x.Result.Ok).ToArray();
            Need(reservedSuccess.Length == 1 && reservedSuccess[0].PlayerId == firstOwner, "Reserved loot contention did not resolve to exactly the round-robin owner.");

            var second = realm.Loot[pileIds[1]];
            Place(partyPlayers, second.Zone, second.Position); realm.State.Time = Math.Max(realm.State.Time, second.PartyAt + .01);
            var shared = Race(partyPlayers.Select(id => (id, Command(id, "loot", pileIds[1]))));
            Need(shared.Count(x => x.Result.Ok) == 1 && !realm.Loot.ContainsKey(pileIds[1]), "Post-reservation loot was duplicated or left collectible.");
        });

        Test("multiple players attack the same boss, share credit, and revive races resolve once per target", () =>
        {
            var partyPlayers = ids.Take(5).ToArray(); Place(partyPlayers, "wayfarers_rest", spawn);
            var bossDef = data.Mobs.First(x => x.Boss);
            var bossPosition = WorldMap.FindFree(data.Zone("wayfarers_rest"), new Point(spawn.X + 1, spawn.Y));
            string bossId = "concurrency/boss";
            realm.State.Creatures[bossId] = new Creature { Id = bossId, Template = bossDef.Id, Zone = "wayfarers_rest", Position = bossPosition, Home = bossPosition, Health = 1_000_000 };
            var before = partyPlayers.ToDictionary(id => id, id => P(id).Bestiary.GetValueOrDefault(bossDef.Id));
            foreach (var id in partyPlayers) P(id).Cooldowns["attack"] = 0;
            var pressure = Race(partyPlayers.Select(id => (id, Command(id, "attack", bossId))));
            Need(pressure.All(x => x.Result.Ok) && realm.State.Creatures.TryGetValue(bossId, out var pressured) && pressured.Health > 0, "Same-boss attack contention rejected a valid attacker or killed the pressure fixture too early.");
            pressured!.Health = 1; P(partyPlayers[0]).Cooldowns["attack"] = 0;
            Need(Act(partyPlayers[0], "attack", bossId).Ok, "Boss finishing blow was rejected.");
            foreach (var id in partyPlayers) Need(P(id).Bestiary.GetValueOrDefault(bossDef.Id) > before[id], "An active boss attacker missed cooperative kill credit.");

            var reviveOps = new List<(string PlayerId, GameCommand Command)>();
            for (int groupIndex = 0; groupIndex < 10; groupIndex++)
            {
                var memberIds = ids.Skip(groupIndex * 5).Take(5).ToArray(); string downedId = memberIds[4];
                Place(memberIds, "wayfarers_rest", spawn); P(downedId).Health = 0; P(downedId).DeadUntil = realm.State.Time + 5;
                foreach (var memberId in memberIds) { P(memberId).Cooldowns["revive"] = 0; P(memberId).Stamina = 100; }
                foreach (var reviverId in memberIds.Take(4)) reviveOps.Add((reviverId, Command(reviverId, "revive", downedId)));
            }
            var revives = Race(reviveOps);
            Need(revives.Count(x => x.Result.Ok) == 10, "Revive contention did not produce exactly one successful revive per party.");
            Need(Enumerable.Range(0, 10).All(i => P(ids[i * 5 + 4]).Health > 0), "A revive race left a target downed.");
        });

        Test("25-member guild cooperative project completes exactly once under concurrent support actions", () =>
        {
            var guildPlayers = ids.Take(25).ToArray();
            var guild = new SocialGroup { Name = "Concurrency Guild", Leader = guildPlayers[0], Members = guildPlayers.ToHashSet() };
            foreach (var id in guildPlayers) { guild.Roles[id] = id == guildPlayers[0] ? "leader" : "member"; P(id).Guild = guild.Id; }
            realm.State.Guilds[guild.Id] = guild; string guildId = guild.Id;
            Need(Act(guildPlayers[0], "guild_project", "fellowship").Ok, "Guild project did not start.");
            realm.State.Guilds[guildId].ProjectGoal = 5;
            var beforeGold = guildPlayers.ToDictionary(id => id, id => P(id).Gold);
            var operations = new List<(string PlayerId, GameCommand Command)>();
            for (int groupIndex = 0; groupIndex < 5; groupIndex++)
            {
                string reviverId = ids[groupIndex * 5], downedId = ids[groupIndex * 5 + 4];
                Place([reviverId, downedId], "wayfarers_rest", spawn); P(downedId).Health = 0; P(downedId).DeadUntil = realm.State.Time + 5;
                P(reviverId).Cooldowns["revive"] = 0; P(reviverId).Stamina = 100;
                operations.Add((reviverId, Command(reviverId, "revive", downedId)));
            }
            var results = Race(operations);
            Need(results.All(x => x.Result.Ok), "A cooperative guild contribution failed.");
            var completed = realm.State.Guilds[guildId];
            Need(completed.CompletedProjects == 1 && completed.Project == "", "Guild project was not completed exactly once.");
            Need(guildPlayers.All(id => P(id).Achievements.Contains("guild_project:fellowship") && P(id).Gold > beforeGold[id]), "Guild completion did not reward every member through authoritative state.");
        });

        Test("ten simultaneous trades transfer unique item identities exactly once", () =>
        {
            var uniqueDef = data.Items.First(x => x.StackMax == 1 && x.Type != "quest" && x.Value > 0);
            var pairs = new List<TradeFixture>();
            for (int i = 0; i < 10; i++)
            {
                string aId = ids[25 + i * 2], bId = ids[26 + i * 2]; Place([aId, bId], "wayfarers_rest", spawn);
                var offered = Items.Create(data, uniqueDef.Id); P(aId).Inventory.Add(offered);
                Need(Act(aId, "trade_invite", bId).Ok, "Trade invite failed.");
                var trade = realm.State.Trades.Values.Single(x => (x.A.Character == aId && x.B.Character == bId) || (x.A.Character == bId && x.B.Character == aId));
                Need(Act(aId, "trade_offer", trade.Id, offered.Id, 1).Ok, "Trade offer failed.");
                pairs.Add(new(aId, bId, offered.Id, trade.Id, realm.State.Trades[trade.Id].Revision));
            }
            var readyOps = pairs.SelectMany(pair => new[]
            {
                (pair.A, Command(pair.A, "trade_ready", pair.TradeId, amount: pair.Revision)),
                (pair.B, Command(pair.B, "trade_ready", pair.TradeId, amount: pair.Revision))
            });
            Need(Race(readyOps).All(x => x.Result.Ok), "Concurrent trade ready phase failed.");
            var confirmOps = pairs.SelectMany(pair => new[]
            {
                (pair.A, Command(pair.A, "trade_confirm", pair.TradeId, amount: pair.Revision)),
                (pair.B, Command(pair.B, "trade_confirm", pair.TradeId, amount: pair.Revision))
            });
            Need(Race(confirmOps).All(x => x.Result.Ok), "Concurrent trade confirmation failed.");
            Need(realm.State.Trades.Count == 0, "Completed trades remained active.");
            foreach (var pair in pairs) Need(!P(pair.A).Inventory.Any(x => x.Id == pair.ItemId) && P(pair.B).Inventory.Count(x => x.Id == pair.ItemId) == 1, "Trade duplicated or lost a unique item identity.");
        });

        Test("auction contention has one winner and preserves escrow identity", () =>
        {
            var auctioneer = data.Npcs.First(x => x.Role == "auctioneer"); string sellerId = ids[45];
            P(sellerId).Zone = auctioneer.Zone; P(sellerId).Position = auctioneer.Position; P(sellerId).Gold = 1_000_000;
            var buyers = ids.Take(10).ToArray(); Place(buyers, auctioneer.Zone, auctioneer.Position); foreach (var id in buyers) P(id).Gold = 1_000_000;
            var uniqueDef = data.Items.First(x => x.StackMax == 1 && x.Type != "quest" && x.Value > 0);
            var sale = Items.Create(data, uniqueDef.Id); P(sellerId).Inventory.Add(sale); string saleId = sale.Id;
            Need(Act(sellerId, "auction_list", target: "25", item: saleId).Ok, "Auction list failed.");
            string auctionId = realm.State.Auctions.Values.Single(x => x.Item.Id == saleId).Id;
            var results = Race(buyers.Select(id => (id, Command(id, "auction_buy", auctionId))));
            Need(results.Count(x => x.Result.Ok) == 1 && !realm.State.Auctions.ContainsKey(auctionId), "Auction race did not resolve to exactly one buyer.");
            int copies = realm.State.Characters.Values.Sum(p => p.Inventory.Count(x => x.Id == saleId)) + realm.State.Auctions.Values.Count(x => x.Item.Id == saleId);
            Need(copies == 1, "Auction contention duplicated or lost escrowed item identity.");
        });

        Test("25 concurrent merchant buyers cannot oversell finite stock", () =>
        {
            var merchant = data.Npcs.First(x => x.Stock.Contains("healing_potion")); var buyers = ids.Take(25).ToArray();
            Place(buyers, merchant.Zone, merchant.Position); foreach (var id in buyers) P(id).Gold = 1_000_000;
            string key = merchant.Id + "/healing_potion"; realm.State.ShopStock[key] = 12;
            int before = buyers.Sum(id => Items.Count(P(id), "healing_potion"));
            var results = Race(buyers.Select(id => (id, Command(id, "buy", merchant.Id, "healing_potion", 1))));
            Need(results.Count(x => x.Result.Ok) == 12, "Merchant contention did not honor the exact available stock.");
            int after = buyers.Sum(id => Items.Count(P(id), "healing_potion"));
            Need(realm.State.ShopStock[key] == 0 && after == before + 12, "Merchant stock and buyer inventory diverged.");
        });

        var handRecipe = data.Recipes.First(r => r.Station == "hand" && r.Ingredients.Count > 0 && !r.Ingredients.ContainsKey(r.Output) && data.Item(r.Output).StackMax > 1);
        Test("25 simultaneous crafting actions consume inputs and create outputs once", () =>
        {
            var crafters = ids.Take(25).ToArray(); var before = new Dictionary<string, int>();
            foreach (var id in crafters)
            {
                var crafter = P(id); crafter.SkillXp[handRecipe.Skill] = Math.Max(crafter.SkillXp.GetValueOrDefault(handRecipe.Skill), Progression.Threshold(handRecipe.Requirement));
                foreach (var ingredient in handRecipe.Ingredients) Items.Add(crafter.Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
                crafter.Cooldowns["craft"] = 0; before[id] = Items.Count(crafter, handRecipe.Output);
            }
            var results = Race(crafters.Select(id => (id, Command(id, "craft", item: handRecipe.Id))));
            Need(results.All(x => x.Result.Ok), "Concurrent crafting rejected a prepared crafter.");
            foreach (var id in crafters) Need(Items.Count(P(id), handRecipe.Output) == before[id] + handRecipe.Quantity, "Craft output count was not exactly once.");
        });

        Test("duplicate concurrent command replay is idempotent", () =>
        {
            string playerId = ids[49]; var player = P(playerId);
            player.SkillXp[handRecipe.Skill] = Math.Max(player.SkillXp.GetValueOrDefault(handRecipe.Skill), Progression.Threshold(handRecipe.Requirement));
            foreach (var ingredient in handRecipe.Ingredients) Items.Add(player.Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
            player.Cooldowns["craft"] = 0; int before = Items.Count(player, handRecipe.Output);
            var command = Command(playerId, "craft", item: handRecipe.Id);
            var results = Race(new[] { (playerId, command), (playerId, command) });
            Need(results.All(x => x.Result.Ok), "Duplicate replay did not return the persisted success receipt.");
            Need(Items.Count(P(playerId), handRecipe.Output) == before + handRecipe.Quantity, "Duplicate replay crafted twice.");
        });

        Test("25 simultaneous regional transitions are independent and authoritative", () =>
        {
            var source = data.Zone("wayfarers_rest"); var exit = source.Exits.OrderBy(x => x.Requirement).First(); var travelers = ids.Take(25).ToArray();
            foreach (var id in travelers)
            {
                var traveler = P(id); traveler.Zone = source.Id; traveler.Position = exit.Position;
                while (Progression.PlayerLevel(traveler) < JourneyProgression.ExitRequirement(data, exit)) traveler.SkillXp["exploration"] += 1000;
            }
            var results = Race(travelers.Select(id => (id, Command(id, "transition", exit.Id))));
            Need(results.All(x => x.Result.Ok) && travelers.All(id => P(id).Zone == exit.Target), "Concurrent regional transition lost or cross-wired a player.");
        });

        Test("50-player snapshot and tick metrics remain within protocol and server-tick contracts", () =>
        {
            Place(ids, "wayfarers_rest", spawn);
            foreach (var id in ids) { P(id).Health = Math.Max(1, P(id).Health); realm.Active.Add(id); }
            var tickMs = new List<double>();
            for (int i = 0; i < 200; i++)
            {
                var watch = Stopwatch.StartNew(); realm.Tick(.05); watch.Stop(); tickMs.Add(watch.Elapsed.TotalMilliseconds);
            }
            var snapshotMs = new List<double>(); var snapshotBytes = new List<int>();
            foreach (var id in ids)
            {
                var watch = Stopwatch.StartNew(); var packet = SnapshotPackets.Create(realm, id); var bytes = JsonSerializer.SerializeToUtf8Bytes(packet, Wire.Json).Length; watch.Stop();
                snapshotMs.Add(watch.Elapsed.TotalMilliseconds); snapshotBytes.Add(bytes);
            }
            Need(snapshotBytes.All(x => x > 0 && x < 2_000_000), "A 50-player snapshot exceeded the live peer packet contract.");
            Need(Percentile(tickMs, .95) < 50, $"Authoritative tick p95 {Percentile(tickMs, .95):F2} ms exceeds the 50 ms server cadence.");
            Console.WriteLine($"CONCURRENCY METRICS: players=50 ticks=200 tick-p50={Percentile(tickMs, .50):F3}ms tick-p95={Percentile(tickMs, .95):F3}ms tick-max={tickMs.Max():F3}ms snapshot-p50={Percentile(snapshotMs, .50):F3}ms snapshot-p95={Percentile(snapshotMs, .95):F3}ms snapshot-max={snapshotMs.Max():F3}ms snapshot-bytes-avg={snapshotBytes.Average():F0} snapshot-bytes-max={snapshotBytes.Max()}");
        });

        Console.WriteLine($"CONCURRENCY STRESS: {passed} groups passed with 50 authoritative characters.");
    }
}
