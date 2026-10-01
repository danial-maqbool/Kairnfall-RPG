namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private readonly Dictionary<string, GridMovementIntent> gridInputs = [];

    private void SetGridMovement(Character player, Point direction, bool singleStep = false)
    {
        inputs.Remove(player.Id);
        if (!gridInputs.TryGetValue(player.Id, out var intent) || intent.Zone != player.Zone)
            gridInputs[player.Id] = intent = new() { Zone = player.Zone };
        intent.Direction = GridMovementRules.Cardinal(direction);
        intent.HeldUntil = singleStep || intent.Direction == default ? State.Time : State.Time + .35;
        // A released key completes at most its current step. Stun and packet loss cannot
        // leave an intention queued indefinitely. Speed remains the ordinary server speed.
        if (intent.Target is null && intent.Direction != default)
        {
            intent.Target = GridMovementRules.Next(player.Position, intent.Direction);
            intent.StepUntil = State.Time + 2;
        }
        if (intent.Target is null) gridInputs.Remove(player.Id);
    }

    private void TickGridMovement(Character player, ZoneDef zone, double speed, double dt)
    {
        if (!gridInputs.TryGetValue(player.Id, out var intent)) return;
        if (player.Health <= 0 || intent.Zone != player.Zone || !player.Position.Finite
            || intent.Target is { } stale && player.Position.Distance(stale) > 1.5)
        { gridInputs.Remove(player.Id); return; }
        if (intent.Target is null)
        {
            if (intent.HeldUntil <= State.Time || intent.Direction == default)
            { gridInputs.Remove(player.Id); return; }
            intent.Target = GridMovementRules.Next(player.Position, intent.Direction);
            intent.StepUntil = State.Time + 2;
        }
        if (State.Time > intent.StepUntil) { gridInputs.Remove(player.Id); return; }
        var target = intent.Target.Value;
        var before = player.Position;
        if (intent.Direction != default) player.Facing = intent.Direction;
        if (!WorldMap.Fits(zone, target) || !WorldMap.LineOfSight(zone, before, target))
        {
            // Border roads still use the existing server transition checks and level gates.
            if (speed > 0) TryWalkTransition(player, zone, before, intent.Direction);
            intent.Target = null; return;
        }
        if (speed <= 0) return;
        player.Statuses.RemoveAll(x => x.Kind == "meditate");
        double remaining = before.Distance(target);
        var direction = before.Direction(target);
        player.Position = WorldMap.Move(zone, before, direction.Scale(Math.Min(remaining, speed * dt)));
        if (player.Position.Distance(target) <= .000001)
        { player.Position = target; intent.Target = null; }
        else if (player.Position.Distance(before) <= .000001) intent.Target = null;
        if (player.Zone == "wayfarers_rest" && player.Position.Distance(Data.Zone(player.Zone).Spawn) >= 1.5)
            FirstHourExperience.Mark(player, "movement");
        TryWalkTransition(player, zone, before, intent.Direction == default ? player.Facing : intent.Direction);
    }
}
