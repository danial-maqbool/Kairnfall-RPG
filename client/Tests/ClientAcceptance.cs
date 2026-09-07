using Godot;
using Kairnfall.Core;
using System.Text.Json;
using Timer = Godot.Timer;

namespace Kairnfall.Client.Tests;

/// <summary>Exercises the actual Godot interface and the authenticated server.</summary>
public partial class ClientAcceptance : Control
{
    private GameRoot game = null!;
    private int passed;
    private readonly string suffix = Guid.NewGuid().ToString("N")[..10];
    private readonly string password = "Qa_" + Guid.NewGuid().ToString("N");
    private string Username => "gui_" + suffix;

    private IEnumerable<T> Descendants<T>(Node node) where T : Node
    {
        if (node is T value) yield return value;
        foreach (Node child in node.GetChildren())
            foreach (var nested in Descendants<T>(child)) yield return nested;
    }
    private bool HasButton(string text) => Descendants<Button>(game)
        .Any(button => GodotObject.IsInstanceValid(button) && button.IsVisibleInTree() && button.Text == text);
    private void Click(string text)
    {
        var candidates = Descendants<Button>(game).Where(button => button.IsVisibleInTree() && button.Text == text).ToArray();
        if (candidates.Length != 1) throw new InvalidOperationException($"Expected one visible '{text}' button, found {candidates.Length}.");
        if (candidates[0].Disabled) throw new InvalidOperationException($"'{text}' is disabled.");
        GD.Print("UI_ACCEPTANCE click: " + text);
        candidates[0].EmitSignal(BaseButton.SignalName.Pressed);
    }
    private void Fill(string placeholder, string text)
    {
        var field = Descendants<LineEdit>(game).Single(edit => edit.IsVisibleInTree() && edit.PlaceholderText == placeholder);
        field.Text = text;
    }
    private void Check(bool condition, string description)
    {
        if (!condition) throw new InvalidOperationException(description);
        passed++;
        GD.Print("UI_ACCEPTANCE pass: " + description);
    }
    private async Task Frames(int count = 2)
    {
        for (int i = 0; i < count; i++) await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    }
    private async Task Until(Func<bool> condition, string description, double seconds = 25)
    {
        ulong deadline = Time.GetTicksMsec() + (ulong)(seconds * 1000);
        while (!condition())
        {
            if (Time.GetTicksMsec() >= deadline) throw new TimeoutException(description);
            await ToSignal(GetTree().CreateTimer(0.05), Timer.SignalName.Timeout);
        }
    }
    private void AddGame()
    {
        game = new GameRoot();
        AddChild(game);
        game.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
    }
    private void LoginFields()
    {
        Fill("https://your-realm.example", System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL") ?? "http://127.0.0.1:5077");
        Fill("Account name", Username);
        Fill("Password", password);
    }
    private async Task<CommandResult> Act(GameCommand command)
    {
        var result = await game.Connection!.ActAsync(command);
        if (!result.Ok) throw new InvalidOperationException(command.Kind + ": " + result.Message);
        await Until(() => game.Snapshot is { } snap && snap.Self.LastAction >= result.Sequence, "The UI did not receive the acknowledged action.");
        return result;
    }
    private void Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("Graphical acceptance requires a rendering display.");
        string directory = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? throw new InvalidOperationException("Set the screenshot output directory.");
        Directory.CreateDirectory(directory);
        using var image = GetViewport().GetTexture().GetImage();
        if (image.SavePng(Path.Combine(directory, name)) != Error.Ok) throw new IOException("Screenshot capture failed.");
    }
    private static void StopInput()
    {
        foreach (var action in new[] { "move_left", "move_right", "move_up", "move_down" }) Input.ActionRelease(action);
    }
    private async Task ReturnTo(Kairnfall.Core.Point position)
    {
        ulong deadline = Time.GetTicksMsec() + 8000;
        while (game.Snapshot!.Self.Position.Distance(position) > 0.25)
        {
            if (Time.GetTicksMsec() > deadline) throw new TimeoutException("Keyboard movement did not return to the starting road.");
            StopInput();
            var current = game.Snapshot.Self.Position;
            if (Math.Abs(position.X - current.X) > 0.15) Input.ActionPress(position.X > current.X ? "move_right" : "move_left");
            if (Math.Abs(position.Y - current.Y) > 0.15) Input.ActionPress(position.Y > current.Y ? "move_down" : "move_up");
            await ToSignal(GetTree().CreateTimer(0.05), Timer.SignalName.Timeout);
        }
        StopInput();
        await Frames(4);
    }

