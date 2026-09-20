using Godot;
using Kairnfall.Core;
using System.Globalization;

namespace Kairnfall.Client;

/// <summary>Shared, centered item card for inspection, shop previews and hover panels.</summary>
public static class CompactItemCard
{
    public const int Width = 328;
    public const int CompactIconSize = 28;
    public const int CompactStatRows = 4;

    public static Label Centered(string text, int size = 13, Color? color = null, bool wrap = true)
    {
        var label = Ui.Label(text, size, color, wrap);
        label.HorizontalAlignment = HorizontalAlignment.Center;
        label.VerticalAlignment = VerticalAlignment.Center;
        label.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        return label;
    }

    public static string Number(double value) => (Math.Abs(value) < .005 ? 0 : value).ToString("0.##", CultureInfo.InvariantCulture);
    public static string Delta(double value) => Math.Abs(value) < .005 ? "0" : value.ToString("+0.##;-0.##;0", CultureInfo.InvariantCulture);
    public static Color StatColor(ItemStatComparison stat) => stat.Improvement > 0 ? Ui.Success : stat.Improvement < 0 ? Ui.Danger : Ui.Text;
    public static string StatName(string key) => key switch
    {
        "item_power" => "Power", "item_armor" => "Item armor", "armor" => "Armor bonus", "weapon_range" => "Range (tiles)",
        "attack_interval" => "Attack interval (s)", _ => Ui.Words(key)
    };

    private static IEnumerable<string> CompactBlockers(IReadOnlyList<string> blockers)
    {
        if (blockers.Count == 0) yield break;
        string primary = blockers.FirstOrDefault(x => x.StartsWith("Requires ", StringComparison.Ordinal)) ?? blockers[0];
        int other = blockers.Count - 1;
        yield return other == 0 ? primary : $"{primary} · +{other} restriction{(other == 1 ? "" : "s")}";
    }

