using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net.WebSockets;
using Kairnfall.Core;

namespace Kairnfall.Server;

public sealed class RealmHost(Catalog catalog, RealmStore store, AccountStore accounts, IHostApplicationLifetime lifetime, ILogger<RealmHost> logger) : BackgroundService
{
    private readonly SemaphoreSlim gate = new(1, 1);
    private readonly ConcurrentDictionary<string, Peer> peers = new();
    private readonly Queue<double> tickDurations = new();
    private RealmEngine? engine;
    private volatile bool ready;
    private long ticks, overruns, commits;
    private double lastPeriodicSave;
    private DateTimeOffset nextSessionCheck = DateTimeOffset.UtcNow.AddSeconds(30);
    public bool Ready => ready;
    private RealmEngine Engine => engine ?? throw new InvalidOperationException("The realm has not started.");

    public override async Task StartAsync(CancellationToken cancel)
    {
        await store.InitializeAsync(cancel);
        var saved = await store.LoadAsync(cancel);
        engine = new RealmEngine(catalog, saved?.State);
        if (saved is not null) engine.Loot = saved.Loot;
        engine.State.Trades.Clear();
        ValidatePersistentState(engine);
        await store.SaveAsync(engine, cancel); commits++;
        ready = true;
        logger.LogInformation("Realm ready. Protocol {Protocol}; revision {Revision}; {Zones} connected zones.", Wire.Version, engine.State.Revision, catalog.Zones.Count);
        await base.StartAsync(cancel);
    }
    private static void ValidatePersistentState(RealmEngine realm)
    {
        var errors = Items.Validate(realm.State, realm.Data);
        var ids = new HashSet<string>();
        foreach (var character in realm.State.Characters.Values)
        {
            foreach (var item in character.Inventory.Concat(character.Bank)) { ids.Add(item.Id); foreach (var rune in item.Runes) ids.Add(rune.Id); }
            var zone = realm.Data.Zones.FirstOrDefault(x => x.Id == character.Zone);
            if (zone is null || !WorldMap.Fits(zone, character.Position) || !double.IsFinite(character.Health) || !double.IsFinite(character.Mana) || !double.IsFinite(character.Stamina)) errors.Add("Invalid persisted character position or statistics: " + character.Id);
        }
        foreach (var auction in realm.State.Auctions.Values) { ids.Add(auction.Item.Id); foreach (var rune in auction.Item.Runes) ids.Add(rune.Id); }
        foreach (var pile in realm.Loot.Values)
        {
            if (pile.Gold < 0 || pile.Gold > Items.GoldCap) errors.Add("Invalid persisted loot gold.");
            foreach (var item in pile.Items)
            {
                var definition = realm.Data.Items.FirstOrDefault(x => x.Id == item.Template);
                if (definition is null || item.Quantity < 1 || item.Quantity > definition.StackMax || !ids.Add(item.Id)) errors.Add("Invalid or duplicated persisted loot item.");
                foreach (var rune in item.Runes) if (!ids.Add(rune.Id)) errors.Add("Duplicated persisted rune.");
            }
        }
        if (errors.Count > 0) throw new InvalidDataException(string.Join("\n", errors));
    }
    private void RequireReady() { if (!ready) throw new RuleException("The realm is not available. Reconnect after the server recovers."); }
    public async Task<T> ReadAsync<T>(Func<RealmEngine, T> read, CancellationToken cancel)
    {
        await gate.WaitAsync(cancel);
        try { RequireReady(); return read(Engine); }
        finally { gate.Release(); }
    }
    public async Task<T> WriteAsync<T>(Func<RealmEngine, T> write, CancellationToken cancel)
    {
        await gate.WaitAsync(cancel);
        try { RequireReady(); var result = write(Engine); await PersistAsync(cancel); return result; }
        catch (RuleException) { throw; }
        catch (Exception error) { FailClosed(error); throw new RuleException("The server could not confirm the operation. Reconnect before retrying."); }
        finally { gate.Release(); }
    }
    private async Task PersistAsync(CancellationToken cancel)
    {
        ValidatePersistentState(Engine);
        await store.SaveAsync(Engine, cancel); commits++; lastPeriodicSave = Engine.State.Time;
    }
    private void FailClosed(Exception error)
    {
        ready = false;
        logger.LogCritical(error, "The authoritative realm stopped because state could not be verified or persisted. No success acknowledgement was sent for the failed operation.");
        foreach (var peer in peers.Values) peer.Abort();
        lifetime.StopApplication();
    }
    public async Task<Peer> AttachAsync(WebSocket socket, AccountSession session, string character, CancellationToken cancel)
    {
        await gate.WaitAsync(cancel);
        try
        {
            RequireReady();
            if (session.Expires <= DateTimeOffset.UtcNow) throw new RuleException("Your session expired. Sign in again.");
            var player = Engine.Player(character);
            if (player.Account != session.AccountId) throw new RuleException("This character does not belong to the signed-in account.");
            if (peers.ContainsKey(character) || peers.Values.Any(x => x.Session.AccountId == session.AccountId)) throw new RuleException("This account already has an active character connection.");
            var peer = new Peer(socket, session, character);
            if (!peers.TryAdd(character, peer)) throw new RuleException("This character is already connected.");
            Engine.Active.Add(character); SendSnapshot(peer); return peer;
        }
        finally { gate.Release(); }
    }
    public async Task HandleCommandAsync(Peer peer, GameCommand command, CancellationToken cancel)
    {
        if (command.Kind is null || command.Target is null || command.Item is null || command.Arg is null || command.RequestId is null)
        { peer.Enqueue(new() { Kind = "error", Error = "Command fields cannot be null." }); return; }
        if (!peer.AcceptRate(command.Kind)) { peer.Enqueue(new() { Kind = "error", Error = "Too many commands. Reduce the input rate." }); return; }
        await gate.WaitAsync(cancel);
        try
        {
            RequireReady();
            if (!peers.TryGetValue(peer.CharacterId, out var current) || !ReferenceEquals(current, peer)) throw new RuleException("This connection is no longer active.");
            // Check after acquiring the gate: queued commands must not retain
            // authority across expiry or connection revocation.
            if (peer.Closed.IsCancellationRequested || peer.Session.Expires <= DateTimeOffset.UtcNow)
            {
                peer.Abort();
                return;
            }
            var result = Engine.Execute(peer.CharacterId, command);
            if (command.Kind == "move") { if (!result.Ok) peer.Enqueue(new() { Kind = "result", Result = result }); return; }
            if (result.Ok) await PersistAsync(cancel);
            peer.Enqueue(new() { Kind = "result", Result = result }); FlushChat(); SendSnapshot(peer);
        }
        catch (RuleException error) { peer.Enqueue(new() { Kind = "error", Error = error.Message }); }
        catch (Exception error) { FailClosed(error); }
        finally { gate.Release(); }
    }
    private void SendSnapshot(Peer peer) => peer.Enqueue(SnapshotPackets.Create(Engine, peer.CharacterId));
    private void FlushChat()
    {
        foreach (var message in Engine.OutgoingChat)
            foreach (var peer in peers.Values)
                if (Engine.CanReceiveChat(peer.CharacterId, message)) peer.Enqueue(new() { Kind = "chat", Chat = message });
        Engine.OutgoingChat.Clear();
    }
    public async Task DetachAsync(Peer peer, CancellationToken cancel)
    {
        peer.Abort(); await gate.WaitAsync(cancel);
        try
        {
            if (peers.TryGetValue(peer.CharacterId, out var current) && ReferenceEquals(current, peer))
            {
                peers.TryRemove(peer.CharacterId, out _);
                if (engine is not null) Engine.Disconnect(peer.CharacterId);
                if (ready) await PersistAsync(cancel);
            }
        }
        catch (Exception error) when (error is not OperationCanceledException) { FailClosed(error); }
        finally { gate.Release(); }
    }
    public void RevokeConnections(string fingerprint)
    {
        foreach (var peer in peers.Values.Where(x => x.Session.TokenFingerprint == fingerprint)) peer.Abort();
    }
    public void RevokeAccountConnections(string account)
    {
        foreach (var peer in peers.Values.Where(x => x.Session.AccountId == account)) peer.Abort();
    }
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromMilliseconds(50));
        try
        {
            while (await timer.WaitForNextTickAsync(stoppingToken))
            {
                var watch = Stopwatch.StartNew(); await gate.WaitAsync(stoppingToken);
                try
                {
                    if (!ready) break;
                    Engine.Tick(.05); ticks++;
                    if (Engine.EconomicDirty || Engine.State.Time - lastPeriodicSave >= 5) await PersistAsync(stoppingToken);
                    FlushChat(); if (ticks % 2 == 0) foreach (var peer in peers.Values) SendSnapshot(peer);
                }
                finally { gate.Release(); }
                double elapsed = watch.Elapsed.TotalMilliseconds;
                lock (tickDurations)
                {
                    tickDurations.Enqueue(elapsed); if (tickDurations.Count > 1200) tickDurations.Dequeue(); if (elapsed > 50) overruns++;
                }
                if (DateTimeOffset.UtcNow >= nextSessionCheck)
                {
                    nextSessionCheck = DateTimeOffset.UtcNow.AddSeconds(30);
                    foreach (var peer in peers.Values) if (!await accounts.IsSessionValidAsync(peer.Session, stoppingToken)) peer.Abort();
                }
            }
        }
        catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { }
        catch (Exception error) { FailClosed(error); }
    }
    public object Diagnostics()
    {
        lock (tickDurations)
        {
            var values = tickDurations.Order().ToArray();
            return new { ready, protocol = Wire.Version, online = peers.Count, ticks, overruns, commits,
                tickAverageMs = values.Length == 0 ? 0 : Math.Round(values.Average(), 3),
                tickP95Ms = values.Length == 0 ? 0 : Math.Round(values[Math.Min(values.Length - 1, (int)(values.Length * .95))], 3) };
        }
    }
    public override async Task StopAsync(CancellationToken cancel)
    {
        bool wasReady = ready; ready = false;
        foreach (var peer in peers.Values) peer.Abort();
        await base.StopAsync(cancel); await gate.WaitAsync(cancel);
        try
        {
            if (engine is not null && wasReady)
            {
                foreach (var id in Engine.Active.ToList()) Engine.Disconnect(id);
                await store.SaveAsync(Engine, cancel);
            }
        }
        finally { gate.Release(); await store.DisposeAsync(); }
    }
}
