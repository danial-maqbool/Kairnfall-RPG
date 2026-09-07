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
        ["basic_attack"] = Key.Space, ["interact"] = Key.E, ["inventory"] = Key.I, ["character"] = Key.C,
        ["skills"] = Key.K, ["quests"] = Key.J, ["map"] = Key.M, ["abilities"] = Key.B,
        ["crafting"] = Key.F, ["social"] = Key.P, ["target_next"] = Key.Tab
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
    private double moveClock, uiClock, noticeUntil;
    private bool actionBusy, movementBusy, autoAttack, closing;
    private Vector2 lastInput;
    private readonly CancellationTokenSource lifetime = new();
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
            BuildExperienceHud();
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
    }
    private void ApplyBinding(string action)
    {
        if (!InputMap.HasAction(action)) InputMap.AddAction(action);
        InputMap.ActionEraseEvents(action);
        InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = bindings[action] });
        Key alternate = action switch
        {
            "move_left" => Key.Left, "move_right" => Key.Right,
            "move_up" => Key.Up, "move_down" => Key.Down, _ => Key.None
        };
        if (alternate != Key.None && alternate != bindings[action])
            InputMap.ActionAddEvent(action, new InputEventKey { PhysicalKeycode = alternate });
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
                    var previous = Snapshot;
                    World.Accept(packet);
                    ObservePlayerChanges(previous, snapshot);
                    invitations = packet.Invitations ?? [];
                    knownNames[snapshot.Self.Id] = snapshot.Self.Name;
                    foreach (var other in snapshot.Players) knownNames[other.Id] = other.Name;
                    if (hotbarCharacter != snapshot.Self.Id)
                    {
                        hotbarCharacter = snapshot.Self.Id;
                        SetInitialHotbar();
                    }
                }
                if (packet.Chat is { } chat) AddChat($"[{chat.Channel}] {chat.Name}: {chat.Text}");
                if (packet.Kind == "error") Notify(packet.Error, true);
            }
        }
        if (Online)
        {
            var self = Snapshot!.Self;
            bool controls = GameplayInputAllowed && awaitingBinding == "";
            Vector2 input = controls ? Input.GetVector("move_left", "move_right", "move_up", "move_down") : Vector2.Zero;
            if (!controls || input.LengthSquared() > .01f) { route.Clear(); pendingInteraction = null; }
            if (input.LengthSquared() < .01f && route.Count > 0 && controls)
            {
                while (route.Count > 0 && self.Position.Distance(route[0]) < .32) route.RemoveAt(0);
                if (route.Count > 0)
                {
                    var dir = self.Position.Direction(route[0]); input = new Vector2((float)dir.X, (float)dir.Y);
                }
            }
            if (controls && pendingInteraction is { } interaction && self.Position.Distance(interaction.Position) <= 2.15
                && WorldMap.LineOfSight(Data.Zone(self.Zone), self.Position, interaction.Position))
            {
                pendingInteraction = null; route.Clear(); input = Vector2.Zero; Activate(interaction);
            }
            moveClock += delta;
            bool changed = (input - lastInput).LengthSquared() > .0001f;
            bool moving = input.LengthSquared() > .0001f;
            if (!movementBusy && (changed || (moving && moveClock >= .08)))
            {
                moveClock = 0; lastInput = input; SendMovement(input);
            }
            audio?.SetRegion(Data.Zone(self.Zone), Snapshot.Creatures.Any(x => Data.Mob(x.Template).Boss && x.Target == self.Id));
        }
        TickExperience(delta);
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

    private void SelectTarget(string kind, string id)
    {
        selectedTargetKind = kind; selectedTarget = id; World.TargetId = id; StopCombatInput();
    }
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
        if (!GameplayInputAllowed || index < 0 || index >= hotbar.Length || string.IsNullOrEmpty(hotbar[index])) return;
        var snapshot = Snapshot!;
        var ability = Data.Ability(hotbar[index]);
        if (ability.Class != "" && ability.Class != snapshot.Self.Class) { Notify("This ability belongs to another class.", true); return; }
        if (Progression.Level(snapshot.Self, ability.Skill) < ability.Requirement)
        { Notify("Requires " + Data.Skill(ability.Skill).Name + " " + ability.Requirement + ".", true); return; }
        if (snapshot.Self.Mana < ability.Mana) { Notify("Not enough mana for " + ability.Name + ".", true); return; }
        if (snapshot.Self.Stamina < ability.Stamina) { Notify("Not enough stamina for " + ability.Name + ".", true); return; }
        var point = World.ScreenToWorld(GetGlobalMousePosition());
        string targetId = selectedTargetKind is "creature" or "player" ? selectedTarget : "";
        if (ability.Kind is "heal" or "shield" or "buff")
        {
            if (selectedTargetKind != "player") { targetId = snapshot.Self.Id; point = snapshot.Self.Position; }
        }
        else if (ability.Kind is "strike" or "projectile" or "interrupt")
        {
            var target = ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data, targetId, ability.Range);
            if (target is null) { Notify("No hostile creature is within this ability's range."); return; }
            targetId = target.Id; point = target.Position;
        }
        else if (snapshot.Self.Position.Distance(point) > ability.Range)
            point = snapshot.Self.Position.Add(snapshot.Self.Facing.Scale(Math.Max(0, ability.Range - .1)));
        _ = SendAsync(new GameCommand { Kind = "cast", Item = ability.Id, Target = targetId, X = point.X, Y = point.Y }, true);
    }
    private void SetInitialHotbar()
    {
        if (Snapshot is null) return;
        var abilities = ExperienceRules.StarterAbilities(Snapshot.Self, Data);
        string section = "hotbar_" + Snapshot.Self.Id;
        Array.Fill(hotbar, "");
        for (int i = 0; i < hotbar.Length; i++)
        {
            if (!settings.HasSectionKey(section, i.ToString())) continue;
            string saved = settings.GetValue(section, i.ToString(), "").AsString();
            hotbar[i] = abilities.Any(x => x.Id == saved) ? saved : "";
        }
        for (int i = 0; i < hotbar.Length; i++)
        {
            if (settings.HasSectionKey(section, i.ToString())) continue;
            hotbar[i] = abilities.FirstOrDefault(x => !hotbar.Contains(x.Id))?.Id ?? "";
        }
    }
    private string PageStamp()
    {
        if (Snapshot is null) return "offline";
        // Movement sequence numbers do not invalidate inventory controls while the user clicks them.
        return currentPage + selectedItem + selectedBag + selectedRecipe + selectedQuest + selectedNpc + JsonSerializer.Serialize(new
        {
            Snapshot.Self.Inventory, Snapshot.Self.Bank, Snapshot.Self.Equipment, Snapshot.Self.SkillXp,
            Snapshot.Self.Quests, Snapshot.Self.Gold, Snapshot.Self.Zone, Dead = Snapshot.Self.Health <= 0,
            Snapshot.Trades, Snapshot.Auctions, Snapshot.Party, Snapshot.Guild, Snapshot.ShopStock, invitations
        }, Wire.Json);
    }
    private string PlayerName(string id) => knownNames.GetValueOrDefault(id, id == "" ? "None" : "Traveler " + id[..Math.Min(6, id.Length)]);
    private void Notify(string text, bool error = false)
    {
        if (notice is null || !GodotObject.IsInstanceValid(notice) || string.IsNullOrWhiteSpace(text)) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (text == lastNoticeText && now - lastNoticeAt < 1.5) return;
        lastNoticeText = text; lastNoticeAt = now;
        notice.Text = text; notice.AddThemeColorOverride("font_color", error ? Ui.Danger : Ui.Text); noticeUntil = now + 5;
    }
    private void AddChat(string text)
    {
        history.Add(text); if (history.Count > 120) history.RemoveAt(0);
        if (chatLog is not null) chatLog.Text = string.Join("\n", history);
    }
    private async void Logout()
    {
        ClosePage(); StopCombatInput(); route.Clear(); pendingInteraction = null;
        try { if (Connection is not null) { await Connection.SignOutAsync(); await Connection.DisposeAsync(); } }
        catch (Exception e) { GD.PushWarning(e.Message); }
        Connection = null; World.ClearSession(); hotbarCharacter = "";
        history.Clear(); knownNames.Clear(); invitations.Clear(); pickupNotes.Clear();
        chatLog.Text = ""; progressionHint.Text = ""; RenderPickupFeed(); ShowLogin();
    }
    public override void _Notification(int what)
    {
        if (what == NotificationApplicationFocusOut)
        {
            applicationFocused = false; StopCombatInput(); route.Clear(); pendingInteraction = null;
            if (!movementBusy && Connection?.Connected == true) { lastInput = Vector2.Zero; SendMovement(Vector2.Zero); }
        }
        if (what == NotificationApplicationFocusIn) applicationFocused = true;
        if (what == NotificationWMCloseRequest && !closing) { closing = true; _ = ShutdownAsync(); }
    }
    private async Task ShutdownAsync()
    {
        StopCombatInput(); lifetime.Cancel();
        if (Connection is not null) { try { await Connection.DisposeAsync(); } catch (Exception e) { GD.PushWarning(e.Message); } }
        GetTree().Quit();
    }

    private async Task StartSmokeAsync()
    {
        try
        {
            if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("The graphical smoke requires a real display.");
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
        if (!Online && smokeTime > 25) { GD.PushError("SMOKE: connection lost."); GetTree().Quit(1); return; }
        if (!Online) return;
        if (smokeTime > 3 && smokeStage == 0) { SetInitialHotbar(); SaveScreenshot("01-world.png"); OpenPage("Inventory"); smokeStage++; }
        if (smokeTime > 5 && smokeStage == 1) { SaveScreenshot("02-inventory.png"); OpenPage("Skills"); smokeStage++; }
        if (smokeTime > 7 && smokeStage == 2) { SaveScreenshot("03-skills.png"); OpenPage("Map"); smokeStage++; }
        if (smokeTime > 9 && smokeStage == 3) { SaveScreenshot("04-map.png"); ClosePage(); smokeStage++; }
        if (smokeTime > 11 && smokeStage == 4)
        {
            if (Assets.Missing.Count != 0) { GD.PushError("SMOKE: missing art: " + string.Join(",", Assets.Missing)); GetTree().Quit(1); }
            else { GD.Print("SMOKE: live world, inventory, skills, and map rendered without missing requested assets."); GetTree().Quit(0); }
            smokeStage++;
        }
    }
    private void SaveScreenshot(string name)
    {
        if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("A headless run cannot produce graphical acceptance evidence.");
        string directory = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://screenshots");
        System.IO.Directory.CreateDirectory(directory);
        var image = GetViewport().GetTexture().GetImage();
        Error error = image.SavePng(System.IO.Path.Combine(directory, name));
        if (error != Error.Ok) throw new IOException("Could not save render evidence: " + error);
    }
}
