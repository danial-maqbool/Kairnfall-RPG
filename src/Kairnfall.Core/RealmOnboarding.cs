namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    private string AcknowledgeGuidance(Character player, GameCommand command)
    {
        Need(command.Target == "" && command.Item == "" && command.Amount == 1 && command.X == 0 && command.Y == 0,
            "Guidance acknowledgements cannot carry gameplay parameters.");
        return NewPlayerJourney.Acknowledge(player, command.Arg);
    }

    // Only authoritative creation and quest/zone state influence this scheduling preference.
    // Client acknowledgements are irrelevant. This replaces one normal scheduled event:
    // no extra timer, capacity, reward, private instance, region, or requestable spawn API.
    private Character? NewPlayerEventCandidate() => Active.Where(State.Characters.ContainsKey).Select(Player)
        .Where(x => x.Health > 0 && x.Zone == "kingsmeadow" && State.Time - x.LastCombat > 10
            && x.Discoveries.Contains(NewPlayerJourney.EligibleKey)
            && x.CompletedQuests.Contains("main_01") && !x.CompletedQuests.Contains("main_03")
            && Progression.PlayerLevel(x) < 20 && x.PublicEventsCompleted == 0
            && !x.Discoveries.Contains(NewPlayerJourney.PublicScheduledKey)
            && !State.Events.Any(activity => activity.Zone == x.Zone && activity.Ends > State.Time))
        .OrderBy(x => x.Id, StringComparer.Ordinal).FirstOrDefault(x => NewPlayerEventPosition(x) is not null);

    private Point? NewPlayerEventPosition(Character player)
    {
        var zone = Data.Zone(player.Zone);
        var hostiles = State.Creatures.Values.Where(x => x.Zone == zone.Id && x.Health > 0 && x.Owner == "")
            .Where(x => Data.Mob(x.Template).Ai is not "passive" and not "fleeing").ToArray();
        foreach (var offset in new Point[] { new(8, 0), new(0, 8), new(-8, 0), new(0, -8), new(6, 6), new(-6, -6), new(0, 0) })
        {
            var point = player.Position.Add(offset);
            if (!WorldMap.Fits(zone, point)) continue;
            if (hostiles.Any(x => x.Position.Distance(point) < Math.Max(10, Data.Mob(x.Template).Aggro + 5))) continue;
            if (point.Distance(player.Position) > .1 && WorldMap.FindPath(zone, player.Position, point, 4096).Count == 0) continue;
            return point;
        }
        return null; // Never draw a newcomer into a hostile pack just to meet a tutorial step.
    }
}
