using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Normal-account native actions against an isolated PostgreSQL realm; no state injection.</summary>
public partial class ClassicLiveLoopContract : Node
{
    private GameRoot game = null!;
    private GameConnection? connection;
    private int checks;
    private bool gatherDiagnostic;
    private string previousGather = "";
    private static double Now => Time.GetTicksMsec() / 1000.0;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private T Field<T>(string name) => (T)Member(name).GetValue(game)!;
    private object? Call(string name, params object?[] args) => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private Character Self => game.Snapshot!.Self;
    private static string RecordPath => System.Environment.GetEnvironmentVariable("KAIRNFALL_CLASSIC_SAVE_RECORD") ?? throw new InvalidOperationException("Private QA record required.");
    private sealed class SaveRecord
    {
        public string Username { get; set; } = "";
        public string Password { get; set; } = "";
        public Character Self { get; set; } = new();
        public List<WorldNode> Structures { get; set; } = [];
        public double Time { get; set; }
    }
    private void Check(bool condition, string message)
    { if (!condition) throw new InvalidOperationException(message); checks++; GD.Print("PASS CLASSIC LIVE: " + message); }
    public override void _Notification(int what)
    {
        if (gatherDiagnostic && (what == NotificationApplicationFocusOut || what == NotificationApplicationFocusIn))
            GD.Print($"FOCUS_EVENT at={Now:0.000} kind={(what == NotificationApplicationFocusOut ? "out" : "in")}");
    }
    private async Task Frame()
    {
        await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
        if (!gatherDiagnostic || game is null || !GodotObject.IsInstanceValid(game) || game.Snapshot is null) return;
        string active = Field<string>("classicGatherTarget");
        if (previousGather != "" && active == "")
        {
            var node = game.Snapshot.Nodes.FirstOrDefault(x => x.Id == previousGather);
            GD.Print($"GATHER_CANCEL_TRACE at={Now:0.000} focused={Field<bool>("applicationFocused")} modal={Field<PanelContainer?>("gameWindow") is not null} guiFocus={GetViewport().GuiGetFocusOwner()?.GetClass() ?? "none"} input={Input.GetVector("move_left", "move_right", "move_up", "move_down")} selected={Field<string>("selectedTargetKind")}/{Field<string>("selectedTarget")} eligibility={ClassicGatherRules.Problem(Self,node,game.Data,game.Snapshot.Time)} health={Self.Health:0.0} stamina={Self.Stamina:0.0}");
        }
        previousGather = active;
    }
    private async Task Delay(double seconds) => await ToSignal(GetTree().CreateTimer(seconds), SceneTreeTimer.SignalName.Timeout);
    private async Task Until(Func<bool> condition, string failure, double seconds = 10)
    {
        double until = Now + seconds;
        while (!condition()) { if (Now > until) throw new TimeoutException(failure); await Frame(); }
    }
    private void KeyEvent(Key key, bool pressed)
    {
        using var input = new InputEventKey { PhysicalKeycode = key, Keycode = key, Pressed = pressed };
        Input.ParseInputEvent(input); Input.FlushBufferedEvents();
    }
    private async Task Tap(Key key) { KeyEvent(key, true); await Delay(.07); KeyEvent(key, false); await Frame(); }
    private void Mouse(Vector2 point, bool pressed)
    {
        using var input = new InputEventMouseButton { Position = point, GlobalPosition = point, ButtonIndex = MouseButton.Left,
            Pressed = pressed, ButtonMask = pressed ? MouseButtonMask.Left : 0 };
        Input.ParseInputEvent(input); Input.FlushBufferedEvents();
    }
    private async Task Click(Control control)
    {
        for (Node? parent = control.GetParent(); parent is not null; parent = parent.GetParent())
            if (parent is ScrollContainer scroll) scroll.EnsureControlVisible(control);
        string originalName = control.Name; string originalText = control is Button originalButton ? originalButton.Text : "";
        Control Current() => GodotObject.IsInstanceValid(control) && !control.IsQueuedForDeletion() ? control
            : originalText != "" ? Action(originalText) : (Control)game.FindChild(originalName, true, false)!;
        await Frame(); await Frame(); control = Current();
        if (control is Button) await Until(() => { control = Current(); return control is Button current && !current.Disabled; }, "The intended native button did not become enabled.", 3);
        Check(GodotObject.IsInstanceValid(control) && !control.IsQueuedForDeletion(), "The mouse action uses a current native widget");
        GD.Print($"CLICK_TRACE name={control.Name} visible={control.IsVisibleInTree()} rect={control.GetGlobalRect()} viewport={GetViewport().GetVisibleRect()}");
        Check(control.IsVisibleInTree() && GetViewport().GetVisibleRect().HasPoint(control.GetGlobalRect().GetCenter()), "Native action is visible: " + control.Name);
        var point = control.GetGlobalRect().GetCenter(); Mouse(point, true); await Frame(); Mouse(point, false); await Frame();
    }
    private Button Action(string text) => game.FindChildren("*", "Button", true, false).OfType<Button>().First(x => !x.IsQueuedForDeletion() && x.IsVisibleInTree() && x.Text == text);
    private async Task Capture(string name)
    {
        if (DisplayServer.GetName() == "headless") { GD.Print("SKIP LIVE PIXEL CAPTURE: " + name + " (headless gameplay gate)"); return; }
        await Frame(); await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string folder = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")!; Directory.CreateDirectory(folder);
        using var image = GetViewport().GetTexture().GetImage(); Check(image.SavePng(Path.Combine(folder, name + ".png")) == Error.Ok, "Rendered live native frame " + name);
    }
    private async Task Walk(Point destination, double radius = .36)
    {
        string zone = Self.Zone; Call("WalkTo", destination, false);
        double nextRouteTrace = 0;
        await Until(() =>
        {
            if (Now >= nextRouteTrace)
            {
                nextRouteTrace = Now + 1;
                GD.Print($"ROUTE_TRACE zone={Self.Zone} self={Self.Position} destination={destination} distance={Self.Position.Distance(destination):0.000} remaining={Field<List<Point>>("route").Count} next={(Field<List<Point>>("route").Count > 0 ? Field<List<Point>>("route")[0].ToString() : "none")} focused={Field<bool>("applicationFocused")} page={Field<string>("currentPage")} modal={Field<PanelContainer?>("gameWindow") is not null} input={Input.GetVector("move_left", "move_right", "move_up", "move_down")} busy={Field<bool>("movementBusy")}");
            }
            return Self.Zone != zone || Self.Position.Distance(destination) <= radius;
        }, "Normal grid path did not reach the requested location.", 65);
        Check(Self.Zone == zone, "Normal path remains in the requested region");
        Field<List<Point>>("route").Clear(); await connection!.GridMoveAsync(0, 0); await Delay(.35);
        Check(WorldMap.Fits(game.Data.Zone(Self.Zone), Self.Position), "Walk ended at a valid authoritative position");
    }
    private async Task Buy(string npcId, string template, int quantity)
    {
        var npc = game.Data.Npc(npcId); await Walk(npc.Position);
        var result = await connection!.ActAsync(new GameCommand { Kind = "buy", Target = npc.Id, Item = template, Amount = quantity });
        Check(result.Ok, "Existing merchant transaction accepts " + template + ": " + result.Message); await Delay(.2);
    }
    private async Task ApproachResource(WorldNode node)
    {
        await Walk(node.Position); Call("SelectTarget", "", "");
        // Routes stop through the same released-step rules as manual movement. Finish
        // the resource approach with real directional taps so Space faces this object.
        for (int step = 0; Self.Position.Distance(node.Position) > .15 && step < 3; step++)
        {
            var direction = GridMovementRules.Cardinal(Self.Position.Direction(node.Position));
            var expected = GridMovementRules.Next(Self.Position, direction);
            await Tap(direction.X < 0 ? Key.A : direction.X > 0 ? Key.D : direction.Y < 0 ? Key.W : Key.S);
            await Until(() => Self.Position.Distance(expected) < .000001, "Directional resource approach did not finish its tile.");
            await Delay(.2);
        }
        Check(Self.Position.Distance(node.Position) < .15, "Real directional taps place the player at the intended resource");
    }
    private async Task GatherOnce(WorldNode node)
    {
        await ApproachResource(node);
        await Until(() => Self.Cooldowns.GetValueOrDefault("gather") <= game.Snapshot!.Time
            && game.Snapshot.Nodes.FirstOrDefault(x => x.Id == node.Id)?.ReadyAt <= game.Snapshot.Time
            && !Field<bool>("actionBusy"), "Gather recovery did not complete.", 45);
        string template = game.Data.Resource(node.Template).Item; int before = Items.Count(Self, template);
        GD.Print($"RESOURCE_TRACE requested={node.Id} at={node.Position} self={Self.Position} context={Call("ContextTarget")} problem={ClassicGatherRules.Problem(Self, game.Snapshot!.Nodes.FirstOrDefault(x => x.Id == node.Id), game.Data, game.Snapshot.Time)} readyIn={(game.Snapshot.Nodes.FirstOrDefault(x => x.Id == node.Id)?.ReadyAt ?? 0) - game.Snapshot.Time:0.00} stamina={Self.Stamina:0.0}");
        KeyEvent(Key.Space, true);
        double nextTrace = 0;
        await Until(() =>
        {
            if (Now > nextTrace) { nextTrace = Now + 1; GD.Print($"RESOURCE_PROGRESS armed={Field<string>("classicGatherTarget")} confirmed={Field<bool>("classicGatherConfirmed")} focused={Field<bool>("applicationFocused")} busy={Field<bool>("actionBusy")} context={Call("ContextTarget")} count={Items.Count(Self, template)}"); }
            return Items.Count(Self, template) > before && Field<bool>("classicGatherConfirmed");
        }, "Space did not gather from the adjacent resource.");
        KeyEvent(Key.Space, false); await Frame(); await Click((Button)game.FindChild("ClassicActionCircle", true, false)!); await Delay(.15);
        Check(Field<string>("classicGatherTarget") == "", "Clicking the Action Circle stops the confirmed gathering intention");
    }
    private async Task OpenCraft(string recipe)
    { Member("selectedRecipe").SetValue(game, recipe); Call("OpenPage", "Crafting"); await Delay(.25); }
    public override async void _Ready()
    {
        try
        {
            Check(DisplayServer.GetName() != "headless" || System.Environment.GetEnvironmentVariable("KAIRNFALL_HEADLESS_CLASSIC_QA") == "1", "Live QA rendering mode is explicit; headless gameplay does not count as pixel approval");
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA"), "Live preferences are isolated from the player project");
            Check(System.Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") == "Testing", "Only the disposable Testing realm is permitted");
            string address = System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL")!;
            Check(LocalRealmAddressRules.Allowed(address), "The real realm is loopback only");
            bool reload = OS.GetCmdlineUserArgs().Contains("--reload");
            gatherDiagnostic = OS.GetCmdlineUserArgs().Contains("--gather-diagnostic");
            string username, password; SaveRecord? record = null;
            if (reload) { record = JsonSerializer.Deserialize<SaveRecord>(File.ReadAllText(RecordPath), Wire.Json)!; username = record.Username; password = record.Password; }
            else { username = "classic_" + Guid.NewGuid().ToString("N")[..8]; password = "QA_" + Guid.NewGuid().ToString("N"); }
            connection = new GameConnection(address); await connection.SignInAsync(username, password, !reload);
            string id = reload ? record!.Self.Id : (await connection.CreateCharacterAsync(new CharacterRequest { Name = "Classic " + username[^8..], Class = "vanguard", Appearance = new() })).Id;
            await connection.ConnectAsync(id);
            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            GetWindow().Size = new Vector2I(916, 515); GetWindow().ContentScaleSize = new Vector2I(916, 515);
            AddChild(game); var settings = Field<ConfigFile>("settings");
            settings.SetValue("controls", "classic_target_attack", true); settings.SetValue("controls", "classic_grid", true);
            settings.SetValue("controls", "classic_gather", true); settings.SetValue("hud", "focus_world", true); settings.SetValue("hud", "classic_panels", true);
            typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, connection);
            Field<Control>("frontend").Hide(); GetViewport().GuiReleaseFocus();
            await Until(() => game.Snapshot is not null, "The native client received no authoritative snapshot.");
            Call("ApplyFocusHud"); if (DisplayServer.GetName() != "headless") GetWindow().GrabFocus(); await Delay(.25);
            if (reload)
            {
                Check(Self.Id == record!.Self.Id && Self.Name == record.Self.Name && Self.Zone == record.Self.Zone, "Server restart restores character identity and region");
                Check(Self.Position.Distance(record.Self.Position) < .000001, "Server restart preserves the exact valid saved position");
                string Owned(Character p) => JsonSerializer.Serialize(p.Inventory.OrderBy(x => x.Id), Wire.Json);
                Check(Owned(Self) == Owned(record.Self), "Server restart preserves every owned item ID, stack, durability, rune and affix");
                Check(Self.Gold == record.Self.Gold && Self.Equipment.OrderBy(x => x.Key).SequenceEqual(record.Self.Equipment.OrderBy(x => x.Key)), "Server restart preserves gold and equipped item ownership");
                Check(Self.SkillXp.OrderBy(x => x.Key).SequenceEqual(record.Self.SkillXp.OrderBy(x => x.Key)), "Server restart preserves all skill progress");
                Check(Self.Cooldowns.OrderBy(x => x.Key).SequenceEqual(record.Self.Cooldowns.OrderBy(x => x.Key)) && Self.DeadUntil == record.Self.DeadUntil, "Server restart preserves cooldown and death timers");
                Check(Self.CompletedQuests.SetEquals(record.Self.CompletedQuests) && JsonSerializer.Serialize(Self.Quests, Wire.Json) == JsonSerializer.Serialize(record.Self.Quests, Wire.Json), "Server restart preserves quest progress");
                foreach (var structure in record.Structures)
                    Check(game.Snapshot!.Nodes.Any(x => x.Id == structure.Id && x.Owner == Self.Id && x.Template == structure.Template && x.Position == structure.Position && x.ReadyAt == structure.ReadyAt), "Server restart preserves the built structure ID, owner, position and timer");
                Check(game.Snapshot!.Time >= record.Time, "Reload never rewinds the authoritative realm clock");
                Check(Field<string>("classicAttackTarget") == "" && Field<string>("classicGatherTarget") == "", "Reconnect starts without stale automatic attack or gather intentions");
                await Capture("09-server-reload");
            }
            else
            {
                var start = Self.Position; KeyEvent(Key.D, true); await Delay(.07); KeyEvent(Key.D, false);
                await Until(() => Self.Position.Distance(start.Add(new Point(1, 0))) < .000001, "Native tile tap did not finish exactly one tile.");
                await Delay(.35); Check(Self.Position == start.Add(new Point(1, 0)), "Native D tap finishes one authoritative tile and stays there");
                KeyEvent(Key.S, true); await Delay(.7); KeyEvent(Key.S, false); await Frame();
                double releasedTime = game.Snapshot!.Time, quietSince = Now;
                var lastPosition = Self.Position;
                await Until(() =>
                {
                    if (Self.Position != lastPosition) { lastPosition = Self.Position; quietSince = Now; }
                    return game.Snapshot!.Time >= releasedTime + .35 && Now - quietSince >= .35
                        && Math.Abs(Self.Position.Y - Math.Floor(Self.Position.Y) - .5) < .000001;
                }, "Native held release did not settle on an authoritative tile center.");
                GD.Print($"HELD_RELEASE_TRACE position={Self.Position} authoritativeElapsed={game.Snapshot.Time-releasedTime:0.000}");
                Check(Math.Abs(Self.Position.Y - Math.Floor(Self.Position.Y) - .5) < .000001, "Native held movement ends on a tile center");
                var stoppedPosition = Self.Position; await Delay(.35);
                Check(Self.Position == stoppedPosition, "Released native held movement remains stopped without an extra tile");
                await Capture("01-grid-movement");
                string weapon = Self.Equipment["weapon"]; Call("OpenPage", "Inventory"); await Delay(.2);
                var slot = game.FindChildren("*", "Control", true, false).OfType<ClassicItemSlot>().First(x => x.Item?.Id == weapon && !x.IsQueuedForDeletion());
                await Click(slot); await Click(Action("UNEQUIP")); await Until(() => !Self.Equipment.ContainsKey("weapon"), "Compact Unequip was not accepted.");
                await Delay(.2); await Click(Action("EQUIP")); await Until(() => Self.Equipment.GetValueOrDefault("weapon") == weapon, "Compact Equip was not accepted.");
                Check(Self.Inventory.Any(x => x.Id == weapon), "Compact equipment actions preserve the owned item ID");
                await Capture("02-compact-equipment"); await Tap(Key.Escape);
                await Buy("wayfarers_rest_provisioner", "bread", 2);
                var pool = game.Snapshot!.Nodes.Where(x => x.Template == "river_trout_pool").OrderBy(x => x.Position.Distance(Self.Position)).First();
                await ApproachResource(pool); int fishBefore = Items.Count(Self, "river_trout"); long fishXp = Self.SkillXp.GetValueOrDefault("fishing");
                var focusedHudButton = Field<Button>("interactionButton"); focusedHudButton.FocusMode = Control.FocusModeEnum.All;
                focusedHudButton.GrabFocus(); await Frame();
                Check(GetViewport().GuiGetFocusOwner() == focusedHudButton, "A HUD button owns keyboard focus before the world Space action");
                GD.Print($"FIRST_GATHER_TRACE context={Call("ContextTarget")} self={Self.Position} pool={pool.Position} readyIn={pool.ReadyAt-game.Snapshot!.Time:0.0} busy={Field<bool>("actionBusy")} focused={Field<bool>("applicationFocused")}");
                KeyEvent(Key.Space, true); await Until(() => Field<bool>("classicGatherConfirmed") && Items.Count(Self, "river_trout") > fishBefore, "Held Space did not receive a first accepted fishing action.");
                focusedHudButton.FocusMode = Control.FocusModeEnum.None; GetViewport().GuiReleaseFocus();
                KeyEvent(Key.Space, false); await Frame();
                Check(Field<string>("classicGatherTarget") == pool.Id, "Release after the accepted action keeps the same resource armed");
                double gatherTraceAt = 0;
                await Until(() =>
                {
                    if (Now >= gatherTraceAt)
                    {
                        gatherTraceAt = Now + 1;
                        var visible = game.Snapshot!.Nodes.FirstOrDefault(x => x.Id == pool.Id);
                        GD.Print($"GATHER_TRACE armed={Field<string>("classicGatherTarget") == pool.Id} confirmed={Field<bool>("classicGatherConfirmed")} focused={Field<bool>("applicationFocused")} busy={Field<bool>("actionBusy")} positionDelta={Self.Position.Distance(pool.Position):0.000} readyIn={(visible?.ReadyAt ?? 0) - game.Snapshot.Time:0.00} clock={game.Snapshot.Time:0.00} fish={Items.Count(Self, "river_trout")}");
                    }
                    return Items.Count(Self, "river_trout") >= fishBefore + 2;
                }, "Released gathering did not repeat after real resource recovery.", 40);
                Check(Self.SkillXp.GetValueOrDefault("fishing") > fishXp, "Repeated fishing grants authoritative skill XP");
                if (gatherDiagnostic)
                {
                    await Capture("focused-repeat-gather"); Call("StopCombatInput");
                    await connection.DisposeAsync(); connection = null;
                    await NativeTestLifetime.ReleaseSceneAsync(this, game);
                    GD.Print($"CLASSIC_GATHER_DIAGNOSTIC: {checks} checks passed. Focus guards retained; this is not a full graphical playthrough.");
                    GetTree().Quit(0); return;
                }
                int bread = Items.Count(Self, "bread");
                await Until(() => !((Button)game.FindChild("ClassicQuick_food", true, false)!).Disabled, "Quick food did not reflect spent gathering stamina.", 2);
                await Click((Button)game.FindChild("ClassicQuick_food", true, false)!);
                await Until(() => Items.Count(Self, "bread") == bread - 1, "Native quick food did not consume exactly one item.");
                Check(Self.Cooldowns.GetValueOrDefault("food") > game.Snapshot!.Time && Self.Statuses.Any(x => x.Kind == "regeneration"), "Food feedback comes from the server cooldown and regeneration status");
                Check(Field<string>("classicGatherTarget") == "", "Using quick food cancels gathering"); await Capture("03-gathering-food-feedback");
                int fishCount = Items.Count(Self, "river_trout"); string fishId = Self.Inventory.First(x => x.Template == "river_trout").Id;
                Member("selectedItem").SetValue(game, fishId); Call("OpenPage", "Inventory"); await Delay(.2);
                var amount = (SpinBox)game.FindChild("ClassicDropAmount", true, false)!; amount.Value = 1;
                await Click(Action("Drop")); await Until(() => Items.Count(Self, "river_trout") == fishCount - 1, "Compact Drop did not split one selected item.");
                await Delay(.2); var pile = game.World.Loot.First(x => x.Owner == Self.Id && x.Items.Any(i => i.Template == "river_trout"));
                await Tap(Key.Escape); await Tap(Key.Shift); await Until(() => !game.World.Loot.Any(x => x.Id == pile.Id), "Native Shift did not collect eligible underfoot loot.");
                Check(Items.Count(Self, "river_trout") == fishCount, "Drop and underfoot pickup conserve the item quantity"); await Capture("04-underfoot-loot");
                var oreNodes = game.Snapshot!.Nodes.Where(x => x.Template == "copper_vein").ToArray();
                foreach (var node in oreNodes) { if (Items.Count(Self, "copper_ore") >= 3) break; await GatherOnce(node); }
                Check(Items.Count(Self, "copper_ore") >= 3, "A normal starter account gathers enough materials for its first smelt");
                await Walk(game.Data.Npc("wayfarers_rest_blacksmith").Position); int ore = Items.Count(Self, "copper_ore"), bars = Items.Count(Self, "copper_bar");
                await OpenCraft("smelt_copper"); await Click(Action("Craft"));
                await Until(() => Items.Count(Self, "copper_bar") == bars + 1, "Compact Craft did not produce the selected real recipe.");
                Check(Items.Count(Self, "copper_ore") == ore - 3 && Self.SkillXp.GetValueOrDefault(game.Data.Recipe("smelt_copper").Skill) > 0, "Crafting consumes actual ingredients and awards its real skill");
                await Capture("05-accepted-crafting"); await Tap(Key.Escape);
                await Buy("wayfarers_rest_blacksmith", "copper_ore", 2);
                var timber = game.Snapshot!.Nodes.Where(x => x.Template == "oak_tree").ToArray();
                for (int harvest = 0; Items.Count(Self, "oak_log") < 4 && harvest < 4; harvest++) await GatherOnce(timber[harvest % timber.Length]);
                Check(Items.Count(Self, "oak_log") >= 4, "A normal starter account gathers the actual campfire timber without free supplies");
                var rat = game.Snapshot!.Creatures.FirstOrDefault(x => x.Template == "field_rat" && x.Health > 0);
                if (rat is null) { await Walk(game.Data.Zone(Self.Zone).Spawn); await Until(() => game.Snapshot!.Creatures.Any(x => x.Template == "field_rat" && x.Health > 0), "The normal starter rat did not respawn.", 40); rat = game.Snapshot!.Creatures.First(x => x.Template == "field_rat" && x.Health > 0); }
                string ratId = rat.Id;
                var approach = new Point(Math.Floor(rat.Position.X) + .5 - 4, Math.Floor(rat.Position.Y) + .5);
                await Walk(WorldMap.FindFree(game.Data.Zone(Self.Zone), approach)); await Delay(.2);
                var liveTarget = game.Snapshot!.Creatures.First(x => x.Id == ratId);
                var targetClick = game.World.WorldToScreen(liveTarget.Position);
                Check(GetViewport().GetVisibleRect().HasPoint(targetClick), "The rat is visible for native world targeting");
                Mouse(targetClick, true); await Frame(); Mouse(targetClick, false); await Frame();
                Check(Field<string>("selectedTarget") == ratId && Field<string>("classicAttackTarget") == ratId, "A native world mouse click selects and arms exactly the living rat");
                var selectedFrom = Self.Position; await Delay(.3);
                Check(Self.Position == selectedFrom, "Classic target selection never starts automatic approach movement");
                double combatUntil = Now + 45;
                while (game.Snapshot!.Creatures.First(x => x.Id == ratId).Health > 0)
                {
                    if (Now > combatUntil) throw new TimeoutException("Selected adjacent attacks did not kill the normal starter rat.");
                    var live = game.Snapshot.Creatures.First(x => x.Id == ratId);
                    if (Self.Position.Distance(live.Position) > ExperienceRules.WeaponRange(Self, game.Data) - .1) Call("WalkTo", live.Position, false);
                    else Field<List<Point>>("route").Clear();
                    await Delay(.15);
                }
                Field<List<Point>>("route").Clear(); await connection.GridMoveAsync(0, 0); await Delay(.3);
                Check(Self.Bestiary.GetValueOrDefault("field_rat") > 0, "Moving into weapon reach automatically attacks the selected rat and records the kill");
                Check(Field<string>("classicAttackTarget") == "", "A dead selected target cancels automatic attacks"); await Capture("06-selected-combat");
                var combatLoot = game.World.Loot.FirstOrDefault(x => x.Owner == Self.Id);
                if (combatLoot is not null)
                {
                    await Walk(new Point(Math.Floor(combatLoot.Position.X) + .5, Math.Floor(combatLoot.Position.Y) + .5)); await Tap(Key.Shift);
                    await Until(() => !game.World.Loot.Any(x => x.Id == combatLoot.Id), "Shift did not collect the rat's owned loot.");
                }
                var exit = game.Data.Zone(Self.Zone).Exits.First(x => x.Target == "kingsmeadow"); string fromZone = Self.Zone;
                Call("WalkTo", exit.Position, false); double nextExitTrace = 0;
                await Until(() =>
                {
                    if (Now >= nextExitTrace)
                    {
                        nextExitTrace = Now + 1;
                        GD.Print($"EXIT_ROUTE_TRACE self={Self.Position} zone={Self.Zone} target={exit.Position} remaining={Field<List<Point>>("route").Count} next={(Field<List<Point>>("route").Count > 0 ? Field<List<Point>>("route")[0].ToString() : "none")} pending={Member("gridRouteTarget").GetValue(game)} focused={Field<bool>("applicationFocused")} busy={Field<bool>("movementBusy")} health={Self.Health:0.0} serverTime={game.Snapshot!.Time:0.000}");
                    }
                    return Self.Zone != fromZone;
                }, "Grid movement did not cross the normal wilderness road.", 65);
                Check(Self.Zone == "kingsmeadow", "Grid movement preserves the server-authoritative road transition");
                var zone = game.Data.Zone(Self.Zone); var buildFrom = WorldMap.FindFree(zone, Self.Position.Add(new Point(-8, 0))); await Walk(buildFrom);
                var at = new[] { new Point(1, 0), new Point(0, 1), new Point(-1, 0), new Point(0, -1) }.Select(x => Self.Position.Add(x)).First(x => WorldMap.Fits(zone, x) && zone.Exits.All(e => e.Position.Distance(x) > 5) && zone.Spawn.Distance(x) > 5);
                int logs = Items.Count(Self, "oak_log"); ore = Items.Count(Self, "copper_ore");
                await OpenCraft("build_campfire"); await Click(Action("Build")); await Delay(.2);
                Check(Field<string>("placement") == "build", "Build opens the existing world placement workflow");
                Check(Items.Count(Self, "oak_log") == logs && Items.Count(Self, "copper_ore") == ore, "Opening placement consumes no materials");
                var click = game.World.WorldToScreen(at); Mouse(click, true); await Frame(); Mouse(click, false);
                await Until(() => game.Snapshot!.Nodes.Any(x => x.Owner == Self.Id && x.Template == "structure_campfire"), "Native world placement did not build the campfire.");
                Check(Items.Count(Self, "oak_log") == logs - 4 && Items.Count(Self, "copper_ore") == ore - 2, "Accepted building consumes only the actual local recipe costs");
                Check(Self.SkillXp.GetValueOrDefault("construction") > 0, "Building awards authoritative construction progress");
                await Capture("07-built-campfire"); Call("StopCombatInput"); Field<List<Point>>("route").Clear(); await connection.GridMoveAsync(0, 0, true); await Delay(.25);
                record = new SaveRecord { Username = username, Password = password, Self = Wire.Copy(Self), Time = game.Snapshot!.Time,
                    Structures = game.Snapshot.Nodes.Where(x => x.Owner == Self.Id).Select(Wire.Copy).ToList() };
                File.WriteAllText(RecordPath, JsonSerializer.Serialize(record, Wire.Json));
                Check(record.Structures.Count > 0, "Private save checkpoint includes the owned structure");
                await Capture("08-save-checkpoint");
            }
            await connection.DisposeAsync(); connection = null;
            await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GD.Print($"CLASSIC_LIVE_LOOP_CONTRACT: {checks} checks passed; phase={(reload ? "server-reload" : "normal-account-play")}. Real loopback PostgreSQL, native input routing and unchanged catalog balance; rendering={DisplayServer.GetName()}.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_LIVE_LOOP_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game) && game.Snapshot is not null) await Capture("failure-context");
            if (connection is not null) await connection.DisposeAsync();
            if (game is not null && GodotObject.IsInstanceValid(game)) await NativeTestLifetime.ReleaseSceneAsync(this, game);
            GetTree().Quit(1);
        }
    }
}
