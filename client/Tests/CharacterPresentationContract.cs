using Godot;
using Kairnfall.Core;
using System.Reflection;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client.Tests;

/// <summary>Native draw and state-machine fixtures; not an account gameplay or artistic sign-off.</summary>
public partial class CharacterPresentationContract : Node
{
    private int checks;
    private void Check(bool value, string message)
    {
        if (!value) throw new InvalidOperationException(message);
        checks++; GD.Print("PASS CHARACTER NATIVE: " + message);
    }
    private async Task Frame() => await ToSignal(GetTree(), SceneTree.SignalName.ProcessFrame);
    private static (int State, int Direction, int Frame, Point Position) Pose(WorldView world, string id, Point at)
        => ((int, int, int, Point))typeof(WorldView).GetMethod("Pose", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(world, [id, at])!;
    private static Point SnapshotVelocity(WorldView world, string id)
    {
        var tracks = (System.Collections.IDictionary)typeof(WorldView).GetField("tracks", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        var track = tracks[id]!;
        return (Point)track.GetType().GetField("SnapshotVelocity")!.GetValue(track)!;
    }
    private void CheckAuthoritativeMotion(WorldView world, Snapshot initial)
    {
        world.ClearSession(); var sample = Wire.Copy(initial); sample.Time = 10;
        sample.Creatures = [new Creature { Id = "native-stop-resume-mob", Template = "field_rat", Zone = sample.Self.Zone,
            Position = sample.Self.Position.Add(new Point(1, 1)), Health = 20 }];
        string remoteId = sample.Players.First().Id, mobId = sample.Creatures[0].Id;
        string[] actors = [sample.Self.Id, remoteId, mobId];
        void MoveActors(Snapshot snapshot)
        {
            var step = new Point(.3, 0);
            snapshot.Self.Position = snapshot.Self.Position.Add(step);
            foreach (var player in snapshot.Players) player.Position = player.Position.Add(step);
            foreach (var creature in snapshot.Creatures) creature.Position = creature.Position.Add(step);
        }
        world.Accept(new TransportPacket { Snapshot = sample }); world.SetLocalMovementIntent(new Vector2(1, 0));
        sample = Wire.Copy(sample); sample.Time = 10.1; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        var velocity = SnapshotVelocity(world, sample.Self.Id);
        Check(velocity.X > 1 && Math.Abs(velocity.Y) < .001,
            "Coalesced snapshots estimate local velocity from authoritative sample time even without a renderer clock advance");
        sample = Wire.Copy(sample); sample.Time = 10.2; world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == velocity,
            "One unchanged authoritative sample preserves visual travel across an interstitial packet");
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == velocity,
            "A duplicate authoritative timestamp cannot count as a second unchanged movement sample");
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "Remote players and creatures also retain velocity through one interstitial sample and its duplicate");
        sample = Wire.Copy(sample); sample.Time = 10.3; world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id) == default(Point),
            "Two genuinely newer unchanged authoritative samples clear stale local velocity");
        Check(actors.All(id => SnapshotVelocity(world, id) == default(Point)),
            "The same two-sample stationary contract clears remote-player and creature estimates");
        sample = Wire.Copy(sample); sample.Time = 10.4; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(SnapshotVelocity(world, sample.Self.Id).X > 1, "A new authoritative position change restores the visual movement estimate");
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "The first resumed step uses the confirmed stationary baseline for every actor type");
        double unchangedRenderClock = world.Clock;
        for (int i = 5; i <= 15; i++)
        {
            sample = Wire.Copy(sample); sample.Time = 10 + i * .1;
            world.Accept(new TransportPacket { Snapshot = sample });
        }
        Check(world.Clock == unchangedRenderClock && actors.All(id => SnapshotVelocity(world, id) == default(Point)),
            "Coalesced authoritative snapshots can confirm a long stop without advancing the renderer clock");
        sample = Wire.Copy(sample); sample.Time = 11.6; MoveActors(sample);
        world.Accept(new TransportPacket { Snapshot = sample });
        Check(actors.All(id => SnapshotVelocity(world, id).X > 1),
            "Movement resumes on its first authoritative step after a long stop even with no render-clock advance");
        world.SetLocalMovementIntent(Vector2.Zero); world.SetLocalMovementIntent(new Vector2(1, 0));
        Check(SnapshotVelocity(world, sample.Self.Id) == default(Point),
            "A release and immediate tap cannot reuse the previous local velocity before a new authoritative sample");
        world.SetLocalMovementIntent(new Vector2(float.NaN, 1));
        var intent = (Vector2)typeof(WorldView).GetField("localMovementIntent", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        Check(intent == Vector2.Zero, "Malformed local intent resets to the definitive zero movement vector");
        world.SetLocalMovementIntent(new Vector2(3, 4));
        intent = (Vector2)typeof(WorldView).GetField("localMovementIntent", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
        Check(Math.Abs(intent.Length() - 1) < .000001, "Local presentation intent normalizes oversized input without changing server positions");
        world.ClearSession(); world.Accept(new TransportPacket { Snapshot = initial });
    }
    private async Task Capture(string name)
    {
        await Frame(); await Frame();
        if (DisplayServer.GetName() == "headless") throw new InvalidOperationException("This contract requires a native rendered viewport.");
        await ToSignal(RenderingServer.Singleton, RenderingServer.SignalName.FramePostDraw);
        string root = System.Environment.GetEnvironmentVariable("KAIRNFALL_SCREENSHOTS") ?? ProjectSettings.GlobalizePath("user://character-review");
        System.IO.Directory.CreateDirectory(root);
        using var image = GetViewport().GetTexture().GetImage();
        Check(image.SavePng(System.IO.Path.Combine(root, name + ".png")) == Error.Ok, "Saved native viewport " + name);
    }

    public override async void _Ready()
    {
        WorldView? world = null; CharacterMotionGallery? gallery = null;
        try
        {
            GetWindow().Size = new Vector2I(1920, 1080);
            GetWindow().ContentScaleSize = new Vector2I(1920, 1080);
            var assets = new PixelAssets(); var data = PixelAssets.LoadCatalog();
            var estimatedVelocity = MotionPresentationRules.EstimateVelocity(new Point(0, 0), new Point(.4, 0), .1, new Point(0, 0));
            Check(estimatedVelocity.X > 2 && estimatedVelocity.X < 4.1 && Math.Abs(estimatedVelocity.Y) < .001,
                "Snapshot velocity estimation smooths a 10 Hz authoritative movement sample");
            var led = MotionPresentationRules.VisualTarget(new Point(1, 1), new Point(6, 0), .09);
            Check(led.X > 1 && led.X <= 1 + MotionPresentationRules.MaxLeadTiles + .0001,
                "Visual extrapolation is positive and bounded by the presentation-only lead cap");
            double freshnessMidpoint = (MotionPresentationRules.SnapshotFreshSeconds + MotionPresentationRules.SnapshotStaleSeconds) / 2;
            Check(MotionPresentationRules.SnapshotFreshness(MotionPresentationRules.SnapshotFreshSeconds) == 1
                && MotionPresentationRules.SnapshotFreshness(freshnessMidpoint) is > 0 and < 1
                && MotionPresentationRules.SnapshotFreshness(MotionPresentationRules.SnapshotStaleSeconds + .01) == 0,
                "Snapshot extrapolation fades to zero after the configured short network stall window");
            var snapped2 = MotionPresentationRules.SnapWorldPixel(new Vector2(10.24f, 20.26f), 2);
            var snapped3 = MotionPresentationRules.SnapWorldPixel(new Vector2(10.24f, 20.26f), 3);
            Check(Math.Abs(snapped2.X * 2 - MathF.Round(snapped2.X * 2)) < .0001f
                && Math.Abs(snapped3.Y * 3 - MathF.Round(snapped3.Y * 3)) < .0001f,
                "Dynamic actor coordinates align to final screen pixels at 2x and 3x zoom");
            var realm = new RealmEngine(data);
            var self = realm.CreateCharacter("native-motion-a", "Native Motion", "vanguard", new());
            var other = realm.CreateCharacter("native-motion-b", "Native Observer", "vanguard", new());
            realm.Active.Add(self.Id); realm.Active.Add(other.Id); other.Position = self.Position.Add(new Point(1, 0));
            world = new WorldView { Assets = assets, Data = data, WeatherEnabled = false };
            AddChild(world); world.SetProcess(false); await Frame();
            var snapshot = realm.Snapshot(self.Id);
            foreach (var mob in snapshot.Creatures) mob.NextAttack = snapshot.Time + 5;
            world.Accept(new TransportPacket { Snapshot = snapshot });
            foreach (var mob in snapshot.Creatures)
                Check(Pose(world, mob.Id, mob.Position).State == 0, "Spawn cooldown does not invent an attack: " + mob.Id);
            CheckAuthoritativeMotion(world, snapshot);
            var remote = snapshot.Players.Single(p => p.Id == other.Id);
            snapshot.ActorCues.Add(new ActorPresentationCue { Actor = other.Id, Sequence = 1, State = 6, Started = snapshot.Time, Duration = .8, Facing = new(-1, 0) });
            world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State == 6, "Remote interaction enters the explicit gesture state");
            world._Process(.3);
            int before = Pose(world, other.Id, other.Position).Frame;
            world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).Frame == before && before > 0, "Repeated snapshots do not restart an action");
            remote.Facing = new(1, 0); world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).Direction == 1, "Action facing remains stable through recovery");
            await Capture("character-remote-interaction");
            remote.Health = 0; world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State == 5 && Pose(world, other.Id, other.Position).Frame == 0,
                "Remote death starts with collapse, not the last corpse frame");
            world._Process(.2);
            Check(Pose(world, other.Id, other.Position).Frame is > 0 and < 7, "Remote collapse advances through intermediate poses");
            world._Process(.6);
            Check(Pose(world, other.Id, other.Position).Frame == 7, "Remote corpse holds its final pose");
            await Capture("character-remote-corpse");
            remote.Health = remote.MaxHealth; snapshot.ActorCues.Clear(); world.Accept(new TransportPacket { Snapshot = snapshot });
            Check(Pose(world, other.Id, other.Position).State != 5, "Respawn clears the terminal corpse state");
            world._Process(.10);
            remote.Position = remote.Position.Add(new Point(.3, 0)); world.Accept(new TransportPacket { Snapshot = snapshot });
            world._Process(.05);
            var firstInterpolated = Pose(world, other.Id, other.Position);
            world._Process(.04);
            var secondInterpolated = Pose(world, other.Id, other.Position);
            Check(firstInterpolated.State is 1 or 8 && secondInterpolated.Position.X > firstInterpolated.Position.X,
                "Rendered travel advances continuously between authoritative snapshots");
            Check(secondInterpolated.Position.Distance(remote.Position) <= MotionPresentationRules.MaxLeadTiles + .02,
                "Rendered interpolation stays within the bounded visual lead around authoritative position");
            world.Animate(other.Id, 2, .6); world._Process(1.0 / 60);
            int locomotion = (int)typeof(WorldView).GetMethod("LocomotionFrame", BindingFlags.Instance | BindingFlags.NonPublic)!.Invoke(world, [other.Id])!;
            Check(locomotion >= 0 && Pose(world, other.Id, other.Position).State == 2, "Leg motion continues beneath an upper-body action");
            for (int i = 0; i < 120; i++) world._Process(1.0 / 60);
            Check(Pose(world, other.Id, other.Position).State == 0, "Stationary actors return to idle after stale visual velocity fades");
            snapshot.Players.Clear(); world.Accept(new TransportPacket { Snapshot = snapshot });
            var tracks = (System.Collections.IDictionary)typeof(WorldView).GetField("tracks", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
            Check(!tracks.Contains(other.Id), "Actors leaving visibility do not retain stale animation tracks");
            world.CombatImpact(self.Position); world.ClearSession();
            var bursts = (System.Collections.ICollection)typeof(WorldView).GetField("combatBursts", BindingFlags.Instance | BindingFlags.NonPublic)!.GetValue(world)!;
            Check(bursts.Count == 0 && world.Snapshot is null, "Logout clears actor and combat presentation state");
            world.QueueFree(); world = null; await Frame(); await Frame();
            gallery = new CharacterMotionGallery { Assets = assets, Data = data };
            AddChild(gallery); gallery.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect); await Frame();
            for (int state = 0; state <= 8; state++)
                for (int frame = 0; frame < 8; frame++)
                {
                    gallery.State = state; gallery.FrameNumber = frame; gallery.QueueRedraw();
                    await Capture($"character-state-{state}-frame-{frame}");
                }
            foreach (var item in data.Items.Where(i => i.Slot == "weapon" && i.Id.Contains("bow", StringComparison.OrdinalIgnoreCase)).Take(8))
            {
                var gear = new Dictionary<string, string> { ["weapon"] = item.Id };
                int pose = SpritePoseRules.WeaponPose(2, gear);
                Check(pose is 9 or 10, "Ranged weapons select their own articulated attack rig: " + item.Id);
                var frame = assets.Frame("people/body_0_0", pose, 2, 3);
                Check(frame is not null && frame.Region.Size == new Vector2(64, 64), "Ranged draw frame resolves a native-size atlas cell");
            }
            Check(assets.Missing.Count == 0, "All native action and equipment requests have an asset; no fallback was used");
            GD.Print($"CHARACTER_NATIVE_CONTRACT: {checks} checks passed; native frames, movement, remote actions, collapse, cleanup, and atlas routing.");
            gallery.QueueFree(); await Frame(); await Frame(); GetTree().Quit(0);
        }
        catch (Exception error)
        {
            GD.PushError("CHARACTER_NATIVE_FAILED: " + error);
            if (world is not null && GodotObject.IsInstanceValid(world)) world.QueueFree();
            if (gallery is not null && GodotObject.IsInstanceValid(gallery)) gallery.QueueFree();
            GetTree().Quit(1);
        }
    }
}

