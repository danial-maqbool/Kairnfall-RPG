using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Client eligibility and feedback. The server validates and resolves each request.</summary>
public static class ExperienceRules
{
    public const double TargetCycleRadius = 12;
    public static bool AllowsWorldInput(bool online, bool typing, bool menuOpen, bool focused, bool alive)
        => online && !typing && !menuOpen && focused && alive;

    public static double WeaponRange(Character self, Catalog data)
    {
        if (self.Equipment.TryGetValue("weapon", out var id))
        {
            var item = self.Inventory.FirstOrDefault(x => x.Id == id);
            if (item is not null) return data.Item(item.Template).Range;
        }
        return 1.6;
    }

    public static double AttackInterval(Character self, Catalog data)
    {
        var item = self.Equipment.TryGetValue("weapon", out var id)
            ? self.Inventory.FirstOrDefault(x => x.Id == id) : null;
        double speed = item is null ? .8 : data.Item(item.Template).Speed;
        return Math.Max(.25, speed / CombatMath.Stats(self, data).AttackSpeed);
    }

    public static string AttackProblem(Character self, Catalog data, double serverTime)
    {
        if (self.Health <= 0) return "Respawn before attacking.";
        if (self.Statuses.Any(x => x.Until > serverTime && x.Kind == "stun")) return "You are stunned.";
        if (self.Equipment.TryGetValue("weapon", out var id)
            && self.Inventory.FirstOrDefault(x => x.Id == id) is not { Durability: > 0 })
            return "Your weapon needs repair.";
        if (self.Stamina < 3) return "Recover stamina before attacking.";
        return "";
    }

    public static bool CanTarget(Character self, Creature creature, Catalog data, double range, bool explicitSelection = false)
    {
        if (!double.IsFinite(range) || range < 0 || !self.Position.Finite) return false;
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
            .OrderBy(x => TargetScore(self, x)).ThenBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault();
    }

    public static Creature? CycleTarget(Character self, IEnumerable<Creature> creatures, Catalog data, string selected, bool reverse = false)
    {
        // Deliberate target cycling includes neutral animals, never pets or corpses.
        var list = creatures.Where(x => CanTarget(self, x, data, TargetCycleRadius, true))
            .OrderBy(x => self.Position.Distance(x.Position)).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
        if (list.Length == 0) return null;
        int index = Array.FindIndex(list, x => x.Id == selected);
        if (index < 0) return reverse ? list[^1] : list[0];
        return list[(index + (reverse ? list.Length - 1 : 1)) % list.Length];
    }

    private static double TargetScore(Character self, Creature creature)
    {
        var direction = self.Position.Direction(creature.Position);
        double facing = direction.X * self.Facing.X + direction.Y * self.Facing.Y;
        return self.Position.Distance(creature.Position) - .35 * facing;
    }

    public static List<Point> ApproachPath(Character self, Creature creature, Catalog data, double remainingDistance = 2.5)
    {
        if (!double.IsFinite(remainingDistance) || remainingDistance <= 0) return [];
        double budget = Math.Min(2.5, remainingDistance);
        double range = WeaponRange(self, data);
        if (!CanTarget(self, creature, data, range + 1.75, true)) return [];
        double distance = self.Position.Distance(creature.Position);
        if (distance <= range) return [];
        var zone = data.Zone(self.Zone);
        // Movement consumes a waypoint within .32 tiles. Finish farther inside
        // weapon range so consuming the final waypoint cannot strand the player.
        double stopRange = Math.Max(.25, range - .4);
        var direction = self.Position.Direction(creature.Position);
        double directLength = distance - stopRange;
        var delta = direction.Scale(directLength);
        var destination = new Point(self.Position.X + delta.X, self.Position.Y + delta.Y);
        if (directLength <= budget && WorldMap.Fits(zone, destination)
            && WorldMap.Move(zone, self.Position, delta).Distance(destination) < .01)
            return [destination];
        var path = WorldMap.FindPath(zone, self.Position, creature.Position, 2048);
        var result = new List<Point>();
        var previous = self.Position;
        double length = 0;
        foreach (var point in path)
        {
            length += previous.Distance(point);
            if (length > budget || !WorldMap.Fits(zone, point)) return [];
            result.Add(point);
            if (point.Distance(creature.Position) <= stopRange && WorldMap.LineOfSight(zone, point, creature.Position)) return result;
            previous = point;
        }
        return [];
    }

