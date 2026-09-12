namespace Kairnfall.Core;

/// <summary>Build private inspection data from authoritative state or a detached frozen realm view.</summary>
public static class SnapshotPackets
{
    public static TransportPacket Create(RealmEngine engine, string characterId) => CreateCore(engine, characterId, false);

    /// <summary>
    /// Builds a packet from a detached realm copy whose character accounts and receipts have
    /// already been redacted. The packet may safely reference that immutable copy directly,
    /// avoiding JSON deep-copy work for every visible object of every connected peer.
    /// </summary>
    public static TransportPacket CreateFrozen(RealmEngine engine, string characterId) => CreateCore(engine, characterId, true);

    private static TransportPacket CreateCore(RealmEngine engine, string characterId, bool frozen)
    {
        var player = engine.Player(characterId);
        if (frozen && (player.Account.Length != 0 || player.Receipts.Count != 0))
            throw new InvalidOperationException("Frozen snapshot state must be detached and redacted before packet construction.");
        var snapshot = frozen ? FrozenSnapshot(engine, player) : engine.Snapshot(characterId);
        var packet = new TransportPacket
        {
            Kind = "snapshot", Snapshot = snapshot, Loot = frozen ? FrozenVisibleLoot(engine, player) : engine.VisibleLoot(characterId),
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

    private static Snapshot FrozenSnapshot(RealmEngine engine, Character player)
    {
        double range=player.Statuses.Any(x=>x.Kind=="tracking"&&x.Until>engine.State.Time)?60:30;
        var snap=new Snapshot{Time=engine.State.Time,Revision=engine.State.Revision,Self=player};
        foreach(var id in engine.Active)
        {
            if(!engine.State.Characters.TryGetValue(id,out var other)||other.Id==player.Id||other.Zone!=player.Zone||other.Position.Distance(player.Position)>range) continue;
            if(other.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>engine.State.Time)&&other.Position.Distance(player.Position)>2&&!(player.Party!=""&&other.Party==player.Party)) continue;
            snap.Players.Add(new(){Id=other.Id,Name=other.Name,Class=other.Class,Appearance=other.Appearance,Position=other.Position,Facing=other.Facing,Health=other.Health,MaxHealth=CombatMath.Stats(other,engine.Data).Health,Level=Progression.PlayerLevel(other),Equipment=other.Equipment.ToDictionary(x=>x.Key,x=>Items.Owned(other,x.Value).Template)});
        }
        snap.Creatures=engine.State.Creatures.Values.Where(x=>x.Zone==player.Zone&&x.Position.Distance(player.Position)<=range).ToList();
        snap.Nodes=engine.State.Nodes.Values.Where(x=>x.Zone==player.Zone&&x.Position.Distance(player.Position)<=range).ToList();
        snap.Chests=engine.State.Chests.Values.Where(x=>x.Zone==player.Zone&&x.Position.Distance(player.Position)<=range&&ExplorationRewards.VisibleChest(player,x,engine.Data)).ToList();
        snap.Telegraphs=engine.State.Telegraphs.Where(x=>x.Zone==player.Zone&&x.Position.Distance(player.Position)<=range).ToList();
        snap.Events=engine.State.Events.ToList();
        snap.Trades=engine.State.Trades.Values.Where(x=>x.A.Character==player.Id||x.B.Character==player.Id).ToList();
        if(player.Party!="") snap.Party=engine.State.Parties.GetValueOrDefault(player.Party);
        if(player.Guild!="") snap.Guild=engine.State.Guilds.GetValueOrDefault(player.Guild);
        bool nearAuctioneer=engine.Data.Npcs.Any(x=>x.Zone==player.Zone&&x.Role=="auctioneer"&&x.Position.Distance(player.Position)<=3&&WorldMap.LineOfSight(engine.Data.Zone(player.Zone),player.Position,x.Position));
        if(nearAuctioneer) snap.Auctions=engine.State.Auctions.Values.OrderBy(x=>x.Expires).Take(200).ToList();
        foreach(var npc in engine.Data.Npcs.Where(x=>x.Zone==player.Zone&&x.Position.Distance(player.Position)<6))
            foreach(var item in npc.Stock) snap.ShopStock[npc.Id+"/"+item]=engine.State.ShopStock.GetValueOrDefault(npc.Id+"/"+item);
        return snap;
    }

    private static List<LootPile> FrozenVisibleLoot(RealmEngine engine, Character player) => engine.Loot.Values
        .Where(x=>double.IsFinite(x.Expires)&&x.Expires>engine.State.Time&&x.Zone==player.Zone&&x.Position.Distance(player.Position)<=30)
        .ToList();
}
