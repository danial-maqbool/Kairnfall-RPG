using System.Runtime.CompilerServices;
using System.Text.Json;
using Kairnfall.Core;
using Kairnfall.Probes;

internal static class NewPlayerJourneyChecks
{
    [ModuleInitializer]
    internal static void Run()
    {
        string root = Directory.GetCurrentDirectory();
        string path = File.Exists(Path.Combine(root, "content", "catalog.json"))
            ? Path.Combine(root, "content", "catalog.json") : Path.Combine(root, "client", "Data", "catalog.json");
        if (!File.Exists(path)) return;
        NewPlayerJourneyProbe.Run(JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path), Wire.Json)
            ?? throw new InvalidDataException("Empty new-player journey catalog."));
    }
}
