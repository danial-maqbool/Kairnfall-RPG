using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>Compact presentation only; all item actions retain authoritative item IDs.</summary>
public partial class ClassicItemSlot : EquipmentItemSlot
{
    public override void _Ready()
    {
        base._Ready();
        if (Item is null)
        {
            FocusMode = FocusModeEnum.None;
            MouseFilter = MouseFilterEnum.Ignore;
            MouseDefaultCursorShape = CursorShape.Arrow;
        }
    }

    // Enter/Space retains the compact panel's inspection behavior. Equipment
    // activation remains an explicit double-click or contextual action.
    protected override void ActivateFromKeyboard() => Clicked?.Invoke();

    public override void _Draw()
    {
        var rect = new Rect2(Vector2.Zero, Size);
        DrawRect(rect, new Color(.065f, .12f, .08f, .92f));
        DrawRect(rect, HasFocus() || Selected ? Ui.Gold : Item is null ? new Color("758078") : Ui.RarityColor(Item.Rarity), false, 2);
        DrawLine(new Vector2(2, 2), new Vector2(Size.X - 2, 2), new Color("a5afa7"));
        DrawLine(new Vector2(2, 2), new Vector2(2, Size.Y - 2), new Color("a5afa7"));
        if (Icon is not null) DrawTextureRect(Icon, PixelPresentation.InventoryIconRect(Size, Icon.GetSize()), false);
        if (ItemElement != Element.Physical)
        {
            var badge = new Rect2(Size.X - 18, 3, 15, 15);
            DrawRect(badge, Ui.Ink); DrawRect(badge, Ui.ElementColor(ItemElement), false, 1);
            DrawString(ThemeDB.FallbackFont, new Vector2(badge.Position.X + 4, badge.Position.Y + 12),
                Ui.ElementGlyph(ItemElement), HorizontalAlignment.Left, -1, 10, Ui.ElementColor(ItemElement));
        }
        if (Equipped) DrawString(ThemeDB.FallbackFont, new Vector2(4, 14), "E", HorizontalAlignment.Left, -1, 11, Ui.Gold);
        if (Item is { Quantity: > 1 })
        {
            string quantity = Item.Quantity.ToString();
            DrawStringOutline(ThemeDB.FallbackFont, new Vector2(4, Size.Y - 5), quantity, HorizontalAlignment.Left, -1, 13, 3, Ui.Ink);
            DrawString(ThemeDB.FallbackFont, new Vector2(4, Size.Y - 5), quantity, HorizontalAlignment.Left, -1, 13, Ui.Text);
        }
    }
}
