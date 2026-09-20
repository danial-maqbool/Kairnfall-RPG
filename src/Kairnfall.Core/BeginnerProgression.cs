namespace Kairnfall.Core;

/// <summary>Early access without rewriting template grades, recipes or saved skill XP.</summary>
public static class BeginnerProgression
{
    public static int EquipmentRequirement(ItemDef item)
    {
        if ((item.Slot == "" && item.Type != "tool") || item.Requirement >= 20) return item.Requirement;
        int accessible = item.Requirement switch { <= 1 => 1, <= 5 => 3, <= 10 => 6, <= 15 => 10, _ => 13 };
        // A low requirement within a band must never become harder. This also
        // preserves future grade-2 and grade-7 equipment without special cases.
        return Math.Min(item.Requirement, accessible);
    }
    /// <summary>A monotone overall-level curve. Raw skill XP and skill levels do not change.</summary>
    public static double OverallEquivalentXp(long total)
    {
        double xp = Math.Max(0, total);
        // The early bonus slope decreases continuously. No new XP cliff at level 20.
        return xp + 50 * xp / (1 + xp / 250_000.0);
    }
}
