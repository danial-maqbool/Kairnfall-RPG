using Godot;

namespace Kairnfall.Client.Tests;

/// <summary>Exercises native GUI routing through the real main scene without a server.</summary>
public partial class InputContract : Node
{
    private int worldClicks;
    private int keyEvents;

    public override void _UnhandledInput(InputEvent input)
    {
        if (input is InputEventMouseButton { Pressed: true, ButtonIndex: MouseButton.Right }) worldClicks++;
        if (input is InputEventKey { Pressed: true, PhysicalKeycode: Key.D }) keyEvents++;
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private void RightClick(Vector2 position)
    {
        using var press = new InputEventMouseButton
        {
            Position = position, GlobalPosition = position,
            ButtonIndex = MouseButton.Right, ButtonMask = MouseButtonMask.Right, Pressed = true
        };
        using var release = new InputEventMouseButton
        {
            Position = position, GlobalPosition = position, ButtonIndex = MouseButton.Right, Pressed = false
        };
        GetViewport().PushInput(press, true);
        GetViewport().PushInput(release, true);
    }

    public override async void _Ready()
    {
        try
        {
            GameRoot game;
            using (var scene = GD.Load<PackedScene>("res://Main.tscn"))
                game = scene.Instantiate<GameRoot>();
            AddChild(game);
            Require(game.World is not null, "The main scene failed to initialize; inspect preceding engine errors.");
            game.SetProcess(false); // Keep the offline fixture HUD visible without a snapshot.
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            // Hide only the login overlay; retain the real world, HUD, and root controls.
            foreach (var node in game.FindChildren("*", "CenterContainer", true, false))
                ((Control)node.GetParent()).Hide();
            GetViewport().GuiReleaseFocus();
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            RightClick(GetViewport().GetVisibleRect().Size / 2);
            Require(worldClicks == 1, "The main scene consumed a world click before unhandled input.");
            RightClick(new Vector2(50, 50));
            Require(worldClicks == 1, "A HUD click leaked through to world input.");
            using (var press = new InputEventKey { Keycode = Key.D, PhysicalKeycode = Key.D, Pressed = true })
                GetViewport().PushInput(press, true);
            using (var release = new InputEventKey { Keycode = Key.D, PhysicalKeycode = Key.D, Pressed = false })
                GetViewport().PushInput(release, true);
            Require(keyEvents == 1, "An unfocused physical-key event did not reach unhandled input.");
            game.QueueFree();
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
            Require(!GodotObject.IsInstanceValid(game), "The main scene was not freed after the input test.");
            GD.Print("INPUT_CONTRACT: world pointer routing, HUD consumption, and native physical-key routing passed.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("INPUT_CONTRACT: " + error);
            GetTree().Quit(1);
        }
    }
}
