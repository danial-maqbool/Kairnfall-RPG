namespace Kairnfall.Core;

/// <summary>Read-only item comparison. Requirements never hide the comparison.</summary>
public sealed record ItemStatComparison(string Key, double Value, double? Difference, bool LowerIsBetter = false)
{
    public int Improvement => Difference is not { } d || Math.Abs(d) < .005 ? 0 : Math.Sign(d) * (LowerIsBetter ? -1 : 1);
}
public sealed record ItemInspection(string ComparedWith, IReadOnlyList<ItemStatComparison> Stats, IReadOnlyList<string> Blockers, IReadOnlyList<string> Notices);

public static class EquipmentComparison
{
    public static Dictionary<string,double> Values(Item item, Catalog data)
    {
        var def = data.Item(item.Template);
        var values = new Dictionary<string,double>(StringComparer.Ordinal);
        void Add(string key, double value) => values[key] = values.GetValueOrDefault(key) + value;
        double quality = 1 + .1 * (int)item.Rarity;
        if (def.Power != 0) Add("item_power", def.Power * quality);
        if (def.Armor != 0) Add("item_armor", def.Armor * quality);
        if (def.Slot == "weapon") { Add("weapon_range", def.Range); Add("attack_interval", def.Speed); }
        foreach (var stat in def.Stats) Add(stat.Key, stat.Value);
        foreach (var affix in item.Affixes) if (!BuildDefiningLoot.IsEffectAffix(affix)) Add(affix.Stat, affix.Value);
        foreach (var rune in item.Runes)
            foreach (var stat in data.Item(rune.Template).Stats) Add(stat.Key, stat.Value);
        // A broken item supplies no equipment bonuses in CombatMath. Its repairable
        // intrinsic values remain useful, but must not masquerade as active bonuses.
        if (item.Durability <= 0 && def.Slot != "")
            foreach (string key in values.Keys.ToArray()) if (key is not "weapon_range" and not "attack_interval") values[key] = 0;
        return values;
    }

    public static ItemInspection Inspect(Character? self, Item item, Catalog data, bool ownedRequired = true)
    {
        var def = data.Item(item.Template);
        var blocked = new List<string>(); var notices = new List<string>();
        var before = new Dictionary<string,double>(StringComparer.Ordinal);
        var replaced = new List<Item>();
        bool compare = self is not null && def.Slot != "";
        if (compare && self!.Equipment.TryGetValue(def.Slot, out string? id))
        {
            var old = self.Inventory.FirstOrDefault(x => x.Id == id);
            if (old is not null) replaced.Add(old);
        }
        if (compare && def.Slot == "weapon" && !HandEquipment.Compatible(def, HandEquipment.Definition(self!, "offhand", data)))
        {
            var offhand = self!.Equipment.TryGetValue("offhand", out string? offId) ? self.Inventory.FirstOrDefault(x => x.Id == offId) : null;
            if (offhand is not null)
            {
                replaced.Add(offhand);
                notices.Add("Unequips " + data.Item(offhand.Template).Name + ". Included in comparison.");
            }
        }
        foreach (var old in replaced.DistinctBy(x => x.Id))
            foreach (var stat in Values(old, data)) before[stat.Key] = before.GetValueOrDefault(stat.Key) + stat.Value;
        var after = Values(item, data);
        var rows = after.Keys.Concat(before.Keys).Distinct(StringComparer.Ordinal)
            .OrderBy(k => k switch { "item_power" => 0, "item_armor" => 1, "attack_interval" => 2, "weapon_range" => 3, _ => 4 })
            .ThenBy(k => k, StringComparer.Ordinal)
            .Select(k => new ItemStatComparison(k, after.GetValueOrDefault(k),
                compare && (k != "attack_interval" || before.ContainsKey(k)) ? after.GetValueOrDefault(k) - before.GetValueOrDefault(k) : null,
                k == "attack_interval")).ToArray();
        if (def.Slot != "" && self is not null)
        {
            if (self.Health <= 0) blocked.Add("Cannot change equipment while dead.");
            if (ownedRequired && !self.Inventory.Any(x => x.Id == item.Id)) blocked.Add("Move this item to your backpack first.");
            if (item.Durability <= 0) blocked.Add("Broken: repair before equipping.");
            int required = BeginnerProgression.EquipmentRequirement(def);
            if (def.Skill != "" && Progression.BaseLevel(self, def.Skill) < required)
                blocked.Add($"Requires {data.Skill(def.Skill).Name} {required} (trained {Progression.BaseLevel(self, def.Skill)}; equipment bonuses do not count).");
            if (def.Slot == "offhand" && !HandEquipment.Compatible(HandEquipment.Definition(self, "weapon", data), def))
                blocked.Add("Incompatible with your equipped weapon.");
            if (blocked.Count == 0 && !Items.Equipped(self, item.Id))
            {
                // The authoritative equip operation catches any additional rule.
                // This copy is never sent to the realm or used to grant equipment.
                var preview = Wire.Copy(self);
                if (!preview.Inventory.Any(x => x.Id == item.Id)) preview.Inventory.Add(Wire.Copy(item));
                try { Items.Equip(preview, item.Id, data); }
                catch (RuleException error) { blocked.Add(error.Message); }
            }
        }
        string comparison = !compare ? "" : replaced.Count == 0 ? "Empty " + def.Slot + " slot"
            : string.Join(" + ", replaced.Select(x => data.Item(x.Template).Name));
        return new(comparison, rows, blocked, notices);
    }
}
