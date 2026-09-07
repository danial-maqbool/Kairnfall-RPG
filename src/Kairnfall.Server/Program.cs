using System.Net;
using System.Net.WebSockets;
using System.Text.Json;
using System.Threading.RateLimiting;
using Kairnfall.Core;
using Kairnfall.Server;
using Microsoft.AspNetCore.RateLimiting;
using Npgsql;

var builder=WebApplication.CreateBuilder(args);
builder.WebHost.ConfigureKestrel(options=>
{
    options.Limits.MaxRequestBodySize=Wire.MaximumMessageBytes;
    options.Limits.RequestHeadersTimeout=TimeSpan.FromSeconds(10);
    options.Limits.KeepAliveTimeout=TimeSpan.FromSeconds(30);
});
builder.Services.ConfigureHttpJsonOptions(options=>
{
    options.SerializerOptions.PropertyNamingPolicy=Wire.Json.PropertyNamingPolicy;
    options.SerializerOptions.PropertyNameCaseInsensitive=true;
    foreach(var converter in Wire.Json.Converters) options.SerializerOptions.Converters.Add(converter);
    options.SerializerOptions.MaxDepth=48;
});
builder.Services.AddRateLimiter(options=>
{
    options.RejectionStatusCode=StatusCodes.Status429TooManyRequests;
    options.AddPolicy("auth",context=>RateLimitPartition.GetFixedWindowLimiter(context.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){PermitLimit=20,Window=TimeSpan.FromMinutes(1),QueueLimit=0,AutoReplenishment=true}));
    options.AddPolicy("api",context=>RateLimitPartition.GetTokenBucketLimiter(context.Connection.RemoteIpAddress?.ToString()??"unknown",_=>new(){TokenLimit=100,TokensPerPeriod=50,ReplenishmentPeriod=TimeSpan.FromSeconds(1),QueueLimit=0,AutoReplenishment=true}));
});
string connectionString=Environment.GetEnvironmentVariable("KAIRNFALL_DB")??throw new InvalidOperationException("Set KAIRNFALL_DB to a PostgreSQL connection string. Use Run-Kairnfall-Dev.ps1 for local setup.");
var dataSourceBuilder=new NpgsqlDataSourceBuilder(connectionString);
builder.Services.AddSingleton(dataSourceBuilder.Build());
builder.Services.AddSingleton<RealmStore>();
builder.Services.AddSingleton<AccountStore>();
string catalogPath=Environment.GetEnvironmentVariable("KAIRNFALL_CATALOG")??Path.Combine(AppContext.BaseDirectory,"content","catalog.json");
if(!File.Exists(catalogPath)) catalogPath=Path.GetFullPath("content/catalog.json");
builder.Services.AddSingleton(Catalog.Load(catalogPath));
builder.Services.AddSingleton<RealmHost>();
builder.Services.AddHostedService(provider=>provider.GetRequiredService<RealmHost>());
var app=builder.Build();
bool localHttp=Environment.GetEnvironmentVariable("KAIRNFALL_ALLOW_LOCAL_HTTP")=="1"&&(app.Environment.IsDevelopment()||app.Environment.IsEnvironment("Testing"));
app.Use(async(context,next)=>
{
    context.Response.Headers.CacheControl="no-store";
    context.Response.Headers["X-Content-Type-Options"]="nosniff";
    bool loopback=context.Connection.RemoteIpAddress is { } ip&&IPAddress.IsLoopback(ip);
    if(!context.Request.IsHttps&&!(localHttp&&loopback))
    {
        context.Response.StatusCode=StatusCodes.Status426UpgradeRequired;
        await context.Response.WriteAsJsonAsync(new ApiError{Error="Use HTTPS and WSS. Plain HTTP is allowed only for explicit loopback development."},context.RequestAborted); return;
    }
    try { await next(context); }
    catch(RuleException error)
    {
        if(context.Response.HasStarted) return;
        context.Response.StatusCode=StatusCodes.Status400BadRequest;
        await context.Response.WriteAsJsonAsync(new ApiError{Error=error.Message},context.RequestAborted);
    }
    catch(OperationCanceledException) when(context.RequestAborted.IsCancellationRequested) { }
    catch(Exception error)
    {
        app.Logger.LogError(error,"Request failed. Sensitive request bodies and session tokens are not logged.");
        if(!context.Response.HasStarted)
        {
            context.Response.StatusCode=StatusCodes.Status503ServiceUnavailable;
            await context.Response.WriteAsJsonAsync(new ApiError{Error="The server could not complete this request. Reconnect before retrying."},context.RequestAborted);
        }
    }
});
app.UseRateLimiter();
app.UseWebSockets(new WebSocketOptions{KeepAliveInterval=TimeSpan.FromSeconds(15),KeepAliveTimeout=TimeSpan.FromSeconds(15)});

static string? Bearer(HttpContext context)
{
    string header=context.Request.Headers.Authorization.ToString();
    return header.StartsWith("Bearer ",StringComparison.Ordinal)?header[7..]:null;
}
static async Task<AccountSession?> Session(HttpContext context,AccountStore accounts)=>await accounts.AuthenticateAsync(Bearer(context),context.RequestAborted);
static CharacterSummary Summary(Character p)=>new(){Id=p.Id,Name=p.Name,Class=p.Class,Zone=p.Zone,Level=Progression.PlayerLevel(p),Appearance=p.Appearance};

