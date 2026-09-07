using System.Data;
using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;
using Kairnfall.Server;
using Npgsql;

var database = args.Contains("--database");
var data = Catalog.Load("content/catalog.json");
var results = new List<object>();
int failures = 0;
void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}
void Throws<T>(Action action) where T : Exception
{
    try { action(); }
    catch (T) { return; }
    throw new InvalidOperationException("Expected " + typeof(T).Name);
}
void Test(string name, Action action)
{
    var watch = Stopwatch.StartNew();
    try
    {
        action();
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
(RealmEngine Realm, Character Player) Fixture(string cls = "vanguard")
{
    var realm = new RealmEngine(data);
    var player = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Review Hero", cls, new());
    realm.Active.Add(player.Id);
    return (realm, player);
}
Item Give(Character player, string template)
{
    var item = Items.Create(data, template);
    Items.Add(player.Inventory, item, data);
    return Items.Owned(player, item.Id);
}
Item Wear(Character player, string template)
{
    var item = Give(player, template);
    Items.Equip(player, item.Id, data);
    return item;
}
Creature Target(RealmEngine realm, Character player)
{
    realm.State.Creatures.Clear();
    var definition = data.Mobs.First(value => !value.Boss && !value.Elite && value.Level == 1);
    var creature = new Creature
    {
        Id = "review-target", Template = definition.Id, Zone = player.Zone,
        Position = player.Position, Home = player.Position, Health = 1000000
    };
    realm.State.Creatures.Add(creature.Id, creature);
    return creature;
}
CommandResult Send(RealmEngine realm, Character player, string kind, string target = "", string item = "", string arg = "")
    => realm.Execute(player.Id, new()
    {
        Kind = kind, Target = target, Item = item, Arg = arg,
        Sequence = realm.Player(player.Id).LastAction + 1, X = player.Position.X, Y = player.Position.Y
    });
void Advance(RealmEngine realm, int frames = 20)
{
    for (int index = 0; index < frames; index++) realm.Tick(0.05);
}

if (!database)
{
    Test("An equipped working shield grants shield block", () =>
    {
        var (_, player) = Fixture();
        Wear(player, "copper_shield");
        Check(CombatMath.Stats(player, data).Block > 0, "Shield did not grant block.");
    });
    foreach (var family in new[] { "focus", "orb" })
        Test(family + " never grants shield block even with a block affix", () =>
        {
            var (_, player) = Fixture();
            var item = Wear(player, "copper_" + family);
            item.Affixes.Add(new() { Name = "Test block", Stat = "block", Value = 50 });
            Check(CombatMath.Stats(player, data).Block == 0, "A non-shield offhand granted shield block.");
        });
    Test("A broken equipped shield does not grant block", () =>
    {
        var (_, player) = Fixture();
        Wear(player, "copper_shield").Durability = 0;
        Check(CombatMath.Stats(player, data).Block == 0, "Broken shield still grants block.");
    });
    Test("A spare shield in inventory does not grant block", () =>
    {
        var (_, player) = Fixture();
        Give(player, "copper_shield");
        Check(CombatMath.Stats(player, data).Block == 0, "Unequipped shield grants block.");
    });
    Test("Bows and crossbows retain compatible quivers", () =>
    {
        var (realm, player) = Fixture();
        Wear(player, "copper_bow");
        var quiver = Wear(player, "copper_quiver");
        Check(CombatMath.Stats(player, data).Block == 0, "Quiver grants shield block.");
        Wear(player, "copper_crossbow");
        Check(player.Equipment["offhand"] == quiver.Id, "Compatible weapon change removed the quiver.");
        Check(Items.Validate(realm.State, data).Count == 0, "Valid ranged equipment was rejected.");
    });
    Test("A quiver cannot be equipped with a sword", () =>
    {
        var (_, player) = Fixture();
        var quiver = Give(player, "copper_quiver");
        Throws<RuleException>(() => Items.Equip(player, quiver.Id, data));
        Check(!player.Equipment.ContainsKey("offhand"), "Rejected equip changed the slot.");
    });
    Test("Changing from a bow to a sword detaches but does not delete the quiver", () =>
    {
        var (_, player) = Fixture();
        Wear(player, "copper_bow");
        var quiver = Wear(player, "copper_quiver");
        Wear(player, "copper_sword");
        Check(!player.Equipment.ContainsKey("offhand"), "Incompatible quiver stayed equipped.");
        Check(player.Inventory.Count(item => item.Id == quiver.Id) == 1, "Quiver ownership changed.");
    });
    Test("Unequipping a bow also detaches its quiver", () =>
    {
        var (realm, player) = Fixture();
        var weapon = Wear(player, "copper_bow");
        var quiver = Wear(player, "copper_quiver");
        var result = Send(realm, player, "unequip", arg: "weapon");
        Check(result.Ok, result.Message);
        Check(!player.Equipment.ContainsKey("weapon") && !player.Equipment.ContainsKey("offhand"), "Unequip left an invalid pair.");
        Check(player.Inventory.Any(item => item.Id == weapon.Id) && player.Inventory.Any(item => item.Id == quiver.Id), "Unequip deleted equipment.");
    });
    Test("A two-handed weapon detaches an equipped shield", () =>
    {
        var (_, player) = Fixture();
        var shield = Wear(player, "copper_shield");
        Wear(player, "copper_greatsword");
        Check(!player.Equipment.ContainsKey("offhand"), "Greatsword retained the shield.");
        Check(player.Inventory.Any(item => item.Id == shield.Id), "Detached shield was deleted.");
    });
    Test("A shield cannot be equipped after a two-handed weapon", () =>
    {
        var (_, player) = Fixture();
        Wear(player, "copper_greatsword");
        var shield = Give(player, "copper_shield");
        Throws<RuleException>(() => Items.Equip(player, shield.Id, data));
    });
    Test("A two-handed staff cannot share the offhand with a focus", () =>
    {
        var (_, player) = Fixture();
        Wear(player, "copper_staff");
        var focus = Give(player, "copper_focus");
        Throws<RuleException>(() => Items.Equip(player, focus.Id, data));
    });
    Test("Invalid saved equipment pairs fail validation and grant no block", () =>
    {
        var (realm, player) = Fixture();
        Wear(player, "copper_greatsword");
        var shield = Give(player, "copper_shield");
        player.Equipment["offhand"] = shield.Id;
        Check(Items.Validate(realm.State, data).Any(error => error.Contains("Incompatible hand equipment")), "Invalid pair passed validation.");
        Check(CombatMath.Stats(player, data).Block == 0, "Invalid pair granted shield block.");
    });
    foreach (var family in new[] { "bow", "crossbow", "wand", "tome" })
        Test(family + " projectile retains its original skill after a weapon change", () =>
        {
            var (realm, player) = Fixture();
            var weapon = Wear(player, "copper_" + family);
            var skill = data.Item(weapon.Template).Skill;
            var creature = Target(realm, player);
            var result = Send(realm, player, "attack", creature.Id);
            Check(result.Ok, result.Message);
            var pending = realm.State.Telegraphs.Single(value => value.Source == player.Id);
            Check(pending.Skill == skill && Wire.Copy(pending).Skill == skill, "Attack provenance was not serialized.");
            Wear(player, "copper_sword");
            Advance(realm);
            Check(player.SkillXp[skill] > 0, "Projectile trained no originating skill.");
            Check(player.SkillXp["swordsmanship"] == 0, "Projectile trained the replacement sword skill.");
        });
    foreach (var family in new[] { "spear", "halberd" })
        Test(family + " uses melee reach rather than spawning a projectile", () =>
        {
            var (realm, player) = Fixture();
            Wear(player, "copper_" + family);
            var creature = Target(realm, player);
            double before = creature.Health;
            var result = Send(realm, player, "attack", creature.Id);
            Check(result.Ok, result.Message);
            Check(creature.Health < before, "Polearm did not hit immediately.");
            Check(realm.State.Telegraphs.All(value => value.Source != player.Id), "Polearm spawned a projectile.");
            Check(player.SkillXp["spear_mastery"] > 0, "Polearm trained no spear skill.");
        });
    foreach (var kind in new[] { "projectile", "area", "cone", "line", "field" })
        Test(kind + " abilities store their actual skill on every delayed hit", () =>
        {
            var ability = data.Abilities.Where(value => value.Kind == kind).OrderBy(value => value.Requirement).First();
            var (realm, player) = Fixture(ability.Class == "" ? "vanguard" : ability.Class);
            player.SkillXp[ability.Skill] = Progression.Threshold(ability.Requirement);
            player.Mana = 100000;
            player.Stamina = 100000;
            var creature = Target(realm, player);
            var result = Send(realm, player, "cast", creature.Id, ability.Id);
            Check(result.Ok, result.Message);
            var pending = realm.State.Telegraphs.Where(value => value.Source == player.Id).ToArray();
            Check(pending.Length > 0, "Ability created no delayed hit.");
            Check(pending.All(value => value.Skill == ability.Skill), "A delayed hit lost its originating skill.");
            Check(Wire.Copy(realm.State).Telegraphs.Where(value => value.Source == player.Id).All(value => value.Skill == ability.Skill), "Save round trip lost the skill.");
        });
    Test("A projectile cannot target a creature in another region", () =>
    {
        var ability = data.Abilities.Where(value => value.Kind == "projectile").OrderBy(value => value.Requirement).First();
        var (realm, player) = Fixture(ability.Class == "" ? "vanguard" : ability.Class);
        player.SkillXp[ability.Skill] = Progression.Threshold(ability.Requirement);
        player.Mana = 100000;
        var creature = Target(realm, player);
        creature.Zone = data.Zones.First(value => value.Id != player.Zone).Id;
        double mana = player.Mana;
        var result = Send(realm, player, "cast", creature.Id, ability.Id);
        Check(!result.Ok, "Cross-region target was accepted.");
        Check(realm.Player(player.Id).Mana == mana && realm.State.Telegraphs.Count == 0, "Rejected cast spent mana or created a hit.");
    });
    Test("A legacy player telegraph without skill metadata cannot invent sword XP", () =>
    {
        var (realm, player) = Fixture();
        Wear(player, "copper_bow");
        var creature = Target(realm, player);
        Check(Send(realm, player, "attack", creature.Id).Ok, "Attack setup failed.");
        realm.State.Telegraphs.Single(value => value.Source == player.Id).Skill = "";
        Advance(realm);
        Check(player.SkillXp["archery"] == 0 && player.SkillXp["swordsmanship"] == 0, "Unknown provenance invented experience.");
    });
    foreach (var field in new[] { "kind", "target", "item", "arg" })
        Test("Null " + field + " is rejected without a crash or state change", () =>
        {
            var (realm, player) = Fixture();
            var command = new GameCommand { Kind = "attack", Sequence = 1 };
            switch (field)
            {
                case "kind": command.Kind = null!; break;
                case "target": command.Target = null!; break;
                case "item": command.Item = null!; break;
                case "arg": command.Arg = null!; break;
            }
            string before = JsonSerializer.Serialize(realm.State, Wire.Json);
            var result = realm.Execute(player.Id, command);
            Check(!result.Ok, "Null field was accepted.");
            Check(JsonSerializer.Serialize(realm.State, Wire.Json) == before, "Rejected command changed realm state.");
        });
    Test("Character name length is checked after removing surrounding spaces", () =>
    {
        var realm = new RealmEngine(data);
        Throws<RuleException>(() => realm.CreateCharacter(Guid.NewGuid().ToString("N"), "A  ", "vanguard", new()));
        var player = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "  Oak Warden  ", "vanguard", new());
        Check(player.Name == "Oak Warden", "Name was not normalized.");
    });
    Test("Expired event cleanup removes its objects but preserves similar event IDs", () =>
    {
        var state = new RealmState();
        state.Events.Add(new() { Id = "event/1", Ends = 10 });
        state.Events.Add(new() { Id = "event/10", Ends = 100 });
        foreach (var id in new[] { "event/1", "event/1/0", "event/1/0/add/one", "event/10", "ordinary" })
        {
            state.Nodes[id] = new() { Id = id };
            state.Chests[id] = new() { Id = id };
            state.Creatures[id] = new() { Id = id };
            state.Telegraphs.Add(new() { Source = id });
        }
        Check(WorldEventLifecycle.Expire(state, 10) == 1, "Wrong expired event count.");
        Check(state.Events.Single().Id == "event/10", "A live event was removed.");
        Check(state.Nodes.Count == 2 && state.Chests.Count == 2 && state.Creatures.Count == 2, "Expired event objects survived.");
        Check(state.Telegraphs.Count == 2 && state.Nodes.ContainsKey("event/10") && state.Nodes.ContainsKey("ordinary"), "Cleanup matched unrelated objects.");
        Check(WorldEventLifecycle.Expire(state, 10) == 0, "Cleanup was not idempotent.");
    });
    Test("Restarting within an active event cycle does not duplicate the event", () =>
    {
        var (realm, player) = Fixture();
        realm.State.Time = 310;
        realm.State.Events.Add(new() { Id = "event/1", Zone = player.Zone, Position = player.Position, Ends = 550 });
        var restored = new RealmEngine(data, Wire.Copy(realm.State));
        restored.Active.Add(player.Id);
        Advance(restored, 40);
        Check(restored.State.Events.Count(value => value.Id == "event/1") == 1, "Restart duplicated the active event.");
    });
    Test("Restarting after event expiry does not recreate the expired cycle", () =>
    {
        var (realm, player) = Fixture();
        realm.State.Time = 280;
        var restored = new RealmEngine(data, Wire.Copy(realm.State));
        restored.Active.Add(player.Id);
        Advance(restored, 40);
        Check(restored.State.Events.Count == 0, "Restart recreated an expired event cycle.");
    });
}
else
{
    if (Environment.GetEnvironmentVariable("KAIRNFALL_ALLOW_DB_TESTS") != "1")
        throw new InvalidOperationException("Database review tests require KAIRNFALL_ALLOW_DB_TESTS=1 and a disposable test database.");
    var connectionString = Environment.GetEnvironmentVariable("KAIRNFALL_TEST_DB")
        ?? throw new InvalidOperationException("KAIRNFALL_TEST_DB is required.");
    string schema = "kairnfall_review_" + Guid.NewGuid().ToString("N");
    await using var adminSource = new NpgsqlDataSourceBuilder(connectionString).Build();
    await using (var create = adminSource.CreateCommand("CREATE SCHEMA \"" + schema + "\""))
        await create.ExecuteNonQueryAsync();
    try
    {
        var settings = new NpgsqlConnectionStringBuilder(connectionString) { SearchPath = schema, MaxPoolSize = 8 };
        await using var source = new NpgsqlDataSourceBuilder(settings.ConnectionString).Build();
        await using var store = new RealmStore(source);
        await store.InitializeAsync(CancellationToken.None);
        var (realm, _) = Fixture();
        Test("First save creates revision one and a matching payload", () =>
        {
            store.SaveAsync(realm, CancellationToken.None).GetAwaiter().GetResult();
            Check(realm.State.Revision == 1, "First revision was not one.");
            var save = store.LoadAsync(CancellationToken.None).GetAwaiter().GetResult();
            Check(save is not null && save.State.Revision == 1, "Stored payload revision differs.");
        });
        var staleState = Wire.Copy(realm.State);
        Test("A normal second save advances the revision", () =>
        {
            store.SaveAsync(realm, CancellationToken.None).GetAwaiter().GetResult();
            Check(realm.State.Revision == 2, "Second revision was not two.");
        });
        Test("A stale writer cannot overwrite the saved realm", () =>
        {
            var stale = new RealmEngine(data, staleState);
            Throws<DBConcurrencyException>(() => store.SaveAsync(stale, CancellationToken.None).GetAwaiter().GetResult());
            Check(stale.State.Revision == 1, "Failed stale save changed its in-memory revision.");
            Check(store.LoadAsync(CancellationToken.None).GetAwaiter().GetResult()!.State.Revision == 2, "Stale save changed the stored revision.");
        });
        Test("A fresh realm cannot replace an existing snapshot", () =>
        {
            var fresh = new RealmEngine(data);
            Throws<DBConcurrencyException>(() => store.SaveAsync(fresh, CancellationToken.None).GetAwaiter().GetResult());
            Check(fresh.State.Revision == 0, "Failed first save changed the fresh revision.");
        });
        Test("A deleted snapshot row cannot be silently recreated by a later save", () =>
        {
            using (var delete = source.CreateCommand("DELETE FROM realm_snapshots WHERE id=1"))
                Check(delete.ExecuteNonQuery() == 1, "Snapshot deletion fixture failed.");
            long revision = realm.State.Revision;
            Throws<DBConcurrencyException>(() => store.SaveAsync(realm, CancellationToken.None).GetAwaiter().GetResult());
            Check(realm.State.Revision == revision, "Failed save advanced the in-memory revision.");
            Check(store.LoadAsync(CancellationToken.None).GetAwaiter().GetResult() is null, "Failed save recreated the missing row.");
        });
    }
    finally
    {
        // Only remove the unique schema created by this invocation.
        await using var drop = adminSource.CreateCommand("DROP SCHEMA \"" + schema + "\" CASCADE");
        await drop.ExecuteNonQueryAsync();
    }
}
Directory.CreateDirectory("artifacts/test-results");
string report = "artifacts/test-results/review-" + (database ? "database" : "core") + ".json";
File.WriteAllText(report, JsonSerializer.Serialize(new { passed = results.Count - failures, failed = failures, results }, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"RESULT: {results.Count - failures} passed; {failures} failed.");
Environment.ExitCode = failures == 0 ? 0 : 1;
