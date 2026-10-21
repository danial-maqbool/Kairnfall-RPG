using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

public partial class ClassicTutorialPresentationContract : Node
{
    private int checks;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private static T Property<T>(GameRoot game, string name)
        => (T)typeof(GameRoot).GetProperty(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS TUTORIAL PRESENTATION: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private static void Catalog(GameRoot game, Catalog data)
    {
        typeof(GameRoot).GetProperty("Data")!.SetValue(game, data); game.World.Data = data;
    }
    private static void Accept(GameRoot game, Snapshot snapshot)
    {
        game.World.Accept(new TransportPacket { Snapshot = snapshot }); Call(game, "UpdateHud");
    }
    private async Task Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") return;
        await Frame(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
            ?? throw new InvalidOperationException("Provide isolated screenshots.");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved native " + name);
    }
    public override async void _Ready()
    {
        GameRoot? game = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal), "Settings stay isolated");
            game = new GameRoot { LayoutMode = 1 }; AddChild(game); game.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
            game.SetProcess(false); await Frame();
            var normal = game.Data; var ordinary = new RealmEngine(normal).CreateCharacter("presentation-normal", "Normal View", "vanguard", new());
            var settings = Field<ConfigFile>(game, "settings"); settings.Clear();
            Accept(game, new Snapshot { Self = ordinary });
            Check(!Property<bool>(game, "ClassicControls") && !Property<bool>(game, "GridControls"), "Fresh ordinary controls retain deliberate selection and explicit attack");
            settings.SetValue("controls", "classic_target_attack", false); settings.SetValue("controls", "classic_grid", false);
            string controls = settings.EncodeToText();
            var optional = Wire.Copy(normal); ClassicTutorialContent.Enable(optional); Catalog(game, optional);
            Check(game.Assets.Icon("copper_ore") == game.Assets.Texture("items/copper_ore"), "Existing path-form catalog icons retain their original texture");
            Check(game.Assets.Icon("classic_wood") == game.Assets.Texture("items/oak_log"), "Bare tutorial aliases display an existing material texture without changing item identity");
            Check(game.Assets.Icon("classic_tinder") == game.Assets.Texture("items/meadow_leaf"), "Tutorial tinder resolves to its real plant icon");
            var realm = new RealmEngine(optional); var player = realm.CreateCharacter("presentation-tutorial", "Tutorial View", "vanguard", new());
            player.Position = new Point(14.5, 13.5); player.Facing = new Point(0, -1); realm.Active.Add(player.Id); realm.Tick(.1);
            var snapshot = realm.Snapshot(player.Id); var frontend = Field<Control>(game, "frontend"); frontend.Hide();
            string state = JsonSerializer.Serialize(snapshot.Self, Wire.Json);
            Accept(game, snapshot);
            Check(Property<bool>(game, "ClassicSessionActive") && Property<bool>(game, "GridControls") && Property<bool>(game, "ClassicControls"), "Accepted tutorial mode enables documented tile/context controls");
            Check(settings.EncodeToText() == controls, "Tutorial mode preserves saved normal-world control choices");
            Check(Math.Abs(game.World.Zoom - optional.ClassicTutorial!.TileZoom) < .0001, "Fresh tutorial uses the server's default zoom");
            Check(Property<bool>(game, "FocusHudEnabled"), "Fresh tutorial presents compact HUD without writing a preference");
            Check(Property<string>(game, "CharacterStartName") == optional.Zone(ClassicTutorialContent.ZoneId).Name, "Character creation names the actual tutorial start");
            Check(Field<Label>(game, "classicFoodCompact").Text.Contains("70 / 100") && Field<Label>(game, "classicFoodCompact").IsVisibleInTree(), "Accepted Food is visible in compact HUD");
            Check(Field<string>(game, "lastNoticeText") == "", "Initial retained milestone notice establishes a silent baseline");
            Check(JsonSerializer.Serialize(snapshot.Self, Wire.Json) == state, "Presentation cannot grant Food, progress, XP or inventory");
            var result = realm.Execute(player.Id, new GameCommand { Kind = "classic_interact", Target = "classic_first_sign", Sequence = 1 });
            Check(result.Ok && player.ClassicTutorial!.NoticeId > snapshot.Self.ClassicTutorial!.NoticeId, "Real sign command earns the server milestone: " + result.Message);
            Accept(game, realm.Snapshot(player.Id));
            Check(Field<string>(game, "lastNoticeText") == player.ClassicTutorial!.Notice, "Only the new authoritative notice reaches feedback");
            Member("lastNoticeText").SetValue(game, "retained feedback"); Accept(game, realm.Snapshot(player.Id));
            Check(Field<string>(game, "lastNoticeText") == "retained feedback", "Repeated snapshot cannot replay milestone feedback");
            player.ClassicTutorial!.Food = 12.25; Accept(game, realm.Snapshot(player.Id));
            Check(Field<Label>(game, "classicFoodCompact").Text.Contains("12 / 100"), "Food refresh follows accepted snapshots without an inventory change");
            GetWindow().Size = new Vector2I(916, 540); GetWindow().ContentScaleSize = new Vector2I(916, 540);
            await Capture("tutorial-food-compact-916");
            settings.SetValue("hud", "focus_world", false); Call(game, "ApplyFocusHud"); Call(game, "UpdateHud");
            Check(Field<Label>(game, "classicFoodExpanded").IsVisibleInTree() && !Field<Label>(game, "classicFoodCompact").IsVisibleInTree(), "Explicit expanded HUD retains the Food display");
            Call(game, "OpenPage", "Settings");
            var toggles = game.FindChildren("*", "CheckButton", true, false).OfType<CheckButton>().ToArray();
            Check(toggles.Any(x => x.Text == "Tile movement (classic mode)" && x.ButtonPressed && x.Disabled)
                && toggles.Any(x => x.Text == "Classic targeting and contextual action" && x.ButtonPressed && x.Disabled), "Settings accurately show tutorial-required controls");
            Call(game, "ClosePage");
            settings.SetValue("display", "native_world_zoom", 2); Member("classicPresentationCharacter").SetValue(game, "");
            Accept(game, realm.Snapshot(player.Id)); Check(game.World.Zoom == 2, "Explicit world zoom survives tutorial defaults");
            Catalog(game, normal); Accept(game, new Snapshot { Self = ordinary, Time = realm.State.Time });
            Check(!Property<bool>(game, "ClassicSessionActive") && !Property<bool>(game, "GridControls") && !Property<bool>(game, "ClassicControls"), "Ordinary world restores saved controls");
            Check(!Field<Label>(game, "classicFoodExpanded").Visible && !Field<Label>(game, "classicFoodCompact").Visible, "Ordinary character does not display tutorial Food");
            Check(Property<string>(game, "CharacterStartName") == normal.Zone(OpeningJourney.Home).Name, "Ordinary creation keeps its established starting town");
            await NativeTestLifetime.ReleaseSceneAsync(this, game); game = null;
            GD.Print($"CLASSIC_TUTORIAL_PRESENTATION_CONTRACT: {checks} checks passed. Offline native fixture; no live server or physical input approval."); GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_TUTORIAL_PRESENTATION_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
