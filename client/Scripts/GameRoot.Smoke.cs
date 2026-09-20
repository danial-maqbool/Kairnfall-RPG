using Godot;
using Kairnfall.Core;
using System.Text.Json;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private double smokeTime;
    private bool smokeCapturing;
    private readonly List<SmokeCapture> smokeCaptures = [];
    private sealed record SmokeCapture(string File, string Page, long RenderedFrame);

    private async Task StartSmokeAsync()
    {
        try
        {
            if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("The graphical smoke requires a real display.");
            string address = System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL") ?? "http://127.0.0.1:5077";
            Connection = new GameConnection(address);
            string suffix = Guid.NewGuid().ToString("N")[..10];
            await Connection.SignInAsync("visual_" + suffix, "QA_" + Guid.NewGuid().ToString("N"), true, lifetime.Token);
            var remote = await Connection.CatalogAsync(lifetime.Token);
            if (remote.Validate().Count > 0) throw new InvalidDataException("Server catalog validation failed.");
            Data = remote; World.Data = Data;
            var character = await Connection.CreateCharacterAsync(new CharacterRequest
            {
                Name = "Visual " + suffix, Class = "vanguard",
                Appearance = new Appearance { Body = 0, Skin = 2, Hair = 4, HairColor = 1 }
            }, lifetime.Token);
            await Connection.ConnectAsync(character.Id, lifetime.Token);
            frontend.Visible = false; smokeStarted = true;
            GD.Print("SMOKE: authenticated Godot client entered the persistent server.");
        }
        catch (Exception error) { GD.PushError(error.ToString()); await ShutdownClientAsync(1); }
    }

    private void TickSmoke(double delta)
    {
        if (closing || smokeCapturing) return;
        smokeTime += delta;
        if (!Online)
        {
            if (smokeTime > 25)
            {
                GD.PushError("SMOKE: the client did not receive an online snapshot.");
                _ = ShutdownClientAsync(1);
            }
            return;
        }
        if (smokeTime < 3) return;
        smokeCapturing = true;
        _ = CaptureSmokeSequenceAsync();
    }

    private async Task CaptureSmokeSequenceAsync()
    {
        try
        {
            SetInitialHotbar();
            await CaptureSmokePageAsync("01-world.png", "");
            await CaptureSmokePageAsync("02-inventory.png", "Inventory");
            await CaptureSmokePageAsync("03-skills.png", "Skills");
            await CaptureSmokePageAsync("04-map.png", "Map");
            ClosePage();
            if (smokeCaptures.Count != 4 || Assets.Missing.Count != 0)
                throw new InvalidOperationException("Missing smoke captures or assets: " + string.Join(",", Assets.Missing));
            string directory = ScreenshotDirectory();
            System.IO.File.WriteAllText(System.IO.Path.Combine(directory, "capture-manifest.json"),
                JsonSerializer.Serialize(new { Mode = "graphical_smoke", Captures = smokeCaptures }, new JsonSerializerOptions { WriteIndented = true }));
            GD.Print("SMOKE: live world, inventory, skills, and map rendered without missing requested assets.");
            await ShutdownClientAsync(0);
        }
        catch (Exception error)
        {
            GD.PushError("SMOKE: " + error);
            await ShutdownClientAsync(1);
        }
    }

    private async Task CaptureSmokePageAsync(string filename, string expectedPage)
    {
        if (closing || !Online) throw new InvalidOperationException("Connection lost before capture: " + filename);
        if (expectedPage == "") ClosePage(); else OpenPage(expectedPage);
        UpdateHud();
        // Container layout is deferred. Wait for layout and then for an actual rendered frame.
        await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        if (closing || !Online || currentPage != expectedPage)
            throw new InvalidOperationException("The requested screen changed before capture: " + filename);
        if (expectedPage != "" && (gameWindow is null || !gameWindow.IsVisibleInTree()
            || gameWindow.GetGlobalRect().Intersection(GetViewport().GetVisibleRect()).Size.Y < 100))
            throw new InvalidOperationException("The requested panel is not visible: " + expectedPage);
        long frame = Engine.GetFramesDrawn();
        if (smokeCaptures.Count > 0 && frame <= smokeCaptures[^1].RenderedFrame)
            throw new InvalidOperationException("Two smoke captures used the same rendered frame.");
        SaveScreenshot(filename);
        smokeCaptures.Add(new SmokeCapture(filename, expectedPage == "" ? "World" : expectedPage, frame));
        GD.Print($"SMOKE_CAPTURE: {filename} page={(expectedPage == "" ? "World" : expectedPage)} renderedFrame={frame}");
    }

    private static string ScreenshotDirectory()
        => System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://screenshots");

    private void SaveScreenshot(string name)
    {
        if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("A headless run cannot produce graphical acceptance evidence.");
        string directory = ScreenshotDirectory();
        System.IO.Directory.CreateDirectory(directory);
        using var image = GetViewport().GetTexture().GetImage();
        if (image.IsEmpty()) throw new InvalidOperationException("The viewport returned an empty capture.");
        Error error = image.SavePng(System.IO.Path.Combine(directory, name));
        if (error != Error.Ok) throw new IOException("Could not save render evidence: " + error);
    }
}
