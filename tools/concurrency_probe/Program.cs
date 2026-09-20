using System.Net.WebSockets;
using System.Text.Json;
using Kairnfall.Core;
using Kairnfall.Server;

var catalogPath = args.Length > 0 ? args[0] : "content/catalog.json";
var catalog = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(catalogPath), Wire.Json)
    ?? throw new InvalidOperationException("Could not load generated content catalog.");
var failures = new List<string>();
ConcurrencyStressChecks.Run(catalog, failures);
try
{
    using var socket = new ClientWebSocket();
    using var peer = new Peer(socket, new AccountSession("rate-account", "rate-fingerprint", DateTimeOffset.UtcNow.AddHours(1)), "rate-character");
    for (int i = 0; i < 16; i++) if (!peer.AcceptRate("chat")) throw new InvalidOperationException("Chat/action rate limiter rejected within the documented 16-action window.");
    if (peer.AcceptRate("chat")) throw new InvalidOperationException("Chat/action rate limiter accepted a 17th action in one second.");
    for (int i = 0; i < 40; i++) if (!peer.AcceptRate("move")) throw new InvalidOperationException("Movement rate limiter rejected within the documented 40-move window.");
    if (peer.AcceptRate("move")) throw new InvalidOperationException("Movement rate limiter accepted a 41st move in one second.");
    Console.WriteLine("PASS CONCURRENCY · chat/action and movement spam are rate limited at the live Peer boundary");
}
catch (Exception error)
{
    failures.Add("Concurrency stress · server rate limiting: " + error.Message);
    Console.WriteLine("FAIL CONCURRENCY · server rate limiting: " + error.Message);
}
foreach (var failure in failures) Console.WriteLine("FAIL " + failure);
return failures.Count == 0 ? 0 : 1;
