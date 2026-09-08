using Godot;
using Kairnfall.Core;
using System.Text;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool inventoryByName = true;
    private bool NearNpc(NpcDef npc) => Snapshot is { } s && s.Self.Zone == npc.Zone && s.Self.Position.Distance(npc.Position) <= 3 && WorldMap.LineOfSight(Data.Zone(npc.Zone), s.Self.Position, npc.Position);
    private bool NearRole(string role) => Data.Npcs.Any(x => x.Role == role && NearNpc(x));
    private int Quantity(SpinBox control, int maximum = 999) => Math.Clamp((int)control.Value, 1, maximum);
    private SpinBox Amount(Node parent, int maximum)
    {
        var row = Ui.Row(parent); row.AddChild(Ui.Label("Quantity", 14, Ui.Muted));
        var amount = new SpinBox { MinValue = 1, MaxValue = Math.Max(1, maximum), Step = 1, Value = 1, CustomMinimumSize = new Vector2(120, 32) }; row.AddChild(amount); return amount;
    }
    private void Confirm(string title, string message, Action action)
    {
        var dialog = new ConfirmationDialog { Title = title, DialogText = message, Theme = Theme, MinSize = new Vector2I(460, 150) };
        AddChild(dialog); dialog.Confirmed += () => { action(); dialog.QueueFree(); }; dialog.Canceled += dialog.QueueFree; dialog.PopupCentered();
    }

    private string ItemDescription(Item item, bool compare = true)
    {
        var def = Data.Item(item.Template); var text = new StringBuilder();
        text.AppendLine(def.Name).AppendLine(item.Rarity + " · " + Ui.Words(def.Type));
        if (def.Power > 0) text.AppendLine($"Power: {def.Power * (1 + .1 * (int)item.Rarity):0.0}");
        if (def.Armor > 0) text.AppendLine($"Armor: {def.Armor * (1 + .1 * (int)item.Rarity):0.0}");
        if (def.Slot == "weapon") text.AppendLine($"Range: {def.Range:0.0} tiles · {def.Element}");
        foreach (var stat in def.Stats) text.AppendLine($"{stat.Value:+0.0;-0.0;0} {Ui.Words(stat.Key)}");
        foreach (var affix in item.Affixes) text.AppendLine($"{affix.Value:+0.0;-0.0;0} {Ui.Words(affix.Stat)}");
        if (def.Skill != "") text.AppendLine($"Requires {Data.Skill(def.Skill).Name} {def.Requirement}");
        if (def.Slot != "") text.AppendLine($"Durability: {item.Durability}% · Runes: {item.Runes.Count}/{item.Sockets}");
        foreach (var rune in item.Runes) text.AppendLine("Rune: " + Data.Item(rune.Template).Name);
        text.AppendLine().Append(def.Description);
        if (compare && Snapshot is { } s && def.Slot != "" && !Items.Equipped(s.Self, item.Id) && s.Self.Inventory.Any(x => x.Id == item.Id))
        {
            try
            {
                var projected = Wire.Copy(s.Self); var before = CombatMath.Stats(projected, Data); Items.Equip(projected, item.Id, Data); var after = CombatMath.Stats(projected, Data);
                text.AppendLine().AppendLine().AppendLine("Compared with current equipment:");
                foreach (var value in new[] { ("Health", after.Health - before.Health), ("Physical power", after.Physical - before.Physical), ("Spell power", after.Spell - before.Spell), ("Armor", after.Armor - before.Armor), ("Mana", after.Mana - before.Mana) })
                    if (Math.Abs(value.Item2) > .01) text.AppendLine($"{value.Item1}: {value.Item2:+0.0;-0.0;0}");
            }
            catch (RuleException) { text.AppendLine().Append("You cannot equip this item yet."); }
        }
        return text.ToString();
    }

    private ItemSlot MakeSlot(Item item, string bag, Action? clicked = null)
    {
        return new ItemSlot
        {
            Item = item,
            Icon = Assets.Icon(item.Template),
            Bag = bag,
            Equipped = Snapshot is { } s && Items.Equipped(s.Self, item.Id),
            Selected = item.Id == selectedItem,
            TooltipText = ItemDescription(item),
            Clicked = clicked ?? (() =>
            {
                selectedItem = item.Id;
                selectedBag = bag;
                refreshPage?.Invoke();
            }),
            RightClicked = () => ShowItemContext(item, bag),
            Dropped = (id, from) =>
            {
                if (Snapshot is null) return;
                if (from == "bank" && bag == "inventory") Send("withdraw", item: id);
                else if (from == "inventory" && bag == "bank") Send("deposit", item: id);
                else if (from == "inventory" && bag == "inventory")
                {
                    var source = Snapshot.Self.Inventory.FirstOrDefault(x => x.Id == id);
                    if (source is not null && Data.Item(source.Template).Type == "rune") Send("socket", item.Id, id);
                }
            }
        };
    }

    private void ShowItemContext(Item item, string bag)
    {
        if (Snapshot is null) return;

        selectedItem = item.Id;
        selectedBag = bag;
        refreshPage?.Invoke();

        var def = Data.Item(item.Template);
        var popup = new PopupPanel
        {
            Name = "ItemContextMenu",
            Size = new Vector2I(240, 120)
        };

        AddChild(popup);
        popup.Theme = Theme;

        var panel = new PanelContainer();
        popup.AddChild(panel);
        panel.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);

        var body = Ui.Column(panel);
        body.AddChild(Ui.Label(def.Name, 16, Ui.Gold, true));

        string actionText;
        Action action;

        if (bag == "inventory" && def.Slot != "")
        {
            bool equipped = Items.Equipped(Snapshot.Self, item.Id);

            actionText = equipped ? "Unequip" : "Equip";
            action = () =>
            {
                popup.Hide();

                if (equipped)
                    Send("unequip", arg: def.Slot);
                else
                    Send("equip", item: item.Id);
            };
        }
        else if (bag == "bank")
        {
            actionText = "Withdraw";
            action = () =>
            {
                popup.Hide();
                Send("withdraw", item: item.Id);
            };
        }
        else if (def.Type is "food" or "potion" or "scroll")
        {
            actionText = "Use";
            action = () =>
            {
                popup.Hide();
                Send("consume", item: item.Id);
            };
        }
        else if (def.Type is "book" or "treasure_map")
        {
            actionText = "Read";
            action = () =>
            {
                popup.Hide();
                Send("read", item: item.Id);
            };
        }
        else
        {
            actionText = "Inspect";
            action = popup.Hide;
        }

        var primary = Ui.Button(actionText, action);
        primary.Name = "ItemContextPrimaryAction";
        body.AddChild(primary);

        popup.PopupHide += () =>
        {
            if (GodotObject.IsInstanceValid(popup))
                popup.QueueFree();
        };

        Vector2 mouse = GetViewport().GetMousePosition();
        popup.Popup(new Rect2I(
            (int)mouse.X + 8,
            (int)mouse.Y + 8,
            240,
            120));
    }

    private void BuildInventoryPage(bool bank)
    {
        if (page is null || Snapshot is null) return;
        var top = Ui.Row(page); var search = Ui.Edit("Search items by name, material, or type"); top.AddChild(search);
        top.AddChild(Ui.Button("Sort", () => { inventoryByName = !inventoryByName; refreshPage?.Invoke(); }));
        top.AddChild(Ui.Button("Equipment", () => OpenPage("Character")));
        if (bank) top.AddChild(Ui.Button("Deposit unequipped", () => _ = DepositAllAsync(), !NearRole("banker")));
        var summary = Ui.Label("", 14, Ui.Muted); page.AddChild(summary);
        var body = Ui.Row(page); body.SizeFlagsVertical = SizeFlags.ExpandFill;
        var left = Ui.Column(body, true); var tabs = Ui.Row(left);
        if (bank)
        {
            tabs.AddChild(Ui.Button("Backpack", () => { selectedBag = "inventory"; selectedItem = ""; refreshPage?.Invoke(); }));
            tabs.AddChild(Ui.Button("Bank", () => { selectedBag = "bank"; selectedItem = ""; refreshPage?.Invoke(); }));
        }
        else selectedBag = "inventory";
        var scroll = Ui.Scroll(left, new Vector2(425, 400)); var grid = new GridContainer { Columns = 6 }; scroll.AddChild(grid);
        var rightScroll = Ui.Scroll(body, new Vector2(310, 400)); var details = Ui.Column(rightScroll);
        void Render()
        {
            if (Snapshot is not { } snap) return;
            var self = snap.Self; Ui.Clear(grid); Ui.Clear(details);
            var source = bank && selectedBag == "bank" ? self.Bank : self.Inventory;
            summary.Text = $"Backpack {self.Inventory.Count}/{Items.InventoryCapacity}  ·  Bank {self.Bank.Count}/{Items.BankCapacity}  ·  {self.Gold:N0} gold" + (bank && !NearRole("banker") ? "  ·  Visit a banker to transfer items." : "");
            var filtered = source.Where(x => (Data.Item(x.Template).Name + " " + Data.Item(x.Template).Material + " " + Data.Item(x.Template).Type).Contains(search.Text, StringComparison.OrdinalIgnoreCase));
            var sorted = inventoryByName ? filtered.OrderBy(x => Data.Item(x.Template).Name) : filtered.OrderByDescending(x => x.Rarity).ThenBy(x => Data.Item(x.Template).Type);
            foreach (var item in sorted) grid.AddChild(MakeSlot(item, selectedBag));
            for (int i = grid.GetChildCount(); i < 36; i++)
            {
                string targetBag = selectedBag;
                grid.AddChild(new ItemSlot { Bag = targetBag, Dropped = (id, from) => { if (from != targetBag) Send(targetBag == "bank" ? "deposit" : "withdraw", item: id); } });
            }
            var selected = source.FirstOrDefault(x => x.Id == selectedItem);
            if (selected is null) { details.AddChild(Ui.Label("Select an item", 23, Ui.Gold)); details.AddChild(Ui.Label("Inspect its statistics and requirements. Drag a rune onto equipment to fill an empty socket.", 16, Ui.Muted, true)); return; }
            DrawItemDetails(details, selected, bank);
        }
        refreshPage = Render; search.TextChanged += _ => Render(); Render();
    }

    private void DrawItemDetails(VBoxContainer parent, Item item, bool bank)
    {
        if (Snapshot is null) return;
        var self = Snapshot.Self; var def = Data.Item(item.Template);
        var heading = Ui.Row(parent); heading.AddChild(Ui.Image(Assets.Icon(item.Template), 64)); var names = Ui.Column(heading); names.AddChild(Ui.Label(def.Name, 21, Ui.RarityColor(item.Rarity), true)); names.AddChild(Ui.Label(item.Rarity.ToString(), 14, Ui.Muted));
        parent.AddChild(Ui.Label(ItemDescription(item), 15, Ui.Text, true));
        var quantity = Amount(parent, item.Quantity);
        if (selectedBag == "bank")
        {
            parent.AddChild(Ui.Button("Withdraw", () => Send("withdraw", item: item.Id, amount: Quantity(quantity, item.Quantity)), !NearRole("banker"))); return;
        }
        if (def.Slot != "")
        {
            bool equipped = Items.Equipped(self, item.Id);
            parent.AddChild(Ui.Button(equipped ? "Unequip" : "Equip", () => { if (equipped) Send("unequip", arg: def.Slot); else Send("equip", item: item.Id); }));
            if (item.Durability < 100) parent.AddChild(Ui.Button("Repair at blacksmith", () => Send("repair", item: item.Id), !NearRole("blacksmith")));
        }
        if (def.Type is "food" or "potion" or "scroll") parent.AddChild(Ui.Button("Use", () => Send("consume", item: item.Id)));
        if (def.Type is "book" or "treasure_map") parent.AddChild(Ui.Button("Read", () => Send("read", item: item.Id)));
        if (def.Type == "food" && self.Pet != "") parent.AddChild(Ui.Button("Feed companion", () => Send("feed", item: item.Id)));
        if (bank) parent.AddChild(Ui.Button("Deposit", () => Send("deposit", item: item.Id, amount: Quantity(quantity, item.Quantity)), !NearRole("banker") || Items.Equipped(self, item.Id)));
        if (def.Type == "rune")
        {
            parent.AddChild(Ui.Label("Insert into equipment", 17, Ui.Gold));
            foreach (var equipment in self.Inventory.Where(x => x.Sockets > x.Runes.Count))
            {
                string target = equipment.Id; parent.AddChild(Ui.Button(Data.Item(equipment.Template).Name, () => Send("socket", target, item.Id)));
            }
        }
        for (int i = 0; i < item.Runes.Count; i++)
        {
            int index = i; parent.AddChild(Ui.Button("Extract " + Data.Item(item.Runes[i].Template).Name, () => Confirm("Extract rune", "The enchanter charges an extraction fee. The rune is returned intact.", () => Send("unsocket", item.Id, amount: index)), !NearRole("enchanter")));
        }
        if (selectedNpc != "" && Data.Npcs.Any(x => x.Id == selectedNpc && x.Stock.Length > 0 && NearNpc(x)) && !Items.Equipped(self, item.Id) && def.Type != "quest")
        {
            long unit = Math.Max(1, (long)Math.Floor(def.Value * .30));
            parent.AddChild(Ui.Button($"Sell · {unit} gold each", () =>
            {
                int count = Math.Min(99, Quantity(quantity, item.Quantity));
                Action sale = () => Send("sell", selectedNpc, item.Id, count);
                if (item.Rarity >= Rarity.Epic) Confirm("Sell valuable equipment", $"Sell {count} {def.Name} for {unit * count} gold?", sale); else sale();
            }));
        }
    }

    private async Task DepositAllAsync()
    {
        if (Snapshot is not { } snap || !NearRole("banker")) return;
        var entries = snap.Self.Inventory.Where(x => !Items.Equipped(snap.Self, x.Id)).Select(x => (x.Id, x.Quantity)).ToArray();
        int completed = 0;
        foreach (var entry in entries)
        {
            var result = await SendAsync(new GameCommand { Kind = "deposit", Item = entry.Id, Amount = entry.Quantity }, true);
            if (result?.Ok != true) { Notify($"Deposited {completed} stacks. The remaining items stayed in your backpack.", true); return; }
            completed++;
        }
        Notify($"Deposited {completed} stacks.");
    }

    private long DisplayBuyPrice(NpcDef npc, ItemDef item)
    {
        if (Snapshot is null) return item.Value;
        double reputation = Math.Clamp(Snapshot.Self.Reputation.GetValueOrDefault(npc.Faction), 0, 1000) / 20000.0;
        double reduction = Math.Min(.15, Progression.Level(Snapshot.Self, "bartering") * .001 + reputation);
        return Math.Max(1, (long)Math.Ceiling(item.Value * (1.2 - reduction)));
    }
    private void BuildShopPage()
    {
        if (page is null || Snapshot is null) return;
        var npc = Data.Npcs.FirstOrDefault(x => x.Id == selectedNpc && x.Stock.Length > 0);
        if (npc is null) { page.AddChild(Ui.Label("Speak with a merchant to view their stock.", 18, Ui.Muted, true)); return; }
        page.AddChild(Ui.Label(npc.Name + " · " + Ui.Words(npc.Role), 22, Ui.Gold));
        var top = Ui.Row(page); var search = Ui.Edit("Search this merchant's stock"); top.AddChild(search); top.AddChild(Ui.Button("Sell from backpack", () => OpenPage("Inventory")));
        var money = Ui.Label("", 14, Ui.Muted); page.AddChild(money);
        var scroll = Ui.Scroll(page, new Vector2(720, 430)); var rows = Ui.Column(scroll);
        void Render()
        {
            if (Snapshot is null) return;
            Ui.Clear(rows); money.Text = $"Your gold: {Snapshot.Self.Gold:N0}  ·  Prices include your Bartering skill and faction reputation.";
            foreach (var template in npc.Stock.Select(Data.Item).Where(x => x.Name.Contains(search.Text, StringComparison.OrdinalIgnoreCase)))
            {
                long price = DisplayBuyPrice(npc, template); int stock = Snapshot.ShopStock.GetValueOrDefault(npc.Id + "/" + template.Id);
                var row = Ui.Row(rows); row.AddChild(Ui.Image(Assets.Icon(template.Id), 48));
                var description = Ui.Column(row); description.AddChild(Ui.Label(template.Name, 17)); description.AddChild(Ui.Label($"{price} gold each · Stock {stock} · {Ui.Words(template.Type)}", 13, Ui.Muted));
                row.TooltipText = ItemDescription(new Item { Template = template.Id }, false);
                var amount = new SpinBox { MinValue = 1, MaxValue = Math.Max(1, Math.Min(99, stock)), Value = 1, CustomMinimumSize = new Vector2(82, 32) }; row.AddChild(amount);
                row.AddChild(Ui.Button("Buy", () =>
                {
                    int count = Quantity(amount, 99); long total = price * count;
                    Action purchase = () => Send("buy", npc.Id, template.Id, count);
                    if (total >= 1000) Confirm("Confirm purchase", $"Buy {count} {template.Name} for {total} gold?", purchase); else purchase();
                }, stock < 1 || !NearNpc(npc)));
            }
        }
        refreshPage = Render; search.TextChanged += _ => Render(); Render();
    }

    private void BuildCharacterPage()
    {
        if (page is null || Snapshot is null) return;
        var self = Snapshot.Self; var cls = Data.Class(self.Class); var stats = CombatMath.Stats(self, Data);
        var row = Ui.Row(page); row.SizeFlagsVertical = SizeFlags.ExpandFill;
        var left = Ui.Column(row); left.CustomMinimumSize = new Vector2(230, 0);
        left.AddChild(Ui.Label(self.Name, 25, Ui.Gold)); left.AddChild(Ui.Label(cls.Name + " · Level " + Progression.PlayerLevel(self), 17, Ui.Muted));
        left.AddChild(new AvatarPreview { Assets = Assets, Appearance = self.Appearance, Equipment = PixelAssets.VisibleEquipment(self), CustomMinimumSize = new Vector2(210, 240) });
        left.AddChild(Ui.Label(cls.Passive, 15, Ui.Text, true));
        left.AddChild(Ui.Label($"Total skill XP: {Progression.Total(self):N0}\nDeaths: {self.Deaths}\nClass affinity: " + string.Join(", ", cls.Affinity.Select(x => Data.Skill(x).Name)), 14, Ui.Muted, true));
        var middle = Ui.Column(row); middle.CustomMinimumSize = new Vector2(200, 0);
        middle.AddChild(Ui.Label("Equipment", 20, Ui.Gold));
        var slots = new GridContainer { Columns = 3 }; middle.AddChild(slots);
        foreach (string slot in new[] { "helmet", "necklace", "cloak", "weapon", "chest", "offhand", "gloves", "legs", "belt", "ring", "boots", "trinket", "charm" })
        {
            var box = Ui.Column(slots); box.AddChild(Ui.Label(Ui.Words(slot), 11, Ui.Muted));
            var item = self.Equipment.TryGetValue(slot, out var id) ? self.Inventory.FirstOrDefault(x => x.Id == id) : null;
            var button = item is null ? new ItemSlot { TooltipText = Ui.Words(slot) + " slot" } : MakeSlot(item, "inventory", () => { selectedItem = item.Id; selectedBag = "inventory"; OpenPage("Inventory"); });
            button.Dropped = (source, bag) => { if (bag == "inventory") Send("equip", item: source); }; box.AddChild(button);
        }
        var right = Ui.Column(Ui.Scroll(row, new Vector2(260, 440)));
        right.AddChild(Ui.Label("Attributes", 20, Ui.Gold));
        foreach (string attribute in new[] { "strength", "dexterity", "intellect", "vitality", "spirit", "resolve", "luck" }) right.AddChild(Ui.Label($"{Ui.Words(attribute)}  {stats.Bonus(attribute):0.0}", 15));
        right.AddChild(Ui.Label("Derived statistics", 20, Ui.Gold));
        foreach (var stat in new[] { ("Maximum health", stats.Health), ("Maximum mana", stats.Mana), ("Maximum stamina", stats.Stamina), ("Physical power", stats.Physical), ("Spell power", stats.Spell), ("Armor", stats.Armor), ("Critical chance %", stats.Crit * 100), ("Critical damage %", stats.CritDamage * 100), ("Evasion %", stats.Evasion * 100), ("Block %", stats.Block * 100), ("Movement tiles/s", stats.MoveSpeed), ("Attack speed", stats.AttackSpeed), ("Cooldown reduction %", stats.CooldownReduction * 100) }) right.AddChild(Ui.Label($"{stat.Item1}  {stat.Item2:0.0}", 14));
        foreach (Element element in Enum.GetValues<Element>()) right.AddChild(Ui.Label($"{element} resistance  {CombatMath.Resist(stats, element) * 100:0}%", 14, WorldView.ElementColor(element)));
    }
}
