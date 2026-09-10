using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

var path=args.Length>0?args[0]:"content/catalog.json";
var results=new List<object>(); int failures=0;
void Check(bool condition,string message) { if(!condition) throw new Exception(message); }
void Test(string name,Action body)
{
    var watch=Stopwatch.StartNew();
    try { body(); results.Add(new{name,status="passed",milliseconds=watch.Elapsed.TotalMilliseconds}); Console.WriteLine("PASS "+name); }
    catch(Exception e) { failures++; results.Add(new{name,status="failed",error=e.ToString(),milliseconds=watch.Elapsed.TotalMilliseconds}); Console.WriteLine("FAIL "+name+"\n"+e); }
}
Catalog data=Catalog.Load(path);
RealmEngine NewRealm()=>new(data);
Character NewPlayer(RealmEngine r,string name="Test Player",string cls="vanguard")
{
    var p=r.CreateCharacter(Guid.NewGuid().ToString("N"),name,cls,new()); r.Active.Add(p.Id); return p;
}
CommandResult Send(RealmEngine r,Character p,string kind,string target="",string item="",int amount=1,string arg="")=>r.Execute(p.Id,new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,Sequence=r.Player(p.Id).LastAction+1});
void MoveTo(RealmEngine r,Character p,NpcDef npc) { p.Zone=npc.Zone; p.Position=npc.Position; }

