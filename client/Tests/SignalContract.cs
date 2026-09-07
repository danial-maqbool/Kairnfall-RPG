using Godot;

namespace Kairnfall.Client.Tests;

/// <summary>Runs inside Godot so the native signal bridge, not only C#, is tested.</summary>
public partial class SignalContract : Control
{
    private int methodCalls;
    private sealed class Counter { public int Value; public void Increment() => Value++; }
    private void IncrementMethod() => methodCalls++;
    private static void Require(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
    }
    public override async void _Ready()
    {
        try
        {
            int captured = 0;
            var capturedButton = Ui.Button("captured callback", () => captured++);
            AddChild(capturedButton);
            capturedButton.EmitSignal(BaseButton.SignalName.Pressed);
            Require(captured == 1, "Captured button callback did not run.");

            var methodButton = Ui.Button("node method callback", IncrementMethod);
            AddChild(methodButton);
            methodButton.EmitSignal(BaseButton.SignalName.Pressed);
            Require(methodCalls == 1, "Node method callback did not run.");

            var counter = new Counter();
            var objectButton = Ui.Button("plain C# object callback", counter.Increment);
            AddChild(objectButton);
            objectButton.EmitSignal(BaseButton.SignalName.Pressed);
            Require(counter.Value == 1, "Plain C# object callback did not run.");

            bool completed = false;
            var asyncButton = Ui.Button("asynchronous callback", async () =>
            {
                await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
                completed = true;
            });
            AddChild(asyncButton);
            asyncButton.EmitSignal(BaseButton.SignalName.Pressed);
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            Require(completed, "Asynchronous callback did not resume.");

            for (int generation = 0; generation < 30; generation++)
            {
                int invocations = 0;
                var transient = Ui.Button("transient callback", () => invocations++);
                AddChild(transient);
                GC.Collect(); GC.WaitForPendingFinalizers();
                transient.EmitSignal(BaseButton.SignalName.Pressed);
                Require(invocations == 1, "Live button lost its callback after collection.");
                RemoveChild(transient);
                AddChild(transient);
                transient.EmitSignal(BaseButton.SignalName.Pressed);
                Require(invocations == 2, "Reattached button lost or duplicated its callback.");
                transient.QueueFree();
                await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            }
            capturedButton.EmitSignal(BaseButton.SignalName.Pressed);
            objectButton.EmitSignal(BaseButton.SignalName.Pressed);
            methodButton.EmitSignal(BaseButton.SignalName.Pressed);
            Require(captured == 2 && counter.Value == 2 && methodCalls == 2,
                "Long-lived button callbacks changed during page recreation.");
            GD.Print("SIGNAL_CONTRACT: captured, method, object, async, collection, and reattachment checks passed.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("SIGNAL_CONTRACT: " + error);
            GetTree().Quit(1);
        }
    }
}
