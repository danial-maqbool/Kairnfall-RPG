using Kairnfall.Core;

var catalog = Catalog.Load(args.Length > 0 ? args[0] : "content/catalog.json");
int passed = 0, failed = 0;
void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
void Test(string name, Action body)
{
    try { body(); passed++; Console.WriteLine("PASS " + name); }
    catch (Exception error) { failed++; Console.WriteLine("FAIL " + name + ": " + error.Message); }
}
(RealmEngine Engine, string Alice, string Bob, string Observer) Fixture()
{
    var engine = new RealmEngine(catalog);
    var a = engine.CreateCharacter("security-a", "Security Alice", "vanguard", new());
    var b = engine.CreateCharacter("security-b", "Security Bob", "ranger", new());
    var c = engine.CreateCharacter("security-c", "Security Observer", "rogue", new());
    foreach (var p in new[] { a, b, c }) { engine.Active.Add(p.Id); p.Gold = 1000; }
    return (engine, a.Id, b.Id, c.Id);
}
CommandResult Act(RealmEngine engine, string actor, string kind, string target = "", string item = "", int amount = 1, string arg = "")
    => engine.Execute(actor, new GameCommand { Kind = kind, Target = target, Item = item, Amount = amount, Arg = arg, Sequence = engine.Player(actor).LastAction + 1 });
(string Trade, string Item) Offer(RealmEngine engine, string alice, string bob)
{
    var item = Items.Create(catalog, "copper_sword", 1, Rarity.Rare); item.Sockets = 1;
    Items.Add(engine.Player(alice).Inventory, item, catalog);
    Check(Act(engine, alice, "trade_invite", bob).Ok, "Could not create test trade.");
    string trade = engine.State.Trades.Values.Single().Id;
    Check(Act(engine, alice, "trade_offer", trade, item.Id).Ok, "Could not offer test item.");
    return (trade, item.Id);
}

Test("trade consent cannot survive offered-item rune mutation", () =>
{
    var f = Fixture(); var offer = Offer(f.Engine, f.Alice, f.Bob);
    int revision = f.Engine.State.Trades[offer.Trade].Revision;
    Check(Act(f.Engine, f.Alice, "trade_ready", offer.Trade, amount: revision).Ok, "Alice ready failed.");
    Check(Act(f.Engine, f.Bob, "trade_ready", offer.Trade, amount: revision).Ok, "Bob ready failed.");
    Check(Act(f.Engine, f.Bob, "trade_confirm", offer.Trade, amount: revision).Ok, "Bob confirmation failed.");
    var rune = f.Engine.Player(f.Alice).Inventory.First(x => catalog.Item(x.Template).Type == "rune");
    var mutation = Act(f.Engine, f.Alice, "socket", offer.Item, rune.Id);
    if (mutation.Ok && f.Engine.State.Trades.TryGetValue(offer.Trade, out var current))
        Check(current.Revision != revision && !current.A.Ready && !current.B.Ready && !current.A.Confirmed && !current.B.Confirmed,
            "Rune mutation changed an offered item while preserving prior consent.");
    var final = Act(f.Engine, f.Alice, "trade_confirm", offer.Trade, amount: revision);
    Check(!mutation.Ok || !final.Ok, "A stale confirmed offer was executed after its item changed.");
});

Test("trade previews expose offered items only to participants", () =>
{
    var f = Fixture(); var offer = Offer(f.Engine, f.Alice, f.Bob);
    var bob = SnapshotPackets.Create(f.Engine, f.Bob);
    var outsider = SnapshotPackets.Create(f.Engine, f.Observer);
    Check(bob.TradeItems.Count == 1, "Participant preview did not contain exactly the offered item.");
    Check(bob.TradeItems[0].Item.Id == offer.Item && bob.TradeItems[0].Item.Template == "copper_sword", "Preview identity mismatch.");
    Check(outsider.TradeItems.Count == 0, "An observer received private offered-item details.");
    Check(outsider.Snapshot!.Trades.Count == 0, "An observer received a private trade.");
    Check(bob.Snapshot!.Self.Account == "", "The client snapshot exposed an account identifier.");
    bob.TradeItems[0].Item.Durability = 0;
    Check(Items.Owned(f.Engine.Player(f.Alice), offer.Item).Durability == 100, "Preview objects alias authoritative inventory.");
});

Test("split conserves quantity and replay is idempotent", () =>
{
    var f = Fixture(); var before = f.Engine.Player(f.Alice).Inventory.First(x => x.Template == "healing_potion");
    int total = f.Engine.Player(f.Alice).Inventory.Where(x => x.Template == before.Template).Sum(x => x.Quantity);
    var command = new GameCommand { Kind = "split", Item = before.Id, Amount = 2, Sequence = f.Engine.Player(f.Alice).LastAction + 1 };
    var result = f.Engine.Execute(f.Alice, command); Check(result.Ok, "Authoritative split failed: " + result.Message);
    var replay = f.Engine.Execute(f.Alice, command); Check(replay.Ok, "Split replay did not return the original result.");
    var stacks = f.Engine.Player(f.Alice).Inventory.Where(x => x.Template == before.Template).ToList();
    Check(stacks.Count == 2, "Split did not produce exactly two stacks.");
    Check(stacks.Sum(x => x.Quantity) == total, "Split changed total quantity.");
    Check(stacks.Select(x => x.Id).Distinct().Count() == 2, "Split duplicated an instance ID.");
    Check(stacks.Any(x => x.Quantity == 2), "Split quantity is incorrect.");
});

Test("invalid split quantities cannot alter inventory", () =>
{
    foreach (int amount in new[] { 0, -1, int.MaxValue, 5 })
    {
        var f = Fixture(); var potion = f.Engine.Player(f.Alice).Inventory.First(x => x.Template == "healing_potion");
        string before = System.Text.Json.JsonSerializer.Serialize(f.Engine.Player(f.Alice).Inventory, Wire.Json);
        Check(!Act(f.Engine, f.Alice, "split", item: potion.Id, amount: amount).Ok, "Invalid split quantity was accepted.");
        Check(System.Text.Json.JsonSerializer.Serialize(f.Engine.Player(f.Alice).Inventory, Wire.Json) == before, "Rejected split mutated inventory.");
    }
});

Test("a full inventory rejects stack splitting without loss", () =>
{
    var f = Fixture(); var player = f.Engine.Player(f.Alice);
    while (player.Inventory.Count < Items.InventoryCapacity) Items.Add(player.Inventory, Items.Create(catalog, "copper_sword"), catalog);
    var potion = player.Inventory.First(x => x.Template == "healing_potion");
    Check(!Act(f.Engine, f.Alice, "split", item: potion.Id, amount: 2).Ok, "Split bypassed the storage limit.");
    Check(f.Engine.Player(f.Alice).Inventory.Count == Items.InventoryCapacity, "Rejected split changed slot count.");
    Check(Items.Owned(f.Engine.Player(f.Alice), potion.Id).Quantity == potion.Quantity, "Rejected split lost items.");
});

Console.WriteLine($"SECURITY_RESULTS passed={passed} failed={failed}");
return failed == 0 ? 0 : 1;
