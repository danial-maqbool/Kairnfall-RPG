namespace Kairnfall.Core;

/// <summary>Removes objects owned by an expired event without matching adjacent event IDs.</summary>
public static class WorldEventLifecycle
{
    public static int Expire(RealmState state, double now)
    {
        if (!double.IsFinite(now)) throw new ArgumentOutOfRangeException(nameof(now));
        var expired = state.Events.Where(value => value.Ends <= now)
            .Select(value => value.Id).ToHashSet(StringComparer.Ordinal);
        foreach (var id in expired)
        {
            bool Owned(string candidate) => candidate == id
                || candidate.StartsWith(id + "/", StringComparison.Ordinal);
            foreach (var key in state.Nodes.Keys.Where(Owned).ToArray()) state.Nodes.Remove(key);
            foreach (var key in state.Chests.Keys.Where(Owned).ToArray()) state.Chests.Remove(key);
            foreach (var key in state.Creatures.Keys.Where(Owned).ToArray()) state.Creatures.Remove(key);
            state.Telegraphs.RemoveAll(value => Owned(value.Source));
        }
        state.Events.RemoveAll(value => expired.Contains(value.Id));
        return expired.Count;
    }
}
