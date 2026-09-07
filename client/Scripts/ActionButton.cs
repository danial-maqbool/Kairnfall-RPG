using Godot;

namespace Kairnfall.Client;

/// <summary>
/// Keeps ordinary C# callbacks outside the native Callable bridge.
/// The native signal targets this live Godot node. The node then invokes the
/// stored delegate in managed code, including delegates on non-Godot objects.
/// </summary>
public partial class ActionButton : Button
{
    public Action? PressedAction { get; set; }

    public override void _EnterTree()
    {
        Pressed += InvokePressedAction;
    }

    public override void _ExitTree()
    {
        Pressed -= InvokePressedAction;
    }

    private void InvokePressedAction()
    {
        PressedAction?.Invoke();
    }
}
