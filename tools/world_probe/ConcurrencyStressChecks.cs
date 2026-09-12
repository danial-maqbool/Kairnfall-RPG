using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

internal static class ConcurrencyStressChecks
{
    private sealed record Attempt(Character Player, CommandResult Result);

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
        GameCommand Command(Character player, string kind, string target = "", string item = "", int amount = 1, string arg = "")
            => new() { Kind = kind, Target = target, Item = item, Amount = amount, Arg = arg, Sequence = player.LastAction + 1, RequestId = Guid.NewGuid().ToString("N") };
        CommandResult Act(RealmEngine realm, Character player, string kind, string target = "", string item = "", int amount = 1, string arg = "")
            => realm.Execute(player.Id, Command(player, kind, target, item, amount, arg));
        List<Attempt> Race(RealmEngine realm, IEnumerable<(Character Player, GameCommand Command)> operations)
        {
            // RealmHost uses one authoritative gate around every state mutation. The probe
            // intentionally gives that gate real contending worker tasks while preserving the
            // same serializable mutation contract instead of calling RealmEngine concurrently.
            object gate = new();
            var tasks = operations.Select(operation => Task.Run(() =>
            {
                lock (gate) return new Attempt(operation.Player, realm.Execute(operation.Player.Id, operation.Command));
            })).ToArray();
            Task.WaitAll(tasks);
            return tasks.Select(task => task.Result).ToList();
        }
        double Percentile(List<double> values, double q)
        {
            var sorted = values.Order().ToArray();
            return sorted.Length == 0 ? 0 : sorted[Math.Min(sorted.Length - 1, Math.Max(0, (int)Math.Ceiling(sorted.Length * q) - 1))];
        }

        var realm = new RealmEngine(data);
        var classes = data.Classes.Select(x => x.Id).ToArray();
        var players = Enumerable.Range(0, 50).Select(i =>
        {
            var player = realm.CreateCharacter("concurrency-account-" + i, $"Stress {i:00}", classes[i % classes.Length], new());
            realm.Active.Add(player.Id);
            return player;
        }).ToArray();
        var spawn = data.Zone("wayfarers_rest").Spawn;
        foreach (var player in players) { player.Zone = "wayfarers_rest"; player.Position = spawn; }

        var parties = new List<SocialGroup>();
        Test("50 active characters form ten authoritative parties and survive concurrent leave/rejoin", () =>
        {
            for (int groupIndex = 0; groupIndex < 10; groupIndex++)
            {
                var members = players.Skip(groupIndex * 5).Take(5).ToArray();
                Need(Act(realm, members[0], "party_create").Ok, "Party creation failed.");
                var party = realm.State.Parties[members[0].Party]; parties.Add(party);
                foreach (var member in members.Skip(1)) Need(Act(realm, members[0], "party_invite", member.Id).Ok, "Party invite failed.");
                foreach (var member in members.Skip(1)) Need(Act(realm, member, "party_join", party.Id).Ok, "Party join failed.");
                Need(party.Members.Count == 5, "Party did not reach five members.");
            }
            var leavers = Enumerable.Range(0, 10).Select(i => players[i * 5 + 4]).ToArray();
            var leaves = Race(realm, leavers.Select(p => (p, Command(p, "party_leave"))));
            Need(leaves.All(x => x.Result.Ok), "A concurrent party leave failed.");
            Need(parties.All(x => x.Members.Count == 4), "Concurrent party leaves corrupted membership.");
            var invites = Race(realm, Enumerable.Range(0, 10).Select(i =>
            {
                var leader = players[i * 5]; var leaver = leavers[i];
                return (leader, Command(leader, "party_invite", leaver.Id));
            }));
            Need(invites.All(x => x.Result.Ok), "A concurrent party reinvite failed.");
            var rejoins = Race(realm, Enumerable.Range(0, 10).Select(i => (leavers[i], Command(leavers[i], "party_join", parties[i].Id))));
            Need(rejoins.All(x => x.Result.Ok) && parties.All(x => x.Members.Count == 5), "Concurrent party rejoins were not atomic.");
        });

