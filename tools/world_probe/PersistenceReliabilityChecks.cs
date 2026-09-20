using System.Text.Json;
using Kairnfall.Core;

internal static class PersistenceReliabilityChecks
{
    public static void Run(Catalog data,List<string> failures)
    {
        int passed=0;
        void Test(string name,Action body)
        {
            try { body(); passed++; Console.WriteLine("PASS PERSISTENCE RELIABILITY: "+name); }
            catch(Exception error) { failures.Add("PERSISTENCE RELIABILITY: "+name); Console.WriteLine("FAIL PERSISTENCE RELIABILITY: "+name+": "+error.Message); }
        }
        void Need(bool condition,string message) { if(!condition) throw new InvalidOperationException(message); }
        string Json<T>(T value)=>JsonSerializer.Serialize(value,Wire.Json);
        RealmEngine Restart(RealmEngine source)
        {
            string json=Json(new RealmSave{State=source.State,Loot=source.Loot});
            var save=JsonSerializer.Deserialize<RealmSave>(json,Wire.Json)??throw new InvalidOperationException("Save roundtrip returned null.");
            var restarted=new RealmEngine(data,save.State){Loot=save.Loot};
            restarted.RecoverLegacyLootPositions();
            restarted.ResetTransientConnectionState();
            PersistenceIntegrity.RequireValid(restarted);
            return restarted;
        }
        (RealmEngine Realm,Character Player) Fixture(string suffix="")
        {
            var realm=new RealmEngine(data);
            var player=realm.CreateCharacter("persist-account"+suffix,"P"+suffix,"vanguard",new());
            realm.Active.Add(player.Id);
            return (realm,player);
        }
        GameCommand Command(RealmEngine realm,Character player,string kind,string target="",string item="",int amount=1,string arg="")
            =>new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,Sequence=player.LastAction+1,RequestId=Guid.NewGuid().ToString("N")};
        void ReplayAfterRestart(RealmEngine realm,string playerId,GameCommand command,string label)
        {
            realm.Disconnect(playerId);
            var restarted=Restart(realm); var before=Json(new RealmSave{State=restarted.State,Loot=restarted.Loot});
            var replay=restarted.Execute(playerId,command);
            Need(replay.Ok,label+" replay lost its persisted success receipt.");
            Need(before==Json(new RealmSave{State=restarted.State,Loot=restarted.Loot}),label+" replay mutated persisted state twice.");
        }

        Test("disconnect stops movement while preserving the last authoritative position",()=>
        {
            var (realm,p)=Fixture("Move");
            var moved=realm.Execute(p.Id,new GameCommand{Kind="move",X=1,Y=0}); Need(moved.Ok,"Movement intent rejected.");
            for(int i=0;i<6;i++) realm.Tick(.05);
            var at=p.Position; realm.Disconnect(p.Id);
            for(int i=0;i<20;i++) realm.Tick(.05);
            Need(p.Position==at,"Disconnected movement input remained authoritative.");
            var restarted=Restart(realm); Need(restarted.Player(p.Id).Position==at,"Restart lost the last authoritative movement position.");
        });

        Test("disconnect during combat preserves pending damage and timed state",()=>
        {
            var (realm,p)=Fixture("Combat"); p.Health=20; p.LastCombat=realm.State.Time;
            p.Cooldowns["fixture"]=realm.State.Time+12;
            p.Statuses.Add(new(){Kind="poison",Element=Element.Poison,Power=2,Until=realm.State.Time+3,Source="fixture"});
            realm.Disconnect(p.Id); for(int i=0;i<20;i++) realm.Tick(.05);
            Need(p.Health<20,"Offline pending damage was skipped.");
            var restarted=Restart(realm); var loaded=restarted.Player(p.Id);
            Need(loaded.Health==p.Health&&loaded.Cooldowns["fixture"]==p.Cooldowns["fixture"]&&loaded.Statuses.Any(x=>x.Kind=="poison"),"Combat timers changed across restart.");
        });

