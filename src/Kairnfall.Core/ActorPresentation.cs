namespace Kairnfall.Core;

/// <summary>Ephemeral, server-authored presentation. Never grants or predicts gameplay results.</summary>
public sealed class ActorPresentationCue
{
    public string Actor { get; set; } = "";
    public long Sequence { get; set; }
    public int State { get; set; }
    public double Started { get; set; }
    public double Duration { get; set; }
    public Point Facing { get; set; }
    public string Npc { get; set; } = "";
}

/// <summary>Deterministic presentation clocks, independent of network and rendering frame rate.</summary>
public static class ActorMotion
{
    public const int Frames = 8;
    public const double StrideTiles = 1.7;
    public const double CorpseCollapseSeconds = .65;
    public static bool IsAction(int state) => state is 2 or 3 or 4 or 5 or 6 or 7 or 9 or 10;

    public static int ActionFrame(int state, double elapsed, double duration)
    {
        if (!IsAction(state) || !double.IsFinite(elapsed) || elapsed <= 0) return 0;
        double length = state == 5 ? CorpseCollapseSeconds : double.IsFinite(duration) && duration > 0
            ? duration : state == 4 ? .3 : .6;
        double t = Math.Clamp(elapsed / length, 0, 1);
        if (state is 2 or 9 or 10)
        {
            // Preserve anticipation, contact, follow-through and recovery at short durations.
            ReadOnlySpan<double> boundaries = [0, .10, .24, .38, .49, .62, .78, .92];
            for (int frame = Frames - 1; frame >= 0; frame--)
                if (t >= boundaries[frame]) return frame;
        }
        return Math.Min(Frames - 1, (int)(t * Frames));
    }

    public static double AdvanceWalk(double phase, double distance)
    {
        if (!double.IsFinite(phase) || !double.IsFinite(distance) || distance < 0 || distance > 6) return 0;
        return ((phase % Frames + Frames) % Frames + distance * Frames / StrideTiles) % Frames;
    }

    public static bool MayInterrupt(int current, int incoming, bool alive)
    {
        if (incoming is < 0 or > 10) return false;
        if (!alive) return incoming == 5;
        if (incoming == 5) return true;
        if (current == 5) return false;
        if (incoming == 4) return true;
        return current != 4;
    }

    public static bool CueIsCurrent(ActorPresentationCue cue, double realmTime)
        => cue is not null && cue.Sequence > 0 && cue.Actor is { Length: > 0 and <= 128 }
           && cue.State is 2 or 3 or 6 or 7 or 8
           && double.IsFinite(cue.Started) && double.IsFinite(cue.Duration)
           && double.IsFinite(realmTime) && cue.Facing.Finite
           && cue.Duration > 0 && cue.Duration <= 2
           && cue.Started <= realmTime + .05 && realmTime - cue.Started < cue.Duration;
}

public sealed partial class RealmEngine
{
    // Not in RealmState, not restored from saves and not client-writable. At most one cue per active actor.
    private readonly Dictionary<string, (string Zone, ActorPresentationCue Cue)> presentationCues = [];

    private void ObservePresentation(Character player, GameCommand command)
    {
        if (command.Kind == "respawn") { presentationCues.Remove(player.Id); return; }
        (int state, double duration) = command.Kind switch
        {
            "attack" => (2, .62),
            "cast" or "meditate" => (3, .85),
            "craft" or "gather" or "repair" or "salvage" or "reforge" or "plant" => (7, 1.0),
            "talk" or "buy" or "sell" or "chest" or "loot" or "consume" or "revive" => (6, .8),
            "dash" => (8, .3),
            _ => (-1, 0)
        };
        if (state < 0 || player.Health <= 0 || !Active.Contains(player.Id)) return;
        if (command.Kind == "attack") duration = Math.Clamp(player.Cooldowns.GetValueOrDefault("attack") - State.Time, .25, .95);
        if (command.Kind == "cast" && Data.Abilities.FirstOrDefault(a => a.Id == command.Item) is { } ability)
        {
            if (ability.Kind is "strike" or "interrupt" or "execute" or "charge") { state = 2; duration = .55; }
            else if (ability.Kind == "dash") { state = 8; duration = .3; }
        }
        Point facing = player.Facing;
        Point? target = null;
        string npcId = "";
        if (command.Kind is "talk" or "buy" or "sell")
        {
            var npc = Data.Npcs.FirstOrDefault(n => n.Id == command.Target && n.Zone == player.Zone);
            if (npc is not null) { target = npc.Position; npcId = npc.Id; }
        }
        else if (command.Kind is "attack" or "cast")
        {
            if (State.Creatures.TryGetValue(command.Target, out var creature) && creature.Zone == player.Zone) target = creature.Position;
            else if (State.Characters.TryGetValue(command.Target, out var other) && other.Zone == player.Zone) target = other.Position;
            else if (command.Kind == "cast" && new Point(command.X, command.Y).Finite) target = new(command.X, command.Y);
        }
        else if (State.Nodes.TryGetValue(command.Target, out var node) && node.Zone == player.Zone) target = node.Position;
        else if (State.Chests.TryGetValue(command.Target, out var chest) && chest.Zone == player.Zone) target = chest.Position;
        if (target is { } point && player.Position.Distance(point) > .001) facing = player.Position.Direction(point);
        presentationCues[player.Id] = (player.Zone, new ActorPresentationCue
        {
            Actor = player.Id, Sequence = command.Sequence, State = state, Started = State.Time,
            Duration = duration, Facing = facing, Npc = npcId
        });
    }

    private void AppendPresentation(Snapshot snapshot)
    {
        foreach (var id in presentationCues.Where(x => !Active.Contains(x.Key)
                     || !State.Characters.TryGetValue(x.Key, out var actor) || actor.Health <= 0 || actor.Zone != x.Value.Zone
                     || !ActorMotion.CueIsCurrent(x.Value.Cue, State.Time)).Select(x => x.Key).ToArray())
            presentationCues.Remove(id);
        var visible = snapshot.Players.Select(p => p.Id).ToHashSet(StringComparer.Ordinal);
        visible.Add(snapshot.Self.Id);
        foreach (var id in visible)
            if (presentationCues.TryGetValue(id, out var entry) && entry.Zone == snapshot.Self.Zone)
                snapshot.ActorCues.Add(Wire.Copy(entry.Cue));
    }
}
