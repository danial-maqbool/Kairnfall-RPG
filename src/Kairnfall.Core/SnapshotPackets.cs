namespace Kairnfall.Core;

/// <summary>Build private inspection data while the realm host holds its state lock.</summary>
public static class SnapshotPackets
{
    public static TransportPacket Create(RealmEngine engine, string characterId)
    {
        var player = engine.Player(characterId);
        var snapshot = engine.Snapshot(characterId);
        var packet = new TransportPacket
        {
            Kind = "snapshot", Snapshot = snapshot, Loot = engine.VisibleLoot(characterId),
            Invitations = engine.State.Parties.Values.Where(x => x.Invites.Contains(characterId))
                .Select(x => new GroupInvitation { Id = x.Id, Name = x.Name, Leader = x.Leader })
                .Concat(engine.State.Guilds.Values.Where(x => x.Invites.Contains(characterId))
                .Select(x => new GroupInvitation { Id = x.Id, Name = x.Name, Leader = x.Leader, Guild = true })).ToList()
        };
        var names = new HashSet<string> { characterId };
        foreach (var visible in snapshot.Players) names.Add(visible.Id);
        foreach (var group in new[] { snapshot.Party, snapshot.Guild })
            if (group is not null) foreach (string member in group.Members) names.Add(member);
        foreach (var invitation in packet.Invitations) names.Add(invitation.Leader);
        foreach (var trade in snapshot.Trades)
        {
            // Never reveal another trade or an inventory item that was not offered.
            if (trade.A.Character != characterId && trade.B.Character != characterId) continue;
            foreach (var offer in new[] { trade.A, trade.B })
            {
                names.Add(offer.Character);
                var owner = engine.Player(offer.Character);
                foreach (var entry in offer.Items)
                {
                    var item = owner.Inventory.FirstOrDefault(x => x.Id == entry.Key);
                    if (item is null || entry.Value < 1 || entry.Value > item.Quantity) continue;
                    var copy = Wire.Copy(item); copy.Quantity = entry.Value;
                    packet.TradeItems.Add(new TradePreview { TradeId = trade.Id, Revision = trade.Revision, Owner = owner.Id, Item = copy });
                }
            }
        }
        foreach (string id in names)
            if (engine.State.Characters.TryGetValue(id, out var member)) packet.Names[id] = member.Name;
        return packet;
    }
}
