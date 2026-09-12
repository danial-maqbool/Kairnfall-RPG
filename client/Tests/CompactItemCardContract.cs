using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client.Tests;

/// <summary>Native layout regression checks for compact item hover cards.</summary>
public partial class CompactItemCardContract : Control
{
    private int checks;

    private void Need(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
        checks++;
        GD.Print("PASS COMPACT ITEM CARD: " + message);
    }

    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);

    private async Task Layout(Control card, Vector2 position)
    {
        AddChild(card);
        card.Position = position;
        await Frame();
        Vector2 minimum = card.GetCombinedMinimumSize();
        card.Size = new Vector2(Mathf.Max(CompactItemCard.Width, minimum.X), minimum.Y);
        await Frame();
        minimum = card.GetCombinedMinimumSize();
        card.Size = new Vector2(Mathf.Max(CompactItemCard.Width, minimum.X), minimum.Y);
        await Frame();
    }

    private static void Release(Control card)
    {
        if (!GodotObject.IsInstanceValid(card)) return;
        if (card.GetParent() is not null) card.GetParent().RemoveChild(card);
        card.Free();
    }

    private void VerifyCompactStructure(Control card, string kind)
    {
        var direct = card.GetChildren().OfType<Control>().Where(x => x.Visible).OrderBy(x => x.Position.Y).ToArray();
        Need(direct.Length >= 3, $"Compact {kind} card has visible content");
        Need(card.GetThemeConstant("separation") <= 2, $"Compact {kind} card uses tight internal separation");
        Need(direct[0].Position.Y <= 1, $"Compact {kind} card has no top spacer");
        for (int index = 1; index < direct.Length; index++)
        {
            float gap = direct[index].Position.Y - (direct[index - 1].Position.Y + direct[index - 1].Size.Y);
            Need(gap >= -1, $"Compact {kind} rows do not overlap");
            Need(gap <= card.GetThemeConstant("separation") + 1, $"Compact {kind} card has no empty vertical spacer");
        }
        float bottom = direct[^1].Position.Y + direct[^1].Size.Y;
        Need(bottom <= card.Size.Y + 1, $"Compact {kind} content stays inside card height");

        var controls = card.FindChildren("*", "Control", true, false).OfType<Control>().ToArray();
        Need(controls.All(x => x.Visible), $"Compact {kind} card creates no hidden layout rows");
        Need(!card.FindChildren("*", "Button", true, false).Any(), $"Compact {kind} card includes no full-detail controls");

        var labels = card.FindChildren("*", "Label", true, false).OfType<Label>().ToArray();
        Need(labels.All(x => !x.ClipText && x.GetVisibleLineCount() == x.GetLineCount()), $"Compact {kind} card does not clip text");
        Need(labels.All(x => x.AutowrapMode != TextServer.AutowrapMode.Off || x.GetMinimumSize().X <= x.Size.X + 1), $"Compact {kind} text stays inside assigned width");
        Need(labels.All(x => !string.IsNullOrWhiteSpace(x.Text)), $"Compact {kind} card creates no blank metadata rows");

        var icon = card.FindChild("ItemIcon", true, false) as TextureRect;
        Need(icon is not null && icon.Size.X <= CompactItemCard.CompactIconSize + 1 && icon.Size.Y <= CompactItemCard.CompactIconSize + 1, $"Compact {kind} icon stays inside its icon box");
        Need(icon is not null && icon.Position.X >= -1 && icon.Position.X + icon.Size.X <= card.Size.X + 1, $"Compact {kind} icon stays inside card width");

        var name = card.FindChild("ItemName", true, false) as Label;
        var meta = card.FindChild("ItemMeta", true, false) as Label;
        Need(name is not null && name.GetThemeFontSize("font_size") >= 14, $"Compact {kind} name remains readable");
        Need(meta is not null && meta.GetThemeFontSize("font_size") >= 11, $"Compact {kind} metadata remains readable");

        var grid = card.FindChild("ItemStatTable", true, false) as GridContainer;
        if (grid is not null)
        {
            var cells = grid.GetChildren().OfType<Control>().ToArray();
            Need(cells.Length <= CompactItemCard.CompactStatRows * 3, $"Compact {kind} card caps stat rows");
            for (int index = 0; index + 2 < cells.Length; index += 3)
            {
                Need(cells[index].Position.X + cells[index].Size.X <= cells[index + 1].Position.X + 1, $"Compact {kind} stat name does not overlap its value");
                Need(cells[index + 1].Position.X + cells[index + 1].Size.X <= cells[index + 2].Position.X + 1, $"Compact {kind} stat value does not overlap its comparison");
            }
        }

        Vector2 minimum = card.GetCombinedMinimumSize();
        foreach (Vector2 viewport in new[] { new Vector2(1024, 720), new Vector2(1280, 720), new Vector2(1920, 1080) })
            Need(minimum.X + 24 <= viewport.X && minimum.Y + 24 <= viewport.Y, $"Compact {kind} card fits {viewport.X:0}x{viewport.Y:0} with edge-clamp room");
    }

    public override async void _Ready()
    {
        try
        {
            Theme = Ui.BuildTheme();
            var data = PixelAssets.LoadCatalog();
            var supported = data.Items
                .GroupBy(x => x.Type, StringComparer.Ordinal)
                .OrderBy(x => x.Key, StringComparer.Ordinal)
                .Select(x => (Kind: x.Key, Template: x.First().Id))
                .ToArray();

            Need(supported.Any(x => x.Kind == "weapon"), "Coverage includes weapons");
            Need(supported.Any(x => x.Kind == "armor"), "Coverage includes armor");
            Need(supported.Any(x => x.Kind is "potion" or "food" or "scroll"), "Coverage includes consumables");
            Need(supported.Any(x => x.Kind is "material" or "ore" or "wood" or "herb"), "Coverage includes materials");
            Need(supported.Any(x => x.Kind == "rune"), "Coverage includes runes");

            foreach (var entry in supported)
            {
                var definition = data.Item(entry.Template);
                var item = Items.Create(data, entry.Template);
                if (definition.StackMax > 1) item.Quantity = Math.Min(7, definition.StackMax);
                var compact = CompactItemCard.Create(data, null, item, null, true, false);
                try
                {
                    await Layout(compact, new Vector2(8, 8));
                    VerifyCompactStructure(compact, entry.Kind);
                }
                finally { Release(compact); }
            }

            foreach (string kind in new[] { "weapon", "armor", "potion", "material", "rune", "tool" })
            {
                var definition = data.Items.FirstOrDefault(x => x.Type == kind);
                if (definition is null) continue;
                var item = Items.Create(data, definition.Id);
                var compact = CompactItemCard.Create(data, null, item, null, true, false);
                var full = CompactItemCard.Create(data, null, item, null, false, false);
                try
                {
                    await Layout(compact, new Vector2(8, 8));
                    await Layout(full, new Vector2(CompactItemCard.Width + 48, 8));
                    Need(compact.GetCombinedMinimumSize().Y + 12 <= full.GetCombinedMinimumSize().Y, $"Compact {kind} card is visibly shorter than full detail");
                    var compactName = compact.FindChild("ItemName", true, false) as Label;
                    var fullName = full.FindChild("ItemName", true, false) as Label;
                    Need(compactName is not null && fullName is not null && compactName.GetThemeFontSize("font_size") < fullName.GetThemeFontSize("font_size"), $"Compact {kind} name typography is smaller than full detail");
                    Need(full.FindChild("ItemDescriptionToggle", true, false) is not null || string.IsNullOrWhiteSpace(definition.Description), $"Full {kind} detail retains its description control");
                    int statCount = EquipmentComparison.Inspect(null, item, data, false).Stats.Count;
                    var compactGrid = compact.FindChild("ItemStatTable", true, false) as GridContainer;
                    var fullGrid = full.FindChild("ItemStatTable", true, false) as GridContainer;
                    if (statCount > 0)
                    {
                        Need(compactGrid is not null && compactGrid.GetChildCount() == Math.Min(statCount, CompactItemCard.CompactStatRows) * 3, $"Compact {kind} card renders only its bounded stat subset");
                        Need(fullGrid is not null && fullGrid.GetChildCount() == (statCount + 1) * 3, $"Full {kind} detail retains every stat and the table header");
                    }
                }
                finally
                {
                    Release(compact);
                    Release(full);
                }
            }

            var signatureDef=data.Items.First(x=>x.Tags.Contains("boss_unique",StringComparer.Ordinal));
            var signatureItem=Items.Create(data,signatureDef.Id,1,Rarity.Relic);
            var signatureCard=CompactItemCard.Create(data,null,signatureItem,null,false,false);
            try
            {
                await Layout(signatureCard,new Vector2(8,8));
                var effects=signatureCard.FindChildren("ItemBuildEffect","Label",true,false).OfType<Label>().ToArray();
                Need(effects.Any(x=>x.Text.Contains("SIGNATURE EFFECT",StringComparison.Ordinal)),"Full signature item card renders its authored special effect");
                Need(effects.Any(x=>x.Text.Contains("TARGET FARM",StringComparison.Ordinal)),"Full signature item card renders its boss source");
            }
            finally { Release(signatureCard); }

            var longData = Wire.Copy(data);
            var longDefinition = longData.Items.First(x => x.Type == "weapon");
            longDefinition.Name = "Tempered Long-Form Expeditionary Arming Sword of the Northern Watch and the Emberward Company";
            var longItem = Items.Create(longData, longDefinition.Id);
            var longCard = CompactItemCard.Create(longData, null, longItem, null, true, false);
            try
            {
                await Layout(longCard, new Vector2(8, 8));
                var name = (Label)longCard.FindChild("ItemName", true, false)!;
                Need(name.GetLineCount() > 1 && name.GetVisibleLineCount() == name.GetLineCount(), "Long item names wrap without clipping");
                Need(longCard.GetCombinedMinimumSize().X <= CompactItemCard.Width + 1, "Long item names do not expand compact card width");
                VerifyCompactStructure(longCard, "long-name weapon");
            }
            finally { Release(longCard); }

            var rareDefinition = data.Items.First(x => x.Type == "weapon");
            var rare = Items.Create(data, rareDefinition.Id, 1, Rarity.Rare);
            rare.Affixes =
            [
                new() { Stat = "vitality", Value = 1 },
                new() { Stat = "luck", Value = 2 },
                new() { Stat = "resolve", Value = 3 },
                new() { Stat = "spirit", Value = 4 },
                new() { Stat = "dexterity", Value = 5 },
                new() { Stat = "intellect", Value = 6 },
                new() { Stat = "strength", Value = 7 },
                new() { Stat = "crit", Value = 8 },
                new() { Stat = "haste", Value = 9 },
                new() { Stat = "mana", Value = 10 }
            ];
            var rareCompact = CompactItemCard.Create(data, null, rare, null, true, false);
            var rareFull = CompactItemCard.Create(data, null, rare, null, false, false);
            try
            {
                await Layout(rareCompact, new Vector2(8, 8));
                await Layout(rareFull, new Vector2(CompactItemCard.Width + 48, 8));
                int statCount = EquipmentComparison.Inspect(null, rare, data, false).Stats.Count;
                var compactGrid = (GridContainer)rareCompact.FindChild("ItemStatTable", true, false)!;
                var fullGrid = (GridContainer)rareFull.FindChild("ItemStatTable", true, false)!;
                Need(compactGrid.GetChildCount() == Math.Min(statCount, CompactItemCard.CompactStatRows) * 3, "Rare compact equipment renders only the bounded stat subset");
                Need(fullGrid.GetChildCount() == (statCount + 1) * 3, "Rare full-detail equipment retains every stat and the table header");
                Need(rareCompact.FindChild("ItemCompactMore", true, false) is not null, "Rare compact equipment reports omitted stats in one summary row");
                Need(rareCompact.GetCombinedMinimumSize().Y + 24 < rareFull.GetCombinedMinimumSize().Y, "Rare metadata cannot expand compact mode to full-detail height");
                VerifyCompactStructure(rareCompact, "rare weapon");
            }
            finally
            {
                Release(rareCompact);
                Release(rareFull);
            }

            foreach (Vector2I size in new[] { new Vector2I(1024, 720), new Vector2I(1280, 720), new Vector2I(1920, 1080) })
            {
                GetWindow().Size = size;
                GetWindow().ContentScaleSize = size;
                await Frame();
                var edgeItem = Items.Create(data, data.Items.First(x => x.Type == "rune").Id);
                var edgeCard = CompactItemCard.Create(data, null, edgeItem, null, true, false);
                try
                {
                    await Layout(edgeCard, Vector2.Zero);
                    edgeCard.Position = new Vector2(size.X - edgeCard.Size.X - 12, size.Y - edgeCard.Size.Y - 12);
                    await Frame();
                    Rect2 rect = edgeCard.GetGlobalRect();
                    Need(rect.Position.X >= 0 && rect.Position.Y >= 0 && rect.End.X <= size.X && rect.End.Y <= size.Y, $"Compact card remains fully inside the {size.X}x{size.Y} viewport near the lower-right edge");
                }
                finally { Release(edgeCard); }
            }

            GD.Print($"COMPACT_ITEM_CARD_CONTRACT: {checks} checks passed.");
            GetTree().Quit();
        }
        catch (Exception error)
        {
            GD.PushError("COMPACT_ITEM_CARD_CONTRACT: " + error);
            GetTree().Quit(1);
        }
    }
}