        Test("inventory equipment quest skill level gold and cooldown identity survive restart",()=>
        {
            var (realm,p)=Fixture("Character");
            p.Gold=777; p.SkillXp["mining"]=Progression.Threshold(3)+17; p.Cooldowns["fixture"]=realm.State.Time+42;
            var quest=data.Quests.First(q=>q.Objectives.Count>0); p.Quests[quest.Id]=new(){Counts=Enumerable.Repeat(1,quest.Objectives.Count).ToList()};
            var completed=data.Quests.First(q=>q.Id!=quest.Id); p.CompletedQuests.Add(completed.Id);
            string inventory=Json(p.Inventory); string equipment=Json(p.Equipment); string quests=Json(p.Quests); string completedQuests=Json(p.CompletedQuests);
            string skills=Json(p.SkillXp); int overall=Progression.PlayerLevel(p); long gold=p.Gold; string cooldowns=Json(p.Cooldowns);
            realm.Disconnect(p.Id); var restarted=Restart(realm); var loaded=restarted.Player(p.Id);
            Need(Json(loaded.Inventory)==inventory&&Json(loaded.Equipment)==equipment,"Restart changed inventory or equipment identity.");
            Need(Json(loaded.Quests)==quests&&Json(loaded.CompletedQuests)==completedQuests,"Restart changed quest progress.");
            Need(Json(loaded.SkillXp)==skills&&Progression.PlayerLevel(loaded)==overall,"Restart changed skill XP or overall level.");
            Need(loaded.Gold==gold&&Json(loaded.Cooldowns)==cooldowns,"Restart changed gold or cooldowns.");
        });

        Test("loot ownership item identity and collection replay survive restart",()=>
        {
            var (realm,p)=Fixture("Loot");
            var item=Items.Create(data,"healing_potion",2); string itemId=item.Id;
            var pile=new LootPile{Id="persist-loot",Zone=p.Zone,Position=p.Position,Owner=p.Id,Gold=17,Items=[item],PublicAt=realm.State.Time+60,Expires=realm.State.Time+180}; realm.Loot[pile.Id]=pile;
            var restarted=Restart(realm); Need(restarted.Loot[pile.Id].Owner==p.Id&&restarted.Loot[pile.Id].Items.Single().Id==itemId,"Restart changed loot ownership or item identity.");
            var loaded=restarted.Player(p.Id); restarted.Active.Add(loaded.Id); var command=Command(restarted,loaded,"loot",target:pile.Id); var result=restarted.Execute(loaded.Id,command); Need(result.Ok,result.Message);
            long gold=loaded.Gold; int quantity=Items.Count(loaded,"healing_potion");
            restarted.Disconnect(loaded.Id); var again=Restart(restarted); var replay=again.Execute(loaded.Id,command); Need(replay.Ok,"Loot acknowledgement replay was lost.");
            Need(again.Player(loaded.Id).Gold==gold&&Items.Count(again.Player(loaded.Id),"healing_potion")==quantity&&!again.Loot.ContainsKey(pile.Id),"Loot replay duplicated rewards.");
        });

