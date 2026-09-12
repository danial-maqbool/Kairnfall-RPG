using System.Diagnostics;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text.Json;
using Kairnfall.Core;

string address=args.Length>0?args[0]:"http://127.0.0.1:5090";
int stageSeconds=args.Length>1?int.Parse(args[1]):20;
string output=args.Length>2?args[2]:"artifacts/load/load-report.json";
if(!Uri.TryCreate(address,UriKind.Absolute,out var endpoint)||!endpoint.IsLoopback) throw new InvalidOperationException("Load acceptance is restricted to loopback.");
int[] stages=[2,10,25,50];
string suffix=Convert.ToHexString(RandomNumberGenerator.GetBytes(4)).ToLowerInvariant();
string password="Load-only-"+Convert.ToHexString(RandomNumberGenerator.GetBytes(10));
using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(14));
var cancel=timeout.Token;
using var health=new HttpClient{BaseAddress=new Uri(address.TrimEnd('/')+"/"),Timeout=TimeSpan.FromSeconds(10)};
var clients=new List<GameConnection>();
var characters=new List<CharacterSummary>();
var lastSnapshot=new Dictionary<GameConnection,double>();
var intervals=new List<double>();
var snapshotSizes=new List<int>();
var stageReports=new List<object>();
var total=Stopwatch.StartNew();

static double Percentile(IEnumerable<double> source,double quantile)
{
    var sorted=source.Order().ToArray();
    return sorted.Length==0?double.PositiveInfinity:sorted[Math.Min(sorted.Length-1,Math.Max(0,(int)Math.Ceiling(sorted.Length*quantile)-1))];
}
static double PercentileInt(IEnumerable<int> source,double quantile)=>Percentile(source.Select(x=>(double)x),quantile);
async Task<JsonElement> Diagnostics()
{
    using var response=await health.GetAsync("health",cancel); response.EnsureSuccessStatusCode();
    return await response.Content.ReadFromJsonAsync<JsonElement>(cancellationToken:cancel);
}
void Drain(int active,List<double> localIntervals,List<int> localSizes,ref int snapshots)
{
    double now=total.Elapsed.TotalMilliseconds;
    for(int i=0;i<active;i++)
    {
        var client=clients[i];
        while(client.TryRead(out var packet))
        {
            if(packet?.Snapshot is null) continue;
            double previous=lastSnapshot.GetValueOrDefault(client,now);
            double interval=now-previous;
            if(interval>0) { intervals.Add(interval); localIntervals.Add(interval); }
            int bytes=JsonSerializer.SerializeToUtf8Bytes(packet,Wire.Json).Length;
            snapshotSizes.Add(bytes); localSizes.Add(bytes);
            lastSnapshot[client]=now; snapshots++;
        }
        if(!client.Connected||client.LastError!="") throw new InvalidOperationException($"Client {i} disconnected under load: {client.LastError}");
    }
}
async Task<double> SendChat(int index,int target)
{
    var watch=Stopwatch.StartNew();
    var result=await clients[index].ActAsync(new GameCommand{Kind="chat",Target="local",Arg=$"LOAD {target:00} · {index:00} · {suffix}"},cancel);
    watch.Stop();
    if(!result.Ok) throw new InvalidOperationException($"Client {index} chat rejected at {target} clients: {result.Message}");
    return watch.Elapsed.TotalMilliseconds;
}
async Task<double> Reconnect(int index)
{
    var watch=Stopwatch.StartNew();
    await clients[index].DisconnectAsync();
    Exception? last=null;
    for(int attempt=0;attempt<20;attempt++)
    {
        try
        {
            await Task.Delay(100+attempt*25,cancel);
            await clients[index].ConnectAsync(characters[index].Id,cancel);
            lastSnapshot[clients[index]]=total.Elapsed.TotalMilliseconds;
            watch.Stop(); return watch.Elapsed.TotalMilliseconds;
        }
        catch(Exception error) when(attempt<19) { last=error; }
    }
    throw new InvalidOperationException($"Client {index} could not reconnect while peers remained active.",last);
}

