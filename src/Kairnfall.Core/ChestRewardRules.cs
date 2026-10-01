namespace Kairnfall.Core;

/// <summary>Ordinary chests never replace rewards earned through a specific journey or encounter.</summary>
public static class ChestRewardRules
{
    public static IEnumerable<ItemDef> EquipmentCandidates(Catalog data, int requirement)
        => data.Items.Where(x => x.Slot != "" && x.Type != "tool"
            && x.Requirement <= Math.Min(100, requirement + 10)
            && x.Requirement >= Math.Max(1, requirement - 20)
            && !x.Tags.Any(tag => tag is "boss_unique" or "opening_reward" or "exploration_unique"));
}