CreatureMotionCases.Run(Test,data);
Test("Catalog references and world graph",()=>Check(data.Validate().Count==0,"Catalog validation failed."));
Test("Required content counts",()=>
{
    Check(data.Skills.Count==60,"Expected 60 skills."); Check(data.Classes.Count==8,"Expected eight classes.");
    Check(data.Items.Count>=450,"Insufficient item templates."); Check(data.Abilities.Count>=120,"Insufficient abilities.");
    Check(data.Mobs.Count(x=>!x.Boss&&!x.Elite)>=100,"Insufficient normal species."); Check(data.Mobs.Count(x=>x.Boss)>=20,"Insufficient bosses.");
    Check(data.Zones.Count(x=>x.Kind=="city")==5,"Expected five cities."); Check(data.Zones.Count(x=>x.Kind=="dungeon")>=20,"Insufficient dungeons.");
    Check(data.Npcs.Count>=150,"Insufficient NPCs."); Check(data.Quests.Count(x=>x.Category=="side")>=100,"Insufficient side quests.");
});
Test("Skill curve monotonicity and exact thresholds",()=>
{
    for(int level=1;level<=100;level++)
    {
        Check(Progression.SkillLevel(Progression.Threshold(level))==level,"Threshold mismatch.");
        if(level>1) Check(Progression.Threshold(level)>Progression.Threshold(level-1),"Curve is not increasing.");
    }
});
Test("Overall level derives directly from awarded skill XP and respects cap",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); Check(Progression.PlayerLevel(p)==1,"New character level.");
    Progression.Train(p,"mining",1000,1,data);
    int trainedLevel=Progression.PlayerLevel(p); double trainedProgress=Progression.PlayerLevelProgress(p);
    Check(trainedLevel>1,"Noncombat skill did not raise character level.");
    p.PracticeOnlyXp=Progression.Total(p); p.OverallCreditRemainder=0;
    Check(Progression.PlayerLevel(p)==trainedLevel&&Math.Abs(Progression.PlayerLevelProgress(p)-trainedProgress)<.000001,"Hidden credit metadata changed character XP.");
    foreach(var skill in data.Skills) p.SkillXp[skill.Id]=Progression.Threshold(100);
    Check(Progression.PlayerLevel(p)==200,"Overall cap mismatch.");
});
Test("Expired ground loot is hidden and removed",()=>
{
    var r=NewRealm(); var p=NewPlayer(r);
    var expired=new LootPile{Zone=p.Zone,Position=p.Position,Expires=r.State.Time-1}; r.Loot[expired.Id]=expired;
    Check(!r.VisibleLoot(p.Id).Any(x=>x.Id==expired.Id),"Expired loot was still visible.");
    var fresh=new LootPile{Zone=p.Zone,Position=p.Position,Expires=r.State.Time+.2}; r.Loot[fresh.Id]=fresh;
    Check(r.VisibleLoot(p.Id).Any(x=>x.Id==fresh.Id),"Fresh loot was hidden early.");
    r.Tick(.1); r.Tick(.1); r.Tick(.1);
    Check(!r.Loot.ContainsKey(fresh.Id),"Expired loot remained in the realm.");
    Check(LootPile.LifetimeSeconds==180,"Ground-loot lifetime must stay at three minutes.");
});
Test("Trivial successful actions retain bounded fractional practice",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); p.SkillXp["mining"]=Progression.Threshold(60);
    long raw=Progression.Total(p),overall=ChallengeProgression.OverallTraining(p);
    for(int i=0;i<200;i++) Progression.Train(p,"mining",1,1,data);
    long gained=Progression.Total(p)-raw;
    Check(gained>0&&gained<=12,"Trivial practice was either lost or disproportionate: "+gained);
    Check(p.GeneralPracticeRemainders.TryGetValue("mining",out double carry)&&double.IsFinite(carry)&&carry>=0&&carry<1,"General practice carry is invalid.");
    Check(ChallengeProgression.OverallTraining(p)>overall||p.OverallCreditRemainder>0,"Successful skill practice stopped contributing to overall progress.");
});
Test("Player and skill experience progress fractions are bounded and move forward",()=>
{
    var r=NewRealm(); var p=NewPlayer(r);
    double playerBefore=Progression.PlayerLevelProgress(p);
    long skillBefore=p.SkillXp.GetValueOrDefault("mining");
    Progression.Train(p,"mining",1000,1,data);
    double skillProgress=Progression.SkillLevelProgress(p.SkillXp["mining"]);
    Check(skillProgress>=0&&skillProgress<=1,"Skill progress fraction is invalid.");
    Check(p.SkillXp["mining"]>skillBefore,"Mining XP did not increase.");
    Check(Progression.PlayerLevel(p)>1||Progression.PlayerLevelProgress(p)>playerBefore,"Overall experience did not move.");
});
Test("Rarity skill bonus ranges and crafting gates are ordered",()=>
{
    int previous=0;
    foreach(Rarity rarity in Enum.GetValues<Rarity>())
    {
        var range=Items.SkillBonusRange(rarity);
        Check(range.Min==(int)rarity&&range.Max==(int)rarity+1,"Unexpected skill bonus range for "+rarity);
        int gate=Items.CraftRarityRequirement(rarity,10); Check(gate>=previous,"Craft rarity gate moved backward."); previous=gate;
        var r=NewRealm(); var p=NewPlayer(r,"Rarity "+rarity);
        var item=Items.Create(data,"steel_sword",1,rarity,p);
        int total=item.SkillBonuses.Values.Sum(); Check(total>=range.Min&&total<=range.Max,"Rolled skill bonus outside rarity range: "+rarity);
        Check(item.SkillBonuses.Keys.All(skill=>data.Skills.Any(x=>x.Id==skill)),"Unknown rolled skill.");
    }
    for(int n=0;n<100;n++) Check(Items.RollCraftRarity(1,1)==Rarity.Common,"Craft rarity bypassed its skill gate.");
});
Test("Equipment skill levels work but never satisfy equipment requirements",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var targetDef=data.Item("steel_sword");
    int required=BeginnerProgression.EquipmentRequirement(targetDef);
    p.SkillXp[targetDef.Skill]=Progression.Threshold(Math.Max(1,required-1));
    var belt=Items.Create(data,"linen_heavy_belt",1,Rarity.Common,p); belt.SkillBonuses.Clear(); belt.SkillBonuses[targetDef.Skill]=1;
    Items.Add(p.Inventory,belt,data); Items.Equip(p,belt.Id,data);
    Check(Progression.BaseLevel(p,targetDef.Skill)==Math.Max(1,required-1),"Base level changed from equipment.");
    Check(Progression.Level(p,targetDef.Skill)>=required,"Equipment skill bonus did not raise effective level.");
    var target=Items.Create(data,targetDef.Id,1,Rarity.Common,p); Items.Add(p.Inventory,target,data);
    bool rejected=false; try { Items.Equip(p,target.Id,data); } catch(RuleException) { rejected=true; }
    Check(rejected,"Equipment bonus incorrectly satisfied another equipment requirement.");
});
Test("Element relationships are balanced and attunement scales matchup magnitude",()=>
{
    var elements=Enum.GetValues<Element>().Where(x=>x!=Element.Physical).ToArray();
    foreach(var element in elements)
    {
        Check(elements.Count(target=>CombatMath.ElementRelationship(element,target)==1)==2,"Element does not have exactly two strengths: "+element);
        Check(elements.Count(target=>CombatMath.ElementRelationship(element,target)==-1)==2,"Element does not have exactly two weaknesses: "+element);
        foreach(var target in elements) Check(CombatMath.ElementRelationship(element,target)==-CombatMath.ElementRelationship(target,element),"Element relationship is not reciprocal.");
    }
    double strong=CombatMath.ElementMultiplier(Element.Fire,Element.Nature);
    double attuned=CombatMath.ElementMultiplier(Element.Fire,Element.Nature,8,0);
    double weak=CombatMath.ElementMultiplier(Element.Fire,Element.Arcane,8,0);
    Check(strong>1&&attuned>strong&&weak<1,"Element matchup or attunement scaling failed.");
    Check(CombatMath.ElementMultiplier(Element.Physical,Element.Fire,20,20)==1,"Physical must remain neutral.");
});
Test("All classes create valid characters and starter equipment",()=>
{
    var r=NewRealm(); foreach(var cls in data.Classes) NewPlayer(r,"Hero "+cls.Name,cls.Id);
    Check(Items.Validate(r.State,data).Count==0,"Invalid starter state.");
});
Test("Duplicate character names rejected",()=>
{
    var r=NewRealm(); NewPlayer(r,"Same Name"); bool rejected=false;
    try { NewPlayer(r,"same name"); } catch(RuleException) { rejected=true; }
    Check(rejected,"Duplicate name accepted.");
});
Test("Movement rejects impossible client coordinates",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var before=p.Position;
    var result=r.Execute(p.Id,new(){Kind="move",X=2000,Y=0}); Check(!result.Ok,"Invalid direction accepted.");
    r.Tick(0.05); Check(p.Position==before,"Rejected movement changed position.");
    result=r.Execute(p.Id,new(){Kind="move",X=double.NaN}); Check(!result.Ok,"NaN accepted.");
});
Test("Movement displacement is server-timed",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var before=p.Position;
    for(int n=0;n<100;n++) r.Execute(p.Id,new(){Kind="move",X=1,Y=1});
    r.Tick(0.05); Check(p.Position.Distance(before)<=CombatMath.Stats(p,data).MoveSpeed*0.05+0.001,"Client packet frequency increased speed.");
});
Test("Every transition is physically reachable from its region spawn",()=>
{
    foreach(var z in data.Zones)
    foreach(var exit in z.Exits)
    {
        var route=WorldMap.FindPath(z,z.Spawn,exit.Position,z.Width*z.Height);
        Check(route.Count>0||z.Spawn.Distance(exit.Position)<1.5,"Unreachable exit: "+z.Id+"/"+exit.Id);
    }
});
Test("World geometry is deterministic",()=>
{
    foreach(var z in data.Zones.Take(8)) for(int i=0;i<100;i++) Check(WorldMap.TileAt(z,i%z.Width,(i*7)%z.Height)==WorldMap.TileAt(Wire.Copy(z),i%z.Width,(i*7)%z.Height),"Geometry mismatch.");
});
Test("Negative purchase rolls back without gold changes",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var npc=data.Npcs.First(x=>x.Role=="provisioner"); MoveTo(r,p,npc); long gold=p.Gold;
    var result=Send(r,p,"buy",npc.Id,"healing_potion",-10);
    Check(!result.Ok&&r.Player(p.Id).Gold==gold,"Negative purchase mutated state.");
});
Test("Shop replay is idempotent",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var npc=data.Npcs.First(x=>x.Role=="provisioner"); MoveTo(r,p,npc); p.Gold=1000;
    var command=new GameCommand{Kind="buy",Target=npc.Id,Item="healing_potion",Amount=1,Sequence=1};
    var first=r.Execute(p.Id,command); Check(first.Ok,first.Message); long gold=p.Gold; int count=Items.Count(p,"healing_potion");
    var second=r.Execute(p.Id,command); Check(second.Ok&&p.Gold==gold&&Items.Count(p,"healing_potion")==count,"Replay duplicated purchase.");
});
Test("Remote service calls rejected",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var banker=data.Npcs.First(x=>x.Role=="banker");
    var item=p.Inventory.First(x=>!Items.Equipped(p,x.Id)); var result=Send(r,p,"deposit",item:item.Id);
    Check(!result.Ok,"Remote bank accepted deposit.");
});
Test("Bank deposits and withdrawals conserve item identity",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); MoveTo(r,p,data.Npcs.First(x=>x.Role=="banker"));
    var item=p.Inventory.First(x=>!Items.Equipped(p,x.Id)&&x.Quantity==1); string id=item.Id;
    Check(Send(r,p,"deposit",item:id).Ok,"Deposit failed."); Check(p.Bank.Any(x=>x.Id==id)&&p.Inventory.All(x=>x.Id!=id),"Deposit ownership invalid.");
    Check(Send(r,p,"withdraw",item:id).Ok,"Withdrawal failed."); Check(p.Inventory.Any(x=>x.Id==id)&&p.Bank.All(x=>x.Id!=id),"Withdrawal ownership invalid.");
});
Test("Equipped items cannot enter bank or trade escrow",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); MoveTo(r,p,data.Npcs.First(x=>x.Role=="banker")); string id=p.Equipment["weapon"];
    var result=Send(r,p,"deposit",item:id); Check(!result.Ok&&r.Player(p.Id).Equipment["weapon"]==id,"Equipped item moved to bank.");
});
Test("Crafting consumes ingredients and awards the correct skill",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var npc=data.Npcs.First(x=>x.Station=="forge"); MoveTo(r,p,npc);
    Items.Add(p.Inventory,Items.Create(data,"copper_ore",3),data); long xp=p.SkillXp["smithing"];
    var result=Send(r,p,"craft",item:"smelt_copper"); Check(result.Ok,result.Message);
    Check(Items.Count(p,"copper_ore")==0&&Items.Count(p,"copper_bar")==1&&p.SkillXp["smithing"]>xp,"Crafting accounting failed.");
});
Test("Crafting rejects missing ingredients atomically",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); MoveTo(r,p,data.Npcs.First(x=>x.Station=="forge")); string before=JsonSerializer.Serialize(p.Inventory,Wire.Json);
    var result=Send(r,p,"craft",item:"smelt_copper"); Check(!result.Ok,"Crafting accepted missing ore.");
    Check(JsonSerializer.Serialize(r.Player(p.Id).Inventory,Wire.Json)==before,"Failed craft changed inventory.");
});
Test("Socketing moves one unique rune into equipment",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var rune=p.Inventory.First(x=>x.Template=="rune_embers_1"); string runeId=rune.Id;
    var result=Send(r,p,"socket",p.Equipment["weapon"],rune.Id); Check(result.Ok,result.Message);
    Check(p.Inventory.All(x=>x.Id!=runeId)&&Items.Owned(p,p.Equipment["weapon"]).Runes.Single().Id==runeId,"Rune ownership was duplicated.");
    Check(Items.Validate(r.State,data).Count==0,"Socket invalidated realm.");
});
Test("Auction purchase cannot execute twice",()=>
{
    var r=NewRealm(); var seller=NewPlayer(r,"Seller Hero"); var buyer=NewPlayer(r,"Buyer Hero"); var npc=data.Npcs.First(x=>x.Role=="auctioneer");
    MoveTo(r,seller,npc); MoveTo(r,buyer,npc); buyer.Gold=1000;
    var item=seller.Inventory.First(x=>x.Template=="copper_pickaxe"); string itemId=item.Id;
    var listing=Send(r,seller,"auction_list","100",item.Id); Check(listing.Ok,listing.Message);
    string auction=r.State.Auctions.Keys.Single(); var purchase=Send(r,buyer,"auction_buy",auction); Check(purchase.Ok,purchase.Message);
    long gold=buyer.Gold; var repeat=Send(r,buyer,"auction_buy",auction); Check(!repeat.Ok&&r.Player(buyer.Id).Gold==gold,"Duplicate auction charge.");
    Check(r.State.Characters.Values.Sum(x=>x.Inventory.Count(i=>i.Id==itemId))==1,"Auction duplicated item.");
});
Test("Trade requires both readiness and final confirmation",()=>
{
    var r=NewRealm(); var a=NewPlayer(r,"Trade Alpha"); var b=NewPlayer(r,"Trade Beta"); b.Position=a.Position;
    Check(Send(r,a,"trade_invite",b.Id).Ok,"Trade invite failed."); string id=r.State.Trades.Keys.Single();
    var item=a.Inventory.First(x=>x.Template=="copper_pickaxe"); string itemId=item.Id;
    Check(Send(r,a,"trade_offer",id,itemId,1).Ok,"Offer failed."); int revision=r.State.Trades[id].Revision;
    Check(!Send(r,a,"trade_confirm",id,amount:revision).Ok,"Trade confirmed before ready.");
    a=r.Player(a.Id); b=r.Player(b.Id);
    Check(Send(r,a,"trade_ready",id,amount:revision).Ok,"First ready failed."); Check(Send(r,b,"trade_ready",id,amount:revision).Ok,"Second ready failed.");
    Check(Send(r,a,"trade_confirm",id,amount:revision).Ok,"First confirmation failed."); Check(r.State.Trades.ContainsKey(id),"Trade completed before second confirmation.");
    Check(Send(r,b,"trade_confirm",id,amount:revision).Ok,"Second confirmation failed.");
    Check(!r.State.Trades.ContainsKey(id)&&b.Inventory.Any(x=>x.Id==itemId)&&a.Inventory.All(x=>x.Id!=itemId),"Trade did not transfer ownership.");
});
Test("Trade offer changes invalidate prior consent",()=>
{
    var r=NewRealm(); var a=NewPlayer(r,"Consent Alpha"); var b=NewPlayer(r,"Consent Beta"); b.Position=a.Position;
    Send(r,a,"trade_invite",b.Id); string id=r.State.Trades.Keys.Single(); Send(r,a,"trade_ready",id,amount:0); Send(r,b,"trade_ready",id,amount:0);
    Check(Send(r,a,"trade_offer",id,arg:"5").Ok,"Gold offer failed."); var t=r.State.Trades[id]; Check(!t.A.Ready&&!t.B.Ready&&!t.A.Confirmed&&!t.B.Confirmed,"Offer change retained consent.");
});
Test("Whispers and group chat do not leak",()=>
{
    var r=NewRealm(); var a=NewPlayer(r,"Chat Alpha"); var b=NewPlayer(r,"Chat Beta"); var c=NewPlayer(r,"Chat Gamma");
    var msg=new ChatMessage{Channel="whisper",Sender=a.Id,Target=b.Id}; Check(r.CanReceiveChat(a.Id,msg)&&r.CanReceiveChat(b.Id,msg)&&!r.CanReceiveChat(c.Id,msg),"Whisper leaked.");
    msg.Channel="party"; Check(!r.CanReceiveChat(b.Id,msg),"Empty party IDs were treated as membership.");
});
Test("Quest reward can only be claimed once",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var quest=data.Quests.First(x=>x.Id=="starter_ore"); MoveTo(r,p,data.Npc(quest.Giver));
    Check(Send(r,p,"accept_quest",item:quest.Id).Ok,"Accept failed."); p.Quests[quest.Id].Counts=[3]; p.Quests[quest.Id].Complete=true;
    Check(Send(r,p,"claim_quest",item:quest.Id).Ok,"Claim failed."); long gold=p.Gold;
    Check(!Send(r,p,"claim_quest",item:quest.Id).Ok&&r.Player(p.Id).Gold==gold,"Quest reward duplicated.");
});
Test("Persistence round trip preserves item IDs and skills",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); Progression.Train(p,"mining",500,1,data); var copy=Wire.Copy(r.State);
    var restored=new RealmEngine(data,copy); Check(Items.Validate(restored.State,data).Count==0,"Restored state invalid.");
    Check(restored.Player(p.Id).Inventory.Select(x=>x.Id).SequenceEqual(p.Inventory.Select(x=>x.Id))&&restored.Player(p.Id).SkillXp["mining"]==p.SkillXp["mining"],"Round trip lost persistent data.");
});
Test("Damage and resistance limits remain finite",()=>
{
    Check(CombatMath.Damage(100,0,1)==0,"Immunity failed."); Check(CombatMath.Damage(100,0,-1)==150,"Weakness cap failed.");
    Check(double.IsFinite(CombatMath.Damage(1e9,1e9,0.5)),"Damage became nonfinite.");
});
Test("Chest ownership and cooldown prevent repeated loot",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var chest=r.State.Chests.Values.First(x=>x.Kind=="weathered"&&x.Zone==p.Zone); p.Position=chest.Position;
    var first=Send(r,p,"chest",chest.Id); Check(first.Ok,first.Message); long gold=p.Gold;
    var second=Send(r,p,"chest",chest.Id); Check(!second.Ok&&r.Player(p.Id).Gold==gold,"Chest paid twice.");
});
Test("Basic combat can kill, award skills, and create owned loot",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); var mob=r.State.Creatures.Values.First(x=>x.Zone==p.Zone); p.Position=mob.Position; mob.Health=1;
    var result=Send(r,p,"attack",mob.Id); Check(result.Ok,result.Message);
    Check(mob.Health==0&&r.Loot.Values.Any(x=>x.Owner==p.Id)&&p.SkillXp["slayer"]>0,"Combat reward chain failed.");
});
Test("Simulation survives ten seconds of active creature behavior",()=>
{
    var r=NewRealm(); var p=NewPlayer(r); for(int i=0;i<200;i++) r.Tick(0.05);
    Check(Items.Validate(r.State,data).Count==0&&double.IsFinite(r.State.Time),"Simulation invariant failed.");
});
Directory.CreateDirectory("artifacts/test-results");
File.WriteAllText("artifacts/test-results/core.json",JsonSerializer.Serialize(new{passed=results.Count-failures,failed=failures,tests=results},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"RESULT: {results.Count-failures} passed; {failures} failed.");
return failures==0?0:1;
