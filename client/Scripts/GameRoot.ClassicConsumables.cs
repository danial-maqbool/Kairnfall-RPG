using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public static class ClassicConsumeRules
{
    public static string Problem(Character self, Item? item, Catalog data, double time)
    {
        if (self.Health <= 0) return "Respawn before using items.";
        if (item is null || item.Quantity < 1 || !self.Inventory.Any(x => x.Id == item.Id)) return "No item in your backpack.";
        var def = data.Item(item.Template); var stats = CombatMath.Stats(self, data);
        if (def.Type is not ("food" or "potion" or "scroll")) return "This item cannot be consumed.";
        string cooldown = def.Effect == "food" ? "food" : "potion";
        if (self.Cooldowns.GetValueOrDefault(cooldown) > time) return "Recovering · " + (self.Cooldowns[cooldown] - time).ToString("0.0") + "s";
        return def.Effect switch
        {
            "heal" when self.Health >= stats.Health => "Your health is full.",
            "mana" when self.Mana >= stats.Mana => "Your mana is full.",
            "food" when self.ClassicTutorial is not { Food: < 100 } && self.Health >= stats.Health && self.Stamina >= stats.Stamina => "You do not need food yet.",
            "purge" when !self.Statuses.Any(x => x.Kind is "poison" or "burn" or "curse") => "No harmful condition to remove.",
            "heal" or "mana" or "food" or "purge" => "",
            _ => "This consumable effect is unavailable."
        };
    }
}

public partial class GameRoot
{
    private readonly List<(Button Button, string Effect)> classicConsumables = [];
    private void BuildClassicConsumables()
    {
        var grid = new GridContainer { Name = "ClassicQuickItems", Columns = 2, AnchorLeft = 1, AnchorRight = 1,
            AnchorTop = .5f, AnchorBottom = .5f, OffsetLeft = -122, OffsetRight = -16, OffsetTop = -92, OffsetBottom = 14 };
        grid.AddThemeConstantOverride("h_separation", 4); grid.AddThemeConstantOverride("v_separation", 4);
        focusHud.AddChild(grid);
        foreach (string effect in new[] { "heal", "mana", "food", "purge" })
        {
            string selected = effect;
            var button = Ui.Button("", () =>
            {
                if (!GameplayInputAllowed || actionBusy || Snapshot is not { } snapshot) return;
                var item = snapshot.Self.Inventory.FirstOrDefault(x => Data.Item(x.Template).Effect == selected && Data.Item(x.Template).Type is "food" or "potion" or "scroll");
                if (ClassicConsumeRules.Problem(snapshot.Self, item, Data, snapshot.Time) != "" || item is null) return;
                StopCombatInput(); Send("consume", item: item.Id);
            });
            button.Name = "ClassicQuick_" + effect; button.FocusMode = FocusModeEnum.None;
            button.CustomMinimumSize = new Vector2(50, 50); button.ExpandIcon = true; button.IconAlignment = HorizontalAlignment.Center;
            button.AddThemeConstantOverride("icon_max_width", 30); button.AddThemeFontSizeOverride("font_size", 12);
            grid.AddChild(button); classicConsumables.Add((button, effect));
        }
        var crafting = Ui.Button("Build & Craft", () => OpenPage("Crafting")); crafting.Name = "ClassicOpenCrafting"; crafting.FocusMode = FocusModeEnum.None;
        crafting.AnchorLeft = crafting.AnchorRight = 1; crafting.AnchorTop = crafting.AnchorBottom = .5f;
        crafting.OffsetLeft = -158; crafting.OffsetRight = -16; crafting.OffsetTop = 22; crafting.OffsetBottom = 58; focusHud.AddChild(crafting);
    }
    private void UpdateClassicConsumables()
    {
        if (Snapshot is not { } snapshot) return;
        foreach (var (button, effect) in classicConsumables)
        {
            var item = snapshot.Self.Inventory.FirstOrDefault(x => Data.Item(x.Template).Effect == effect && Data.Item(x.Template).Type is "food" or "potion" or "scroll");
            var def = item is null ? Data.Items.FirstOrDefault(x => x.Effect == effect && x.Type is "food" or "potion" or "scroll") : Data.Item(item.Template);
            string problem = ClassicConsumeRules.Problem(snapshot.Self, item, Data, snapshot.Time);
            button.Icon = def is null ? null : Assets.Icon(def.Id); button.Text = item is null ? "0" : item.Quantity.ToString();
            button.Disabled = !GameplayInputAllowed || actionBusy || problem != "";
            string benefit = effect == "food" ? "Uses one. Restores up to 20 stamina and grants 12s health regeneration."
                : effect == "heal" ? "Uses one. Restores health." : effect == "mana" ? "Uses one. Restores mana." : "Uses one. Removes poison, burn and curse.";
            if (effect == "food" && snapshot.Self.ClassicTutorial is not null && Data.ClassicTutorial is { } tuning)
                benefit += " Restores up to " + tuning.FoodRestore.ToString("0.#") + " Food.";
            button.TooltipText = (def?.Name ?? Ui.Words(effect)) + "\n" + benefit + (problem == "" ? "" : "\n" + problem);
        }
    }
}
