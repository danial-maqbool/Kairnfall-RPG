using Godot;
using Kairnfall.Core;
using Point = Kairnfall.Core.Point;

namespace Kairnfall.Client;

public partial class GameRoot
{
    private readonly GridNavigationState gridNavigation = new();
    // Presentation of the current route; the separately owned retired step must
    // be cancelled before this field can describe a replacement step.
    private Point? gridRouteTarget;
    private CancellationTokenSource? navigationLifetime = new();
    private object? navigationSend;
    private GameConnection? navigationConnection;
    private string navigationCharacter = "", navigationZone = "";

    private void ClearRoute() => ClearRouteOwnership(retireManual: true);
    private void ClearRouteForHeldMovement() => ClearRouteOwnership(retireManual: false);
    private void ClearRouteOwnership(bool retireManual)
    {
        route.Clear(); gridNavigation.RetireRoute(retireManual);
        gridRouteTarget = null;
        // Deliberately retain pendingInteraction: WalkTo(keepInteraction:true)
        // has just selected it, and an owned cancellation may defer activation.
    }

    private void RetireNavigationSession()
    {
        ClearRoute(); pendingInteraction = null; gridNavigation.ResetSession();
        navigationConnection = null; navigationCharacter = navigationZone = "";
        navigationSend = null; movementBusy = false; lastInput = Vector2.Zero; gridWasAllowed = false;
        navigationLifetime?.Cancel(); navigationLifetime?.Dispose();
        navigationLifetime = closing ? null : new CancellationTokenSource();
    }

    private void ObserveNavigationContext(GameConnection connection, Snapshot snapshot)
    {
        if (navigationConnection is not null && (!ReferenceEquals(navigationConnection, connection)
            || navigationCharacter != snapshot.Self.Id || navigationZone != snapshot.Self.Zone)) RetireNavigationSession();
        navigationConnection = connection; navigationCharacter = snapshot.Self.Id; navigationZone = snapshot.Self.Zone;
        bool wasSettling = gridNavigation.Settling;
        gridNavigation.ObserveAccepted(snapshot);
        if (wasSettling && !gridNavigation.Settling && route.Count > 0)
        {
            // A cancelled step may have advanced since the replacement click.
            // Replan its retained destination from the latest accepted stopped position.
            var destination = route[^1];
            var path = WorldMap.FindPath(Data.Zone(snapshot.Self.Zone), snapshot.Self.Position, destination, 16000);
            ClearRoute(); route.AddRange(path);
            if (route.Count == 0 && snapshot.Self.Position.Distance(destination) > .000001)
            { pendingInteraction = null; Notify("No nearby route was found. Choose another tile.", true); }
        }
        if (gridNavigation.Step is null && !gridNavigation.BlocksMovement) gridRouteTarget = null;
    }

    private object BeginNavigationSend()
    {
        var operation = new object(); navigationSend = operation; movementBusy = true; return operation;
    }
    private bool CurrentNavigationSend(object operation) => ReferenceEquals(navigationSend, operation) && !closing && IsInsideTree();
    private void EndNavigationSend(object operation)
    {
        if (!ReferenceEquals(navigationSend, operation)) return;
        navigationSend = null; movementBusy = false;
    }
    private CancellationTokenSource NavigationSendCancellation(CancellationToken navigationToken)
    {
        var cancel = CancellationTokenSource.CreateLinkedTokenSource(lifetime.Token, navigationToken);
        cancel.CancelAfter(TimeSpan.FromSeconds(10)); return cancel;
    }

    private bool ResolvePendingRouteInteraction(bool controls)
    {
        if (!controls || Snapshot is not { } snapshot || pendingInteraction is not { } interaction) return false;
        if (interaction.Kind != "classic_site" && (snapshot.Self.Position.Distance(interaction.Position) > 2.15
            || !WorldMap.LineOfSight(Data.Zone(snapshot.Self.Zone), snapshot.Self.Position, interaction.Position))) return false;
        // Resolve the action decision before any route step. A retired in-flight
        // step settles first; Activate rechecks readiness against that latest snapshot.
        ClearRoute(); TrySendGridCancellation();
        if (gridNavigation.BlocksMovement) return true;
        pendingInteraction = null; Activate(interaction); return true;
    }