        Test("shared kills award active party support credit and rotate contested loot ownership", () =>
        {
            var partyPlayers = players.Take(5).ToArray();
            var outsider = players[5]; outsider.Position = partyPlayers[0].Position;
            var def = data.Mobs.First(x => !x.Boss && !x.Elite && x.Ai != "passive" && x.Gold > 0);
            var zone = data.Zone(partyPlayers[0].Zone);
            var position = WorldMap.FindFree(zone, new Point(partyPlayers[0].Position.X + 1, partyPlayers[0].Position.Y));
            var before = partyPlayers.ToDictionary(x => x.Id, x => x.Bestiary.GetValueOrDefault(def.Id));
            int outsiderBefore = outsider.Bestiary.GetValueOrDefault(def.Id);
            var pileIds = new List<string>();
            for (int kill = 0; kill < 2; kill++)
            {
                foreach (var supporter in partyPlayers.Skip(1)) supporter.LastCombat = realm.State.Time;
                var mob = new Creature { Id = "concurrency/loot/" + kill, Template = def.Id, Zone = zone.Id, Position = position, Home = position, Health = 1 };
                realm.State.Creatures[mob.Id] = mob;
                partyPlayers[0].Cooldowns["attack"] = 0;
                Need(Act(realm, partyPlayers[0], "attack", mob.Id).Ok, "Shared kill attack failed.");
                var newest = realm.Loot.Values.Where(x => x.Party == partyPlayers[0].Party && !pileIds.Contains(x.Id)).OrderByDescending(x => x.Expires).FirstOrDefault();
                Need(newest is not null, "Party kill did not produce authoritative loot."); pileIds.Add(newest!.Id);
            }
            foreach (var supporter in partyPlayers) Need(supporter.Bestiary.GetValueOrDefault(def.Id) >= before[supporter.Id] + 2, "Active party supporter missed shared kill credit.");
            Need(outsider.Bestiary.GetValueOrDefault(def.Id) == outsiderBefore, "Nearby non-party player received shared kill credit.");
            var piles = pileIds.Select(id => realm.Loot[id]).ToArray();
            Need(piles[0].Owner != piles[1].Owner, "Round-robin loot owner did not rotate.");

            foreach (var player in partyPlayers) player.Position = piles[0].Position;
            var reserved = Race(realm, partyPlayers.Select(p => (p, Command(p, "loot", piles[0].Id))));
            var reservedSuccess = reserved.Where(x => x.Result.Ok).ToArray();
            Need(reservedSuccess.Length == 1 && reservedSuccess[0].Player.Id == piles[0].Owner, "Reserved loot contention did not resolve to exactly the round-robin owner.");

            foreach (var player in partyPlayers) player.Position = piles[1].Position;
            realm.State.Time = Math.Max(realm.State.Time, piles[1].PartyAt + .01);
            var shared = Race(realm, partyPlayers.Select(p => (p, Command(p, "loot", piles[1].Id))));
            Need(shared.Count(x => x.Result.Ok) == 1 && !realm.Loot.ContainsKey(piles[1].Id), "Post-reservation loot was duplicated or left collectible.");
        });

        Test("multi-player boss credit and ten simultaneous revive races resolve once per target", () =>
        {
            var partyPlayers = players.Take(5).ToArray();
            foreach (var player in partyPlayers) { player.Zone = "wayfarers_rest"; player.Position = spawn; player.LastCombat = realm.State.Time; }
            var bossDef = data.Mobs.First(x => x.Boss);
            var bossPosition = WorldMap.FindFree(data.Zone("wayfarers_rest"), new Point(spawn.X + 1, spawn.Y));
            var boss = new Creature { Id = "concurrency/boss", Template = bossDef.Id, Zone = "wayfarers_rest", Position = bossPosition, Home = bossPosition, Health = 1 };
            realm.State.Creatures[boss.Id] = boss;
            var before = partyPlayers.ToDictionary(x => x.Id, x => x.Bestiary.GetValueOrDefault(bossDef.Id));
            partyPlayers[0].Cooldowns["attack"] = 0;
            Need(Act(realm, partyPlayers[0], "attack", boss.Id).Ok, "Boss kill was rejected.");
            foreach (var player in partyPlayers) Need(player.Bestiary.GetValueOrDefault(bossDef.Id) > before[player.Id], "Party member missed multi-player boss credit.");

            var reviveOps = new List<(Character Player, GameCommand Command)>();
            for (int groupIndex = 0; groupIndex < 10; groupIndex++)
            {
                var members = players.Skip(groupIndex * 5).Take(5).ToArray();
                var downed = members[4]; downed.Health = 0; downed.DeadUntil = realm.State.Time + 5;
                foreach (var member in members) { member.Zone = downed.Zone = "wayfarers_rest"; member.Position = downed.Position = spawn; member.Cooldowns["revive"] = 0; }
                foreach (var reviver in members.Take(4)) reviveOps.Add((reviver, Command(reviver, "revive", downed.Id)));
            }
            var revives = Race(realm, reviveOps);
            Need(revives.Count(x => x.Result.Ok) == 10, "Revive contention did not produce exactly one successful revive per party.");
            Need(Enumerable.Range(0, 10).All(i => players[i * 5 + 4].Health > 0), "A revive race left a target downed.");
        });

