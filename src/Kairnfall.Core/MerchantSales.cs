namespace Kairnfall.Core;

/// <summary>One sale quote for both the interface and authoritative transaction.</summary>
public static class MerchantSales
{
    public static long UnitPrice(ItemDef definition) => Math.Max(1, checked((long)definition.Value * 3) / 10);
    public static long Quote(Character self, NpcDef merchant, Item item, int quantity, Catalog data)
    {
        var owned = self.Inventory.FirstOrDefault(x => x.Id == item.Id) ?? throw new RuleException("The item is not in your backpack.");
        var def = data.Item(owned.Template);
        if (self.Health <= 0) throw new RuleException("Respawn before trading.");
        if (self.Zone != merchant.Zone || !self.Position.Finite || self.Position.Distance(merchant.Position) > 3
            || !WorldMap.LineOfSight(data.Zone(merchant.Zone), self.Position, merchant.Position))
            throw new RuleException("Move closer to the merchant.");
        if (merchant.Stock.Length == 0) throw new RuleException("This NPC does not trade goods.");
        if (quantity <= 0 || quantity > owned.Quantity || quantity > Math.Min(999, def.StackMax))
            throw new RuleException("Choose a quantity within this item's stack.");
        if (Items.Equipped(self, owned.Id)) throw new RuleException("Unequip this item before selling.");
        if (def.Type == "quest" || def.Value <= 0) throw new RuleException("This item cannot be sold.");
        if (merchant.Role != "provisioner" && !merchant.Stock.Any(x => data.Item(x).Type == def.Type))
            throw new RuleException("This merchant does not buy this item type.");
        long total = checked(UnitPrice(def) * quantity);
        if (total > Items.GoldCap - self.Gold) throw new RuleException("Gold limit reached.");
        return total;
    }
    public static string Problem(Character self, NpcDef merchant, Item item, int quantity, Catalog data)
    {
        try { Quote(self, merchant, item, quantity, data); return ""; }
        catch (RuleException error) { return error.Message; }
    }
}
