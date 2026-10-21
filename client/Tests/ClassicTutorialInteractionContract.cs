using Godot;
using Kairnfall.Core;
using System.Reflection;
using System.Text.Json;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Offline native site selection and readiness. Realm commands below use only an in-memory authority.</summary>
public partial class ClassicTutorialInteractionContract : Node
{
    private int checks;
    private static FieldInfo Member(string name) => typeof(GameRoot).GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)!;
    private static T Field<T>(GameRoot game, string name) => (T)Member(name).GetValue(game)!;
    private static object? Call(GameRoot game, string name, params object?[] args)
        => typeof(GameRoot).GetMethod(name, BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, args);
    private static T Property<T>(GameRoot game, string name)
        => (T)typeof(GameRoot).GetProperty(name, BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
    private static string State(Character player) => JsonSerializer.Serialize(player, Wire.Json);
    private static WorldTarget Target(ClassicTutorialSite site) => new("classic_site", site.Id, site.Name, site.Position);
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS TUTORIAL INTERACTION: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private static void Catalog(GameRoot game, Catalog data)
    {
        typeof(GameRoot).GetProperty(nameof(GameRoot.Data))!.SetValue(game, data); game.World.Data = data;
    }
    private static void Connected(GameConnection connection, bool value)
        => typeof(GameConnection).GetField("connected", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(connection, value);
    private string TraceInputGate(GameRoot game, string stage)
    {
        string diagnostic = $"allowed={Property<bool>(game, "GameplayInputAllowed")} online={Property<bool>(game, "Online")}"
            + $" focused={Field<bool>(game, "applicationFocused")} typing={Property<bool>(game, "Typing")}"
            + $" frontend={Field<Control>(game, "frontend").Visible} modal={Field<PanelContainer?>(game, "gameWindow") is not null}"
            + $" closing={Field<bool>(game, "closing")} binding={Field<string>(game, "awaitingBinding")} health={game.Snapshot?.Self.Health}"
            + $" guiFocus={GetViewport().GuiGetFocusOwner()?.GetClass() ?? "none"} actionBusy={Field<bool>(game, "actionBusy")}"
            + $" movementBusy={Field<bool>(game, "movementBusy")} selected={Field<string>(game, "selectedTargetKind")}/{Field<string>(game, "selectedTarget")}";
        GD.Print("TUTORIAL_INPUT_GATE " + stage + " " + diagnostic);
        return diagnostic;
    }
    private void CheckInputGate(GameRoot game, bool expected, string stage)
    {
        string diagnostic = TraceInputGate(game, stage);
        Check(Property<bool>(game, "GameplayInputAllowed") == expected,
            stage + (expected ? " permits world input" : " blocks world input") + " (" + diagnostic + ")");
    }
    private void FocusForSyntheticInput(GameRoot game, GameConnection connection, string stage)
    {
        // Exercise the production callback, never overwrite applicationFocused.
        // Keep the socketless connection disconnected while notifications run,
        // so focus cancellation cannot attempt an asynchronous movement send.
        Connected(connection, false); game.Notification(checked((int)NotificationApplicationFocusIn));
        GetViewport().GuiReleaseFocus(); Connected(connection, true);
        Check(Field<bool>(game, "applicationFocused"), stage + " restores application focus through its notification");
        CheckInputGate(game, true, stage);
    }
    private void ClickWorld(GameRoot game, Point position, bool allowed, string stage)
    {
        // No frame or await may intervene between this gate assertion and the
        // synthetic input: actual native windows can lose focus during a frame.
        CheckInputGate(game, allowed, stage);
        using var click = new InputEventMouseButton { Position = game.World.WorldToScreen(position), ButtonIndex = MouseButton.Left, Pressed = true };
        game._UnhandledInput(click);
    }
    private static void Accept(GameRoot game, Snapshot snapshot)
    {
        // Sites are catalog-defined. Unrelated dynamic targets do not take part in this fixture.
        snapshot.Nodes.Clear(); snapshot.Creatures.Clear(); snapshot.Chests.Clear(); snapshot.Events.Clear();
        game.World.Accept(new TransportPacket { Snapshot = snapshot, Loot = [] }); Call(game, "UpdateHud");
    }
    private async Task Capture(string name, GameConnection connection)
    {
        if (DisplayServer.GetName() == "headless") return;
        bool wasConnected = connection.Connected;
        // Native focus notifications can arrive while awaited frames render.
        // The fake input gate must not send movement during those callbacks.
        Connected(connection, false);
        try
        {
            await Frame(); await Frame();
            await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
            string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS")
                ?? throw new InvalidOperationException("Provide isolated screenshots.");
            System.IO.Directory.CreateDirectory(root);
            using var image = GetViewport().GetTexture().GetImage();
            Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved native " + name);
        }
        finally { Connected(connection, wasConnected); }
    }
    private void CheckReadiness(Catalog normal, Catalog data, Character player)
    {
        var self = Wire.Copy(player); var site = ClassicTutorialContent.Sites[0]; var target = Target(site);
        foreach (var facing in new Point[] { new(0, -1), new(1, 0), new(0, 1), new(-1, 0) })
        {
            self.Position = site.Position.Add(facing.Scale(-1)); self.Facing = facing;
            string before = State(self);
            Check(ClassicTutorialContent.FacingAdjacent(self, site.Position), "Cardinal fixture matches the realm's facing contract: " + facing);
            Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) == "", "Each accepted facing-adjacent tile permits a site intention: " + facing);
            Check(State(self) == before, "Readiness cannot grant progress or rewards: " + facing);
        }
        self.Position = site.Position.Add(new Point(0, 1)); self.Facing = new Point(0, -1);
        Check(!WorldMap.LineOfSight(data.Zone(self.Zone), self.Position, site.Position), "Solid sign blocks the ordinary full endpoint check");
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) == "", "Short approach visibility retains a reachable solid sign");
        self.Facing = new Point(1, 0);
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10).Contains("face"), "Wrong facing explains the adjacent action");
        Check(ClassicInteractionRules.ChooseTutorialSite(self, [target], data, 10) is null, "Automatic context excludes a site the player does not face");
        self.Position = site.Position.Add(new Point(1, 1)); self.Facing = new Point(-1, -1);
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) != "", "Diagonal contact is not cardinal adjacency");
        self.Position = site.Position.Add(new Point(0, 2)); self.Facing = new Point(0, -1);
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) != "", "A distant site cannot imply an interaction");
        self.Position = site.Position.Add(new Point(0, 1.04));
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) == "", "Readiness preserves the realm's 1.05 distance tolerance");
        self.Position = site.Position.Add(new Point(0, 1.06));
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) != "", "Distance beyond the realm's tolerance is blocked");
        self.Position = site.Position.Add(new Point(0, 1));
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target with { Position = self.Position }, data, 10).Contains("no longer"), "Forged site coordinates cannot alter readiness");
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target with { Id = "missing-site" }, data, 10) != "", "Unknown site IDs are excluded");
        foreach (double invalid in new[] { double.NaN, double.PositiveInfinity, double.NegativeInfinity })
            Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, invalid).Contains("snapshot"), "Nonfinite realm time cannot advertise a ready site");
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, normal, 10) != "", "An ordinary catalog cannot expose optional site actions");
        self.ClassicTutorial = null;
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) != "", "Local progress is required even in an optional catalog");
        self.ClassicTutorial = Wire.Copy(player.ClassicTutorial!); self.Zone = OpeningJourney.Home;
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10) != "", "Tutorial progress does not expose First Glade objects in another zone");
        self.Zone = ClassicTutorialContent.ZoneId; self.Health = 0;
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10).StartsWith("Respawn"), "A dead player cannot advertise site actions");
        self.Health = player.Health; self.Facing = new Point(double.NaN, 0);
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, data, 10).Contains("snapshot"), "Malformed accepted facing is blocked before cardinal conversion");
        self.Facing = new Point(0, -1);
        var obstructed = Wire.Copy(data);
        obstructed.Zone(self.Zone).Furnishings.Add(new FurnishingDef { Id = "fixture-obstacle", X = (int)self.Position.X, Y = (int)self.Position.Y, Solid = true });
        Check(InteractionReadinessRules.TutorialSiteProblem(self, target, obstructed, 10).Contains("obstacle"), "Short approach still respects actual collision obstacles");
    }
    private void CheckNormalCreatureControls(GameRoot game, Catalog data, Character ordinary, GameConnection connection)
    {
        var config = Field<ConfigFile>(game, "settings"); string preferences = config.EncodeToText();
        var zone = data.Zone(ordinary.Zone); var definition = data.Mobs.First(x => x.Ai is "passive" or "fleeing");
        var directions = new Point[] { new(1, 0), new(-1, 0), new(0, 1), new(0, -1) };
        double reach = ExperienceRules.BasicAttackRange(ordinary, data);
        Point Clear(IEnumerable<Point> points) => points.First(x => WorldMap.Fits(zone, x) && WorldMap.LineOfSight(zone, ordinary.Position, x));
        var near = Clear(directions.Select(x => ordinary.Position.Add(x.Scale(Math.Min(1, reach)))));
        var far = Clear(directions.SelectMany(direction => Enumerable.Range(3, 7)
            .Select(distance => ordinary.Position.Add(direction.Scale(distance))))
            .Where(x => x.Distance(ordinary.Position) > reach && x.Distance(ordinary.Position) < ExperienceRules.TargetCycleRadius));
        var neutral = new Creature { Id = "normal-neutral-selection", Template = definition.Id, Zone = ordinary.Zone,
            Position = near, Home = near, Health = definition.Health, Facing = new Point(0, 1) };
        void ShowNeutral(Point at)
        {
            neutral.Position = at;
            game.World.Accept(new TransportPacket { Snapshot = new Snapshot { Self = Wire.Copy(ordinary), Time = 10, Creatures = [Wire.Copy(neutral)] }, Loot = [] });
            Call(game, "UpdateHud");
        }
        void ClickNeutral() => ClickWorld(game, neutral.Position, true, "Normal creature click");
        try
        {
            config.Clear(); ShowNeutral(near); Call(game, "SelectTarget", "", "");
            Check(!Property<bool>(game, "ClassicControls"), "Fresh ordinary controls require an explicit attack input");
            FocusForSyntheticInput(game, connection, "Normal-world selection setup"); string before = State(game.Snapshot!.Self);
            ClickNeutral();
            // Check before ticking: a fallback regression must fail before the
            // fake input gate could issue any ready attack intention.
            Check(Field<string>(game, "classicAttackTarget") == "", "Fresh normal single click never arms neutral wildlife");
            Call(game, "TickExperience", .11d);
            Check(Field<string>(game, "selectedTargetKind") == "creature" && Field<string>(game, "selectedTarget") == neutral.Id,
                "Fresh normal click retains exactly the inspected creature");
            Check(Field<List<Point>>(game, "route").Count == 0 && !Field<bool>(game, "combatApproach")
                && !Field<bool>(game, "attackKeyHeld"), "Ordinary selection cannot start movement or a held attack");
            Check(State(game.Snapshot.Self) == before && connection.LastSequence == 0 && !Field<bool>(game, "actionBusy"),
                "Idle normal selection preserves rewards and transport sequence");

            config.SetValue("controls", "classic_target_attack", true); ShowNeutral(far);
            Call(game, "SelectTarget", "", ""); Field<List<Point>>(game, "route").Add(neutral.Position);
            Check(Property<bool>(game, "ClassicControls") && !ClassicTargetRules.Ready(game.Snapshot!.Self, neutral, data, 10),
                "Explicit saved classic preference remains active with the fixture outside attack reach");
            ClickNeutral(); Call(game, "TickExperience", .11d);
            Check(Field<string>(game, "classicAttackTarget") == neutral.Id && Field<string>(game, "selectedTarget") == neutral.Id,
                "Explicit classic click arms only its chosen creature");
            Check(Field<List<Point>>(game, "route").Count == 0 && !Field<bool>(game, "combatApproach") && connection.LastSequence == 0,
                "Armed classic selection waits for player movement without chasing or sending out-of-range attacks");
            Connected(connection, false); game.Notification(checked((int)NotificationApplicationFocusOut));
            Check(Field<string>(game, "classicAttackTarget") == "", "Focus loss clears explicitly armed normal-world classic targeting");
            FocusForSyntheticInput(game, connection, "Normal-world focus recovery");
            ClickNeutral(); Call(game, "OpenPage", "Inventory"); Call(game, "TickExperience", .11d);
            Check(Field<string>(game, "classicAttackTarget") == "" && Field<List<Point>>(game, "route").Count == 0,
                "A menu cancels armed classic targeting through the active input gate");
            Call(game, "ClosePage"); GetViewport().GuiReleaseFocus();
        }
        finally
        {
            Connected(connection, false); Call(game, "StopCombatInput"); config.Clear();
            Check(config.Parse(preferences) == Error.Ok && config.EncodeToText() == preferences,
                "Normal-control regression restores its in-memory preferences without saving them");
        }
    }
    private void CheckTutorialResourceControls(GameRoot game, Catalog normal, Catalog data, RealmEngine realm, Character player, GameConnection connection)
    {
        var config = Field<ConfigFile>(game, "settings"); string preferences = config.EncodeToText();
        var original = Wire.Copy(game.Snapshot!); var originalLoot = Wire.Copy(game.World.Loot);
        string originalKind = Field<string>(game, "selectedTargetKind"), originalTarget = Field<string>(game, "selectedTarget");
        var snapshot = realm.Snapshot(player.Id); snapshot.Creatures.Clear(); snapshot.Chests.Clear(); snapshot.Events.Clear();
        var node = Wire.Copy(snapshot.Nodes.First(x => x.Template == "classic_tree")); snapshot.Nodes = [node];
        snapshot.Self.Position = node.Position.Add(new Point(0, 1)); snapshot.Self.Facing = new(0, -1);
        var target = new WorldTarget("node", node.Id, data.Resource(node.Template).Name, node.Position);
        void Show(Snapshot value)
        {
            Call(game, "StopCombatInput");
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(value), Loot = [] });
            Call(game, "SelectTarget", "node", node.Id); Call(game, "UpdateHud");
        }
        void ReleaseSpace()
        {
            using var release = new InputEventAction { Action = "basic_attack", Pressed = false };
            game._Input(release);
        }
        void Reject(Snapshot value, string label, string reason)
        {
            Show(value); CheckInputGate(game, true, label); Call(game, "TickExperience", .11d);
            var button = Field<Button>(game, "interactionButton");
            Check(Call(game, "ContextTarget") is WorldTarget { Kind: "node" } selected && selected.Id == node.Id
                && button.Disabled && button.TooltipText.Contains(reason, StringComparison.Ordinal),
                label + " retains the resource and its actionable readiness reason");
            string before = State(game.Snapshot!.Self); Call(game, "PrimaryAction", true);
            Check(Field<string>(game, "classicGatherTarget") == "" && Field<string>(game, "classicAttackTarget") == ""
                && !Field<bool>(game, "attackKeyHeld") && !Field<bool>(game, "combatApproach")
                && Field<List<Point>>(game, "route").Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null,
                label + " cannot arm gathering, attack or a chase route");
            Check(State(game.Snapshot.Self) == before && connection.LastSequence == 0 && !Field<bool>(game, "actionBusy"),
                label + " preserves rewards and transport sequence");
            ReleaseSpace();
        }
        try
        {
            config.SetValue("controls", "classic_gather", true);
            FocusForSyntheticInput(game, connection, "Tutorial resource setup");
            foreach (var facing in new Point[] { new(0, -1), new(1, 0), new(0, 1), new(-1, 0) })
            {
                var cardinal = Wire.Copy(snapshot); cardinal.Self.Position = node.Position.Add(facing.Scale(-1)); cardinal.Self.Facing = facing;
                Check(ClassicTutorialContent.FacingAdjacent(cardinal.Self, node.Position)
                    && ClassicGatherRules.Problem(cardinal.Self, node, data, cardinal.Time) == "",
                    "Each realm-accepted cardinal resource approach has matching client readiness: " + facing);
            }
            var wrongFacing = Wire.Copy(snapshot); wrongFacing.Self.Facing = new(1, 0); Reject(wrongFacing, "Wrong-facing resource", "face");
            Call(game, "SelectTarget", "", "");
            var automatic = Call(game, "ContextTarget") is WorldTarget chosen ? (WorldTarget?)chosen : null;
            Check(automatic is null || automatic.Value.Kind != "node" || automatic.Value.Id != node.Id,
                "Automatic context excludes the wrong-facing tutorial resource");
            var distant = Wire.Copy(snapshot); distant.Self.Position = node.Position.Add(new Point(0, 3)); Reject(distant, "Distant selected resource", "adjacent");
            var diagonal = Wire.Copy(snapshot); diagonal.Self.Position = node.Position.Add(new Point(1, 1)); diagonal.Self.Facing = new(-1, -1);
            Reject(diagonal, "Diagonal resource contact", "adjacent");
            // Nonfinite numbers cannot cross the strict JSON wire. Exercise the
            // detached readiness guards without serializing invalid fixtures.
            var malformed = Wire.Copy(snapshot); malformed.Self.Facing = new(double.NaN, 0);
            Check(ClassicGatherRules.Problem(malformed.Self, node, data, malformed.Time).Contains("snapshot", StringComparison.Ordinal),
                "Malformed resource facing cannot advertise readiness");
            var invalidRecovery = Wire.Copy(snapshot); invalidRecovery.Nodes[0].ReadyAt = double.PositiveInfinity;
            Check(ClassicGatherRules.Problem(invalidRecovery.Self, invalidRecovery.Nodes[0], data, invalidRecovery.Time).Contains("snapshot", StringComparison.Ordinal),
                "Nonfinite resource recovery cannot advertise readiness");
            var unknown = Wire.Copy(snapshot); unknown.Nodes[0].Template = "classic_unknown_resource";
            Reject(unknown, "Unknown tutorial resource", "cannot be gathered");
            Check(ClassicGatherRules.Problem(snapshot.Self, node, normal, snapshot.Time).Contains("optional", StringComparison.Ordinal),
                "An ordinary catalog cannot make an optional resource ready");
            Show(snapshot);
            Check(Call(game, "InteractionProblem", target with { Position = target.Position.Add(new Point(1, 0)) }, false)
                is string moved && moved.Contains("no longer", StringComparison.Ordinal),
                "A stale resource coordinate is rejected against the latest accepted node");
            foreach (bool wrongZone in new[] { false, true })
            {
                var unavailable = Wire.Copy(snapshot);
                if (wrongZone) unavailable.Nodes[0].Zone = OpeningJourney.Home; else unavailable.Nodes.Clear();
                Show(unavailable); string before = State(game.Snapshot!.Self);
                Call(game, "PrimaryAction", true);
                Check(Field<string>(game, "lastNoticeText").Contains("no longer", StringComparison.Ordinal)
                    && !Field<bool>(game, "attackKeyHeld") && Field<string>(game, "classicGatherTarget") == ""
                    && Field<string>(game, "classicAttackTarget") == "" && !Field<bool>(game, "combatApproach")
                    && Field<List<Point>>(game, "route").Count == 0 && connection.LastSequence == 0,
                    (wrongZone ? "Another-region" : "Removed") + " resource selection cannot turn Space into an automatic attack");
                Check(State(game.Snapshot.Self) == before && !Field<bool>(game, "actionBusy"), "Unavailable resource action cannot change authoritative state");
            }

            // Recovery keeps the first start unconfirmed without sending a ready
            // socketless request. The busy variant models an in-flight receipt;
            // it does not fabricate an accepted gather or claim live latency QA.
            var waiting = Wire.Copy(snapshot); waiting.Nodes[0].ReadyAt = waiting.Time + 30; Show(waiting);
            string unchanged = State(game.Snapshot!.Self); Call(game, "PrimaryAction", false);
            Check(Field<string>(game, "classicGatherTarget") == node.Id && !Field<bool>(game, "classicGatherConfirmed")
                && connection.LastSequence == 0 && !Field<bool>(game, "actionBusy"), "A valid recovery-waiting tutorial resource can be explicitly armed without an intention");
            ReleaseSpace();
            Check(Field<string>(game, "classicGatherTarget") == node.Id && !Field<bool>(game, "classicGatherConfirmed"),
                "Space release preserves the tutorial's explicit start before the first accepted gather");
            Member("actionBusy").SetValue(game, true); ReleaseSpace();
            Check(Field<string>(game, "classicGatherTarget") == node.Id && !Field<bool>(game, "classicGatherConfirmed")
                && State(game.Snapshot.Self) == unchanged && connection.LastSequence == 0,
                "A modeled pending receipt cannot lose the toggle or fabricate confirmation, rewards or sequence");
            Call(game, "PrimaryAction", false);
            Check(Field<string>(game, "classicGatherTarget") == "" && !Field<bool>(game, "classicGatherConfirmed")
                && Field<bool>(game, "actionBusy"), "Action again cancels pending tutorial gathering while the real receipt remains outstanding");
            Member("actionBusy").SetValue(game, false);
            Show(waiting); Call(game, "PrimaryAction", false);
            var movedSnapshot = Wire.Copy(game.Snapshot!); movedSnapshot.Self.Position = movedSnapshot.Self.Position.Add(new Point(.2, 0));
            game.World.Accept(new TransportPacket { Snapshot = movedSnapshot, Loot = [] }); Call(game, "TickClassicGather");
            Check(Field<string>(game, "classicGatherTarget") == "" && connection.LastSequence == 0,
                "Accepted movement still cancels an unconfirmed tutorial start");
            Show(waiting); Call(game, "PrimaryAction", false);
            var turnedSnapshot = Wire.Copy(game.Snapshot!); turnedSnapshot.Self.Facing = new(1, 0);
            game.World.Accept(new TransportPacket { Snapshot = turnedSnapshot, Loot = [] }); ReleaseSpace();
            Check(Field<string>(game, "classicGatherTarget") == "" && !Field<bool>(game, "classicGatherConfirmed") && connection.LastSequence == 0,
                "Latest accepted invalid facing cannot preserve an unconfirmed tutorial toggle");
            Show(waiting); Call(game, "PrimaryAction", false);
            Connected(connection, false); game.Notification(checked((int)NotificationApplicationFocusOut));
            Check(Field<string>(game, "classicGatherTarget") == "" && !Field<bool>(game, "classicGatherConfirmed") && connection.LastSequence == 0,
                "Production focus loss still cancels an unconfirmed tutorial start without sending movement");
            FocusForSyntheticInput(game, connection, "Resource focus recovery");
            config.SetValue("controls", "classic_gather", false); Show(waiting);
            Member("classicGatherTarget").SetValue(game, node.Id); ReleaseSpace();
            Check(Field<string>(game, "classicGatherTarget") == "", "A disabled gathering-repeat preference retains its original pre-receipt release behavior");

            var ordinary = new RealmEngine(normal).CreateCharacter("ordinary-gather-fixture", "Ordinary Gather", "vanguard", new());
            var ordinaryZone = normal.Zone(ordinary.Zone);
            var ordinaryPosition = new Point[] { new(0, 1.5), new(1.5, 0), new(0, -1.5), new(-1.5, 0) }
                .Select(offset => ordinary.Position.Add(offset)).First(at => WorldMap.Fits(ordinaryZone, at)
                    && WorldMap.LineOfSight(ordinaryZone, ordinary.Position, at));
            var ordinaryNode = new WorldNode { Id = "ordinary-release-oak", Template = "oak_tree", Zone = ordinary.Zone,
                Position = ordinaryPosition };
            ordinary.Facing = new(0, -1);
            Check(ClassicGatherRules.Problem(ordinary, ordinaryNode, normal, 10) == "", "Ordinary resource reach and non-cardinal facing requirements are unchanged");
            config.SetValue("controls", "classic_target_attack", true); config.SetValue("controls", "classic_gather", true);
            Catalog(game, normal); game.World.Accept(new TransportPacket { Snapshot = new Snapshot { Self = ordinary, Time = 10, Nodes = [ordinaryNode] }, Loot = [] });
            Call(game, "SelectTarget", "node", ordinaryNode.Id); Member("classicGatherTarget").SetValue(game, ordinaryNode.Id);
            Member("classicGatherConfirmed").SetValue(game, false); ReleaseSpace();
            Check(Field<string>(game, "classicGatherTarget") == "" && connection.LastSequence == 0,
                "Ordinary gathering still cancels an unconfirmed start on Space release");
        }
        finally
        {
            Connected(connection, false); Member("actionBusy").SetValue(game, false); Call(game, "StopCombatInput");
            config.Clear(); Check(config.Parse(preferences) == Error.Ok && config.EncodeToText() == preferences,
                "Resource regressions restore in-memory preferences without saving them");
            Catalog(game, data); game.World.Accept(new TransportPacket { Snapshot = original, Loot = originalLoot });
            Call(game, "SelectTarget", originalKind, originalTarget); Call(game, "UpdateHud");
        }
    }
    private async Task CheckOffscreenSiteControls(GameRoot game, Catalog data, GameConnection connection)
    {
        var original = Wire.Copy(game.Snapshot!); var originalLoot = Wire.Copy(game.World.Loot);
        string originalKind = Field<string>(game, "selectedTargetKind"), originalTarget = Field<string>(game, "selectedTarget");
        string preferences = Field<ConfigFile>(game, "settings").EncodeToText();
        var window = GetWindow(); var size = window.Size; var scale = window.ContentScaleSize; var mode = window.Mode;
        float zoom = game.World.Zoom; var site = ClassicTutorialContent.Sites[0];
        var snapshot = Wire.Copy(original); snapshot.Self.Position = new(37.5, 29.5); snapshot.Self.Facing = new(0, 1);
        snapshot.Nodes.Clear(); snapshot.Creatures.Clear(); snapshot.Chests.Clear(); snapshot.Events.Clear();
        LootPile Competitor(Snapshot value) => new() { Id = "offscreen-site-competing-loot", Zone = value.Self.Zone,
            Position = value.Self.Position, Owner = value.Self.Id, Gold = 3, Expires = value.Time + LootPile.LifetimeSeconds };
        void Show(Catalog current, Snapshot value, string id)
        {
            Connected(connection, false); Catalog(game, current);
            game.World.Accept(new TransportPacket { Snapshot = Wire.Copy(value), Loot = [Competitor(value)] });
            Call(game, "SelectTarget", "classic_site", id); Call(game, "UpdateHud");
        }
        void Reject(Catalog current, Snapshot value, string id, string label)
        {
            Show(current, value, id); FocusForSyntheticInput(game, connection, label);
            Check(ClassicInteractionRules.TutorialSite(value.Self, current, id) is null && Call(game, "ContextTarget") is null,
                label + " cannot resolve a stale site or silently choose competing loot");
            string before = State(game.Snapshot!.Self);
            Call(game, "InteractWithContext");
            Check(connection.LastSequence == 0 && State(game.Snapshot.Self) == before && !Field<bool>(game, "actionBusy"),
                label + " cannot send a competing context intention");
            Field<List<Point>>(game, "route").Add(site.Position); game.World.Waypoint = site.Position;
            Member("pendingInteraction").SetValue(game, Target(site)); Call(game, "PrimaryAction", true);
            Check(Field<string>(game, "lastNoticeText").Contains("no longer", StringComparison.Ordinal)
                && Field<string>(game, "selectedTargetKind") == "" && Field<string>(game, "selectedTarget") == ""
                && !Field<bool>(game, "attackKeyHeld") && Field<string>(game, "classicAttackTarget") == ""
                && Field<string>(game, "classicGatherTarget") == "" && !Field<bool>(game, "combatApproach")
                && Field<List<Point>>(game, "route").Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null && game.World.Waypoint is null,
                label + " retires its selection and navigation before basic-attack fallthrough");
            Check(connection.LastSequence == 0 && State(game.Snapshot.Self) == before && !Field<bool>(game, "actionBusy")
                && Call(game, "ContextTarget") is WorldTarget { Kind: "loot", Id: "offscreen-site-competing-loot" },
                label + " preserves rewards and ordinary context priority after explicit recovery");
        }
        try
        {
            Connected(connection, false); window.Mode = Window.ModeEnum.Windowed;
            window.Size = new(916, 515); window.ContentScaleSize = new(916, 515); game.World.Zoom = 1;
            Show(data, snapshot, site.Id); await Frame(); await Frame();
            FocusForSyntheticInput(game, connection, "Offscreen deliberate site");
            Check(!game.World.Targets.Any(x => x.Kind == "classic_site" && x.Id == site.Id)
                && game.World.Targets.Any(x => x.Kind == "loot" && x.Id == "offscreen-site-competing-loot"),
                "Native camera culls the distant sign while competing loot remains available");
            Call(game, "SelectTarget", "", "");
            Check(Call(game, "ContextTarget") is WorldTarget { Kind: "loot", Id: "offscreen-site-competing-loot" },
                "Unselected ordinary context chooses the nearby competing loot");
            Call(game, "SelectTarget", "classic_site", site.Id); Call(game, "TickExperience", .11d);
            Check(Call(game, "ContextTarget") is WorldTarget { Kind: "classic_site" } selected
                && selected.Id == site.Id && selected.Position == site.Position && selected.Name == site.Name,
                "A deliberately selected offscreen sign resolves its current catalog identity independently of world targets");
            var button = Field<Button>(game, "interactionButton");
            Check(button.Disabled && button.Text.StartsWith("Read [") && button.TooltipText.Contains("adjacent", StringComparison.Ordinal),
                "Offscreen selected sign retains its blocked adjacency explanation");
            Check(Call(game, "InteractionProblem", Target(site), false) is string blocked && blocked.Contains("adjacent", StringComparison.Ordinal),
                "Offscreen sign action is blocked before any socketless activation");
            string before = State(game.Snapshot!.Self); Call(game, "PrimaryAction", true);
            Check(Field<string>(game, "selectedTarget") == site.Id && !Field<bool>(game, "attackKeyHeld")
                && Field<string>(game, "classicAttackTarget") == "" && Field<string>(game, "classicGatherTarget") == ""
                && Field<List<Point>>(game, "route").Count == 0 && connection.LastSequence == 0 && !Field<bool>(game, "actionBusy")
                && State(game.Snapshot.Self) == before,
                "Offscreen selected sign cannot redirect Action to loot, gathering, movement, attack or rewards");
            await Capture("tutorial-offscreen-selected-site", connection);
            FocusForSyntheticInput(game, connection, "Offscreen site capture recovery");
            var forged = Target(site) with { Position = snapshot.Self.Position };
            Check(Call(game, "InteractionProblem", forged, false) is string stale && stale.Contains("no longer", StringComparison.Ordinal),
                "Forged sign coordinates cannot advertise a ready offscreen site");
            Call(game, "Activate", forged);
            Check(connection.LastSequence == 0 && !Field<bool>(game, "actionBusy") && State(game.Snapshot.Self) == before,
                "Forged sign activation remains rejected without a context intention or rewards");
            var near = Wire.Copy(snapshot); near.Self.Position = site.Position.Add(new Point(0, 1)); near.Self.Facing = new(0, -1);
            var removed = Wire.Copy(data); removed.Zone(near.Self.Zone).Furnishings.RemoveAll(x => x.Id == site.Id);
            Reject(removed, near, site.Id, "Removed catalog site");
            var moved = Wire.Copy(data); moved.Zone(near.Self.Zone).Furnishings.First(x => x.Id == site.Id).X++;
            Reject(moved, near, site.Id, "Mismatched catalog site position");
            var wrongKind = Wire.Copy(data); wrongKind.Zone(near.Self.Zone).Furnishings.First(x => x.Id == site.Id).Kind = "classic_fountain";
            Reject(wrongKind, near, site.Id, "Mismatched catalog site kind");
            var wrongRise = Wire.Copy(data); wrongRise.Zone(near.Self.Zone).Furnishings.First(x => x.Id == site.Id).Rise = 25;
            Reject(wrongRise, near, site.Id, "Mismatched catalog site drawing anchor");
            Reject(data, near, "forged-tutorial-site", "Unknown selected site ID");
            var wrongZone = Wire.Copy(near); wrongZone.Self.Zone = OpeningJourney.Home; wrongZone.Self.Position = data.Zone(wrongZone.Self.Zone).Spawn;
            Reject(data, wrongZone, site.Id, "Site selected in another region");
            var noProgress = Wire.Copy(near); noProgress.Self.ClassicTutorial = null;
            Reject(data, noProgress, site.Id, "Site selected without accepted tutorial progress");
            Check(Field<ConfigFile>(game, "settings").EncodeToText() == preferences,
                "Offscreen and stale-site handling never rewrites ordinary player preferences");
        }
        finally
        {
            Connected(connection, false); Catalog(game, data); Call(game, "StopCombatInput");
            game.World.Accept(new TransportPacket { Snapshot = original, Loot = originalLoot });
            Call(game, "SelectTarget", originalKind, originalTarget); Call(game, "UpdateHud"); game.World.Zoom = zoom;
            window.Mode = mode; window.Size = size; window.ContentScaleSize = scale;
        }
    }
    public override async void _Ready()
    {
        GameRoot? game = null; GameConnection? connection = null;
        try
        {
            Check(ProjectSettings.GlobalizePath("user://").Contains("Kairnfall-Classic-QA", StringComparison.Ordinal), "Native preferences stay isolated");
            game = new GameRoot { LayoutMode = 1 }; AddChild(game); game.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
            game.SetProcess(false); await Frame();
            var normal = game.Data; var data = Wire.Copy(normal); ClassicTutorialContent.Enable(data);
            var realm = new RealmEngine(data); var player = realm.CreateCharacter("site-fixture", "Site Fixture", "vanguard", new());
            realm.Active.Add(player.Id); var site = ClassicTutorialContent.Sites[0]; var target = Target(site);
            CheckReadiness(normal, data, player); Catalog(game, data);
            Field<Control>(game, "frontend").Hide(); GetViewport().GuiReleaseFocus();
            // Only the UI input gate is marked connected. This connection has no
            // socket, session, account or server; every actionable call below is blocked or disconnected.
            connection = new GameConnection("http://127.0.0.1:1");
            typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, connection);
            player.Position = site.Position.Add(new Point(0, 1)); player.Facing = new Point(1, 0);
            Accept(game, realm.Snapshot(player.Id)); await Frame();
            TraceInputGate(game, "Accepted native sign before controlled focus transition");
            Check(game.World.Targets.Any(x => x.Kind == "classic_site" && x.Id == site.Id), "Accepted tutorial exposes visible site targets without renderer discovery");
            Check(game.World.Pick(game.World.WorldToScreen(site.Position)) is { Kind: "classic_site", Id: "classic_first_sign" }, "Solid sign can be deliberately selected in world space");
            var route = Field<List<Point>>(game, "route"); route.Add(site.Position); Member("pendingInteraction").SetValue(game, target);
            string before = State(game.Snapshot!.Self); string settings = Field<ConfigFile>(game, "settings").EncodeToText();
            Check(Call(game, "InteractionProblem", target, false) is string problem && problem.Contains("face"),
                "Sign click fixture is authoritatively blocked before any socketless activation");
            Call(game, "SelectTarget", "", "");
            Connected(connection, false); game.Notification(checked((int)NotificationApplicationFocusOut)); Connected(connection, true);
            Check(!Field<bool>(game, "applicationFocused") && route.Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null,
                "Production focus loss cancels the retained solid-site route and pending interaction");
            Check(Property<bool>(game, "Online") && !Property<bool>(game, "Typing")
                && !Field<Control>(game, "frontend").Visible && Field<PanelContainer?>(game, "gameWindow") is null
                && !Field<bool>(game, "closing") && Field<string>(game, "awaitingBinding") == "" && game.Snapshot.Self.Health > 0,
                "Application focus is the only disabled prerequisite in the ignored-click fixture");
            ClickWorld(game, site.Position, false, "Unfocused sign click");
            Check(Field<string>(game, "selectedTargetKind") == "" && Field<string>(game, "selectedTarget") == ""
                && route.Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null
                && Field<string>(game, "classicAttackTarget") == "" && !Field<bool>(game, "attackKeyHeld") && !Field<bool>(game, "combatApproach"),
                "A click while unfocused cannot select, arm, approach or restore a cancelled site route");
            Check(State(game.Snapshot.Self) == before && connection.LastSequence == 0
                && !Field<bool>(game, "actionBusy") && !Field<bool>(game, "movementBusy"),
                "Unfocused site click preserves rewards and transport sequence");
            FocusForSyntheticInput(game, connection, "Sign focus recovery");
            route.Add(site.Position); Member("pendingInteraction").SetValue(game, target);
            ClickWorld(game, site.Position, true, "Recovered sign click");
            Check(Field<string>(game, "selectedTargetKind") == "classic_site" && Field<string>(game, "selectedTarget") == site.Id,
                "Focus recovery accepts the blocked sign selection before ticking");
            Call(game, "TickExperience", .11d);
            Check(Field<string>(game, "selectedTargetKind") == "classic_site" && Field<string>(game, "selectedTarget") == site.Id, "Blocked deliberate click retains the selected site");
            Check(route.Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null, "Click clears a solid-endpoint route and repeated pending attempts");
            var button = Field<Button>(game, "interactionButton"); var hint = Field<Label>(game, "interactionHint");
            Check(button.Disabled && button.Text.StartsWith("Read [") && button.TooltipText.Contains("face") && hint.Text.Contains(site.Name), "Read action retains its actionable facing reason");
            Check(State(game.Snapshot.Self) == before && connection.LastSequence == 0 && !Field<bool>(game, "actionBusy"), "Blocked click never changes rewards or sends an intention");
            // A retained route from an older selection must be cancelled before
            // TickGridRoute could attempt even one movement request.
            route.Add(site.Position); Member("pendingInteraction").SetValue(game, target);
            Member("gridWasAllowed").SetValue(game, true); Member("lastInput").SetValue(game, Vector2.Zero);
            game._Process(0);
            Check(route.Count == 0 && Field<WorldTarget?>(game, "pendingInteraction") is null
                && Field<Point?>(game, "gridRouteTarget") is null && Field<string>(game, "lastNoticeText").Contains("face"),
                "Retained site route is cancelled before a grid step or transport error can replace its facing reason");
            Check(State(game.Snapshot.Self) == before && !Field<bool>(game, "movementBusy"), "Retained route cannot predict movement, facing or rewards");
            await Capture("tutorial-sign-facing-blocked", connection);

            FocusForSyntheticInput(game, connection, "Facing refresh after native capture");
            player.Facing = new Point(0, -1); Accept(game, realm.Snapshot(player.Id)); Call(game, "TickExperience", .11d);
            Check(!button.Disabled && button.Text.StartsWith("Read [") && button.TooltipText == "", "Latest accepted facing makes the context button ready");
            Call(game, "SelectTarget", "", "");
            Check(Call(game, "ContextTarget") is WorldTarget { Kind: "classic_site", Id: "classic_first_sign" }, "Facing-adjacent site participates in automatic contextual action");
            Call(game, "SelectTarget", "classic_site", site.Id);
            player.Facing = new Point(1, 0); Accept(game, realm.Snapshot(player.Id)); before = State(game.Snapshot!.Self);
            Call(game, "Activate", target); Call(game, "TickExperience", .11d);
            Check(button.Disabled && Field<string>(game, "lastNoticeText").Contains("face") && connection.LastSequence == 0,
                "Action preflight rechecks latest facing rather than a previously ready selection");
            Check(State(game.Snapshot.Self) == before, "Latest-snapshot rejection preserves authoritative state");

            player.Position = site.Position.Add(new Point(0, 4)); player.Facing = new Point(0, -1);
            Accept(game, realm.Snapshot(player.Id)); Call(game, "TickExperience", .11d);
            Check(button.Disabled && hint.Text.Contains("adjacent") && Call(game, "ContextTarget") is WorldTarget { Id: "classic_first_sign" }, "Distant deliberate selection retains approach instructions without auto walking");
            var fountain = ClassicTutorialContent.Sites.Single(x => x.Kind == "fountain");
            player.Position = fountain.Position.Add(new Point(0, 1)); player.Facing = new Point(0, -1);
            Accept(game, realm.Snapshot(player.Id)); Call(game, "SelectTarget", "classic_site", fountain.Id); Call(game, "TickExperience", .11d);
            Check(!button.Disabled && button.Text.StartsWith("Visit ["), "Fountain context describes a visit without promising healing");
            before = State(game.Snapshot!.Self); Connected(connection, false); Call(game, "Activate", Target(fountain));
            Check(State(game.Snapshot.Self) == before && connection.LastSequence == 0, "Disconnected activation cannot fabricate a fountain milestone, Food or healing");
            await Capture("tutorial-fountain-ready", connection);
            CheckTutorialResourceControls(game, normal, data, realm, player, connection);
            await CheckOffscreenSiteControls(game, data, connection);

            // Positive commands are exercised against the real Core authority,
            // separately from UI-only fixtures. They never touch a live server or database.
            double food = player.ClassicTutorial!.Food, health = player.Health;
            var command = new GameCommand { Kind = "classic_interact", Target = fountain.Id, Sequence = 1 };
            var accepted = realm.Execute(player.Id, command);
            Check(accepted.Ok && player.ClassicTutorial.Completed.Contains("fountain"), "Only the in-memory realm command records its legitimate milestone");
            long notice = player.ClassicTutorial.NoticeId; double xp = player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing);
            var replay = realm.Execute(player.Id, command);
            Check(replay.Ok && player.ClassicTutorial.NoticeId == notice && player.SkillXp.GetValueOrDefault(ClassicTutorialContent.Questing) == xp,
                "An authority receipt cannot replay the site's reward");
            Check(player.Health == health && player.ClassicTutorial.Food == food, "Fountain visit grants neither unobserved healing nor Food");

            player.ClassicTutorial = null; Accept(game, realm.Snapshot(player.Id));
            Check(!game.World.Targets.Any(x => x.Kind == "classic_site") && Call(game, "ContextTarget") is null, "Local progress removal retires a selected site");
            player.ClassicTutorial = new(); player.Zone = OpeningJourney.Home; player.Position = data.Zone(player.Zone).Spawn;
            Accept(game, realm.Snapshot(player.Id));
            Check(!game.World.Targets.Any(x => x.Kind == "classic_site"), "Leaving First Glade removes site targets");
            var ordinary = new RealmEngine(normal).CreateCharacter("ordinary-site-fixture", "Ordinary Fixture", "vanguard", new());
            Catalog(game, normal); Accept(game, new Snapshot { Self = ordinary, Time = 10 });
            Check(!game.World.Targets.Any(x => x.Kind == "classic_site"), "Normal world retains its existing target discovery");
            Check(Field<ConfigFile>(game, "settings").EncodeToText() == settings, "Site input does not persist or change player preferences");
            CheckNormalCreatureControls(game, normal, ordinary, connection);
            typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, null); await connection.DisposeAsync(); connection = null;
            await NativeTestLifetime.ReleaseSceneAsync(this, game); game = null;
            GD.Print($"CLASSIC_TUTORIAL_INTERACTION_CONTRACT: {checks} checks passed. Offline native and in-memory authority; live server, artwork and physical input approval unrun.");
            GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CLASSIC_TUTORIAL_INTERACTION_CONTRACT: " + error);
            if (game is not null && GodotObject.IsInstanceValid(game))
            {
                typeof(GameRoot).GetProperty(nameof(GameRoot.Connection))!.SetValue(game, null);
                await NativeTestLifetime.ReleaseSceneAsync(this, game);
            }
            if (connection is not null) { Connected(connection, false); await connection.DisposeAsync(); }
            GetTree().Quit(1);
        }
    }
}
