using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native GUI events against a disposable real server. Not a human playthrough.</summary>
public partial class LiveExperienceContract : Node
{
    private GameRoot game = null!;
    private int checks;
    private static double Now => Time.GetTicksMsec() / 1000.0;
    private static T Field<T>(GameRoot value, string name)
        => (T)typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(value)!;
    private object? Call(string method, params object?[] args)
        => typeof(GameRoot).GetMethod(method, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private void Attach(GameConnection? connection)
        => typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, connection);
    private Character Self => game.Snapshot?.Self ?? throw new InvalidOperationException("No authoritative snapshot.");
    private void Require(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS LIVE EXPERIENCE: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private async Task Delay(double seconds) => await ToSignal(GetTree().CreateTimer(seconds), SceneTreeTimer.SignalName.Timeout);
    private async Task Until(Func<bool> condition, string failure, double timeout = 8)
    {
        double deadline = Now + timeout;
        while (!condition())
        {
            if (Now >= deadline) throw new TimeoutException(failure);
            await Frame();
        }
    }
    private void KeyEvent(Key key, bool pressed)
    {
        using var input = new InputEventKey { PhysicalKeycode = key, Keycode = key, Pressed = pressed };
        Input.ParseInputEvent(input); Input.FlushBufferedEvents();
    }
    private async Task Tap(Key key)
    {
        KeyEvent(key, true); await Frame(); KeyEvent(key, false); await Frame();
    }
    private void Mouse(Vector2 at, MouseButton button, bool pressed, bool doubleClick = false)
    {
        using var input = new InputEventMouseButton
        {
            Position = at, GlobalPosition = at, ButtonIndex = button, Pressed = pressed, DoubleClick = doubleClick,
            ButtonMask = pressed ? button == MouseButton.Left ? MouseButtonMask.Left : MouseButtonMask.Right : 0
        };
        Input.ParseInputEvent(input); Input.FlushBufferedEvents();
    }
    private async Task Click(Control control, MouseButton button = MouseButton.Left, bool doubleClick = false)
    {
        await Reveal(control);
        var rect = control.GetGlobalRect();
        Require(control.IsVisibleInTree() && GetViewport().GetVisibleRect().HasPoint(rect.GetCenter()), "The native click target is visible: " + control.Name);
        var at = rect.GetCenter(); Mouse(at, button, true, doubleClick); await Frame(); Mouse(at, button, false); await Frame();
    }
    private async Task Reveal(Control control)
    {
        for (Node? parent = control.GetParent(); parent is not null; parent = parent.GetParent())
            if (parent is ScrollContainer scroll) scroll.EnsureControlVisible(control);
        await Frame(); await Frame();
    }
    private EquipmentItemSlot ItemControl(string id)
        => game.FindChildren("*", "Control", true, false).OfType<EquipmentItemSlot>().First(x => x.Item?.Id == id && !x.IsQueuedForDeletion());
    private Button EquipmentAction()
        => game.FindChildren("PrimaryEquipmentAction", "Button", true, false).Cast<Button>().First(x => !x.IsQueuedForDeletion());
    private async Task Drag(EquipmentItemSlot source, Control target)
    {
        await Reveal(source); await Reveal(target);
        var from = source.GetGlobalRect().GetCenter(); var to = target.GetGlobalRect().GetCenter();
        Mouse(from, MouseButton.Left, true); await Frame();
        using (var start = new InputEventMouseMotion { Position = from + new Vector2(16, 0), GlobalPosition = from + new Vector2(16, 0), Relative = new Vector2(16, 0), ButtonMask = MouseButtonMask.Left })
            Input.ParseInputEvent(start);
        Input.FlushBufferedEvents(); await Frame();
        using (var move = new InputEventMouseMotion { Position = to, GlobalPosition = to, Relative = to - from - new Vector2(16, 0), ButtonMask = MouseButtonMask.Left })
            Input.ParseInputEvent(move);
        Input.FlushBufferedEvents(); await Frame();
        Mouse(to, MouseButton.Left, false); await Frame();
    }
    private async Task WalkNear(string creatureId, double distance)
    {
        double deadline = Now + 20;
        while (true)
        {
            var mob = game.Snapshot!.Creatures.FirstOrDefault(x => x.Id == creatureId)
                ?? throw new InvalidOperationException("The setup target left the snapshot.");
            if (Self.Position.Distance(mob.Position) <= distance) break;
            if (Now > deadline) throw new TimeoutException("A normal movement path did not reach the creature.");
            var path = WorldMap.FindPath(game.Data.Zone(Self.Zone), Self.Position, mob.Position, 16000);
            if (path.Count == 0) throw new InvalidOperationException("The setup target has no walkable path.");
            var next = path.FirstOrDefault(x => Self.Position.Distance(x) > .35);
            var direction = Self.Position.Direction(next);
            await game.Connection!.MoveAsync(direction.X, direction.Y);
            await Delay(.08);
        }
        await game.Connection!.MoveAsync(0, 0); await Delay(.3);
    }

    public override async void _Ready()
    {
        try
        {
            if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("This contract requires graphical rendering.");
            if (System.Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT") != "Testing")
                throw new InvalidOperationException("Use the disposable Testing realm.");
            string address = System.Environment.GetEnvironmentVariable("KAIRNFALL_SMOKE_URL") ?? "http://127.0.0.1:5077";
            if (!Uri.TryCreate(address, UriKind.Absolute, out var uri) || !uri.IsLoopback)
                throw new InvalidOperationException("Live QA must use a loopback realm.");
            string suffix = Guid.NewGuid().ToString("N")[..8];
            string username = "native_" + suffix, password = "QA_" + Guid.NewGuid().ToString("N");
            var connection = new GameConnection(address);
            await connection.SignInAsync(username, password, true);
            var created = await connection.CreateCharacterAsync(new CharacterRequest { Name = "Native " + suffix, Class = "vanguard", Appearance = new() });
            await connection.ConnectAsync(created.Id);
            using (var scene = GD.Load<PackedScene>("res://Main.tscn")) game = scene.Instantiate<GameRoot>();
            AddChild(game); Attach(connection); Field<Control>(game, "frontend").Hide(); GetViewport().GuiReleaseFocus();
            await Until(() => game.Snapshot is not null, "The graphical client did not receive its first snapshot.");
            await Delay(.3);
            Require(Self.Zone == "wayfarers_rest", "A normal account starts in Wayfarer's Rest");
            Require(game.Data.Ability(Field<string[]>(game, "hotbar")[0]).Class == Self.Class, "Hotbar 1 starts with the character's class ability");
            var start = Self.Position;
            KeyEvent(Key.D, true); await Delay(1.2); KeyEvent(Key.D, false); await Delay(.4);
            Require(Self.Position.X > start.X + 2.5, "Native physical D input moves the authoritative character");
            Require(Call("ContextTarget") is null, "The empty-space interaction fixture has no nearby interactable");
            long sequence = Self.LastAction; int chatCount = Field<List<string>>(game, "history").Count;
            for (int i = 0; i < 20; i++) { KeyEvent(Key.E, true); KeyEvent(Key.E, false); }
            await Delay(.4);
            Require(Self.LastAction == sequence && Field<List<string>>(game, "history").Count == chatCount,
                "Twenty empty-space E presses send no accepted action and no chat message");
            var dashStart = Self.Position; double dashMana = Self.Mana; long dashSequence = Self.LastAction;
            KeyEvent(Key.Q, true); KeyEvent(Key.Q, false); KeyEvent(Key.Q, true); KeyEvent(Key.Q, false);
            await Until(() => Self.LastAction == dashSequence + 1, "Native Q did not produce one authoritative dash.");
            Require(Self.Position.Distance(dashStart) >= .25 && Self.Position.Distance(dashStart) <= DashRules.Distance + .05, "Native Q performs a bounded server-validated dash");
            Require(Self.Mana < dashMana && Self.Cooldowns.ContainsKey("dash"), "Dash consumes mana and supplies an authoritative cooldown");
            await TargetKeyChecks.Run(this,game,Require);
            await Delay(.3);
            sequence = Self.LastAction;
            KeyEvent(Key.Space, true); await Delay(.1);
            Require(Field<bool>(game, "attackKeyHeld"), "Native Space press arms held combat without sending empty-target requests");
            Field<LineEdit>(game, "chatInput").GrabFocus(); await Delay(.2);
            Require(!Field<bool>(game, "attackKeyHeld"), "Chat focus cancels held combat in the running client");
            var still = Self.Position;
            foreach (var key in new[] { Key.W, Key.E, Key.Q, (Key)49, Key.Tab }) await Tap(key);
            KeyEvent(Key.Space, false); await Delay(.35);
            Require(Self.Position.Distance(still) < .05 && Self.LastAction == sequence, "Typing suppresses movement, interaction, hotbar, and target controls");
            Field<LineEdit>(game, "chatInput").Text = ""; GetViewport().GuiReleaseFocus();
            await Tap(Key.I); await Delay(.3);
            Require(Field<string>(game, "currentPage") == "Inventory", "Native I opens inventory");
            still = Self.Position;
            foreach (var key in new[] { Key.D, Key.E, Key.Q, Key.Space, (Key)49 }) await Tap(key);
            await Delay(.35);
            Require(Self.Position.Distance(still) < .05 && Self.LastAction == sequence, "An open menu blocks world movement and combat");
            string weapon = Self.Equipment["weapon"];
            await Click(ItemControl(weapon)); await Delay(.3);
            Require(EquipmentAction().Text == "UNEQUIP", "Selecting equipped gear exposes a prominent Unequip action");
            await Click(EquipmentAction());
            await Until(() => !Self.Equipment.ContainsKey("weapon"), "Native Unequip button did not change server equipment.");
            await Delay(.3);
            Require(EquipmentAction().Text == "EQUIP", "The same visible action changes to Equip after the server update");
            await Click(EquipmentAction());
            await Until(() => Self.Equipment.GetValueOrDefault("weapon") == weapon, "Native Equip button did not equip the item.");
            Require(true, "The Equip button sends a validated equipment request");
            await Delay(.3); await Click(ItemControl(weapon), doubleClick: true);
            await Until(() => !Self.Equipment.ContainsKey("weapon"), "Native double-click did not unequip the item.");
            await Delay(.3); await Click(ItemControl(weapon), doubleClick: true);
            await Until(() => Self.Equipment.GetValueOrDefault("weapon") == weapon, "Native double-click did not equip the item.");
            Require(true, "Native double-click supports equip and unequip");
            await Delay(.3); await Click(ItemControl(weapon), MouseButton.Right); await Delay(.15);
            EquipmentMenu OpenMenu() => game.FindChildren("*", "Control", true, false).OfType<EquipmentMenu>().Single(x => !x.IsQueuedForDeletion());
            var menu = OpenMenu();
            Require(menu.GetActionButton(0).Text == "Unequip", "Native right-click opens the equipment context menu");
            await Click(menu.GetActionButton(0));
            await Until(() => !Self.Equipment.ContainsKey("weapon"), "Native context-menu Unequip did not change server equipment.");
            Require(true, "A native mouse click on context Unequip reaches the authoritative server");
            await Delay(.3); await Click(ItemControl(weapon), MouseButton.Right); await Delay(.15);
            menu = OpenMenu();
            Require(menu.GetActionButton(0).Text == "Equip", "The reopened context menu reflects authoritative unequipped state");
            await Click(menu.GetActionButton(0));
            await Until(() => Self.Equipment.GetValueOrDefault("weapon") == weapon, "Native context-menu Equip did not change server equipment.");
            Require(true, "A native mouse click on context Equip reaches the authoritative server");
            await Delay(.3); sequence = Self.LastAction;
            var stableSelectedSlot = ItemControl(weapon);
            for (int cycle = 0; cycle < 8; cycle++)
            {
                await Click(ItemControl(weapon), MouseButton.Right); await Delay(.1);
                Require(OpenMenu().IsVisibleInTree(), "Repeated context menu opens without an orphan overlay");
                await Tap(Key.Escape); await Frame();
                Require(!game.FindChildren("*", "Control", true, false).OfType<EquipmentMenu>().Any(x => !x.IsQueuedForDeletion()), "Escape removes the context menu");
                Require(Field<string>(game, "currentPage") == "Inventory", "Closing a context menu retains the inventory window");
                Require(GodotObject.IsInstanceValid(stableSelectedSlot) && ReferenceEquals(stableSelectedSlot,ItemControl(weapon)),
                    "Opening and cancelling selected-item actions preserves the inventory control");
            }
            await Delay(.3);
            Require(Self.LastAction == sequence, "Cancelled context actions send no equipment requests");
            await Click(ItemControl(weapon), MouseButton.Right); await Delay(.15);
            await Click(OpenMenu().GetActionButton(0));
            await Until(() => !Self.Equipment.ContainsKey("weapon"), "The context menu failed after repeated recreation.");
            Require(true, "Context Unequip still works after repeated recreation");
            Call("SaveScreenshot", "06-inventory.png");
            GetViewport().GuiReleaseFocus(); await Tap(Key.C); await Delay(.4);
            var weaponSlot = game.FindChildren("Equipment_weapon", "Control", true, false).Cast<Control>().Single();
            await Drag(ItemControl(weapon), weaponSlot);
            await Until(() => Self.Equipment.GetValueOrDefault("weapon") == weapon, "Native drag-to-weapon-slot did not equip the item.");
            Require(true, "Native drag-and-drop equips the matching paper-doll slot");
            await Delay(.3); Call("SaveScreenshot", "07-equipment.png");
            await Tap(Key.Escape); await Delay(.2); GetViewport().GuiReleaseFocus();
            string rat = game.Snapshot!.Creatures.First(x => x.Template == "field_rat" && x.Health > 0).Id;
            await WalkNear(rat, 1.4);
            var target = game.Snapshot!.Creatures.Single(x => x.Id == rat);
            sequence = Self.LastAction; double health = target.Health;
            var at = game.World.WorldToScreen(target.Position);
            Mouse(at, MouseButton.Left, true); await Frame(); Mouse(at, MouseButton.Left, false); await Delay(.4);
            Require(Field<string>(game, "selectedTarget") == rat, "Native mouse click selects the visible creature");
            Require(Self.LastAction == sequence && game.Snapshot!.Creatures.Single(x => x.Id == rat).Health == health,
                "Selecting a creature does not start automatic attacks");
            double began = Now;
            KeyEvent(Key.Space, true);
            double nextCombatTrace = 0;
            await Until(() =>
            {
                var creature = game.Snapshot!.Creatures.Single(x => x.Id == rat);
                if (Now >= nextCombatTrace)
                {
                    nextCombatTrace = Now + .5;
                    bool held = Field<bool>(game, "attackKeyHeld");
                    bool physical = Input.IsActionPressed("basic_attack");
                    string pageName = Field<string>(game, "currentPage");
                    double cooldown = Self.Cooldowns.GetValueOrDefault("attack") - game.Snapshot.Time;
                    GD.Print($"COMBAT_TRACE elapsed={Now - began:0.00} health={creature.Health:0.0} distance={Self.Position.Distance(creature.Position):0.00} range={ExperienceRules.WeaponRange(Self, game.Data):0.00} held={held} physical={physical} page={pageName} stamina={Self.Stamina:0.0} cooldown={cooldown:0.00} sequence={Self.LastAction - sequence}");
                }
                return creature.Health <= 0;
            }, "Held Space did not resolve the normal starter encounter.", 15);
            long attacks = Self.LastAction - sequence;
            Require(attacks >= 2, "Holding Space sends repeated server-validated attacks");
            Require(attacks <= Math.Ceiling((Now - began) / ExperienceRules.AttackInterval(Self, game.Data)) + 1,
                "Held combat request count stays within weapon cadence");
            await Delay(.4); sequence = Self.LastAction; await Delay(.6);
            Require(Self.LastAction == sequence && !Field<bool>(game, "attackKeyHeld"), "Target death stops held combat without an extra request stream");
            KeyEvent(Key.Space, false);
            Call("SaveScreenshot", "04-player-combat.png");
            long skillXp = Progression.Total(Self);
            Require(skillXp > 0, "Normal movement and combat award authoritative skill XP");
            var pile = game.World.Loot.FirstOrDefault(x => x.Owner == Self.Id);
            if (pile is not null)
            {
                int expectedItems = pile.Items.Count;
                Require(Self.Position.Distance(pile.Position) <= 2.15, "Owned combat loot is within interaction range");
                var pickupTarget = (WorldTarget?)Call("ContextTarget");
                GD.Print($"LOOT_TRACE visiblePiles={game.World.Loot.Count} contextKind={pickupTarget?.Kind} selectedOwnedPile={pickupTarget?.Id == pile.Id}");
                await Tap(Key.E);
                await Until(() => !game.World.Loot.Any(x => x.Id == pile.Id), "E did not collect owned combat loot.");
                if (expectedItems > 0)
                {
                    await Delay(.3);
                    Require(Field<VBoxContainer>(game, "pickupFeed").GetChildCount() > 0, "A real item pickup creates an icon-and-name notification");
                    Call("SaveScreenshot", "10-loot-popup.png");
                }
            }
            var merchantSale = await LiveMerchantChecks.Run(this, game, Require);
            long checkpointXp = Progression.Total(Self);
            string characterId = Self.Id; sequence = Self.LastAction;
            await connection.DisposeAsync(); Attach(null); game.World.ClearSession();
            var reconnected = new GameConnection(address);
            await reconnected.SignInAsync(username, password, false); await reconnected.ConnectAsync(characterId); Attach(reconnected);
            await Until(() => game.Snapshot?.Self.Id == characterId && Self.LastAction >= sequence, "Reconnect did not restore acknowledged state.");
            Require(Self.Gold == merchantSale.Gold && !Self.Inventory.Any(x => x.Id == merchantSale.ItemId), "Native merchant sale quantities and exact gold survive reconnect");
            Require(Self.Equipment.GetValueOrDefault("weapon") == weapon, "GUI-equipped item identity survives reconnect");
            Require(Progression.Total(Self) == checkpointXp, "Acknowledged skill progress survives reconnect");
            Require(!Field<bool>(game, "attackKeyHeld"), "Reconnect does not resume an old held attack");
            for (int cycle = 0; cycle < 3; cycle++)
            {
                await reconnected.DisconnectAsync(); game.World.ClearSession();
                Require(!reconnected.Connected, "Repeated live shutdown completes without a disposed-socket failure");
                await reconnected.ConnectAsync(characterId);
                await Until(() => game.Snapshot?.Self.Id == characterId && Self.LastAction >= sequence, "Repeated reconnect did not restore the authoritative snapshot.");
                Require(Self.Gold == merchantSale.Gold && !Self.Inventory.Any(x => x.Id == merchantSale.ItemId)
                    && Self.Equipment.GetValueOrDefault("weapon") == weapon && Progression.Total(Self) == checkpointXp,
                    "Repeated reconnect retains sold quantities, exact gold, equipment and earned XP");
            }
            GD.Print($"LIVE_EXPERIENCE_CONTRACT: {checks} checks passed. Native generated input, real server and PostgreSQL; not human playtesting or Windows hardware input.");
            await (Task)Call("ShutdownClientAsync", 0)!;
        }
        catch (Exception error)
        {
            GD.PushError("LIVE_EXPERIENCE_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game)) await (Task)Call("ShutdownClientAsync", 1)!;
            else GetTree().Quit(1);
        }
    }
}
