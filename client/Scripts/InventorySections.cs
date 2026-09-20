using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Views over one backpack. No extra containers or capacity are created.</summary>
public static class InventorySections
{
    public static readonly string[] Names = ["Equipped", "Ready to equip", "Locked or unavailable", "Tools and supplies"];
    public static int Group(Character self, Item item, Catalog data)
    {
        var definition = data.Item(item.Template);
        if (definition.Slot == "") return 3;
        if (Items.Equipped(self, item.Id)) return 0;
        return ExperienceRules.EquipmentProblem(self, item, data) == "" ? 1 : 2;
    }
}
