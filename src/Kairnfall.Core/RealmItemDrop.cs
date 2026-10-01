namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private string DropItem(Character player, string id, int quantity)
    {
        var owned = Items.Owned(player, id);
        Need(Data.Item(owned.Template).Type != "quest", "Quest items must stay in your backpack.");
        Need(player.Position.Finite && WorldMap.Fits(Data.Zone(player.Zone), player.Position), "Stand on valid ground before dropping items.");
        // Existing Take owns stack splitting, equipment safety and item metadata.
        // Execute's receipt/rollback path makes transfer replay-safe and atomic.
        var item = Items.Take(player.Inventory, id, quantity, player);
        var pile = new LootPile
        {
            Zone = player.Zone, Position = player.Position, Owner = player.Id,
            Items = [item], PublicAt = State.Time + 60,
            Expires = State.Time + LootPile.LifetimeSeconds
        };
        Loot.Add(pile.Id, pile);
        return "Dropped " + quantity + " " + Data.Item(item.Template).Name + ". Ground loot expires after " + LootPile.LifetimeSeconds + " seconds.";
    }
}
