using System.Text.Json;
using Kairnfall.Core;

if(args.Length<3) throw new ArgumentException("Usage: <create|reconnect> <server-url> <state-file>");
string mode=args[0],address=args[1],statePath=args[2];
if(!Uri.TryCreate(address,UriKind.Absolute,out var uri)||!uri.IsLoopback) throw new InvalidOperationException("Package probe is restricted to loopback.");
using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(2)); var cancel=timeout.Token;

async Task<Snapshot> Snapshot(GameConnection connection,double seconds=15)
{
    var until=DateTime.UtcNow.AddSeconds(seconds);
    while(DateTime.UtcNow<until)
    {
        while(connection.TryRead(out var packet)) if(packet?.Snapshot is { } snapshot) return snapshot;
        if(!connection.Connected&&connection.LastError!="") throw new InvalidOperationException(connection.LastError);
        await Task.Delay(50,cancel);
    }
    throw new TimeoutException("Snapshot did not arrive.");
}

if(mode=="create")
{
    string suffix=Guid.NewGuid().ToString("N")[..10]; string username="package_"+suffix,password="Package-only-"+Guid.NewGuid().ToString("N");
    await using var connection=new GameConnection(address);
    await connection.SignInAsync(username,password,true,cancel);
    var character=await connection.CreateCharacterAsync(new CharacterRequest{Name="Package "+suffix,Class="vanguard",Appearance=new()},cancel);
    await connection.ConnectAsync(character.Id,cancel); var initial=await Snapshot(connection);
    for(int i=0;i<15;i++) { await connection.MoveAsync(1,0,cancel); await Task.Delay(100,cancel); }
    await connection.MoveAsync(0,0,cancel); await Task.Delay(400,cancel);
    var chat=await connection.ActAsync(new GameCommand{Kind="chat",Target="say",Arg="package restart persistence"},cancel);
    if(!chat.Ok) throw new InvalidOperationException("Persistence command failed: "+chat.Message);
    var moved=await Snapshot(connection);
    if(moved.Self.Position.Distance(initial.Self.Position)<1) throw new InvalidOperationException("Packaged probe character did not move before restart.");
    var state=new ProbeState(username,password,character.Id,moved.Self.Zone,moved.Self.Position.X,moved.Self.Position.Y,moved.Self.Inventory.Sum(item=>item.Quantity));
    Directory.CreateDirectory(Path.GetDirectoryName(statePath)??"."); File.WriteAllText(statePath,JsonSerializer.Serialize(state,new JsonSerializerOptions{WriteIndented=true}));
    Console.WriteLine($"PACKAGE_PROBE_CREATE: character={character.Id} zone={moved.Self.Zone} inventory={state.InventoryCount}");
}
else if(mode=="reconnect")
{
    var state=JsonSerializer.Deserialize<ProbeState>(File.ReadAllText(statePath))??throw new InvalidDataException("Package probe state is empty.");
    await using var connection=new GameConnection(address);
    await connection.SignInAsync(state.Username,state.Password,false,cancel);
    var characters=await connection.CharactersAsync(cancel);
    if(!characters.Any(character=>character.Id==state.CharacterId)) throw new InvalidOperationException("Persisted character is missing after packaged server restart.");
    await connection.ConnectAsync(state.CharacterId,cancel); var snapshot=await Snapshot(connection);
    if(snapshot.Self.Zone!=state.Zone) throw new InvalidOperationException("Persisted zone changed after restart.");
    if(snapshot.Self.Position.Distance(new Point(state.X,state.Y))>.75) throw new InvalidOperationException("Persisted position changed after restart.");
    if(snapshot.Self.Inventory.Sum(item=>item.Quantity)!=state.InventoryCount) throw new InvalidOperationException("Persisted inventory changed after restart.");
    Console.WriteLine($"PACKAGE_PROBE_RECONNECT: character={state.CharacterId} zone={snapshot.Self.Zone} inventory={state.InventoryCount}");
}
else throw new ArgumentException("Unknown package probe mode: "+mode);

internal sealed record ProbeState(string Username,string Password,string CharacterId,string Zone,double X,double Y,int InventoryCount);
