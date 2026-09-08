using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Presentation-only rules. They never change authoritative movement or equipment.</summary>
public static class SpritePoseRules
{
    public const int ActorSize = 64;
    public const int FootBaseline = 55;
    private static readonly string[][] Orders =
    [
        ["cloak", "body", "legs", "boots", "chest", "belt", "hair", "helmet", "necklace", "charm", "trinket", "offhand", "weapon", "gloves", "ring"],
        ["cloak", "weapon", "body", "legs", "boots", "chest", "belt", "hair", "helmet", "necklace", "charm", "trinket", "offhand", "gloves", "ring"],
        ["cloak", "offhand", "body", "legs", "boots", "chest", "belt", "hair", "helmet", "necklace", "charm", "trinket", "weapon", "gloves", "ring"],
        ["weapon", "offhand", "body", "legs", "boots", "chest", "belt", "cloak", "hair", "helmet", "necklace", "charm", "trinket", "gloves", "ring"]
    ];
    private static readonly IReadOnlyList<string>[] ReadOnlyOrders = Orders.Select(Array.AsReadOnly).ToArray();
    public static IReadOnlyList<string> Layers(int direction) => ReadOnlyOrders[Math.Clamp(direction, 0, 3)];
    public static Vector2 Anchor(int size) => new(size / 2f, MathF.Round(size * .86f));

    public static int Direction(Point facing, int previous)
    {
        previous = Math.Clamp(previous, 0, 3);
        if (!facing.Finite || Math.Abs(facing.X) + Math.Abs(facing.Y) < .001) return previous;
        double x = Math.Abs(facing.X), y = Math.Abs(facing.Y);
        // Preserve the dominant axis near a diagonal instead of alternating sheet rows.
        bool horizontal = previous is 1 or 2;
        if (horizontal && y <= x * 1.18) return facing.X < 0 ? 1 : 2;
        if (!horizontal && x <= y * 1.18) return facing.Y < 0 ? 3 : 0;
        return x > y ? facing.X < 0 ? 1 : 2 : facing.Y < 0 ? 3 : 0;
    }

    public static double AdvanceWalk(double phase, double distance)
    {
        if (!double.IsFinite(phase) || !double.IsFinite(distance) || distance < 0) return 0;
        // One gait cycle per 1.7 tiles. Network cadence does not restart the cycle.
        return (phase + Math.Min(distance, 6) * PixelAssets.Frames / 1.7) % PixelAssets.Frames;
    }
}
