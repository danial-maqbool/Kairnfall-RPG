using Godot;
using Kairnfall.Core;
using System.Globalization;

namespace Kairnfall.Client;

/// <summary>Shared, centered item card for inspection, shop previews and hover panels.</summary>
public static class CompactItemCard
{
    public const int Width = 328;
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
        "item_power" => "Power", "item_armor" => "Item armor", "armor" => "Armor bonus" , "weapon_range" => "Range (tiles)",
        "attack_interval" => "Attack interval (s)", _ => Ui.Words(key)
    };
    public static Control Create(Catalog data, Character? self, Item item, Texture2D? icon, bool compact = false, bool ownedRequired = true)
    {
        var def = data.Item(item.Template);
        var info = EquipmentComparison.Inspect(self, item, data, ownedRequired);
        var box = new VBoxContainer { Name = "CompactItemCard", CustomMinimumSize = new Vector2(Width, 0), SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter, MouseFilter = Control.MouseFilterEnum.Ignore };
        box.AddThemeConstantOverride("separation", 3);
        var image = Ui.Image(icon, compact ? 32 : 40); image.SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter; box.AddChild(image);
        box.AddChild(Centered(def.Name, 16, Ui.RarityColor(item.Rarity)));
        box.AddChild(Centered(item.Rarity + " · " + Ui.Words(def.Type) + (self is not null && Items.Equipped(self,item.Id) ? " · Equipped" : ""), 12, Ui.Muted));
        foreach (string reason in info.Blockers)
        {
            var blocker = Centered(reason, 12, Ui.Danger); blocker.Name = "ItemBlocker"; box.AddChild(blocker);
        }
        if (def.Skill != "" && !info.Blockers.Any(x => x.StartsWith("Requires ", StringComparison.Ordinal)))
            box.AddChild(Centered($"Requires {data.Skill(def.Skill).Name} {BeginnerProgression.EquipmentRequirement(def)}", 12, Ui.Muted));
        if (info.ComparedWith != "") box.AddChild(Centered("Compared with: " + info.ComparedWith, 12, Ui.Muted));
        if (info.Stats.Count > 0)
        {
            var grid = new GridContainer { Name = "ItemStatTable", Columns = 3, SizeFlagsHorizontal = Control.SizeFlags.ExpandFill };
            grid.AddThemeConstantOverride("h_separation", 5); grid.AddThemeConstantOverride("v_separation", 2); box.AddChild(grid);
            void Cell(string text, int width, Color color, string name = "")
            {
                var label = Centered(text, 12, color); label.CustomMinimumSize = new Vector2(width, 18);
                if (name != "") label.Name = name;
                grid.AddChild(label);
            }
            Cell("Stat", 166, Ui.Muted); Cell("Item", 65, Ui.Muted); Cell("Change", 65, Ui.Muted);
            foreach (var stat in info.Stats.Take(compact ? 10 : int.MaxValue))
            {
                Color color = StatColor(stat);
                Cell(StatName(stat.Key), 166, color, "StatName_" + stat.Key);
                Cell(Number(stat.Value), 65, color, "StatValue_" + stat.Key);
                Cell(stat.Difference is { } difference ? Delta(difference) : "—", 65, color, "StatDelta_" + stat.Key);
            }
            if (compact && info.Stats.Count > 10) box.AddChild(Centered($"{info.Stats.Count - 10} more stats · Select to inspect", 12, Ui.Muted));
        }
        foreach (string notice in info.Notices) box.AddChild(Centered(notice, 12, Ui.Gold));
        if (def.Slot != "" || def.Type == "tool")
            box.AddChild(Centered($"Durability {item.Durability}%" + (def.Slot != "" ? $" · Runes {item.Runes.Count}/{item.Sockets}" : ""), 12, item.Durability == 0 ? Ui.Danger : Ui.Muted));
        if (def.Slot == "weapon") box.AddChild(Centered(def.Element + " · Lower attack interval is faster", 11, Ui.Muted));
        if (item.Quantity > 1) box.AddChild(Centered("Stack: " + item.Quantity, 12, Ui.Muted));
        if (!compact)
        {
            foreach (var rune in item.Runes) box.AddChild(Centered("Rune: " + data.Item(rune.Template).Name, 12, Ui.Gold));
            if (def.Description != "")
            {
                var description = Centered(def.Description, 12, Ui.Muted); description.Visible = false;
                var more = Ui.Button("Description", () => description.Visible = !description.Visible);
                more.CustomMinimumSize = new Vector2(0, 28); more.SizeFlagsHorizontal = Control.SizeFlags.ShrinkCenter;
                box.AddChild(more); box.AddChild(description);
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