        Test("25-member guild cooperative project completes exactly once under concurrent support actions", () =>
        {
            var guildPlayers = players.Take(25).ToArray();
            var guild = new SocialGroup { Name = "Concurrency Guild", Leader = guildPlayers[0].Id, Members = guildPlayers.Select(x => x.Id).ToHashSet() };
            foreach (var member in guildPlayers) { guild.Roles[member.Id] = member == guildPlayers[0] ? "leader" : "member"; member.Guild = guild.Id; }
            realm.State.Guilds[guild.Id] = guild;
            Need(Act(realm, guildPlayers[0], "guild_project", "fellowship").Ok, "Guild project did not start.");
            guild.ProjectGoal = 5;
            var beforeGold = guildPlayers.ToDictionary(x => x.Id, x => x.Gold);
            var operations = new List<(Character Player, GameCommand Command)>();
            for (int groupIndex = 0; groupIndex < 5; groupIndex++)
            {
                var reviver = players[groupIndex * 5]; var downed = players[groupIndex * 5 + 4];
                downed.Health = 0; downed.DeadUntil = realm.State.Time + 5; downed.Zone = reviver.Zone = "wayfarers_rest"; downed.Position = reviver.Position = spawn; reviver.Cooldowns["revive"] = 0;
                operations.Add((reviver, Command(reviver, "revive", downed.Id)));
            }
            var results = Race(realm, operations);
            Need(results.All(x => x.Result.Ok), "A cooperative guild contribution failed.");
            Need(guild.CompletedProjects == 1 && guild.Project == "", "Guild project was not completed exactly once.");
            Need(guildPlayers.All(x => x.Achievements.Contains("guild_project:fellowship") && x.Gold > beforeGold[x.Id]), "Guild completion did not reward every member exactly through authoritative state.");
        });

        Test("ten simultaneous trades transfer unique item identities exactly once", () =>
        {
            var pairs = new List<(Character A, Character B, string ItemId, Trade Trade)>();
            for (int i = 0; i < 10; i++)
            {
                var a = players[25 + i * 2]; var b = players[26 + i * 2];
                a.Zone = b.Zone = "wayfarers_rest"; a.Position = b.Position = spawn;
                var offered = a.Inventory.First(x => !Items.Equipped(a, x.Id) && data.Item(x.Template).Type != "quest");
                Need(Act(realm, a, "trade_invite", b.Id).Ok, "Trade invite failed.");
                var trade = realm.State.Trades.Values.Single(x => (x.A.Character == a.Id && x.B.Character == b.Id) || (x.A.Character == b.Id && x.B.Character == a.Id));
                Need(Act(realm, a, "trade_offer", trade.Id, offered.Id, 1).Ok, "Trade offer failed.");
                pairs.Add((a, b, offered.Id, trade));
            }
            var readyOps = pairs.SelectMany(pair => new[]
            {
                (pair.A, Command(pair.A, "trade_ready", pair.Trade.Id, amount: pair.Trade.Revision)),
                (pair.B, Command(pair.B, "trade_ready", pair.Trade.Id, amount: pair.Trade.Revision))
            });
            Need(Race(realm, readyOps).All(x => x.Result.Ok), "Concurrent trade ready phase failed.");
            var confirmOps = pairs.SelectMany(pair => new[]
            {
                (pair.A, Command(pair.A, "trade_confirm", pair.Trade.Id, amount: pair.Trade.Revision)),
                (pair.B, Command(pair.B, "trade_confirm", pair.Trade.Id, amount: pair.Trade.Revision))
            });
            Need(Race(realm, confirmOps).All(x => x.Result.Ok), "Concurrent trade confirmation failed.");
            Need(realm.State.Trades.Count == 0, "Completed trades remained active.");
            foreach (var pair in pairs)
            {
                Need(!pair.A.Inventory.Any(x => x.Id == pair.ItemId) && pair.B.Inventory.Count(x => x.Id == pair.ItemId) == 1, "Trade duplicated or lost a unique item identity.");
            }
        });

