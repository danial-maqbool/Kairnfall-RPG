using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

var catalog = Catalog.Load(args.Length > 0 ? args[0] : "content/catalog.json");
var results = new List<object>();
int failures = 0;

void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

void Test(string name, Action body)
{
    var watch = Stopwatch.StartNew();
    try
    {
        body();
        results.Add(new { name, status = "passed", milliseconds = watch.Elapsed.TotalMilliseconds });
        Console.WriteLine("PASS " + name);
    }
    catch (Exception error)
    {
        failures++;
        results.Add(new { name, status = "failed", error = error.ToString(), milliseconds = watch.Elapsed.TotalMilliseconds });
        Console.WriteLine("FAIL " + name + "\n" + error);
    }
}

(RealmEngine Engine, Character Alice, Character Bob, Character Observer) Fixture()
{
    var engine = new RealmEngine(catalog);
    var alice = engine.CreateCharacter("independent-a", "QA Alice", "vanguard", new());
    var bob = engine.CreateCharacter("independent-b", "QA Bob", "ranger", new());
    var observer = engine.CreateCharacter("independent-c", "QA Observer", "rogue", new());
    foreach (var player in new[] { alice, bob, observer })
    {
        engine.Active.Add(player.Id);
        player.Gold = 10_000;
    }
    return (engine, alice, bob, observer);
}

Character Live(RealmEngine engine, Character actor) => engine.Player(actor.Id);

CommandResult Act(RealmEngine engine, Character actor, string kind, string target = "", string item = "", int amount = 1, string arg = "", double x = 0, double y = 0)
{
    var current = Live(engine, actor);
    return engine.Execute(current.Id, new GameCommand
    {
        Kind = kind,
        Target = target,
        Item = item,
        Amount = amount,
        Arg = arg,
        Sequence = current.LastAction + 1,
        X = x,
        Y = y
    });
}

Item Give(Character player, string template, int quantity = 1)
{
    var item = Items.Create(catalog, template, quantity);
    Items.Add(player.Inventory, item, catalog);
    return Items.Owned(player, item.Id);
}

void AtService(string role, params Character[] players)
{
    var npc = catalog.Npcs.First(value => value.Role == role);
    foreach (var player in players)
    {
        player.Zone = npc.Zone;
        player.Position = npc.Position;
    }
}

Test("bank rejects forged ownership and preserves unique instance identity", () =>
{
    var f = Fixture();
    AtService("banker", f.Alice, f.Bob);
    var item = Give(f.Alice, "copper_sword");
    string itemId = item.Id;
    long bobGold = f.Bob.Gold;
    var forged = Act(f.Engine, f.Bob, "deposit", item: itemId, amount: 1);
    Check(!forged.Ok, "Another player's item was accepted for deposit.");
    var alice = Live(f.Engine, f.Alice);
    var bob = Live(f.Engine, f.Bob);
    Check(alice.Inventory.Any(value => value.Id == itemId), "Rejected forged deposit changed owner inventory.");
    Check(bob.Bank.All(value => value.Id != itemId) && bob.Gold == bobGold, "Rejected forged deposit changed bank or gold state.");

    var deposited = Act(f.Engine, alice, "deposit", item: itemId, amount: 1);
    Check(deposited.Ok, deposited.Message);
    alice = Live(f.Engine, alice);
    Check(alice.Bank.Count(value => value.Id == itemId) == 1 && alice.Inventory.All(value => value.Id != itemId), "Deposit did not preserve the unique item in bank escrow.");
    var withdrawn = Act(f.Engine, alice, "withdraw", item: itemId, amount: 1);
    Check(withdrawn.Ok, withdrawn.Message);
    alice = Live(f.Engine, alice);
    Check(alice.Inventory.Count(value => value.Id == itemId) == 1 && alice.Bank.All(value => value.Id != itemId), "Withdraw changed or duplicated the unique item identity.");
});

Test("invalid auction quantities fail atomically", () =>
{
    foreach (var amount in new[] { 0, -1, int.MaxValue })
    {
        var f = Fixture();
        AtService("auctioneer", f.Alice);
        var stack = f.Alice.Inventory.First(value => value.Template == "healing_potion");
        string stackId = stack.Id;
        int quantity = stack.Quantity;
        long gold = f.Alice.Gold;
        var result = Act(f.Engine, f.Alice, "auction_list", target: "100", item: stackId, amount: amount);
        Check(!result.Ok, "Invalid auction quantity was accepted: " + amount);
        var alice = Live(f.Engine, f.Alice);
        Check(f.Engine.State.Auctions.Count == 0, "Rejected auction created escrow.");
        Check(Items.Owned(alice, stackId).Quantity == quantity && alice.Gold == gold, "Rejected auction changed inventory or gold.");
    }
});

