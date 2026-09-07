using Godot;

namespace Kairnfall.Client;

public partial class GameRoot
{
    public override void _ExitTree()
    {
        // Child controls have exited before the root releases their shared resources.
        lifetime.Cancel();
        settings.Dispose();
        lifetime.Dispose();
        Assets.Dispose();
        var ownedTheme = Theme;
        Theme = null;
        if (ownedTheme is not null && GodotObject.IsInstanceValid(ownedTheme)) ownedTheme.Dispose();
        // Flush transient managed image wrappers while the rendering server still exists.
        GC.Collect();
        GC.WaitForPendingFinalizers();
    }
}
