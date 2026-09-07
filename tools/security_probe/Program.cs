using System.Collections;
using System.Collections.Concurrent;
using System.Net.WebSockets;
using System.Reflection;
using Kairnfall.Core;
using Kairnfall.Server;
using Microsoft.Extensions.Logging.Abstractions;

// Isolated defect probes. No database, accounts service, network listener, or
// saved realm is opened. Reflection wires only the host command boundary.
// These fixtures are not normal-play, real-network, or persistence acceptance.
var catalog = Catalog.Load(args.Length > 0 ? args[0] : "content/catalog.json");
int failures = 0, probes = 0;
async Task Probe(string name, Func<Task> body)
{
    probes++;
    try { await body(); Console.WriteLine("PASS " + name); }
    catch (Exception error) { failures++; Console.WriteLine("FAIL " + name + ": " + error.Message); }
}
void Check(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}
FieldInfo Field(Type type, string name) => type.GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)
    ?? throw new InvalidOperationException("Probe wiring changed: " + type.Name + "." + name);
(RealmEngine Realm, Character Player) Fixture(string name)
{
    var realm = new RealmEngine(catalog);
    var player = realm.CreateCharacter("isolated-probe-account", name, "vanguard", new());
    realm.State.Creatures.Clear();
    realm.Active.Add(player.Id);
    return (realm, player);
}

foreach(bool expired in new[] { true, false })
await Probe(expired ? "expired session cannot enqueue authoritative movement" : "valid session can enqueue authoritative movement", async () =>
{
    var (realm, player) = Fixture("Expiry Probe");
    using var socket = new ClientWebSocket();
    using var peer = new Peer(socket, new AccountSession(player.Account, "isolated-probe", DateTimeOffset.UtcNow.AddMinutes(expired ? -1 : 1)), player.Id);
    // Dependencies deliberately absent: movement must reject without touching
    // persistence, account lookup, or application lifetime infrastructure.
    using var host = new RealmHost(catalog, null!, null!, null!, NullLogger<RealmHost>.Instance);
    Field(typeof(RealmHost), "engine").SetValue(host, realm);
    Field(typeof(RealmHost), "ready").SetValue(host, true);
    var peers = (ConcurrentDictionary<string, Peer>)Field(typeof(RealmHost), "peers").GetValue(host)!;
    peers[player.Id] = peer;
    await host.HandleCommandAsync(peer, new GameCommand { Kind = "move", X = 1, Y = 0 }, CancellationToken.None);
    var inputs = (IDictionary)Field(typeof(RealmEngine), "inputs").GetValue(realm)!;
    Console.WriteLine($"EVIDENCE session_expired={expired}; movement_accepted={inputs.Contains(player.Id)}");
    Check(inputs.Contains(player.Id) == !expired, "Session expiry did not determine movement authority correctly.");
});

await Probe("expired session cannot attach", async () =>
{
    var (realm, player) = Fixture("Attach Probe");
    realm.Active.Remove(player.Id);
    using var socket = new ClientWebSocket();
    using var host = new RealmHost(catalog, null!, null!, null!, NullLogger<RealmHost>.Instance);
    Field(typeof(RealmHost), "engine").SetValue(host, realm);
    Field(typeof(RealmHost), "ready").SetValue(host, true);
    bool rejected = false;
    try { await host.AttachAsync(socket, new AccountSession(player.Account, "isolated-probe", DateTimeOffset.UtcNow.AddMinutes(-1)), player.Id, CancellationToken.None); }
    catch (RuleException) { rejected = true; }
    Check(rejected && !realm.Active.Contains(player.Id), "Expired handshake activated a character.");
});

await Probe("disconnect does not erase lethal pending poison", () =>
{
    var connected = Fixture("Connected Probe");
    var disconnected = Fixture("Logout Probe");
    foreach (var fixture in new[] { connected, disconnected })
    {
        fixture.Player.Health = 1;
        fixture.Player.LastCombat = fixture.Realm.State.Time;
        fixture.Player.Statuses.Add(new StatusEffect { Kind = "poison", Element = Element.Poison, Power = 100, Until = fixture.Realm.State.Time + 3 });
        // A later regeneration entry must not resurrect a lethal damage tick.
        fixture.Player.Statuses.Add(new StatusEffect { Kind = "regeneration", Element = Element.Nature, Power = 100, Until = fixture.Realm.State.Time + 3 });
    }
    disconnected.Realm.Disconnect(disconnected.Player.Id);
    for (int n = 0; n < 90; n++) { connected.Realm.Tick(.05); disconnected.Realm.Tick(.05); }
    disconnected.Realm.Active.Add(disconnected.Player.Id);
    disconnected.Realm.Tick(.05);
    var online = connected.Realm.Player(connected.Player.Id);
    var rejoined = disconnected.Realm.Player(disconnected.Player.Id);
    Console.WriteLine($"EVIDENCE connected_health={online.Health}; disconnected_rejoined_health={rejoined.Health}; remaining_poison={rejoined.Statuses.Any(x => x.Kind == "poison")}");
    Check(online.Health == 0, "Control fixture did not experience lethal poison.");
    Check(rejoined.Health == 0, "Disconnecting until the poison deadline avoided lethal damage.");
    return Task.CompletedTask;
});

await Probe("offline pending damage grants neither regeneration nor training", () =>
{
    var (realm, player) = Fixture("Offline Probe");
    player.Health = 20; player.Mana = 1; player.Stamina = 1;
    var xp = player.SkillXp.ToDictionary(x => x.Key, x => x.Value);
    player.Statuses.Add(new StatusEffect { Kind = "poison", Element = Element.Poison, Power = 1, Until = realm.State.Time + 3 });
    player.Statuses.Add(new StatusEffect { Kind = "regeneration", Element = Element.Nature, Power = 100, Until = realm.State.Time + 3 });
    player.Statuses.Add(new StatusEffect { Kind = "meditate", Element = Element.Arcane, Power = 1, Until = realm.State.Time + 3 });
    realm.Disconnect(player.Id);
    for (int n = 0; n < 90; n++) realm.Tick(.05);
    Check(player.Health > 0 && player.Health < 20, "Offline damage was skipped or regeneration was awarded.");
    Check(player.Mana == 1 && player.Stamina == 1, "Offline resources regenerated.");
    Check(player.SkillXp.Count == xp.Count && xp.All(x => player.SkillXp.GetValueOrDefault(x.Key) == x.Value), "Offline status processing awarded skill XP.");
    return Task.CompletedTask;
});

Console.WriteLine($"ISOLATED SECURITY PROBES: {probes - failures} passed, {failures} failed.");
return failures == 0 ? 0 : 1;
