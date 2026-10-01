namespace Kairnfall.Core;

/// <summary>Optional server-owned tile steps. Existing positions are approached, never rounded in saves.</summary>
public static class GridMovementRules
{
    public const string Intent = "classic_grid", Cancel = "classic_stop", Step = "classic_step";
    public static Point Cardinal(Point direction)
        => !direction.Finite || direction.Distance(default) < .01 ? default
            : Math.Abs(direction.X) >= Math.Abs(direction.Y) ? new(Math.Sign(direction.X), 0) : new(0, Math.Sign(direction.Y));
    public static Point Next(Point position, Point direction)
    {
        var center = new Point(Math.Floor(position.X) + .5, Math.Floor(position.Y) + .5);
        return position.Distance(center) > .000001 ? center : center.Add(Cardinal(direction));
    }
}

internal sealed class GridMovementIntent
{
    public string Zone = "";
    public Point Direction;
    public double HeldUntil, StepUntil;
    public Point? Target;
}
