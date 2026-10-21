using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public static class MotionPresentationRules
{
    public const double SnapshotLeadSeconds = .20;
    public const double SnapshotFreshSeconds = .20;
    public const double SnapshotStaleSeconds = .30;
    public const double MaxLeadTiles = .45;
    public const double LocalIntentLeadSeconds = .12;
    public const double LocalIntentMaxLeadTiles = .45;
    public const double TeleportDistance = 6;

    public static Point EstimateVelocity(Point previousTarget, Point target, double sampleSeconds, Point previousVelocity)
    {
        if (!previousTarget.Finite || !target.Finite || !previousVelocity.Finite
            || !double.IsFinite(sampleSeconds) || sampleSeconds < .035 || sampleSeconds > .35)
            return new Point(0, 0);
        double shift = previousTarget.Distance(target);
        if (shift > 2) return new Point(0, 0);
        if (shift < .01) return previousVelocity.Scale(.20);
        var raw = new Point((target.X - previousTarget.X) / sampleSeconds, (target.Y - previousTarget.Y) / sampleSeconds);
        double speed = raw.Distance(new Point(0, 0));
        if (!raw.Finite || speed > 12) return new Point(0, 0);
        double alignment = previousVelocity.X * raw.X + previousVelocity.Y * raw.Y;
        if (previousVelocity.Distance(new Point(0, 0)) > .05 && alignment < 0) return raw;
        var blended = new Point(previousVelocity.X * .45 + raw.X * .55, previousVelocity.Y * .45 + raw.Y * .55);
        double blendedSpeed = blended.Distance(new Point(0, 0));
        return blendedSpeed <= 12 ? blended : blended.Scale(12 / blendedSpeed);
    }

    public static double SnapshotFreshness(double snapshotAge)
    {
        if (!double.IsFinite(snapshotAge) || snapshotAge < 0 || snapshotAge >= SnapshotStaleSeconds) return 0;
        if (snapshotAge <= SnapshotFreshSeconds) return 1;
        return (SnapshotStaleSeconds - snapshotAge) / (SnapshotStaleSeconds - SnapshotFreshSeconds);
    }

    public static Point VisualTarget(Point authoritative, Point velocity, double snapshotAge)
        => VisualTarget(authoritative, velocity, snapshotAge, snapshotAge);

    public static Point VisualTarget(Point authoritative, Point velocity, double snapshotAge,
        double motionSampleAge, Point? localIntent = null)
    {
        if (!authoritative.Finite || !velocity.Finite || !double.IsFinite(snapshotAge)
            || !double.IsFinite(motionSampleAge)) return authoritative;
        double speed = velocity.Distance(new Point(0, 0));
        double freshness = SnapshotFreshness(snapshotAge);
        if (speed < .02 || speed > 12 || freshness <= 0) return authoritative;

        Point extrapolationVelocity = velocity;
        double seconds = Math.Clamp(snapshotAge, 0, SnapshotLeadSeconds);
        double leadCap = MaxLeadTiles;
        if (localIntent is { } intent)
        {
            double intentLength = intent.Distance(new Point(0, 0));
            // Input affects presentation only; the server remains the sole position authority.
            if (intentLength <= .05) return authoritative;
            extrapolationVelocity = intent.Scale(speed / intentLength);
            // An unchanged interstitial packet does not reset LastTargetAt, so it cannot
            // collapse the bounded extrapolation phase back to the authoritative sample.
            seconds = Math.Clamp(motionSampleAge, 0, LocalIntentLeadSeconds);
            leadCap = LocalIntentMaxLeadTiles;
        }

        double lead = Math.Min(leadCap, speed * seconds) * freshness;
        return authoritative.Add(extrapolationVelocity.Scale(lead / speed));
    }

    public static double SmoothingWeight(double delta)
        => !double.IsFinite(delta) || delta <= 0 ? 0 : 1 - Math.Exp(-18 * Math.Min(delta, .1));

    public static Vector2 SnapWorldPixel(Vector2 worldPixels, float zoom)
    {
        zoom = Math.Clamp(zoom, 1, 3);
        return (worldPixels * zoom).Round() / zoom;
    }
}

public partial class WorldView
{
    private readonly Dictionary<string, NpcGesture> npcGestures = [];
    private sealed record NpcGesture(int Direction, double Started, double Until);

    private static double IdleOffset(string id)
    {
        uint hash = 2166136261;
        foreach (char letter in id) hash = unchecked((hash ^ letter) * 16777619);
        return (hash % 8000) / 1000.0;
    }

