using Godot;

namespace Kairnfall.Client.Tests;

/// <summary>Drain native audio work before destroying a scene in fast headless tests.</summary>
public static class NativeTestLifetime
{
    public static async Task ReleaseSceneAsync(Node owner, GameRoot game)
    {
        game.SetProcess(false);
        foreach (var audio in game.FindChildren("*", "Node", true, false).OfType<ClientAudio>())
            audio.ReleasePlayback();
        var tree = owner.GetTree();
        // Two process frames can finish before the separate audio mixer consumes Stop.
        // Retain the engine's resource-error checks after the real mixer has run.
        await owner.ToSignal(tree.CreateTimer(.15), SceneTreeTimer.SignalName.Timeout);
        game.QueueFree();
        await owner.ToSignal(tree, SceneTree.SignalName.ProcessFrame);
        await owner.ToSignal(tree, SceneTree.SignalName.ProcessFrame);
        await owner.ToSignal(tree.CreateTimer(.06), SceneTreeTimer.SignalName.Timeout);
    }
}
