using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Kairnfall.Core;

int passed = 0, failed = 0;
void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
async Task Test(string name, Func<Task> test)
{
    try { await test(); passed++; Console.WriteLine("PASS " + name); }
    catch (Exception error) { failed++; Console.WriteLine("FAIL " + name + ": " + error.GetType().Name + " " + error.Message); }
}
LoginResponse Session() => new() { Token = new string('A', 43), AccountId = "test-account", Expires = DateTimeOffset.UtcNow.AddHours(1) };
HttpResponseMessage Json(object value, HttpStatusCode status = HttpStatusCode.OK) => new(status) { Content = JsonContent.Create(value, options: Wire.Json) };

await Test("registration uses HTTP before a gameplay socket exists", async () =>
{
    int requests = 0;
    var handler = new DelegateHandler(async (request, cancel) =>
    {
        requests++;
        Check(request.Method == HttpMethod.Post && request.RequestUri!.AbsolutePath == "/api/register", "Wrong registration method or path.");
        Check(request.Headers.Authorization is null, "Registration sent stale account credentials.");
        var body = await request.Content!.ReadFromJsonAsync<LoginRequest>(Wire.Json, cancel);
        Check(body is { Username: "testaccount", Password: "Test-password-123" }, "Incorrect registration body.");
        return Json(Session());
    });
    await using var connection = new GameConnection("http://127.0.0.1:5077", handler);
    var response = await connection.SignInAsync("testaccount", "Test-password-123", true);
    Check(requests == 1 && response.AccountId == "test-account", "HTTP registration was not completed exactly once.");
    Check(connection.Session is not null && !connection.Connected, "Registration must not create a gameplay connection.");
});

await Test("login and character listing use account HTTP headers", async () =>
{
    int requests = 0;
    var session = Session();
    var handler = new DelegateHandler((request, cancel) =>
    {
        requests++;
        if (requests == 1)
        {
            Check(request.Method == HttpMethod.Post && request.RequestUri!.AbsolutePath == "/realm/api/login", "Wrong login endpoint.");
            return Task.FromResult(Json(session));
        }
        Check(request.Method == HttpMethod.Get && request.RequestUri!.AbsolutePath == "/realm/api/characters", "Wrong character endpoint.");
        Check(request.Headers.Authorization?.Scheme == "Bearer" && request.Headers.Authorization.Parameter == session.Token, "Missing account authorization.");
        return Task.FromResult(Json(new List<CharacterSummary>()));
    });
    await using var connection = new GameConnection("https://realm.example/realm", handler);
    await connection.SignInAsync("tester", "Test-password-123", false);
    Check((await connection.CharactersAsync()).Count == 0 && requests == 2, "Character HTTP exchange failed.");
});

await Test("an HTTP authentication rejection does not become a socket error", async () =>
{
    var handler = new DelegateHandler((request, cancel) => Task.FromResult(Json(new ApiError { Error = "Invalid account name or password." }, HttpStatusCode.Unauthorized)));
    await using var connection = new GameConnection("http://localhost:5077", handler);
    bool rejected = false;
    try { await connection.SignInAsync("tester", "wrong-password", false); }
    catch (RuleException error) { rejected = error.Message == "Invalid account name or password."; }
    Check(rejected && connection.Session is null && !connection.Connected, "Rejected authentication left a session or returned the wrong error.");
});

await Test("invalid session tokens are rejected", async () =>
{
    var invalid = Session(); invalid.Token = "invalid";
    await using var connection = new GameConnection("http://localhost:5077", new DelegateHandler((request, cancel) => Task.FromResult(Json(invalid))));
    bool rejected = false;
    try { await connection.SignInAsync("tester", "Test-password-123", false); }
    catch (RuleException) { rejected = true; }
    Check(rejected && connection.Session is null, "Malformed session accepted.");
});

await Test("expired sessions are rejected", async () =>
{
    var invalid = Session(); invalid.Expires = DateTimeOffset.UtcNow.AddMinutes(-1);
    await using var connection = new GameConnection("http://localhost:5077", new DelegateHandler((request, cancel) => Task.FromResult(Json(invalid))));
    bool rejected = false;
    try { await connection.SignInAsync("tester", "Test-password-123", false); }
    catch (RuleException) { rejected = true; }
    Check(rejected && connection.Session is null, "Expired session accepted.");
});

await Test("HTTP cancellation reaches the account request", async () =>
{
    var handler = new DelegateHandler(async (request, cancel) => { await Task.Delay(Timeout.Infinite, cancel); return Json(Session()); });
    await using var connection = new GameConnection("http://localhost:5077", handler);
    using var cancel = new CancellationTokenSource(TimeSpan.FromMilliseconds(100));
    bool cancelled = false;
    try { await connection.SignInAsync("tester", "Test-password-123", true, cancel.Token); }
    catch (OperationCanceledException) { cancelled = true; }
    Check(cancelled && connection.Session is null && !connection.Connected, "Cancelled authentication created a session.");
});

await Test("changing accounts clears old authorization before the request", async () =>
{
    int requests = 0;
    var handler = new DelegateHandler((request, cancel) =>
    {
        requests++;
        Check(request.Headers.Authorization is null, "Old bearer token was attached to a new login.");
        return Task.FromResult(requests == 1 ? Json(Session()) : Json(new ApiError { Error = "Rejected." }, HttpStatusCode.Unauthorized));
    });
    await using var connection = new GameConnection("http://localhost:5077", handler);
    await connection.SignInAsync("tester", "Test-password-123", false);
    try { await connection.SignInAsync("second", "bad-password", false); } catch (RuleException) { }
    Check(requests == 2 && connection.Session is null, "Rejected account change retained the old account.");
});

await Test("remote plaintext and embedded credentials are refused", async () =>
{
    foreach (var address in new[] { "http://realm.example", "https://user:password@realm.example", "https://realm.example?token=private", "https://realm.example#fragment" })
    {
        bool rejected = false;
        try { await using var connection = new GameConnection(address); }
        catch (RuleException) { rejected = true; }
        Check(rejected, "Unsafe server address accepted.");
    }
});

Console.WriteLine($"HTTP_TRANSPORT_RESULTS passed={passed} failed={failed} revision={GameConnection.TransportRevision}");
return failed == 0 ? 0 : 1;

sealed class DelegateHandler(Func<HttpRequestMessage, CancellationToken, Task<HttpResponseMessage>> send) : HttpMessageHandler
{
    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) => send(request, cancellationToken);
}
