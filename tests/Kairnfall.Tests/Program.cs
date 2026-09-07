using System.Diagnostics;
using System.Text.Json;
using Kairnfall.Core;

var path=args.FirstOrDefault()??"content/catalog.json";
var data=Catalog.Load(path);
var results=new List<object>();
int failed=0;
void Check(bool value,string message="Assertion failed") { if(!value) throw new Exception(message); }
void Equal<T>(T expected,T actual) { Check(EqualityComparer<T>.Default.Equals(expected,actual),$"Expected {expected}; received {actual}."); }
void Test(string name,Action body)
{
    var watch=Stopwatch.StartNew();
    try { body(); Console.WriteLine("PASS "+name); results.Add(new{name,passed=true,milliseconds=watch.ElapsedMilliseconds}); }
    catch(Exception error) { failed++; Console.WriteLine("FAIL "+name+": "+error.Message); results.Add(new{name,passed=false,error=error.ToString(),milliseconds=watch.ElapsedMilliseconds}); }
}
(RealmEngine Engine,string Player) Fresh(string cls="vanguard")
{
    var engine=new RealmEngine(data);
    var p=engine.CreateCharacter("test-account", "Test Traveler",cls,new());
    engine.Active.Add(p.Id);
    return(engine,p.Id);
}
GameCommand Command(RealmEngine engine,string player,string kind,string target="",string item="",int amount=1,string arg="")
    =>new(){Kind=kind,Target=target,Item=item,Amount=amount,Arg=arg,Sequence=engine.Player(player).LastAction+1};
void NearNpc(RealmEngine engine,string player,string id)
{
    var npc=data.Npc(id); var p=engine.Player(player); p.Zone=npc.Zone; p.Position=npc.Position;
}
void Step(RealmEngine engine,int ticks=40) { for(int i=0;i<ticks;i++) engine.Tick(0.05); }
void AssertValid(RealmEngine engine) { var errors=Items.Validate(engine.State,data); Check(errors.Count==0,string.Join("; ",errors)); }