        Test("crafting and merchant transactions are exactly once across acknowledgement loss",()=>
        {
            var (realm,p)=Fixture("Commerce");
            var hand=data.Recipes.First(r=>r.Station=="hand"&&r.Ingredients.Count>0&&data.Items.Any(i=>i.Id==r.Output));
            foreach(var ingredient in hand.Ingredients) Items.Add(p.Inventory,Items.Create(data,ingredient.Key,ingredient.Value),data);
            p.SkillXp[hand.Skill]=Progression.Threshold(hand.Requirement);
            var craft=Command(realm,p,"craft",item:hand.Id); var crafted=realm.Execute(p.Id,craft); Need(crafted.Ok,"Fixture craft rejected: "+crafted.Message); ReplayAfterRestart(realm,p.Id,craft,"Craft");

            var restarted=Restart(realm); var buyer=restarted.Player(p.Id); restarted.Active.Add(buyer.Id); var merchant=data.Npcs.First(n=>n.Stock.Contains("healing_potion")); buyer.Zone=merchant.Zone; buyer.Position=merchant.Position; buyer.Gold=Math.Max(buyer.Gold,500);
            var buy=Command(restarted,buyer,"buy",target:merchant.Id,item:"healing_potion"); var bought=restarted.Execute(buyer.Id,buy); Need(bought.Ok,"Fixture merchant buy rejected: "+bought.Message); ReplayAfterRestart(restarted,buyer.Id,buy,"Merchant");
        });

        Test("disconnect cancels trade consent without moving inventory gold or social membership",()=>
        {
            var realm=new RealmEngine(data); var a=realm.CreateCharacter("trade-a","Persist Trader A","vanguard",new()); var b=realm.CreateCharacter("trade-b","Persist Trader B","vanguard",new()); realm.Active.Add(a.Id); realm.Active.Add(b.Id); b.Zone=a.Zone; b.Position=a.Position;
            var party=new SocialGroup{Name="Persistent Party",Leader=a.Id,Members=[a.Id,b.Id],Roles=new(){{a.Id,"leader"},{b.Id,"member"}}}; realm.State.Parties[party.Id]=party; a.Party=party.Id; b.Party=party.Id;
            var guild=new SocialGroup{Name="Persistent Guild",Leader=a.Id,Members=[a.Id,b.Id],Roles=new(){{a.Id,"leader"},{b.Id,"member"}}}; realm.State.Guilds[guild.Id]=guild; a.Guild=guild.Id; b.Guild=guild.Id;
            string item=a.Inventory.First(x=>!Items.Equipped(a,x.Id)).Id; long gold=a.Gold;
            var invite=Command(realm,a,"trade_invite",target:b.Id); Need(realm.Execute(a.Id,invite).Ok,"Trade invite rejected.");
            string trade=realm.State.Trades.Values.Single().Id; var offer=Command(realm,a,"trade_offer",target:trade,item:item,amount:1); Need(realm.Execute(a.Id,offer).Ok,"Trade offer rejected.");
            string inventory=Json(a.Inventory); realm.Disconnect(a.Id);
            Need(realm.State.Trades.Count==0&&Json(a.Inventory)==inventory&&a.Gold==gold,"Disconnect changed trade inventory or gold.");
            var restarted=Restart(realm); var loaded=restarted.Player(a.Id); Need(loaded.Party==party.Id&&loaded.Guild==guild.Id&&restarted.State.Parties[party.Id].Members.Contains(a.Id)&&restarted.State.Guilds[guild.Id].Members.Contains(a.Id),"Disconnect/restart lost party or guild membership.");
        });

        Test("crash restart clears socket-bound LFG ready trade and aggro state only",()=>
        {
            var realm=new RealmEngine(data); var a=realm.CreateCharacter("stale-a","Stale A","vanguard",new()); var b=realm.CreateCharacter("stale-b","Stale B","vanguard",new());
            var party=new SocialGroup{Name="Restart Party",Leader=a.Id,Members=[a.Id,b.Id],Roles=new(){{a.Id,"leader"},{b.Id,"member"}},ReadyCheckEnds=100,ReadyMembers=[a.Id]}; realm.State.Parties[party.Id]=party; a.Party=party.Id; b.Party=party.Id;
            a.LfgActivity="boss"; a.LfgRole="tank"; a.LfgSince=5;
            var trade=new Trade{A=new(){Character=a.Id},B=new(){Character=b.Id},Expires=100}; realm.State.Trades[trade.Id]=trade;
            var creature=realm.State.Creatures.Values.First(); creature.Target=a.Id; creature.Threat[a.Id]=50;
            var restarted=Restart(realm); var loaded=restarted.Player(a.Id); var loadedParty=restarted.State.Parties[party.Id]; var loadedCreature=restarted.State.Creatures[creature.Id];
            Need(restarted.State.Trades.Count==0&&loaded.LfgActivity==""&&loaded.LfgRole==""&&loaded.LfgSince==0,"Restart retained stale trade or LFG connection state.");
            Need(loadedParty.ReadyCheckEnds==0&&loadedParty.ReadyMembers.Count==0,"Restart retained a ready check with no connected members.");
            Need(loaded.Party==party.Id&&loadedParty.Members.SetEquals([a.Id,b.Id]),"Restart removed durable party membership.");
            Need(loadedCreature.Target==""&&loadedCreature.Threat.Count==0,"Restart retained stale creature aggro against disconnected players.");
        });

