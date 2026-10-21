using Kairnfall.Core;

namespace Kairnfall.Client;

/// <summary>
/// Client intention ownership only. Cancellation completion is a send result, not
/// movement acceptance; positions and arrival come only from realm snapshots.
/// </summary>
internal sealed class GridNavigationState
{
    public static bool SendCancellationIsTimeout(CancellationToken mainLifetime, CancellationToken navigationLifetime)
        => !mainLifetime.IsCancellationRequested && !navigationLifetime.IsCancellationRequested;

    internal sealed class StepRequest(object owner, long generation, Snapshot snapshot, Point direction, double requestedAt, bool manual = false)
    {
        public object Owner { get; } = owner;
        public long Generation { get; } = generation;
        public string Character { get; } = snapshot.Self.Id;
        public string Zone { get; } = snapshot.Self.Zone;
        public double SnapshotTime { get; } = snapshot.Time;
        public Point Direction { get; } = GridMovementRules.Cardinal(direction);
        public Point Target { get; } = GridMovementRules.Next(snapshot.Self.Position, direction);
        // Manual intent may retain a server target across key release. Its local
        // Target is intention metadata only and never an accepted-arrival test.
        public bool Manual { get; } = manual;
        public double RequestedAt { get; set; } = requestedAt;
        public bool SendCompleted { get; set; }
        public bool Retired { get; set; }
        public bool Matches(Snapshot snapshot) => snapshot.Self.Id == Character && snapshot.Self.Zone == Zone;
    }

    public long Generation { get; private set; }
    public StepRequest? Step { get; private set; }
    public bool Cancelling { get; private set; }
    public bool Settling { get; private set; }
    public bool CancellationFailed { get; private set; }
    public bool BlocksMovement => Step is { Retired: true } || Cancelling || Settling || CancellationFailed;
    private StepRequest? settlingOwner;
    private double fenceTime, stationaryTime;
    private Point? stationaryPosition;

    public void RetireRoute(bool retireManual = true)
    {
        Generation++;
        if (Step is { } step && (!step.Manual || retireManual)) step.Retired = true;
    }

    public void ResetSession()
    {
        Generation++;
        Step = null; settlingOwner = null; stationaryPosition = null;
        Cancelling = Settling = CancellationFailed = false;
    }

    public StepRequest? BeginStep(object owner, Snapshot snapshot, Point direction, double now)
    {
        if (Step is not null || BlocksMovement || !snapshot.Self.Position.Finite
            || !double.IsFinite(snapshot.Time) || !double.IsFinite(now) || GridMovementRules.Cardinal(direction) == default) return null;
        return Step = new StepRequest(owner, Generation, snapshot, direction, now);
    }

    public StepRequest? BeginManualSend(object owner, Snapshot snapshot, Point direction, double now)
    {
        if (BlocksMovement || !snapshot.Self.Position.Finite || !double.IsFinite(snapshot.Time) || !double.IsFinite(now)) return null;
        if (Step is { Manual: true, Retired: false } retained)
        {
            if (!ReferenceEquals(retained.Owner, owner) || !retained.Matches(snapshot)) return null;
            // Include release/refresh sends in the same owner so cancellation
            // waits for the newest prior write through the ordered transport.
            retained.SendCompleted = false; return retained;
        }
        if (Step is not null || GridMovementRules.Cardinal(direction) == default) return null;
        return Step = new StepRequest(owner, Generation, snapshot, direction, now, manual: true);
    }

    // A failed send can have written bytes before failing. Keep its owned step
    // available for ordered cancellation; only a current route may receive its error.
    public bool CompleteStepSend(StepRequest request, bool failed, double now)
    {
        if (!ReferenceEquals(Step, request)) return false;
        request.SendCompleted = true; request.RequestedAt = now;
        return failed && !request.Retired && (request.Manual || request.Generation == Generation);
    }

    public StepRequest? BeginCancellation()
    {
        if (Step is not { Retired: true, SendCompleted: true } step || Cancelling || CancellationFailed) return null;
        Cancelling = true; return step;
    }

    public bool CompleteCancellation(StepRequest request, Snapshot? latest, bool failed)
    {
        if (!ReferenceEquals(Step, request) || !Cancelling) return false;
        Cancelling = false;
        if (failed) { CancellationFailed = true; return true; }
        Step = null; settlingOwner = request; Settling = true;
        fenceTime = latest is not null && request.Matches(latest) && double.IsFinite(latest.Time)
            ? latest.Time : double.NegativeInfinity;
        stationaryPosition = null; stationaryTime = fenceTime;
        return true;
    }

    public void ObserveAccepted(Snapshot snapshot)
    {
        if (!snapshot.Self.Position.Finite || !double.IsFinite(snapshot.Time)) return;
        if (Step is { Manual: false, Retired: false, SendCompleted: true } step && !Cancelling && step.Matches(snapshot)
            && snapshot.Time > step.SnapshotTime && snapshot.Self.Position.Distance(step.Target) <= .000001)
            Step = null;
        if (!Settling || settlingOwner is not { } owner || !owner.Matches(snapshot)
            || snapshot.Time <= fenceTime || snapshot.Time <= stationaryTime) return;
        // This is an observation fence, never a cancellation ACK. The caller
        // must still send Cancel before a replacement through the ordered transport.
        if (stationaryPosition is { } previous && previous.Distance(snapshot.Self.Position) <= .000001)
        {
            Settling = false; settlingOwner = null; stationaryPosition = null;
        }
        else
        {
            stationaryPosition = snapshot.Self.Position; stationaryTime = snapshot.Time;
        }
    }
}
