namespace Kairnfall.Core;

/// <summary>Server-authoritative rules for changing maps by physically walking through authored exits.</summary>
public static class MapTransitionRules
{
    public const double BorderMargin = 4.75;
    public const double WalkTriggerRadius = 0.68;
    public const double BorderLaneRadius = 1.45;
    public const double ArrivalClearance = 1.35;

    public static bool IsBorderExit(ZoneDef zone, ExitDef exit)
        => BorderOutward(zone, exit).Distance(new Point(0, 0)) > 0.01;

    public static Point BorderOutward(ZoneDef zone, ExitDef exit)
    {
        var choices = new (double Distance, Point Direction)[]
        {
            (exit.Position.X - 1, new Point(-1, 0)),
            ((zone.Width - 1) - exit.Position.X, new Point(1, 0)),
            (exit.Position.Y - 1, new Point(0, -1)),
            ((zone.Height - 1) - exit.Position.Y, new Point(0, 1))
        };
        var nearest = choices.OrderBy(x => x.Distance).First();
        return nearest.Distance <= BorderMargin ? nearest.Direction : new Point(0, 0);
    }

    public static ExitDef? TriggeredExit(ZoneDef zone, Point before, Point after, Point direction)
    {
        double length = direction.Distance(new Point(0, 0));
        if (length <= 0.01) return null;
        var unit = direction.Scale(1 / length);
        return zone.Exits
            .Where(exit => Triggered(zone, exit, before, after, unit))
            .OrderBy(exit => exit.Position.Distance(after))
            .ThenBy(exit => exit.Id, StringComparer.Ordinal)
            .FirstOrDefault();
    }

    private static bool Triggered(ZoneDef zone, ExitDef exit, Point before, Point after, Point unit)
    {
        var outward = BorderOutward(zone, exit);
        if (outward.Distance(new Point(0, 0)) > 0.01)
        {
            if (Dot(unit, outward) < 0.30) return false;
            double lateral = Math.Abs(outward.X) > 0.5
                ? Math.Abs(after.Y - exit.Position.Y)
                : Math.Abs(after.X - exit.Position.X);
            if (lateral > BorderLaneRadius) return false;
            if (outward.X < -0.5) return after.X <= exit.Position.X + 0.35;
            if (outward.X > 0.5) return after.X >= exit.Position.X - 0.35;
            if (outward.Y < -0.5) return after.Y <= exit.Position.Y + 0.35;
            return after.Y >= exit.Position.Y - 0.35;
        }

        if (SegmentDistance(before, after, exit.Position) > WalkTriggerRadius
            && after.Distance(exit.Position) > WalkTriggerRadius) return false;

        // Interior/cave/settlement entrances have a front side. The authored zone
        // spawn represents the playable side of that threshold, so crossing traffic
        // cannot trigger a doorway simply by brushing across its tile.
        var forward = zone.Spawn.Direction(exit.Position);
        if (forward.Distance(new Point(0, 0)) > 0.01)
        {
            if (Dot(unit, forward) < 0.55) return false;
            var fromExit = new Point(before.X - exit.Position.X, before.Y - exit.Position.Y);
            if (Dot(fromExit, forward) > 0.15) return false;
        }
        var toward = before.Direction(exit.Position);
        return toward.Distance(new Point(0, 0)) > 0.01 && Dot(unit, toward) > 0.20;
    }

    public static Point ArrivalPoint(Catalog data, ZoneDef source, ExitDef exit)
    {
        var target = data.Zone(exit.Target);
        var anchor = exit.Arrival;
        // Follow the actual target-zone path inward. This works for borders, doors,
        // caves and stairwells and guarantees we do not arrive on the reciprocal trigger.
        foreach (var point in WorldMap.FindPath(target, anchor, target.Spawn, target.Width * target.Height * 2))
            if (point.Distance(anchor) >= ArrivalClearance && WorldMap.Fits(target, point)) return point;

        var direction = anchor.Direction(target.Spawn);
        if (direction.Distance(new Point(0, 0)) > 0.01)
        {
            foreach (double distance in new[] { 2.0, 1.5, 1.0 })
            {
                var candidate = anchor.Add(direction.Scale(distance));
                if (WorldMap.Fits(target, candidate)) return candidate;
            }
        }
        return WorldMap.FindFree(target, anchor);
    }

    public static string EntranceVisualKey(ZoneDef source, ExitDef exit, ZoneDef target)
    {
        if (exit.Kind == "door") return "entrance_door";
        if (exit.Kind == "gate") return "entrance_gate";
        if (exit.Kind == "portal") return "entrance_portal";
        if (exit.Kind == "lift") return "entrance_lift";
        if (exit.Kind == "tunnel") return source.Layer == "Surface" ? "entrance_cave" : "entrance_tunnel";
        if (exit.Kind == "stairs")
            return source.Layer == "Surface" && (target.Layer != "Surface" || target.Kind == "dungeon")
                ? "entrance_cave" : "entrance_stairs";
        if (exit.Kind == "road") return "entrance_road";
        return "entrance_stairs";
    }

    private static double Dot(Point a, Point b) => a.X * b.X + a.Y * b.Y;

    private static double SegmentDistance(Point a, Point b, Point p)
    {
        double dx = b.X - a.X, dy = b.Y - a.Y;
        double lengthSquared = dx * dx + dy * dy;
        if (lengthSquared <= 0.000001) return p.Distance(a);
        double t = Math.Clamp(((p.X - a.X) * dx + (p.Y - a.Y) * dy) / lengthSquared, 0, 1);
        return p.Distance(new Point(a.X + dx * t, a.Y + dy * t));
    }
}
