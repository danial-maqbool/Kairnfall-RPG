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
        packet.FriendInvitations = player.FriendInvites.Where(engine.State.Characters.ContainsKey).OrderBy(x=>x,StringComparer.Ordinal).ToList();
        packet.Lfg = engine.Active.Where(engine.State.Characters.ContainsKey).Select(engine.Player)
            .Where(x=>x.Id!=characterId&&x.LfgActivity!=""&&!player.Ignored.Contains(x.Id)&&!x.Ignored.Contains(characterId))
            .OrderBy(x=>x.LfgSince).ThenBy(x=>x.Name,StringComparer.OrdinalIgnoreCase)
            .Select(x=>new LfgListing
            {
                Character=x.Id,Name=x.Name,Class=x.Class,Activity=x.LfgActivity,Role=x.LfgRole,Zone=x.Zone,
                Level=Progression.PlayerLevel(x),Since=x.LfgSince,
                PartySize=x.Party!=""&&engine.State.Parties.TryGetValue(x.Party,out var party)?party.Members.Count:1
            }).ToList();
        var profileIds = player.Friends
            .Concat(player.RecentPlayers.Where(x=>x.Value>=engine.State.Time-SocialCooperationRules.RecentPlayerLifetime).Select(x=>x.Key))
            .Concat(snapshot.Party?.Members??[]).Concat(snapshot.Guild?.Members??[])
            .Concat(packet.FriendInvitations).Concat(packet.Lfg.Select(x=>x.Character))
            .Where(x=>x!=characterId).Distinct(StringComparer.Ordinal).Take(150).ToArray();
        foreach(string id in profileIds)
        {
            if(!engine.State.Characters.TryGetValue(id,out var member)||player.Ignored.Contains(id)) continue;
            string guild=member.Guild!=""&&engine.State.Guilds.TryGetValue(member.Guild,out var memberGuild)?memberGuild.Name:"";
            packet.SocialProfiles.Add(new(){Id=id,Name=member.Name,Class=member.Class,Zone=member.Zone,Guild=guild,Level=Progression.PlayerLevel(member),Online=engine.Active.Contains(id),Friend=player.Friends.Contains(id),LastSeen=player.RecentPlayers.GetValueOrDefault(id)});
        }
        var names = new HashSet<string> { characterId };
        foreach (var visible in snapshot.Players) names.Add(visible.Id);
        foreach (var group in new[] { snapshot.Party, snapshot.Guild })
            if (group is not null) foreach (string member in group.Members) names.Add(member);
        foreach (var invitation in packet.Invitations) names.Add(invitation.Leader);
        foreach (var id in packet.FriendInvitations) names.Add(id);
        foreach (var listing in packet.Lfg) names.Add(listing.Character);
        foreach (var profile in packet.SocialProfiles) names.Add(profile.Id);
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
