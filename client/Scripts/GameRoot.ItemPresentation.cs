using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private Control ItemTooltip(string id, string bag)
    {
        var self = Snapshot?.Self;
        var item = (bag == "bank" ? self?.Bank : self?.Inventory)?.FirstOrDefault(x => x.Id == id);
        return item is null ? CompactItemCard.TextTooltip("This item is no longer available.")
            : CompactItemCard.Create(Data, self, item, Assets.Icon(item.Template), true);
    }
    private void BuildSellPage()
    {
        if (page is null || Snapshot is null) return;
        var merchant = Data.Npcs.FirstOrDefault(x => x.Id == selectedNpc && x.Stock.Length > 0);
        if (merchant is null) { page.AddChild(CompactItemCard.Centered("Speak with a merchant before selling.", 16, Ui.Danger)); return; }
        var panel = new MerchantSellPanel
        {
            Data = Data, Assets = Assets, Merchant = merchant,
            ReadCharacter = () => Snapshot?.Self,
            SellItem = (id, count) => SendAsync(new GameCommand { Kind = "sell", Target = merchant.Id, Item = id, Amount = count })
        };
        page.AddChild(panel); refreshPage = panel.RefreshSnapshot;
    }
}

public partial class ItemPreviewRow : HBoxContainer
{
    public Func<Control>? MakeTooltip { get; set; }
    public override GodotObject _MakeCustomTooltip(string forText) => MakeTooltip?.Invoke() ?? CompactItemCard.TextTooltip(forText);
    public override void _ExitTree() { MakeTooltip = null; }
}
