using Godot;
using Kairnfall.Core;
using System.Globalization;
using System.Text.Json;

namespace Kairnfall.Client;

/// <summary>Persistent merchant controls. Snapshot refresh never discards typed quantity.</summary>
public partial class MerchantSellPanel : VBoxContainer
{
    public Catalog Data { get; set; } = null!;
    public PixelAssets Assets { get; set; } = null!;
    public NpcDef Merchant { get; set; } = null!;
    public Func<Character?>? ReadCharacter { get; set; }
    public Func<string,int,Task<CommandResult?>>? SellItem { get; set; }
    private ItemList list = null!;
    private LineEdit amount = null!;
    private Button sell = null!, sellAll = null!;
    private Label total = null!, status = null!, money = null!;
    private VBoxContainer details = null!;
    private readonly List<string> ids = [];
    private string selected = "", layout = "", cardStamp = "";
    private bool busy, ready, refreshing, confirming;
    private long awaitingSequence;
    private string awaitingCharacter = "";
    private bool AwaitingSnapshot => awaitingSequence > 0;
    public override void _Ready()
    {
        Name = "MerchantSellPanel"; SizeFlagsHorizontal = SizeFlags.ExpandFill; SizeFlagsVertical = SizeFlags.ExpandFill;
        AddThemeConstantOverride("separation", 5);
        AddChild(CompactItemCard.Centered(Merchant.Name + " · Sell from backpack", 18, Ui.Gold));
        money = CompactItemCard.Centered("", 13, Ui.Muted); AddChild(money);
        var row = Ui.Row(this); row.SizeFlagsVertical = SizeFlags.ExpandFill;
        list = new ItemList { Name = "SaleItems", CustomMinimumSize = new Vector2(310, 220), SizeFlagsHorizontal = SizeFlags.ExpandFill, SizeFlagsVertical = SizeFlags.ExpandFill,
            FixedIconSize = new Vector2I(32,32), SelectMode = ItemList.SelectModeEnum.Single };
        row.AddChild(list);
        var inspector = Ui.Column(row, true);
        var scroll = Ui.Scroll(inspector, new Vector2(340, 160)); details = Ui.Column(scroll);
        var amountRow = Ui.Row(inspector); amountRow.Alignment = BoxContainer.AlignmentMode.Center;
        amountRow.AddChild(CompactItemCard.Centered("Quantity", 13));
        var decrease = Ui.Button("−", () => AdjustQuantity(-1)); decrease.Name = "SaleQuantityDecrease";
        decrease.CustomMinimumSize = new Vector2(32, 32); decrease.FocusMode = FocusModeEnum.None; amountRow.AddChild(decrease);
        amount = new LineEdit { Name = "SaleQuantity", Text = "1", MaxLength = 12, Alignment = HorizontalAlignment.Center,
            CustomMinimumSize = new Vector2(104, 32), SizeFlagsHorizontal = SizeFlags.ShrinkCenter };
        amount.TooltipText = "Enter a whole quantity. Invalid text is never converted into a sale."; amountRow.AddChild(amount);
        var increase = Ui.Button("+", () => AdjustQuantity(1)); increase.Name = "SaleQuantityIncrease";
        increase.CustomMinimumSize = new Vector2(32, 32); increase.FocusMode = FocusModeEnum.None; amountRow.AddChild(increase);
        total = CompactItemCard.Centered("", 14, Ui.Gold); total.Name = "SaleGoldTotal"; inspector.AddChild(total);
        // Separate rows keep both complete gold totals visible at the minimum viewport.
        var buttons = Ui.Column(inspector); buttons.Name = "MerchantSaleActions";
        buttons.AddThemeConstantOverride("separation", 4);
        sell = Ui.Button("Sell quantity", () => Request(false)); sell.Name = "SellSelectedQuantity";
        sellAll = Ui.Button("Sell entire stack", () => Request(true)); sellAll.Name = "SellAllQuantity";
        sell.Alignment = sellAll.Alignment = HorizontalAlignment.Center;
        sell.SizeFlagsHorizontal = sellAll.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        buttons.AddChild(sell); buttons.AddChild(sellAll);
        status = CompactItemCard.Centered("", 12, Ui.Danger); status.Name = "SaleBlocker"; inspector.AddChild(status);
        list.ItemSelected += index =>
        {
            if (refreshing || index < 0 || index >= ids.Count) return;
            selected = ids[(int)index]; cardStamp = ""; amount.Text = "1"; RefreshSnapshot();
        };
        amount.TextChanged += _ => RefreshQuote();
        ready = true; RefreshSnapshot();
    }
    private Item? Current(Character self) => self.Inventory.FirstOrDefault(x => x.Id == selected);
    public static bool TryQuantity(string text, int maximum, out int quantity)
        => int.TryParse(text.Trim(), NumberStyles.None, CultureInfo.InvariantCulture, out quantity) && quantity > 0 && quantity <= maximum;
    public void RefreshSnapshot()
    {
        if (!ready || ReadCharacter?.Invoke() is not { } self) return;
        if (AwaitingSnapshot && (self.Id != awaitingCharacter || self.LastAction >= awaitingSequence))
        {
            awaitingSequence = 0; awaitingCharacter = "";
        }
        refreshing = true;
        try
        {
            var items = self.Inventory.OrderBy(x => Data.Item(x.Template).Name, StringComparer.Ordinal).ThenBy(x => x.Id, StringComparer.Ordinal).ToArray();
            string next = self.Id + "|" + string.Join(';', items.Select(x => x.Id));
            if (next != layout)
            {
                list.Clear(); ids.Clear();
                foreach (var item in items) { ids.Add(item.Id); list.AddItem("", Assets.Icon(item.Template)); }
                if (!ids.Contains(selected))
                {
                    // Do not arm another item under the same Sell button after removal.
                    selected = layout == "" ? ids.FirstOrDefault() ?? "" : "";
                    amount.Text = "1"; cardStamp = "";
                }
                layout = next;
            }
            for (int i = 0; i < items.Length; i++)
            {
                var item = items[i]; string problem = MerchantSales.Problem(self, Merchant, item, 1, Data);
                list.SetItemText(i, Data.Item(item.Template).Name + " ×" + item.Quantity);
                list.SetItemCustomFgColor(i, problem == "" ? Ui.Text : Ui.Danger);
                list.SetItemTooltip(i, problem == "" ? MerchantSales.UnitPrice(Data.Item(item.Template)) + " gold each" : problem);
                if (item.Id == selected) list.Select(i);
            }
            money.Text = $"Gold: {self.Gold:N0} · One backpack: {self.Inventory.Count}/{Items.InventoryCapacity} slots";
            var current = Current(self);
            if (current is not null)
            {
                // Snapshot updates change validation, never the pending text or caret.
                amount.PlaceholderText = "1–" + current.Quantity;
                // Durability, affixes and runes can change while the equipment IDs stay fixed.
                var equippedItems = self.Inventory.Where(x => Items.Equipped(self, x.Id)).ToArray();
                string stamp = JsonSerializer.Serialize(new { current, self.Equipment, equippedItems, self.SkillXp, dead = self.Health <= 0 }, Wire.Json);
                if (stamp != cardStamp)
                {
                    Ui.Clear(details); details.AddChild(CompactItemCard.Create(Data, self, current, Assets.Icon(current.Template)));
                    cardStamp = stamp;
                }
            }
            else
            {
                Ui.Clear(details);
                details.AddChild(CompactItemCard.Centered(self.Inventory.Count == 0 ? "No items in your backpack." : "Select an item to inspect and sell."));
                cardStamp = "";
            }
        }
        finally { refreshing = false; }
        RefreshQuote();
    }
    private void AdjustQuantity(int difference)
    {
        if (busy || confirming || AwaitingSnapshot || ReadCharacter?.Invoke() is not { } self || Current(self) is not { } item) return;
        if (!TryQuantity(amount.Text, item.Quantity, out int current)) { RefreshQuote(); return; }
        amount.Text = Math.Clamp(current + difference, 1, item.Quantity).ToString(CultureInfo.InvariantCulture);
        RefreshQuote();
    }
    private void RefreshQuote()
    {
        if (!ready || refreshing) return;
        var self = ReadCharacter?.Invoke(); var item = self is null ? null : Current(self);
        if (item is null) { sell.Disabled = sellAll.Disabled = true; total.Text = ""; status.Text = "Select an item."; return; }
        bool valid = TryQuantity(amount.Text, item.Quantity, out int count);
        string problem = MerchantSales.Problem(self!, Merchant, item, valid ? count : 1, Data);
        string allProblem = MerchantSales.Problem(self!, Merchant, item, item.Quantity, Data);
        long unit = MerchantSales.UnitPrice(Data.Item(item.Template));
        sell.Disabled = busy || AwaitingSnapshot || confirming || !valid || problem != "";
        sellAll.Disabled = busy || AwaitingSnapshot || confirming || allProblem != "";
        sell.Text = valid ? $"Sell {count} · {unit * count:N0} gold" : "Sell quantity";
        sellAll.Text = $"Sell all {item.Quantity} · {unit * item.Quantity:N0} gold";
        total.Text = valid ? $"Receive {unit * count:N0} gold · {unit:N0} each" : $"Enter 1–{item.Quantity} whole items.";
        status.Text = busy ? "Waiting for the server…" : AwaitingSnapshot ? "Sale confirmed. Waiting for inventory update…" : problem != "" ? problem : !valid ? "Enter a valid whole quantity." : "";
    }
    private void Request(bool all)
    {
        if (busy || AwaitingSnapshot || confirming || ReadCharacter?.Invoke() is not { } self || Current(self) is not { } item) return;
        int count = item.Quantity;
        if (!all && !TryQuantity(amount.Text, item.Quantity, out count)) { RefreshQuote(); return; }
        string problem = MerchantSales.Problem(self, Merchant, item, count, Data);
        if (problem != "") { status.Text = problem; return; }
        string id = item.Id;
        if (item.Rarity >= Rarity.Epic || item.Runes.Count > 0)
        {
            confirming = true; RefreshQuote();
            var dialog = new ConfirmationDialog { Title = "Sell valuable item", DialogText = $"Sell {count} {Data.Item(item.Template).Name} for {MerchantSales.Quote(self,Merchant,item,count,Data):N0} gold?", Theme = Theme };
            AddChild(dialog);
            dialog.Confirmed += () => { confirming = false; dialog.QueueFree(); _ = ExecuteSale(id, count); };
            dialog.Canceled += () => { confirming = false; dialog.QueueFree(); RefreshQuote(); };
            dialog.PopupCentered();
        }
        else _ = ExecuteSale(id, count);
    }
    private async Task ExecuteSale(string id, int count)
    {
        var send = SellItem;
        if (send is null || busy || AwaitingSnapshot) return;
        string character = ReadCharacter?.Invoke()?.Id ?? "";
        busy = true; RefreshQuote();
        string error = "";
        try
        {
            var result = await send(id, count);
            if (result?.Ok != true) error = result?.Message ?? "Sale was not confirmed. Inventory is unchanged until the server confirms it.";
            else
            {
                // The command receipt may arrive before the matching snapshot.
                // Never enable another sale against the old displayed inventory.
                awaitingSequence = result.Sequence; awaitingCharacter = character;
            }
        }
        catch (Exception) { error = "Sale connection failed. Check the server response before trying again."; }
        if (!GodotObject.IsInstanceValid(this) || !IsInsideTree()) return;
        busy = false; RefreshSnapshot();
        if (error != "") status.Text = error;
    }
    public override void _ExitTree() { ReadCharacter = null; SellItem = null; }
}