    public override async void _Ready()
    {
        GameConnection? second = null;
        try
        {
            GD.Print("UI_ACCEPTANCE_V2 assembly=" + typeof(GameRoot).Assembly.ManifestModule.ModuleVersionId);
            AddGame();
            await Frames(3);
            Check(HasButton("Create account"), "The real login page opens.");
            LoginFields();
            Fill("Repeat password for a new account", password);
            Click("Create account");
            await Until(() => HasButton("Create character"), "Account registration through the native button failed.");
            Check(game.Connection?.Session is not null, "Native registration produced an authenticated session.");
            Click("Create character");
            await Frames(3);
            Fill("Character name: 3–20 characters", "Gui " + suffix);
            Check(game.Data.Classes.Count == 8 && game.Data.Skills.Count == 60, "The client loaded the required class and skill definitions.");
            Click("Begin at Wayfarer's Rest");
            await Until(() => game.Connection?.Connected == true && game.Snapshot is not null, "Character creation or world entry failed.");
            Check(game.Snapshot!.Self.Zone == "wayfarers_rest", "The new character starts at Wayfarer's Rest.");
            var origin = game.Snapshot.Self.Position;
            GetViewport().GuiReleaseFocus();
            Input.ActionPress("move_right");
            await Until(() => game.Snapshot!.Self.Position.Distance(origin) > 1, "Keyboard input did not change authoritative position.", 8);
            StopInput();
            await ReturnTo(origin);
            Check(WorldMap.Fits(game.Data.Zone(game.Snapshot.Self.Zone), game.Snapshot.Self.Position), "Keyboard movement preserves server collision constraints.");
            await Frames(10);
            Capture("01-world.png");

            Click("Inventory"); await Frames(5); Capture("02-inventory.png");
            Check(Descendants<ItemSlot>(game).Any(slot => slot.Item?.Template == "healing_potion"), "The inventory displays actual server-owned items.");
            var potion = game.Snapshot.Self.Inventory.First(item => item.Template == "healing_potion");
            int originalQuantity = potion.Quantity;
            int originalStacks = game.Snapshot.Self.Inventory.Count;
            await Act(new GameCommand { Kind = "split", Item = potion.Id, Amount = 1 });
            Check(game.Snapshot.Self.Inventory.Count == originalStacks + 1 &&
                game.Snapshot.Self.Inventory.Where(item => item.Template == "healing_potion").Sum(item => item.Quantity) == originalQuantity,
                "Stack splitting creates a second instance without changing total quantity.");
            var rune = game.Snapshot.Self.Inventory.First(item => game.Data.Item(item.Template).Type == "rune");
            string weapon = game.Snapshot.Self.Equipment["weapon"];
            await Act(new GameCommand { Kind = "socket", Target = weapon, Item = rune.Id });
            Check(Items.Owned(game.Snapshot.Self, weapon).Runes.Count == 1, "The server sockets the owned rune into the starting weapon.");

            Click("Skills"); await Frames(5); Capture("03-skills.png");
            Check(Descendants<Label>(game).Any(label => label.IsVisibleInTree() && label.Text.Contains("Mining", StringComparison.Ordinal)), "The skills page shows Mining.");
            Click("World map  [M]"); await Frames(5); Capture("04-map.png");
            Check(game.Assets.Missing.Count == 0, "The rendered pages requested no missing assets.");

            second = new GameConnection(System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL") ?? "http://127.0.0.1:5077");
            await second.SignInAsync("peer_" + suffix, "Qa_" + Guid.NewGuid().ToString("N"), true);
            var peer = await second.CreateCharacterAsync(new CharacterRequest { Name = "Peer " + suffix, Class = "ranger" });
            await second.ConnectAsync(peer.Id);
            Snapshot? peerSnapshot = null;
            void DrainPeer()
            {
                while (second.TryRead(out var packet)) if (packet?.Snapshot is { } snap) peerSnapshot = snap;
            }
            await Until(() => { DrainPeer(); return peerSnapshot is not null; }, "The second client did not receive its initial state.");
            int peerPotions = peerSnapshot!.Self.Inventory.Where(item => item.Template == "healing_potion").Sum(item => item.Quantity);
            await Until(() => game.Snapshot!.Players.Any(player => player.Id == peer.Id), "A second authenticated client was not visible.");
            Check(true, "Two authenticated clients share the same authoritative world.");
            await Act(new GameCommand { Kind = "trade_invite", Target = peer.Id });
            var trade = game.Snapshot!.Trades.Single();
            var offered = game.Snapshot.Self.Inventory.First(item => item.Template == "healing_potion" && item.Quantity == 1);
            await Act(new GameCommand { Kind = "trade_offer", Target = trade.Id, Item = offered.Id, Amount = 1 });
            int revision = game.Snapshot.Trades.Single().Revision;
            await Act(new GameCommand { Kind = "trade_ready", Target = trade.Id, Amount = revision });
            var peerReady = await second.ActAsync(new GameCommand { Kind = "trade_ready", Target = trade.Id, Amount = revision });
            Check(peerReady.Ok, "The second participant can independently review the trade.");
            await Act(new GameCommand { Kind = "trade_confirm", Target = trade.Id, Amount = revision });
            var peerConfirmed = await second.ActAsync(new GameCommand { Kind = "trade_confirm", Target = trade.Id, Amount = revision });
            Check(peerConfirmed.Ok, "Both participants must confirm the trade revision.");
            await Until(() => game.Snapshot!.Trades.Count == 0 && game.Snapshot.Self.Inventory.All(item => item.Id != offered.Id), "The completed trade did not update the first client.");
            await Until(() =>
            {
                DrainPeer();
                // Stack merging can retire the transferred stack ID. Verify the
                // conserved quantity rather than requiring the old stack ID.
                return peerSnapshot!.Self.Inventory.Where(item => item.Template == "healing_potion").Sum(item => item.Quantity) == peerPotions + 1;
            }, "The second client did not receive the transferred quantity.");
            Check(game.Snapshot.Self.Inventory.Where(item => item.Template == "healing_potion").Sum(item => item.Quantity) == originalQuantity - 1,
                "Trade conserves the total quantity across both clients.");

            string characterId = game.Snapshot.Self.Id;
            string inventory = JsonSerializer.Serialize(game.Snapshot.Self.Inventory, Wire.Json);
            long gold = game.Snapshot.Self.Gold;
            await game.Connection!.SignOutAsync();
            game.QueueFree(); await Frames(5);
            AddGame(); await Frames(3);
            LoginFields(); Click("Sign in");
            await Until(() => HasButton("Enter world"), "Reauthentication did not show the saved character.");
            Click("Enter world");
            await Until(() => game.Snapshot?.Self.Id == characterId && game.Connection?.Connected == true, "The saved character did not reconnect.");
            Check(game.Snapshot!.Self.Gold == gold && JsonSerializer.Serialize(game.Snapshot.Self.Inventory, Wire.Json) == inventory,
                "Reauthentication preserves item ownership, runes, stack quantities, and gold.");
            await Frames(5);
            Check(game.Assets.Missing.Count == 0, "Reconnect does not request missing assets.");
            await second.DisposeAsync(); second = null;
            await game.Connection!.SignOutAsync();
            GD.Print($"UI_ACCEPTANCE_V2_COMPLETE passed={passed} failed=0");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("UI_ACCEPTANCE_V2_FAILED: " + error);
            if (second is not null) await second.DisposeAsync();
            GetTree().Quit(1);
        }
        finally { StopInput(); }
    }
}
