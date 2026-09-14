using System.Globalization;
using System.Text.Json;

namespace Kairnfall.Core;

public sealed record PowerChange(string Name, double Before, double After)
{
    public double Difference => After - Before;
    public string Text => Name + " " + Difference.ToString("+0.##;-0.##;0", CultureInfo.InvariantCulture);
}
public sealed record EquipmentUpgrade(string ItemId, string Name, string Detail);
public sealed record ProgressionMoment(string Id, string Kind, string Title, string Detail, int Level = 0);

/// <summary>Presentation differences only. Every value comes from real character/item rules.</summary>
public static class ProgressionFeedback
{
    private static Dictionary<string, double> Values(Catalog data, Character player)
    {
        var stats = CombatMath.Stats(player, data);
        var result = new Dictionary<string, double>(StringComparer.Ordinal)
        {
            ["Physical power"] = stats.Physical, ["Spell power"] = stats.Spell,
            ["Armor"] = stats.Armor, ["Max health"] = stats.Health, ["Max mana"] = stats.Mana,
            ["Max stamina"] = stats.Stamina, ["Critical chance (points)"] = stats.Crit * 100,
            ["Evasion chance (points)"] = stats.Evasion * 100, ["Block chance (points)"] = stats.Block * 100,
            ["Movement speed"] = stats.MoveSpeed, ["Attack speed multiplier"] = stats.AttackSpeed
        };
        // Keep elemental/rune bonuses visible even when they do not alter physical power.
        // Raw named bonuses are deliberately not combined into a fictitious gear-score number.
        foreach (var bonus in stats.Bonuses)
            if (bonus.Key.StartsWith("resist_", StringComparison.Ordinal) || bonus.Key.StartsWith("damage_", StringComparison.Ordinal)
                || bonus.Key.EndsWith("_damage", StringComparison.Ordinal) || bonus.Key.EndsWith("_power", StringComparison.Ordinal))
                result[bonus.Key.Replace('_', ' ')] = bonus.Value;
        return result;
    }
    public static IReadOnlyList<PowerChange> StatChanges(Catalog data, Character before, Character after)
    {
        var old = Values(data, before); var current = Values(data, after);
        return old.Keys.Concat(current.Keys).Distinct(StringComparer.Ordinal)
            .Select(key => new PowerChange(key, old.GetValueOrDefault(key), current.GetValueOrDefault(key)))
            .Where(x => double.IsFinite(x.Difference) && Math.Abs(x.Difference) >= .005).ToArray();
    }
    public static IReadOnlyList<PowerChange> PowerChanges(Catalog data, Character before, Character after)
        => StatChanges(data, before, after).Where(x => x.Difference > 0).ToArray();

    public static EquipmentUpgrade? FindUpgrade(Catalog data, Character player)
    {
        if (player.Health <= 0) return null;
        foreach (var item in player.Inventory.OrderBy(x => x.Id, StringComparer.Ordinal))
        {
            var definition = data.Item(item.Template);
            if (definition.Slot == "" || definition.Type == "tool" || Items.Equipped(player, item.Id) || item.Durability <= 0) continue;
            var comparison = EquipmentComparison.Inspect(player, item, data);
            // A rarer item, a requirement-locked item, a slower weapon, or a two-hand
            // swap that removes useful offhand stats is not advertised as a simple upgrade.
            if (comparison.Blockers.Count != 0 || comparison.Notices.Count != 0
                || comparison.Stats.Any(x => x.Improvement < 0)
                || !comparison.Stats.Any(x => x.Improvement > 0)) continue;
            var preview = Wire.Copy(player);
            try { Items.Equip(preview, item.Id, data); }
            catch (RuleException) { continue; }
            var changes = StatChanges(data, player, preview);
            if (changes.Count == 0 || changes.Any(x => x.Difference < 0)) continue;
            return new(item.Id, definition.Name, string.Join(" · ", changes.Select(x => x.Text)));
        }
        return null;
    }
    private static string GearStamp(Character player) => JsonSerializer.Serialize(player.Equipment.OrderBy(x => x.Key, StringComparer.Ordinal)
        .Select(x => new { Slot = x.Key, Item = player.Inventory.FirstOrDefault(item => item.Id == x.Value) }), Wire.Json);
    private static bool Knows(Character player, AbilityDef ability) => Progression.Level(player, ability.Skill)
        >= ability.Requirement + (ability.Class != "" && ability.Class != player.Class ? 20 : 0);

