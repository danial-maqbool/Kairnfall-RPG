using Godot;

namespace Kairnfall.Client.Tests;

/// <summary>Exercises native GUI routing through the real main scene at explicit client resolutions.</summary>
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
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);

    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            // A headless display does not provide a desktop window size. With stretch
            // disabled, an implicit 64-pixel window cannot represent the supported UI.
            // Set the same physical dimensions as the graphical fixtures. Keep all
            // routing assertions, and repeat them after resizing the real scene.
            GD.Print("INPUT_INITIAL_VIEWPORT: " + GetViewport().GetVisibleRect().Size);
            GetWindow().Size = new Vector2I(1280, 720);
            await Frame();
            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            AddChild(game);
            Require(game.World is not null, "The main scene failed to initialize; inspect preceding engine errors.");
            game.SetProcess(false);
            await Frame();
            foreach (var node in game.FindChildren("*", "CenterContainer", true, false))
                ((Control)node.GetParent()).Hide();
            GetViewport().GuiReleaseFocus();

            foreach (var size in new[] { new Vector2I(1280, 720), new Vector2I(1920, 1080), new Vector2I(1280, 720) })
            {
                GetWindow().Size = size;
                await Frame(); await Frame();
                var viewport = GetViewport().GetVisibleRect();
                GD.Print("INPUT_ROUTING_VIEWPORT: requested=" + size + " actual=" + viewport.Size);
                Require(viewport.Size.IsEqualApprox(new Vector2(size.X, size.Y)), "The input fixture must use native window pixels.");
                Require(game.Size.IsEqualApprox(viewport.Size), "The main scene did not resize with its viewport.");
                int beforeWorld = worldClicks;
                RightClick(viewport.GetCenter());
                Require(worldClicks == beforeWorld + 1, "The main scene consumed a world click before unhandled input.");
                RightClick(new Vector2(50, 50));
                Require(worldClicks == beforeWorld + 1, "A HUD click leaked through to world input.");
                int beforeKeys = keyEvents;
                using (var press = new InputEventKey { Keycode = Key.D, PhysicalKeycode = Key.D, Pressed = true })
                    GetViewport().PushInput(press, true);
                using (var release = new InputEventKey { Keycode = Key.D, PhysicalKeycode = Key.D, Pressed = false })
                    GetViewport().PushInput(release, true);
                Require(keyEvents == beforeKeys + 1, "An unfocused physical-key event did not reach unhandled input.");
            }
            await NativeTestLifetime.ReleaseSceneAsync(this, game);
            Require(!GodotObject.IsInstanceValid(game), "The main scene was not freed after the input test.");
            GD.Print("INPUT_CONTRACT: world pointer routing, HUD consumption, native physical-key routing and repeated native-window resize passed.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("INPUT_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
