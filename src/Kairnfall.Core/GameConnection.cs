using System.Collections.Concurrent;
using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Net.WebSockets;
using System.Text.Json;

namespace Kairnfall.Core;

/// <summary>Desktop and test transport. HTTP owns account exchange; the socket carries gameplay intentions.</summary>
public sealed class GameConnection : IAsyncDisposable
{
    public const string TransportRevision = "http-account-socket-gameplay-v2";
    private readonly HttpClient http;
    private readonly Uri endpoint;
    private ClientWebSocket? socket;
    private CancellationTokenSource? sessionCancel;
    private Task? receiver;
    private readonly SemaphoreSlim sendGate = new(1, 1);
    private readonly SemaphoreSlim actionGate = new(1, 1);
    private readonly ConcurrentDictionary<string, TaskCompletionSource<CommandResult>> pending = new();
    private readonly ConcurrentQueue<TransportPacket> control = new();
    private TransportPacket? latestSnapshot;
    private TaskCompletionSource<bool>? firstSnapshot;
    private long sequence;
    private string token = "";
    private volatile bool connected;
    public bool Connected => connected;
    public LoginResponse? Session { get; private set; }
    public TransportPacket? LastSnapshot { get; private set; }
    public string CharacterId { get; private set; } = "";
    public string LastError { get; private set; } = "";
    public Uri Endpoint => endpoint;
    public long LastSequence => Interlocked.Read(ref sequence);

    public GameConnection(string address) : this(address, new SocketsHttpHandler { AllowAutoRedirect = false }) { }

    /// <summary>Supply a handler for deterministic HTTP contract tests. This connection owns the handler.</summary>
    public GameConnection(string address, HttpMessageHandler handler)
    {
        ArgumentNullException.ThrowIfNull(handler);
        if (!Uri.TryCreate(address, UriKind.Absolute, out var uri) || uri.Scheme is not ("http" or "https") || uri.UserInfo != "" || uri.Query != "" || uri.Fragment != "")
            throw new RuleException("Enter an HTTP or HTTPS server address without embedded credentials, query parameters, or a fragment.");
        bool loopback = uri.IsLoopback || (IPAddress.TryParse(uri.Host, out var ip) && IPAddress.IsLoopback(ip));
        if (uri.Scheme != "https" && !loopback) throw new RuleException("Remote servers require HTTPS and WSS. Plain HTTP is allowed only for localhost.");
        endpoint = new Uri(uri.AbsoluteUri.TrimEnd('/') + "/");
        http = new HttpClient(handler, disposeHandler: true) { BaseAddress = endpoint, Timeout = TimeSpan.FromSeconds(20) };
    }

    private static async Task<T> ReadResponseAsync<T>(HttpResponseMessage response, CancellationToken cancel)
    {
        if (!response.IsSuccessStatusCode)
        {
            string message = response.StatusCode == HttpStatusCode.Unauthorized ? "Your session expired. Sign in again." : response.StatusCode == (HttpStatusCode)429 ? "The server rate limit was reached. Reduce the request rate." : "The server rejected the request.";
            try
            {
                var error = await response.Content.ReadFromJsonAsync<ApiError>(Wire.Json, cancel).ConfigureAwait(false);
                if (!string.IsNullOrWhiteSpace(error?.Error)) message = error.Error;
            }
            catch (JsonException) { }
            throw new RuleException(message);
        }
        return await response.Content.ReadFromJsonAsync<T>(Wire.Json, cancel).ConfigureAwait(false)
            ?? throw new RuleException("The server returned an empty response.");
    }

    public void UseSession(LoginResponse session)
    {
        ArgumentNullException.ThrowIfNull(session);
        if (!AccountTokenLooksValid(session.Token) || session.Expires <= DateTimeOffset.UtcNow)
            throw new RuleException("The session token is invalid or expired.");
        Session = session;
        token = session.Token;
        http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }
    private static bool AccountTokenLooksValid(string value) => value is { Length: 43 } && value.All(c => char.IsAsciiLetterOrDigit(c) || c is '-' or '_');

    // This method must never call SendObjectAsync. Authentication precedes the
    // gameplay WebSocket. Keep it testable before any socket has been created.
    public Task<LoginResponse> SignInAsync(string username, string password, bool register, CancellationToken cancel = default)
        => AuthenticateHttpAsync(new LoginRequest { Username = username, Password = password }, register, cancel);

