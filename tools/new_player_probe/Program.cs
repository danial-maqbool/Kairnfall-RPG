using System.Text.Json;
using Kairnfall.Core;
using Kairnfall.Probes;

bool classicLive = args.FirstOrDefault() == "--classic-tutorial-live";
bool classicScope = args.FirstOrDefault() == "--classic-tutorial-scope-checks";
string path = classicLive || classicScope ? args.ElementAtOrDefault(1) ?? "content/catalog.json" : args.FirstOrDefault() ?? "content/catalog.json";
try
{
    if (!File.Exists(path)) throw new FileNotFoundException("Build content first with python tools/build_content.py.", path);
    var data = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(path), Wire.Json)
        ?? throw new InvalidDataException("The new-player probe catalog is empty.");
    if (classicScope) { ClassicTutorialLiveProbe.CheckScopeBoundaries(data); return 0; }
    if (classicLive) return await ClassicTutorialLiveProbe.RunAsync(data, path);
    NewPlayerJourneyProbe.Run(data);
    return 0;
}
catch (Exception error)
{
    Console.Error.WriteLine("NEW_PLAYER_JOURNEY_FAILED: " + error);
    return 1;
}