public partial class CharacterMotionGallery : Control
{
    public PixelAssets Assets { get; set; } = null!;
    public Catalog Data { get; set; } = null!;
    public int State { get; set; }
    public int FrameNumber { get; set; }
    public override void _Ready() { TextureFilter = TextureFilterEnum.Nearest; MouseFilter = MouseFilterEnum.Ignore; }
    public override void _Draw()
    {
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("171e2a"));
        var font = ThemeDB.FallbackFont;
        DrawString(font, new Vector2(40, 45), $"KAIRNFALL / NATIVE CHARACTER REVIEW / STATE {State} / FRAME {FrameNumber}", fontSize: 22, modulate: new Color("e8d7b0"));
        var classes = Data.Classes.ToArray();
        float cell = Math.Min(220, (Size.X - 80) / classes.Length);
        for (int i = 0; i < classes.Length; i++)
        {
            var cls = classes[i];
            DrawString(font, new Vector2(40 + i * cell, 90), cls.Name, fontSize: 18, modulate: new Color("e8d7b0"));
            var equipment = new Dictionary<string, string> { ["weapon"] = cls.Weapon, [Data.Item(cls.Armor).Slot] = cls.Armor };
            for (int direction = 0; direction < 4; direction++)
            {
                var feet = new Vector2(40 + i * cell + cell / 2, 245 + direction * 185);
                DrawSetTransform(feet.Round(), 0, new Vector2(2, 2));
                Assets.DrawPerson(this, new Appearance { Body = i % 2, Skin = i % 6, Hair = i % 6, HairColor = i % 8 }, equipment,
                    Vector2.Zero, State, direction, FrameNumber);
                DrawSetTransform(Vector2.Zero);
            }
        }
    }
}
