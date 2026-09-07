namespace Kairnfall.Core;

/// <summary>Defines compatible hand slots independently from item rarity and affixes.</summary>
public static class HandEquipment
{
    public static ItemDef? Definition(Character player, string slot, Catalog data)
    {
        if (!player.Equipment.TryGetValue(slot, out var id)) return null;
        var item = player.Inventory.FirstOrDefault(candidate => candidate.Id == id);
        return item is null ? null : data.Items.FirstOrDefault(candidate => candidate.Id == item.Template);
    }

    public static bool Compatible(ItemDef? weapon, ItemDef? offhand)
    {
        if (offhand is null) return true;
        if (offhand.Slot != "offhand") return false;
        if (offhand.Tags.Contains("quiver"))
            return weapon is not null && (weapon.Tags.Contains("bow") || weapon.Tags.Contains("crossbow"));
        return weapon is null || !weapon.Tags.Contains("two_handed");
    }

    public static bool HasUsableShield(Character player, Catalog data)
    {
        if (!player.Equipment.TryGetValue("offhand", out var id)) return false;
        var item = player.Inventory.FirstOrDefault(candidate => candidate.Id == id);
        if (item is null || item.Durability <= 0) return false;
        var offhand = Definition(player, "offhand", data);
        return offhand is not null && offhand.Tags.Contains("shield")
            && Compatible(Definition(player, "weapon", data), offhand);
    }

    public static bool IsProjectileWeapon(ItemDef? weapon) => weapon is not null
        && weapon.Tags.Any(tag => tag is "bow" or "crossbow" or "wand" or "tome");
}
