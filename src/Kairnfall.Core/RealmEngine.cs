using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace Kairnfall.Core;

public sealed partial class RealmEngine
{
    public Catalog Data { get; }
    public RealmState State { get; set; }
    public Dictionary<string,LootPile> Loot { get; set; } = [];
    public HashSet<string> Active { get; } = [];
    public List<ChatMessage> OutgoingChat { get; } = [];
    public bool EconomicDirty { get; private set; }
    private readonly Dictionary<string,(Point Direction,double Until)> inputs=[];
    private readonly Dictionary<string,string> playerTargets=[];
    private readonly Dictionary<string,double> transitionReady=[];
    private double aiElapsed;
    private double environmentElapsed;
    private long lastEventCycle=-1;
    public RealmEngine(Catalog data,RealmState? state=null)
    {
        Data=data; State=state??new();
        if(State.Schema!=1) throw new InvalidDataException("Unsupported realm schema.");
        if(state is not null) RecoverLegacyRoadPositions();
        SeedWorld();
        if(state is not null) lastEventCycle=(long)(State.Time/WorldEventRules.SpawnCadence);
    }
    private void RecoverLegacyRoadPositions()
    {
        var repairs=new List<Action>();
        void Plan(string zoneId,Point position,Action<Point> apply,bool character=false)
        {
            var zone=Data.Zones.FirstOrDefault(z=>z.Id==zoneId);
            if(zone is null)
            {
                if(character) throw new InvalidDataException("Saved character has an unknown region.");
                return;
            }
            bool inBounds=position.Finite&&position.X>=1&&position.Y>=1&&position.X<zone.Width-1&&position.Y<zone.Height-1;
            if(inBounds&&WorldMap.Fits(zone,position)) return;
            if(!WorldMap.TryRecoverLegacyRoadPosition(zone,position,out var recovered))
            {
                if(character) throw new InvalidDataException("Saved world position is invalid outside the legacy road geometry repair.");
                // Do not broaden historical validation policy for unrelated world data.
                return;
            }
            repairs.Add(()=>apply(recovered));
        }
        foreach(var player in State.Characters.Values) Plan(player.Zone,player.Position,p=>player.Position=p,true);
        foreach(var creature in State.Creatures.Values)
        {
            Plan(creature.Zone,creature.Position,p=>creature.Position=p);
            Plan(creature.Zone,creature.Home,p=>creature.Home=p);
        }
        foreach(var node in State.Nodes.Values) Plan(node.Zone,node.Position,p=>node.Position=p);
        foreach(var chest in State.Chests.Values) Plan(chest.Zone,chest.Position,p=>chest.Position=p);
        // A later corrupt record must not leave the caller's supplied state partly migrated.
        foreach(var repair in repairs) repair();
        if(repairs.Count>0) EconomicDirty=true;
    }
    public void MarkSaved()=>EconomicDirty=false;
    public void RecoverLegacyLootPositions()
    {
        // Loot is loaded separately by RealmHost after the realm-state constructor.
        foreach(var pile in Loot.Values)
        {
            var zone=Data.Zones.FirstOrDefault(z=>z.Id==pile.Zone);
            if(zone is not null && WorldMap.TryRecoverLegacyRoadPosition(zone,pile.Position,out var recovered))
            {
                pile.Position=recovered; EconomicDirty=true;
            }
        }
    }
    public Character Player(string id)=>State.Characters.GetValueOrDefault(id)??throw new RuleException("Character not found.");
    private void Need(bool condition,string message) { if(!condition) throw new RuleException(message); }
    private void Alive(Character p)=>Need(p.Health>0,"You must respawn first.");
    private void Near(Character p,string zone,Point point,double range=2.5)
    {
        Need(p.Zone==zone&&p.Position.Distance(point)<=range,"Move closer to the target.");
        Need(WorldMap.LineOfSight(Data.Zone(p.Zone),p.Position,point),"The target is behind an obstacle.");
    }
    private void Ready(Character p,string action,double cooldown)
    {
        Need(p.Cooldowns.GetValueOrDefault(action)<=State.Time,"This action is on cooldown.");
        p.Cooldowns[action]=State.Time+cooldown;
    }
    private bool NearService(Character p,string role)=>Data.Npcs.Any(x=>x.Zone==p.Zone&&x.Role==role&&x.Position.Distance(p.Position)<=3&&WorldMap.LineOfSight(Data.Zone(p.Zone),p.Position,x.Position));
    private void Service(Character p,string role)=>Need(NearService(p,role),"Visit a "+role+" to use this service.");
    private bool AtStation(Character p,string station)
    {
        if(station=="hand") return true;
        var zone=Data.Zone(p.Zone);
        if(Data.Npcs.Any(x=>x.Zone==p.Zone&&x.Station==station&&x.Position.Distance(p.Position)<=3&&WorldMap.LineOfSight(zone,p.Position,x.Position))) return true;
        return State.Nodes.Values.Any(x=>x.Zone==p.Zone&&x.Owner==p.Id&&x.Position.Distance(p.Position)<=3&&x.Template=="structure_"+station&&WorldMap.LineOfSight(zone,p.Position,x.Position));
    }
    public Character CreateCharacter(string account,string name,string classId,Appearance appearance)
    {
        Need(Regex.IsMatch((name??"").Trim(),@"\A[A-Za-z][A-Za-z0-9_ ]{2,19}\z"),"Use 3–20 letters, digits, spaces, or underscores. Start with a letter.");
        name=name!.Trim();
        Need(!new[]{"admin","moderator","system","gamemaster"}.Contains(name.ToLowerInvariant()),"That name is reserved.");
        Need(State.Characters.Values.Count(x=>x.Account==account)<4,"This account already has four characters.");
        Need(!State.Characters.Values.Any(x=>string.Equals(x.Name,name,StringComparison.OrdinalIgnoreCase)),"That character name is taken.");
        var cls=Data.Class(classId);
        Need(appearance.Body is >=0 and <2&&appearance.Skin is >=0 and <6&&appearance.Hair is >=0 and <6&&appearance.HairColor is >=0 and <8,"Invalid appearance.");
        var p=new Character{Account=account,Name=name,Class=cls.Id,Appearance=appearance,Zone="wayfarers_rest",Position=Data.Zone("wayfarers_rest").Spawn};
        foreach(var skill in Data.Skills) p.SkillXp[skill.Id]=0;
        var weapon=Items.Create(Data,cls.Weapon); weapon.Sockets=1;
        Items.Add(p.Inventory,weapon,Data); p.Equipment["weapon"]=weapon.Id;
        var armor=Items.Create(Data,cls.Armor); Items.Add(p.Inventory,armor,Data); p.Equipment[Data.Item(cls.Armor).Slot]=armor.Id;
        foreach(var id in new[]{"copper_pickaxe","woodcutters_axe","field_rod","sickle","shovel","skinning_knife","crafting_hammer","lockpick"}) Items.Add(p.Inventory,Items.Create(Data,id),Data);
        Items.Add(p.Inventory,Items.Create(Data,"healing_potion",5),Data);
        Items.Add(p.Inventory,Items.Create(Data,"wheat_seed",3),Data);
        Items.Add(p.Inventory,Items.Create(Data,"rune_embers_1"),Data);
        var stats=CombatMath.Stats(p,Data); p.Health=stats.Health; p.Mana=stats.Mana; p.Stamina=stats.Stamina;
        p.Discoveries.Add(p.Zone); State.Characters.Add(p.Id,p); EconomicDirty=true;
        return p;
    }
    public CommandResult Execute(string character,GameCommand command)
    {
        Character p=Player(character);
        CommandResult Result(bool ok,string message)=>new(){Ok=ok,Message=message,RequestId=command.RequestId,Sequence=Player(character).LastAction};
        if(command.Version!=Wire.Version) return Result(false,"Client protocol version does not match the server.");
        if(!Guid.TryParseExact(command.RequestId,"N",out _)) return Result(false,"Invalid request identifier.");
        if(command.Kind is null||command.Target is null||command.Item is null||command.Arg is null) return Result(false,"Command fields cannot be null.");
        if(command.Target.Length>128||command.Item.Length>128||command.Arg.Length>512||command.Kind.Length>40) return Result(false,"Command field is too long.");
        if(!double.IsFinite(command.X)||!double.IsFinite(command.Y)) return Result(false,"Invalid coordinates.");
        if(command.Kind=="move")
        {
            if(p.Health<=0) return Result(false,"You must respawn first.");
            if(Math.Abs(command.X)>1||Math.Abs(command.Y)>1) return Result(false,"Invalid movement direction.");
            var dir=new Point(command.X,command.Y); double length=Math.Sqrt(dir.X*dir.X+dir.Y*dir.Y);
            if(length>1) dir=dir.Scale(1/length);
            inputs[p.Id]=(dir,State.Time+0.35);
            return Result(true,"");
        }
        var prior=p.Receipts.FirstOrDefault(x=>x.RequestId==command.RequestId);
        if(prior is not null) return prior.Result;
        if(command.Sequence!=p.LastAction+1) return Result(false,"Action sequence is stale. Synchronize before retrying.");
        if(command.Kind=="dash" && DashRules.Problem(p,State.Time) is { Length: > 0 } dashProblem) return Result(false,dashProblem);
        var backup=Wire.Copy(State); var lootBackup=Wire.Copy(Loot); int chatCount=OutgoingChat.Count;
        try
        {
            if(command.Kind!="respawn") Alive(p);
            string message=Dispatch(p,command);
            InvalidateTradeConsents();
            p.LastAction=command.Sequence;
            var result=Result(true,message);
            p.Receipts.Add(new(){RequestId=command.RequestId,Result=result});
            if(p.Receipts.Count>32) p.Receipts.RemoveAt(0);
            var errors=Items.Validate(State,Data);
            if(errors.Count>0) throw new InvalidOperationException(string.Join("; ",errors));
            EconomicDirty=true; return result;
        }
        catch(RuleException e)
        {
            State=backup; Loot=lootBackup;
            if(OutgoingChat.Count>chatCount) OutgoingChat.RemoveRange(chatCount,OutgoingChat.Count-chatCount);
            return Result(false,e.Message);
        }
        catch
        {
            State=backup; Loot=lootBackup;
            if(OutgoingChat.Count>chatCount) OutgoingChat.RemoveRange(chatCount,OutgoingChat.Count-chatCount);
            throw;
        }
    }
    private string Dispatch(Character p,GameCommand c)
    {
        switch(c.Kind)
        {
            case "dash": return Dash(p,c);
            case "equip": Items.Equip(p,c.Item,Data); Progress(p,"equip",Data.Item(Items.Owned(p,c.Item).Template).Type); return "Equipment changed.";
            case "unequip": Items.Unequip(p,c.Arg,Data); return "Item unequipped.";
            case "split": return SplitStack(p,c.Item,c.Amount);
            case "gather": return Gather(p,c.Target);
            case "attack": return Attack(p,c.Target);
            case "cast": return Cast(p,c.Item,c.Target,new(c.X,c.Y));
            case "loot": return CollectLoot(p,c.Target);
            case "chest": return OpenChest(p,c.Target);
            case "event": return EventAction(p,c.Target);
            case "buy": return Buy(p,c.Target,c.Item,c.Amount);
            case "sell": return Sell(p,c.Target,c.Item,c.Amount);
            case "deposit": Service(p,"banker"); Items.Add(p.Bank,Items.Take(p.Inventory,c.Item,c.Amount,p),Data,Items.BankCapacity); return "Deposited.";
            case "withdraw": Service(p,"banker"); Items.Add(p.Inventory,Items.Take(p.Bank,c.Item,c.Amount),Data); return "Withdrawn.";
            case "craft": return Craft(p,c.Item,c.Amount);
            case "salvage": return Salvage(p,c.Item);
            case "socket": Items.Socket(p,c.Target,c.Item,Data); Progression.Train(p,"runecrafting",30,Math.Max(1,Progression.Level(p,"runecrafting")),Data); Progress(p,"socket","*"); return "Rune inserted.";
            case "unsocket": return Unsocket(p,c.Target,c.Amount);
            case "repair": return Repair(p,c.Item);
            case "talk": return Talk(p,c.Target);
            case "inspect": return InspectLandmark(p,c.Target);
            case "accept_quest": return AcceptQuest(p,c.Item);
            case "claim_quest": return ClaimQuest(p,c.Item);
            case "transition": return Transition(p,c.Target);
            case "travel": return Travel(p,c.Target);
            case "consume": return Consume(p,c.Item);
            case "meditate": Need(p.Mana<CombatMath.Stats(p,Data).Mana-1,"Your mana is full."); Ready(p,"meditate",3); ApplyStatus(p.Statuses,"meditate",Element.Arcane,6,2,p.Id); return "Meditating. Movement or damage ends the channel.";
            case "rest": return Rest(p);
            case "respawn": return Respawn(p);
            case "auction_list": return AuctionList(p,c.Item,c.Amount,c.Target);
            case "auction_buy": return AuctionBuy(p,c.Target);
            case "auction_cancel": return AuctionCancel(p,c.Target);
            case "trade_invite": return TradeInvite(p,c.Target);
            case "trade_offer": return TradeChange(p,c.Target,c.Item,c.Amount,c.Arg);
            case "trade_ready": return TradeReady(p,c.Target,c.Amount,false);
            case "trade_confirm": return TradeReady(p,c.Target,c.Amount,true);
            case "trade_cancel": return TradeCancel(p,c.Target);
            case "party_create": return GroupCreate(p,false,c.Arg);
            case "guild_create": return GroupCreate(p,true,c.Arg);
            case "party_invite": return GroupInvite(p,false,c.Target);
            case "guild_invite": return GroupInvite(p,true,c.Target);
            case "party_join": return GroupJoin(p,false,c.Target);
            case "guild_join": return GroupJoin(p,true,c.Target);
            case "party_leave": return GroupLeave(p,false);
            case "guild_leave": return GroupLeave(p,true);
            case "party_kick": return GroupKick(p,false,c.Target);
            case "guild_kick": return GroupKick(p,true,c.Target);
            case "guild_message": return GuildMessage(p,c.Arg);
            case "guild_role": return GuildRole(p,c.Target,c.Arg);
            case "guild_project": return GuildProject(p,c.Target);
            case "party_ready_start": return PartyReadyStart(p);
            case "party_ready": return PartyReady(p);
            case "revive": return Revive(p,c.Target);
            case "lfg_set": return LfgSet(p,c.Target,c.Arg);
            case "lfg_request": return LfgRequest(p,c.Target);
            case "friend_invite": return FriendInvite(p,c.Target);
            case "friend_accept": return FriendAccept(p,c.Target);
            case "friend_remove": return FriendRemove(p,c.Target);
            case "chat": return Chat(p,c.Target,c.Item,c.Arg);
            case "ignore": Need(State.Characters.ContainsKey(c.Target),"Character not found."); if(!p.Ignored.Add(c.Target)) p.Ignored.Remove(c.Target); return "Ignore list updated.";
            case "plant": return Plant(p,new(c.X,c.Y));
            case "build": return Build(p,c.Item,new(c.X,c.Y));
            case "dismantle": return Dismantle(p,c.Target);
            case "tame": return Tame(p,c.Target);
            case "feed": return Feed(p,c.Item);
            case "pet_dismiss": return PetDismiss(p);
            case "prospect": return Prospect(p,c.Target);
            case "chart": return Chart(p);
            case "track": Ready(p,"track",30); Need(p.Stamina>=10,"Not enough stamina."); p.Stamina-=10; ApplyStatus(p.Statuses,"tracking",Element.Nature,30,1,p.Id); return "Nearby animal tracks are highlighted.";
            case "read": return Read(p,c.Item);
            default: throw new RuleException("Unknown command.");
        }
    }
    public void Tick(double dt)
    {
        if(!double.IsFinite(dt)||dt<=0||dt>0.1) throw new ArgumentOutOfRangeException(nameof(dt));
        State.Time+=dt;
        foreach(var id in Active.ToList())
        {
            if(!State.Characters.TryGetValue(id,out var p)||p.Health<=0) continue;
            var stats=CombatMath.Stats(p,Data); var zone=Data.Zone(p.Zone);
            if(inputs.TryGetValue(id,out var input)&&input.Until>=State.Time)
            {
                var direction=input.Direction;
                if(direction.Distance(new(0,0))>0.01)
                {
                    p.Statuses.RemoveAll(x=>x.Kind=="meditate");
                    double slow=Math.Clamp(1-CombatMath.StatusPower(p.Statuses,"chill",State.Time),0.25,1);
                    if(CombatMath.StatusPower(p.Statuses,"root",State.Time)>0||CombatMath.StatusPower(p.Statuses,"stun",State.Time)>0) slow=0;
                    var before=p.Position;
                    double eventMove=WorldEventRules.MovementMultiplier(State,p.Zone,State.Time);
                    p.Position=WorldMap.Move(zone,p.Position,direction.Scale(stats.MoveSpeed*slow*eventMove*dt)); p.Facing=direction;
                    if(slow>0) TryWalkTransition(p,zone,before,direction);
                    zone=Data.Zone(p.Zone);
                }
            }
            p.Stamina=Math.Min(stats.Stamina,p.Stamina+dt*(8+Progression.Level(p,"endurance")*0.08+WorldEventRules.StaminaRegenBonus(State,p.Zone,State.Time)));
            double manaRegen=2+Progression.Level(p,"meditation")*0.04+WorldEventRules.ManaRegenBonus(State,p.Zone,State.Time);
            if(p.Statuses.Any(x=>x.Kind=="meditate"&&x.Until>State.Time)) manaRegen*=4;
            p.Mana=Math.Min(stats.Mana,p.Mana+dt*manaRegen);
            if(State.Time-p.LastCombat>8) p.Health=Math.Min(stats.Health,p.Health+dt*(1.5+stats.Bonus("health_regen")+WorldEventRules.HealthRegenBonus(State,p.Zone,State.Time)));
            p.Health=Math.Min(p.Health,stats.Health); p.Mana=Math.Min(p.Mana,stats.Mana);
            ClassCombatRules.Tick(p,dt,State.Time);
            p.Statuses.RemoveAll(x=>x.Until<=State.Time);
            string chunk=$"{p.Zone}:{(int)p.Position.X/16}:{(int)p.Position.Y/16}";
            if(p.Discoveries.Add(chunk)) { Progression.Train(p,"exploration",10,Math.Clamp(zone.Level,1,100),Data); EconomicDirty=true; }
            if(p.Position.Distance(zone.Spawn)<=3&&zone.Kind is "city" or "settlement") p.Waypoints.Add(zone.Id);
            foreach(var chest in State.Chests.Values.Where(x=>x.Hidden&&x.Zone==p.Zone&&x.Position.Distance(p.Position)<2.2))
                if(p.Discoveries.Add("secret:"+chest.Id)) { Progression.Train(p,"treasure_hunting",30,chest.Requirement,Data); Progress(p,"discover",chest.Kind); EconomicDirty=true; }
        }
        aiElapsed+=dt;
        if(aiElapsed>=0.2) { TickCreatures(aiElapsed); aiElapsed=0; }
        environmentElapsed+=dt;
        if(environmentElapsed>=1) { TickEnvironment(environmentElapsed); TickSocialCooperation(); environmentElapsed=0; }
        ResolveTelegraphs();
        if(State.Time>=State.NextRestock) Restock();
        foreach(var a in State.Auctions.Values.Where(x=>x.Expires<=State.Time).ToList())
        {
            var seller=Player(a.Seller);
            try { Items.Add(seller.Bank,a.Item,Data,Items.BankCapacity); State.Auctions.Remove(a.Id); EconomicDirty=true; }
            catch(RuleException) { a.Expires=State.Time+60; }
        }
        foreach(var t in State.Trades.Values.Where(x=>x.Expires<=State.Time).ToList()) { State.Trades.Remove(t.Id); EconomicDirty=true; }
        foreach(var l in Loot.Values.Where(x=>!double.IsFinite(x.Expires)||x.Expires<=State.Time).ToList()) { Loot.Remove(l.Id); EconomicDirty=true; }
        TickEvents();
        InvalidateTradeConsents();
    }
    public Snapshot Snapshot(string player)
    {
        var p=Player(player); double range=p.Statuses.Any(x=>x.Kind=="tracking"&&x.Until>State.Time)?60:30;
        var self=Wire.Copy(p); self.Account=""; self.Receipts.Clear();
        var snap=new Snapshot{Time=State.Time,Revision=State.Revision,Self=self};
        foreach(var id in Active)
        {
            if(!State.Characters.TryGetValue(id,out var other)||other.Id==p.Id||other.Zone!=p.Zone||other.Position.Distance(p.Position)>range) continue;
            if(other.Statuses.Any(x=>x.Kind=="stealth"&&x.Until>State.Time)&&other.Position.Distance(p.Position)>2&&!(p.Party!=""&&other.Party==p.Party)) continue;
            snap.Players.Add(new(){Id=other.Id,Name=other.Name,Class=other.Class,Appearance=other.Appearance,Position=other.Position,Facing=other.Facing,Health=other.Health,MaxHealth=CombatMath.Stats(other,Data).Health,Level=Progression.PlayerLevel(other),Equipment=other.Equipment.ToDictionary(x=>x.Key,x=>Items.Owned(other,x.Value).Template)});
        }
        snap.Creatures=State.Creatures.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range).Select(Wire.Copy).ToList();
        snap.Nodes=State.Nodes.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range).Select(Wire.Copy).ToList();
        snap.Chests=State.Chests.Values.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range&&ExplorationRewards.VisibleChest(p,x,Data)).Select(Wire.Copy).ToList();
        snap.Telegraphs=State.Telegraphs.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<=range).Select(Wire.Copy).ToList();
        snap.Events=State.Events.Select(Wire.Copy).ToList();
        snap.Trades=State.Trades.Values.Where(x=>x.A.Character==p.Id||x.B.Character==p.Id).Select(Wire.Copy).ToList();
        if(p.Party!="") snap.Party=Wire.Copy(State.Parties.GetValueOrDefault(p.Party));
        if(p.Guild!="") snap.Guild=Wire.Copy(State.Guilds.GetValueOrDefault(p.Guild));
        if(NearService(p,"auctioneer")) snap.Auctions=State.Auctions.Values.OrderBy(x=>x.Expires).Take(200).Select(Wire.Copy).ToList();
        foreach(var npc in Data.Npcs.Where(x=>x.Zone==p.Zone&&x.Position.Distance(p.Position)<6))
            foreach(var item in npc.Stock) snap.ShopStock[npc.Id+"/"+item]=State.ShopStock.GetValueOrDefault(npc.Id+"/"+item);
        return snap;
    }
    public List<LootPile> VisibleLoot(string player)
    {
        var p=Player(player); return Loot.Values
            .Where(x=>double.IsFinite(x.Expires)&&x.Expires>State.Time&&x.Zone==p.Zone&&x.Position.Distance(p.Position)<=30)
            .Select(Wire.Copy).ToList();
    }
    public void Disconnect(string id)
    {
        Active.Remove(id); inputs.Remove(id); playerTargets.Remove(id); transitionReady.Remove(id);
        if(State.Characters.TryGetValue(id,out var player)) ClearLfg(player);
        foreach(var t in State.Trades.Values.Where(x=>x.A.Character==id||x.B.Character==id).ToList()) State.Trades.Remove(t.Id);
        EconomicDirty=true;
    }
    private void SeedWorld()
    {
        foreach(var zone in Data.Zones)
        {
            int n=0;
            foreach(var species in zone.Species)
            {
                string id=zone.Id+"/"+species; if(State.Creatures.ContainsKey(id)) { n++; continue; }
                var def=Data.Mob(species); double angle=n*2.399;
                var point=WorldMap.FindFree(zone,new(zone.Spawn.X+Math.Cos(angle)*(zone.Kind=="city"?30:15),zone.Spawn.Y+Math.Sin(angle)*(zone.Kind=="city"?30:15)));
                State.Creatures[id]=new(){Id=id,Template=species,Zone=zone.Id,Position=point,Home=point,Health=def.Health}; n++;
            }
            if(zone.Boss!="")
            {
                string id=zone.Id+"/boss";
                if(!State.Creatures.ContainsKey(id))
                {
                    var point=WorldMap.FindFree(zone,new(zone.Spawn.X+6,zone.Spawn.Y+3)); var def=Data.Mob(zone.Boss);
                    State.Creatures[id]=new(){Id=id,Template=def.Id,Zone=zone.Id,Position=point,Home=point,Health=def.Health};
                }
            }
            for(int i=0;i<zone.Resources.Length;i++) for(int j=0;j<3;j++)
            {
                string id=$"{zone.Id}/node/{i}/{j}"; if(State.Nodes.ContainsKey(id)) continue;
                var p=WorldMap.FindFree(zone,new(zone.Spawn.X-12+i*3,zone.Spawn.Y+7+j*4));
                State.Nodes[id]=new(){Id=id,Template=zone.Resources[i],Zone=zone.Id,Position=p};
            }
            for(int i=0;i<3;i++)
            {
                string id=$"{zone.Id}/chest/{i}"; if(State.Chests.ContainsKey(id)) continue;
                var p=WorldMap.FindFree(zone,new(zone.Spawn.X+10+i*6,zone.Spawn.Y-8-i*3));
                State.Chests[id]=new(){Id=id,Zone=zone.Id,Position=p,Kind=i==0?"weathered":i==1?"locked":zone.Layer=="Surface"?"runic":"ancient",Requirement=Math.Clamp(zone.Level,1,100),Hidden=i==2};
            }
        }
        SeedHuntingWorld();
        if(State.NextRestock==0) Restock();
    }
    private void Restock()
    {
        foreach(var npc in Data.Npcs) foreach(var item in npc.Stock) State.ShopStock[npc.Id+"/"+item]=20;
        State.NextRestock=State.Time+600; EconomicDirty=true;
    }
    private void ApplyStatus(List<StatusEffect> effects,string kind,Element element,double duration,double power,string source)
    {
        if(kind==""||duration<=0) return;
        int cap=kind=="poison"?5:1;
        var matching=effects.Where(x=>x.Kind==kind).ToList();
        if(matching.Count>=cap)
        {
            var old=matching.OrderBy(x=>x.Until).First(); old.Until=State.Time+Math.Min(60,duration); old.Power=Math.Max(old.Power,power); old.Source=source; return;
        }
        effects.Add(new(){Kind=kind,Element=element,Until=State.Time+Math.Min(60,duration),Power=power,Source=source});
    }
    private void Progress(Character p,string action,string target,int amount=1)
    {
        if(amount<1) return;
        AdvanceGuildProject(p,action,amount);
        foreach(var entry in p.Quests)
        {
            var q=Data.Quest(entry.Key); var progress=entry.Value;
            for(int i=0;i<q.Objectives.Count;i++)
            {
                var o=q.Objectives[i];
                if(o.Action==action&&(o.Target=="*"||o.Target==target)) progress.Counts[i]=Math.Min(o.Count,progress.Counts[i]+amount);
            }
            progress.Complete=q.Objectives.Select((o,i)=>progress.Counts[i]>=o.Count).All(x=>x);
        }
    }
}