    private void AdvanceTrack(ActorTrack track, double delta)
    {
        if (!double.IsFinite(delta) || delta <= 0) return;
        var previous = track.Position;
        double authoritativeRemaining = previous.Distance(track.Target);
        if (authoritativeRemaining > MotionPresentationRules.TeleportDistance)
        {
            track.Position = track.Target; track.SnapshotVelocity = new Point(0, 0);
            track.WalkPhase = 0; track.RenderSpeed = 0; track.Moving = false;
            return;
        }

        double snapshotAge = Math.Max(0, Clock - track.LastSnapshotAt);
        double motionSampleAge = Math.Max(0, Clock - track.LastTargetAt);
        double velocitySpeed = track.SnapshotVelocity.Distance(new Point(0, 0));
        Point? localIntent = track.Local ? new Point(localMovementIntent.X, localMovementIntent.Y) : null;
        double sourceSpeed = velocitySpeed * MotionPresentationRules.SnapshotFreshness(snapshotAge);
        if (track.Local && !LocalMovementExpected) sourceSpeed = 0;
        var visualTarget = MotionPresentationRules.VisualTarget(
            track.Target, track.SnapshotVelocity, snapshotAge, motionSampleAge, localIntent);
        double visualRemaining = previous.Distance(visualTarget);
        if (authoritativeRemaining < .006 && sourceSpeed < .06)
        {
            track.Position = track.Target; track.RenderSpeed = 0; track.Moving = false;
            return;
        }

        double weight = MotionPresentationRules.SmoothingWeight(delta);
        track.Position = visualRemaining < .003 ? visualTarget : new Point(
            previous.X + (visualTarget.X - previous.X) * weight,
            previous.Y + (visualTarget.Y - previous.Y) * weight);
        if (track.Local)
        {
            double authoritativeOffset = track.Position.Distance(track.Target);
            if (authoritativeOffset > MotionPresentationRules.LocalIntentMaxLeadTiles)
            {
                var correction = track.Target.Direction(track.Position);
                track.Position = track.Target.Add(correction.Scale(MotionPresentationRules.LocalIntentMaxLeadTiles));
            }
        }
        double travelled = previous.Distance(track.Position);
        double instantSpeed = travelled / delta;
        double speedWeight = 1 - Math.Exp(-12 * Math.Min(delta, .1));
        track.RenderSpeed += (instantSpeed - track.RenderSpeed) * speedWeight;
        bool keepMoving = track.RenderSpeed > .055 || visualRemaining > .012 || sourceSpeed > .08;
        bool startMoving = track.RenderSpeed > .12 && (visualRemaining > .012 || sourceSpeed > .12);
        track.Moving = track.Moving ? keepMoving : startMoving;
        if (track.Moving && travelled > .0001)
            track.WalkPhase = SpritePoseRules.AdvanceWalk(track.WalkPhase, travelled);
    }

    private int LocomotionFrame(string id)
        => tracks.TryGetValue(id, out var track) && track.Moving && track.Health > 0 ? (int)track.WalkPhase : -1;
    private bool Running(string id)
        => tracks.TryGetValue(id, out var track) && track.Player && track.Health > 0
           && (track.RenderSpeed > 6.2 || track.State == 8 && Clock < track.StateUntil);

    private void AcceptPresentation(Snapshot snapshot)
    {
        var visible = snapshot.Players.Select(p => p.Id).Concat(snapshot.Creatures.Select(c => c.Id)).ToHashSet(StringComparer.Ordinal);
        visible.Add(snapshot.Self.Id);
        foreach (var id in tracks.Keys.Where(id => !visible.Contains(id)).ToArray()) tracks.Remove(id);
        foreach (var id in npcGestures.Where(x => x.Value.Until <= Clock).Select(x => x.Key).ToArray()) npcGestures.Remove(id);
        if (snapshot.ActorCues is not { } cues) return;
        foreach (var cue in cues.Take(128))
        {
            if (cue is null || string.IsNullOrEmpty(cue.Actor)) continue;
            if (!tracks.TryGetValue(cue.Actor, out var track) || !track.Player || cue.Sequence <= track.CueSequence) continue;
            track.CueSequence = cue.Sequence;
            if (!ActorMotion.CueIsCurrent(cue, snapshot.Time) || track.Health <= 0) continue;
            int current = Clock < track.StateUntil ? track.State : 0;
            if (!ActorMotion.MayInterrupt(current, cue.State, true)) continue;
            double elapsed = Math.Max(0, snapshot.Time - cue.Started);
            track.State = cue.State;
            track.StateStart = Clock - elapsed;
            track.StateUntil = track.StateStart + cue.Duration;
            track.ActionDirection = SpritePoseRules.Direction(cue.Facing, track.FacingDirection);
            if (!string.IsNullOrEmpty(cue.Npc) && Data.Npcs.FirstOrDefault(n => n.Id == cue.Npc && n.Zone == snapshot.Self.Zone) is { } npc)
            {
                int facing = SpritePoseRules.Direction(npc.Position.Direction(track.Target), 0);
                npcGestures[npc.Id] = new NpcGesture(facing, track.StateStart, track.StateUntil);
            }
        }
    }

    private void DrawNpc(NpcDef npc, Vector2 feet)
    {
        if (npcGestures.TryGetValue(npc.Id, out var gesture) && gesture.Until > Clock)
        {
            int frame = SpritePoseRules.ActionFrame(6, Clock - gesture.Started, gesture.Until - gesture.Started);
            Assets.DrawFrame(this, "npcs/" + npc.Role, feet, 6, gesture.Direction, frame);
            return;
        }
        // A nearby person, not the camera, supplies the attention direction.
        int direction = 0;
        if (Snapshot is { } snapshot && snapshot.Self.Health > 0 && snapshot.Self.Position.Distance(npc.Position) <= 3)
            direction = SpritePoseRules.Direction(npc.Position.Direction(snapshot.Self.Position), 0);
        int idle = (int)(Clock * 5 + IdleOffset(npc.Id)) % PixelAssets.Frames;
        Assets.DrawFrame(this, "npcs/" + npc.Role, feet, 0, direction, idle);
    }
}
