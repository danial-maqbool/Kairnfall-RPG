using System.Net;
using System.Security.Cryptography;
using System.Text.Json;
using System.Threading.RateLimiting;
using Kairnfall.Core;
using Kairnfall.Server;
using Microsoft.AspNetCore.RateLimiting;

var builder=WebApplication.CreateBuilder(args);
if(string.IsNullOrWhiteSpace(Environment.GetEnvironmentVariable("ASPNETCORE_URLS")))
    builder.WebHost.UseUrls("http://127.0.0.1:5080");
builder.WebHost.ConfigureKestrel(options=>options.Limits.MaxRequestBodySize=Wire.MaximumMessageBytes);
string contentPath=Environment.GetEnvironmentVariable("KAIRNFALL_CONTENT")
    ??Path.Combine(AppContext.BaseDirectory,"content","catalog.json");
if(!File.Exists(contentPath)&&File.Exists("content/catalog.json")) contentPath=Path.GetFullPath("content/catalog.json");
if(!File.Exists(contentPath)) throw new FileNotFoundException("Build the content first: python tools/build_content.py. Set KAIRNFALL_CONTENT to catalog.json.",contentPath);
var data=Catalog.Load(contentPath);
string catalogHash=Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(contentPath))).ToLowerInvariant();
string connectionString=Environment.GetEnvironmentVariable("KAIRNFALL_DB")
    ??throw new InvalidOperationException("KAIRNFALL_DB is not set. Run bootstrap.ps1 to create local development configuration.");

builder.Services.AddSingleton(data);
builder.Services.AddSingleton(new RealmStore(connectionString));
builder.Services.AddSingleton<AccountService>();
builder.Services.AddSingleton<RealmHub>(services=>new RealmHub(data,services.GetRequiredService<RealmStore>(),
    services.GetRequiredService<AccountService>(),services.GetRequiredService<ILogger<RealmHub>>(),
    services.GetRequiredService<IHostApplicationLifetime>(),catalogHash));
builder.Services.AddHostedService(services=>services.GetRequiredService<RealmHub>());
builder.Services.ConfigureHttpJsonOptions(options=>
{
    options.SerializerOptions.PropertyNamingPolicy=JsonNamingPolicy.CamelCase;
    options.SerializerOptions.PropertyNameCaseInsensitive=true;
    options.SerializerOptions.MaxDepth=48;
    foreach(var converter in Wire.Json.Converters) options.SerializerOptions.Converters.Add(converter);
});
builder.Services.AddRateLimiter(options=>
{
    options.RejectionStatusCode=StatusCodes.Status429TooManyRequests;
    options.AddPolicy("authentication",context=>RateLimitPartition.GetFixedWindowLimiter(
        context.Connection.RemoteIpAddress?.ToString()??"unknown",
        _=>new FixedWindowRateLimiterOptions{PermitLimit=12,Window=TimeSpan.FromMinutes(1),QueueLimit=0}));
    options.AddPolicy("api",context=>RateLimitPartition.GetFixedWindowLimiter(
        context.Connection.RemoteIpAddress?.ToString()??"unknown",
        _=>new FixedWindowRateLimiterOptions{PermitLimit=240,Window=TimeSpan.FromMinutes(1),QueueLimit=0}));
});

var app=builder.Build();
app.Use(async(context,next)=>
{
    var remote=context.Connection.RemoteIpAddress;
    bool local=remote is null||IPAddress.IsLoopback(remote)||(remote.IsIPv4MappedToIPv6&&IPAddress.IsLoopback(remote.MapToIPv4()));
    if(!context.Request.IsHttps&&!local)
    {
        context.Response.StatusCode=StatusCodes.Status403Forbidden;
        await context.Response.WriteAsJsonAsync(new{error="Remote connections require HTTPS and WSS. This HTTP endpoint accepts loopback connections only."});
        return;
    }
    context.Response.Headers["X-Content-Type-Options"]="nosniff";
    context.Response.Headers.CacheControl="no-store";
    try { await next(context); }
    catch(RuleException error)
    {
        if(context.Response.HasStarted) throw;
        context.Response.StatusCode=StatusCodes.Status400BadRequest;
        await context.Response.WriteAsJsonAsync(new{error=error.Message});
    }
    catch(UnauthorizedAccessException)
    {
        if(context.Response.HasStarted) throw;
        context.Response.StatusCode=StatusCodes.Status401Unauthorized;
        await context.Response.WriteAsJsonAsync(new{error="Log in before using this endpoint."});
    }
    catch(JsonException)
    {
        if(context.Response.HasStarted) throw;
        context.Response.StatusCode=StatusCodes.Status400BadRequest;
        await context.Response.WriteAsJsonAsync(new{error="Invalid JSON request."});
    }
});
app.UseRateLimiter();
app.UseWebSockets(new WebSocketOptions{KeepAliveInterval=TimeSpan.FromSeconds(15)});

Session RequireSession(HttpContext context,AccountService accounts)
    =>accounts.Authenticate(AccountService.Bearer(context))??throw new UnauthorizedAccessException();

app.MapGet("/healthz",(RealmHub hub)=>hub.Ready?Results.Ok(new{ready=true,protocol=Wire.Version}):Results.StatusCode(503));
app.MapGet("/api/status",async(RealmHub hub,CancellationToken cancellationToken)=>Results.Json(await hub.StatusAsync(cancellationToken),Wire.Json))
    .RequireRateLimiting("api");
app.MapPost("/api/accounts",async(Credentials input,AccountService accounts,CancellationToken cancellationToken)=>
    Results.Json(await accounts.RegisterAsync(input,cancellationToken),Wire.Json)).RequireRateLimiting("authentication");
app.MapPost("/api/login",async(Credentials input,AccountService accounts,CancellationToken cancellationToken)=>
    Results.Json(await accounts.LoginAsync(input,cancellationToken),Wire.Json)).RequireRateLimiting("authentication");
app.MapPost("/api/logout",(HttpContext context,AccountService accounts)=>
{
    accounts.Logout(AccountService.Bearer(context)); return Results.NoContent();
}).RequireRateLimiting("api");
app.MapGet("/api/characters",async(HttpContext context,AccountService accounts,RealmHub hub,CancellationToken cancellationToken)=>
{
    var session=RequireSession(context,accounts);
    return Results.Json(await hub.CharactersAsync(session.Account,cancellationToken),Wire.Json);
}).RequireRateLimiting("api");
app.MapPost("/api/characters",async(CharacterRequest input,HttpContext context,AccountService accounts,RealmHub hub,CancellationToken cancellationToken)=>
{
    var session=RequireSession(context,accounts);
    return Results.Json(await hub.CreateCharacterAsync(session.Account,input,cancellationToken),Wire.Json);
}).RequireRateLimiting("api");
app.MapGet("/realm",async(HttpContext context,RealmHub hub)=>
{
    if(!hub.Ready) { context.Response.StatusCode=503; return; }
    if(!context.WebSockets.IsWebSocketRequest) { context.Response.StatusCode=400; return; }
    await hub.ServeSocketAsync(context);
}).RequireRateLimiting("api");
await app.RunAsync();