Test("auction rejects forged ownership without charging the attacker", () =>
{
    var f = Fixture();
    AtService("auctioneer", f.Alice, f.Bob);
    var item = Give(f.Alice, "copper_sword");
    string itemId = item.Id;
    long before = f.Bob.Gold;
    var result = Act(f.Engine, f.Bob, "auction_list", target: "250", item: itemId, amount: 1);
    Check(!result.Ok, "Another player's item was listed.");
    var alice = Live(f.Engine, f.Alice);
    var bob = Live(f.Engine, f.Bob);
    Check(f.Engine.State.Auctions.Count == 0 && alice.Inventory.Any(value => value.Id == itemId), "Forged listing changed item ownership.");
    Check(bob.Gold == before, "Rejected forged listing charged a fee.");
});

Test("auction purchase transfers exact escrow once under request replay", () =>
{
    var f = Fixture();
    AtService("auctioneer", f.Alice, f.Bob);
    var item = Give(f.Alice, "copper_sword");
    var listed = Act(f.Engine, f.Alice, "auction_list", target: "250", item: item.Id, amount: 1);
    Check(listed.Ok, listed.Message);
    var auction = f.Engine.State.Auctions.Values.Single();
    Check(auction.Item.Id == item.Id && f.Alice.Inventory.All(value => value.Id != item.Id), "Auction escrow changed unique item identity.");

    var buyer = Live(f.Engine, f.Bob);
    var command = new GameCommand { Kind = "auction_buy", Target = auction.Id, Sequence = buyer.LastAction + 1 };
    var first = f.Engine.Execute(buyer.Id, command);
    Check(first.Ok, first.Message);
    buyer = Live(f.Engine, buyer);
    var seller = Live(f.Engine, f.Alice);
    Check(buyer.Inventory.Count(value => value.Id == item.Id) == 1 && !f.Engine.State.Auctions.ContainsKey(auction.Id), "Purchase did not transfer exactly one escrow item.");
    long buyerGold = buyer.Gold, sellerGold = seller.Gold;
    var replay = f.Engine.Execute(buyer.Id, command);
    Check(replay.Ok && replay.RequestId == first.RequestId, "Idempotent replay did not return the original receipt.");
    buyer = Live(f.Engine, buyer);
    seller = Live(f.Engine, seller);
    Check(buyer.Inventory.Count(value => value.Id == item.Id) == 1, "Request replay duplicated the purchased item.");
    Check(buyer.Gold == buyerGold && seller.Gold == sellerGold, "Request replay moved gold twice.");
});

Test("private trade snapshot is participant-only and detached from authority", () =>
{
    var f = Fixture();
    var item = Give(f.Alice, "copper_sword");
    Check(Act(f.Engine, f.Alice, "trade_invite", target: f.Bob.Id).Ok, "Trade invite failed.");
    string tradeId = f.Engine.State.Trades.Values.Single().Id;
    Check(Act(f.Engine, f.Alice, "trade_offer", target: tradeId, item: item.Id, amount: 1).Ok, "Trade offer failed.");

    var participant = SnapshotPackets.Create(f.Engine, f.Bob.Id);
    var outsider = SnapshotPackets.Create(f.Engine, f.Observer.Id);
    Check(participant.TradeItems.Count == 1 && participant.TradeItems[0].Item.Id == item.Id, "Participant did not receive the offered item preview.");
    Check(outsider.TradeItems.Count == 0 && outsider.Snapshot!.Trades.Count == 0, "Observer received private trade data.");
    participant.TradeItems[0].Item.Durability = 0;
    Check(Items.Owned(Live(f.Engine, f.Alice), item.Id).Durability == 100, "Client preview aliases authoritative inventory state.");
});

Test("map transition cancels an active private trade", () =>
{
    var f = Fixture();
    foreach (var skill in catalog.Skills) f.Alice.SkillXp[skill.Id] = Progression.Threshold(100);
    var exit = catalog.Zone(f.Alice.Zone).Exits.First();
    f.Alice.Position = exit.Position;
    f.Bob.Zone = f.Alice.Zone;
    f.Bob.Position = exit.Position;
    Check(Act(f.Engine, f.Alice, "trade_invite", target: f.Bob.Id).Ok, "Trade setup failed.");
    Check(f.Engine.State.Trades.Count == 1, "Trade setup did not create an active trade.");
    var transitioned = Act(f.Engine, f.Alice, "transition", target: exit.Id);
    Check(transitioned.Ok, transitioned.Message);
    Check(f.Engine.State.Trades.Count == 0, "Transition left private trade state active across regions.");
    Check(Live(f.Engine, f.Alice).Zone == exit.Target, "Transition did not enter the expected region.");
});

