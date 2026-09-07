using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net.WebSockets;
using System.Text.Json;
using System.Threading.Channels;
using Kairnfall.Core;

namespace Kairnfall.Server;

public sealed record CharacterRequest(string Name,string Class,Appearance Appearance);
public sealed record CharacterSummary(string Id,string Name,string Class,int Level,string Zone,Appearance Appearance);
public sealed record ClientHello(string Kind,int Version,string Token,string CharacterId,string CatalogHash);

public sealed class RealmHub : BackgroundService
{
    private readonly Catalog data;
    private readonly RealmStore store;
    private readonly AccountService accounts;
    private readonly ILogger<RealmHub> logger;
    private readonly IHostApplicationLifetime lifetime;
    private readonly SemaphoreSlim gate=new(1,1);
    private readonly ConcurrentDictionary<string,Peer> peers=new(StringComparer.Ordinal);
    private RealmEngine engine;
    private long ticks;
    private double maximumTickMilliseconds;
    private int slowTicks;
    public string CatalogHash { get; }
    public bool Ready { get; private set; }

    public RealmHub(Catalog data,RealmStore store,AccountService accounts,ILogger<RealmHub> logger,
                    IHostApplicationLifetime lifetime,string catalogHash)
    {
        this.data=data; this.store=store; this.accounts=accounts; this.logger=logger;
        this.lifetime=lifetime; CatalogHash=catalogHash; engine=new RealmEngine(data);
    }

    public override async Task StartAsync(CancellationToken cancellationToken)
    {
        await store.InitializeAsync(cancellationToken);
        var saved=await store.LoadAsync(cancellationToken);
        if(saved is not null) engine=new RealmEngine(data,saved.State){Loot=saved.Loot};
        var errors=Items.Validate(engine.State,data);
        if(errors.Count>0) throw new InvalidDataException("Saved inventory validation failed: "+string.Join("; ",errors));
        // Connections are not durable. Cancel interrupted offers before accepting
        // new sessions; offered items remain with their owners until settlement.
        engine.State.Trades.Clear();
        await store.SaveAsync(engine,cancellationToken);
        Ready=true;
        await base.StartAsync(cancellationToken);
        logger.LogInformation("Realm loaded at revision {Revision}. Protocol {Protocol}.",store.Revision,Wire.Version);
    }

    public async Task<T> ReadAsync<T>(Func<RealmEngine,T> read,CancellationToken cancellationToken)
    {
        await gate.WaitAsync(cancellationToken);
        try { EnsureReady(); return read(engine); }
        finally { gate.Release(); }
    }

    public async Task<IReadOnlyList<CharacterSummary>> CharactersAsync(string account,CancellationToken cancellationToken)
        =>await ReadAsync(e=>(IReadOnlyList<CharacterSummary>)e.State.Characters.Values.Where(x=>x.Account==account)
            .Select(x=>new CharacterSummary(x.Id,x.Name,x.Class,Progression.PlayerLevel(x),x.Zone,Wire.Copy(x.Appearance))).ToArray(),cancellationToken);

    public async Task<CharacterSummary> CreateCharacterAsync(string account,CharacterRequest input,CancellationToken cancellationToken)
    {
        if(input is null||input.Appearance is null||input.Name is null||input.Class is null)
            throw new RuleException("Character fields are required.");
        await gate.WaitAsync(cancellationToken);
        try
        {
            EnsureReady();
            var player=engine.CreateCharacter(account,input.Name,input.Class,input.Appearance);
            await PersistOrStopAsync();
            return new(player.Id,player.Name,player.Class,Progression.PlayerLevel(player),player.Zone,Wire.Copy(player.Appearance));
        }
        finally { gate.Release(); }
    }

    private void EnsureReady()
    {
        if(!Ready) throw new InvalidOperationException("The realm is not ready. Reconnect after the server restarts.");
    }

    private async Task PersistOrStopAsync()
    {
        try { await store.SaveAsync(engine,lifetime.ApplicationStopping); }
        catch(Exception error)
        {
            Ready=false;
            foreach(var peer in peers.Values) peer.Abort();
            logger.LogCritical(error,"Persistence failed. The realm is stopping without acknowledging the action.");
            lifetime.StopApplication();
            throw;
        }
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var timer=new PeriodicTimer(TimeSpan.FromMilliseconds(50));
        try
        {
            while(await timer.WaitForNextTickAsync(stoppingToken))
            {
                var watch=Stopwatch.StartNew();
                await gate.WaitAsync(stoppingToken);
                try
                {
                    if(!Ready) break;
                    engine.Tick(0.05); ticks++;
                    if(ticks%100==0) await PersistOrStopAsync();
                    if(ticks%4==0)
                    {
                        foreach(var peer in peers.Values)
                        {
                            if(accounts.Authenticate(peer.Token) is null) { peer.Abort(); continue; }
                            SendSnapshot(peer);
                        }
                    }
                    FlushChat();
                }
                finally { gate.Release(); }
                double elapsed=watch.Elapsed.TotalMilliseconds;
                maximumTickMilliseconds=Math.Max(maximumTickMilliseconds,elapsed);
                if(elapsed>50) slowTicks++;
            }
        }
        catch(OperationCanceledException) when(stoppingToken.IsCancellationRequested) { }
        catch(Exception error)
        {
            Ready=false;
            logger.LogCritical(error,"Authoritative simulation stopped. No further commands will be accepted.");
            foreach(var peer in peers.Values) peer.Abort();
            lifetime.StopApplication();
        }
    }

