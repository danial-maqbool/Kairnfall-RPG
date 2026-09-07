using System.Security.Cryptography;
using System.Text.Json;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private string SplitStack(Character player, string itemId, int amount)
    {
        var source = Items.Owned(player, itemId);
        var definition = Data.Item(source.Template);
        Need(definition.StackMax > 1 && !Items.Equipped(player, itemId),
            "Only unequipped, stackable items can be split.");
        Need(source.Affixes.Count == 0 && source.Runes.Count == 0 && source.Sockets == 0,
            "Modified equipment cannot be split.");
        Need(amount > 0 && amount < source.Quantity,
            "Split at least one item and leave at least one in the original stack.");
        Need(player.Inventory.Count < Items.InventoryCapacity,
            "A free inventory slot is required to split a stack.");

        // Do not call Items.Add: it deliberately merges compatible stacks.
        var separated = Wire.Copy(source);
        separated.Id = Guid.NewGuid().ToString("N");
        separated.Quantity = amount;
        source.Quantity -= amount;
        player.Inventory.Add(separated);
        return $"Split {amount} {definition.Name}.";
    }

    private bool CanFulfillTradeOffer(TradeOffer offer)
    {
        if (!State.Characters.TryGetValue(offer.Character, out var owner) ||
            offer.Gold < 0 || offer.Gold > owner.Gold || offer.Items.Count > 12)
            return false;
        foreach (var pair in offer.Items)
        {
            var item = owner.Inventory.FirstOrDefault(x => x.Id == pair.Key);
            if (item is null || pair.Value < 1 || pair.Value > item.Quantity ||
                Items.Equipped(owner, item.Id) || Data.Item(item.Template).Type == "quest")
                return false;
        }
        return true;
    }

    private string TradeContentFingerprint(Trade trade)
    {
        object Describe(TradeOffer offer)
        {
            var owner = Player(offer.Character);
            return new
            {
                offer.Character,
                offer.Gold,
                Funded = offer.Gold >= 0 && offer.Gold <= owner.Gold,
                Items = offer.Items.OrderBy(x => x.Key, StringComparer.Ordinal)
                    .Select(x => new
                    {
                        Id = x.Key,
                        Offered = x.Value,
                        Instance = owner.Inventory.FirstOrDefault(i => i.Id == x.Key),
                        Equipped = Items.Equipped(owner, x.Key)
                    }).ToArray()
            };
        }
        var content = JsonSerializer.SerializeToUtf8Bytes(
            new { A = Describe(trade.A), B = Describe(trade.B) }, Wire.Json);
        return Convert.ToHexString(SHA256.HashData(content));
    }

    private bool InvalidateTradeConsent(Trade trade)
    {
        if (!trade.A.Ready && !trade.B.Ready && !trade.A.Confirmed && !trade.B.Confirmed)
            return false;
        string current = TradeContentFingerprint(trade);
        bool changed = ((trade.A.Ready || trade.A.Confirmed) && trade.A.ApprovedFingerprint != current) ||
                       ((trade.B.Ready || trade.B.Confirmed) && trade.B.ApprovedFingerprint != current);
        if (!changed) return false;
        trade.A.Ready = trade.B.Ready = false;
        trade.A.Confirmed = trade.B.Confirmed = false;
        trade.A.ApprovedFingerprint = trade.B.ApprovedFingerprint = "";
        trade.Revision = checked(trade.Revision + 1);
        EconomicDirty = true;
        return true;
    }

    private void InvalidateTradeConsents()
    {
        foreach (var trade in State.Trades.Values) InvalidateTradeConsent(trade);
    }
}
