using Godot;
using Kairnfall.Core;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot : Control
{
    public PixelAssets Assets { get; private set; } = new();
    public ClientPerformanceDiagnostics Diagnostics { get; private set; } = ClientPerformanceDiagnostics.FromEnvironment();
    public Catalog Data { get; private set; } = null!;
    public GameConnection? Connection { get; private set; }
    public WorldView World { get; private set; } = null!;
    public Snapshot? Snapshot => World?.Snapshot;
    private Control interfaceRoot = null!, frontend = null!;
    private PanelContainer? gameWindow;
    private VBoxContainer? page;
    private Label notice = null!, location = null!, characterTitle = null!;
    private Label healthText = null!, manaText = null!, staminaText = null!, targetText = null!;
    private ProgressBar health = null!, mana = null!, stamina = null!;
    private RichTextLabel chatLog = null!;
    private LineEdit chatInput = null!;
    private OptionButton chatChannel = null!;
    private readonly List<string> history = [];
    private readonly Dictionary<string, string> knownNames = [];
    private List<GroupInvitation> invitations = [];
    private List<string> friendInvitations = [];
    private List<LfgListing> lfgListings = [];
    private List<SocialProfile> socialProfiles = [];
    private readonly Dictionary<string, Key> bindings = new()
    {
        ["move_left"] = Key.A, ["move_right"] = Key.D, ["move_up"] = Key.W, ["move_down"] = Key.S,
        ["basic_attack"] = Key.Space, ["interact"] = Key.E, ["inventory"] = Key.I, ["character"] = Key.C,
        ["skills"] = Key.K, ["quests"] = Key.J, ["map"] = Key.M, ["abilities"] = Key.B,
        ["crafting"] = Key.F, ["social"] = Key.P, ["target_next"] = Key.Tab, ["dash"] = Key.Q, ["hunting"] = Key.H
    };
    private readonly ConfigFile settings = new();
    private string awaitingBinding = "", currentPage = "", selectedItem = "", selectedBag = "inventory";
    private string selectedRecipe = "", selectedNpc = "", selectedRune = "", selectedQuest = "";
    private string selectedZone = "", selectedTrade = "", selectedTarget = "", selectedTargetKind = "";
    private string placement = "", structureRecipe = "";
    private WorldTarget? pendingInteraction;
    private readonly List<Point> route = [];
    private readonly string[] hotbar = new string[10];
    private readonly Button[] hotbarButtons = new Button[10];
    private Action? refreshPage;
    private double moveClock, uiClock, noticeUntil;
    private bool actionBusy, movementBusy, closing;
    private Vector2 lastInput;
    private readonly CancellationTokenSource lifetime = new();
    private object? lastPageStamp = "";
    private ClientAudio? audio;
    private bool smoke, smokeStarted;

    public override void _Ready()
    {
        try
        {
            GetTree().AutoAcceptQuit = false;
            Theme = Ui.BuildTheme();
            settings.Load("user://settings.cfg");
            var fullscreen = settings.GetValue("display", "fullscreen", false);
            if (fullscreen.VariantType == Variant.Type.Bool && fullscreen.AsBool())
                GetWindow().Mode = Window.ModeEnum.Fullscreen;
            InstallBindings();
            Data = PixelAssets.LoadCatalog();
            Assets.Diagnostics = Diagnostics;
            World = new WorldView { Assets = Assets, Data = Data, Diagnostics = Diagnostics }; AddChild(World);
            interfaceRoot = new Control { MouseFilter = MouseFilterEnum.Ignore };
            AddChild(interfaceRoot); interfaceRoot.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            frontend = new Control { MouseFilter = MouseFilterEnum.Ignore };
            interfaceRoot.AddChild(frontend); frontend.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            BuildHud(); BuildExperienceHud();
            audio = new ClientAudio(); AddChild(audio);
            audio.SetVolumes((float)settings.GetValue("audio", "music", .35).AsDouble(), (float)settings.GetValue("audio", "effects", .65).AsDouble());
            World.WeatherEnabled = settings.GetValue("display", "weather", true).AsBool();
            World.ShowNames = settings.GetValue("display", "names", true).AsBool();
            World.Zoom = PixelPresentation.WorldZoom(settings);
            ShowLogin();
            smoke = OS.GetCmdlineUserArgs().Contains("--smoke");
            if (smoke) _ = StartSmokeAsync();
        }
        catch (Exception error)
        {
            GD.PushError(error.ToString());
            var message = Ui.Label("Kairnfall could not start.\n\n" + error.Message + "\n\nRun bootstrap.ps1 from the repository root.", 19, Ui.Text, true);
            AddChild(message); message.SetAnchorsAndOffsetsPreset(LayoutPreset.FullRect);
            message.OffsetLeft = 50; message.OffsetTop = 50; message.OffsetRight = -50;
            if (OS.GetCmdlineUserArgs().Contains("--smoke")) _ = ShutdownClientAsync(1);
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
        using var primary = new InputEventKey { PhysicalKeycode = bindings[action] };
        InputMap.ActionAddEvent(action, primary);
        Key alternate = action switch
        {
            "move_left" => Key.Left, "move_right" => Key.Right,
            "move_up" => Key.Up, "move_down" => Key.Down, _ => Key.None
        };
        if (alternate != Key.None && alternate != bindings[action])
        {
            using var secondary = new InputEventKey { PhysicalKeycode = alternate };
            InputMap.ActionAddEvent(action, secondary);
        }
    }
    private bool Typing => GetViewport().GuiGetFocusOwner() is LineEdit or TextEdit;
    private bool Online => Connection?.Connected == true && Snapshot is not null;

    public override void _Process(double delta)
    {
        if (World is null || Data is null || closing) return;
        if (Connection is { } connection)
        {
            int drained = 0;
            while (drained++ < 150 && connection.TryRead(out var packet))
            {
                if (packet is null) continue;
                if (packet.Snapshot is { } snapshot)
                {
                    var previous = Snapshot;
                    World.Accept(packet); ObservePlayerChanges(previous, snapshot);
                    invitations = packet.Invitations ?? [];
                    friendInvitations = packet.FriendInvitations ?? [];
                    lfgListings = packet.Lfg ?? [];
                    socialProfiles = packet.SocialProfiles ?? [];
                    knownNames[snapshot.Self.Id] = snapshot.Self.Name;
                    foreach (var other in snapshot.Players) knownNames[other.Id] = other.Name;
                    foreach (var listing in lfgListings) knownNames[listing.Character] = listing.Name;
                    foreach (var profile in socialProfiles) knownNames[profile.Id] = profile.Name;
                    if (hotbarCharacter != snapshot.Self.Id)
                    {
                        hotbarCharacter = snapshot.Self.Id; SetInitialHotbar();
                    }
                }
                if (packet.Chat is { } chat) AddChat($"[{chat.Channel}] {chat.Name}: {chat.Text}");
                if (packet.Kind == "error") Notify(packet.Error, true);
            }
        }
        World.SetLocalMovementIntent(Vector2.Zero);
        if (Online)
        {
            var self = Snapshot!.Self;
            bool controls = GameplayInputAllowed;
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
            // Feed the resolved manual/route intent only to presentation continuity;
            // authoritative displacement still comes exclusively from server snapshots.
            World.SetLocalMovementIntent(input);
            moveClock += delta;
            bool changed = (input - lastInput).LengthSquared() > .0001f;
            bool moving = input.LengthSquared() > .0001f;
            if (!movementBusy && (changed || moving && moveClock >= .08))
            {
                moveClock = 0; lastInput = input; SendMovement(input);
            }
            bool bossAudio=Snapshot.Creatures.Any(x=>Data.Mob(x.Template).Boss&&x.Target==self.Id);
            bool combatAudio=Snapshot.Time-self.LastCombat<7;
            audio?.SetRegion(Data.Zone(self.Zone),bossAudio,combatAudio);
        }
        TickExperience(delta);
        uiClock += delta;
        if (uiClock > .2)
        {
            uiClock = 0;
            long hudStarted = Diagnostics.StartTimer();
            UpdateHud();
            Diagnostics.RecordDuration(ClientPerfPhase.HudUpdate, hudStarted);
            if (refreshPage is not null && !Input.IsMouseButtonPressed(MouseButton.Left))
            {
                long stampStarted = Diagnostics.StartTimer();
                object stamp = PageStamp();
                bool pageChanged = !Equals(stamp, lastPageStamp);
                Diagnostics.RecordDuration(ClientPerfPhase.PanelStamp, stampStarted);
                if (pageChanged)
                {
                    lastPageStamp = stamp;
                    long refreshStarted = Diagnostics.StartTimer();
                    refreshPage();
                    Diagnostics.RecordDuration(ClientPerfPhase.PanelRefresh, refreshStarted);
                }
            }
        }
        if (notice is not null && Time.GetTicksMsec() / 1000.0 > noticeUntil) notice.Text = "";
        if (smoke && smokeStarted) TickSmoke(delta);
    }

    private async void SendMovement(Vector2 direction)
    {
        if (Connection is null || !Connection.Connected || closing) return;
        movementBusy = true;
        try { await Connection.MoveAsync(direction.X, direction.Y, lifetime.Token); }
        catch (Exception error) when (error is not OperationCanceledException) { Notify(error.Message, true); }
        catch (OperationCanceledException) { }
        finally { movementBusy = false; }
    }
    private async Task<CommandResult?> SendAsync(GameCommand command, bool quiet = false)
    {
        if (!Online || actionBusy || closing) return null;
        actionBusy = true;
        try
        {
            var result = await Connection!.ActAsync(command, lifetime.Token);
            if (closing || !IsInsideTree()) return result;
            if (!result.Ok || !quiet) Notify(result.Message, !result.Ok);
            if (result.Ok)
            {
                // Accepted server cues drive both self and remote actions; receipts must not restart them.
                if (command.Kind == "cast")
                    for (int i = 0; i < hotbar.Length; i++)
                        if (hotbar[i] == command.Item && hotbarButtons[i] is AbilitySlot slot) slot.ShowActivation();
                audio?.PlayEffect(command.Kind,Snapshot?.Self.Class??""); lastPageStamp = "";
            }
            return result;
        }
        catch (OperationCanceledException) { return null; }
        catch (Exception error) { Notify(error.Message, true); return null; }
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
            if (!closing && IsInsideTree() && result?.Ok == true) { selectedNpc = target.Id; OpenPage("Dialogue"); }
        }
        else if (target.Kind == "node")
        {
            var node = Snapshot?.Nodes.FirstOrDefault(x => x.Id == target.Id);
            if (node is not null && node.Template.StartsWith("structure_", StringComparison.Ordinal)) OpenPage("Crafting");
            else Send("gather", target.Id);
        }
        else if (target.Kind == "landmark") Send("inspect", target.Id);
        else if (target.Kind == "event") Send("event", target.Id);
        else if (target.Kind == "chest") Send("chest", target.Id);
        else if (target.Kind == "loot") Send("loot", target.Id);
    }
    private const double AbilityBufferSeconds = .35;
    private int queuedHotbar = -1;
    private double queuedAbilityUntil;
    private string queuedAbilityTargetKind = "", queuedAbilityTarget = "";
    private Point queuedAbilityAim;

    private void ClearAbilityBuffer()
    {
        queuedHotbar = -1; queuedAbilityUntil = 0;
        queuedAbilityTargetKind = ""; queuedAbilityTarget = ""; queuedAbilityAim = default;
    }

    private void QueueAbilityIntent(int index, double duration, bool announce)
    {
        queuedHotbar = index;
        queuedAbilityUntil = Time.GetTicksMsec() / 1000.0 + duration;
        queuedAbilityTargetKind = selectedTargetKind;
        queuedAbilityTarget = selectedTarget;
        queuedAbilityAim = World.ScreenToWorld(GetGlobalMousePosition());
        if (announce) Notify("Queued " + Data.Ability(hotbar[index]).Name + ".");
    }

    private void UseHotbar(int index) => TryUseHotbar(index, true);
    private void TryUseHotbar(int index, bool allowQueue)
    {
        if (!GameplayInputAllowed || index < 0 || index >= hotbar.Length || string.IsNullOrEmpty(hotbar[index])) return;
        var snapshot = Snapshot!;
        var ability = Data.Ability(hotbar[index]);
        double readyIn = ExperienceRules.AbilityReadyIn(snapshot.Self, ability, snapshot.Time);
        string problem = ExperienceRules.AbilityProblem(snapshot.Self, ability, Data, snapshot.Time);
        if (problem != "")
        {
            if (allowQueue && readyIn > 0 && readyIn <= AbilityBufferSeconds)
            {
                QueueAbilityIntent(index, AbilityBufferSeconds + .12, true);
                return;
            }
            Notify(problem); return;
        }
        if (actionBusy)
        {
            if (allowQueue) QueueAbilityIntent(index, AbilityBufferSeconds, false);
            return;
        }

        bool replayQueued = !allowQueue && queuedHotbar == index;
        string intentKind = replayQueued ? queuedAbilityTargetKind : selectedTargetKind;
        string intentTarget = replayQueued ? queuedAbilityTarget : selectedTarget;
        var point = replayQueued ? queuedAbilityAim : World.ScreenToWorld(GetGlobalMousePosition());
        string targetId = intentKind is "creature" or "player" ? intentTarget : "";
        ClearAbilityBuffer();
        if (ability.Kind is "heal" or "shield" or "buff" or "stealth" or "summon" or "purge")
        {
            if (ability.Kind != "heal" || intentKind != "player") { targetId = snapshot.Self.Id; point = snapshot.Self.Position; }
        }
        else if (ability.Kind is "strike" or "projectile" or "interrupt" or "drain" or "dot")
        {
            Creature? target = null;
            if (intentKind == "creature" && targetId != "")
            {
                target = snapshot.Creatures.FirstOrDefault(x => x.Id == targetId);
                if (target is null) { Notify("Selected target is no longer available."); return; }
                string blocker = ExperienceRules.TargetProblem(snapshot.Self, target, Data, ability.Range);
                if (blocker != "") { Notify(blocker); return; }
            }
            target ??= ExperienceRules.ChooseTarget(snapshot.Self, snapshot.Creatures, Data, "", ability.Range);
            if (target is null) { Notify("No hostile creature is within this ability's range."); return; }
            targetId = target.Id; point = target.Position;
        }
        else
        {
            targetId = "";
            if (snapshot.Self.Position.Distance(point) > ability.Range)
                point = snapshot.Self.Position.Add(snapshot.Self.Facing.Scale(Math.Max(0, ability.Range - .1)));
        }
        _ = SendAsync(new GameCommand { Kind = "cast", Item = ability.Id, Target = targetId, X = point.X, Y = point.Y }, true);
    }

    private void TickAbilityBuffer()
    {
        if (queuedHotbar < 0 || Snapshot is not { } snapshot) return;
        double now = Time.GetTicksMsec() / 1000.0;
        if (!GameplayInputAllowed || now > queuedAbilityUntil || queuedHotbar >= hotbar.Length
            || string.IsNullOrEmpty(hotbar[queuedHotbar]))
        {
            ClearAbilityBuffer(); return;
        }
        var ability = Data.Ability(hotbar[queuedHotbar]);
        if (!actionBusy && ExperienceRules.AbilityReadyIn(snapshot.Self, ability, snapshot.Time) <= .02
            && ExperienceRules.AbilityProblem(snapshot.Self, ability, Data, snapshot.Time) == "")
            TryUseHotbar(queuedHotbar, false);
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
    private sealed class InventoryRefreshStamp(
        Snapshot snapshot, string page, string item, string bag, string npc)
    {
        private readonly Snapshot snapshot = snapshot;
        private readonly string page = page, item = item, bag = bag, npc = npc;

        private static bool DictionaryEqual<TKey, TValue>(
            IReadOnlyDictionary<TKey, TValue> left, IReadOnlyDictionary<TKey, TValue> right)
            where TKey : notnull
        {
            if (left.Count != right.Count) return false;
            foreach (var entry in left)
                if (!right.TryGetValue(entry.Key, out var value)
                    || !EqualityComparer<TValue>.Default.Equals(entry.Value, value)) return false;
            return true;
        }

        private static bool ItemEqual(Item left, Item right)
        {
            if (left.Id != right.Id || left.Template != right.Template || left.Quantity != right.Quantity
                || left.Rarity != right.Rarity || left.Element != right.Element || left.Sockets != right.Sockets
                || left.Durability != right.Durability || !DictionaryEqual(left.SkillBonuses, right.SkillBonuses)
                || left.Affixes.Count != right.Affixes.Count || left.Runes.Count != right.Runes.Count) return false;
            for (int i = 0; i < left.Affixes.Count; i++)
            {
                var a = left.Affixes[i]; var b = right.Affixes[i];
                if (a.Name != b.Name || a.Stat != b.Stat || a.Value != b.Value) return false;
            }
            for (int i = 0; i < left.Runes.Count; i++)
                if (left.Runes[i].Id != right.Runes[i].Id || left.Runes[i].Template != right.Runes[i].Template) return false;
            return true;
        }

        private static bool ItemsEqual(IReadOnlyList<Item> left, IReadOnlyList<Item> right)
        {
            if (left.Count != right.Count) return false;
            for (int i = 0; i < left.Count; i++) if (!ItemEqual(left[i], right[i])) return false;
            return true;
        }

        private static bool StationsEqual(Snapshot left, Snapshot right, string owner)
        {
            int leftCount = 0, rightCount = 0;
            foreach (var node in left.Nodes)
            {
                if (node.Owner != owner || !node.Template.StartsWith("structure_", StringComparison.Ordinal)) continue;
                leftCount++;
                WorldNode? match = null;
                foreach (var candidate in right.Nodes)
                    if (candidate.Id == node.Id && candidate.Owner == owner
                        && candidate.Template.StartsWith("structure_", StringComparison.Ordinal)) { match = candidate; break; }
                if (match is null || match.Template != node.Template || match.Zone != node.Zone
                    || match.Position.X != node.Position.X || match.Position.Y != node.Position.Y) return false;
            }
            foreach (var node in right.Nodes)
                if (node.Owner == owner && node.Template.StartsWith("structure_", StringComparison.Ordinal)) rightCount++;
            return leftCount == rightCount;
        }

        public override bool Equals(object? obj)
        {
            if (obj is not InventoryRefreshStamp other || page != other.page || item != other.item
                || bag != other.bag || npc != other.npc) return false;
            var left = snapshot.Self; var right = other.snapshot.Self;
            return left.Id == right.Id && left.Class == right.Class && left.Gold == right.Gold
                && left.Zone == right.Zone && left.Position.X == right.Position.X && left.Position.Y == right.Position.Y
                && (left.Health <= 0) == (right.Health <= 0) && left.Pet == right.Pet
                && DictionaryEqual(left.Equipment, right.Equipment)
                && DictionaryEqual(left.SkillXp, right.SkillXp)
                && ItemsEqual(left.Inventory, right.Inventory) && ItemsEqual(left.Bank, right.Bank)
                && StationsEqual(snapshot, other.snapshot, left.Id);
        }

        public override int GetHashCode() => 0;
    }

    private object InventoryPageStamp(Snapshot snapshot)
        => new InventoryRefreshStamp(snapshot, currentPage, selectedItem, selectedBag, selectedNpc);

    private object PageStamp()
    {
        if (Snapshot is not { } snapshot) return "offline";
        if (currentPage is "Inventory" or "Bank") return InventoryPageStamp(snapshot);
        return currentPage + selectedItem + selectedBag + selectedRecipe + selectedQuest + selectedNpc + JsonSerializer.Serialize(new
        {
            snapshot.Self.Inventory, snapshot.Self.Bank, snapshot.Self.Equipment, snapshot.Self.SkillXp,
            snapshot.Self.Quests, snapshot.Self.Gold, snapshot.Self.Zone, Dead = snapshot.Self.Health <= 0,
            snapshot.Trades, snapshot.Auctions, snapshot.Party, snapshot.Guild, snapshot.ShopStock, snapshot.Events,
            invitations, friendInvitations, lfgListings, socialProfiles
        }, Wire.Json);
    }
    private string PlayerName(string id) => knownNames.GetValueOrDefault(id, id == "" ? "None" : "Traveler " + id[..Math.Min(6, id.Length)]);
    private void Notify(string text, bool error = false)
    {
        if (closing || notice is null || !GodotObject.IsInstanceValid(notice) || string.IsNullOrWhiteSpace(text)) return;
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
        catch (Exception error) { GD.PushWarning(error.Message); }
        if (closing || !IsInsideTree()) return;
        Connection = null; World.ClearSession(); hotbarCharacter = "";
        history.Clear(); knownNames.Clear(); invitations.Clear(); friendInvitations.Clear(); lfgListings.Clear(); socialProfiles.Clear(); pickupNotes.Clear(); lastExperienceSkill = "";
        chatLog.Text = ""; RenderPickupFeed(); ShowLogin();
    }
    public override void _Notification(int what)
    {
        if (what == NotificationApplicationFocusOut)
        {
            applicationFocused = false; StopCombatInput(); route.Clear(); pendingInteraction = null;
            if (!movementBusy && Connection?.Connected == true) { lastInput = Vector2.Zero; SendMovement(Vector2.Zero); }
        }
        if (what == NotificationApplicationFocusIn) applicationFocused = true;
        if (what == NotificationWMCloseRequest) _ = ShutdownAsync();
    }
}
