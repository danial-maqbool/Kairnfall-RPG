using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Presentation-only rules. They never alter movement, ownership or combat results.</summary>
public static class SpritePoseRules
{
    public const int ActorSize = 64;
    public const int FootBaseline = 55;
    public const int WaistCut = 43;
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

    public static float CharacterScale(Catalog data, Character? character)
    {
        if (data.ClassicTutorial is not { } tuning || character?.ClassicTutorial is null) return 1;
        double scale = tuning.AvatarScale;
        return double.IsFinite(scale) && scale is >= .5 and <= 1 ? (float)scale : 1;
    }

    public static Rect2 FrameDestination(Vector2 feet, int size, int top, int bottom, float scale = 1)
    {
        if (!float.IsFinite(scale) || scale is < .5f or > 1) scale = 1;
        // Scale every composited layer and action slice around the same authored
        // floor point. Source rows, hit geometry and world positions stay intact.
        return new Rect2(feet - Anchor(size) * scale + new Vector2(0, top * scale),
            new Vector2(size * scale, (bottom - top) * scale));
    }

    public static int Direction(Point facing, int previous)
    {
        previous = Math.Clamp(previous, 0, 3);
        if (!facing.Finite || Math.Abs(facing.X) + Math.Abs(facing.Y) < .001) return previous;
        double x = Math.Abs(facing.X), y = Math.Abs(facing.Y);
        bool horizontal = previous is 1 or 2;
        if (horizontal && y <= x * 1.18) return facing.X < 0 ? 1 : 2;
        if (!horizontal && x <= y * 1.18) return facing.Y < 0 ? 3 : 0;
        return x > y ? facing.X < 0 ? 1 : 2 : facing.Y < 0 ? 3 : 0;
    }

    public static int ActionFrame(int state, double elapsed, double duration)
        => ActorMotion.ActionFrame(state, elapsed, duration);
    public static double AdvanceWalk(double phase, double distance)
        => ActorMotion.AdvanceWalk(phase, distance);

    public static (string Key, int State) SheetAddress(string key, int state)
    {
        bool human = key.StartsWith("people/", StringComparison.Ordinal)
            || key.StartsWith("equipment/", StringComparison.Ordinal)
            || key.StartsWith("npcs/", StringComparison.Ordinal);
        if (human && state is >= 6 and <= 10)
        {
            string[] motions = ["interact", "craft", "run", "bow_attack", "crossbow_attack"];
            return ("motions/" + motions[state - 6] + "/" + key, 0);
        }
        return (key, Math.Clamp(state, 0, key.StartsWith("motions/", StringComparison.Ordinal) ? 0 : 5));
    }

    public static int WeaponPose(int state, IReadOnlyDictionary<string, string> equipment)
    {
        if (state != 2 || !equipment.TryGetValue("weapon", out var weapon)) return state;
        if (weapon.Contains("crossbow", StringComparison.OrdinalIgnoreCase)) return 10;
        return weapon.Contains("bow", StringComparison.OrdinalIgnoreCase) ? 9 : state;
    }
}
