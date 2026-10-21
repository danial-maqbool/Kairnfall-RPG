using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool classicFullPage;
    private int classicInventoryPage, classicCraftPage;
    private string classicRecipeSearch = "";
    private Action? classicConsumeReadinessTick;
    private bool ClassicPanelsEnabled => FocusHudEnabled && settings.GetValue("hud", "classic_panels", true).AsBool();

    private static PanelContainer ClassicPanel()
    {
        var panel = new PanelContainer();
        panel.AddThemeStyleboxOverride("panel", Ui.Box(new Color(.08f, .15f, .095f, .98f), new Color("89928a"), 6));
        return panel;
    }
    private void OpenClassicPage(string name)
    {
        gameWindow = new PanelContainer { Name = "ClassicOverlay", CustomMinimumSize = new Vector2(414, 0) };
        gameWindow.AddThemeStyleboxOverride("panel", Ui.Box(new Color(0, 0, 0, 0), new Color(0, 0, 0, 0), 0));
        gameWindow.SetMeta("classic_overlay", true); interfaceRoot.AddChild(gameWindow);
        var body = new HBoxContainer { Name = "ClassicOverlayBody" }; body.AddThemeConstantOverride("separation", 6); gameWindow.AddChild(body);
        var inspector = ClassicPanel(); inspector.CustomMinimumSize = new Vector2(198, 0); body.AddChild(inspector);
        var detailScroll = new ScrollContainer { HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled, SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill };
        inspector.AddChild(detailScroll); var details = Ui.Column(detailScroll); details.CustomMinimumSize = new Vector2(184, 0);
        var bag = ClassicPanel(); bag.CustomMinimumSize = new Vector2(210, 0); body.AddChild(bag);
        var contents = Ui.Column(bag); contents.AddThemeConstantOverride("separation", 4);
        var header = Ui.Row(contents); var title = Ui.Label(name == "Crafting" ? "Build & Craft" : "Inventory", 14, Ui.Gold); title.SizeFlagsHorizontal = SizeFlags.ExpandFill; header.AddChild(title);
        var close = Ui.Button("Close", ClosePage); close.Name = "ClassicClose"; close.CustomMinimumSize = new Vector2(0, 28); close.AddThemeFontSizeOverride("font_size", 12); header.AddChild(close);
        var grid = new GridContainer { Columns = 3, Name = "ClassicGrid" }; grid.AddThemeConstantOverride("h_separation", 4); grid.AddThemeConstantOverride("v_separation", 4);
        if (name == "Crafting")
        {
            var search = new LineEdit { Name = "ClassicRecipeSearch", Text = classicRecipeSearch, MaxLength = 128,
                PlaceholderText = "Find recipe or skill", CustomMinimumSize = new Vector2(0, 28),
                TooltipText = "Search recipe, output, skill or station. All words must match; clear to show every recipe." };
            search.AddThemeFontSizeOverride("font_size", 12); contents.AddChild(search);
            search.TextChanged += text =>
            {
                classicRecipeSearch = text; classicCraftPage = 0;
                lastPageStamp = ""; refreshPage?.Invoke();
            };
        }
        contents.AddChild(grid);
        var pager = Ui.Row(contents); var count = Ui.Label("", 12, Ui.Muted); count.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        Button previous = null!, next = null!;
        previous = Ui.Button("<", () => { if (name == "Inventory") classicInventoryPage--; else classicCraftPage--; lastPageStamp = ""; refreshPage?.Invoke(); });
        next = Ui.Button(">", () => { if (name == "Inventory") classicInventoryPage++; else classicCraftPage++; lastPageStamp = ""; refreshPage?.Invoke(); });
        previous.Name = "ClassicPreviousPage"; next.Name = "ClassicNextPage";
        previous.CustomMinimumSize = next.CustomMinimumSize = new Vector2(32, 28);
        pager.AddChild(previous); pager.AddChild(count); pager.AddChild(next);
        if (name == "Inventory") BuildClassicInventory(grid, details, count, previous, next);
        else BuildClassicCrafting(grid, details, count, previous, next);
        SynchronizeModalUx();
    }
    private void OpenFullClassicPage(string name)
    { classicFullPage = true; OpenPage(name); }

    private string ClassicItemActions(Item item)
    {
        var definition = Data.Item(item.Template);
        return "Select / Enter / Space: inspect."
            + (definition.Slot != "" ? "\nDouble-click: equip or unequip." : "")
            + "\nRight-click: item actions."
            + (definition.Type == "tool" ? "\nKeep this tool in your backpack. The best learned tool is selected automatically." : "");
    }

    private string ClassicSlotTooltip(Item item) => ItemDescription(item) + "\n\n" + ClassicItemActions(item);

    private Control ClassicItemTooltip(string id)
    {
        var tooltip = ItemTooltip(id, "inventory");
        if (Snapshot?.Self.Inventory.FirstOrDefault(x => x.Id == id) is { } item)
            tooltip.AddChild(CompactItemCard.Centered(ClassicItemActions(item), 11, Ui.Muted));
        return tooltip;
    }

    private void BuildClassicInventory(GridContainer grid, VBoxContainer details, Label count, Button previous, Button next)
    {
        if (Snapshot is { } initialSnapshot)
        {
            int initial = initialSnapshot.Self.Inventory.FindIndex(x => x.Id == selectedItem);
            if (initial >= 0) classicInventoryPage = initial / 15;
        }
        string layout = "", inspected = "", detailStamp = ""; int amountValue = 1; SpinBox? amount = null;
        Button? consumeButton = null; Label? consumeReadiness = null;
        var slots = new Dictionary<string, ClassicItemSlot>(StringComparer.Ordinal);
        void UpdateConsumeReadiness()
        {
            if (closing || gameWindow is null || !GodotObject.IsInstanceValid(details) || details.IsQueuedForDeletion())
            { classicConsumeReadinessTick = null; return; }
            if (consumeButton is null || consumeReadiness is null || !GodotObject.IsInstanceValid(consumeButton)
                || consumeButton.IsQueuedForDeletion() || Snapshot is not { } current) return;
            var item = current.Self.Inventory.FirstOrDefault(x => x.Id == inspected);
            string problem = ClassicConsumeRules.Problem(current.Self, item, Data, current.Time);
            consumeButton.Disabled = !Online || actionBusy || problem != "";
            consumeButton.TooltipText = problem;
            consumeReadiness.Text = problem; consumeReadiness.Visible = problem != "";
        }
        // The inventory layout stamp intentionally omits health, stamina and time.
        // Refresh eligibility separately so normal snapshots never rebuild editors.
        classicConsumeReadinessTick = UpdateConsumeReadiness;
        void Render()
        {
            if (Snapshot is not { } snap) return;
            var self = snap.Self; var items = self.Inventory.ToArray();
            int pages = Math.Max(1, (items.Length + 14) / 15); classicInventoryPage = Math.Clamp(classicInventoryPage, 0, pages - 1);
            count.Text = (classicInventoryPage + 1) + "/" + pages + " · " + items.Length + "/" + Items.InventoryCapacity;
            previous.Disabled = classicInventoryPage == 0; next.Disabled = classicInventoryPage >= pages - 1;
            if (!items.Any(x => x.Id == selectedItem)) selectedItem = items.FirstOrDefault()?.Id ?? "";
            var visible = items.Skip(classicInventoryPage * 15).Take(15).ToArray(); string stamp = classicInventoryPage + "|" + string.Join(";", visible.Select(x => x.Id));
            if (!visible.Any(x => x.Id == selectedItem)) selectedItem = visible.FirstOrDefault()?.Id ?? "";
            if (stamp != layout)
            {
                Ui.Clear(grid); slots.Clear();
                foreach (var item in visible)
                {
                    string id = item.Id;
                    var slot = new ClassicItemSlot { Name = "ClassicItem_" + id, Icon = Assets.Icon(item.Template), Item = item,
                        TooltipFactory = () => ClassicItemTooltip(id),
                        Clicked = () => { selectedItem = id; selectedBag = "inventory"; lastPageStamp = ""; refreshPage?.Invoke(); },
                        Activated = () =>
                        {
                            if (Snapshot?.Self.Inventory.FirstOrDefault(x => x.Id == id) is not { } current) return;
                            selectedItem = id; selectedBag = "inventory"; lastPageStamp = ""; refreshPage?.Invoke();
                            if (Data.Item(current.Template).Slot != "") ToggleEquipment(id);
                        },
                        ContextRequested = at =>
                        {
                            if (Snapshot?.Self.Inventory.FirstOrDefault(x => x.Id == id) is not { } current) return;
                            selectedItem = id; selectedBag = "inventory"; lastPageStamp = ""; refreshPage?.Invoke();
                            ItemContext(current, "inventory", at);
                        } };
                    grid.AddChild(slot); slots[id] = slot;
                }
                for (int i = visible.Length; i < 15; i++) grid.AddChild(new ClassicItemSlot { FocusMode = FocusModeEnum.None });
                layout = stamp;
            }
            foreach (var item in visible)
            {
                var slot = slots[item.Id]; slot.Item = item; slot.Selected = selectedItem == item.Id;
                slot.ItemElement = Items.ElementOf(item, Data.Item(item.Template));
                slot.Equipped = Items.Equipped(self, item.Id); slot.TooltipText = ClassicSlotTooltip(item); slot.QueueRedraw();
            }
            if (amount is not null && GodotObject.IsInstanceValid(amount)) amountValue = (int)amount.Value;
            var selected = items.FirstOrDefault(x => x.Id == selectedItem);
            string nextDetails = selected is null ? "empty" : System.Text.Json.JsonSerializer.Serialize(selected, Wire.Json)
                + "|" + Items.Equipped(self, selected.Id) + "|" + ExperienceRules.EquipmentProblem(self, selected, Data)
                + "|" + Online + "|" + actionBusy;
            // Clock/health updates must not destroy a focused amount editor or a pressed button.
            if (nextDetails == detailStamp) { UpdateConsumeReadiness(); return; }
            detailStamp = nextDetails; Ui.Clear(details); consumeButton = null; consumeReadiness = null;
            if (selected is null) { details.AddChild(Ui.Label("Backpack is empty.", 14, Ui.Muted, true)); return; }
            if (inspected != selected.Id) amountValue = 1;
            inspected = selected.Id; var def = Data.Item(selected.Template);
            details.AddChild(Ui.Image(Assets.Icon(selected.Template), 56));
            details.AddChild(Ui.Label(def.Name, 15, Ui.RarityColor(selected.Rarity), true));
            Element element = Items.ElementOf(selected, def);
            var identity = Ui.Label(selected.Rarity + " · " + Ui.Words(def.Type) + " · " + element, 12, Ui.Muted, true);
            identity.Name = "ClassicItemIdentity"; details.AddChild(identity);
            if (def.Skill != "")
            {
                int requirement = def.Slot != "" ? BeginnerProgression.EquipmentRequirement(def) : def.Requirement;
                var requirementLabel = Ui.Label("Requires " + Data.Skill(def.Skill).Name + " " + requirement, 12, Ui.Muted, true);
                requirementLabel.Name = "ClassicItemRequirement"; details.AddChild(requirementLabel);
            }
            if (def.Slot != "" || def.Type == "tool")
            {
                var durability = Ui.Label("Durability " + selected.Durability + "%", 12, selected.Durability <= 0 ? Ui.Danger : Ui.Muted, true);
                durability.Name = "ClassicItemDurability"; details.AddChild(durability);
            }
            var description = Ui.Label(def.Description, 12, Ui.Muted, true); description.MaxLinesVisible = 4; details.AddChild(description);
            details.AddChild(Ui.Label(selected.Quantity + " owned" + (Items.Equipped(self, selected.Id) ? " · equipped" : ""), 12, Ui.Gold, true));
            if (def.Slot != "") BuildEquipmentAction(details, selected, "inventory");
            if (def.Type is "food" or "potion" or "scroll")
            {
                string id = selected.Id;
                consumeButton = Ui.Button("Use", () =>
                {
                    if (Snapshot is not { } current || current.Self.Inventory.FirstOrDefault(x => x.Id == id) is not { } owned || !Online || actionBusy) return;
                    string problem = ClassicConsumeRules.Problem(current.Self, owned, Data, current.Time);
                    if (problem != "") { Notify(problem, true); return; }
                    Send("consume", item: id);
                });
                consumeButton.Name = "ClassicUseItem"; details.AddChild(consumeButton);
                consumeReadiness = Ui.Label("", 12, Ui.Danger, true); consumeReadiness.Name = "ClassicConsumeReadiness";
                details.AddChild(consumeReadiness); UpdateConsumeReadiness();
            }
            if (def.Type is "book" or "treasure_map") details.AddChild(Ui.Button("Read", () => Send("read", item: selected.Id), !Online || actionBusy));
            var dropLabel = Ui.Label("Drop amount", 12, Ui.Muted); dropLabel.TooltipText = "Ground loot stays reserved for you for 60s, then becomes public. It expires after " + LootPile.LifetimeSeconds + "s. Equipped and quest items cannot be dropped."; details.AddChild(dropLabel);
            amount = new SpinBox { Name = "ClassicDropAmount", MinValue = 1, MaxValue = selected.Quantity, Step = 1, Value = Math.Clamp(amountValue, 1, selected.Quantity), Rounded = true, CustomMinimumSize = new Vector2(0, 30) }; details.AddChild(amount);
            bool cannotDrop = !Online || actionBusy || Items.Equipped(self, selected.Id) || def.Type == "quest";
            var drop = Ui.Button("Drop", () => Send("drop", item: selected.Id, amount: Math.Clamp((int)amount!.Value, 1, selected.Quantity)), cannotDrop);
            drop.TooltipText = dropLabel.TooltipText; details.AddChild(drop);
            var dropAll = Ui.Button("Drop all · " + selected.Quantity, () => Send("drop", item: selected.Id, amount: selected.Quantity), cannotDrop);
            dropAll.TooltipText = dropLabel.TooltipText; details.AddChild(dropAll);
            details.AddChild(Ui.Button("Full item details", () => OpenFullClassicPage("Inventory")));
        }
        refreshPage = Render; selectedBag = "inventory"; Render();
    }

    private void BuildClassicCrafting(GridContainer grid, VBoxContainer details, Label count, Button previous, Button next)
    {
        var allRecipes = Data.Recipes.OrderBy(x => x.Requirement).ThenBy(x => x.Name, StringComparer.Ordinal).ToArray();
        int initial = Array.FindIndex(allRecipes, x => x.Id == selectedRecipe);
        if (initial >= 0) classicCraftPage = initial / 15;
        string layout = "", detailStamp = ""; var slots = new Dictionary<string, ClassicItemSlot>(StringComparer.Ordinal);
        void Render()
        {
            if (Snapshot is not { } snap) return;
            var words = classicRecipeSearch.Split((char[]?)null, StringSplitOptions.RemoveEmptyEntries);
            var recipes = allRecipes.Where(recipe => words.All(word =>
                (recipe.Name + " " + Data.Item(recipe.Output).Name + " " + Data.Skill(recipe.Skill).Name + " " + Ui.Words(recipe.Station))
                    .Contains(word, StringComparison.OrdinalIgnoreCase))).ToArray();
            int pages = Math.Max(1, (recipes.Length + 14) / 15); classicCraftPage = Math.Clamp(classicCraftPage, 0, pages - 1);
            count.Text = recipes.Length == 0 ? "0 recipes" : (classicCraftPage + 1) + "/" + pages + " · " + recipes.Length;
            previous.Disabled = classicCraftPage == 0; next.Disabled = classicCraftPage >= pages - 1;
            if (!recipes.Any(x => x.Id == selectedRecipe)) selectedRecipe = recipes.FirstOrDefault()?.Id ?? "";
            var visible = recipes.Skip(classicCraftPage * 15).Take(15).ToArray(); string stamp = classicCraftPage + "|" + string.Join(";", visible.Select(x => x.Id));
            if (!visible.Any(x => x.Id == selectedRecipe)) selectedRecipe = visible.FirstOrDefault()?.Id ?? "";
            if (stamp != layout)
            {
                Ui.Clear(grid); slots.Clear();
                foreach (var recipe in visible)
                {
                    string id = recipe.Id;
                    var slot = new ClassicItemSlot { Name = "ClassicRecipe_" + id, Icon = Assets.Icon(recipe.Output), Item = new Item { Id = id, Template = recipe.Output, Quantity = recipe.Quantity },
                        Clicked = () => { selectedRecipe = id; lastPageStamp = ""; refreshPage?.Invoke(); } };
                    // A recipe slot only inspects; double-click never submits a craft.
                    slot.Activated = slot.Clicked;
                    grid.AddChild(slot); slots[id] = slot;
                }
                for (int i = visible.Length; i < 15; i++) grid.AddChild(new ClassicItemSlot { FocusMode = FocusModeEnum.None });
                layout = stamp;
            }
            foreach (var recipe in visible)
            {
                var slot = slots[recipe.Id]; slot.Selected = selectedRecipe == recipe.Id;
                slot.ItemElement = Data.Item(recipe.Output).Element;
                slot.TooltipText = recipe.Name + "\nSelect / Enter / Space / double-click: inspect recipe.\nUse Craft or Build after reviewing the requirements.";
                slot.QueueRedraw();
            }
            var selected = recipes.FirstOrDefault(x => x.Id == selectedRecipe);
            if (selected is null)
            {
                if (detailStamp != "empty")
                {
                    Ui.Clear(details); details.AddChild(Ui.Label("No matching recipes", 15, Ui.Gold, true));
                    details.AddChild(Ui.Label("Try an item or skill name, or clear the search to see every recipe.", 12, Ui.Muted, true));
                    detailStamp = "empty";
                }
                return;
            }
            string problem = ClassicCraftRules.Problem(snap.Self, selected, Data, snap.Time, ClientAtStation(selected.Station), Online && !actionBusy);
            string nextDetails = selected.Id + "|" + problem + "|" + string.Join(";", selected.Ingredients.Keys.Select(x => x + ":" + Items.Count(snap.Self, x)));
            if (nextDetails == detailStamp) return;
            detailStamp = nextDetails; Ui.Clear(details);
            var def = Data.Item(selected.Output); bool structure = def.Type == "structure";
            details.AddChild(Ui.Image(Assets.Icon(selected.Output), 56)); details.AddChild(Ui.Label(selected.Name, 15, Ui.Gold, true));
            var description = Ui.Label(def.Description, 12, Ui.Muted, true); description.MaxLinesVisible = 3; details.AddChild(description);
            details.AddChild(Ui.Label(Data.Skill(selected.Skill).Name + " " + selected.Requirement + " · " + Ui.Words(selected.Station), 12, Ui.Muted, true));
            foreach (var ingredient in selected.Ingredients)
            {
                int owned = Items.Count(snap.Self, ingredient.Key);
                details.AddChild(Ui.Label(owned + "/" + ingredient.Value + " " + Data.Item(ingredient.Key).Name, 12, owned >= ingredient.Value ? Ui.Success : Ui.Danger, true));
            }
            details.AddChild(Ui.Button(structure ? "Build" : "Craft", () =>
            {
                if (Snapshot is not { } current || ClassicCraftRules.Problem(current.Self, selected, Data, current.Time, ClientAtStation(selected.Station), Online && !actionBusy) != "") return;
                if (structure) { structureRecipe = selected.Id; placement = "build"; ClosePage(); Notify("Choose clear wilderness within three tiles. The realm validates placement and materials."); }
                else Send("craft", item: selected.Id, amount: 1);
            }, problem != ""));
            var readiness = Ui.Label(problem, 12, Ui.Danger, true); readiness.Name = "ClassicCraftReadiness"; details.AddChild(readiness);
            details.AddChild(Ui.Button("Info", () => Notify(selected.Name + " · " + string.Join(", ", selected.Ingredients.Select(x => x.Value + " " + Data.Item(x.Key).Name)) + ". " + def.Description)));
            details.AddChild(Ui.Button("Full crafting guide", () => OpenFullClassicPage("Crafting")));
        }
        refreshPage = Render; Render();
    }
}