    public async Task<object> StatusAsync(CancellationToken cancellationToken)
        =>await ReadAsync(e=>(object)new{ready=Ready,protocol=Wire.Version,catalogHash=CatalogHash,
             players=peers.Count,revision=store.Revision,time=e.State.Time,ticks,
             maximumTickMilliseconds,slowTicks,targetTickHz=20},cancellationToken);

    private void SendSnapshot(Peer peer)
    {
        if(!engine.State.Characters.ContainsKey(peer.Character)) return;
        var invites=engine.State.Parties.Values.Where(g=>g.Invites.Contains(peer.Character))
            .Select(g=>new{id=g.Id,name=g.Name,kind="party"})
            .Concat(engine.State.Guilds.Values.Where(g=>g.Invites.Contains(peer.Character)).Select(g=>new{id=g.Id,name=g.Name,kind="guild"})).ToArray();
        peer.Send(new{kind="snapshot",snapshot=engine.Snapshot(peer.Character),loot=engine.VisibleLoot(peer.Character),invites,catalogHash=CatalogHash});
    }

    private void FlushChat()
    {
        foreach(var message in engine.OutgoingChat)
            foreach(var peer in peers.Values)
                if(engine.CanReceiveChat(peer.Character,message)) peer.Send(new{kind="chat",chat=message});
        engine.OutgoingChat.Clear();
    }

