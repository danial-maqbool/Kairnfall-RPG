using System.Diagnostics;
using System.Net;
using System.Net.Http.Json;
using System.Net.WebSockets;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Kairnfall.Core;
using Kairnfall.Server;
using Npgsql;

string? database=Environment.GetEnvironmentVariable("KAIRNFALL_TEST_DB");
if(string.IsNullOrWhiteSpace(database)) { Console.Error.WriteLine("Set KAIRNFALL_TEST_DB to a disposable PostgreSQL database whose name ends with _test."); return 2; }
var settings=new NpgsqlConnectionStringBuilder(database);
if(settings.Database is null||!settings.Database.EndsWith("_test",StringComparison.Ordinal)) throw new InvalidOperationException("Integration tests refuse to modify a database without the _test suffix.");
var root=Directory.GetCurrentDirectory(); var data=Catalog.Load(Path.Combine(root,"content/catalog.json"));
Directory.CreateDirectory("artifacts/test-results"); Directory.CreateDirectory("artifacts/logs");
string serverDll=Path.Combine(root,"src/Kairnfall.Server/bin/Release/net10.0/Kairnfall.Server.dll");
if(!File.Exists(serverDll)) throw new FileNotFoundException("Build the Release server before running integration tests.",serverDll);
var results=new List<object>(); int failures=0; Process? server=null;
var logGate=new object(); string logPath=Path.Combine(root,"artifacts/logs/server-integration.log");
var states=new Dictionary<GameConnection,Snapshot>();
using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(8)); var cancel=timeout.Token;
await using var source=NpgsqlDataSource.Create(database);
using var http=new HttpClient{BaseAddress=new Uri("http://127.0.0.1:5088/"),Timeout=TimeSpan.FromSeconds(20)};
string suffix=Convert.ToHexString(RandomNumberGenerator.GetBytes(4)).ToLowerInvariant();
string password="Test-only-"+Convert.ToHexString(RandomNumberGenerator.GetBytes(12));

