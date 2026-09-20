using Godot;
using Kairnfall.Core;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private Task ShutdownAsync() => ShutdownClientAsync(0);

    private async Task ShutdownClientAsync(int exitCode)
    {
        if (closing) return;
        closing = true;
        SetProcess(false);
        StopCombatInput(); route.Clear(); pendingInteraction = null;
        lifetime.Cancel();
        if (audio is not null && GodotObject.IsInstanceValid(audio)) audio.ReleasePlayback();
        var connection = Connection;
        Connection = null;
        if (connection is not null) await DisposeConnectionAsync(connection);
        if (!IsInsideTree()) return;
        var tree = GetTree();
        // AudioServer processes stop requests during subsequent mix/process iterations.
        // Quitting in the same iteration retains active WAV playback objects.
        await ToSignal(tree.CreateTimer(.12), SceneTreeTimer.SignalName.Timeout);
        await ToSignal(tree, SceneTree.SignalName.ProcessFrame);
        tree.Quit(exitCode);
    }

    private static async Task DisposeConnectionAsync(GameConnection connection)
    {
        try { await connection.DisposeAsync(); }
        catch (OperationCanceledException) { }
        catch (Exception error) { GD.PushWarning("Connection cleanup: " + error.GetType().Name); }
    }

    public override void _ExitTree()
    {
        closing = true;
        StopCombatInput();
        lifetime.Cancel();
        refreshPage = null;
        if (audio is not null && GodotObject.IsInstanceValid(audio)) audio.ReleasePlayback();
        if (Connection is { } connection)
        {
            Connection = null;
            _ = DisposeConnectionAsync(connection);
        }
    }
}