Test("death blocks mutations until authoritative respawn", () =>
{
    var f = Fixture();
    f.Alice.Health = 0;
    f.Alice.DeadUntil = 0;
    long sequence = f.Alice.LastAction;
    var blocked = Act(f.Engine, f.Alice, "party_create");
    Check(!blocked.Ok, "Dead character changed social state.");
    var alice = Live(f.Engine, f.Alice);
    Check(f.Engine.State.Parties.Count == 0 && alice.LastAction == sequence, "Rejected dead-character command mutated state.");
    var respawn = Act(f.Engine, alice, "respawn");
    Check(respawn.Ok, respawn.Message);
    alice = Live(f.Engine, alice);
    Check(alice.Health > 0 && alice.DeadUntil == 0, "Respawn did not restore a living authoritative state.");
    Check(WorldMap.Fits(catalog.Zone(alice.Zone), alice.Position), "Respawn placed the character outside walkable world geometry.");
});

Test("stale group command is rejected and valid leave cancels trade", () =>
{
    var f = Fixture();
    Check(Act(f.Engine, f.Alice, "party_create").Ok, "Party creation failed.");
    string partyId = Live(f.Engine, f.Alice).Party;
    Check(Act(f.Engine, f.Alice, "party_invite", target: f.Bob.Id).Ok, "Party invite failed.");
    Check(Act(f.Engine, f.Bob, "party_join", target: partyId).Ok, "Party join failed.");
    Check(Act(f.Engine, f.Alice, "trade_invite", target: f.Bob.Id).Ok, "Trade setup failed.");

    var bob = Live(f.Engine, f.Bob);
    var stale = new GameCommand { Kind = "party_leave", Sequence = bob.LastAction };
    var staleResult = f.Engine.Execute(bob.Id, stale);
    Check(!staleResult.Ok, "Stale group command was accepted.");
    bob = Live(f.Engine, bob);
    Check(bob.Party == partyId && f.Engine.State.Parties[partyId].Members.Contains(bob.Id), "Stale command changed party membership.");
    Check(f.Engine.State.Trades.Count == 1, "Stale command cancelled the active trade.");

    var leave = Act(f.Engine, bob, "party_leave");
    Check(leave.Ok, leave.Message);
    bob = Live(f.Engine, bob);
    Check(bob.Party == "" && !f.Engine.State.Parties[partyId].Members.Contains(bob.Id), "Valid leave left stale party membership.");
    Check(f.Engine.State.Trades.Count == 0, "Valid party leave left private trade active.");
});

Test("active trade and auction preserve identities across state serialization", () =>
{
    var f = Fixture();
    AtService("auctioneer", f.Alice, f.Bob);
    var offered = Give(f.Alice, "copper_sword");
    var listedItem = Give(f.Alice, "copper_sword");
    Check(Act(f.Engine, f.Alice, "trade_invite", target: f.Bob.Id).Ok, "Trade setup failed.");
    string tradeId = f.Engine.State.Trades.Values.Single().Id;
    Check(Act(f.Engine, f.Alice, "trade_offer", target: tradeId, item: offered.Id, amount: 1).Ok, "Trade offer failed.");
    Check(Act(f.Engine, f.Alice, "auction_list", target: "300", item: listedItem.Id, amount: 1).Ok, "Auction setup failed.");
    string auctionId = f.Engine.State.Auctions.Values.Single().Id;

    var saved = Wire.Copy(f.Engine.State);
    var restored = new RealmEngine(catalog, saved);
    Check(restored.State.Trades.TryGetValue(tradeId, out var trade) && trade.A.Items.GetValueOrDefault(offered.Id) == 1, "Save round trip lost the offered trade item identity.");
    Check(restored.State.Auctions.TryGetValue(auctionId, out var auction) && auction.Item.Id == listedItem.Id, "Save round trip lost auction escrow identity.");
    Check(restored.State.Characters[f.Alice.Id].Inventory.Any(value => value.Id == offered.Id), "Save round trip lost ownership of the active trade item.");
    Check(restored.State.Characters[f.Alice.Id].Inventory.All(value => value.Id != listedItem.Id), "Save round trip duplicated auction escrow into seller inventory.");
});

Test("ignored LFG requester cannot force a party invitation", () =>
{
    var f = Fixture();
    Check(Act(f.Engine, f.Alice, "lfg_set", target: "dungeon", arg: "tank").Ok, "LFG listing setup failed.");
    Check(Act(f.Engine, f.Alice, "ignore", target: f.Bob.Id).Ok, "Ignore setup failed.");
    var request = Act(f.Engine, f.Bob, "lfg_request", target: f.Alice.Id);
    Check(!request.Ok, "Ignored player forced an LFG invitation.");
    var alice = Live(f.Engine, f.Alice);
    var bob = Live(f.Engine, f.Bob);
    Check(bob.Party == "" && alice.Party == "", "Rejected LFG request created a party.");
});

Directory.CreateDirectory("artifacts/test-results");
var report = new
{
    scope = "Task 13 adversarial acceptance",
    passed = results.Count - failures,
    failed = failures,
    results
};
File.WriteAllText("artifacts/test-results/independent-qa.json", JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"TASK13_ADVERSARIAL_RESULTS passed={results.Count - failures} failed={failures}");
Environment.ExitCode = failures == 0 ? 0 : 1;