        Test("auction escrow and purchase replay preserve unique item identity and gold",()=>
        {
            var realm=new RealmEngine(data); var seller=realm.CreateCharacter("auction-s","Persist Seller","vanguard",new()); var buyer=realm.CreateCharacter("auction-b","Persist Buyer","vanguard",new()); realm.Active.Add(seller.Id); realm.Active.Add(buyer.Id);
            var auctioneer=data.Npcs.First(n=>n.Role=="auctioneer"); seller.Zone=buyer.Zone=auctioneer.Zone; seller.Position=buyer.Position=auctioneer.Position; buyer.Gold=1000;
            var unique=data.Items.First(i=>i.StackMax==1&&i.Type!="quest"&&i.Value>0); var sale=Items.Create(data,unique.Id,1); seller.Inventory.Add(sale); string itemId=sale.Id;
            var list=Command(realm,seller,"auction_list",item:itemId,amount:1,target:"25"); var listed=realm.Execute(seller.Id,list); Need(listed.Ok,"Auction list rejected: "+listed.Message);
            var auction=realm.State.Auctions.Values.Single(x=>x.Item.Id==itemId); var buy=Command(realm,buyer,"auction_buy",target:auction.Id); var bought=realm.Execute(buyer.Id,buy); Need(bought.Ok,"Auction buy rejected: "+bought.Message);
            long sellerGold=seller.Gold; realm.Disconnect(buyer.Id); var restarted=Restart(realm); var replay=restarted.Execute(buyer.Id,buy); Need(replay.Ok,"Auction replay lost persisted receipt.");
            Need(restarted.Player(seller.Id).Gold==sellerGold&&restarted.Player(buyer.Id).Inventory.Count(x=>x.Id==itemId)==1&&!restarted.State.Auctions.ContainsKey(auction.Id),"Auction replay duplicated gold or item identity.");
        });

        Test("regional transition and stale-client commands are restart safe",()=>
        {
            var (realm,p)=Fixture("Transition"); var zone=data.Zone(p.Zone); var exit=zone.Exits.OrderBy(x=>x.Requirement).First();
            p.Position=exit.Position; p.SkillXp["exploration"]=Progression.Threshold(Math.Max(1,exit.Requirement));
            while(Progression.PlayerLevel(p)<exit.Requirement) p.SkillXp["exploration"]+=1000;
            var transition=Command(realm,p,"transition",target:exit.Id); var moved=realm.Execute(p.Id,transition); Need(moved.Ok,"Transition rejected: "+moved.Message); string target=p.Zone; ReplayAfterRestart(realm,p.Id,transition,"Transition");
            var restarted=Restart(realm); var loaded=restarted.Player(p.Id); var before=Json(loaded); var stale=Command(restarted,loaded,"consume",item:"healing_potion"); stale.Sequence=Math.Max(0,loaded.LastAction-1); var rejected=restarted.Execute(loaded.Id,stale);
            Need(!rejected.Ok&&Json(loaded)==before&&loaded.Zone==target,"Stale reconnect command mutated authoritative state.");
        });