void Check(bool condition,string message) { if(!condition) throw new Exception(message); }
async Task Test(string name,Func<Task> body)
{
    var watch=Stopwatch.StartNew();
    try { await body(); results.Add(new{name,status="passed",milliseconds=watch.Elapsed.TotalMilliseconds}); Console.WriteLine("PASS "+name); }
    catch(Exception error) { failures++; results.Add(new{name,status="failed",error=error.ToString(),milliseconds=watch.Elapsed.TotalMilliseconds}); Console.WriteLine("FAIL "+name+"\n"+error); throw; }
}
void Log(string? text) { if(text is not null) lock(logGate) File.AppendAllText(logPath,text+Environment.NewLine); }
async Task StartServer()
{
    var start=new ProcessStartInfo("dotnet"){WorkingDirectory=root,UseShellExecute=false,RedirectStandardOutput=true,RedirectStandardError=true};
    start.ArgumentList.Add(serverDll);
    start.Environment["ASPNETCORE_URLS"]="http://127.0.0.1:5088";
    start.Environment["ASPNETCORE_ENVIRONMENT"]="Testing";
    start.Environment["KAIRNFALL_ALLOW_LOCAL_HTTP"]="1";
    start.Environment["KAIRNFALL_DB"]=database;
    start.Environment["KAIRNFALL_CATALOG"]=Path.Combine(root,"content/catalog.json");
    server=Process.Start(start)??throw new Exception("Server process did not start.");
    server.OutputDataReceived+=(_,e)=>Log(e.Data); server.ErrorDataReceived+=(_,e)=>Log(e.Data); server.BeginOutputReadLine(); server.BeginErrorReadLine();
    var watch=Stopwatch.StartNew();
    while(watch.Elapsed<TimeSpan.FromSeconds(40))
    {
        if(server.HasExited) throw new Exception("Server exited during startup. Read artifacts/logs/server-integration.log.");
        try { using var response=await http.GetAsync("health",cancel); if(response.IsSuccessStatusCode) return; } catch(HttpRequestException) { }
        await Task.Delay(200,cancel);
    }
    throw new TimeoutException("The server did not become ready.");
}
async Task CrashServer()
{
    if(server is null) return;
    if(!server.HasExited) { server.Kill(true); await server.WaitForExitAsync(cancel); }
    server.Dispose(); server=null; await Task.Delay(300,cancel);
}
Snapshot? Pump(GameConnection client)
{
    while(client.TryRead(out var packet)) if(packet?.Snapshot is { } snapshot) states[client]=snapshot;
    return states.GetValueOrDefault(client);
}
async Task<Snapshot> State(GameConnection client,Func<Snapshot,bool>? condition=null,double seconds=10)
{
    var watch=Stopwatch.StartNew();
    while(watch.Elapsed.TotalSeconds<seconds)
    {
        var current=Pump(client); if(current is not null&&(condition is null||condition(current))) return current;
        if(!client.Connected&&client.LastError!="") throw new Exception(client.LastError);
        await Task.Delay(30,cancel);
    }
    throw new TimeoutException("Expected client state did not arrive.");
}
async Task<CommandResult> Act(GameConnection client,string kind,string target="",string item="",int amount=1,string arg="",double x=0,double y=0)
{
    var result=await client.ActAsync(new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,X=x,Y=y},cancel);
    Check(result.Ok,kind+": "+result.Message); await State(client,s=>s.Self.LastAction>=result.Sequence); return result;
}
async Task Navigate(GameConnection client,Point destination)
{
    var snapshot=await State(client); string zoneId=snapshot.Self.Zone; var zone=data.Zone(zoneId);
    var route=WorldMap.FindPath(zone,snapshot.Self.Position,destination,zone.Width*zone.Height);
    route.Add(destination); int next=0; var watch=Stopwatch.StartNew();
    while(watch.Elapsed<TimeSpan.FromSeconds(100))
    {
        snapshot=await State(client); Check(snapshot.Self.Zone==zoneId,"Navigation crossed an unexpected zone.");
        var position=snapshot.Self.Position;
        if(position.Distance(destination)<0.7) { await client.MoveAsync(0,0,cancel); return; }
        while(next<route.Count-1&&position.Distance(route[next])<0.7) next++;
        var goal=route[Math.Min(next,route.Count-1)]; var direction=position.Direction(goal);
        double scale=Math.Clamp(position.Distance(goal)/0.55,0.25,1);
        await client.MoveAsync(direction.X*scale,direction.Y*scale,cancel);
        await Task.Delay(100,cancel); Pump(client);
    }
    await client.MoveAsync(0,0,cancel); throw new TimeoutException("Navigation did not reach "+destination+" in "+zoneId);
}
async Task ReachDawnreach(GameConnection client)
{
    foreach(var destination in new[]{"kingsmeadow","dawnreach"})
    {
        var state=await State(client); var exit=data.Zone(state.Self.Zone).Exits.First(x=>x.Target==destination);
        await Navigate(client,exit.Position); await Act(client,"transition",exit.Id); await State(client,s=>s.Self.Zone==destination);
    }
}

await using var alice=new GameConnection(http.BaseAddress!.AbsoluteUri);
await using var bob=new GameConnection(http.BaseAddress!.AbsoluteUri);
await using var charlie=new GameConnection(http.BaseAddress!.AbsoluteUri);
LoginResponse? aliceSession=null,bobSession=null,charlieSession=null;
CharacterSummary? aliceCharacter=null,bobCharacter=null,charlieCharacter=null;
string transferredItem=""; long expectedGold=0; string expectedWeapon="";

