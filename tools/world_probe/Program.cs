using Kairnfall.Core;
using System.Text.Json;

var catalog = JsonSerializer.Deserialize<Catalog>(File.ReadAllText(args.Length > 0 ? args[0] : "content/catalog.json"), Wire.Json)!;
var failures = new List<string>();
int walls = 0, destinations = 0;
foreach (var zone in catalog.Zones)
{
    foreach (var building in zone.Buildings)
        for (int y = building.Y + 1; y < building.Y + building.Height; y++)
            for (int x = building.X; x < building.X + building.Width; x++)
            {
                if (x == building.X + building.Width / 2 && y == building.Y + building.Height - 1) continue;
                walls++;
                if (WorldMap.Walkable(zone, new Point(x + .5, y + .5))) failures.Add($"Walkable masonry {zone.Id}/{building.Id} ({x},{y})");
            }
    // Flood actual actor-fitting tile centers; graph edges alone cannot prove accessibility.
    var reached = new HashSet<(int X, int Y)>();
    var queue = new Queue<(int X, int Y)>();
    queue.Enqueue(((int)zone.Spawn.X, (int)zone.Spawn.Y));
    while (queue.TryDequeue(out var tile))
    {
        if (tile.X < 1 || tile.Y < 1 || tile.X >= zone.Width - 1 || tile.Y >= zone.Height - 1 || reached.Contains(tile)) continue;
        if (!WorldMap.Fits(zone, new Point(tile.X + .5, tile.Y + .5))) continue;
        reached.Add(tile);
        queue.Enqueue((tile.X + 1, tile.Y)); queue.Enqueue((tile.X - 1, tile.Y));
        queue.Enqueue((tile.X, tile.Y + 1)); queue.Enqueue((tile.X, tile.Y - 1));
    }
    void Require(Point at, string label)
    {
        destinations++;
        if (!WorldMap.Fits(zone, at) || !reached.Contains(((int)at.X, (int)at.Y))) failures.Add($"Unreachable {zone.Id}/{label} ({at.X},{at.Y})");
    }
    Require(zone.Spawn, "spawn");
    foreach (var exit in zone.Exits) Require(exit.Position, "exit " + exit.Id);
    foreach (var source in catalog.Zones)
        foreach (var exit in source.Exits.Where(e => e.Target == zone.Id)) Require(exit.Arrival, "arrival " + exit.Id);
    foreach (var building in zone.Buildings) Require(new Point(building.X + building.Width / 2 + .5, building.Y + building.Height - .5), "door " + building.Id);
    foreach (var npc in catalog.Npcs.Where(n => n.Zone == zone.Id)) Require(npc.Position, "service " + npc.Id);
}
foreach (var failure in failures) Console.WriteLine("FAIL " + failure);
Console.WriteLine($"WORLD PROBE: {catalog.Zones.Count} zones; {walls} masonry tiles; {destinations} destinations; {failures.Count} failures.");
return failures.Count == 0 ? 0 : 1;