    public async Task ServeSocketAsync(HttpContext context)
    {
        using var socket=await context.WebSockets.AcceptWebSocketAsync();
        using var lifetimeToken=CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted,lifetime.ApplicationStopping);
        Peer? peer=null;
        try
        {
            byte[]? first;
            using(var handshake=CancellationTokenSource.CreateLinkedTokenSource(lifetimeToken.Token))
            {
                handshake.CancelAfter(TimeSpan.FromSeconds(10));
                first=await ReceiveMessageAsync(socket,handshake.Token);
            }
            if(first is null) return;
            var hello=JsonSerializer.Deserialize<ClientHello>(first,Wire.Json);
            if(hello is null||hello.Kind!="hello"||hello.Version!=Wire.Version)
                throw new RuleException("The client protocol does not match this server.");
            var session=accounts.Authenticate(hello.Token)??throw new RuleException("Your session expired. Log in again.");
            if(hello.CatalogHash!=CatalogHash) throw new RuleException("Client and server content differ. Use builds from the same revision.");
            await gate.WaitAsync(lifetimeToken.Token);
            try
            {
                EnsureReady();
                if(hello.CharacterId is null||!engine.State.Characters.TryGetValue(hello.CharacterId,out var player)||player.Account!=session.Account)
                    throw new RuleException("This character does not belong to your account.");
                if(peers.Values.Any(p=>p.Account==session.Account))
                    throw new RuleException("This account already has a character connected.");
                peer=new Peer(socket,player.Id,session.Account,hello.Token,lifetimeToken);
                if(!peers.TryAdd(player.Id,peer)) throw new RuleException("This character is already connected.");
                engine.Active.Add(player.Id);
                SendSnapshot(peer);
            }
            finally { gate.Release(); }
            Task sending=peer.SendLoopAsync();
            try
            {
                while(socket.State==WebSocketState.Open&&!lifetimeToken.IsCancellationRequested)
                {
                    byte[]? bytes=await ReceiveMessageAsync(socket,lifetimeToken.Token);
                    if(bytes is null) break;
                    if(!peer.AcceptMessage()) throw new RuleException("Command rate exceeded. Reconnect before continuing.");
                    var command=JsonSerializer.Deserialize<GameCommand>(bytes,Wire.Json);
                    if(command is null||command.Kind is null||command.Target is null||command.Item is null||command.Arg is null||command.RequestId is null)
                        throw new RuleException("A command contains missing fields.");
                    if(command.Kind=="ping") { peer.Send(new{kind="pong"}); continue; }
                    await gate.WaitAsync(lifetimeToken.Token);
                    try
                    {
                        EnsureReady();
                        if(accounts.Authenticate(peer.Token) is null) throw new RuleException("Your session expired. Log in again.");
                        var result=engine.Execute(peer.Character,command);
                        if(command.Kind!="move")
                        {
                            if(result.Ok) await PersistOrStopAsync();
                            peer.Send(new{kind="result",result});
                            SendSnapshot(peer);
                            FlushChat();
                        }
                        else if(!result.Ok) peer.Send(new{kind="result",result});
                    }
                    finally { gate.Release(); }
                }
            }
            finally
            {
                peer.Complete();
                try { await sending.WaitAsync(TimeSpan.FromSeconds(2)); }
                catch(Exception error) when(error is OperationCanceledException or WebSocketException or TimeoutException) { }
            }
        }
        catch(Exception error) when(error is RuleException or JsonException or InvalidDataException)
        {
            if(peer is null&&socket.State==WebSocketState.Open)
            {
                byte[] payload=JsonSerializer.SerializeToUtf8Bytes(new{kind="error",error=error is JsonException?"Invalid JSON message.":error.Message},Wire.Json);
                try { await socket.SendAsync(payload.AsMemory(),WebSocketMessageType.Text,true,CancellationToken.None); }
                catch(WebSocketException) { }
            }
            logger.LogInformation("A client connection was rejected: {Reason}",error is JsonException?"Invalid JSON":error.Message);
        }
        catch(Exception error) when(error is OperationCanceledException or WebSocketException or ChannelClosedException) { }
        finally
        {
            if(peer is not null)
            {
                await gate.WaitAsync(CancellationToken.None);
                try
                {
                    peers.TryRemove(peer.Character,out _);
                    engine.Disconnect(peer.Character);
                    if(Ready) await PersistOrStopAsync();
                }
                catch(Exception error) { logger.LogError(error,"Could not persist a disconnected character."); }
                finally { gate.Release(); }
            }
            lifetimeToken.Cancel();
            if(socket.State is WebSocketState.Open or WebSocketState.CloseReceived)
            {
                using var closeTimeout=new CancellationTokenSource(TimeSpan.FromSeconds(2));
                try { await socket.CloseAsync(WebSocketCloseStatus.NormalClosure,"Session ended.",closeTimeout.Token); }
                catch(Exception error) when(error is WebSocketException or OperationCanceledException) { }
            }
        }
    }

    private static async Task<byte[]?> ReceiveMessageAsync(WebSocket socket,CancellationToken cancellationToken)
    {
        byte[] buffer=new byte[4096];
        using var message=new MemoryStream();
        while(true)
        {
            var result=await socket.ReceiveAsync(buffer.AsMemory(),cancellationToken);
            if(result.MessageType==WebSocketMessageType.Close) return null;
            if(result.MessageType!=WebSocketMessageType.Text) throw new InvalidDataException("Only text protocol messages are accepted.");
            if(message.Length+result.Count>Wire.MaximumMessageBytes) throw new InvalidDataException("The command exceeds the message-size limit.");
            message.Write(buffer,0,result.Count);
            if(result.EndOfMessage) return message.ToArray();
        }
    }

    public override async Task StopAsync(CancellationToken cancellationToken)
    {
        foreach(var peer in peers.Values) peer.Abort();
        await base.StopAsync(cancellationToken);
        await gate.WaitAsync(CancellationToken.None);
        try
        {
            if(Ready)
            {
                using var timeout=new CancellationTokenSource(TimeSpan.FromSeconds(10));
                await store.SaveAsync(engine,timeout.Token);
            }
            Ready=false;
        }
        finally { gate.Release(); }
    }

    private sealed class Peer
    {
        private readonly WebSocket socket;
        private readonly CancellationTokenSource lifetime;
        private readonly Channel<byte[]> outgoing=Channel.CreateBounded<byte[]>(new BoundedChannelOptions(64)
            {SingleReader=true,SingleWriter=false,FullMode=BoundedChannelFullMode.Wait});
        private long window=Stopwatch.GetTimestamp();
        private int messages;
        public string Character { get; }
        public string Account { get; }
        public string Token { get; }
        public Peer(WebSocket socket,string character,string account,string token,CancellationTokenSource lifetime)
        { this.socket=socket; Character=character; Account=account; Token=token; this.lifetime=lifetime; }
        public bool AcceptMessage()
        {
            long now=Stopwatch.GetTimestamp();
            if(Stopwatch.GetElapsedTime(window,now).TotalSeconds>=1) { window=now; messages=0; }
            return ++messages<=60;
        }
        public void Send(object message)
        {
            byte[] bytes=JsonSerializer.SerializeToUtf8Bytes(message,Wire.Json);
            if(!outgoing.Writer.TryWrite(bytes)) Abort();
        }
        public async Task SendLoopAsync()
        {
            await foreach(var bytes in outgoing.Reader.ReadAllAsync(lifetime.Token))
                await socket.SendAsync(bytes.AsMemory(),WebSocketMessageType.Text,true,lifetime.Token);
        }
        public void Complete()=>outgoing.Writer.TryComplete();
        public void Abort() { outgoing.Writer.TryComplete(); lifetime.Cancel(); socket.Abort(); }
    }
}