Test("catalog content targets and all references",()=>
{
    Equal(60,data.Skills.Count); Equal(8,data.Classes.Count); Check(data.Items.Count>=450);
    Equal(120,data.Abilities.Count); Equal(100,data.Mobs.Count(x=>!x.Boss&&!x.Elite));
    Equal(25,data.Mobs.Count(x=>x.Elite)); Equal(20,data.Mobs.Count(x=>x.Boss));
    Equal(5,data.Zones.Count(x=>x.Kind=="city")); Check(data.Npcs.Count>=150);
    Equal(25,data.Quests.Count(x=>x.Category=="main")); Equal(100,data.Quests.Count(x=>x.Category=="side"));
    Equal(30,data.Quests.Count(x=>x.Repeatable)); Equal(0,data.Validate().Count);
});
Test("every class starts with valid owned equipment",()=>
{
    foreach(var cls in data.Classes)
    {
        var(e,id)=Fresh(cls.Id); var p=e.Player(id);
        Equal(60,p.SkillXp.Count); Equal("wayfarers_rest",p.Zone);
        Equal(cls.Weapon,Items.Owned(p,p.Equipment["weapon"]).Template);
        Check(p.Health>0&&p.Mana>0&&p.Stamina>0); AssertValid(e);
    }
});
Test("skill thresholds are monotonic",()=>
{
    long previous=-1;
    for(int level=1;level<=100;level++) { long threshold=Progression.Threshold(level); Check(threshold>previous); previous=threshold; }
});
Test("every skill can earn persistent experience",()=>
{
    var(e,id)=Fresh(); var p=e.Player(id);
    foreach(var skill in data.Skills) { Progression.Train(p,skill.Id,200,1,data); Check(p.SkillXp[skill.Id]>0,skill.Id); }
    Check(Progression.PlayerLevel(p)>1); var copy=Wire.Copy(p);
    foreach(var skill in data.Skills) Equal(p.SkillXp[skill.Id],copy.SkillXp[skill.Id]);
});
Test("negative experience is rejected",()=>
{
    var(e,id)=Fresh(); bool rejected=false;
    try { Progression.Train(e.Player(id),"mining",-1,1,data); } catch(RuleException) { rejected=true; }
    Check(rejected); Equal(0L,e.Player(id).SkillXp["mining"]);
});
Test("movement cannot teleport or exceed input range",()=>
{
    var(e,id)=Fresh(); var before=e.Player(id).Position;
    var command=Command(e,id,"move"); command.X=900;
    Check(!e.Execute(id,command).Ok); Step(e,2); Equal(before,e.Player(id).Position);
});
Test("nonfinite movement is rejected",()=>
{
    var(e,id)=Fresh(); var command=Command(e,id,"move"); command.X=double.NaN;
    Check(!e.Execute(id,command).Ok);
});
Test("diagonal movement is normalized and input expires",()=>
{
    var(e,id)=Fresh(); var before=e.Player(id).Position;
    var command=Command(e,id,"move"); command.X=1; command.Y=1;
    Check(e.Execute(id,command).Ok); Step(e,7);
    Check(before.Distance(e.Player(id).Position)<=1.5);
    var stopped=e.Player(id).Position; Step(e,20); Check(stopped.Distance(e.Player(id).Position)<0.25);
});
Test("protocol mismatch is rejected",()=>
{
    var(e,id)=Fresh(); var command=Command(e,id,"move"); command.Version=999;
    Check(!e.Execute(id,command).Ok);
});
Test("unknown command cannot assign gold",()=>
{
    var(e,id)=Fresh(); long before=e.Player(id).Gold;
    Check(!e.Execute(id,Command(e,id,"set_gold",amount:999999)).Ok); Equal(before,e.Player(id).Gold);
});
Test("negative shop quantities preserve state",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_provisioner");
    long gold=e.Player(id).Gold; int count=e.Player(id).Inventory.Sum(x=>x.Quantity);
    Check(!e.Execute(id,Command(e,id,"buy","wayfarers_rest_provisioner","bread",-4)).Ok);
    Equal(gold,e.Player(id).Gold); Equal(count,e.Player(id).Inventory.Sum(x=>x.Quantity)); AssertValid(e);
});
Test("out-of-range purchases are rejected",()=>
{
    var(e,id)=Fresh(); Check(!e.Execute(id,Command(e,id,"buy","dawnreach_provisioner","bread",1)).Ok);
});
Test("shop replay is idempotent",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_provisioner"); e.Player(id).Gold=1000;
    var command=Command(e,id,"buy","wayfarers_rest_provisioner","bread",2);
    var first=e.Execute(id,command); Check(first.Ok,first.Message);
    long gold=e.Player(id).Gold; int bread=Items.Count(e.Player(id),"bread");
    var second=e.Execute(id,command); Check(second.Ok); Equal(gold,e.Player(id).Gold); Equal(bread,Items.Count(e.Player(id),"bread")); AssertValid(e);
});
Test("stale sequence cannot repeat a purchase",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_provisioner"); e.Player(id).Gold=1000;
    var command=Command(e,id,"buy","wayfarers_rest_provisioner","bread",1);
    Check(e.Execute(id,command).Ok); command.RequestId=Guid.NewGuid().ToString("N");
    Check(!e.Execute(id,command).Ok); Equal(1,Items.Count(e.Player(id),"bread"));
});
Test("insufficient funds roll back stock and inventory",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_provisioner"); e.Player(id).Gold=0;
    var key="wayfarers_rest_provisioner/bread"; var before=e.State.ShopStock[key];
    Check(!e.Execute(id,Command(e,id,"buy","wayfarers_rest_provisioner","bread",1)).Ok);
    Equal(before,e.State.ShopStock[key]); Equal(0,Items.Count(e.Player(id),"bread")); AssertValid(e);
});
Test("bank transfer preserves the unique item",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_banker");
    var item=e.Player(id).Inventory.First(x=>x.Template=="copper_pickaxe");
    var deposit=Command(e,id,"deposit",item:item.Id);
    Check(e.Execute(id,deposit).Ok); Check(e.Player(id).Bank.Any(x=>x.Id==item.Id));
    Check(!e.Player(id).Inventory.Any(x=>x.Id==item.Id));
    Check(e.Execute(id,deposit).Ok); Equal(1,e.Player(id).Bank.Count(x=>x.Id==item.Id));
    Check(e.Execute(id,Command(e,id,"withdraw",item:item.Id)).Ok); Check(e.Player(id).Inventory.Any(x=>x.Id==item.Id));
    AssertValid(e);
});
Test("equipped items cannot be banked or sold",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_banker"); var weapon=e.Player(id).Equipment["weapon"];
    Check(!e.Execute(id,Command(e,id,"deposit",item:weapon)).Ok);
    NearNpc(e,id,"wayfarers_rest_blacksmith"); Check(!e.Execute(id,Command(e,id,"sell","wayfarers_rest_blacksmith",weapon)).Ok); AssertValid(e);
});
Test("another character's item cannot be equipped",()=>
{
    var(e,id)=Fresh(); var other=e.CreateCharacter("other","Other Traveler","ranger",new());
    Check(!e.Execute(id,Command(e,id,"equip",item:other.Equipment["weapon"])).Ok); AssertValid(e);
});
Test("rune insertion consumes the rune and preserves its identity",()=>
{
    var(e,id)=Fresh(); var p=e.Player(id); var weapon=p.Equipment["weapon"];
    var rune=p.Inventory.Single(x=>x.Template=="rune_embers_1");
    var result=e.Execute(id,Command(e,id,"socket",weapon,rune.Id)); Check(result.Ok,result.Message);
    p=e.Player(id); Check(!p.Inventory.Any(x=>x.Id==rune.Id));
    Equal(rune.Id,Items.Owned(p,weapon).Runes.Single().Id);
    Check(CombatMath.Stats(p,data).Bonus("damage_fire")>0); AssertValid(e);
});
Test("socket replay cannot duplicate rune effects",()=>
{
    var(e,id)=Fresh(); var p=e.Player(id); var weapon=p.Equipment["weapon"]; var rune=p.Inventory.Single(x=>x.Template=="rune_embers_1");
    var command=Command(e,id,"socket",weapon,rune.Id);
    Check(e.Execute(id,command).Ok); Check(e.Execute(id,command).Ok);
    Equal(1,Items.Owned(e.Player(id),weapon).Runes.Count); AssertValid(e);
});
Test("gathering awards materials and skill experience",()=>
{
    var(e,id)=Fresh(); var node=e.State.Nodes.Values.First(x=>x.Zone=="wayfarers_rest"&&x.Template=="copper_vein");
    e.Player(id).Position=node.Position;
    var result=e.Execute(id,Command(e,id,"gather",node.Id)); Check(result.Ok,result.Message);
    Check(Items.Count(e.Player(id),"copper_ore")>0); Check(e.Player(id).SkillXp["mining"]>0);
    Check(!e.Execute(id,Command(e,id,"gather",node.Id)).Ok); AssertValid(e);
});
Test("crafting consumes ingredients and produces an ingot",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_blacksmith");
    Items.Add(e.Player(id).Inventory,Items.Create(data,"copper_ore",3),data);
    var result=e.Execute(id,Command(e,id,"craft",item:"make_copper_ingot")); Check(result.Ok,result.Message);
    Equal(0,Items.Count(e.Player(id),"copper_ore")); Equal(1,Items.Count(e.Player(id),"copper_ingot"));
    Check(e.Player(id).SkillXp["smithing"]>0); AssertValid(e);
});
Test("missing crafting material leaves all materials unchanged",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_blacksmith");
    Items.Add(e.Player(id).Inventory,Items.Create(data,"copper_ore",2),data);
    Check(!e.Execute(id,Command(e,id,"craft",item:"make_copper_ingot")).Ok);
    Equal(2,Items.Count(e.Player(id),"copper_ore")); Equal(0,Items.Count(e.Player(id),"copper_ingot")); AssertValid(e);
});
Test("quest reward cannot be claimed before objectives",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_trainer");
    Check(e.Execute(id,Command(e,id,"accept_quest",item:"main_01")).Ok);
    Check(!e.Execute(id,Command(e,id,"claim_quest",item:"main_01")).Ok);
});
Test("tutorial dialogue objective and reward persist",()=>
{
    var(e,id)=Fresh(); NearNpc(e,id,"wayfarers_rest_trainer");
    Check(e.Execute(id,Command(e,id,"accept_quest",item:"main_01")).Ok);
    NearNpc(e,id,"wayfarers_rest_blacksmith"); Check(e.Execute(id,Command(e,id,"talk","wayfarers_rest_blacksmith")).Ok);
    NearNpc(e,id,"wayfarers_rest_trainer"); var result=e.Execute(id,Command(e,id,"claim_quest",item:"main_01")); Check(result.Ok,result.Message);
    Check(e.Player(id).CompletedQuests.Contains("main_01"));
    Check(!e.Execute(id,Command(e,id,"claim_quest",item:"main_01")).Ok); AssertValid(e);
});
Test("every exit and arrival are walkable",()=>
{
    foreach(var z in data.Zones) foreach(var exit in z.Exits)
    { Check(WorldMap.Fits(z,exit.Position),exit.Id+" source"); Check(WorldMap.Fits(data.Zone(exit.Target),exit.Arrival),exit.Id+" arrival"); }
});
Test("all cities and layers are connected from the start",()=>
{
    var seen=new HashSet<string>{"wayfarers_rest"}; var queue=new Queue<string>(seen);
    while(queue.TryDequeue(out var zone)) foreach(var exit in data.Zone(zone).Exits) if(seen.Add(exit.Target)) queue.Enqueue(exit.Target);
    Equal(data.Zones.Count,seen.Count); Equal(4,data.Zones.Select(x=>x.Layer).Distinct().Count());
});
Test("boundary collision blocks travel outside a zone",()=>
{
    foreach(var zone in data.Zones)
    {
        Check(!WorldMap.Fits(zone,new(-1,2))); Check(!WorldMap.Fits(zone,new(zone.Width+1,2)));
        Check(!WorldMap.Fits(zone,new(0,0))); Check(WorldMap.Fits(zone,zone.Spawn),zone.Id);
    }
});
Test("transition requires proximity and survives serialization",()=>
{
    var(e,id)=Fresh(); var exit=data.Zone("wayfarers_rest").Exits.First();
    Check(!e.Execute(id,Command(e,id,"transition",exit.Id)).Ok);
    e.Player(id).Position=exit.Position; Check(e.Execute(id,Command(e,id,"transition",exit.Id)).Ok);
    Equal(exit.Target,e.Player(id).Zone);
    var restarted=new RealmEngine(data,Wire.Copy(e.State)); Equal(exit.Target,restarted.Player(id).Zone); AssertValid(restarted);
});
Test("snapshot removes account identity and command receipts",()=>
{
    var(e,id)=Fresh(); var snapshot=e.Snapshot(id); Equal("",snapshot.Self.Account); Equal(0,snapshot.Self.Receipts.Count);
});
Test("damage and resistance remain finite and bounded",()=>
{
    Equal(0.0,CombatMath.Damage(100,100,1)); Check(CombatMath.Damage(100,100,0)<100);
    Check(CombatMath.Damage(100,0,-0.5)<=150); bool rejected=false;
    try { CombatMath.Damage(double.PositiveInfinity,0,0); } catch(RuleException) { rejected=true; }
    Check(rejected);
});
Test("world state round trip preserves ownership and progression",()=>
{
    var(e,id)=Fresh(); Progression.Train(e.Player(id),"mining",800,10,data);
    e.Player(id).Gold=1234; e.Player(id).Discoveries.Add("test-discovery");
    var restored=new RealmEngine(data,Wire.Copy(e.State));
    Equal(1234L,restored.Player(id).Gold); Equal(e.Player(id).SkillXp["mining"],restored.Player(id).SkillXp["mining"]);
    Check(restored.Player(id).Discoveries.Contains("test-discovery")); AssertValid(restored);
});
Test("disconnect clears active input",()=>
{
    var(e,id)=Fresh(); var command=Command(e,id,"move"); command.X=1; Check(e.Execute(id,command).Ok);
    e.Disconnect(id); var position=e.Player(id).Position; Step(e,10); Equal(position,e.Player(id).Position); Check(!e.Active.Contains(id));
});

Directory.CreateDirectory("test-results");
File.WriteAllText("test-results/core.json",JsonSerializer.Serialize(new{passed=results.Count-failed,failed,results},new JsonSerializerOptions{WriteIndented=true}));
Console.WriteLine($"RESULT: {results.Count-failed} passed; {failed} failed.");
Environment.ExitCode=failed==0?0:1;