    private Vector2 TickGridRoute()
    {
        if (Snapshot is not { } snapshot || route.Count == 0) return Vector2.Zero;
        // A retained manual intention has no accepted target address that this
        // click route can reuse. Fence it before deriving any replacement step.
        if (gridNavigation.Step is { Manual: true, Retired: false })
        { gridNavigation.RetireRoute(); gridRouteTarget = null; }
        TrySendGridCancellation();
        if (gridNavigation.BlocksMovement) return Vector2.Zero;
        var self = snapshot.Self;
        if (gridNavigation.Step is { } pending)
        {
            if (!pending.Matches(snapshot)) { RetireNavigationSession(); return Vector2.Zero; }
            if (pending.SendCompleted && Time.GetTicksMsec() / 1000.0 - pending.RequestedAt > 2.5)
            {
                ClearRoute(); pendingInteraction = null; TrySendGridCancellation();
                Notify("The route is blocked. Choose another tile.", true); return Vector2.Zero;
            }
            var direction = self.Position.Direction(pending.Target);
            return new Vector2((float)direction.X, (float)direction.Y);
        }
        // Only accepted arrival consumes a point; send completion never predicts it.
        while (route.Count > 0 && self.Position.Distance(route[0]) <= .000001) route.RemoveAt(0);
        if (route.Count == 0 || movementBusy || Connection is not { Connected: true } connection || closing) return Vector2.Zero;
        var next = GridMovementRules.Cardinal(self.Position.Direction(route[0]));
        var request = gridNavigation.BeginStep(connection, snapshot, next, Time.GetTicksMsec() / 1000.0);
        if (request is null) return Vector2.Zero;
        gridRouteTarget = request.Target;
        SendGridRouteStep(request);
        return new Vector2((float)next.X, (float)next.Y);
    }

    private async void SendGridRouteStep(GridNavigationState.StepRequest request)
    {
        if (request.Owner is not GameConnection connection || !ReferenceEquals(Connection, connection)
            || !connection.Connected || closing || navigationLifetime is null) return;
        var operation = BeginNavigationSend();
        var navigationToken = navigationLifetime.Token;
        using var cancel = NavigationSendCancellation(navigationToken);
        Exception? failure = null;
        try { await connection.GridStepAsync(request.Direction.X, request.Direction.Y, cancel.Token); }
        catch (OperationCanceledException error) when (GridNavigationState.SendCancellationIsTimeout(lifetime.Token, navigationToken))
        { failure = new TimeoutException("The movement request timed out. Reconnect before walking.", error); }
        catch (OperationCanceledException) { }
        catch (Exception error) { failure = error; }
        finally
        {
            if (CurrentNavigationSend(operation))
            {
                if (gridNavigation.CompleteStepSend(request, failure is not null, Time.GetTicksMsec() / 1000.0))
                { ClearRoute(); pendingInteraction = null; Notify(failure!.Message, true); }
                EndNavigationSend(operation); TrySendGridCancellation();
            }
        }
    }

    private void TrySendGridCancellation()
    {
        if (movementBusy || closing || navigationLifetime is null || Connection is not { Connected: true } connection
            || gridNavigation.Step is not { Retired: true } owned || !ReferenceEquals(owned.Owner, connection)) return;
        if (gridNavigation.BeginCancellation() is { } request) SendGridCancellation(request, connection);
    }

    private async void SendGridCancellation(GridNavigationState.StepRequest request, GameConnection connection)
    {
        var operation = BeginNavigationSend();
        var navigationToken = navigationLifetime!.Token;
        using var cancel = NavigationSendCancellation(navigationToken);
        Exception? failure = null;
        try { await connection.GridMoveAsync(0, 0, cancelStep: true, cancel: cancel.Token); }
        catch (OperationCanceledException error) when (GridNavigationState.SendCancellationIsTimeout(lifetime.Token, navigationToken))
        { failure = new TimeoutException("The route cancellation timed out.", error); }
        catch (OperationCanceledException) { }
        catch (Exception error) { failure = error; }
        finally
        {
            if (CurrentNavigationSend(operation))
            {
                bool current = gridNavigation.CompleteCancellation(request, Snapshot, failure is not null);
                EndNavigationSend(operation);
                if (current && failure is not null)
                { ClearRoute(); pendingInteraction = null; Notify("Could not stop the route. Reconnect before walking. " + failure.Message, true); }
            }
        }
    }
}
