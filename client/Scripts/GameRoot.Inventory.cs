using Godot;
using Kairnfall.Core;
using System.Text;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private bool inventoryByName = true;
    private bool NearNpc(NpcDef npc) => Snapshot is { } s && s.Self.Zone == npc.Zone && s.Self.Position.Distance(npc.Position) <= 3 && WorldMap.LineOfSight(Data.Zone(npc.Zone), s.Self.Position, npc.Position);
    private bool NearRole(string role) => Data.Npcs.Any(x => x.Role == role && NearNpc(x));
    private int Quantity(SpinBox control, int maximum = 999) => Math.Clamp((int)control.Value, 1, Math.Max(1, maximum));
    private SpinBox Amount(Node parent, int maximum)
    {
        var row = Ui.Row(parent); row.AddChild(Ui.Label("Quantity", 14, Ui.Muted));
        var amount = new SpinBox { MinValue = 1, MaxValue = Math.Max(1, maximum), Step = 1, Value = 1, CustomMinimumSize = new Vector2(120, 32) };
        row.AddChild(amount); return amount;
    }
    private void Confirm(string title, string message, Action action)
    {
        var dialog = new ConfirmationDialog { Title = title, DialogText = message, Theme = Theme, MinSize = new Vector2I(460, 150) };
        AddChild(dialog);
        dialog.Confirmed += () => { action(); dialog.QueueFree(); };
        dialog.Canceled += dialog.QueueFree;
        dialog.PopupCentered();
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
        else if (def.Type == "tool") text.AppendLine($"Tool durability: {item.Durability}%");
        foreach (var rune in item.Runes) text.AppendLine("Rune: " + Data.Item(rune.Template).Name);
        text.AppendLine().Append(def.Description);
        if (compare && Snapshot is { } s && def.Slot != "" && !Items.Equipped(s.Self, item.Id) && s.Self.Inventory.Any(x => x.Id == item.Id))
        {
            try
            {
                var projected = Wire.Copy(s.Self);
                var before = CombatMath.Stats(projected, Data);
                Items.Equip(projected, item.Id, Data);
                var after = CombatMath.Stats(projected, Data);
                text.AppendLine().AppendLine().AppendLine("Compared with current equipment:");
                foreach (var value in new[] { ("Health", after.Health - before.Health), ("Physical power", after.Physical - before.Physical), ("Spell power", after.Spell - before.Spell), ("Armor", after.Armor - before.Armor), ("Mana", after.Mana - before.Mana) })
                    if (Math.Abs(value.Item2) > .01) text.AppendLine($"{value.Item1}: {value.Item2:+0.0;-0.0;0}");
            }
            catch (RuleException error) { text.AppendLine().Append(error.Message); }
        }
        // Godot text layout expects LF. Windows AppendLine emits CRLF, which
        // produces extra paragraph spacing in the native item inspector.
        return text.ToString().ReplaceLineEndings("\n");
    }

    private ItemSlot MakeSlot(Item item, string bag, Action? clicked = null)
    {
        return new EquipmentItemSlot
        {
            Item = item, Icon = Assets.Icon(item.Template), Bag = bag,
            Equipped = Snapshot is { } s && Items.Equipped(s.Self, item.Id), Selected = item.Id == selectedItem,
            TooltipText = ItemDescription(item) + (Data.Item(item.Template).Type == "tool" ? "\n\nKeep this tool in your backpack. The best learned tool is selected automatically." : "\n\nDouble-click: equip or unequip. Right-click: item actions."),
            Clicked = clicked ?? (() => { selectedItem = item.Id; selectedBag = bag; lastPageStamp = ""; }),
            Activated = () =>
            {
                selectedItem = item.Id; selectedBag = bag; lastPageStamp = "";
                if (Data.Item(item.Template).Slot != "") ToggleEquipment(item.Id);
            },
            ContextRequested = at => ItemContext(item, bag, at),
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

    private void BuildInventoryPage(bool bank)
    {
        if (page is null || Snapshot is null) return;
        var top = Ui.Row(page);
        var search = Ui.Edit("Search by item name, material, or type"); top.AddChild(search);
        top.AddChild(Ui.Button("Sort", () => { inventoryByName = !inventoryByName; lastPageStamp = ""; }));
        top.AddChild(Ui.Button("Equipment & backpack", () => OpenPage("Character")));
        var upgrades=Ui.Button("Upgrade guide",()=>OpenPage("Equipment Guide")); upgrades.Name="OpenEquipmentGuide"; top.AddChild(upgrades);
        if (bank) top.AddChild(Ui.Button("Deposit unequipped", () => _ = DepositAllAsync(), !NearRole("banker")));
        var summary = Ui.Label("", 14, Ui.Muted, true); page.AddChild(summary);
        var body = Ui.Row(page); body.SizeFlagsVertical = SizeFlags.ExpandFill;
        var left = Ui.Column(body, true); var tabs = Ui.Row(left);
        if (bank)
        {
            tabs.AddChild(Ui.Button("Backpack", () => { selectedBag = "inventory"; selectedItem = ""; lastPageStamp = ""; }));
            tabs.AddChild(Ui.Button("Bank", () => { selectedBag = "bank"; selectedItem = ""; lastPageStamp = ""; }));
        }
        else selectedBag = "inventory";
        var scroll = Ui.Scroll(left, new Vector2(350, 250));
        var grid = new GridContainer { Columns = 5 }; scroll.AddChild(grid);
        left.AddChild(Ui.Label("Select to inspect · Double-click to equip · Right-click for actions", 12, Ui.Muted, true));
        var inspector = Ui.Column(body, true); inspector.CustomMinimumSize = new Vector2(300, 0);
        // The primary action stays outside the scrolling statistics panel.
        var primary = Ui.Column(inspector); primary.Name = "EquipmentActionBar";
        var rightScroll = Ui.Scroll(inspector, new Vector2(300, 200));
        var details = Ui.Column(rightScroll);
        void Render()
        {
            if (Snapshot is not { } snap) return;
            var self = snap.Self;
            Ui.Clear(grid); Ui.Clear(details); Ui.Clear(primary);
            var source = bank && selectedBag == "bank" ? self.Bank : self.Inventory;
            summary.Text = $"Backpack {self.Inventory.Count}/{Items.InventoryCapacity} · Bank {self.Bank.Count}/{Items.BankCapacity} · {self.Gold:N0} gold"
                + (bank && !NearRole("banker") ? " · Visit a banker to transfer items." : "");
            var filtered = source.Where(x => (Data.Item(x.Template).Name + " " + Data.Item(x.Template).Material + " " + Data.Item(x.Template).Type).Contains(search.Text, StringComparison.OrdinalIgnoreCase));
            var sorted = (inventoryByName ? filtered.OrderBy(x => Data.Item(x.Template).Name) : filtered.OrderByDescending(x => x.Rarity).ThenBy(x => Data.Item(x.Template).Type)).ToArray();
            if (!source.Any(x => x.Id == selectedItem))
                selectedItem = sorted.FirstOrDefault(x => Data.Item(x.Template).Slot != "")?.Id ?? sorted.FirstOrDefault()?.Id ?? "";
            foreach (var item in sorted) grid.AddChild(MakeSlot(item, selectedBag));
            for (int i = grid.GetChildCount(); i < 30; i++)
            {
                string targetBag = selectedBag;
                grid.AddChild(new EquipmentItemSlot
                {
                    Bag = targetBag,
                    Dropped = (id, from) => { if (bank && from != targetBag) Send(targetBag == "bank" ? "deposit" : "withdraw", item: id); }
                });
            }
            var selected = source.FirstOrDefault(x => x.Id == selectedItem);
            if (selected is null)
            {
                details.AddChild(Ui.Label("Select an item", 23, Ui.Gold));
                details.AddChild(Ui.Label("Equipment actions appear above the item details. Drag a rune onto equipment to fill an empty socket.", 16, Ui.Muted, true));
                return;
            }
            BuildEquipmentAction(primary, selected, selectedBag);
            DrawItemDetails(details, selected, bank);
        }
        refreshPage = Render; search.TextChanged += _ => Render(); Render();
    }

    private void DrawItemDetails(VBoxContainer parent, Item item, bool bank)
    {
        if (Snapshot is null) return;
        var self = Snapshot.Self; var def = Data.Item(item.Template);
        var heading = Ui.Row(parent); heading.AddChild(Ui.Image(Assets.Icon(item.Template), 64));
        var names = Ui.Column(heading);
        names.AddChild(Ui.Label(def.Name, 21, Ui.RarityColor(item.Rarity), true));
        names.AddChild(Ui.Label(item.Rarity + (Items.Equipped(self, item.Id) ? " · Equipped" : ""), 14, Ui.Muted));
        // The heading already names the item and rarity. Keep the statistics
        // compact enough to expose quantity/actions in the 720p inspector.
        parent.AddChild(Ui.Label(string.Join('\n', ItemDescription(item).Split('\n').Skip(2)), 15, Ui.Text, true));
        var quantity = Amount(parent, item.Quantity);
        if (selectedBag == "bank")
        {
            parent.AddChild(Ui.Button("Withdraw", () => Send("withdraw", item: item.Id, amount: Quantity(quantity, item.Quantity)), !NearRole("banker")));
            return;
        }
        if ((def.Slot != "" || def.Type == "tool") && item.Durability < 100)
        {
            var repair = Ui.Button("Repair at blacksmith", () => Send("repair", item: item.Id), !NearRole("blacksmith"));
            repair.Name = "RepairEquipmentAction"; parent.AddChild(repair);
        }
        if (def.Type is "food" or "potion" or "scroll") parent.AddChild(Ui.Button("Use", () => Send("consume", item: item.Id)));
        if (def.Type is "book" or "treasure_map") parent.AddChild(Ui.Button("Read", () => Send("read", item: item.Id)));
        if (def.Type == "food" && self.Pet != "") parent.AddChild(Ui.Button("Feed companion", () => Send("feed", item: item.Id)));
        if (item.Quantity > 1 && !Items.Equipped(self, item.Id))
            parent.AddChild(Ui.Button("Split selected quantity", () => Send("split", item: item.Id, amount: Quantity(quantity, item.Quantity - 1))));
        if (bank) parent.AddChild(Ui.Button("Deposit", () => Send("deposit", item: item.Id, amount: Quantity(quantity, item.Quantity)), !NearRole("banker") || Items.Equipped(self, item.Id)));
        if (def.Type == "rune")
        {
            parent.AddChild(Ui.Label("Insert into equipment", 17, Ui.Gold));
            foreach (var equipment in self.Inventory.Where(x => x.Sockets > x.Runes.Count))
            {
                string target = equipment.Id;
                parent.AddChild(Ui.Button(Data.Item(equipment.Template).Name, () => Send("socket", target, item.Id)));
            }
        }
        for (int i = 0; i < item.Runes.Count; i++)
        {
            int index = i;
            parent.AddChild(Ui.Button("Extract " + Data.Item(item.Runes[i].Template).Name,
                () => Confirm("Extract rune", "The enchanter charges an extraction fee. The rune is returned intact.", () => Send("unsocket", item.Id, amount: index)), !NearRole("enchanter")));
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
        var top = Ui.Row(page); var search = Ui.Edit("Search this merchant's stock"); top.AddChild(search);
        top.AddChild(Ui.Button("Sell from backpack", () => OpenPage("Inventory")));
        var money = Ui.Label("", 14, Ui.Muted); page.AddChild(money);
        var scroll = Ui.Scroll(page, new Vector2(720, 300)); var rows = Ui.Column(scroll);
        void Render()
        {
            if (Snapshot is null) return;
            Ui.Clear(rows);
            money.Text = $"Your gold: {Snapshot.Self.Gold:N0} · Prices include your Bartering skill and faction reputation.";
            foreach (var template in npc.Stock.Select(Data.Item).Where(x => x.Name.Contains(search.Text, StringComparison.OrdinalIgnoreCase)))
            {
                long price = DisplayBuyPrice(npc, template); int stock = Snapshot.ShopStock.GetValueOrDefault(npc.Id + "/" + template.Id);
                var row = Ui.Row(rows); row.AddChild(Ui.Image(Assets.Icon(template.Id), 48));
                var description = Ui.Column(row); description.AddChild(Ui.Label(template.Name, 17));
                description.AddChild(Ui.Label($"{price} gold each · Stock {stock} · {Ui.Words(template.Type)}", 13, Ui.Muted));
                row.TooltipText = ItemDescription(new Item { Template = template.Id }, false);
                var amount = new SpinBox { MinValue = 1, MaxValue = Math.Max(1, Math.Min(99, stock)), Value = 1, CustomMinimumSize = new Vector2(82, 32) };
                row.AddChild(amount);
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
        page.AddChild(Ui.Label("Drag from the backpack to the matching equipment slot. Double-click equipped gear to remove it.", 14, Ui.Muted, true));
        var row = Ui.Row(page); row.SizeFlagsVertical = SizeFlags.ExpandFill;
        var left = Ui.Column(Ui.Scroll(row, new Vector2(210, 260)));
        var middle = Ui.Column(Ui.Scroll(row, new Vector2(245, 260)));
        var right = Ui.Column(row, true);
        right.AddChild(Ui.Label("Backpack", 20, Ui.Gold));
        var backpack = new GridContainer { Columns = 4 };
        Ui.Scroll(right, new Vector2(270, 220)).AddChild(backpack);
        var actions = Ui.Column(right);
        void Render()
        {
            if (Snapshot is not { } snapshot) return;
            var self = snapshot.Self; var cls = Data.Class(self.Class); var stats = CombatMath.Stats(self, Data);
            Ui.Clear(left); Ui.Clear(middle); Ui.Clear(backpack); Ui.Clear(actions);
            left.AddChild(Ui.Label(self.Name, 22, Ui.Gold));
            left.AddChild(Ui.Label(cls.Name + " · Level " + Progression.PlayerLevel(self), 15, Ui.Muted));
            left.AddChild(new AvatarPreview { Assets = Assets, Appearance = self.Appearance, Equipment = PixelAssets.VisibleEquipment(self), CustomMinimumSize = new Vector2(180, 195) });
            left.AddChild(Ui.Label(cls.Passive, 14, Ui.Text, true));
            left.AddChild(Ui.Label($"Total skill XP: {Progression.Total(self):N0}\nHealth {stats.Health:0} · Mana {stats.Mana:0}\nPhysical {stats.Physical:0.0} · Spell {stats.Spell:0.0}\nArmor {stats.Armor:0.0}", 14, Ui.Muted, true));
            foreach (string attribute in new[] { "strength", "dexterity", "intellect", "vitality", "spirit", "resolve", "luck" })
                left.AddChild(Ui.Label($"{Ui.Words(attribute)} {stats.Bonus(attribute):0.0}", 13));
            foreach (var stat in new[] { ("Stamina", stats.Stamina), ("Critical chance %", stats.Crit * 100), ("Critical damage %", stats.CritDamage * 100), ("Evasion %", stats.Evasion * 100), ("Block %", stats.Block * 100), ("Movement tiles/s", stats.MoveSpeed), ("Attack speed", stats.AttackSpeed), ("Cooldown reduction %", stats.CooldownReduction * 100) })
                left.AddChild(Ui.Label($"{stat.Item1} {stat.Item2:0.0}", 13));
            foreach (Element element in Enum.GetValues<Element>())
                left.AddChild(Ui.Label($"{element} resistance {CombatMath.Resist(stats, element) * 100:0}%", 13, WorldView.ElementColor(element)));
            middle.AddChild(Ui.Label("Equipment", 20, Ui.Gold));
            var slots = new GridContainer { Columns = 3 }; middle.AddChild(slots);
            foreach (string slot in new[] { "helmet", "necklace", "cloak", "weapon", "chest", "offhand", "gloves", "legs", "belt", "ring", "boots", "trinket", "charm" })
            {
                var box = Ui.Column(slots); box.AddChild(Ui.Label(Ui.Words(slot), 11, Ui.Muted));
                var item = self.Equipment.TryGetValue(slot, out var id) ? self.Inventory.FirstOrDefault(x => x.Id == id) : null;
                var button = item is null ? new EquipmentItemSlot { TooltipText = Ui.Words(slot) + " slot" } : MakeSlot(item, "inventory");
                button.Name = "Equipment_" + slot;
                button.Dropped = (source, bag) =>
                {
                    if (bag == "inventory") ToggleEquipment(source, slot, true);
                    else Notify("Move this item to your backpack first.");
                };
                box.AddChild(button);
            }
            foreach (var item in self.Inventory.OrderBy(x => Data.Item(x.Template).Name)) backpack.AddChild(MakeSlot(item, "inventory"));
            var selected = self.Inventory.FirstOrDefault(x => x.Id == selectedItem);
            if (selected is not null)
            {
                actions.AddChild(Ui.Label(Data.Item(selected.Template).Name, 15, Ui.RarityColor(selected.Rarity), true));
                BuildEquipmentAction(actions, selected, "inventory");
                actions.AddChild(Ui.Button("Inspect statistics and runes", () => { selectedBag = "inventory"; OpenPage("Inventory"); }));
            }
        }
        refreshPage = Render; Render();
    }
}
