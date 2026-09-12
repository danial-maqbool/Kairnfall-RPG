namespace Kairnfall.Core;

/// <summary>
/// Fail-closed validation for state that crosses a process restart. This deliberately
/// validates persistence invariants rather than subjective gameplay balance.
/// </summary>
public static class PersistenceIntegrity
{
    public static List<string> Validate(RealmEngine realm)
    {
        var state=realm.State; var data=realm.Data;
        var errors=Items.Validate(state,data);
        var zones=data.Zones.ToDictionary(x=>x.Id,StringComparer.Ordinal);
        var items=data.Items.ToDictionary(x=>x.Id,StringComparer.Ordinal);
        var identities=new HashSet<string>(StringComparer.Ordinal);

        void Error(string text)=>errors.Add(text);
        bool Finite(double value)=>double.IsFinite(value);
        bool ValidPoint(string zoneId,Point point)=>zones.TryGetValue(zoneId,out var zone)&&point.Finite&&WorldMap.Fits(zone,point);
        void ValidateStatus(StatusEffect effect,string where)
        {
            if(!Finite(effect.Until)||!Finite(effect.Power)) Error("Invalid persisted status timing or power: "+where);
        }
        void ValidateItem(Item item,string where)
        {
            if(string.IsNullOrWhiteSpace(item.Id)||!identities.Add(item.Id)) Error("Duplicated or empty persisted item identity: "+where);
            if(!items.TryGetValue(item.Template,out var definition)||item.Quantity<1||item.Quantity>definition.StackMax) Error("Invalid persisted item stack: "+where);
            foreach(var affix in item.Affixes) if(!Finite(affix.Value)) Error("Invalid persisted affix value: "+where);
            foreach(var rune in item.Runes)
                if(string.IsNullOrWhiteSpace(rune.Id)||!identities.Add(rune.Id)||!items.ContainsKey(rune.Template)) Error("Invalid or duplicated persisted rune: "+where);
        }
        void ValidateGroup(Dictionary<string,SocialGroup> groups,bool guild)
        {
            foreach(var pair in groups)
            {
                var group=pair.Value; string kind=guild?"guild":"party";
                if(pair.Key!=group.Id||string.IsNullOrWhiteSpace(group.Id)) Error("Invalid persisted "+kind+" identity.");
                if(!group.Members.Contains(group.Leader)||!state.Characters.ContainsKey(group.Leader)) Error("Invalid persisted "+kind+" leader.");
                foreach(var member in group.Members)
                {
                    if(!state.Characters.TryGetValue(member,out var character)) { Error("Unknown persisted "+kind+" member."); continue; }
                    if((guild?character.Guild:character.Party)!=group.Id) Error("Persisted "+kind+" membership pointer mismatch.");
                }
                if(group.ReadyMembers.Any(member=>!group.Members.Contains(member))) Error("Invalid persisted party ready member.");
                if(!Finite(group.ReadyCheckEnds)) Error("Invalid persisted party ready timer.");
                if(group.Experience<0||group.ProjectProgress<0||group.ProjectGoal<0||group.CompletedProjects<0) Error("Invalid persisted guild progression.");
            }
        }

        if(state.Schema!=1) Error("Unsupported persisted realm schema.");
        if(state.Revision<0||!Finite(state.Time)||state.Time<0||!Finite(state.NextRestock)) Error("Invalid persisted realm revision or clock.");

        foreach(var pair in state.Characters)
        {
            var player=pair.Value;
            if(pair.Key!=player.Id||string.IsNullOrWhiteSpace(player.Id)) Error("Invalid persisted character identity.");
            if(!ValidPoint(player.Zone,player.Position)) Error("Invalid persisted character position: "+player.Id);
            if(!Finite(player.Health)||!Finite(player.Mana)||!Finite(player.Stamina)||!Finite(player.ClassResource)||!Finite(player.OverallCreditRemainder)||!Finite(player.LastCombat)||!Finite(player.DeadUntil)||!Finite(player.LfgSince)) Error("Invalid persisted character statistics or timers: "+player.Id);
            if(player.Gold<0||player.Gold>Items.GoldCap||player.LastAction<0) Error("Invalid persisted character gold or action sequence: "+player.Id);
            if(player.Cooldowns.Values.Any(value=>!Finite(value))||player.CombatPracticeRemainders.Values.Any(value=>!Finite(value))||player.GeneralPracticeRemainders.Values.Any(value=>!Finite(value))||player.RecentPlayers.Values.Any(value=>!Finite(value))) Error("Invalid persisted character timed/remainder state: "+player.Id);
            foreach(var status in player.Statuses) ValidateStatus(status,"character "+player.Id);
            if(player.RecentLearningEncounter is { } encounter&&(!Finite(encounter.At)||encounter.EnemyLevel<0||!zones.ContainsKey(encounter.Zone))) Error("Invalid persisted learning encounter: "+player.Id);
            var receiptIds=new HashSet<string>(StringComparer.Ordinal);
            if(player.Receipts.Count>32) Error("Persisted replay ledger exceeds its bounded window: "+player.Id);
            foreach(var receipt in player.Receipts)
            {
                bool validId=Guid.TryParseExact(receipt.RequestId,"N",out _);
                if(!validId||!receiptIds.Add(receipt.RequestId)||receipt.Result.RequestId!=receipt.RequestId||receipt.Result.Sequence<0||receipt.Result.Sequence>player.LastAction) Error("Invalid persisted command receipt: "+player.Id);
            }
            foreach(var item in player.Inventory) ValidateItem(item,"inventory "+player.Id);
            foreach(var item in player.Bank) ValidateItem(item,"bank "+player.Id);
        }

        foreach(var pair in state.Creatures)
        {
            var creature=pair.Value;
            if(pair.Key!=creature.Id||string.IsNullOrWhiteSpace(creature.Id)) Error("Invalid persisted creature identity.");
            if(!ValidPoint(creature.Zone,creature.Position)||!ValidPoint(creature.Zone,creature.Home)) Error("Invalid persisted creature position: "+creature.Id);
            if(!Finite(creature.Health)||!Finite(creature.RespawnAt)||!Finite(creature.NextAttack)||creature.Generation<0||creature.Phase<0||creature.AttackStep<0) Error("Invalid persisted creature state: "+creature.Id);
            if(creature.Owner!=""&&!state.Characters.ContainsKey(creature.Owner)) Error("Persisted creature has an unknown owner: "+creature.Id);
            if(creature.Threat.Values.Any(value=>!Finite(value))) Error("Invalid persisted creature threat: "+creature.Id);
            foreach(var status in creature.Statuses) ValidateStatus(status,"creature "+creature.Id);
        }
        foreach(var player in state.Characters.Values.Where(x=>x.Pet!=""))
            if(!state.Creatures.TryGetValue(player.Pet,out var pet)||pet.Owner!=player.Id) Error("Persisted pet ownership mismatch: "+player.Id);

        foreach(var pair in state.Nodes)
        {
            var node=pair.Value;
            if(pair.Key!=node.Id||string.IsNullOrWhiteSpace(node.Id)||!ValidPoint(node.Zone,node.Position)||!Finite(node.ReadyAt)) Error("Invalid persisted world node: "+pair.Key);
            if(node.Owner!=""&&!state.Characters.ContainsKey(node.Owner)) Error("Persisted world node has an unknown owner: "+pair.Key);
        }
        foreach(var pair in state.Chests)
        {
            var chest=pair.Value;
            if(pair.Key!=chest.Id||string.IsNullOrWhiteSpace(chest.Id)||!ValidPoint(chest.Zone,chest.Position)||!Finite(chest.ReadyAt)) Error("Invalid persisted chest: "+pair.Key);
        }
        foreach(var pair in state.Auctions)
        {
            var auction=pair.Value;
            if(pair.Key!=auction.Id||string.IsNullOrWhiteSpace(auction.Id)||!state.Characters.ContainsKey(auction.Seller)||auction.Price<1||auction.Price>Items.GoldCap||!Finite(auction.Expires)) Error("Invalid persisted auction: "+pair.Key);
            ValidateItem(auction.Item,"auction "+pair.Key);
        }

        ValidateGroup(state.Parties,false); ValidateGroup(state.Guilds,true);
        foreach(var player in state.Characters.Values)
        {
            if(player.Party!=""&&(!state.Parties.TryGetValue(player.Party,out var party)||!party.Members.Contains(player.Id))) Error("Persisted character party pointer is orphaned: "+player.Id);
            if(player.Guild!=""&&(!state.Guilds.TryGetValue(player.Guild,out var guild)||!guild.Members.Contains(player.Id))) Error("Persisted character guild pointer is orphaned: "+player.Id);
        }
        foreach(var pair in state.Trades)
        {
            var trade=pair.Value;
            if(pair.Key!=trade.Id||string.IsNullOrWhiteSpace(trade.Id)||trade.A.Character==trade.B.Character||!state.Characters.ContainsKey(trade.A.Character)||!state.Characters.ContainsKey(trade.B.Character)||!Finite(trade.Expires)||trade.Revision<0||trade.A.Gold<0||trade.B.Gold<0) Error("Invalid persisted trade: "+pair.Key);
        }

        var eventIds=new HashSet<string>(StringComparer.Ordinal);
        foreach(var worldEvent in state.Events)
        {
            if(string.IsNullOrWhiteSpace(worldEvent.Id)||!eventIds.Add(worldEvent.Id)||!ValidPoint(worldEvent.Zone,worldEvent.Position)||!Finite(worldEvent.Ends)||!Finite(worldEvent.Started)||!Finite(worldEvent.StageStarted)||!Finite(worldEvent.StageEnds)||!Finite(worldEvent.Progress)||!Finite(worldEvent.Goal)||!Finite(worldEvent.EffectEnds)||!Finite(worldEvent.LastTick)||worldEvent.Contributions.Values.Any(value=>!Finite(value))) Error("Invalid persisted world event: "+worldEvent.Id);
        }
        var telegraphIds=new HashSet<string>(StringComparer.Ordinal);
        foreach(var telegraph in state.Telegraphs)
            if(string.IsNullOrWhiteSpace(telegraph.Id)||!telegraphIds.Add(telegraph.Id)||!ValidPoint(telegraph.Zone,telegraph.Position)||!telegraph.Direction.Finite||!Finite(telegraph.Radius)||!Finite(telegraph.Power)||!Finite(telegraph.Resolves)) Error("Invalid persisted telegraph: "+telegraph.Id);

        foreach(var pair in realm.Loot)
        {
            var pile=pair.Value;
            if(pair.Key!=pile.Id||string.IsNullOrWhiteSpace(pile.Id)||!ValidPoint(pile.Zone,pile.Position)||pile.Gold<0||pile.Gold>Items.GoldCap||!Finite(pile.PartyAt)||!Finite(pile.PublicAt)||!Finite(pile.Expires)) Error("Invalid persisted loot pile: "+pair.Key);
            if(pile.Owner!=""&&!state.Characters.ContainsKey(pile.Owner)) Error("Persisted loot has an unknown owner: "+pair.Key);
            foreach(var item in pile.Items) ValidateItem(item,"loot "+pair.Key);
        }

        return errors.Distinct(StringComparer.Ordinal).ToList();
    }

    public static void RequireValid(RealmEngine realm)
    {
        var errors=Validate(realm);
        if(errors.Count>0) throw new InvalidDataException(string.Join("\n",errors));
    }
}