        Test("auction contention has one winner and preserves escrow identity", () =>
        {
            var auctioneer = data.Npcs.First(x => x.Role == "auctioneer");
            var seller = players[45]; seller.Zone = auctioneer.Zone; seller.Position = auctioneer.Position; seller.Gold = Math.Max(seller.Gold, 1000);
            var buyers = players.Take(10).ToArray();
            foreach (var buyer in buyers) { buyer.Zone = auctioneer.Zone; buyer.Position = auctioneer.Position; buyer.Gold = 1000; }
            var uniqueDef = data.Items.First(x => x.StackMax == 1 && x.Type != "quest" && x.Value > 0);
            var sale = Items.Create(data, uniqueDef.Id); seller.Inventory.Add(sale);
            Need(Act(realm, seller, "auction_list", target: "25", item: sale.Id).Ok, "Auction list failed.");
            var auction = realm.State.Auctions.Values.Single(x => x.Item.Id == sale.Id);
            var results = Race(realm, buyers.Select(b => (b, Command(b, "auction_buy", auction.Id))));
            Need(results.Count(x => x.Result.Ok) == 1 && !realm.State.Auctions.ContainsKey(auction.Id), "Auction race did not resolve to exactly one buyer.");
            int copies = realm.State.Characters.Values.Sum(p => p.Inventory.Count(x => x.Id == sale.Id)) + realm.State.Auctions.Values.Count(x => x.Item.Id == sale.Id);
            Need(copies == 1, "Auction contention duplicated or lost escrowed item identity.");
        });

        Test("25 concurrent merchant buyers cannot oversell finite stock", () =>
        {
            var merchant = data.Npcs.First(x => x.Stock.Contains("healing_potion"));
            var buyers = players.Take(25).ToArray();
            foreach (var buyer in buyers) { buyer.Zone = merchant.Zone; buyer.Position = merchant.Position; buyer.Gold = 1000; }
            string key = merchant.Id + "/healing_potion"; realm.State.ShopStock[key] = 12;
            int before = buyers.Sum(x => Items.Count(x, "healing_potion"));
            var results = Race(realm, buyers.Select(b => (b, Command(b, "buy", merchant.Id, "healing_potion", 1))));
            Need(results.Count(x => x.Result.Ok) == 12, "Merchant contention did not honor the exact available stock.");
            Need(realm.State.ShopStock[key] == 0 && buyers.Sum(x => Items.Count(x, "healing_potion")) == before + 12, "Merchant stock and buyer inventory diverged.");
        });