app.MapGet("/health",(RealmHost realm)=>Results.Json(realm.Diagnostics(),statusCode:realm.Ready?200:503)).RequireRateLimiting("api");
app.MapPost("/api/register",async(LoginRequest request,AccountStore accounts,HttpContext context)=>
    Results.Json(await accounts.RegisterAsync(request,context.RequestAborted))).RequireRateLimiting("auth");
app.MapPost("/api/login",async(LoginRequest request,AccountStore accounts,RealmHost realm,HttpContext context)=>
{
    var login=await accounts.LoginAsync(request,context.RequestAborted);
    realm.RevokeAccountConnections(login.AccountId);
    return Results.Json(login);
}).RequireRateLimiting("auth");
app.MapPost("/api/logout",async(AccountStore accounts,RealmHost realm,HttpContext context)=>
{
    var token=Bearer(context); var fingerprint=AccountStore.Fingerprint(token);
    if(token is null||fingerprint is null) return Results.Unauthorized();
    await accounts.RevokeAsync(token,context.RequestAborted); realm.RevokeConnections(Convert.ToHexString(fingerprint));
    return Results.NoContent();
}).RequireRateLimiting("api");
app.MapGet("/api/characters",async(AccountStore accounts,RealmHost realm,HttpContext context)=>
{
    var session=await Session(context,accounts); if(session is null) return Results.Unauthorized();
    var characters=await realm.ReadAsync(r=>r.State.Characters.Values.Where(x=>x.Account==session.AccountId).Select(Summary).ToList(),context.RequestAborted);
    return Results.Json(characters);
}).RequireRateLimiting("api");
app.MapPost("/api/characters",async(CharacterRequest request,AccountStore accounts,RealmHost realm,HttpContext context)=>
{
    var session=await Session(context,accounts); if(session is null) return Results.Unauthorized();
    if(request.Appearance is null||request.Name is null||request.Class is null) throw new RuleException("Character fields cannot be null.");
    var character=await realm.WriteAsync(r=>Summary(r.CreateCharacter(session.AccountId,request.Name,request.Class,request.Appearance)),context.RequestAborted);
    return Results.Json(character,statusCode:201);
}).RequireRateLimiting("api");
app.MapGet("/api/catalog",(Catalog catalog)=>Results.Json(catalog,Wire.Json)).RequireRateLimiting("api");

app.Map("/play",async(HttpContext context,AccountStore accounts,RealmHost realm)=>
{
    if(!context.WebSockets.IsWebSocketRequest) { context.Response.StatusCode=400; return; }
    if(context.Request.Headers.Origin.Count>0) { context.Response.StatusCode=403; return; }
    if(!realm.Ready) { context.Response.StatusCode=503; return; }
    using var socket=await context.WebSockets.AcceptWebSocketAsync();
    Peer? peer=null;
    try
    {
        using var handshake=CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted);
        handshake.CancelAfter(TimeSpan.FromSeconds(10));
        var hello=await Peer.ReceiveAsync<ConnectionHello>(socket,Wire.MaximumMessageBytes,handshake.Token);
        if(hello is null||hello.Version!=Wire.Version||!Guid.TryParseExact(hello.CharacterId,"N",out _)) throw new RuleException("Invalid connection handshake or protocol version.");
        var session=await accounts.AuthenticateAsync(hello.Token,handshake.Token)??throw new RuleException("Your session expired. Sign in again.");
        peer=await realm.AttachAsync(socket,session,hello.CharacterId,handshake.Token);
        using var linked=CancellationTokenSource.CreateLinkedTokenSource(context.RequestAborted,peer.Closed.Token);
        var sender=peer.SendLoopAsync(context.RequestAborted);
        try
        {
            while(socket.State==WebSocketState.Open&&!linked.IsCancellationRequested)
            {
                var command=await Peer.ReceiveAsync<GameCommand>(socket,Wire.MaximumMessageBytes,linked.Token);
                if(command is null) break;
                await realm.HandleCommandAsync(peer,command,linked.Token);
            }
        }
        finally { peer.Abort(); await sender; }
    }
    catch(OperationCanceledException) { }
    catch(WebSocketException) { }
    catch(Exception error) when(error is RuleException or JsonException)
    {
        if(peer is null&&socket.State==WebSocketState.Open)
        {
            var payload=JsonSerializer.SerializeToUtf8Bytes(new TransportPacket{Kind="error",Error=error is RuleException?error.Message:"Malformed JSON message."},Wire.Json);
            try { await socket.SendAsync(payload,WebSocketMessageType.Text,true,CancellationToken.None); } catch(WebSocketException) { }
        }
    }
    finally
    {
        if(peer is not null)
        {
            using var cleanup=new CancellationTokenSource(TimeSpan.FromSeconds(10));
            try { await realm.DetachAsync(peer,cleanup.Token); } catch(OperationCanceledException) { }
            peer.Dispose();
        }
        socket.Abort();
    }
});

await app.RunAsync();
