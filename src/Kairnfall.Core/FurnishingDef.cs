namespace Kairnfall.Core;

/// <summary>Authored furniture. Art and collision share this floor footprint.</summary>
public sealed class FurnishingDef
{
    public string Id { get; set; } = "";
    public string Kind { get; set; } = "";
    public int X { get; set; }
    public int Y { get; set; }
    public int Width { get; set; } = 1;
    public int Height { get; set; } = 1;
    public int Rise { get; set; }
    public bool Solid { get; set; }
    public bool Ground { get; set; }

    public bool Covers(int x, int y) => x >= X && y >= Y
        && (long)x < (long)X + Width && (long)y < (long)Y + Height;

    public static void Validate(ZoneDef zone, List<string> errors)
    {
        var ids = new HashSet<string>(StringComparer.Ordinal);
        var occupied = new HashSet<(int, int)>();
        foreach (var item in zone.Furnishings)
        {
            bool valid = !string.IsNullOrWhiteSpace(item.Id) && ids.Add(item.Id)
                && item.Kind is { Length: > 0 and <= 48 }
                && item.Kind.All(c => c is >= 'a' and <= 'z' or '_')
                && item.Width is >= 1 and <= 8 && item.Height is >= 1 and <= 8
                && item.Rise is >= 0 and <= 96 && !(item.Ground && item.Solid)
                && item.X >= 1 && item.Y >= 1
                && (long)item.X + item.Width < zone.Width - 1
                && (long)item.Y + item.Height < zone.Height - 1;
            if (!valid) { errors.Add("Invalid furnishing " + zone.Id + "/" + item.Id); continue; }
            for (int y = item.Y; y < item.Y + item.Height; y++)
                for (int x = item.X; x < item.X + item.Width; x++)
                {
                    if (item.Solid && !occupied.Add((x, y))) errors.Add("Overlapping solid furnishings " + zone.Id);
                    // Ground art also must not make water or masonry look traversable.
                    if (WorldMap.IsSolid(WorldMap.GroundTileAt(zone, x, y)))
                        errors.Add("Furnishing occupies existing solid terrain " + zone.Id + "/" + item.Id);
                }
        }
    }
}
