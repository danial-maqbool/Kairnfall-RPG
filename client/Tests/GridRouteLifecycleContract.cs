using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Offline navigation decisions and detached authority commands; no transport or physical-input acceptance.</summary>
public partial class GridRouteLifecycleContract : Node
{
    private int checks;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private static string Json<T>(T value) => JsonSerializer.Serialize(value, Wire.Json);
    private static void Connected(GameConnection connection, bool value)
        => typeof(GameConnection).GetField("connected", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(connection, value);
    private void Check([System.Diagnostics.CodeAnalysis.DoesNotReturnIf(false)] bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS GRID ROUTE LIFECYCLE: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);

    private void Move(RealmEngine realm, string id, Point direction, string arg = GridMovementRules.Step)
    {
        var command = new GameCommand { Kind = "move", Arg = arg, X = direction.X, Y = direction.Y, Sequence = realm.Player(id).LastAction + 1 };
        var result = realm.Execute(id, command);
        Check(Guid.TryParseExact(command.RequestId, "N", out _) && result.Ok && result.RequestId == command.RequestId,
            "Detached authority accepts the real " + arg + " intention with a protocol GUID");
    }

    private void Walk(RealmEngine realm, string id, Point direction)
    {
        var target = GridMovementRules.Next(realm.Player(id).Position, direction);
        Move(realm, id, direction);
        for (int tick = 0; tick < 25 && realm.Player(id).Position.Distance(target) > .000001; tick++) realm.Tick(.1);
        Check(realm.Player(id).Position.Distance(target) <= .000001, "Normal authority ticks complete one cardinal tile");
    }

    private void CheckAuthorityAndGenerations(Catalog data)
    {
        using (var main = new CancellationTokenSource())
        using (var navigationLifetime = new CancellationTokenSource())
        using (var boundedSend = CancellationTokenSource.CreateLinkedTokenSource(main.Token, navigationLifetime.Token))
        {
            boundedSend.Cancel();
            Check(GridNavigationState.SendCancellationIsTimeout(main.Token, navigationLifetime.Token),
                "A bounded send cancellation with live owner lifetimes is a failure, not silent retirement");
            navigationLifetime.Cancel();
            Check(!GridNavigationState.SendCancellationIsTimeout(main.Token, navigationLifetime.Token),
                "Navigation retirement cancellation remains silent");
            using var activeNavigation = new CancellationTokenSource(); main.Cancel();
            Check(!GridNavigationState.SendCancellationIsTimeout(main.Token, activeNavigation.Token),
                "Main lifetime cancellation remains silent");
        }
        var realm = new RealmEngine(data);
        string id = realm.CreateCharacter("offline-grid-route", "Route Wayfarer", "vanguard", new()).Id;
        realm.Active.Add(id);
        var navigation = new GridNavigationState(); var owner = new object();
        var start = realm.Snapshot(id); string initial = Json(realm.State);
        var old = navigation.BeginStep(owner, start, new Point(1, 0), 1)!;
        Check(old is not null && Json(realm.State) == initial, "Planning an unsent owned intention never predicts an accepted world position");
        Move(realm, id, old.Direction); realm.Tick(.1);
        Check(realm.Player(id).Position.Distance(start.Self.Position) > 0
            && realm.Player(id).Position.Distance(old.Target) > .000001, "The real east step is in flight after a normal tick");
        navigation.RetireRoute(); long replacementGeneration = navigation.Generation;
        Check(old.Retired && navigation.BlocksMovement && navigation.BeginCancellation() is null,
            "Replacement retires its owner immediately and cancellation waits for the earlier send completion");
        Check(navigation.BeginStep(owner, realm.Snapshot(id), new Point(-1, 0), 2) is null,
            "A replacement cannot send a conflicting west step while the retired east step is owned");
        Check(!navigation.CompleteStepSend(old, failed: true, now: 2) && navigation.Generation == replacementGeneration,
            "A late old send failure cannot clear or replace the new route generation");
        var cancellation = navigation.BeginCancellation();
        Check(ReferenceEquals(cancellation, old) && navigation.Cancelling && navigation.BeginCancellation() is null,
            "The retired step owns one ordered cancellation decision");
        Move(realm, id, default, GridMovementRules.Cancel); var stopped = realm.Snapshot(id); var stoppedPosition = stopped.Self.Position;
        Check(navigation.CompleteCancellation(old, stopped, failed: false) && navigation.BlocksMovement,
            "Cancel send completion alone does not approve movement or permit a replacement step");
        navigation.ObserveAccepted(stopped); navigation.ObserveAccepted(stopped);
        Check(navigation.Settling, "Repeated pre-fence snapshots cannot settle cancellation");
        realm.Tick(.1); var first = realm.Snapshot(id); navigation.ObserveAccepted(first);
        Check(first.Self.Position == stoppedPosition && navigation.Settling,
            "The real cancellation stops displacement; one newer stationary snapshot still keeps the fence");
        navigation.ObserveAccepted(first);
        Check(navigation.Settling, "Repeating one accepted snapshot cannot count as a second observation");
        realm.Tick(.1); var second = realm.Snapshot(id); navigation.ObserveAccepted(second);
        Check(second.Self.Position == stoppedPosition && !navigation.BlocksMovement,
            "Two distinct newer authoritative stationary snapshots release the observation fence without claiming a cancellation ACK");
        var replacement = navigation.BeginStep(owner, second, new Point(-1, 0), 3)!;
        Check(replacement is not null && replacement.Target == GridMovementRules.Next(second.Self.Position, new Point(-1, 0)),
            "Replacement derives its target solely from the latest accepted stopped position");
        Check(!navigation.CompleteStepSend(old, failed: true, now: 3)
            && ReferenceEquals(navigation.Step, replacement), "Old completion cannot reset the replacement step owner");
        Move(realm, id, replacement.Direction); navigation.CompleteStepSend(replacement, failed: false, now: 3);
        for (int tick = 0; tick < 25 && realm.Player(id).Position.Distance(replacement.Target) > .000001; tick++) realm.Tick(.1);
        navigation.ObserveAccepted(realm.Snapshot(id));
        Check(realm.Player(id).Position.Distance(replacement.Target) <= .000001 && navigation.Step is null,
            "The replacement arrives through actual authority ticks rather than fabricated accepted movement");

        var uncertain = navigation.BeginStep(owner, realm.Snapshot(id), new Point(1, 0), 4)!;
        navigation.CompleteStepSend(uncertain, failed: false, now: 4); navigation.RetireRoute(); navigation.BeginCancellation();
        Check(navigation.CompleteCancellation(uncertain, realm.Snapshot(id), failed: true)
            && navigation.CancellationFailed && navigation.BlocksMovement,
            "An unsuccessful cancellation keeps movement blocked instead of dispatching a conflicting step");
        navigation.ResetSession(); var newOwner = new object();
        var fresh = navigation.BeginStep(newOwner, realm.Snapshot(id), new Point(0, 1), 5)!;
        Check(fresh is not null && !navigation.CompleteCancellation(uncertain, realm.Snapshot(id), failed: false)
            && !navigation.CompleteStepSend(uncertain, failed: true, now: 5)
            && ReferenceEquals(navigation.Step, fresh), "Session recovery rejects every old send/cancellation completion");
    }

    private void SeedUnsentRoute(GameRoot game, GameConnection owner)
    {
        Call(game, "ClearRoute");
        Field<List<Point>>(game, "route").Add(game.Snapshot!.Self.Position.Add(new Point(1, 0)));
        var request = Field<GridNavigationState>(game, "gridNavigation").BeginStep(owner, game.Snapshot!, new Point(1, 0), 1)!;
        Check(request is not null, "Offline UI fixture owns an unsent intention, not simulated transport acceptance");
        Member("gridRouteTarget").SetValue(game, request.Target);
    }

    private void CheckManualToClick(Catalog data)
    {
        var realm = new RealmEngine(data);
        string id = realm.CreateCharacter("offline-manual-grid-route", "Manual Route", "vanguard", new()).Id;
        realm.Active.Add(id);
        var navigation = new GridNavigationState(); var owner = new object();
        var start = realm.Snapshot(id);
        var manual = navigation.BeginManualSend(owner, start, new Point(1, 0), 1)!;
        Move(realm, id, manual.Direction, GridMovementRules.Intent);
        navigation.CompleteStepSend(manual, failed: false, now: 1); realm.Tick(.02);
        var partial = realm.Snapshot(id);
        Check(partial.Self.Position.X > start.Self.Position.X && partial.Self.Position.X < manual.Target.X,
            "The real manual grid intention owns an in-flight east target");
        navigation.RetireRoute(retireManual: false);
        Check(!manual.Retired && !navigation.BlocksMovement,
            "Clearing click routing for held input never cancels the manual intention on every frame");
        Check(ReferenceEquals(navigation.BeginManualSend(owner, partial, default, 2), manual) && !manual.SendCompleted,
            "A key-release write remains owned and must finish before a later cancellation can be sent");
        Move(realm, id, default, GridMovementRules.Intent);
        navigation.CompleteStepSend(manual, failed: false, now: 2); realm.Tick(.02);
        var released = realm.Snapshot(id);
        Check(released.Self.Position.X > partial.Self.Position.X && released.Self.Position.X < manual.Target.X,
            "Real key release preserves and continues the manual server target");
        // Reproduce the former conflict through actual detached commands. This
        // deliberately unfenced baseline is not fabricated movement acceptance.
        var unfencedTarget = GridMovementRules.Next(released.Self.Position, new Point(-1, 0));
        Move(realm, id, new Point(-1, 0)); realm.Tick(.02);
        var retained = realm.Snapshot(id);
        Check(unfencedTarget.X < released.Self.Position.X && retained.Self.Position.X > released.Self.Position.X,
            "A direct conflicting click step changes direction but the authority retains its earlier manual east target");
        navigation.RetireRoute();
        Check(manual.Retired && navigation.BlocksMovement
            && navigation.BeginStep(owner, retained, new Point(0, 1), 3) is null,
            "Click replacement fences possible manual ownership before deriving a new step target");
        Check(ReferenceEquals(navigation.BeginCancellation(), manual),
            "The possible manual target uses the same owned ordered cancellation decision");
        Move(realm, id, default, GridMovementRules.Cancel);
        navigation.CompleteCancellation(manual, realm.Snapshot(id), failed: false);
        realm.Tick(.02); navigation.ObserveAccepted(realm.Snapshot(id));
        realm.Tick(.02); var stopped = realm.Snapshot(id); navigation.ObserveAccepted(stopped);
        Check(!navigation.BlocksMovement && stopped.Self.Position == retained.Self.Position,
            "Real cancellation and newer stationary observations retire the manual target without claiming a transport ACK");
        var destination = start.Self.Position.Add(new Point(0, 2));
        var path = WorldMap.FindPath(data.Zone(stopped.Self.Zone), stopped.Self.Position, destination, 16000);
        Check(path.Count > 0, "The replacement click route is replanned from the actual fractional stopped position");
        int steps = 0;
        while (path.Count > 0 && steps++ < 8)
        {
            var accepted = realm.Snapshot(id);
            while (path.Count > 0 && accepted.Self.Position.Distance(path[0]) <= .000001) path.RemoveAt(0);
            if (path.Count == 0) break;
            var request = navigation.BeginStep(owner, accepted, accepted.Self.Position.Direction(path[0]), 4 + steps)!;
            Check(request is not null, "A replanned replacement step starts only after the old manual owner is retired");
            Move(realm, id, request.Direction); navigation.CompleteStepSend(request, failed: false, now: 4 + steps);
            for (int tick = 0; tick < 25 && realm.Player(id).Position.Distance(request.Target) > .000001; tick++) realm.Tick(.1);
            navigation.ObserveAccepted(realm.Snapshot(id));
            Check(navigation.Step is null && realm.Player(id).Position.Distance(request.Target) <= .000001,
                "The replanned route step reaches its accepted target through normal authority ticks");
        }
        Check(realm.Player(id).Position.Distance(destination) <= .000001,
            "The fenced manual-to-click route reaches its requested destination without a retained-target timeout");
    }

    private async Task Capture()
    {
        if (DisplayServer.GetName() == "headless") return;
        await Frame(); await Frame();
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
            ?? throw new InvalidOperationException("Provide isolated fixture screenshots.");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, "grid-route-retirement-offline.png")) == Error.Ok,
            "Saved the offline navigation fixture frame; no physical input or live transport approval");
    }

    public override async void _Ready()
    {
        GameRoot? game = null; GameConnection? connection = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal), "Native fixture settings remain isolated");
            var ordinary = PixelAssets.LoadCatalog(); string ordinaryBefore = Json(ordinary);
            var data = Wire.Copy(ordinary); ClassicTutorialContent.Enable(data);
            CheckAuthorityAndGenerations(data);
            CheckManualToClick(data);

            var realm = new RealmEngine(data);
            string id = realm.CreateCharacter("offline-grid-ui", "Route Observer", "vanguard", new()).Id; realm.Active.Add(id);
            string secondId = realm.CreateCharacter("offline-grid-ui-other", "Other Route", "vanguard", new()).Id;
            // All UI snapshots below come from real movement commands. No character
            // position, facing, stamina, XP, inventory or world record is patched.
            for (int tile = 0; tile < 3; tile++) Walk(realm, id, new Point(0, 1));
            for (int tile = 0; tile < 2; tile++) Walk(realm, id, new Point(1, 0));
            var snapshot = realm.Snapshot(id); var node = snapshot.Nodes.Single(x => x.Id == ClassicTutorialContent.ZoneId + "/tree");
            Check(ClassicTutorialContent.FacingAdjacent(snapshot.Self, node.Position), "UI readiness uses real adjacent position and facing earned through tile movement");
            string worldBefore = Json(realm.State), lootBefore = Json(realm.Loot), selfBefore = Json(snapshot.Self);
            game = new GameRoot { LayoutMode = 1 }; AddChild(game); game.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
            game.SetProcess(false); await Frame();
            typeof(GameRoot).GetProperty(nameof(GameRoot.Data))!.SetValue(game, data); game.World.Data = data;
            game.World.Accept(new TransportPacket { Snapshot = snapshot }); Field<Control>(game, "frontend").Hide();
            connection = new GameConnection("http://127.0.0.1:1");
            typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, connection);
            Check(!connection.Connected, "Fixture connection has no socket, session, account or live service");
            var target = new WorldTarget("node", node.Id, data.Resource(node.Template).Name, node.Position);

            SeedUnsentRoute(game, connection); Member("pendingInteraction").SetValue(game, target);
            long beforeGeneration = Field<GridNavigationState>(game, "gridNavigation").Generation;
            Call(game, "WalkTo", snapshot.Self.Position.Add(new Point(0, 2)), true);
            Check(Field<Point?>(game, "gridRouteTarget") is null && Field<List<Point>>(game, "route").Count > 0
                && Field<GridNavigationState>(game, "gridNavigation").Generation > beforeGeneration
                && Field<WorldTarget?>(game, "pendingInteraction") == target,
                "Immediate route replacement retires its pending target while keepInteraction preserves the selected action");
            Check((Vector2)Call(game, "TickGridRoute")! == Vector2.Zero,
                "Replacement before any cleanup frame cannot reuse an old pending direction or timeout");

            Call(game, "RetireNavigationSession"); SeedUnsentRoute(game, connection);
            game.Notification(checked((int)NotificationApplicationFocusOut));
            Check(Field<Point?>(game, "gridRouteTarget") is null && Field<List<Point>>(game, "route").Count == 0,
                "Production focus loss retires the pending target immediately");
            game.Notification(checked((int)NotificationApplicationFocusIn));
            Call(game, "WalkTo", snapshot.Self.Position.Add(new Point(0, 2)), false);
            Check((Vector2)Call(game, "TickGridRoute")! == Vector2.Zero,
                "Focus recovery and replacement before a frame cannot resume the cancelled owned step");

            Call(game, "RetireNavigationSession"); SeedUnsentRoute(game, connection);
            game.Notification(checked((int)NotificationApplicationFocusIn)); GetViewport().GuiReleaseFocus();
            // Connected is only the UI gate. The unsent owned step blocks every
            // sender below; this connection still has no socket/session/server.
            Connected(connection, true); Input.ActionPress("move_left");
            try { game._Process(0); }
            finally { Input.ActionRelease("move_left"); Connected(connection, false); }
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<Point?>(game, "gridRouteTarget") is null
                && Field<GridNavigationState>(game, "gridNavigation").BlocksMovement && connection.LastSequence == 0,
                "Production manual-input frame retires the old target before any conflicting movement dispatch");

            Call(game, "RetireNavigationSession");
            var manualNavigation = Field<GridNavigationState>(game, "gridNavigation");
            var manualUi = manualNavigation.BeginManualSend(connection, snapshot, new Point(1, 0), 1)!;
            manualNavigation.CompleteStepSend(manualUi, failed: false, now: 1);
            Call(game, "ClearRouteForHeldMovement");
            Check(!manualUi.Retired && !manualNavigation.BlocksMovement,
                "Production held-input cleanup preserves possible manual tile ownership");
            Call(game, "WalkTo", snapshot.Self.Position.Add(new Point(0, 2)), false);
            Check(manualUi.Retired && manualNavigation.BlocksMovement && Field<List<Point>>(game, "route").Count > 0
                && (Vector2)Call(game, "TickGridRoute")! == Vector2.Zero && connection.LastSequence == 0,
                "Production first click routing fences possible manual ownership before any new target dispatch");

            Call(game, "RetireNavigationSession"); SeedUnsentRoute(game, connection);
            using (var escape = new InputEventKey { PhysicalKeycode = Key.Escape, Keycode = Key.Escape, Pressed = true }) game._UnhandledInput(escape);
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<Point?>(game, "gridRouteTarget") is null,
                "Production Escape cancellation retires ownership without waiting for a cleanup frame");

            Call(game, "RetireNavigationSession"); SeedUnsentRoute(game, connection);
            Member("pendingInteraction").SetValue(game, target);
            Check((string)Call(game, "InteractionProblem", target, false)! == "", "Generic resource interaction is ready in the actual authority snapshot");
            Check((bool)Call(game, "ResolvePendingRouteInteraction", true)! && Field<List<Point>>(game, "route").Count == 0
                && Field<Point?>(game, "gridRouteTarget") is null && Field<GridNavigationState>(game, "gridNavigation").BlocksMovement
                && Field<WorldTarget?>(game, "pendingInteraction") == target && connection.LastSequence == 0,
                "Ready generic interaction retires movement before any new dispatch and defers activation behind owned cancellation");

            Call(game, "RetireNavigationSession"); SeedUnsentRoute(game, connection);
            var oldOperation = Call(game, "BeginNavigationSend")!; var newOperation = Call(game, "BeginNavigationSend")!;
            Call(game, "EndNavigationSend", oldOperation);
            Check(Field<bool>(game, "movementBusy") && ReferenceEquals(Field<object>(game, "navigationSend"), newOperation),
                "A stale asynchronous finally cannot release the newer movement owner's busy guard");
            Call(game, "EndNavigationSend", newOperation);
            Call(game, "ObserveNavigationContext", connection, snapshot); game._Process(.01);
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<Point?>(game, "gridRouteTarget") is null
                && Field<GridNavigationState>(game, "gridNavigation").Step is null && !Field<bool>(game, "movementBusy"),
                "Production disconnected frame retires every old navigation owner before recovery");

            SeedUnsentRoute(game, connection); Call(game, "ObserveNavigationContext", connection, snapshot);
            // Seed stale navigation metadata, never an accepted character position.
            Member("navigationZone").SetValue(game, "wayfarers_rest");
            Call(game, "ObserveNavigationContext", connection, snapshot);
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<GridNavigationState>(game, "gridNavigation").Step is null,
                "Accepted zone ownership retires a route recorded for the prior zone");
            SeedUnsentRoute(game, connection);
            var secondSnapshot = realm.Snapshot(secondId); game.World.Accept(new TransportPacket { Snapshot = secondSnapshot });
            Call(game, "ObserveNavigationContext", connection, secondSnapshot);
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<GridNavigationState>(game, "gridNavigation").Step is null,
                "A real other character's initial snapshot cannot inherit the previous character's navigation");
            game.World.Accept(new TransportPacket { Snapshot = snapshot }); Call(game, "ObserveNavigationContext", connection, snapshot);

            SeedUnsentRoute(game, connection); Call(game, "OpenPage", "Menu");
            Check(Field<List<Point>>(game, "route").Count == 0 && Field<Point?>(game, "gridRouteTarget") is null,
                "Full menus retire routes immediately, including while disconnected");
            Call(game, "ClosePage"); Call(game, "RetireNavigationSession");
            Check(Json(realm.State) == worldBefore && Json(realm.Loot) == lootBefore && Json(snapshot.Self) == selfBefore
                && Json(ordinary) == ordinaryBefore && connection.LastSequence == 0,
                "UI retirement changes no authoritative positions, facing, rewards, saves or transport action sequence");
            await Capture();
            typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, null);
            await connection.DisposeAsync(); connection = null;
            await NativeTestLifetime.ReleaseSceneAsync(this, game); game = null;
            GD.Print($"GRID_ROUTE_LIFECYCLE_CONTRACT: {checks} checks passed. Offline native decisions and real detached authority move/cancel commands; no live transport, reconnect round-trip or physical-input acceptance.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("GRID_ROUTE_LIFECYCLE_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game))
            {
                typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, null);
                await NativeTestLifetime.ReleaseSceneAsync(this, game);
            }
            if (connection is not null) await connection.DisposeAsync();
            GetTree().Quit(1);
        }
    }
}