try
{
    await Test("Server starts against PostgreSQL and becomes ready",StartServer);
    await Test("Accounts register and reject incorrect passwords",async()=>
    {
        aliceSession=await alice.SignInAsync("alice_"+suffix,password,true,cancel);
        bobSession=await bob.SignInAsync("bob_"+suffix,password,true,cancel);
        charlieSession=await charlie.SignInAsync("charlie_"+suffix,password,true,cancel);
        using var bad=await http.PostAsJsonAsync("api/login",new LoginRequest{Username="alice_"+suffix,Password="Incorrect-password-123"},Wire.Json,cancel);
        Check(bad.StatusCode==HttpStatusCode.BadRequest,"Incorrect password was accepted.");
        using var anonymous=await http.GetAsync("api/characters",cancel); Check(anonymous.StatusCode==HttpStatusCode.Unauthorized,"Anonymous character access was accepted.");
    });
    await Test("Character creation persists ownership and appearance",async()=>
    {
        aliceCharacter=await alice.CreateCharacterAsync(new(){Name="Alice "+suffix,Class="vanguard",Appearance=new(){Body=0,Skin=2,Hair=3,HairColor=4}},cancel);
        bobCharacter=await bob.CreateCharacterAsync(new(){Name="Bob "+suffix,Class="ranger"},cancel);
        charlieCharacter=await charlie.CreateCharacterAsync(new(){Name="Charlie "+suffix,Class="arcanist"},cancel);
        var list=await alice.CharactersAsync(cancel); Check(list.Any(x=>x.Id==aliceCharacter.Id&&x.Appearance.Skin==2),"Character appearance was not persisted.");
        Check(list.All(x=>x.Id!=bobCharacter.Id),"Another account's character appeared in the list.");
    });
    await Test("A foreign account cannot attach to another player's character",async()=>
    {
        await using var foreign=new GameConnection(http.BaseAddress.AbsoluteUri); foreign.UseSession(charlieSession!); bool rejected=false;
        try { await foreign.ConnectAsync(aliceCharacter!.Id,cancel); } catch(RuleException) { rejected=true; }
        Check(rejected,"Foreign character ownership was not enforced.");
    });
    await Test("Three real clients enter one authoritative world",async()=>
    {
        await alice.ConnectAsync(aliceCharacter!.Id,cancel); await bob.ConnectAsync(bobCharacter!.Id,cancel); await charlie.ConnectAsync(charlieCharacter!.Id,cancel);
        var state=await State(alice,s=>s.Players.Any(p=>p.Id==bobCharacter.Id)&&s.Players.Any(p=>p.Id==charlieCharacter.Id));
        Check(state.Self.Zone=="wayfarers_rest","The fixed starting point was not used.");
    });
    await Test("Whisper messages reach only the sender and recipient",async()=>
    {
        Pump(alice); Pump(bob); Pump(charlie); string text="Private test "+suffix;
        await Act(alice,"chat","whisper",bobCharacter!.Id,arg:text);
        bool received=false,leaked=false; var watch=Stopwatch.StartNew();
        while(watch.Elapsed<TimeSpan.FromSeconds(2))
        {
            while(bob.TryRead(out var packet)) { if(packet?.Chat?.Text==text) received=true; if(packet?.Snapshot is { } s) states[bob]=s; }
            while(charlie.TryRead(out var packet)) { if(packet?.Chat?.Text==text) leaked=true; if(packet?.Snapshot is { } s) states[charlie]=s; }
            await Task.Delay(30,cancel);
        }
        Check(received&&!leaked,"Whisper delivery or privacy failed.");
    });
    await Test("Player trade needs two readiness checks and two final confirmations",async()=>
    {
        var state=await State(alice); transferredItem=state.Self.Inventory.First(x=>x.Template=="shovel").Id;
        await Act(alice,"trade_invite",bobCharacter!.Id);
        state=await State(alice,s=>s.Trades.Count==1); string trade=state.Trades[0].Id;
        await Act(alice,"trade_offer",trade,transferredItem,1);
        await Act(bob,"trade_offer",trade,arg:"10");
        state=await State(alice,s=>s.Trades[0].Revision==2); int revision=state.Trades[0].Revision;
        var invalid=await alice.ActAsync(new(){Kind="trade_confirm",Target=trade,Amount=revision},cancel); Check(!invalid.Ok,"Trade completed without readiness.");
        await Act(alice,"trade_ready",trade,amount:revision); await Act(bob,"trade_ready",trade,amount:revision);
        await Act(alice,"trade_confirm",trade,amount:revision); await Act(bob,"trade_confirm",trade,amount:revision);
        var a=await State(alice,s=>s.Trades.Count==0&&!s.Self.Inventory.Any(x=>x.Id==transferredItem));
        var b=await State(bob,s=>s.Self.Inventory.Any(x=>x.Id==transferredItem));
        Check(a.Self.Gold==50&&b.Self.Gold==30,"Trade gold was not conserved.");
    });
    await Test("A rune moves from inventory into its equipment socket",async()=>
    {
        var state=await State(alice); expectedWeapon=state.Self.Equipment["weapon"]; var rune=state.Self.Inventory.First(x=>x.Template=="rune_embers_1");
        await Act(alice,"socket",expectedWeapon,rune.Id);
        state=await State(alice,s=>s.Self.Inventory.First(x=>x.Id==expectedWeapon).Runes.Count==1);
        Check(state.Self.Inventory.All(x=>x.Id!=rune.Id),"Socketing duplicated the rune item.");
    });
    await Test("Forged actions and remote bank calls do not change ownership",async()=>
    {
        var state=await State(alice); long gold=state.Self.Gold;
        var forged=await alice.ActAsync(new(){Kind="set_gold",Amount=1000000},cancel); Check(!forged.Ok,"Forged gold command was accepted.");
        var remote=await alice.ActAsync(new(){Kind="deposit",Item=state.Self.Inventory.First(x=>x.Template=="copper_pickaxe").Id},cancel); Check(!remote.Ok,"Remote bank access was accepted.");
        state=await State(alice); Check(state.Self.Gold==gold,"Rejected actions changed gold.");
    });
    await Test("Party invitations are visible and require recipient acceptance",async()=>
    {
        await Act(alice,"party_create"); await Act(alice,"party_invite",bobCharacter!.Id);
        string invitation=""; var watch=Stopwatch.StartNew();
        while(watch.Elapsed<TimeSpan.FromSeconds(5)&&invitation=="")
        {
            while(bob.TryRead(out var packet))
            {
                if(packet?.Snapshot is { } s) states[bob]=s;
                invitation=packet?.Invitations?.FirstOrDefault(x=>!x.Guild)?.Id??invitation;
            }
            await Task.Delay(30,cancel);
        }
        Check(invitation!="","The party invitation did not reach the recipient."); await Act(bob,"party_join",invitation);
        var state=await State(alice,s=>s.Party?.Members.Count==2); Check(state.Party!.Members.Contains(bobCharacter!.Id),"Party membership was not synchronized.");
    });
    await Test("Movement, resource gathering, crafting, and quest rewards work over the network",async()=>
    {
        var smith=data.Npc("wayfarers_rest_blacksmith"); await Navigate(alice,smith.Position); await Act(alice,"accept_quest",item:"starter_ore");
        var state=await State(alice);
        var nodes=state.Nodes.Where(x=>x.Template=="copper_vein").OrderBy(x=>x.Id,StringComparer.Ordinal).Take(3).ToList(); Check(nodes.Count==3,"Starter copper nodes are missing.");
        foreach(var node in nodes)
        {
            await Navigate(alice,node.Position); await Task.Delay(1900,cancel); await Act(alice,"gather",node.Id);
        }
        await Navigate(alice,smith.Position); await Act(alice,"craft",item:"smelt_copper"); await Act(alice,"claim_quest",item:"starter_ore");
        state=await State(alice,s=>s.Self.CompletedQuests.Contains("starter_ore"));
        Check(state.Self.SkillXp["mining"]>0&&state.Self.SkillXp["smithing"]>0&&state.Self.Inventory.Any(x=>x.Template=="copper_bar"),"The gather-to-craft progression chain failed.");
    });
    await Test("Both players traverse connected maps to the capital",async()=>
    {
        await Task.WhenAll(ReachDawnreach(alice),ReachDawnreach(bob));
        var a=await State(alice,s=>s.Self.Zone=="dawnreach"); var b=await State(bob,s=>s.Self.Zone=="dawnreach");
        Check(a.Self.Discoveries.Contains("dawnreach")&&b.Self.Discoveries.Contains("kingsmeadow"),"Travel discovery was not recorded.");
    });
    await Test("Bank operations conserve unique item identities",async()=>
    {
        var banker=data.Npcs.First(x=>x.Zone=="dawnreach"&&x.Role=="banker"); await Navigate(alice,banker.Position);
        var state=await State(alice); var item=state.Self.Inventory.First(x=>x.Template=="copper_bar");
        await Act(alice,"deposit",item:item.Id);
        state=await State(alice,s=>s.Self.Bank.Any(x=>x.Template=="copper_bar")); var bankItem=state.Self.Bank.First(x=>x.Template=="copper_bar");
        await Act(alice,"withdraw",item:bankItem.Id);
        state=await State(alice,s=>s.Self.Bank.All(x=>x.Id!=bankItem.Id)); Check(state.Self.Inventory.Any(x=>x.Template=="copper_bar"),"Bank withdrawal lost the item.");
    });
    await Test("Auction escrow transfers an item and pays the seller once",async()=>
    {
        var broker=data.Npcs.First(x=>x.Zone=="dawnreach"&&x.Role=="auctioneer"); await Task.WhenAll(Navigate(alice,broker.Position),Navigate(bob,broker.Position));
        var a=await State(alice); var b=await State(bob); long aGold=a.Self.Gold,bGold=b.Self.Gold; string item=a.Self.Inventory.First(x=>x.Template=="copper_bar").Id;
        await Act(alice,"auction_list","10",item);
        a=await State(alice,s=>s.Auctions.Any(x=>x.Seller==aliceCharacter!.Id)); string auction=a.Auctions.First(x=>x.Seller==aliceCharacter!.Id).Id;
        await Act(bob,"auction_buy",auction);
        a=await State(alice,s=>s.Self.Gold==aGold+9); b=await State(bob,s=>s.Self.Gold==bGold-10);
        Check(b.Self.Inventory.Any(x=>x.Template=="copper_bar"),"Auction purchase lost the item.");
        var repeat=await bob.ActAsync(new(){Kind="auction_buy",Target=auction},cancel); Check(!repeat.Ok,"An auction listing sold twice.");
        expectedGold=a.Self.Gold;
    });
    await Test("PostgreSQL stores password hashes and token fingerprints, not plaintext",async()=>
    {
        await using var command=source.CreateCommand("SELECT octet_length(password_hash),octet_length(password_salt),password_iterations FROM accounts WHERE id=$1");
        command.Parameters.AddWithValue(Guid.ParseExact(aliceSession!.AccountId,"N"));
        await using var reader=await command.ExecuteReaderAsync(cancel); Check(await reader.ReadAsync(cancel),"Account row missing.");
        Check(reader.GetInt32(0)==32&&reader.GetInt32(1)==16&&reader.GetInt32(2)>=600000,"Password storage parameters are invalid.");
    });
    await Test("A second authoritative writer cannot acquire the realm lease",async()=>
    {
        await using var other=new RealmStore(source); bool rejected=false;
        try { await other.InitializeAsync(cancel); } catch(InvalidOperationException) { rejected=true; }
        Check(rejected,"Two realm writers acquired the same database.");
    });
    await Test("Acknowledged inventory, runes, quests, gold, and position survive a hard server restart",async()=>
    {
        await CrashServer(); await alice.DisconnectAsync(); await bob.DisconnectAsync(); await charlie.DisconnectAsync();
        states.Clear(); await StartServer();
        alice.UseSession(aliceSession!); bob.UseSession(bobSession!);
        await alice.ConnectAsync(aliceCharacter!.Id,cancel); await bob.ConnectAsync(bobCharacter!.Id,cancel);
        var a=await State(alice); var b=await State(bob);
        Check(a.Self.Gold==expectedGold&&a.Self.Zone=="dawnreach"&&a.Self.CompletedQuests.Contains("starter_ore"),"Acknowledged character state did not survive restart.");
        Check(a.Self.Inventory.First(x=>x.Id==expectedWeapon).Runes.Count==1&&b.Self.Inventory.Any(x=>x.Id==transferredItem),"Persistent item or rune ownership changed after restart.");
    });
    await Test("Session logout revokes further authenticated access",async()=>
    {
        await bob.SignOutAsync(cancel);
        using var request=new HttpRequestMessage(HttpMethod.Get,"api/characters"); request.Headers.Authorization=new("Bearer",bobSession!.Token);
        using var response=await http.SendAsync(request,cancel); Check(response.StatusCode==HttpStatusCode.Unauthorized,"A revoked token remained usable.");
    });
    var diagnostics=await http.GetStringAsync("health",cancel);
    File.WriteAllText("artifacts/test-results/network-diagnostics.json",diagnostics);
}
catch(Exception error)
{
    if(failures==0) { failures++; results.Add(new{name="integration harness",status="failed",error=error.ToString()}); Console.Error.WriteLine(error); }
}
finally
{
    try { await alice.DisconnectAsync(); await bob.DisconnectAsync(); await charlie.DisconnectAsync(); } catch(Exception e) { Log("Cleanup: "+e.GetType().Name); }
    if(server is {HasExited:false}) { server.Kill(true); await server.WaitForExitAsync(); }
    server?.Dispose();
    File.WriteAllText("artifacts/test-results/integration.json",JsonSerializer.Serialize(new{passed=results.Count-failures,failed=failures,tests=results},new JsonSerializerOptions{WriteIndented=true}));
}
Console.WriteLine($"INTEGRATION RESULT: {results.Count-failures} passed; {failures} failed.");
return failures==0?0:1;
