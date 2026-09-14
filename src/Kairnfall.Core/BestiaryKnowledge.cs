namespace Kairnfall.Core;

public sealed record BestiaryEntrySummary(
    string Rank,
    string Tactic,
    string[] Attacks,
    string[] Regions,
    string[] Drops,
    int Gold,
    int Xp);

/// <summary>Read-only presentation facts for creatures the authoritative character has already discovered.</summary>
public static class BestiaryKnowledge
{
    public static bool IsChampion(MobDef definition)
        => definition.Elite && definition.Name.StartsWith("Champion ", StringComparison.Ordinal);

    public static string Rank(MobDef definition)
        => definition.Boss ? "Boss" : IsChampion(definition) ? "Champion" : definition.Elite ? "Rare / Elite" : "Creature";

    public static string[] AttackLabels(MobDef definition)
        => definition.Attacks
            .Where(attack => !EnemyCombatRules.IsEliteTrait(attack) && EnemyCombatRules.IsKnownAttack(attack))
            .Select(EnemyCombatRules.AttackLabel)
            .Distinct(StringComparer.Ordinal)
            .ToArray();

    public static string[] EncounterRegions(Catalog data, MobDef definition)
        => data.Zones
            .Where(zone => zone.Boss == definition.Id || zone.Species.Contains(definition.Id, StringComparer.Ordinal))
            .OrderBy(zone => zone.Level)
            .ThenBy(zone => zone.Name, StringComparer.Ordinal)
            .Select(zone => zone.Name)
            .Distinct(StringComparer.Ordinal)
            .ToArray();

    public static string[] DropNames(Catalog data, MobDef definition)
        => definition.Drops
            .Select(id => data.Item(id).Name)
            .Distinct(StringComparer.Ordinal)
            .ToArray();

    public static BestiaryEntrySummary Describe(Catalog data, MobDef definition)
        => new(
            Rank(definition),
            EnemyCombatRules.TacticLabel(definition),
            AttackLabels(definition),
            EncounterRegions(data, definition),
            DropNames(data, definition),
            definition.Gold,
            definition.Xp);
}
