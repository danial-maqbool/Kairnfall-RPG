namespace Kairnfall.Core;

/// <summary>A movement intention. The server owns length, mana cost and cooldown.</summary>
public static class DashRules
{
    public const double Distance = 2.5;
    public const double ManaCost = 4;
    public const double Cooldown = .65;
    public static string Problem(Character player, double now)
    {
        if (player.Health <= 0) return "Respawn before dashing.";
        if (player.Statuses.Any(s => s.Until > now && s.Kind is "stun" or "root" or "silence"))
            return "You cannot dash while rooted, stunned or silenced.";
        if (player.Cooldowns.GetValueOrDefault("dash") > now) return "Dash is recovering.";
        if (player.Mana < ManaCost) return "Dash needs 4 mana. Wait for mana to recover.";
        return "";
    }
    public static Point Direction(Point input, Point facing)
    {
        if (!input.Finite || Math.Abs(input.X) > 1 || Math.Abs(input.Y) > 1)
            throw new RuleException("Invalid dash direction.");
        var direction = input.Distance(new Point(0, 0)) < .01 ? facing : input;
        if (!direction.Finite) throw new RuleException("Invalid dash direction.");
        double length = direction.Distance(new Point(0, 0));
        return length < .01 ? new Point(0, 1) : direction.Scale(1 / length);
    }
}

public sealed partial class RealmEngine
{
    private string Dash(Character player, GameCommand command)
    {
        string problem = DashRules.Problem(player, State.Time);
        Need(problem == "", problem);
        var direction = DashRules.Direction(new Point(command.X, command.Y), player.Facing);
        var zone = Data.Zone(player.Zone);
        var destination = WorldMap.Move(zone, player.Position, direction.Scale(DashRules.Distance));
        Need(destination.Distance(player.Position) >= .25, "The dash path is blocked.");
        Need(WorldMap.Fits(zone, destination), "The dash path is blocked.");
        Ready(player, "dash", DashRules.Cooldown);
        player.Mana -= DashRules.ManaCost;
        player.Facing = direction; player.Position = destination;
        player.Statuses.RemoveAll(s => s.Kind == "meditate");
        inputs.Remove(player.Id);
        return "";
    }
}
