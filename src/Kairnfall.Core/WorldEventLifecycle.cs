namespace Kairnfall.Core;

/// <summary>Exact event-owned cleanup plus expiry for staged events and historical saves.</summary>
public static class WorldEventLifecycle
{
    public static int CleanupOwned(RealmState state, string id)
    {
        bool Owned(string candidate) => candidate == id || candidate.StartsWith(id + "/", StringComparison.Ordinal);
        int removed = 0;
        foreach (var key in state.Nodes.Keys.Where(Owned).ToArray()) { state.Nodes.Remove(key); removed++; }
        foreach (var key in state.Chests.Keys.Where(Owned).ToArray()) { state.Chests.Remove(key); removed++; }
        foreach (var key in state.Creatures.Keys.Where(Owned).ToArray()) { state.Creatures.Remove(key); removed++; }
        removed += state.Telegraphs.RemoveAll(value => Owned(value.Source));
        return removed;
    }

    public static int Expire(RealmState state, double now)
    {
        if (!double.IsFinite(now)) throw new ArgumentOutOfRangeException(nameof(now));
        var expired = state.Events.Where(value => value.Ends <= now
                && (value.Status != "active" || value.StageEnds <= 0))
            .Select(value => value.Id).ToArray();
        foreach (var id in expired) CleanupOwned(state, id);
        state.Events.RemoveAll(value => expired.Contains(value.Id, StringComparer.Ordinal));
        return expired.Length;
    }
}
