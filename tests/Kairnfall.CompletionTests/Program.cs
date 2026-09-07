using Kairnfall.Core;

var data = Catalog.Load("content/catalog.json");
var failures = 0;

void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

void Test(string name, Action action)
{
    try
    {
        action();
        Console.WriteLine("PASS " + name);
    }
    catch (Exception error)
    {
        failures++;
        Console.WriteLine("FAIL " + name + "\n" + error);
    }
}

(RealmEngine Realm, Character Player) Fixture(string name = "Completion Hero")
{
    var realm = new RealmEngine(data);
    var player = realm.CreateCharacter(Guid.NewGuid().ToString("N"), name, "vanguard", new());
    realm.Active.Add(player.Id);
    return (realm, player);
}

CommandResult Send(RealmEngine realm, Character player, string kind, string target = "", string item = "", string arg = "")
    => realm.Execute(player.Id, new GameCommand
    {
        Kind = kind,
        Target = target,
        Item = item,
        Arg = arg,
        RequestId = Guid.NewGuid().ToString("N"),
        Sequence = realm.Player(player.Id).LastAction + 1
    });

Test("Guild leader can promote and demote an officer", () =>
{
    var (realm, leader) = Fixture("Guild Leader");
    var member = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Guild Member", "vanguard", new());
    var guild = new SocialGroup
    {
        Name = "Completion Guild",
        Leader = leader.Id,
        Members = [leader.Id, member.Id],
        Roles = new() { [leader.Id] = "leader", [member.Id] = "member" }
    };
    realm.State.Guilds[guild.Id] = guild;
    leader.Guild = guild.Id;
    member.Guild = guild.Id;

    var promote = Send(realm, leader, "guild_role", member.Id, arg: "officer");
    Check(promote.Ok, promote.Message);
    Check(guild.Roles[member.Id] == "officer", "Promotion did not change the role.");

    var demote = Send(realm, leader, "guild_role", member.Id, arg: "member");
    Check(demote.Ok, demote.Message);
    Check(guild.Roles[member.Id] == "member", "Demotion did not change the role.");
});

Test("Non-leader cannot change guild roles", () =>
{
    var (realm, leader) = Fixture("Second Leader");
    var officer = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Guild Officer", "vanguard", new());
    var member = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Second Member", "vanguard", new());
    var guild = new SocialGroup
    {
        Name = "Restricted Guild",
        Leader = leader.Id,
        Members = [leader.Id, officer.Id, member.Id],
        Roles = new() { [leader.Id] = "leader", [officer.Id] = "officer", [member.Id] = "member" }
    };
    realm.State.Guilds[guild.Id] = guild;
    leader.Guild = guild.Id;
    officer.Guild = guild.Id;
    member.Guild = guild.Id;

    var result = Send(realm, officer, "guild_role", member.Id, arg: "officer");
    Check(!result.Ok, "Officer changed a guild role without leader authority.");
    Check(guild.Roles[member.Id] == "member", "Rejected role change modified guild state.");
});

Test("Pet dismissal releases the companion and clears combat state", () =>
{
    var (realm, player) = Fixture();
    var animal = data.Mobs.First(value => value.Anatomy.StartsWith("animal:", StringComparison.Ordinal) && !value.Boss && !value.Elite);
    var pet = new Creature
    {
        Id = "completion-pet",
        Template = animal.Id,
        Zone = player.Zone,
        Position = player.Position,
        Home = player.Position,
        Health = animal.Health,
        Owner = player.Id,
        Target = "hostile-target",
        Threat = new() { ["hostile-target"] = 20 }
    };
    realm.State.Creatures[pet.Id] = pet;
    player.Pet = pet.Id;

    var result = Send(realm, player, "pet_dismiss");
    Check(result.Ok, result.Message);
    Check(player.Pet == "", "Character still references the released companion.");
    Check(pet.Owner == "" && pet.Target == "" && pet.Threat.Count == 0, "Released companion retained ownership or combat state.");
});

Test("Pet dismissal repairs a stale companion reference", () =>
{
    var (realm, player) = Fixture();
    player.Pet = "missing-pet";
    var result = Send(realm, player, "pet_dismiss");
    Check(result.Ok, result.Message);
    Check(player.Pet == "", "Stale companion reference was not cleared.");
});

Test("Owner can dismantle a structure", () =>
{
    var (realm, player) = Fixture();
    var structure = data.Items.First(value => value.Type == "structure");
    var node = new WorldNode
    {
        Id = "completion-structure",
        Template = structure.Id,
        Zone = player.Zone,
        Position = player.Position,
        Owner = player.Id
    };
    realm.State.Nodes[node.Id] = node;

    var result = Send(realm, player, "dismantle", node.Id);
    Check(result.Ok, result.Message);
    Check(!realm.State.Nodes.ContainsKey(node.Id), "Dismantled structure remains in the realm.");
    Check(Items.Validate(realm.State, data).Count == 0, "Dismantling produced invalid inventory state.");
});

Test("Player cannot dismantle another player's structure", () =>
{
    var (realm, player) = Fixture();
    var owner = realm.CreateCharacter(Guid.NewGuid().ToString("N"), "Structure Owner", "vanguard", new());
    var structure = data.Items.First(value => value.Type == "structure");
    var node = new WorldNode
    {
        Id = "protected-structure",
        Template = structure.Id,
        Zone = player.Zone,
        Position = player.Position,
        Owner = owner.Id
    };
    realm.State.Nodes[node.Id] = node;

    var result = Send(realm, player, "dismantle", node.Id);
    Check(!result.Ok, "Foreign structure dismantling was accepted.");
    Check(realm.State.Nodes.ContainsKey(node.Id), "Rejected dismantle removed the structure.");
});

Console.WriteLine($"Completion regression tests: {6 - failures} passed, {failures} failed.");
return failures == 0 ? 0 : 1;