// One active WebSocket is allowed per account, so the live 50-client stage needs
// 50 distinct accounts. Respect the production auth limiter instead of bypassing it.
for(int i=0;i<stages[^1];i++)
{
    if(i>0&&i%20==0)
    {
        Console.WriteLine($"LOAD SETUP: {i}/50 accounts created; waiting for the real auth-rate window before continuing.");
        await Task.Delay(TimeSpan.FromSeconds(62),cancel);
    }
    var client=new GameConnection(address); clients.Add(client);
    await client.SignInAsync($"load_{i:00}_{suffix}",password,true,cancel);
    var character=await client.CreateCharacterAsync(new CharacterRequest{Name=$"Load {i:00} {suffix}",Class=i%2==0?"vanguard":"ranger",Appearance=new()},cancel);
    characters.Add(character);
}
Console.WriteLine($"LOAD SETUP: {clients.Count} independent accounts and characters created through the production HTTP API.");

int active=0;
try
{
    foreach(int target in stages)
    {
        var connectWatch=Stopwatch.StartNew();
        int first=active;
        await Task.WhenAll(Enumerable.Range(first,target-first).Select(i=>clients[i].ConnectAsync(characters[i].Id,cancel)));
        active=target; connectWatch.Stop();
        foreach(var client in clients.Take(active)) lastSnapshot[client]=total.Elapsed.TotalMilliseconds;

        var beforeChat=await Diagnostics();
        long commitsBeforeChat=beforeChat.GetProperty("commits").GetInt64();
        var chatTimes=(await Task.WhenAll(Enumerable.Range(0,active).Select(i=>SendChat(i,target)))).ToList();
        var afterChat=await Diagnostics();
        long chatCommitDelta=afterChat.GetProperty("commits").GetInt64()-commitsBeforeChat;
        if(chatCommitDelta<1||chatCommitDelta>active) throw new InvalidOperationException($"Durable chat checkpoint count {chatCommitDelta} is invalid for {active} acknowledged actions.");
        if(target>=25&&chatCommitDelta>=active) throw new InvalidOperationException($"The {target}-client persisted-action burst was not checkpoint-coalesced and required {chatCommitDelta} full realm commits.");
        double chatP95=Percentile(chatTimes,.95);
        if(chatP95>=4500) throw new InvalidOperationException($"Persisted action latency p95 {chatP95:F1} ms is too close to the 5 second client retry boundary at {target} clients.");
        double chatActionsPerCommit=active/(double)chatCommitDelta;

        var localIntervals=new List<double>(); var localSizes=new List<int>();
        var stage=Stopwatch.StartNew(); int loop=0; int snapshots=0;
        while(stage.Elapsed<TimeSpan.FromSeconds(stageSeconds))
        {
            Drain(active,localIntervals,localSizes,ref snapshots);
            double phase=(loop/20)%4;
            double x=phase switch {0=>1,2=>-1,_=>0};
            double y=phase switch {1=>1,3=>-1,_=>0};
            await Task.WhenAll(clients.Take(active).Select(client=>client.MoveAsync(x,y,cancel)));
            loop++; await Task.Delay(100,cancel);
        }
        await Task.WhenAll(clients.Take(active).Select(client=>client.MoveAsync(0,0,cancel)));
        await Task.Delay(300,cancel); Drain(active,localIntervals,localSizes,ref snapshots);

        int reconnectCount=target<10?0:Math.Max(2,target/5);
        var reconnectTimes=new List<double>(); long reconnectCommitDelta=0;
        if(reconnectCount>0)
        {
            var beforeReconnect=await Diagnostics(); long commitsBeforeReconnect=beforeReconnect.GetProperty("commits").GetInt64();
            var indices=Enumerable.Range(0,reconnectCount).Select(n=>active-1-n).ToArray();
            reconnectTimes=(await Task.WhenAll(indices.Select(Reconnect))).ToList();
            await Task.Delay(500,cancel); Drain(active,localIntervals,localSizes,ref snapshots);
            var afterReconnect=await Diagnostics(); reconnectCommitDelta=afterReconnect.GetProperty("commits").GetInt64()-commitsBeforeReconnect;
            if(afterReconnect.GetProperty("online").GetInt32()!=target) throw new InvalidOperationException($"Reconnect wave did not restore all {target} active clients.");
            if(reconnectCommitDelta<reconnectCount) throw new InvalidOperationException($"Reconnect wave recorded only {reconnectCommitDelta} commits for {reconnectCount} authoritative detaches.");
        }

        var diag=await Diagnostics();
        int online=diag.GetProperty("online").GetInt32();
        double tickAverage=diag.GetProperty("tickAverageMs").GetDouble();
        double tickP95=diag.GetProperty("tickP95Ms").GetDouble();
        long overruns=diag.GetProperty("overruns").GetInt64();
        long commits=diag.GetProperty("commits").GetInt64();
        double snapshotP95=Percentile(localIntervals,.95);
        double snapshotBytesP95=PercentileInt(localSizes,.95);
        int snapshotBytesMax=localSizes.Count==0?0:localSizes.Max();
        if(online!=target) throw new InvalidOperationException($"Expected {target} online clients, diagnostics reported {online}.");
        if(localIntervals.Count<target) throw new InvalidOperationException($"Only {localIntervals.Count} snapshot intervals were observed for {target} active clients.");
        if(snapshotP95>=500) throw new InvalidOperationException($"Snapshot interval p95 {snapshotP95:F1} ms exceeds 500 ms at {target} clients.");
        if(snapshotBytesMax>=2_000_000) throw new InvalidOperationException($"A live snapshot reached {snapshotBytesMax} bytes, exceeding the peer packet limit.");
        if(tickP95>=50) throw new InvalidOperationException($"Server rolling tick p95 {tickP95:F2} ms exceeds the 50 ms authoritative tick cadence at {target} clients.");
        stageReports.Add(new{clients=target,durationSeconds=stageSeconds,connectMilliseconds=connectWatch.Elapsed.TotalMilliseconds,snapshots,snapshotP95Ms=snapshotP95,snapshotBytesP95,snapshotBytesMax,
            persistedChatActions=active,chatCommitDelta,chatActionsPerCommit,chatLatencyP50Ms=Percentile(chatTimes,.50),chatLatencyP95Ms=chatP95,chatLatencyMaxMs=chatTimes.Max(),
            reconnectCount,reconnectCommitDelta,reconnectLatencyP95Ms=reconnectTimes.Count==0?0:Percentile(reconnectTimes,.95),tickAverageMs=tickAverage,tickP95Ms=tickP95,overruns,commits});
        Console.WriteLine($"LOAD STAGE: clients={target} duration={stageSeconds}s snapshots={snapshots} snapshotP95={snapshotP95:F1}ms snapshotBytesP95={snapshotBytesP95:F0} chatP95={chatP95:F1}ms chatCommits={chatCommitDelta} actionsPerCommit={chatActionsPerCommit:F2} reconnects={reconnectCount} cumulativeTickAvg={tickAverage:F3}ms cumulativeTickP95={tickP95:F3}ms overruns={overruns} commits={commits}");
    }
    var final=await Diagnostics();
    if(!final.GetProperty("ready").GetBoolean()) throw new InvalidOperationException("Server was not ready after sustained load.");
    if(final.GetProperty("online").GetInt32()!=50) throw new InvalidOperationException("All 50 clients were not online after the final stress stage.");
    if(final.GetProperty("commits").GetInt64()<1) throw new InvalidOperationException("Database diagnostics did not record any durable realm checkpoints.");
    double finalTickP95=final.GetProperty("tickP95Ms").GetDouble();
    if(finalTickP95>=50) throw new InvalidOperationException($"Server rolling tick p95 {finalTickP95:F2} ms exceeds the 50 ms cadence after the full staged load.");
    var report=new{referenceTarget="GitHub-hosted Linux CI; staged 2, 10, 25, then 50 independent real WebSocket clients against PostgreSQL",stageSeconds,totalSeconds=total.Elapsed.TotalSeconds,stages=stageReports,
        finalDiagnostics=JsonSerializer.Deserialize<object>(final.GetRawText()),snapshotP95Ms=Percentile(intervals,.95),snapshotBytesP95=PercentileInt(snapshotSizes,.95),snapshotBytesMax=snapshotSizes.Count==0?0:snapshotSizes.Max(),productionCapacityApproved=false};
    Directory.CreateDirectory(Path.GetDirectoryName(output)??".");
    File.WriteAllText(output,JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+Environment.NewLine);
    Console.WriteLine($"LOAD_ACCEPTANCE: 2/10/25/50 real clients passed for {stageSeconds}s per stage; snapshot p95 {Percentile(intervals,.95):F1} ms; snapshot bytes p95 {PercentileInt(snapshotSizes,.95):F0}; final rolling tick p95 {finalTickP95:F1} ms. This is a CI reference target, not a production-player capacity claim.");
}
finally
{
    foreach(var client in clients) await client.DisposeAsync();
}
