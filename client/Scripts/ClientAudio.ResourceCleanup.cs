using Godot;

namespace Kairnfall.Client;

public partial class ClientAudio
{
    public override void _ExitTree()
    {
        // The audio-player children have exited. Do not retain native stream handles.
        foreach (var stream in cache.Values)
            if (GodotObject.IsInstanceValid(stream)) stream.Dispose();
        cache.Clear();
        voices.Clear();
    }
}