    public static Control Create(Catalog data, Character? self, Item item, Texture2D? icon, bool compact = false, bool ownedRequired = true)
    {
        var def = data.Item(item.Template);
        var info = EquipmentComparison.Inspect(self, item, data, ownedRequired);
        int nameSize = compact ? 14 : 16;
        int metaSize = compact ? 11 : 12;
        int statSize = compact ? 11 : 12;
        var box = new VBoxContainer
        {
            Name = "CompactItemCard",
            CustomMinimumSize = new Vector2(Width, 0),
            SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter,
            SizeFlagsVertical = Control.SizeFlags.ShrinkCenter,
            MouseFilter = Control.MouseFilterEnum.Ignore
        };
        box.AddThemeConstantOverride("separation", compact ? 2 : 3);

        var image = Ui.Image(icon, compact ? CompactIconSize : 40);
        image.Name = "ItemIcon";
        image.SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter;
        image.SizeFlagsVertical = Control.SizeFlags.ShrinkCenter;
        box.AddChild(image);

        var name = Centered(def.Name, nameSize, Ui.RarityColor(item.Rarity));
        name.Name = "ItemName";
        box.AddChild(name);

        int skillTotal=item.SkillBonuses.Values.Sum();
        Element actualElement=Items.ElementOf(item,def);
        string rolledMeta=(skillTotal>0?$" · +{skillTotal} skill":"")+(actualElement!=Element.Physical?$" · {actualElement}":"");
        string identity=item.Rarity+(def.Tags.Contains("boss_unique",StringComparer.Ordinal)?" · Signature":def.Tags.Any(x=>x.StartsWith("set:",StringComparison.Ordinal))?" · Set piece":"");
        var metadata = Centered(identity + " · " + Ui.Words(def.Type) + rolledMeta + (self is not null && Items.Equipped(self, item.Id) ? " · Equipped" : ""), metaSize, Ui.Muted);
        metadata.Name = "ItemMeta";
        box.AddChild(metadata);

        IEnumerable<string> blockers = compact ? CompactBlockers(info.Blockers) : info.Blockers;
        foreach (string reason in blockers)
        {
            var blocker = Centered(reason, metaSize, Ui.Danger);
            blocker.Name = "ItemBlocker";
            box.AddChild(blocker);
        }

        if (def.Skill != "" && !info.Blockers.Any(x => x.StartsWith("Requires ", StringComparison.Ordinal)))
        {
            var requirement = Centered($"Requires {data.Skill(def.Skill).Name} {BeginnerProgression.EquipmentRequirement(def)}", metaSize, Ui.Muted);
            requirement.Name = "ItemRequirement";
            box.AddChild(requirement);
        }

        if (!compact && item.SkillBonuses.Count > 0)
        {
            foreach (var skill in item.SkillBonuses.OrderBy(x=>x.Key))
            {
                var bonus = Centered($"+{skill.Value} {data.Skill(skill.Key).Name} level while equipped", metaSize, Ui.Success);
                bonus.Name = "ItemSkillBonus"; box.AddChild(bonus);
            }
        }

        if (info.ComparedWith != "")
        {
            var compared = Centered((compact ? "Compare: " : "Compared with: ") + info.ComparedWith, metaSize, Ui.Muted);
            compared.Name = "ItemComparison";
            box.AddChild(compared);
        }

        if (info.Stats.Count > 0)
        {
            var grid = new GridContainer { Name = "ItemStatTable", Columns = 3, SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
            grid.AddThemeConstantOverride("h_separation", compact ? 4 : 5);
            grid.AddThemeConstantOverride("v_separation", compact ? 1 : 2);
            box.AddChild(grid);

            int statNameWidth = compact ? 160 : 166;
            int statValueWidth = compact ? 62 : 65;
            int statHeight = compact ? 16 : 18;
            void Cell(string text, int width, Color color, string cellName = "", bool wrap = true)
            {
                var label = Centered(text, statSize, color, wrap);
                label.CustomMinimumSize = new Vector2(width, statHeight);
                if (cellName != "") label.Name = cellName;
                grid.AddChild(label);
            }

            if (!compact)
            {
                Cell("Stat", statNameWidth, Ui.Muted);
                Cell("Item", statValueWidth, Ui.Muted, wrap: false);
                Cell("Change", statValueWidth, Ui.Muted, wrap: false);
            }

            foreach (var stat in info.Stats.Take(compact ? CompactStatRows : int.MaxValue))
            {
                Color color = StatColor(stat);
                Cell(StatName(stat.Key), statNameWidth, color, "StatName_" + stat.Key);
                Cell(Number(stat.Value), statValueWidth, color, "StatValue_" + stat.Key, false);
                Cell(stat.Difference is { } difference ? Delta(difference) : "—", statValueWidth, color, "StatDelta_" + stat.Key, false);
            }

            if (compact && info.Stats.Count > CompactStatRows)
            {
                var more = Centered($"+{info.Stats.Count - CompactStatRows} more stats · Select for details", metaSize, Ui.Muted);
                more.Name = "ItemCompactMore";
                box.AddChild(more);
            }
        }

        IEnumerable<string> notices = compact ? info.Notices.Take(1) : info.Notices;
        foreach (string notice in notices)
        {
            var label = Centered(notice, metaSize, Ui.Gold);
            label.Name = "ItemNotice";
            box.AddChild(label);
        }

        var buildLines=BuildDefiningLoot.TooltipLines(item,def,data,self);
        if(!compact&&buildLines.Count>0)
        {
            var effect=Centered(string.Join("\n",buildLines),metaSize,Ui.Gold);
            effect.Name="ItemBuildEffect";box.AddChild(effect);
        }

        if (def.Slot != "" || def.Type == "tool")
        {
            var condition = Centered(
                $"Durability {item.Durability}%" + (def.Slot != "" ? $" · Runes {item.Runes.Count}/{item.Sockets}" : ""),
                metaSize,
                item.Durability == 0 ? Ui.Danger : Ui.Muted);
            condition.Name = "ItemCondition";
            box.AddChild(condition);
        }

        if (!compact && (def.Slot == "weapon" || actualElement != Element.Physical))
        {
            string points=actualElement==Element.Physical?"":$" · {Items.ElementPoints(item,def)} attunement points";
            var element = Centered(actualElement + points + (def.Slot=="weapon"?" · Lower attack interval is faster":""), 11, Ui.Muted);
            element.Name = "ItemElement";
            box.AddChild(element);
        }

        if (item.Quantity > 1)
        {
            var stack = Centered("Stack: " + item.Quantity, metaSize, Ui.Muted);
            stack.Name = "ItemStack";
            box.AddChild(stack);
        }

        if (!compact)
        {
            foreach (var rune in item.Runes) box.AddChild(Centered("Rune: " + data.Item(rune.Template).Name, 12, Ui.Gold));
            if (def.Description != "")
            {
                var description = Centered(def.Description, 12, Ui.Muted);
                description.Name = "ItemDescription";
                description.Visible = false;
                var more = Ui.Button("Description", () => description.Visible = !description.Visible);
                more.Name = "ItemDescriptionToggle";
                more.CustomMinimumSize = new Vector2(0, 28);
                more.SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter;
                box.AddChild(more);
                box.AddChild(description);
            }
        }

        return box;
    }

    public static Control TextTooltip(string text)
    {
        string normalized = text.ReplaceLineEndings("\n").Trim();
        if (normalized.Length > 640) normalized = normalized[..640].TrimEnd() + "…\nOpen the panel for full details.";
        var box = new VBoxContainer { CustomMinimumSize = new Vector2(Width, 0), MouseFilter = Control.MouseFilterEnum.Ignore };
        box.AddThemeConstantOverride("separation", 2);
        box.AddChild(Centered(normalized, 12));
        return box;
    }
}
