using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native control and real WorldView playback regressions, not a human playtest.</summary>
internal static class PresentationChecks
{
    public static async Task Run(Node host, GameRoot game, Action<bool, string> check)
    {
        async Task Frame() => await host.ToSignal(host.GetTree(), SceneTree.SignalName.ProcessFrame);
        foreach (int state in new[] { 2, 3, 4 })
            foreach (double duration in new[] { .2, .3, .6, 1.4 })
            {
                check(SpritePoseRules.ActionFrame(state, 0, duration) == 0, "Action starts at its first frame");
                check(SpritePoseRules.ActionFrame(state, duration * .51, duration) == 4, "Action midpoint follows its actual duration");
                check(SpritePoseRules.ActionFrame(state, duration * .99, duration) == 7, "Short and long actions both reach recovery frame 7");
                int previous = -1;
                for (int step = 0; step <= 16; step++)
                {
                    int frame = SpritePoseRules.ActionFrame(state, duration * step / 16, duration);
                    check(frame >= previous && frame is >= 0 and <= 7, "Action frames remain ordered and bounded");
                    previous = frame;
                }
            }
        check(SpritePoseRules.ActionFrame(4, double.NaN, .3) == 0, "Invalid elapsed time cannot address a texture outside its sheet");
        check(SpritePoseRules.ActionFrame(2, -.1, .6) == 0, "A future action does not play backwards");
        check(SpritePoseRules.ActionFrame(5, .7, 6) == 7, "A corpse completes collapse before its retention timer expires");
        check(SpritePoseRules.ActionFrame(5, 5, 6) == 7, "A corpse holds its collapsed frame");

        var world = game.World;
        const string id = "presentation-clock-fixture";
        Point position = game.Data.Zone("wayfarers_rest").Spawn;
        var track = typeof(WorldView).GetMethod("Track", BindingFlags.Instance | BindingFlags.NonPublic)!;
        var pose = typeof(WorldView).GetMethod("Pose", BindingFlags.Instance | BindingFlags.NonPublic)!;
        (int State, int Direction, int Frame, Point Position) ReadPose()
            => ((int, int, int, Point))pose.Invoke(world, new object[] { id, position })!;
        bool processing = world.IsProcessing(); world.SetProcess(false);
        try
        {
            track.Invoke(world, new object[] { id, position, new Point(1, 0), 100.0 });
            foreach (int state in new[] { 2, 3, 4 })
            {
                world.Animate(id, state, .3);
                world._Process(.285);
                var sample = ReadPose();
                check(sample.State == state && sample.Frame == 7, "WorldView plays the final recovery frame before a short action ends");
                check(sample.Position == position, "Action presentation does not move the authoritative position");
                world._Process(.03);
                check(ReadPose().State == 0, "WorldView leaves the action after its declared duration");
            }
            track.Invoke(world, new object[] { id, position, new Point(1, 0), 0.0 });
            world._Process(.7);
            check(ReadPose().State == 5 && ReadPose().Frame == 7, "The real corpse renderer uses a completed collapse pose");
            world._Process(1);
            check(ReadPose().Frame == 7, "Corpse retention does not restart animation");
        }
        finally { world.SetProcess(processing); }

        foreach (var size in new[] { new Vector2(60, 54), new Vector2(75, 68), new Vector2(90, 81), new Vector2(140, 54) })
        {
            var rect = AbilitySlot.IconBounds(size);
            check(rect.Size.X == rect.Size.Y && rect.Size.X > 0, "Hotbar icon retains its square silhouette at " + size);
            check(rect.Position.X >= 0 && rect.Position.Y >= 0 && rect.End.X <= size.X && rect.End.Y <= size.Y,
                "Hotbar icon stays inside its native click target at " + size);
        }
        check(AbilitySlot.IconBounds(Vector2.Zero).Size == Vector2.Zero, "An unlaid-out slot has no negative draw area");

        var toggle = game.FindChildren("ToggleObjectives", "Button", true, false).OfType<Button>().Single();
        var text = (Label)typeof(GameRoot).GetField("objectiveText", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
        bool initial = text.Visible;
        for (int i = 0; i < 2; i++)
        {
            var at = toggle.GetGlobalRect().GetCenter();
            using (var press = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left, ButtonMask = MouseButtonMask.Left, Pressed = true })
                host.GetViewport().PushInput(press, true);
            await Frame();
            using (var release = new InputEventMouseButton { Position = at, GlobalPosition = at, ButtonIndex = MouseButton.Left })
                host.GetViewport().PushInput(release, true);
            await Frame(); await Frame();
            check(text.Visible == (i == 0 ? !initial : initial), "Native objective toggle changes its content visibility");
            check(toggle.Text == (text.Visible ? "−" : "+"), "Objective toggle symbol follows its actual state");
        }

        // Task #9: exercise the real combat-readability integration without claiming subjective feel.
        var original = world.Snapshot;
        var realm = new RealmEngine(game.Data);
        var self = realm.CreateCharacter("combat-presentation", "Combat Presentation", "vanguard", new());
        self.Position = position; self.Zone = "wayfarers_rest"; self.Stamina = 100;
        self.Statuses.Add(new StatusEffect { Kind = "stun", Until = 30, Source = "fixture" });
        var eliteDef = game.Data.Mobs.First(x => x.Elite);
        var elite = new Creature
        {
            Id = "combat-readability-elite", Template = eliteDef.Id, Zone = self.Zone,
            Position = new Point(position.X + 1, position.Y), Home = position, Health = eliteDef.Health,
            Statuses = [new StatusEffect { Kind = "root", Until = 30, Source = self.Id }]
        };
        string allyId = "combat-readability-ally";
        var party = new SocialGroup { Id = "combat-readability-party", Leader = self.Id, Members = [self.Id, allyId] };
        self.Party = party.Id;
        var snap = new Snapshot
        {
            Self = self, Time = 20, Party = party, Creatures = [elite],
            Players = [new PublicPlayer { Id = allyId, Name = "Downed Ally", Position = new Point(position.X, position.Y + 1), Health = 0, MaxHealth = 100 }],
            Telegraphs = [new Telegraph { Id = "combat-cast", Source = elite.Id, Zone = self.Zone, Position = self.Position, Skill = "interruptible", Shape = "circle", Radius = 2, Resolves = 21.4 }]
        };
        world.Accept(new TransportPacket { Snapshot = snap });
        typeof(GameRoot).GetField("selectedTargetKind", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(game, "creature");
        typeof(GameRoot).GetField("selectedTarget", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(game, elite.Id);
        world.TargetId = elite.Id;
        typeof(GameRoot).GetMethod("UpdateMobControls", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, null);
        await Frame();
        var overlay = (CombatReadabilityOverlay)typeof(GameRoot).GetField("combatReadability", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
        check(overlay.VisibleTelegraphCount == 1, "Native combat overlay reads the authoritative enemy cast telegraph");
        check(overlay.VisibleStatusCount == 2, "Native combat overlay exposes self and target crowd-control state");
        check(overlay.RevivePromptVisible, "Native combat overlay exposes a nearby eligible party revive");
        var attack = (Button)typeof(GameRoot).GetField("basicAttackButton", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)!;
        self.Cooldowns["attack"] = 21.2;
        world.Accept(new TransportPacket { Snapshot = snap });
        typeof(GameRoot).GetMethod("UpdateMobControls", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, null);
        check(attack.Text.Contains("1.2s", StringComparison.Ordinal), "Basic attack control renders authoritative cooldown time");
        check(attack.TooltipText.Contains("tile reach", StringComparison.Ordinal), "Basic attack control exposes weapon reach");

        var interrupted = Wire.Copy(snap); interrupted.Time = 20.2; interrupted.Telegraphs.Clear(); interrupted.Creatures[0].Health -= 5;
        world.Accept(new TransportPacket { Snapshot = interrupted });
        typeof(GameRoot).GetMethod("UpdateMobControls", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, null);
        check(overlay.PrimaryCue == "INTERRUPTED", "Early disappearance of a live enemy cast produces explicit interrupt confirmation");

        var dead = Wire.Copy(interrupted); dead.Time = 20.3; dead.Creatures[0].Health = 0;
        world.Accept(new TransportPacket { Snapshot = dead });
        typeof(GameRoot).GetMethod("UpdateMobControls", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(game, null);
        check((string)typeof(GameRoot).GetField("selectedTarget", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)! == ""
            && (string)typeof(GameRoot).GetField("selectedTargetKind", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(game)! == ""
            && world.TargetId == "", "Dead combat targets are removed from every client selection surface");

        if (original is not null) world.Accept(new TransportPacket { Snapshot = original });
        typeof(GameRoot).GetField("selectedTarget", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(game, "");
        typeof(GameRoot).GetField("selectedTargetKind", BindingFlags.Instance | BindingFlags.NonPublic)!.SetValue(game, "");
        world.TargetId = "";
    }
}