    public static bool LootAvailable(Character self, LootPile pile, double serverTime)
        => double.IsFinite(serverTime) && pile.Zone == self.Zone
            && (pile.Owner == self.Id || pile.PublicAt <= serverTime || (pile.Party != "" && pile.Party == self.Party));

    public static WorldTarget? ChooseInteraction(Character self, IEnumerable<WorldTarget> targets, Catalog data)
        => targets.Where(x => x.Kind is "npc" or "exit" or "node" or "chest" or "loot" or "landmark")
            .Where(x => x.Position.Finite && self.Position.Distance(x.Position) <= 2.15)
            .Where(x => WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, x.Position))
            .OrderBy(x => self.Position.Distance(x.Position))
            .ThenBy(x => x.Kind == "loot" ? 0 : 1).ThenBy(x => x.Id, StringComparer.Ordinal)
            .Select(x => (WorldTarget?)x).FirstOrDefault();

    public static string InteractionVerb(string kind) => kind switch
    {
        "npc" => "Talk to", "exit" => "Enter", "node" => "Gather",
        "chest" => "Open", "loot" => "Pick up", "landmark" => "Survey", _ => "Use"
    };

    public static string EquipmentProblem(Character self, Item item, Catalog data, string expectedSlot = "")
    {
        if (self.Health <= 0) return "You cannot change equipment while dead.";
        if (!self.Inventory.Any(x => x.Id == item.Id)) return "Move this item to your backpack first.";
        var definition = data.Item(item.Template);
        if (definition.Slot == "") return "This item is not equipment.";
        if (expectedSlot != "" && expectedSlot != definition.Slot) return "Place this item in the " + definition.Slot + " slot.";
        if (Items.Equipped(self, item.Id)) return "";
        int required = BeginnerProgression.EquipmentRequirement(definition);
        if (definition.Skill != "" && Progression.Level(self, definition.Skill) < required)
            return "Requires " + data.Skill(definition.Skill).Name + " " + required + ".";
        try { Items.Equip(Wire.Copy(self), item.Id, data); return ""; }
        catch (RuleException error) { return error.Message; }
    }

    public static int AbilityRequirement(Character self, AbilityDef ability)
        => ability.Requirement + (ability.Class != "" && ability.Class != self.Class ? 20 : 0);

    public static string AbilityProblem(Character self, AbilityDef ability, Catalog data, double serverTime)
    {
        if (self.Health <= 0) return "Respawn before using an ability.";
        if (self.Statuses.Any(x => x.Until > serverTime && x.Kind is "stun" or "silence")) return "You cannot cast while stunned or silenced.";
        int requirement = AbilityRequirement(self, ability);
        if (Progression.Level(self, ability.Skill) < requirement) return "Requires " + data.Skill(ability.Skill).Name + " " + requirement + ".";
        if (self.Mana < ability.Mana) return "Not enough mana for " + ability.Name + ".";
        if (self.Stamina < ability.Stamina) return "Not enough stamina for " + ability.Name + ".";
        if (self.Cooldowns.GetValueOrDefault("ability:" + ability.Id) > serverTime
            || self.Cooldowns.GetValueOrDefault("global_ability") > serverTime) return ability.Name + " is on cooldown.";
        return "";
    }

    public static IReadOnlyList<AbilityDef> StarterAbilities(Character self, Catalog data)
    {
        string weaponSkill = self.Equipment.TryGetValue("weapon", out var id)
            ? data.Item(Items.Owned(self, id).Template).Skill : "unarmed_combat";
        return data.Abilities.Where(x => Progression.Level(self, x.Skill) >= AbilityRequirement(self, x))
            .OrderByDescending(x => x.Class == self.Class)
            .ThenByDescending(x => x.Kind is "strike" or "projectile" or "cone" or "line" or "area" or "drain" or "dot")
            .ThenByDescending(x => x.Skill == weaponSkill).ThenBy(x => x.Requirement)
            .ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
    }
}

/// <summary>A release does not reset the rate limit. Server cooldown remains mandatory.</summary>
public sealed class AttackRequestGate
{
    private double nextLocalRequest;
    public bool TryTake(double localTime, double serverTime, double serverReadyAt, bool allowed, double minimumInterval = .15)
    {
        if (!allowed || !double.IsFinite(localTime) || !double.IsFinite(serverTime)
            || !double.IsFinite(serverReadyAt) || !double.IsFinite(minimumInterval)) return false;
        if (localTime < nextLocalRequest || serverReadyAt > serverTime) return false;
        nextLocalRequest = localTime + Math.Max(.15, minimumInterval);
        return true;
    }
}
