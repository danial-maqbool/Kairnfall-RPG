using System.Diagnostics;
using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text.Json;
using Kairnfall.Core;

string address=args.Length>0?args[0]:"http://127.0.0.1:5090";
int stageSeconds=args.Length>1?int.Parse(args[1]):20;
string output=args.Length>2?args[2]:"artifacts/load/load-report.json";
if(!Uri.TryCreate(address,UriKind.Absolute,out var endpoint)||!endpoint.IsLoopback) throw new InvalidOperationException("Load acceptance is restricted to loopback.");
int[] stages=[4,8,16];
string suffix=Convert.ToHexString(RandomNumberGenerator.GetBytes(4)).ToLowerInvariant();
string password="Load-only-"+Convert.ToHexString(RandomNumberGenerator.GetBytes(10));
using var timeout=new CancellationTokenSource(TimeSpan.FromMinutes(8));
var cancel=timeout.Token;
using var health=new HttpClient{BaseAddress=new Uri(address.TrimEnd('/')+"/"),Timeout=TimeSpan.FromSeconds(10)};
var clients=new List<GameConnection>();
var characters=new List<CharacterSummary>();
var lastSnapshot=new Dictionary<GameConnection,double>();
var intervals=new List<double>();
var stageReports=new List<object>();
var total=Stopwatch.StartNew();

static double Percentile(List<double> values,double quantile)
{
    if(values.Count==0) return double.PositiveInfinity;
    var sorted=values.Order().ToArray(); return sorted[Math.Min(sorted.Length-1,(int)Math.Ceiling(sorted.Length*quantile)-1)];
}
async Task<JsonElement> Diagnostics()
{
    using var response=await health.GetAsync("health",cancel); response.EnsureSuccessStatusCode();
    return (await response.Content.ReadFromJsonAsync<JsonElement>(cancellationToken:cancel));
}

for(int i=0;i<stages[^1];i++)
{
    var client=new GameConnection(address); clients.Add(client);
    await client.SignInAsync($"load_{i:00}_{suffix}",password,true,cancel);
    var character=await client.CreateCharacterAsync(new CharacterRequest{Name=$"Load {i:00} {suffix}",Class=i%2==0?"vanguard":"ranger",Appearance=new()},cancel);
    characters.Add(character);
}

int active=0;
try
{
    foreach(int target in stages)
    {
        var connectWatch=Stopwatch.StartNew();
        for(int i=active;i<target;i++)
        {
            await clients[i].ConnectAsync(characters[i].Id,cancel);
            lastSnapshot[clients[i]]=total.Elapsed.TotalMilliseconds;
        }
        active=target; connectWatch.Stop();
        var localIntervals=new List<double>();
        var stage=Stopwatch.StartNew(); int loop=0; int snapshots=0;
        while(stage.Elapsed<TimeSpan.FromSeconds(stageSeconds))
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
                    lastSnapshot[client]=now; snapshots++;
                }
                if(!client.Connected||client.LastError!="") throw new InvalidOperationException($"Client {i} disconnected under load: {client.LastError}");
            }
            double phase=(loop/20)%4;
            double x=phase switch {0=>1,2=>-1,_=>0};
            double y=phase switch {1=>1,3=>-1,_=>0};
            await Task.WhenAll(clients.Take(active).Select(client=>client.MoveAsync(x,y,cancel)));
            loop++; await Task.Delay(100,cancel);
        }
        for(int i=0;i<active;i++) await clients[i].MoveAsync(0,0,cancel);
        await Task.Delay(300,cancel);
        var diag=await Diagnostics();
        int online=diag.GetProperty("online").GetInt32();
        double tickAverage=diag.GetProperty("tickAverageMs").GetDouble();
        double tickP95=diag.GetProperty("tickP95Ms").GetDouble();
        long overruns=diag.GetProperty("overruns").GetInt64();
        long commits=diag.GetProperty("commits").GetInt64();
        double snapshotP95=Percentile(localIntervals,.95);
        if(online!=target) throw new InvalidOperationException($"Expected {target} online clients, diagnostics reported {online}.");
        if(tickP95>=45) throw new InvalidOperationException($"Server tick p95 {tickP95:F2} ms exceeds 45 ms at {target} clients.");
        if(snapshotP95>=400) throw new InvalidOperationException($"Snapshot interval p95 {snapshotP95:F1} ms exceeds 400 ms at {target} clients.");
        stageReports.Add(new{clients=target,durationSeconds=stageSeconds,connectMilliseconds=connectWatch.Elapsed.TotalMilliseconds,snapshots,snapshotP95Ms=snapshotP95,tickAverageMs=tickAverage,tickP95Ms=tickP95,overruns,commits});
        Console.WriteLine($"LOAD STAGE: clients={target} duration={stageSeconds}s snapshots={snapshots} snapshotP95={snapshotP95:F1}ms tickAvg={tickAverage:F3}ms tickP95={tickP95:F3}ms overruns={overruns} commits={commits}");
    }
    var final=await Diagnostics();
    if(!final.GetProperty("ready").GetBoolean()) throw new InvalidOperationException("Server was not ready after sustained load.");
    if(final.GetProperty("commits").GetInt64()<17) throw new InvalidOperationException("Database commit diagnostics did not include initial state and 16 character creations.");
    var report=new{referenceTarget="GitHub-hosted Linux CI; staged 4, 8, then 16 active graphical-protocol connections",stageSeconds,totalSeconds=total.Elapsed.TotalSeconds,stages=stageReports,
        finalDiagnostics=JsonSerializer.Deserialize<object>(final.GetRawText()),snapshotP95Ms=Percentile(intervals,.95),productionCapacityApproved=false};
    Directory.CreateDirectory(Path.GetDirectoryName(output)??".");
    File.WriteAllText(output,JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+Environment.NewLine);
    Console.WriteLine($"LOAD_ACCEPTANCE: 4/8/16 clients passed for {stageSeconds}s per stage; snapshot p95 {Percentile(intervals,.95):F1} ms. This is a CI reference target, not a production-player capacity claim.");
}
finally
{
    foreach(var client in clients) await client.DisposeAsync();
}