    public static IReadOnlyList<ProgressionMoment> Between(Catalog data, Character before, Character after)
    {
        if (before.Id != after.Id) return [];
        var result = new List<ProgressionMoment>();
        int oldLevel = Progression.PlayerLevel(before), level = Progression.PlayerLevel(after);
        if (level > oldLevel)
        {
            double oldHealth = CombatMath.Stats(before, data).Health, health = CombatMath.Stats(after, data).Health;
            string change = (health - oldHealth).ToString("+0.##;-0.##;0", CultureInfo.InvariantCulture);
            result.Add(new("level:" + level, "level", "LEVEL UP · " + level,
                $"Max health {health:0.##} ({change}) · Skill training also advances character XP.", level));
        }
        foreach (var questId in after.CompletedQuests.Except(before.CompletedQuests, StringComparer.Ordinal))
        {
            QuestDef quest;
            try { quest = EndgameLoops.ResolveQuest(data, questId); }
            catch (RuleException) { continue; }
            result.Add(new("quest:" + questId, "quest", "QUEST COMPLETE · " + quest.Name,
                quest.Gold + " gold" + (quest.Reward == "" ? "" : " · " + data.Item(quest.Reward).Name) + " · Your next objective is ready."));
        }
        if (GearStamp(before) != GearStamp(after))
        {
            var changes = StatChanges(data, before, after);
            if (changes.Count > 0)
                result.Add(new("equipment:" + GearStamp(after), "equipment",
                    changes.All(x => x.Difference > 0) ? "POWER INCREASED" : "EQUIPMENT CHANGED · trade-offs",
                    string.Join(" · ", changes.Select(x => x.Text))));
        }
        var previousItems = before.Inventory.Select(x => x.Id).ToHashSet(StringComparer.Ordinal);
        if (after.Inventory.Any(x => !previousItems.Contains(x.Id))
            && FindUpgrade(data, after) is { } upgrade && !previousItems.Contains(upgrade.ItemId))
            result.Add(new("upgrade:" + upgrade.ItemId, "upgrade", "UPGRADE FOUND · " + upgrade.Name,
                upgrade.Detail + " · Open the backpack to review and equip."));
        var trained = data.Skills.Where(x => Progression.BaseLevel(after, x.Id) > Progression.BaseLevel(before, x.Id))
            .Select(x => x.Name + " " + Progression.BaseLevel(after, x.Id)).ToArray();
        if (trained.Length > 0) result.Add(new("skills:" + string.Join("|", trained), "skill", "SKILL UP",
            string.Join(" · ", trained) + " · Skills and character level progress separately."));
        var unlocked = data.Abilities.Where(x => !Knows(before, x) && Knows(after, x)).OrderBy(x => x.Requirement).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (unlocked.Length > 0) result.Add(new("arts:" + string.Join("|", unlocked.Select(x => x.Id)), "unlock", "NEW ARTS AVAILABLE",
            string.Join(" · ", unlocked.Take(3).Select(x => x.Name)) + (unlocked.Length > 3 ? $" (+{unlocked.Length - 3} more)" : "") + " · Review your arts and hotbar."));
        if (after.Gold > before.Gold && !before.Discoveries.Contains(NewPlayerJourney.MilestoneKey("loot"))
            && after.Discoveries.Contains(NewPlayerJourney.MilestoneKey("loot")) && !result.Any(x => x.Kind == "quest"))
            result.Add(new("first-loot", "reward", "SPOILS RECEIVED", $"Gold +{after.Gold - before.Gold} · Items are in your backpack."));
        if (after.PublicEventsCompleted > before.PublicEventsCompleted)
            result.Add(new("public:" + after.PublicEventsCompleted, "public", "PUBLIC CONTRIBUTION REWARDED",
                "Your participation was credited by the realm. Check your backpack and continue your quest."));
        if (before.Zone != after.Zone && data.Zone(after.Zone).Kind is "city" or "settlement")
            result.Add(new("arrival:" + after.Zone, "arrival", "ARRIVED · " + data.Zone(after.Zone).Name,
                "Follow the current objective for your next lead. Services and social opportunities are optional."));
        return result;
    }
}
