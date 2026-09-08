using Godot;
using Kairnfall.Core;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot : Control
{
    public PixelAssets Assets { get; private set; } = new();
    public Catalog Data { get; private set; } = null!;
    public GameConnection? Connection { get; private set; }
    public WorldView World { get; private set; } = null!;
    public Snapshot? Snapshot => World?.Snapshot;
    private Control interfaceRoot = null!;
    private Control frontend = null!;
    private PanelContainer? gameWindow;
    private VBoxContainer? page;
    private Label notice = null!;
    private Label location = null!;
    private Label characterTitle = null!;
    private Label healthText = null!;
    private Label manaText = null!;
    private Label staminaText = null!;
    private Label targetText = null!;
    private ProgressBar health = null!, mana = null!, stamina = null!;
    private RichTextLabel chatLog = null!;
    private LineEdit chatInput = null!;
    private OptionButton chatChannel = null!;
    private readonly List<string> history = [];
    private readonly Dictionary<string, string> knownNames = [];
    private List<GroupInvitation> invitations = [];
    private readonly Dictionary<string, Key> bindings = new()
    {
        ["move_left"] = Key.A, ["move_right"] = Key.D, ["move_up"] = Key.W, ["move_down"] = Key.S,
        ["interact"] = Key.E, ["inventory"] = Key.I, ["character"] = Key.C, ["skills"] = Key.K,
        ["quests"] = Key.J, ["map"] = Key.M, ["abilities"] = Key.B, ["crafting"] = Key.F,
        ["social"] = Key.P, ["target_next"] = Key.Tab
    };
    private readonly ConfigFile settings = new();
    private string awaitingBinding = "";
    private string currentPage = "";
    private string selectedItem = "";
    private string selectedBag = "inventory";
    private string selectedRecipe = "";
    private string selectedNpc = "";
    private string selectedRune = "";
    private string selectedQuest = "";
    private string selectedZone = "";
    private string selectedTrade = "";
    private string selectedTarget = "";
    private string selectedTargetKind = "";
    private string placement = "";
    private string structureRecipe = "";
    private WorldTarget? pendingInteraction;
    private readonly List<Point> route = [];
    private readonly string[] hotbar = new string[10];
    private readonly Button[] hotbarButtons = new Button[10];
    private Action? refreshPage;
    private double moveClock, uiClock, attackClock, noticeUntil;
    private bool actionBusy, movementBusy, autoAttack, closing;
    private Vector2 lastInput;
    private CancellationTokenSource lifetime = new();
    private string lastPageStamp = "";
    private ClientAudio? audio;
    private bool smoke;
    private bool smokeStarted;
    private double smokeTime;
    private int smokeStage;

    public override void _Ready()
    {
        try
        {
            Theme = Ui.BuildTheme();
            settings.Load("user://settings.cfg");
            InstallBindings();
            Data = PixelAssets.LoadCatalog();
            World = new WorldView { Assets = Assets, Data = Data };
            AddChild(World);
            interfaceRoot = new Control { MouseFilter = MouseFilterEnum.Ignore };
            AddChild(interfaceRoot); interfaceRoot.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            frontend = new Control { MouseFilter = MouseFilterEnum.Ignore };
            interfaceRoot.AddChild(frontend); frontend.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            BuildHud();
            audio = new ClientAudio(); AddChild(audio);
            audio.SetVolumes((float)settings.GetValue("audio", "music", .35).AsDouble(), (float)settings.GetValue("audio", "effects", .65).AsDouble());
            World.WeatherEnabled = settings.GetValue("display", "weather", true).AsBool();
            World.ShowNames = settings.GetValue("display", "names", true).AsBool();
            World.Zoom = (float)settings.GetValue("display", "zoom", 2).AsDouble();
            ShowLogin();
            smoke = OS.GetCmdlineUserArgs().Contains("--smoke");
            if (smoke) _ = StartSmokeAsync();
        }
        catch (Exception error)
        {
            GD.PushError(error.ToString());
            var message = Ui.Label("Kairnfall could not start.\n\n" + error.Message + "\n\nRun bootstrap.ps1 from the repository root.", 19, Ui.Text, true);
            AddChild(message); message.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect); message.OffsetLeft = 50; message.OffsetTop = 50; message.OffsetRight = -50;
            if (OS.GetCmdlineUserArgs().Contains("--smoke")) GetTree().Quit(1);
        }
    }

    private void InstallBindings()
    {
        foreach (var action in bindings.Keys.ToArray())
        {
            if (settings.HasSectionKey("keys", action)) bindings[action] = (Key)settings.GetValue("keys", action).AsInt64();
            ApplyBinding(action);
        }
        foreach (var entry in new[] { ("move_left", Key.Left), ("move_right", Key.Right), ("move_up", Key.Up), ("move_down", Key.Down) })
            InputMap.ActionAddEvent(entry.Item1, new InputEventKey { PhysicalKeycode = entry.Item2 });
    }
    private void ApplyBinding(string action)
    {
        if (!InputMap.HasAction(action)) InputMap.AddAction(action);
        InputMap.ActionEraseEvents(action);
        InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = bindings[action] });
    }
    private bool Typing => GetViewport().GuiGetFocusOwner() is LineEdit or TextEdit;
    private bool Online => Connection?.Connected == true && Snapshot is not null;

    public override void _Process(double delta)
    {
        if (World is null || Data is null) return;
        if (Connection is { } connection)
        {
            int drained = 0;
            while (drained++ < 150 && connection.TryRead(out var packet))
            {
                if (packet is null) continue;
                if (packet.Snapshot is { } snapshot)
                {
                    World.Accept(packet);
                    invitations = packet.Invitations ?? [];
                    knownNames[snapshot.Self.Id] = snapshot.Self.Name;
                    foreach (var other in snapshot.Players) knownNames[other.Id] = other.Name;
                }
                if (packet.Chat is { } chat) AddChat($"[{chat.Channel}] {chat.Name}: {chat.Text}");
                if (packet.Kind == "error") Notify(packet.Error, true);
            }
        }
        if (Online)
        {
            var self = Snapshot!.Self;
            Vector2 input = !Typing && awaitingBinding == "" ? Input.GetVector("move_left", "move_right", "move_up", "move_down") : Vector2.Zero;
            if (input.LengthSquared() > .01f) { route.Clear(); pendingInteraction = null; }
            if (input.LengthSquared() < .01f && route.Count > 0 && !Typing)
            {
                while (route.Count > 0 && self.Position.Distance(route[0]) < .32) route.RemoveAt(0);
                if (route.Count > 0)
                {
                    var dir = self.Position.Direction(route[0]); input = new Vector2((float)dir.X, (float)dir.Y);
                }
            }
            if (pendingInteraction is { } interaction && self.Position.Distance(interaction.Position) < 2.2)
            {
                pendingInteraction = null; route.Clear(); input = Vector2.Zero; Activate(interaction);
            }
            moveClock += delta;
            if ((moveClock >= .08 || (input - lastInput).LengthSquared() > .1f) && !movementBusy)
            {
                moveClock = 0; lastInput = input; SendMovement(input);
            }
            attackClock += delta;
            if (autoAttack && attackClock > .3 && !actionBusy && selectedTargetKind == "creature")
            {
                attackClock = 0;
                var target = Snapshot.Creatures.FirstOrDefault(x => x.Id == selectedTarget && x.Health > 0);
                if (target is null) autoAttack = false;
                else
                {
                    double range = self.Equipment.TryGetValue("weapon", out var weapon) ? Data.Item(Items.Owned(self, weapon).Template).Range : 1.7;
                    if (self.Position.Distance(target.Position) <= range && self.Cooldowns.GetValueOrDefault("attack") <= Snapshot.Time)
                        _ = SendAsync(new GameCommand { Kind = "attack", Target = target.Id }, quiet: true);
                }
            }
            audio?.SetRegion(Data.Zone(self.Zone), Snapshot.Creatures.Any(x => Data.Mob(x.Template).Boss && x.Target == self.Id));
        }
        uiClock += delta;
        if (uiClock > .2)
        {
            uiClock = 0; UpdateHud();
            if (refreshPage is not null && !Input.IsMouseButtonPressed(MouseButton.Left))
            {
                string stamp = PageStamp();
                if (stamp != lastPageStamp) { lastPageStamp = stamp; refreshPage(); }
            }
        }
        if (notice is not null && Time.GetTicksMsec() / 1000.0 > noticeUntil) notice.Text = "";
        if (smoke && smokeStarted) TickSmoke(delta);
    }

    private async void SendMovement(Vector2 direction)
    {
        if (Connection is null || !Connection.Connected) return;
        movementBusy = true;
        try { await Connection.MoveAsync(direction.X, direction.Y, lifetime.Token); }
        catch (Exception e) when (e is not OperationCanceledException) { Notify(e.Message, true); }
        catch (OperationCanceledException) { }
        finally { movementBusy = false; }
    }

    private async Task<CommandResult?> SendAsync(GameCommand command, bool quiet = false)
    {
        if (!Online || actionBusy) return null;
        actionBusy = true;
        try
        {
            var result = await Connection!.ActAsync(command, lifetime.Token);
            if (!result.Ok || !quiet) Notify(result.Message, !result.Ok);
            if (result.Ok)
            {
                if (command.Kind is "attack" or "cast" or "gather") World.Animate(Snapshot!.Self.Id, command.Kind == "cast" ? 3 : 2, .6);
                audio?.PlayEffect(command.Kind);
                lastPageStamp = "";
            }
            return result;
        }
        catch (OperationCanceledException) { return null; }
        catch (Exception e) { Notify(e.Message, true); return null; }
        finally { actionBusy = false; }
    }
    private void Send(string kind, string target = "", string item = "", int amount = 1, string arg = "")
        => _ = SendAsync(new GameCommand { Kind = kind, Target = target, Item = item, Amount = amount, Arg = arg });

    public override void _UnhandledInput(InputEvent @event)
    {
        if (@event is InputEventKey { Pressed: true, Echo: false } key)
        {
            if (awaitingBinding != "")
            {
                if (key.PhysicalKeycode != Key.Escape)
                {
                    bindings[awaitingBinding] = key.PhysicalKeycode; ApplyBinding(awaitingBinding);
                    settings.SetValue("keys", awaitingBinding, (long)key.PhysicalKeycode); settings.Save("user://settings.cfg");
                }
                awaitingBinding = ""; OpenPage("Settings"); GetViewport().SetInputAsHandled(); return;
            }
            if (key.PhysicalKeycode == Key.Escape)
            {
                if (Typing) GetViewport().GuiReleaseFocus();
                else if (placement != "") { placement = ""; Notify("Placement cancelled."); }
                else if (gameWindow is not null) ClosePage();
                else { autoAttack = false; route.Clear(); pendingInteraction = null; if (Online) OpenPage("Settings"); }
                GetViewport().SetInputAsHandled(); return;
            }
            if (!Online) return;
            if (key.PhysicalKeycode == Key.Enter) { chatInput.GrabFocus(); GetViewport().SetInputAsHandled(); return; }
            if (Typing) return;
            foreach (string action in new[] { "inventory", "character", "skills", "quests", "map", "abilities", "crafting", "social" })
                if (key.IsActionPressed(action)) { OpenPage(Ui.Words(action)); GetViewport().SetInputAsHandled(); return; }
            if (key.IsActionPressed("interact"))
            {
                var closest = World.Nearest(Snapshot!.Self.Position);
                if (closest is { } target) Activate(target); else Notify("Move closer to an NPC, resource, chest, entrance, or dropped item.");
                GetViewport().SetInputAsHandled(); return;
            }
            if (key.IsActionPressed("target_next"))
            {
                var targets = Snapshot!.Creatures.Where(x => x.Health > 0).OrderBy(x => x.Position.Distance(Snapshot.Self.Position)).ToList();
                if (targets.Count > 0) { int index = targets.FindIndex(x => x.Id == selectedTarget); SelectTarget("creature", targets[(index + 1) % targets.Count].Id); }
                GetViewport().SetInputAsHandled(); return;
            }
            int code = (int)key.PhysicalKeycode;
            if (code is >= 48 and <= 57) { UseHotbar(code == 48 ? 9 : code - 49); GetViewport().SetInputAsHandled(); return; }
        }
        if (!Online) return;
        if (@event is InputEventMouseButton { Pressed: true } mouse)
        {
            if (mouse.ButtonIndex == MouseButton.WheelUp || mouse.ButtonIndex == MouseButton.WheelDown)
            {
                World.Zoom = Math.Clamp(World.Zoom + (mouse.ButtonIndex == MouseButton.WheelUp ? 1 : -1), 1, 3);
                settings.SetValue("display", "zoom", World.Zoom); settings.Save("user://settings.cfg"); return;
            }
            Point point = World.ScreenToWorld(mouse.Position);
            if (placement != "" && mouse.ButtonIndex == MouseButton.Left)
            {
                _ = SendAsync(new GameCommand { Kind = placement, Item = structureRecipe, X = point.X, Y = point.Y }); placement = ""; return;
            }
            if (mouse.ButtonIndex == MouseButton.Right) { WalkTo(point); return; }
            if (mouse.ButtonIndex == MouseButton.Left && World.Pick(mouse.Position) is { } hit)
            {
                SelectTarget(hit.Kind, hit.Id);
                if (hit.Kind == "creature") autoAttack = true;
                else if (hit.Kind == "player") OpenPage("Social");
                else if (Snapshot!.Self.Position.Distance(hit.Position) < 2.2) Activate(hit);
                else { pendingInteraction = hit; WalkTo(hit.Position, keepInteraction: true); }
            }
        }
    }

    private void SelectTarget(string kind, string id) { selectedTargetKind = kind; selectedTarget = id; World.TargetId = id; autoAttack = false; }
    private void WalkTo(Point point, bool keepInteraction = false)
    {
        if (Snapshot is null) return;
        var zone = Data.Zone(Snapshot.Self.Zone);
        if (!point.Finite || !WorldMap.Fits(zone, point)) { Notify("That position is blocked.", true); return; }
        if (!keepInteraction) pendingInteraction = null;
        route.Clear(); route.AddRange(WorldMap.FindPath(zone, Snapshot.Self.Position, point, 16000));
        if (route.Count == 0) Notify("No nearby route was found. Use the roads or move closer.", true);
    }
    private async void Activate(WorldTarget target)
    {
        SelectTarget(target.Kind, target.Id);
        if (target.Kind == "npc")
        {
            var result = await SendAsync(new GameCommand { Kind = "talk", Target = target.Id }, true);
            if (result?.Ok == true) { selectedNpc = target.Id; OpenPage("Dialogue"); }
        }
        else if (target.Kind == "node")
        {
            var node = Snapshot?.Nodes.FirstOrDefault(x => x.Id == target.Id);
            if (node is not null && node.Template.StartsWith("structure_", StringComparison.Ordinal)) OpenPage("Crafting");
            else Send("gather", target.Id);
        }
        else if (target.Kind == "exit") Send("transition", target.Id);
        else if (target.Kind == "chest") Send("chest", target.Id);
        else if (target.Kind == "loot") Send("loot", target.Id);
    }
    private void UseHotbar(int index)
    {
        if (Snapshot is null || index < 0 || index >= hotbar.Length || string.IsNullOrEmpty(hotbar[index])) return;
        var ability = Data.Ability(hotbar[index]);
        var target = World.ScreenToWorld(GetGlobalMousePosition());
        string targetId = selectedTarget;
        if (targetId == "" && ability.Kind is "heal" or "shield" or "buff") targetId = Snapshot.Self.Id;
        _ = SendAsync(new GameCommand { Kind = "cast", Item = ability.Id, Target = targetId, X = target.X, Y = target.Y }, true);
    }
    private void SetInitialHotbar()
    {
        if (Snapshot is null) return;
        var abilities = Data.Abilities.Where(x => (x.Class == "" || x.Class == Snapshot.Self.Class) && Progression.Level(Snapshot.Self, x.Skill) >= x.Requirement).OrderBy(x => x.Requirement).ToList();
        for (int i = 0; i < hotbar.Length; i++)
        {
            string saved = settings.GetValue("hotbar_" + Snapshot.Self.Id, i.ToString(), "").AsString();
            hotbar[i] = Data.Abilities.Any(x => x.Id == saved) ? saved : i < abilities.Count ? abilities[i].Id : "";
        }
    }
    private string PageStamp()
    {
        if (Snapshot is null) return "offline";
        return currentPage + selectedItem + selectedBag + selectedRecipe + selectedQuest + selectedNpc + JsonSerializer.Serialize(new { Snapshot.Self.LastAction, Snapshot.Self.Inventory, Snapshot.Self.Bank, Snapshot.Self.SkillXp, Snapshot.Self.Quests, Snapshot.Self.Gold, Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, invitations }, Wire.Json);
    }
    private string PlayerName(string id) => knownNames.GetValueOrDefault(id, id == "" ? "None" : "Traveler " + id[..Math.Min(6, id.Length)]);
    private void Notify(string text, bool error = false)
    {
        if (notice is null || !GodotObject.IsInstanceValid(notice)) return;
        notice.Text = text; notice.AddThemeColorOverride("font_color", error ? Ui.Danger : Ui.Text); noticeUntil = Time.GetTicksMsec() / 1000.0 + 6;
        if (text != "") AddChat("[System] " + text);
    }
    private void AddChat(string text)
    {
        history.Add(text); if (history.Count > 120) history.RemoveAt(0);
        if (chatLog is not null) chatLog.Text = string.Join("\n", history);
    }
    private async void Logout()
    {
        ClosePage(); autoAttack = false; route.Clear(); pendingInteraction = null;
        try { if (Connection is not null) { await Connection.SignOutAsync(); await Connection.DisposeAsync(); } }
        catch (Exception e) { GD.PushWarning(e.Message); }
        Connection = null; World.ClearSession(); ShowLogin();
    }
    public override void _Notification(int what)
    {
        if (what == NotificationWMCloseRequest && !closing) { closing = true; _ = ShutdownAsync(); }
    }
    private async Task ShutdownAsync()
    {
        lifetime.Cancel();
        if (Connection is not null) { try { await Connection.DisposeAsync(); } catch (Exception e) { GD.PushWarning(e.Message); } }
        GetTree().Quit();
    }

    private async Task StartSmokeAsync()
    {
        try
        {
            string address = System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL") ?? "http://127.0.0.1:5077";
            Connection = new GameConnection(address);
            string suffix = Guid.NewGuid().ToString("N")[..10];
            await Connection.SignInAsync("visual_" + suffix, "QA_" + Guid.NewGuid().ToString("N"), true);
            var remote = await Connection.CatalogAsync();
            if (remote.Validate().Count > 0) throw new InvalidDataException("Server catalog validation failed.");
            Data = remote; World.Data = Data;
            var character = await Connection.CreateCharacterAsync(new CharacterRequest { Name = "Visual " + suffix, Class = "vanguard", Appearance = new Appearance { Body = 0, Skin = 2, Hair = 4, HairColor = 1 } });
            await Connection.ConnectAsync(character.Id);
            frontend.Visible = false; smokeStarted = true;
            GD.Print("SMOKE: authenticated Godot client entered the persistent server.");
        }
        catch (Exception error) { GD.PushError(error.ToString()); GetTree().Quit(1); }
    }
    private void TickSmoke(double delta)
    {
        smokeTime += delta;

        if (!Online && smokeTime > 25)
        {
            GD.PushError("SMOKE: connection lost.");
            GetTree().Quit(1);
            return;
        }

        if (!Online) return;

        if (smokeTime > 3 && smokeStage == 0)
        {
            SetInitialHotbar();
            SaveScreenshot("01-world.png");
            OpenPage("Inventory");
            smokeStage++;
            return;
        }

        if (smokeTime > 5 && smokeStage == 1)
        {
            SaveScreenshot("02-inventory.png");
            OpenPage("Skills");
            smokeStage++;
            return;
        }

        if (smokeTime > 7 && smokeStage == 2)
        {
            SaveScreenshot("03-skills.png");
            OpenPage("Map");
            smokeStage++;
            return;
        }

        if (smokeTime > 9 && smokeStage == 3)
        {
            SaveScreenshot("04-map.png");
            ClosePage();
            smokeStage++;
            return;
        }

        if (smokeTime > 11 && smokeStage == 4)
        {
            if (Assets.Missing.Count != 0)
            {
                GD.PushError("SMOKE: missing art: " + string.Join(",", Assets.Missing));
                GetTree().Quit(1);
            }
            else
            {
                GD.Print("SMOKE: live world, inventory, skills, and map rendered without missing requested assets.");
                GetTree().Quit(0);
            }

            smokeStage++;
        }
    }
    private void SaveScreenshot(string name)
    {
        if (DisplayServer.GetName() == "headless") return;
        string directory = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://screenshots");
        System.IO.Directory.CreateDirectory(directory);
        var image = GetViewport().GetTexture().GetImage();
        Error error = image.SavePng(System.IO.Path.Combine(directory, name));
        if (error != Error.Ok) throw new IOException("Could not save render evidence: " + error);
    }
}
