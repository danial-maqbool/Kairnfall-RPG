using System.Net.WebSockets;
using System.Text.Json;
using System.Threading.Channels;
using Kairnfall.Core;

namespace Kairnfall.Server;

public sealed class Peer(WebSocket socket,AccountSession session,string characterId) : IDisposable
{
    public WebSocket Socket { get; }=socket;
    public AccountSession Session { get; }=session;
    public string CharacterId { get; }=characterId;
    public CancellationTokenSource Closed { get; }=new();
    private readonly Channel<byte[]> control=Channel.CreateBounded<byte[]>(new BoundedChannelOptions(64){SingleReader=true,SingleWriter=false,FullMode=BoundedChannelFullMode.Wait});
    private byte[]? latestSnapshot;
    private long window=Environment.TickCount64;
    private int moveCount;
    private int actionCount;
    public bool AcceptRate(string kind)
    {
        long now=Environment.TickCount64;
        if(now-window>=1000) { window=now; moveCount=0; actionCount=0; }
        return kind=="move"?++moveCount<=40:++actionCount<=16;
    }
    public void Enqueue(TransportPacket packet)
    {
        if(Closed.IsCancellationRequested) return;
        var bytes=JsonSerializer.SerializeToUtf8Bytes(packet,Wire.Json);
        if(bytes.Length>2_000_000) { Abort(); return; }
        if(packet.Kind=="snapshot") Interlocked.Exchange(ref latestSnapshot,bytes);
        else if(!control.Writer.TryWrite(bytes)) Abort();
    }
    public async Task SendLoopAsync(CancellationToken shutdown)
    {
        using var linked=CancellationTokenSource.CreateLinkedTokenSource(shutdown,Closed.Token);
        using var timer=new PeriodicTimer(TimeSpan.FromMilliseconds(20));
        try
        {
            while(await timer.WaitForNextTickAsync(linked.Token))
            {
                while(control.Reader.TryRead(out var packet)) await Socket.SendAsync(packet,WebSocketMessageType.Text,true,linked.Token);
                var snapshot=Interlocked.Exchange(ref latestSnapshot,null);
                if(snapshot is not null) await Socket.SendAsync(snapshot,WebSocketMessageType.Text,true,linked.Token);
            }
        }
        catch(OperationCanceledException) { }
        catch(WebSocketException) { }
        finally { Abort(); }
    }
    public void Abort()
    {
        if(!Closed.IsCancellationRequested) Closed.Cancel();
        control.Writer.TryComplete(); Socket.Abort();
    }
    public void Dispose() { Abort(); Closed.Dispose(); }
    public static async Task<T?> ReceiveAsync<T>(WebSocket socket,int maximumBytes,CancellationToken cancel) where T:class
    {
        using var stream=new MemoryStream(); byte[] buffer=new byte[4096];
        while(true)
        {
            var result=await socket.ReceiveAsync(buffer.AsMemory(),cancel);
            if(result.MessageType==WebSocketMessageType.Close) return null;
            if(result.MessageType!=WebSocketMessageType.Text) throw new RuleException("Only UTF-8 JSON text messages are accepted.");
            if(stream.Length+result.Count>maximumBytes) throw new RuleException("The network message exceeds the size limit.");
            stream.Write(buffer,0,result.Count);
            if(result.EndOfMessage) break;
        }
        if(stream.Length==0) throw new RuleException("Empty network message.");
        return JsonSerializer.Deserialize<T>(stream.ToArray(),Wire.Json)??throw new RuleException("Invalid JSON object.");
    }
}