        Test("world events pets cooldowns and dropped loot retain identity and timers",()=>
        {
            var (realm,p)=Fixture("Timed"); realm.State.Time=123.5; p.Cooldowns["dash"]=140; p.Statuses.Add(new(){Kind="slow",Element=Element.Frost,Until=130,Power=.25,Source="fixture"});
            var pet=realm.State.Creatures.Values.First(c=>c.Owner==""&&c.Health>0); pet.Owner=p.Id; pet.Target=""; pet.Threat.Clear(); p.Pet=pet.Id;
            var worldEvent=new WorldEvent{Id="persist-event",Name="Restart Event",Zone=p.Zone,Position=p.Position,Kind="rift",Started=120,StageStarted=122,StageEnds=150,Ends=180,Goal=10,Progress=3,LastTick=123}; worldEvent.Contributions[p.Id]=2; realm.State.Events.Add(worldEvent);
            var drop=new LootPile{Id="persist-drop",Zone=p.Zone,Position=p.Position,Owner=p.Id,Items=[Items.Create(data,"healing_potion")],Gold=3,PublicAt=150,Expires=300}; realm.Loot[drop.Id]=drop;
            realm.Disconnect(p.Id); var restarted=Restart(realm); var loaded=restarted.Player(p.Id);
            Need(restarted.State.Time==123.5&&loaded.Cooldowns["dash"]==140&&loaded.Statuses.Single(x=>x.Kind=="slow").Until==130,"Timed character state changed on restart.");
            Need(loaded.Pet==pet.Id&&restarted.State.Creatures[pet.Id].Owner==loaded.Id,"Pet identity/ownership changed on restart.");
            Need(restarted.State.Events.Count(x=>x.Id==worldEvent.Id)==1&&restarted.State.Events.Single(x=>x.Id==worldEvent.Id).Progress==3,"World event duplicated or reset on restart.");
            Need(restarted.Loot[drop.Id].Owner==loaded.Id&&restarted.Loot[drop.Id].Items[0].Id==drop.Items[0].Id,"Dropped loot identity or ownership changed on restart.");
        });

        Test("corrupt persistent identities timers and replay ledgers fail closed",()=>
        {
            void Reject(Action<RealmEngine> corrupt,string label)
            {
                var (realm,_)=Fixture("Corrupt"+Guid.NewGuid().ToString("N")[..6]); corrupt(realm); bool rejected=false; try { PersistenceIntegrity.RequireValid(realm); } catch(InvalidDataException) { rejected=true; }
                Need(rejected,"Corrupt "+label+" was accepted.");
            }
            Reject(r=>r.State.Time=double.NaN,"realm clock");
            Reject(r=>r.State.Creatures.First().Value.Position=new Point(double.MaxValue,4),"creature position");
            Reject(r=>r.State.Nodes.First().Value.ReadyAt=double.NaN,"node timer");
            Reject(r=>r.State.Chests.First().Value.Id="wrong-id","chest identity");
            Reject(r=>r.Player(r.State.Characters.Keys.First()).Cooldowns["bad"]=double.PositiveInfinity,"cooldown");
            Reject(r=>{var p=r.Player(r.State.Characters.Keys.First());p.LastAction=1;p.Receipts.Add(new(){RequestId=Guid.NewGuid().ToString("N"),Result=new(){RequestId="mismatch",Sequence=1,Ok=true}});},"replay receipt");
            Reject(r=>{var p=r.Player(r.State.Characters.Keys.First());p.Pet="missing-pet";},"pet pointer");
        });

        Console.WriteLine($"PERSISTENCE RELIABILITY: {passed}/11 groups passed; failures {failures.Count}. Covers disconnect/reconnect, restart, replay, complete character state, timed state, ownership, social state, transitions, pets, events and corruption. Human multiplayer feel remains separate.");
    }
}
