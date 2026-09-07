using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Client-side eligibility and presentation. The server still resolves every action.</summary>
public static class ExperienceRules
{
    public static bool AllowsWorldInput(bool online, bool typing, bool menuOpen, bool focused, bool alive)
        => online && !typing && !menuOpen && focused && alive;

    public static double WeaponRange(Character self, Catalog data)
    {
        if (self.Equipment.TryGetValue("weapon", out var id))
        {
            var item = self.Inventory.FirstOrDefault(x => x.Id == id);
            if (item is { Durability: > 0 }) return data.Item(item.Template).Range;
        }
        return 1.7;
    }

    public static bool CanTarget(Character self, Creature creature, Catalog data, double range, bool explicitSelection = false)
    {
        if (self.Health <= 0 || creature.Health <= 0 || creature.Owner != "" || creature.Zone != self.Zone) return false;
        if (!creature.Position.Finite || self.Position.Distance(creature.Position) > range) return false;
        var definition = data.Mob(creature.Template);
        if (!explicitSelection && definition.Ai is "passive" or "fleeing" && creature.Target != self.Id) return false;
        return WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, creature.Position);
    }

    public static Creature? ChooseTarget(Character self, IEnumerable<Creature> creatures, Catalog data, string selected, double range)
    {
        var list = creatures.ToArray();
        var current = list.FirstOrDefault(x => x.Id == selected && CanTarget(self, x, data, range, true));
        if (current is not null) return current;
        return list.Where(x => CanTarget(self, x, data, range))
            .OrderBy(x => TargetScore(self, x))
            .ThenBy(x => x.Id, StringComparer.Ordinal)
            .FirstOrDefault();
    }

    private static double TargetScore(Character self, Creature creature)
    {
        var direction = self.Position.Direction(creature.Position);
        double facing = direction.X * self.Facing.X + direction.Y * self.Facing.Y;
        return self.Position.Distance(creature.Position) - .35 * facing;
    }

    public static WorldTarget? ChooseInteraction(Character self, IEnumerable<WorldTarget> targets, Catalog data)
        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot")
            .Where(x => x.Position.Finite && self.Position.Distance(x.Position) <= 2.15)
            .Where(x => WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, x.Position))
            .OrderBy(x => self.Position.Distance(x.Position))
            .ThenBy(x => x.Id, StringComparer.Ordinal)
            .Select(x => (WorldTarget?)x).FirstOrDefault();

    public static string InteractionVerb(string kind) => kind switch
    {
        "npc" => "Talk to", "exit" => "Enter", "node" => "Gather",
        "chest" => "Open", "loot" => "Pick up", _ => "Use"
    };

    public static string EquipmentProblem(Character self, Item item, Catalog data, string expectedSlot = "")
    {
        if (self.Health <= 0) return "You cannot change equipment while dead.";
        if (!self.Inventory.Any(x => x.Id == item.Id)) return "Move this item to your backpack first.";
        var definition = data.Item(item.Template);
        if (definition.Slot == "") return "This item is not equipment.";
        if (expectedSlot != "" && expectedSlot != definition.Slot)
            return "Place this item in the " + definition.Slot + " slot.";
        if (Items.Equipped(self, item.Id)) return "";
        if (definition.Skill != "" && Progression.Level(self, definition.Skill) < definition.Requirement)
            return "Requires " + data.Skill(definition.Skill).Name + " " + definition.Requirement + ".";
        try { Items.Equip(Wire.Copy(self), item.Id, data); return ""; }
        catch (RuleException error) { return error.Message; }
    }

    public static IReadOnlyList<AbilityDef> StarterAbilities(Character self, Catalog data)
    {
        string weaponSkill = self.Equipment.TryGetValue("weapon", out var id)
            ? data.Item(Items.Owned(self, id).Template).Skill : "unarmed_combat";
        return data.Abilities.Where(x => (x.Class == "" || x.Class == self.Class)
                && Progression.Level(self, x.Skill) >= x.Requirement)
            .OrderByDescending(x => x.Class == self.Class)
            .ThenByDescending(x => x.Kind is "strike" or "projectile" or "cone" or "line" or "aoe")
            .ThenByDescending(x => x.Skill == weaponSkill)
            .ThenBy(x => x.Requirement)
            .ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
    }
}

/// <summary>Limits requests across taps and held input. A release does not reset the rate limit.</summary>
public sealed class AttackRequestGate
{
    private double nextLocalRequest;
    public bool TryTake(double localTime, double serverTime, double serverReadyAt, bool allowed)
    {
        if (!allowed || !double.IsFinite(localTime) || !double.IsFinite(serverTime) || !double.IsFinite(serverReadyAt)) return false;
        if (localTime < nextLocalRequest || serverReadyAt > serverTime) return false;
        nextLocalRequest = localTime + .15;
        return true;
    }
}