    private async Task<LoginResponse> AuthenticateHttpAsync(LoginRequest credentials, bool register, CancellationToken cancel)
    {
        if (Connected) throw new RuleException("Leave the current world before changing accounts.");
        Session = null;
        token = "";
        http.DefaultRequestHeaders.Authorization = null;
        LastError = "";
        using var request = new HttpRequestMessage(HttpMethod.Post, register ? "api/register" : "api/login")
        {
            Content = JsonContent.Create(credentials, options: Wire.Json)
        };
        using var response = await http.SendAsync(request, HttpCompletionOption.ResponseContentRead, cancel).ConfigureAwait(false);
        var session = await ReadResponseAsync<LoginResponse>(response, cancel).ConfigureAwait(false);
        UseSession(session);
        return session;
    }

    public async Task<List<CharacterSummary>> CharactersAsync(CancellationToken cancel = default)
    {
        using var response = await http.GetAsync("api/characters", cancel).ConfigureAwait(false);
        return await ReadResponseAsync<List<CharacterSummary>>(response, cancel).ConfigureAwait(false);
    }
    public async Task<CharacterSummary> CreateCharacterAsync(CharacterRequest request, CancellationToken cancel = default)
    {
        using var response = await http.PostAsJsonAsync("api/characters", request, Wire.Json, cancel).ConfigureAwait(false);
        return await ReadResponseAsync<CharacterSummary>(response, cancel).ConfigureAwait(false);
    }
    public async Task<Catalog> CatalogAsync(CancellationToken cancel = default)
    {
        using var response = await http.GetAsync("api/catalog", cancel).ConfigureAwait(false);
        return await ReadResponseAsync<Catalog>(response, cancel).ConfigureAwait(false);
    }
    public async Task ConnectAsync(string character, CancellationToken cancel = default)
    {
        if (Session is null || token == "") throw new RuleException("Sign in before entering the world.");
        await DisconnectAsync();
        CharacterId = character; LastError = ""; Interlocked.Exchange(ref sequence, 0);
        sessionCancel = CancellationTokenSource.CreateLinkedTokenSource(cancel);
        socket = new ClientWebSocket(); socket.Options.KeepAliveInterval = TimeSpan.FromSeconds(15);
        var target = new UriBuilder(new Uri(endpoint, "play")) { Scheme = endpoint.Scheme == "https" ? "wss" : "ws" };
        firstSnapshot = new(TaskCreationOptions.RunContinuationsAsynchronously);
        try
        {
            await socket.ConnectAsync(target.Uri, sessionCancel.Token);
            await SendObjectAsync(new ConnectionHello { Token = token, CharacterId = character }, sessionCancel.Token);
            connected = true; receiver = ReceiveLoopAsync(socket, sessionCancel.Token);
            await firstSnapshot.Task.WaitAsync(TimeSpan.FromSeconds(15), cancel);
        }
        catch { await DisconnectAsync(); throw; }
    }
    public bool TryRead(out TransportPacket? packet)
    {
        if (control.TryDequeue(out packet)) return true;
        packet = Interlocked.Exchange(ref latestSnapshot, null);
        if (packet is not null) LastSnapshot = packet;
        return packet is not null;
    }
    private async Task SendObjectAsync<T>(T value, CancellationToken cancel)
    {
        var bytes = JsonSerializer.SerializeToUtf8Bytes(value, Wire.Json);
        if (bytes.Length > Wire.MaximumMessageBytes) throw new RuleException("The command is too large.");
        await sendGate.WaitAsync(cancel);
        try
        {
            var current = socket;
            if (current is null || current.State != WebSocketState.Open) throw new RuleException("The gameplay connection is closed. Enter the world before sending game commands.");
            await current.SendAsync(bytes, WebSocketMessageType.Text, true, cancel);
        }
        finally { sendGate.Release(); }
    }
    public Task MoveAsync(double x, double y, CancellationToken cancel = default) => SendObjectAsync(new GameCommand { Kind = "move", X = x, Y = y }, cancel);
    public async Task<CommandResult> ActAsync(GameCommand command, CancellationToken cancel = default)
    {
        if (command.Kind == "move") throw new ArgumentException("Use MoveAsync for movement intents.", nameof(command));
        await actionGate.WaitAsync(cancel);
        try
        {
            if (!connected) throw new RuleException("The gameplay connection is closed. Enter the world before sending game commands.");
            command.Version = Wire.Version; command.RequestId = Guid.NewGuid().ToString("N"); command.Sequence = LastSequence + 1;
            var result = new TaskCompletionSource<CommandResult>(TaskCreationOptions.RunContinuationsAsynchronously);
            pending[command.RequestId] = result;
            try
            {
                for (int attempt = 0; attempt < 3; attempt++)
                {
                    await SendObjectAsync(command, cancel);
                    try { return await result.Task.WaitAsync(TimeSpan.FromSeconds(5), cancel); }
                    catch (TimeoutException) when (attempt < 2) { }
                }
                throw new RuleException("The operation was not confirmed. Reconnect and inspect your inventory before retrying.");
            }
            finally { pending.TryRemove(command.RequestId, out _); }
        }
        finally { actionGate.Release(); }
    }
    private void AdvanceSequence(long value)
    {
        long current;
        do { current = Interlocked.Read(ref sequence); if (value <= current) return; }
        while (Interlocked.CompareExchange(ref sequence, value, current) != current);
    }
    private async Task ReceiveLoopAsync(ClientWebSocket current, CancellationToken cancel)
    {
        byte[] buffer = new byte[16384];
        try
        {
            while (!cancel.IsCancellationRequested && current.State == WebSocketState.Open)
            {
                using var stream = new MemoryStream();
                while (true)
                {
                    var part = await current.ReceiveAsync(buffer.AsMemory(), cancel);
                    if (part.MessageType == WebSocketMessageType.Close) return;
                    if (part.MessageType != WebSocketMessageType.Text || stream.Length + part.Count > 2_000_000) throw new RuleException("The server sent an invalid or oversized packet.");
                    stream.Write(buffer, 0, part.Count); if (part.EndOfMessage) break;
                }
                var packet = JsonSerializer.Deserialize<TransportPacket>(stream.ToArray(), Wire.Json) ?? throw new RuleException("The server returned an invalid packet.");
                if (packet.Kind == "snapshot" && packet.Snapshot is not null)
                {
                    if (packet.Snapshot.Version != Wire.Version) throw new RuleException("The server protocol does not match this client.");
                    AdvanceSequence(packet.Snapshot.Self.LastAction);
                    Interlocked.Exchange(ref latestSnapshot, packet); firstSnapshot?.TrySetResult(true);
                }
                else
                {
                    if (packet.Result is { } result)
                    {
                        AdvanceSequence(result.Sequence);
                        if (pending.TryGetValue(result.RequestId, out var waiter)) waiter.TrySetResult(result);
                    }
                    if (packet.Kind == "error")
                    {
                        LastError = packet.Error;
                        if (firstSnapshot is { Task.IsCompleted: false }) firstSnapshot.TrySetException(new RuleException(packet.Error));
                    }
                    if (control.Count >= 128) throw new RuleException("The client did not consume network messages quickly enough.");
                    control.Enqueue(packet);
                }
            }
        }
        catch (OperationCanceledException) when (cancel.IsCancellationRequested) { }
        catch (Exception error) when (error is WebSocketException or JsonException or RuleException or IOException)
        {
            LastError = error.Message; control.Enqueue(new() { Kind = "error", Error = LastError });
        }
        finally
        {
            connected = false;
            var error = new RuleException(LastError == "" ? "The connection closed. Sign in again to restore your persisted character." : LastError);
            firstSnapshot?.TrySetException(error);
            foreach (var waiter in pending.Values) waiter.TrySetException(error);
        }
    }
    public async Task DisconnectAsync()
    {
        connected = false;
        sessionCancel?.Cancel(); socket?.Abort();
        if (receiver is not null) { try { await receiver; } catch (OperationCanceledException) { } receiver = null; }
        socket?.Dispose(); socket = null; sessionCancel?.Dispose(); sessionCancel = null;
        Interlocked.Exchange(ref latestSnapshot, null); LastSnapshot = null; while (control.TryDequeue(out _)) { }
    }
    public async Task SignOutAsync(CancellationToken cancel = default)
    {
        await DisconnectAsync();
        try { if (token != "") { using var response = await http.PostAsync("api/logout", null, cancel); } }
        finally { token = ""; Session = null; http.DefaultRequestHeaders.Authorization = null; }
    }
    public async ValueTask DisposeAsync()
    {
        await DisconnectAsync(); http.Dispose(); sendGate.Dispose(); actionGate.Dispose();
    }
}
