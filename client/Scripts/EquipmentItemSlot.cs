using Godot;

namespace Kairnfall.Client;

/// <summary>Completes selection on release so a pressed item survives until drag detection.</summary>
public partial class EquipmentItemSlot : ItemSlot
{
    public Action? Activated { get; set; }
    public Action<Vector2>? ContextRequested { get; set; }
    private bool pressed;
    private bool dragging;
    private bool skipRelease;

    public override void _Ready()
    {
        base._Ready();
        FocusMode = FocusModeEnum.All;
        MouseFilter = MouseFilterEnum.Stop;
    }

    public override void _GuiInput(InputEvent input)
    {
        if (input is InputEventKey { Pressed: true, Echo: false } key && key.PhysicalKeycode == Key.Enter)
        {
            AcceptEvent();
            Activated?.Invoke();
            return;
        }
        if (input is not InputEventMouseButton mouse) return;
        if (mouse.ButtonIndex == MouseButton.Right && mouse.Pressed)
        {
            pressed = false; dragging = false;
            AcceptEvent();
            ContextRequested?.Invoke(GetGlobalMousePosition());
            return;
        }
        if (mouse.ButtonIndex != MouseButton.Left) return;
        if (mouse.Pressed)
        {
            pressed = true; dragging = false; skipRelease = mouse.DoubleClick;
            GrabFocus();
            AcceptEvent();
            if (mouse.DoubleClick) Activated?.Invoke();
        }
        else
        {
            bool select = pressed && !dragging && !skipRelease && new Rect2(Vector2.Zero, Size).HasPoint(mouse.Position);
            pressed = false; dragging = false; skipRelease = false;
            AcceptEvent();
            if (select) Clicked?.Invoke();
        }
    }

    public override Variant _GetDragData(Vector2 position)
    {
        dragging = Item is not null;
        return base._GetDragData(position);
    }

    public override void _ExitTree()
    {
        Clicked = null; Activated = null; ContextRequested = null; Dropped = null;
        pressed = false; dragging = false;
    }
}