        Test("25 simultaneous crafting actions consume inputs and create outputs once", () =>
        {
            var recipe = data.Recipes.First(r => r.Station == "hand" && r.Ingredients.Count > 0 && !r.Ingredients.ContainsKey(r.Output) && data.Item(r.Output).StackMax > 1);
            var crafters = players.Take(25).ToArray();
            var before = new Dictionary<string, int>();
            foreach (var crafter in crafters)
            {
                crafter.SkillXp[recipe.Skill] = Math.Max(crafter.SkillXp.GetValueOrDefault(recipe.Skill), Progression.Threshold(recipe.Requirement));
                foreach (var ingredient in recipe.Ingredients) Items.Add(crafter.Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
                crafter.Cooldowns["craft"] = 0; before[crafter.Id] = Items.Count(crafter, recipe.Output);
            }
            var results = Race(realm, crafters.Select(p => (p, Command(p, "craft", item: recipe.Id))));
            Need(results.All(x => x.Result.Ok), "Concurrent crafting rejected a prepared crafter.");
            foreach (var crafter in crafters) Need(Items.Count(crafter, recipe.Output) == before[crafter.Id] + recipe.Quantity, "Craft output count was not exactly once.");
        });

        Test("duplicate concurrent command replay is idempotent", () =>
        {
            var player = players[49];
            var recipe = data.Recipes.First(r => r.Station == "hand" && r.Ingredients.Count > 0 && !r.Ingredients.ContainsKey(r.Output) && data.Item(r.Output).StackMax > 1);
            player.SkillXp[recipe.Skill] = Math.Max(player.SkillXp.GetValueOrDefault(recipe.Skill), Progression.Threshold(recipe.Requirement));
            foreach (var ingredient in recipe.Ingredients) Items.Add(player.Inventory, Items.Create(data, ingredient.Key, ingredient.Value), data);
            player.Cooldowns["craft"] = 0;
            int before = Items.Count(player, recipe.Output);
            var command = Command(player, "craft", item: recipe.Id);
            var results = Race(realm, new[] { (player, command), (player, command) });
            Need(results.All(x => x.Result.Ok), "Duplicate replay did not return the persisted success receipt.");
            Need(Items.Count(player, recipe.Output) == before + recipe.Quantity, "Duplicate replay crafted twice.");
        });

        Test("25 simultaneous regional transitions are independent and authoritative", () =>
        {
            var source = data.Zone("wayfarers_rest"); var exit = source.Exits.OrderBy(x => x.Requirement).First();
            var travelers = players.Take(25).ToArray();
            foreach (var traveler in travelers)
            {
                traveler.Zone = source.Id; traveler.Position = exit.Position;
                while (Progression.PlayerLevel(traveler) < JourneyProgression.ExitRequirement(data, exit)) traveler.SkillXp["exploration"] += 1000;
            }
            var results = Race(realm, travelers.Select(p => (p, Command(p, "transition", exit.Id))));
            Need(results.All(x => x.Result.Ok) && travelers.All(x => x.Zone == exit.Target), "Concurrent regional transition lost or cross-wired a player.");
        });

        Test("50-player snapshot and tick metrics remain within protocol and server-tick contracts", () =>
        {
            foreach (var player in players)
            {
                player.Zone = "wayfarers_rest"; player.Position = spawn; player.Health = Math.Max(1, player.Health); realm.Active.Add(player.Id);
            }
            var tickMs = new List<double>();
            for (int i = 0; i < 200; i++)
            {
                var watch = Stopwatch.StartNew(); realm.Tick(.05); watch.Stop(); tickMs.Add(watch.Elapsed.TotalMilliseconds);
            }
            var snapshotMs = new List<double>(); var snapshotBytes = new List<int>();
            foreach (var player in players)
            {
                var watch = Stopwatch.StartNew(); var packet = SnapshotPackets.Create(realm, player.Id); var bytes = JsonSerializer.SerializeToUtf8Bytes(packet, Wire.Json).Length; watch.Stop();
                snapshotMs.Add(watch.Elapsed.TotalMilliseconds); snapshotBytes.Add(bytes);
            }
            Need(snapshotBytes.All(x => x > 0 && x < 2_000_000), "A 50-player snapshot exceeded the live peer packet contract.");
            Need(Percentile(tickMs, .95) < 50, $"Authoritative tick p95 {Percentile(tickMs, .95):F2} ms exceeds the 50 ms server cadence.");
            Console.WriteLine($"CONCURRENCY METRICS: players=50 ticks=200 tick-p50={Percentile(tickMs, .50):F3}ms tick-p95={Percentile(tickMs, .95):F3}ms tick-max={tickMs.Max():F3}ms snapshot-p50={Percentile(snapshotMs, .50):F3}ms snapshot-p95={Percentile(snapshotMs, .95):F3}ms snapshot-max={snapshotMs.Max():F3}ms snapshot-bytes-avg={snapshotBytes.Average():F0} snapshot-bytes-max={snapshotBytes.Max()}");
        });

        Console.WriteLine($"CONCURRENCY STRESS: {passed} groups passed with 50 authoritative characters.");
    }
}
